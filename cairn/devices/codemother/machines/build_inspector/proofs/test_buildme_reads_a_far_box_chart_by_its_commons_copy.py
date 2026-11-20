r"""Proof for ticket 072a482e6dd7 — the BUILDME chart lane reads a far box's validate berth.

Measured 2026-11-19: akiendell_cc_0 re-crossed 2a530dc20826 and 3413bea597fc at BUILDME after
both were charted on akiendelllinux, and each refused with
``[buildme_rides_the_chart] chart chain claims this ticket (expected: True, actual: False,
{"searched": "C:\\Users\\akien\\.cairn\\devices\\chart"})``. The lane globbed its own
``_CHART_BERTHS`` and never read through ``chain.claiming_packets``, whose index adds the commons
mirror where this box lacks the berth (e8fb6bcd23c5). The third site of one shape: 1e99a571dd6d
(sail.verdict) and 7cae18f7f9c2 (the verdict gate) fixed the same far-box read at their readers.

The world is a fixture: a scratch local chart root standing in for the default store, and a
scratch commons mirror (``chain._commons_mirror`` pointed at it). Nothing live is read.

    PYTHONPATH=. python3 cairn/devices/codemother/machines/build_inspector/proofs/test_buildme_reads_a_far_box_chart_by_its_commons_copy.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "072a482e6dd7": {
        "1": "test_a_far_box_validate_berth_is_read_by_its_commons_copy",
        "2": "test_no_claim_anywhere_names_both_roots_in_one_finding",
        "3": "test_a_local_berth_and_a_passed_root_read_as_before",
    },
}

_TICKET = "a0b1c2d3e4f5"
_NAME = "validate-20261119T211210-0123456789ab.json"


def _berth(path: Path, ticket: str = _TICKET) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"ticket": ticket, "hypothesize_ref": "fixture"}), encoding="utf-8")


@contextmanager
def _world():
    """A scratch default store and a scratch commons mirror, swapped in for the block."""
    from cairn.tools.chain import chain
    from cairn.devices.codemother.machines.build_inspector import inspector
    with tempfile.TemporaryDirectory() as tmp:
        local, mirror = Path(tmp) / "chart", Path(tmp) / "commons" / "berths" / "chart"
        local.mkdir(parents=True)
        mirror.mkdir(parents=True)
        saved = (chain.BERTHS_ROOT, chain._commons_mirror, inspector._CHART_BERTHS)
        chain.BERTHS_ROOT, inspector._CHART_BERTHS = str(local), local
        chain._commons_mirror = lambda: str(mirror)
        chain._INDEX_CACHE.clear()
        try:
            yield {"local": local, "mirror": mirror, "lane": inspector.buildme_rides_the_chart}
        finally:
            chain.BERTHS_ROOT, chain._commons_mirror, inspector._CHART_BERTHS = saved
            chain._INDEX_CACHE.clear()


def test_a_far_box_validate_berth_is_read_by_its_commons_copy():
    with _world() as w:
        _berth(w["mirror"] / _NAME)  # charted on another box: only its commons copy is here
        got = w["lane"](_TICKET)
        assert got == [], got
    print("ok test_a_far_box_validate_berth_is_read_by_its_commons_copy")


def test_no_claim_anywhere_names_both_roots_in_one_finding():
    with _world() as w:
        _berth(w["mirror"] / _NAME, ticket="ffffffffffff")  # a claim, but on another ticket
        got = w["lane"](_TICKET)
        assert len(got) == 1, got
        said = json.dumps(got[0])
        assert str(w["local"]) in said and str(w["mirror"]) in said, got[0]
    print("ok test_no_claim_anywhere_names_both_roots_in_one_finding")


def test_a_local_berth_and_a_passed_root_read_as_before():
    with _world() as w:
        _berth(w["local"] / "0" / "packets" / _NAME)
        assert w["lane"](_TICKET) == []
    with _world() as w:
        passed = w["local"].parent / "passed"
        _berth(passed / "0" / "packets" / _NAME)
        assert w["lane"](_TICKET, berths_root=passed) == []
        # a passed root reads only itself: a mirror claim does not leak into a caller's world
        _berth(w["mirror"] / _NAME)
        empty = w["local"].parent / "empty"
        empty.mkdir()
        got = w["lane"](_TICKET, berths_root=empty)
        assert len(got) == 1, got
    print("ok test_a_local_berth_and_a_passed_root_read_as_before")


if __name__ == "__main__":
    failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
            except AssertionError as exc:
                failed += 1
                print(f"RED {_name}: {exc}")
    sys.exit(1 if failed else 0)
