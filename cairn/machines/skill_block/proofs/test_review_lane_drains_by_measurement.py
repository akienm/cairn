"""Proof for the measured review lane (ticket fb988505c5cb, 2026-09-15) — teeth a hollow
predicate could not pass.

THE CLAIM. ``pending_reviews`` drops every berth whose ticket rests at a terminal cursor,
read from the TICKET side: ``intent_berth`` / ``sorted_berth`` are berth paths on the
ticket, and ``from_idea`` is an idea id whose FILE under ideas/ carries ``berth`` — the
idea berth doc itself records no idea id, so the join goes ticket → ideas/<id>.json →
berth, never through a field on the berth (D3's second sentence corrected here, on the
record the tooth reads). The cursor is read through ``transitions.parse_workflow`` and
terminality through ``transitions.is_terminal``; ANY terminal ticket drains a berth
several tickets name (Akien, open-d0a5003c404a). Nothing is written: the reviewed log
is his voice (Law 6) and its bytes are compared before and after every read.

ISOLATION. Every call runs against a scratch berth root, a scratch reviewed log, a scratch
tickets dir and a scratch ideas dir, all passed as parameters or through
``CAIRN_ARTIFACT_ROOTS``; the live commons and the live berths are never read (memory
hollow-worktree-has-no-commons-beside: a proof crossing the live world is a live fire
inside a proof).

    python3 cairn/machines/skill_block/proofs/test_review_lane_drains_by_measurement.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.machines.skill_block import skill_block as sb  # noqa: E402
from cairn.tools.base import transitions  # noqa: E402
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

WF = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> {cursor}"


def _wf(state: str, phase: str | None = "waiting") -> str:
    """A code-seam@v2 string with the cursor at ``state`` — rendered by hand only as far as
    the grammar needs; ``parse_workflow`` is what the reader runs, so a string it rejects
    is a tooth failing loudly rather than a berth quietly kept."""
    if state == "PROVED":
        return "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]"
    path = ["THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"]
    tok = f"[{state}:{phase}]" if phase else f"[{state}]"
    return "code-seam@v2: " + " -> ".join(tok if s == state else s for s in path)


class World:
    """One scratch world: berths/, reviewed.jsonl, tickets/, ideas/."""

    def __init__(self):
        self.root = scratch_dir("review-lane-drain-proof-")
        self.berths = self.root / "berths"
        self.reviewed = self.root / "reviewed.jsonl"
        self.tickets = self.root / "tickets"
        self.ideas = self.root / "ideas"
        for d in (self.berths / "intent", self.berths / "sorted", self.berths / "idea",
                  self.tickets, self.ideas):
            d.mkdir(parents=True)
        self.reviewed.write_text('{"berth_id": "already-reviewed-0000", "when": "x", "words": "ok"}\n')

    def berth(self, skill: str, fid: str) -> Path:
        p = self.berths / skill / f"{skill}-20260915T000000-{fid}.json"
        p.write_text(json.dumps({"skill": skill, "finding_id": fid, "title": fid,
                                 "when": "2026-09-15T00:00:00", "exit": "routed_forward",
                                 "bullets": [], "answers": {}}))
        return p

    def ticket(self, tid: str, state: str, *, intent: Path | None = None,
               sorted_: Path | None = None, from_idea: str | None = None,
               raw: str | None = None) -> Path:
        p = self.tickets / f"{tid}-a-scratch-ticket.json"
        if raw is not None:
            p.write_text(raw)
            return p
        doc = {"id": tid, "workflow_and_state": _wf(state),
               "intent_berth": str(intent) if intent else "none, because scratch",
               "sorted_berth": str(sorted_) if sorted_ else "none, because scratch"}
        if from_idea is not None:
            doc["from_idea"] = from_idea
        p.write_text(json.dumps(doc))
        return p

    def idea(self, iid: str, berth: Path | None, *, raw: str | None = None) -> Path:
        p = self.ideas / f"{iid}.json"
        p.write_text(raw if raw is not None else json.dumps({"id": iid, "berth": str(berth)}))
        return p

    def lane(self, **kw) -> list[str]:
        rows = sb.pending_reviews(root=self.berths, reviewed_path=self.reviewed,
                                  tickets=self.tickets, ideas=self.ideas, **kw)
        return sorted(r["berth_id"] for r in rows)

    def reviewed_sha(self) -> str:
        return hashlib.sha256(self.reviewed.read_bytes()).hexdigest()


def standard_world() -> World:
    """The four-berth world every lane tooth reads:
      proved-intent   named by a [PROVED] ticket        → drains
      buildme-sorted  named by a [BUILDME] ticket       → stays
      unnamed-intent  named by no ticket                → stays
      broken-sorted   named only by an unreadable ticket → stays (Law 7)"""
    w = World()
    pi = w.berth("intent", "proved-intent")
    bs = w.berth("sorted", "buildme-sorted")
    w.berth("intent", "unnamed-intent")
    br = w.berth("sorted", "broken-sorted")
    w.ticket("aaaa00000001", "PROVED", intent=pi)
    w.ticket("bbbb00000002", "BUILDME", sorted_=bs)
    w.ticket("cccc00000003", "PROVED", raw='{"workflow_and_state": "code-seam@v2: [PROVED]", "sorted_berth": "%s"' % br)
    return w


# ── the map ───────────────────────────────────────────────────────────────────

def test_map_reads_the_cursor_state_for_each_named_berth():
    w = World()
    x = w.berth("intent", "x")
    y = w.berth("idea", "y")
    w.idea("idea-one", y)
    w.ticket("aaaa00000001", "PROVED", intent=x, from_idea="idea-one")
    m = sb.berth_ticket_cursors(tickets=w.tickets, ideas=w.ideas)
    assert m == {str(x.resolve()): ["PROVED"], str(y.resolve()): ["PROVED"]}, m


def test_map_joins_the_idea_berth_through_the_idea_file_not_the_berth_doc():
    """D3 corrected: the berth doc carries no idea id; ideas/<id>.json carries ``berth``.
    A ticket whose idea file is missing contributes nothing for the idea berth."""
    w = World()
    y = w.berth("idea", "y")
    w.ticket("aaaa00000001", "PROVED", from_idea="idea-that-has-no-file")
    assert sb.berth_ticket_cursors(tickets=w.tickets, ideas=w.ideas) == {}
    w.idea("idea-that-has-no-file", y)
    m = sb.berth_ticket_cursors(tickets=w.tickets, ideas=w.ideas)
    assert m == {str(y.resolve()): ["PROVED"]}, m


def test_map_accepts_a_from_idea_that_is_a_path_to_the_idea_file():
    """Eight older tickets carry a path, not an id (census 2026-09-15)."""
    w = World()
    y = w.berth("idea", "y")
    ip = w.idea("idea-two", y)
    w.ticket("aaaa00000001", "PROVED", from_idea=str(ip))
    m = sb.berth_ticket_cursors(tickets=w.tickets, ideas=w.ideas)
    assert m == {str(y.resolve()): ["PROVED"]}, m


def test_map_skips_an_unreadable_ticket_and_an_unparseable_cursor():
    w = World()
    x = w.berth("intent", "x")
    w.ticket("aaaa00000001", "PROVED", raw="{not json")
    w.ticket("bbbb00000002", "PROVED", raw=json.dumps(
        {"workflow_and_state": "prose, no bracket", "intent_berth": str(x)}))
    w.ticket("cccc00000003", "PROVED", raw=json.dumps({"id": "no cursor at all"}))
    assert sb.berth_ticket_cursors(tickets=w.tickets, ideas=w.ideas) == {}


def test_map_collects_every_ticket_naming_one_berth():
    w = World()
    y = w.berth("idea", "y")
    w.idea("idea-three", y)
    w.ticket("aaaa00000001", "TICKETME", from_idea="idea-three")
    w.ticket("bbbb00000002", "PROVED", from_idea="idea-three")
    w.ticket("cccc00000003", "BUILDME", from_idea="idea-three")
    m = sb.berth_ticket_cursors(tickets=w.tickets, ideas=w.ideas)
    assert sorted(m[str(y.resolve())]) == ["BUILDME", "PROVED", "TICKETME"]


def test_map_reads_the_roots_from_the_artifact_door_seam():
    """``CAIRN_ARTIFACT_ROOTS`` — the door's own scratch seam — points the map at a scratch
    commons with no parameter passed; the live commons is not read."""
    w = World()
    x = w.berth("intent", "x")
    commons = w.root / "commons"
    (commons / "tickets").mkdir(parents=True)
    (commons / "ideas").mkdir()
    (commons / "tickets" / "aaaa00000001-t.json").write_text(json.dumps(
        {"workflow_and_state": _wf("PROVED"), "intent_berth": str(x)}))
    saved = {k: os.environ.get(k) for k in ("CAIRN_ARTIFACT_ROOTS", "CAIRN_TICKETS_DIR", "CAIRN_IDEAS_DIR")}
    try:
        os.environ["CAIRN_ARTIFACT_ROOTS"] = json.dumps({"cairn": str(REPO), "CairnCommons": str(commons)})
        os.environ.pop("CAIRN_TICKETS_DIR", None)
        os.environ.pop("CAIRN_IDEAS_DIR", None)
        assert sb.tickets_root() == commons / "tickets"
        assert sb.ideas_root() == commons / "ideas"
        assert sb.berth_ticket_cursors() == {str(x.resolve()): ["PROVED"]}
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ── the ANY-terminal rule ─────────────────────────────────────────────────────

def test_any_terminal_drains_and_an_empty_list_keeps():
    assert sb.drains_by_measurement(["PROVED"]) is True
    assert sb.drains_by_measurement(["TICKETME", "PROVED", "TICKETME"]) is True
    assert sb.drains_by_measurement(["BUILDME", "PROVEME"]) is False
    assert sb.drains_by_measurement([]) is False


def test_the_rule_reads_the_grammars_terminal_vocabulary_not_a_local_copy():
    for state in transitions.TERMINAL_STATES:
        assert sb.drains_by_measurement([state]) is True, state
    assert sb.drains_by_measurement(["WATCHME"]) is False


def test_the_inbox_label_tail_is_the_grammars_terminal_vocabulary():
    """D4: one vocabulary. The renderer's LABEL_ORDER ends with exactly the grammar's
    TERMINAL_STATES, so a word added to one and not the other reds here."""
    from cairn.tools.operator_inbox.inbox import LABEL_ORDER
    n = len(transitions.TERMINAL_STATES)
    assert set(LABEL_ORDER[-n:]) == set(transitions.TERMINAL_STATES), LABEL_ORDER[-n:]
    assert not set(LABEL_ORDER[:-n]) & set(transitions.TERMINAL_STATES)


# ── the lane ──────────────────────────────────────────────────────────────────

def test_the_lane_drops_the_proved_named_berth_and_keeps_the_other_three():
    w = standard_world()
    assert w.lane() == ["broken-sorted", "buildme-sorted", "unnamed-intent"]


def test_drain_false_is_the_full_census():
    w = standard_world()
    assert w.lane(drain=False) == ["broken-sorted", "buildme-sorted", "proved-intent", "unnamed-intent"]


def test_the_any_rule_holds_in_the_lane_over_the_idea_berth():
    """The 2026-09-15 idea bore three tickets; one PROVED drains its berth."""
    w = World()
    y = w.berth("idea", "shared-idea")
    w.idea("idea-shared", y)
    w.ticket("aaaa00000001", "TICKETME", from_idea="idea-shared")
    w.ticket("bbbb00000002", "TICKETME", from_idea="idea-shared")
    assert w.lane() == ["shared-idea"]
    w.ticket("cccc00000003", "PROVED", from_idea="idea-shared")
    assert w.lane() == []


def test_the_reviewed_log_is_byte_identical_across_every_read():
    w = standard_world()
    before = w.reviewed_sha()
    w.lane(); w.lane(drain=False); sb.berth_ticket_cursors(tickets=w.tickets, ideas=w.ideas)
    assert w.reviewed_sha() == before
    assert not list(w.tickets.glob("*.tmp")) and not list(w.berths.rglob("*.tmp"))


def test_the_reviewed_log_still_drains_what_he_reviewed():
    w = standard_world()
    w.reviewed.write_text(w.reviewed.read_text() + json.dumps(
        {"berth_id": "unnamed-intent", "when": "x", "words": "seen"}) + "\n")
    assert w.lane() == ["broken-sorted", "buildme-sorted"]


def test_the_lane_is_all_kept_when_no_tickets_dir_exists():
    w = standard_world()
    assert sorted(r["berth_id"] for r in sb.pending_reviews(
        root=w.berths, reviewed_path=w.reviewed, tickets=w.root / "nowhere", ideas=w.ideas)
    ) == ["broken-sorted", "buildme-sorted", "proved-intent", "unnamed-intent"]


def test_reverting_the_predicate_reds_this_proof():
    """The tooth a hollow build cannot pass: with the predicate a no-op the PROVED-named
    berth is back. Stated as the difference between the two readings so that a revert
    that makes drain=True behave like drain=False fails here by name."""
    w = standard_world()
    assert set(w.lane(drain=False)) - set(w.lane()) == {"proved-intent"}

if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
