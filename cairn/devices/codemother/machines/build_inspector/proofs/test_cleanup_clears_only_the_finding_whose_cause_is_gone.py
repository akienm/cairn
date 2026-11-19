"""Proof for ticket 95557c2ed44f: cairn cleanup re-runs the sieve behind each standing finding
trouble over the whole repo, and clears only the troubles whose cause is gone.

Measured 2026-11-16: nothing schedules the build inspector's whole-repo sweep, and since ticket
044020db63c0 a one-component run never clears. So inspector-new-finding-history-integrity stood
after 74b4209b71ee's dirt was committed (17b738522), until a hand ran the 5m25s sweep and
``cairn trouble drain``. ``cairn cleanup`` ends every voyage, and a voyage ending is when a fix
lands; until now its one step was the drain.

  1. a scratch world holds one cleared cause and one standing cause: the recheck clears only the
     cleared cause's trouble, by its exact identity, and leaves the standing one;
  2. the recheck runs only the sieves the troubles name, each over every component, never the
     rest of the nest;
  3. the rule is the whole-repo reconcile's: a sieve that fires only at a baselined site clears,
     and an identity naming no registered sieve is left standing and reported;

Clause 4 (``cairn cleanup`` hands the recheck the standing ids, before the drain) is bin's, and
its tooth berths there: bin/proofs/test_cleanup_rechecks_the_standing_findings_first.py.

The world: a scratch root with two testing component dirs, the census and the sieve registry
answering from a script, and a recorder for a raiser, so nothing reaches the live trouble lane.

    python3 cairn/devices/codemother/machines/build_inspector/proofs/test_cleanup_clears_only_the_finding_whose_cause_is_gone.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"95557c2ed44f": {
    "1": "test_only_the_cleared_causes_trouble_goes",
    "2": "test_only_the_named_sieves_run_over_every_component",
    "3": "test_the_rule_is_the_whole_repo_reconciles"}}

_A, _B = "tools/testing-9555a", "devices/testing-9555b"


class _Recorder:
    def __init__(self):
        self.cleared, self.raised, self.reconciled = [], [], []

    def clear_trouble(self, identity, **kw):
        self.cleared.append(identity)

    def raise_trouble(self, identity, **kw):
        self.raised.append(identity)

    def reconcile_troubles(self, prefix, still, **kw):
        self.reconciled.append(prefix)


def _cause_sieve(name: str, calls: list):
    """A testing sieve that fires at a component whose dir holds the file testing-cause-<name>."""
    def sieve(row, comp_dir):
        calls.append((name, row["dir"]))
        if (Path(comp_dir) / f"testing-cause-{name}").exists():
            return [{"method": name, "component": row["component"], "values": {"reason": "testing"}}]
        return []
    return sieve


def _recheck(ids, *, causes, known=()):
    """Run inspector.recheck(ids) over a scratch world. ``causes`` is {sieve: [dirs it fires at]};
    ``known`` is baselined (sieve, dir) pairs. Returns (result, recorder, calls)."""
    from cairn.devices.codemother.machines.build_inspector import inspector as mod
    root = scratch_dir("testing-9555-world-")
    for d in (_A, _B):
        (root / d).mkdir(parents=True)
    for name, dirs in causes.items():
        for d in dirs:
            (root / d / f"testing-cause-{name}").write_text("testing\n", encoding="utf-8")
    baseline = root / "finding_baseline.json"
    baseline.write_text(json.dumps({"known": [{"method": m, "at": a} for m, a in known],
                                    "updated": "2026-11-16"}), encoding="utf-8")
    rows = [{"component": Path(d).name, "dir": d} for d in (_A, _B)]
    calls, rec = [], _Recorder()
    sieves = {n: _cause_sieve(n, calls) for n in ("testing_cleared", "testing_standing", "testing_idle")}
    saved = mod.SIEVES, mod.device_census, mod._raiser
    mod.SIEVES = sieves
    mod.device_census = lambda root=None: {"measured": {"components": rows}}
    mod._raiser = lambda: rec
    try:
        result = mod.recheck(ids, root=root, baseline_path=baseline)
    finally:
        mod.SIEVES, mod.device_census, mod._raiser = saved
    return result, rec, calls


def _id(name: str) -> str:
    from cairn.devices.codemother.machines.build_inspector.inspector import _finding_trouble_id
    return _finding_trouble_id(name)


def test_only_the_cleared_causes_trouble_goes():
    ids = [_id("testing_cleared"), _id("testing_standing")]
    result, rec, _ = _recheck(ids, causes={"testing_standing": [_B]})
    assert rec.cleared == [_id("testing_cleared")], (
        f"the recheck cleared {rec.cleared}, want only {_id('testing_cleared')} (its cause is gone; "
        f"testing_standing still fires at {_B})")
    assert result["standing"] == [_id("testing_standing")], result
    assert rec.reconciled == [], f"the recheck reconciled a prefix {rec.reconciled}; a clear names its identity"


def test_only_the_named_sieves_run_over_every_component():
    _, _, calls = _recheck([_id("testing_cleared")], causes={"testing_idle": [_A]})
    assert {n for n, _ in calls} == {"testing_cleared"}, f"sieves run: {sorted({n for n, _ in calls})}"
    assert sorted(d for _, d in calls) == sorted([_A, _B]), f"components visited: {calls}"


def test_the_rule_is_the_whole_repo_reconciles():
    ids = [_id("testing_standing"), "inspector-new-finding-testing-no-such-sieve"]
    result, rec, _ = _recheck(ids, causes={"testing_standing": [_B]},
                              known=[("testing_standing", _B)])
    assert rec.cleared == [_id("testing_standing")], (
        f"a sieve firing only at a baselined site was not cleared: {rec.cleared}")
    assert result["unknown"] == ["inspector-new-finding-testing-no-such-sieve"], result
    assert "inspector-new-finding-testing-no-such-sieve" not in rec.cleared


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
