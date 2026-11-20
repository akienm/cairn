r"""Proof for ticket 7cae18f7f9c2 — the verdict gate reads a berth recorded on another host.

Measured 2026-11-19 on akiendell: ``sail.py verdict 8e0cfb77827c`` -> the verdict gate refused,
``FileNotFoundError: [Errno 2] No such file or directory:
'\home\akien\.cairn\devices\chart\0\packets\validate-20261119T071409-86ddb12d17da.json'``.
``StageGate._dispose`` opened ``packet['validate_ref']`` and ``validate['hypothesize_ref']`` directly;
``chain.resolve_berth`` is the door that finds the commons copy ``carry_berth`` left (1e99a571dd6d
fixed sail.verdict's lookup, 4e84a96955a1 the verdict contract's).

The world is a fixture: a scratch commons mirror holding the validate and hypothesize berths, the
packet naming them by a path recorded on ANOTHER host (a Linux ``/home/akien/...`` spelling and a
``PureWindowsPath`` ``C:\...`` spelling), so it reds on Linux as on Windows. No instrument forks:
the runner is injected.

    python3 cairn/devices/codemother/machines/chart_gate/proofs/test_the_verdict_gate_reads_a_far_box_berth_by_its_commons_copy.py
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
    "7cae18f7f9c2": {
        "1": "test_a_validate_berth_recorded_elsewhere_is_read_by_its_commons_copy",
        "2": "test_the_hypothesize_berth_it_names_is_read_by_its_commons_copy",
        "3": "test_an_unresolvable_ref_still_raises_naming_the_recorded_path",
    },
}

_LINUX = "/home/akien/.cairn/devices/chart/0/packets/"
_WINDOWS = r"C:\Users\other\.cairn\devices\chart\0\packets" + "\\"


def _runner(command, *, timeout_s=600, cwd=None):
    return {"command": command, "exit": 0, "timed_out": False, "timeout_s": timeout_s,
            "seconds": 0.0, "tail": "fixture"}


@contextmanager
def _commons(*, with_copies=True, spelling=_LINUX):
    """A scratch mirror; ``chain._commons_mirror`` pointed at it for the block."""
    from cairn.tools.chain import chain
    with tempfile.TemporaryDirectory() as tmp:
        mirror = Path(tmp)
        hyp_name, val_name = "hypothesize-20261119T000000-aaaa.json", "validate-20261119T000001-bbbb.json"
        hyp_ref, val_ref = spelling + hyp_name, spelling + val_name
        if with_copies:
            (mirror / hyp_name).write_text(json.dumps({"hypotheses": [
                {"piece": "the gate", "expect": "ok", "instrument": "`true`"}]}), encoding="utf-8")
            (mirror / val_name).write_text(json.dumps({"hypothesize_ref": hyp_ref}), encoding="utf-8")
        was = chain._commons_mirror
        chain._commons_mirror = lambda: str(mirror)
        try:
            yield {"validate_ref": val_ref, "hypothesize_ref": hyp_ref, "mirror": mirror}
        finally:
            chain._commons_mirror = was


def _gate():
    from cairn.devices.codemother.machines.chart_gate.gate import StageGate

    class _Mute:
        def post(self, **_):
            return None
    return StageGate("verdict", participant=_Mute(), runner=_runner)


def _dispose(w):
    return _gate()._dispose({"ticket": "7cae18f7f9c2", "validate_ref": w["validate_ref"]})


def test_a_validate_berth_recorded_elsewhere_is_read_by_its_commons_copy():
    for spelling in (_LINUX, _WINDOWS):
        with _commons(spelling=spelling) as w:
            got = _dispose(w)
            assert got["dispositions"] and got["dispositions"][0]["disposition"] == "confirmed", got
    print("ok test_a_validate_berth_recorded_elsewhere_is_read_by_its_commons_copy")


def test_the_hypothesize_berth_it_names_is_read_by_its_commons_copy():
    with _commons() as w:
        # the validate copy names the hypothesize berth by ITS recorded foreign path
        recorded = json.loads((w["mirror"] / Path(w["validate_ref"]).name).read_text(encoding="utf-8"))
        assert recorded["hypothesize_ref"] == w["hypothesize_ref"], recorded
        got = _dispose(w)
        assert [d["piece"] for d in got["dispositions"]] == ["the gate"], got
    print("ok test_the_hypothesize_berth_it_names_is_read_by_its_commons_copy")


def test_an_unresolvable_ref_still_raises_naming_the_recorded_path():
    with _commons(with_copies=False) as w:
        try:
            _dispose(w)
        except FileNotFoundError as exc:
            assert Path(w["validate_ref"]).name in str(exc), str(exc)
        else:
            raise AssertionError("an unresolvable berth must refuse loudly (Law 7)")
    print("ok test_an_unresolvable_ref_still_raises_naming_the_recorded_path")


if __name__ == "__main__":
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
