"""The build_inspector teeth that sweep the REAL tree, moved out of test_inspector.py (ticket
e7d244d66bd7) so that each file finishes well inside the verdict door's 600 s bound.

MEASURED 2026-11-14 on akiendelllinux (bin/cairn test, per-tooth wall times printed by
test_inspector.py's _Teeth): of 564 s, tooth 11 (a whole-tree ``inspect()``) took 233 s and THE
GRADATION (a second whole-tree ``inspect()`` of the same tree) took 223 s. Both teeth judge one
sweep, so here they share ONE sweep: the claims are unchanged and the cost is halved.

Invariants only, never a snapshot of findings (memory: proof-over-live-data-assert-invariants).

  test_the_real_tree_sweep_runs_sees_the_tree_and_exits_gateably: tooth 11, as it stood;
  test_the_gradation_scores_every_sieve_that_ran_and_rolls_up_by_min: THE GRADATION and BY
     ADDRESS, NOT BY NAME, as they stood.

    bin/cairn test cairn/machines/build_inspector/proofs/test_inspector_over_the_real_tree.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector import inspector as _insp  # noqa: E402

# This bound catches a HANG, it does not enforce speed: one whole-tree sweep measured 291 s on the Dell
# (2026-11-14), and the hollow reading's 120 s default would kill it with no tooth read. About 2x that
# measured max, so a slow day (a reseal alongside) reads as slow, not as a kill; and still under the verdict
# door's 600 s, so a real hang is killed by this file's own bound and named here, before the door times out.
PROOF_TIMEOUT_S = 560

_REAL: dict = {}


def _real() -> dict:
    """The one sweep both teeth judge, taken on first use."""
    if not _REAL:
        _REAL.update(_insp.inspect())
    return _REAL


def test_the_real_tree_sweep_runs_sees_the_tree_and_exits_gateably():
    real = _real()
    assert real["components_inspected"] >= 10, "the sweep barely saw the tree"
    assert real["sieves_run"] == sorted(_insp.SIEVES)
    for x in real["findings"]:
        assert set(x) - {"values"} == _insp.FINDING_SHAPE, x
    assert real["clean"] == (not real["findings"])


def test_the_gradation_scores_every_sieve_that_ran_and_rolls_up_by_min():
    rep, sieves = _real(), _insp.SIEVES
    assert rep["gradation"], "the sweep graded no component — every check below would be vacuous"
    for comp, scores in rep["gradation"].items():
        assert set(scores) == set(sieves), \
            f"{comp}: the gradation must score every sieve the nest shook, not a subset"
        assert set(scores.values()) <= {0.0, 1.0}, \
            f"{comp}: sieves are binary today, as floats — a third value is not the design"
        assert rep["component_scores"][comp] == min(scores.values()), (
            "the roll-up is min() — one zero sinks the component, and a pile of passes "
            "may not buy past a real catch")
    # BY ADDRESS, NOT BY NAME (2026-08-13). The gradation is keyed by the component's dir
    # because two components answer to "orient"; correlating on the bare name here would
    # either KeyError (as it did the day the builder device landed) or, worse, silently match
    # the wrong subject's row and pronounce the pairing sound.
    for f in rep["findings"]:
        assert rep["gradation"][f["at"]][f["method"]] == 0.0, f
    for comp, scores in rep["gradation"].items():
        for name, s in scores.items():
            if s == 1.0:
                assert not any(f["method"] == name and f["at"] == comp
                               for f in rep["findings"]), \
                    ("a sieve scored 1.0 while emitting a finding — the score and "
                     "the finding are two faces of one judgement and cannot disagree")
    assert {f["method"] for f in rep["findings"]} <= set(sieves)


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
