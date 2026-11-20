r"""Proof for ticket 5703d091eab6 — build_inspector reads a berth ref recorded on another box.

Measured 2026-11-19 on akiendelllinux: 7cae18f7f9c2's PROVED crossing refused
``[proved_answers_the_chart] verdict answers claiming chart`` because its verdict's ``validate_ref``
was the akiendell spelling ``C:\Users\akien\...\validate-...json`` while ``claiming_packets`` returned
that berth's commons copy, compared as literal strings. Over the commons mirror the four stage
judges red ``<x>_ref does not read as a <x> berth`` on all 168 berths whose ref names another box;
``chain.resolve_berth`` finds every copy. Prior sites of the shape: 1e99a571dd6d, 7cae18f7f9c2,
072a482e6dd7.

The world is a fixture: a scratch local chart store standing in for the default one and a scratch
commons mirror (``chain._commons_mirror`` pointed at it). Nothing live is read.

    PYTHONPATH=. python3 cairn/devices/codemother/machines/build_inspector/proofs/test_the_inspector_reads_a_far_box_berth_ref_by_its_commons_copy.py
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
    "5703d091eab6": {
        "1": "test_a_verdict_naming_a_far_box_validate_answers_its_commons_copy",
        "2": "test_each_stage_judge_reads_a_far_box_upstream_ref_by_its_commons_copy",
        "3": "test_a_local_ref_and_a_passed_root_read_as_before",
    },
}

_T = "f1x75703d091"   # a fixture ticket id; no live ticket carries it
_VAL = "validate-20261119T210906-0123456789ab.json"
_SPELLINGS = ("C:\\Users\\other\\.cairn\\devices\\chart\\0\\packets\\",
              "/home/somebody/.cairn/devices/chart/0/packets/")
_ABOUT = "verdict answers claiming chart"

# stage judged -> (its upstream ref field, the upstream stage, the upstream berth body, the packet)
_STAGES = {
    "decompose": ("survey_ref", "survey", {"holdings": [], "absences": []},
                  {"sub_problems": [{"what": "p", "why": "w", "kind": "build"}]}),
    "triage": ("decompose_ref", "decompose", {"sub_problems": [{"what": "p"}]},
               {"order": [{"what": "p", "why": "w"}]}),
    "hypothesize": ("triage_ref", "triage", {"order": [{"what": "p"}]},
                    {"hypotheses": [{"piece": "p", "expect": "e", "instrument": "`true`"}]}),
    "validate": ("hypothesize_ref", "hypothesize", {"hypotheses": [{"piece": "p"}]},
                 {"criteria": [{"claim": "c", "instrument": "`true`"}]}),
}


@contextmanager
def _world():
    from cairn.tools.chain import chain
    from cairn.devices.codemother.machines.build_inspector import inspector
    with tempfile.TemporaryDirectory() as tmp:
        local, mirror = Path(tmp) / "chart", Path(tmp) / "commons" / "berths" / "chart"
        (local / "0" / "packets").mkdir(parents=True)
        mirror.mkdir(parents=True)
        saved = (chain.BERTHS_ROOT, chain._commons_mirror, inspector._CHART_BERTHS)
        chain.BERTHS_ROOT, inspector._CHART_BERTHS = str(local), local
        chain._commons_mirror = lambda: str(mirror)
        chain._INDEX_CACHE.clear()
        try:
            yield {"local": local, "packets": local / "0" / "packets", "mirror": mirror, "I": inspector}
        finally:
            chain.BERTHS_ROOT, chain._commons_mirror, inspector._CHART_BERTHS = saved
            chain._INDEX_CACHE.clear()


def _write(path: Path, body: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")


def _verdict(validate_ref: str) -> dict:
    return {"ticket": _T, "validate_ref": validate_ref,
            "verdicts": [{"claim": "c", "instrument": "`true`", "outcome": "pass", "evidence": "fixture"}],
            "dispositions": [{"piece": "p", "expect": "e", "disposition": "confirmed", "by": "fixture"}]}


def _abouts(findings) -> list:
    return [f.get("about") for f in findings]


def test_a_verdict_naming_a_far_box_validate_answers_its_commons_copy():
    for spelling in _SPELLINGS:
        with _world() as w:
            _write(w["mirror"] / _VAL, {"ticket": _T, "hypothesize_ref": "fixture"})
            _write(w["packets"] / "verdict-20261119T223442-0123456789ab.json", _verdict(spelling + _VAL))
            got = w["I"].proved_answers_the_chart(_T)
            assert _ABOUT not in _abouts(got), (spelling, got)
    with _world() as w:  # a verdict naming ANOTHER berth still does not answer this chart
        _write(w["mirror"] / _VAL, {"ticket": _T, "hypothesize_ref": "fixture"})
        other = _SPELLINGS[0] + "validate-20261119T000000-ffffffffffff.json"
        _write(w["packets"] / "verdict-20261119T223442-0123456789ab.json", _verdict(other))
        assert _ABOUT in _abouts(w["I"].proved_answers_the_chart(_T)), "a wrong berth answered"


def _chain_reds(judge, packet) -> list:
    flat = [f for frag in judge(packet) for f in (frag.get("findings") or [frag])]
    return [f for f in flat if "does not read as" in (f.get("finding") or "")]


def test_each_stage_judge_reads_a_far_box_upstream_ref_by_its_commons_copy():
    for stage, (field, upstream, body, packet) in _STAGES.items():
        name = f"{upstream}-20261119T000000-0123456789ab.json"
        for spelling in _SPELLINGS:
            with _world() as w:
                judge = getattr(w["I"], f"judge_{stage}")
                _write(w["mirror"] / name, body)
                reds = _chain_reds(judge, dict(packet, **{field: spelling + name}))
                assert reds == [], (stage, spelling, reds)
                # no copy anywhere: still loud (Law 7)
                (w["mirror"] / name).unlink()
                assert _chain_reds(judge, dict(packet, **{field: spelling + name})), (stage, "silent")


def test_a_local_ref_and_a_passed_root_read_as_before():
    with _world() as w:  # a ref that resolves as written is read where it is
        for stage, (field, upstream, body, packet) in _STAGES.items():
            here = w["packets"] / f"{upstream}-20261119T000001-0123456789ab.json"
            _write(here, body)
            assert _chain_reds(getattr(w["I"], f"judge_{stage}"), dict(packet, **{field: str(here)})) == [], stage
        _write(w["packets"] / _VAL, {"ticket": _T, "hypothesize_ref": "fixture"})
        _write(w["packets"] / "verdict-20261119T223442-0123456789ab.json", _verdict(str(w["packets"] / _VAL)))
        assert _ABOUT not in _abouts(w["I"].proved_answers_the_chart(_T))
    with _world() as w:  # a passed root reads only itself: the mirror copy never answers it
        passed = w["local"].parent / "passed"
        _write(passed / "0" / "packets" / _VAL, {"ticket": _T, "hypothesize_ref": "fixture"})
        _write(passed / "0" / "packets" / "verdict-20261119T223442-0123456789ab.json",
               _verdict(_SPELLINGS[0] + _VAL))
        _write(w["mirror"] / _VAL, {"ticket": _T, "hypothesize_ref": "fixture"})
        got = w["I"].proved_answers_the_chart(_T, berths_root=passed)
        assert _ABOUT in _abouts(got), got


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
