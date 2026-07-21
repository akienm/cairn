"""Proof for charter/projector — ``state`` is COMPILED from ``history``, and cannot drift.

Teeth a hollow projector could not pass:

  - DERIVED, NOT AUTHORED (no drift, Law 1). The persisted ``state`` always equals a
    fresh projection of the persisted ``history``. Hand-corrupt the ``state`` sidecar and
    one more append restores the truth — a hollow build that trusted the on-disk state trips this.
  - BOUNDED BY CONSTRUCTION (Law 4). A count-N window holds at most N records no matter how
    long history grows — a hollow build that returned the whole log trips this.
  - APPEND-ONLY (Law 7). History only grows; a prior record is never rewritten. A hollow
    build that mutated in place trips the prefix check.
  - SINCE-GATE SELF-SIZES. The event-based window returns exactly the records since the last
    gate (inclusive) — a hollow build that ignored the gate marker trips this.
  - CURSOR TRACKS THE HEAD. Empty → no cursor; after appends → the latest record.

Self-contained and DB-free (pure charter logic); self-cleaning (a temp dir).

    python3 cairn/charter/proofs/test_projector.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.charter import projector


def test_state_is_derived_not_authored():
    with tempfile.TemporaryDirectory() as d:
        hp, sp = os.path.join(d, "h.json"), os.path.join(d, "s.json")
        for i in range(3):
            projector.append_entry(hp, sp, {"standing": f"step{i}"})
        # the persisted sidecar equals a fresh projection of the persisted history
        with open(sp, encoding="utf-8") as f:
            persisted = json.load(f)
        assert persisted == projector.project(projector.read_history(hp))
        # corrupt the sidecar by hand; ONE more append must restore the truth —
        # state is recomputed from history, so it cannot stay diverged.
        projector._atomic_write(sp, {"cursor": "LIES", "window": ["forged"], "count": 999})
        returned = projector.append_entry(hp, sp, {"standing": "step3"})
        with open(sp, encoding="utf-8") as f:
            after = json.load(f)
        assert after == returned == projector.project(projector.read_history(hp))
        assert after["cursor"]["standing"] == "step3"


def test_count_window_is_bounded():
    with tempfile.TemporaryDirectory() as d:
        hp, sp = os.path.join(d, "h.json"), os.path.join(d, "s.json")
        win = {"kind": "count", "n": 3}
        state = None
        for i in range(10):
            state = projector.append_entry(hp, sp, {"standing": f"s{i}"}, window=win)
        assert len(state["window"]) == 3, "a count-3 window must hold exactly 3, not 10"
        assert state["count"] == 10, "the full history length stays visible beyond the window"
        assert [r["standing"] for r in state["window"]] == ["s7", "s8", "s9"]


def test_history_is_append_only():
    with tempfile.TemporaryDirectory() as d:
        hp, sp = os.path.join(d, "h.json"), os.path.join(d, "s.json")
        projector.append_entry(hp, sp, {"standing": "first"})
        snapshot = projector.read_history(hp)
        projector.append_entry(hp, sp, {"standing": "second"})
        grown = projector.read_history(hp)
        assert grown[: len(snapshot)] == snapshot, "prior records must be untouched — history only grows"
        assert len(grown) == len(snapshot) + 1
        assert grown[0]["seq"] == 0 and grown[1]["seq"] == 1, "seq is monotonic"


def test_since_gate_window_self_sizes():
    with tempfile.TemporaryDirectory() as d:
        hp, sp = os.path.join(d, "h.json"), os.path.join(d, "s.json")
        win = {"kind": "since_gate"}
        projector.append_entry(hp, sp, {"standing": "a"}, window=win)
        projector.append_entry(hp, sp, {"standing": "b", "gate": True}, window=win)
        projector.append_entry(hp, sp, {"standing": "c"}, window=win)
        state = projector.append_entry(hp, sp, {"standing": "d"}, window=win)
        got = [r["standing"] for r in state["window"]]
        assert got == ["b", "c", "d"], f"since_gate must start at the last gate (inclusive), got {got}"


def test_cursor_tracks_the_head():
    assert projector.project([])["cursor"] is None
    history = projector.append(projector.append([], {"standing": "x"}), {"standing": "y"})
    cursor = projector.project(history)["cursor"]
    assert cursor["standing"] == "y" and cursor["seq"] == 1


def _main() -> int:
    checks = [
        test_state_is_derived_not_authored,
        test_count_window_is_bounded,
        test_history_is_append_only,
        test_since_gate_window_self_sizes,
        test_cursor_tracks_the_head,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — charter/projector: state is compiled from history, bounded, append-only, drift-free")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
