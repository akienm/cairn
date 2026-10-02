"""Proof for ticket 9fb045a476dc — a clean rehearsal stands over the ticket's DESIGN, not its cursor.

A clean record carries ``design_sha256``: the sha of the ticket with ``workflow_and_state`` and
``rehearsal`` removed. ``standing()`` compares that, so the cursor moving through the workflow
leaves the record standing and any edit to the design still makes it stale. A record written
before the change carries no ``design_sha256`` and falls back to the whole-bytes compare.

Fixtures are the sibling proof's (``test_rehearsal.World`` and friends) — a scratch commons
handed to the artifact door; no tooth reads the live commons or calls the live reader. The
machine is resolved at CALL time inside each tooth, so a reverted build reds teeth instead of
killing the import.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.artifact import artifact as door                                   # noqa: E402
from cairn.machines.rehearsal.proofs.test_rehearsal import World, Stub, CLEAN_TREE, TID, _kw  # noqa: E402

PROVES = {
    "9fb045a476dc": {
        "1": "test_a_cursor_move_leaves_the_record_standing",
        "2": "test_a_design_edit_makes_the_record_stale",
        "3": "test_a_pre_change_record_still_stands_on_the_whole_bytes",
        "4": "test_a_clean_record_carries_design_sha256",
    },
}

MOVED = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
STALE = "the ticket was edited after its rehearsal — rehearse again"


def _R():
    return importlib.import_module("cairn.machines.rehearsal.rehearsal")


def _clean(w):
    R = _R()
    rec = R.rehearse(TID, reader=Stub([CLEAN_TREE]), **_kw(w))
    assert rec["clean"], rec
    assert R.standing(TID, w.commons)["ok"], R.standing(TID, w.commons)
    return rec


def _move_cursor(w):
    doc = json.loads(w.ticket.read_text())
    doc["workflow_and_state"] = (doc["workflow_and_state"]
                                 .replace("[BUILDME:waiting]", "BUILDME")
                                 .replace("-> PROVEME ->", "-> [PROVEME] ->"))
    assert doc["workflow_and_state"] == MOVED, doc["workflow_and_state"]
    door.write(str(w.ticket), json.dumps(doc, indent=2) + "\n", verb="cast", why="fixture cursor move")


def test_a_cursor_move_leaves_the_record_standing():
    w = World()
    try:
        _clean(w)
        _move_cursor(w)
        st = _R().standing(TID, w.commons)
        assert st["ok"] is True, st
    finally:
        w.close()


def test_a_design_edit_makes_the_record_stale():
    w = World()
    try:
        _clean(w)
        doc = json.loads(w.ticket.read_text())
        doc["decisions"].append({"n": 3, "text": "a new decision", "by": "the proof"})
        door.write(str(w.ticket), json.dumps(doc, indent=2) + "\n", verb="cast", why="fixture design edit")
        st = _R().standing(TID, w.commons)
        assert st["ok"] is False, st
        assert st.get("lack") == STALE, st
    finally:
        w.close()


def test_a_pre_change_record_still_stands_on_the_whole_bytes():
    w = World()
    try:
        rec = _clean(w)
        p = w.commons / rec["record"]
        d = json.loads(p.read_text())
        d.pop("design_sha256", None)
        door.write(str(p), json.dumps(d, indent=2) + "\n", verb="rehearse", why="fixture pre-change record")
        R = _R()
        st = R.standing(TID, w.commons)
        assert st["ok"] is True, st
        _move_cursor(w)
        st = R.standing(TID, w.commons)
        assert st["ok"] is False, st
    finally:
        w.close()


def test_a_clean_record_carries_design_sha256():
    w = World()
    try:
        rec = _clean(w)
        design_sha = getattr(_R(), "design_sha")
        assert rec.get("design_sha256") == design_sha(w.ticket.read_bytes()), rec.get("design_sha256")
    finally:
        w.close()


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    failed = []
    for tooth in teeth:
        try:
            tooth()
        except Exception as e:                       # noqa: BLE001 — the reason is the record
            failed.append(tooth.__name__)
            print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {str(e)[:300]}")
            continue
        print(f"  PASS  {tooth.__name__}")
    if failed:
        print(f"red — {len(failed)} of {len(teeth)} teeth: {', '.join(failed)}")
        return 1
    print(f"green — {len(teeth)} teeth: a clean rehearsal stands over the design, a cursor move "
          "leaves it standing, a design edit makes it stale, and a pre-change record still stands "
          "on the whole bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
