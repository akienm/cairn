"""Proof: a hand crossing through cross() into FIXME leaves the fixme list on the ticket.

Ticket 5a2a8f45177a. Measured 2026-11-02: ``cross(<id>, "FIXME", missing=["a","b"])`` moved
the cursor to ``[FIXME:waiting]`` and left ``fixme`` None. emit wrote the list (44cc43080f93),
then cross() rewrote the copy of the ticket it had read BEFORE emit, and the list was gone.
cross() now re-reads the ticket after emit and sets the cursor on the fresh doc.

Three teeth, one per falsifier clause:

  1. cross into FIXME with missing a,b leaves fixme [{n:1,hand_kickback,a},{n:2,...,b}] and
     the cursor at FIXME.
  2. cross into FIXME with no missing refuses (IllegalTransition), and the ticket's bytes and
     the component's history.json are unchanged.
  3. cross from PROVEME back to BUILDME (not a repair summons) writes no fixme key.

Each tooth runs over a scratch ticket store with ticket_file._TICKETS repointed and restored
in finally, and a COPY of the live code-seam.json with the repair summons set in the copy, so
the proof measures cross(), not the live class or the live store. cross is resolved inside
the tooth, so a reverted build reds the tooth instead of crashing the import.

    python3 cairn/tools/base/proofs/test_a_hand_crossing_into_fixme_writes_its_list.py
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
    "5a2a8f45177a": {
        "1": "test_a_hand_crossing_into_fixme_writes_its_list",
        "2": "test_a_crossing_into_fixme_without_missing_writes_nothing",
        "3": "test_a_back_edge_to_buildme_writes_no_fixme",
    },
}

# Read where hollow.py reads the commons: beside the repo when it is there, else at the home
# path (a hollow worktree in /tmp has no commons beside it).
_COMMONS_CLASSES = (transitions._NODE_CLASSES if transitions._NODE_CLASSES.is_dir()
                    else Path.home() / "dev" / "src" / "CairnCommons" / "node_classes")
_COMMONS_TICKETS = (ticket_file._TICKETS if ticket_file._TICKETS.is_dir()
                    else Path.home() / "dev" / "src" / "CairnCommons" / "tickets")
_AT_PROVEME = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
_TID = "a0crossfixme"


def _world() -> tuple[Path, Path, Path, Path]:
    """A scratch commons: node-class copy, ticket store with one ticket at PROVEME, component."""
    d = json.loads((_COMMONS_CLASSES / "code-seam.json").read_text(encoding="utf-8"))
    d["workflow_versions"]["v2"]["repair_summons"] = {"FIXME": "BUILDME"}
    ncr = scratch_dir("hand_crossing_fixture_node_classes_")
    (ncr / "code-seam.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    commons = scratch_dir("hand_crossing_fixture_commons_")
    tickets = commons / "tickets"
    tickets.mkdir()
    (tickets / "_charter+why.json").write_bytes((_COMMONS_TICKETS / "_charter+why.json").read_bytes())
    comp = commons / "comp"
    comp.mkdir()
    (comp / ("intention+" + "why.json")).write_text("{}", encoding="utf-8")
    plan = tickets / f"{_TID}-a-fixture-boat-crossed-by-hand.json"
    plan.write_text(json.dumps({"id": _TID, "owning_intention": "comp/intention+" + "why.json",
                                "workflow_and_state": _AT_PROVEME}, indent=2) + "\n",
                    encoding="utf-8")
    return ncr, commons, tickets, plan


def _cross(target: str, **kw):
    """One cross() over a fresh scratch world; returns (result or exception, plan, commons)."""
    from cairn.tools.base.cross import cross
    ncr, commons, tickets, plan = _world()
    saved = ticket_file._TICKETS
    ticket_file._TICKETS = tickets
    try:
        before = plan.read_bytes()
        try:
            out = cross(_TID, target, actor="cc", why="proof", tickets_dir=tickets,
                        node_class_root=ncr, commons_root=commons, repo_root=commons, **kw)
        except Exception as e:  # noqa: BLE001 — tooth 2 measures the refusal itself
            out = e
        return out, before, ticket_file.read_ticket(plan), plan, commons
    finally:
        ticket_file._TICKETS = saved


def test_a_hand_crossing_into_fixme_writes_its_list():
    out, _, doc, _, _ = _cross("FIXME", missing=["a", "b"])
    assert isinstance(out, str), out
    assert "[FIXME" in doc["workflow_and_state"], doc["workflow_and_state"]
    assert doc.get("fixme") == [{"n": 1, "kind": "hand_kickback", "missing": "a"},
                                {"n": 2, "kind": "hand_kickback", "missing": "b"}], doc.get("fixme")


def test_a_crossing_into_fixme_without_missing_writes_nothing():
    out, before, _, plan, commons = _cross("FIXME")
    assert isinstance(out, transitions.IllegalTransition), out
    assert plan.read_bytes() == before
    hist = commons / "comp" / "history.json"
    assert not hist.exists() or json.loads(hist.read_text(encoding="utf-8") or "[]") in ([], {}), \
        hist.read_text(encoding="utf-8")


def test_a_back_edge_to_buildme_writes_no_fixme():
    out, _, doc, _, _ = _cross("BUILDME")
    assert isinstance(out, str), out
    assert "[BUILDME" in doc["workflow_and_state"], doc["workflow_and_state"]
    assert "fixme" not in doc, doc.get("fixme")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
