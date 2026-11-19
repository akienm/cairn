"""Proof for ticket 044020db63c0: a one-component inspector run clears no finding trouble.

Measured 2026-11-16 by reading origin/main: ``python3 -m cairn.devices.codemother.machines.build_inspector.inspector
<component>`` narrows ``inspect`` to that component's census row (inspector.py, ``inspect``:
``rows = [r for r in rows if r["component"] == component]``), then hands the narrowed findings to
``_reconcile_cleared_findings``, which reconciles the whole ``inspector-new-finding-`` prefix. A
finding trouble is one per SIEVE (ticket cd27b72ba964), its components riding the detail, so a
sieve still firing at another component is absent from the narrowed set and its trouble is
cleared, though its cause still stands. A trouble cleared while its cause stands is quiet and
wrong (Law 7). Only a run that saw every component can say a sieve no longer fires anywhere.

  1. a one-component run tells trouble nothing about what stands: no reconcile is emitted, so
     the trouble of a sieve firing at another component is left standing;
  2. the whole-repo run still reconciles, handing trouble every sieve above baseline;
  3. a one-component run still raises the trouble of its own above-baseline finding.

The world: ``inspect`` answers from a script (narrowed by component as the real one is), the
baseline is an empty scratch file, and the raiser is a recorder, so nothing reaches the live
trouble lane.

    python3 cairn/devices/codemother/machines/build_inspector/proofs/test_a_one_component_run_clears_no_other_components_trouble.py
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"044020db63c0": {
    "1": "test_a_one_component_run_emits_no_reconcile",
    "2": "test_the_whole_repo_run_still_reconciles",
    "3": "test_a_one_component_run_still_raises_its_own_finding"}}

_HERE = {"method": "component_color", "at": "tools/testing-044a", "values": {"reason": "testing"}}
_THERE = {"method": "encapsulation_holds", "at": "devices/testing-044b", "values": {"reason": "testing"}}
_FINDINGS = [_HERE, _THERE]


class _Recorder:
    def __init__(self):
        self.raised, self.reconciled = [], []

    def raise_trouble(self, identity, **kw):
        self.raised.append(identity)

    def reconcile_troubles(self, prefix, still, **kw):
        self.reconciled.append((prefix, sorted(still)))


def _run(argv: list[str]) -> _Recorder:
    from cairn.devices.codemother.machines.build_inspector import inspector as mod
    from cairn.tools.scratch.scratch import scratch_dir
    baseline = scratch_dir("testing-044a-baseline-") / "finding_baseline.json"
    baseline.write_text(json.dumps({"known": [], "updated": "2026-11-16"}), encoding="utf-8")
    rec = _Recorder()

    def inspect(*, component=None, **kw):
        found = [f for f in _FINDINGS if component is None or f["at"] == component]
        return {"findings": found, "gate": {"opens": not found}}

    saved = mod.inspect, mod._raiser, mod._BASELINE_PATH
    mod.inspect, mod._raiser, mod._BASELINE_PATH = inspect, (lambda: rec), baseline
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            mod._main(argv)
    finally:
        mod.inspect, mod._raiser, mod._BASELINE_PATH = saved
    return rec


def _id(f: dict) -> str:
    from cairn.devices.codemother.machines.build_inspector.inspector import _finding_trouble_id
    return _finding_trouble_id(f["method"])


def test_a_one_component_run_emits_no_reconcile():
    rec = _run([_HERE["at"]])
    assert rec.reconciled == [], (
        f"a run over {_HERE['at']} alone told trouble only {rec.reconciled} stand, so "
        f"{_id(_THERE)} (still firing at {_THERE['at']}) would be cleared")


def test_the_whole_repo_run_still_reconciles():
    rec = _run([])
    want = ("inspector-new-finding-", sorted({_id(_HERE), _id(_THERE)}))
    assert rec.reconciled == [want], f"the whole-repo run reconciled {rec.reconciled}, want [{want}]"


def test_a_one_component_run_still_raises_its_own_finding():
    rec = _run([_HERE["at"]])
    assert rec.raised == [_id(_HERE)], f"a one-component run raised {rec.raised}, want [{_id(_HERE)}]"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
