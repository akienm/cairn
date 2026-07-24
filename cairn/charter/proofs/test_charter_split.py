"""Proof: the charter-state-history split is FAITHFUL for every real component that has taken it.

Child a (projector.py) proved the MECHANISM against synthetic histories. This proves the
mechanism holds IN SITU — for the actual components migrated (charter-state-history-split child c):
the persisted `state.json` beside a component is exactly `project(history.json)` (it cannot have
drifted — Law 1), and the migrated charter carries NO `state` FIELD (the split is real — the
operational voyage moved to the sidecars, the charter is pure intention+why).

This proof SCANS — it finds every component with a `history.json` and checks it. So it is not
pinned to one component: as each further charter migrates, this same proof covers it automatically,
and a hand-edited (drifted) `state.json` or a charter that keeps a `state` field turns it red.

Non-hollow floor: at least ONE component must be split (the horizon of the split — "at least one
live component runs on state+history with a projector"). A green over zero components would be a
hollow pass, so an empty scan is itself a red.

Deliberately dependency-light: pure file reads + the projector's pure core. Runs bare.

    python3 cairn/charter/proofs/test_charter_split.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.charter import projector

_CAIRN = _REPO_ROOT / "cairn"


def _split_components() -> list[Path]:
    """Every component directory that has taken the split (carries a history.json)."""
    return sorted(p.parent for p in _CAIRN.glob("*/history.json"))


def test_at_least_one_component_is_split():
    comps = _split_components()
    assert comps, ("no component carries a history.json — the split has zero live subjects; "
                   "a green here would be hollow (the horizon needs at least one real split)")
    print(f"    ({len(comps)} split: {', '.join(c.name for c in comps)})")


def test_state_is_exactly_the_projection_of_history_no_drift():
    for comp in _split_components():
        history = projector.read_history(str(comp / "history.json"))
        persisted = json.loads((comp / "state.json").read_text(encoding="utf-8"))
        assert persisted == projector.project(history), (
            f"{comp.name}: state.json DRIFTED from project(history) — the window is a second copy "
            f"someone maintained, not a projection (the defect the split exists to kill, Law 1)")


def test_history_is_append_only_shape_monotonic_seq_from_zero():
    for comp in _split_components():
        history = projector.read_history(str(comp / "history.json"))
        seqs = [r.get("seq") for r in history]
        assert seqs == list(range(len(history))), (
            f"{comp.name}: history seq is not a monotonic 0..n — it was not grown through the "
            f"append door (Law 7: a record of truth is only appended)")


def test_the_migrated_charter_is_pure_intention_why_no_state_field():
    for comp in _split_components():
        charter = json.loads((comp / "intention+why.json").read_text(encoding="utf-8"))
        assert "state" not in charter, (
            f"{comp.name}: the charter still carries a `state` FIELD — the split is not real; the "
            f"charter must be pure intention+why (the mutable voyage lives in state.json/history.json)")


def _main() -> int:
    checks = [
        test_at_least_one_component_is_split,
        test_state_is_exactly_the_projection_of_history_no_drift,
        test_history_is_append_only_shape_monotonic_seq_from_zero,
        test_the_migrated_charter_is_pure_intention_why_no_state_field,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the charter-state-history split is faithful in situ: every split component's "
          "state.json is exactly project(history.json) (no drift, Law 1), its history is append-only "
          "(Law 7), and its charter is pure intention+why (the split is real)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
