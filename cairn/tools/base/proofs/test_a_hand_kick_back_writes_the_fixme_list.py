"""Proof: a hand kick-back into FIXME writes the ticket's fixme list.

Ticket 44cc43080f93. Measured 2026-10-29 on 7a31059daa23: a hand ``emit(..., "FIXME",
missing=[...])`` journaled ``missing`` and left the ticket with no ``fixme`` list, so the
crossing back out refused (FixmeGateRed) for a reason nobody had written. Only clearance
wrote the list. Now emit writes it, after the journal, on any back-edge into a repair summons
that names a ticket; clearance passes ``write_fixme=False`` because it writes its own list
with the lack kinds (its tooth beside it, in harbor_master/proofs/test_clearance.py, counts
that it is written exactly once).

One tooth for the one falsifier clause:

  all. A hand emit into FIXME with missing=['a','b'] over a scratch ticket store leaves
       fixme [{n:1,...'a'},{n:2,...'b'}], replacing a list already there; the same crossing
       with write_fixme=False leaves the ticket untouched, and the flag is never journaled.

The fixture node-class root is a COPY of the live code-seam.json with the repair summons set
in the copy, so the proof measures emit, not the live class. Build names are resolved inside
the tooth, so a reverted build reds the tooth instead of crashing the import.

    python3 cairn/tools/base/proofs/test_a_hand_kick_back_writes_the_fixme_list.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.base import transitions  # noqa: E402
from cairn.tools.base import ticket_file  # noqa: E402

PROVES = {
    "44cc43080f93": {
        "all": "test_a_hand_kick_back_writes_the_fixme_list",
    },
}

# Read where hollow.py reads the commons: beside the repo when it is there, else at the home
# path (a hollow worktree in /tmp has no commons beside it).
_COMMONS_CLASSES = (transitions._NODE_CLASSES if transitions._NODE_CLASSES.is_dir()
                    else Path.home() / "dev" / "src" / "CairnCommons" / "node_classes")
_AT_PROVEME = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
_TID = "a0fixme0hand"


def _class_root() -> Path:
    d = json.loads((_COMMONS_CLASSES / "code-seam.json").read_text(encoding="utf-8"))
    d["workflow_versions"]["v2"]["repair_summons"] = {"FIXME": "BUILDME"}
    root = scratch_dir("hand_kickback_fixture_node_classes_")
    (root / "code-seam.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    return root


def _component() -> tuple[str, str]:
    # Nested one level: the build gate censuses the parent of the directory holding history.json.
    comp = scratch_dir("hand_kickback_fixture_component_") / "comp"
    comp.mkdir()
    return str(comp / "history.json"), str(comp / "state.json")


def _kick_back(**flag) -> tuple[dict, list[dict]]:
    """One hand kick-back over a scratch ticket store holding a ticket with an OLD list."""
    from cairn.tools.base.transitions import emit
    from cairn.tools.charter import projector
    tickets = scratch_dir("hand_kickback_fixture_tickets_")
    plan = tickets / f"{_TID}-a-fixture-boat-kicked-back-by-hand.json"
    plan.write_text(json.dumps({"id": _TID, "workflow_and_state": _AT_PROVEME,
                                "fixme": [{"n": 1, "kind": "old", "missing": "stale"}]},
                               indent=2) + "\n", encoding="utf-8")
    hist, state = _component()
    saved = ticket_file._TICKETS
    ticket_file._TICKETS = tickets
    try:
        emit(_AT_PROVEME, "FIXME", history_path=hist, state_path=state,
             node_class_root=_class_root(), ticket=_TID, missing=["a", "b"], **flag)
        doc = ticket_file.read_ticket(plan)
    finally:
        ticket_file._TICKETS = saved
    return doc, projector.read_history(hist)


def test_a_hand_kick_back_writes_the_fixme_list():
    doc, journal = _kick_back()
    assert doc.get("fixme") == [{"n": 1, "kind": "hand_kickback", "missing": "a"},
                                {"n": 2, "kind": "hand_kickback", "missing": "b"}], doc.get("fixme")
    assert journal and journal[-1].get("to") == "FIXME", journal
    assert "write_fixme" not in journal[-1], journal[-1]
    quiet, journal = _kick_back(write_fixme=False)
    assert quiet.get("fixme") == [{"n": 1, "kind": "old", "missing": "stale"}], quiet.get("fixme")
    assert "write_fixme" not in journal[-1], journal[-1]


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
