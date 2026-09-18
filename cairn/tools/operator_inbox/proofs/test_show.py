"""Proof for ticket a705346aa75c — `operator show <slug|id>` reaches every item the inbox
lists, over a SCRATCH commons with one collision.

The falsifier's proves_red, clause by clause:
  (1) the command still only searches berths — a token naming an idea, a question, a
      trouble or an intention resolves to that record, in its lane, with its path;
  (2) an idea slug returns 'no match' when the idea file exists — an idea that MOVED ON
      (a ticket cites it, so the inbox no longer lists it) still resolves to its file;
  (3) the lookup silently picks one lane when the slug matches in multiple — the one
      collision the scratch commons carries (the same idea captured on two days) is
      announced with both hits named, and the verb exits 1 rather than choosing.

Every read is over a scratch root (Law: no proof reads the live commons); the names
under test are imported INSIDE the teeth so a hollow build reds at PROVEME, not UNRAN.
"""

import json
from pathlib import Path
import tempfile

PROVES = {
    "a705346aa75c": {
        "1": "test_resolve_reaches_every_lane_not_only_berths",
        "2": "test_a_moved_on_idea_still_resolves_to_its_file",
        "3": "test_a_collision_is_announced_never_picked",
    },
}


def _scratch_commons(root: Path) -> dict:
    """One record per lane, one collision: `ticket-and-task` captured as an idea on two
    days. The trouble `boat-stuck-at-buildme` is CLEARED (left the inbox); the idea
    `2026-01-01-a-lot-of-things-look-alike` is cited by the ticket (moved on)."""
    ideas = root / "ideas"
    questions = root / "questions"
    troubles = root / "troubles"
    intentions = root / "intentions"
    tickets = root / "tickets"
    firings = root / "skill_block_instance"
    lap = root / "adjudications"
    for d in (ideas, questions, troubles, intentions, tickets, lap,
              firings / "berths" / "intent"):
        d.mkdir(parents=True)
    for stem in ("2026-01-01-a-lot-of-things-look-alike",
                 "2026-01-05-ticket-and-task", "2026-01-06-ticket-and-task"):
        (ideas / f"{stem}.json").write_text(json.dumps({"prose": stem, "author": "Akien"}))
    (questions / "open-0123456789ab.json").write_text(json.dumps({
        "id": "open-0123456789ab", "question": "one question?", "ticket": "aaaaaaaaaaaa"}))
    (troubles / "boat-stuck-at-buildme.json").write_text(json.dumps({
        "id": "boat-stuck-at-buildme", "standing": "CLEARED", "count": 1,
        "why": "a fixture trouble, cleared"}))
    (troubles / "loop-not-beating.json").write_text(json.dumps({
        "id": "loop-not-beating", "standing": "OPEN", "count": 2, "why": "fixture live"}))
    (intentions / "I-no-ticket-yet.md").write_text("# no ticket yet\n")
    (tickets / "aaaaaaaaaaaa-fixture.json").write_text(json.dumps({
        "id": "aaaaaaaaaaaa", "title": "fixture ticket",
        "linked_ideas": ["2026-01-01-a-lot-of-things-look-alike"],
        "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME] -> BUILDME -> PROVED",
    }))
    return {"ideas_dir": ideas, "questions_dir": questions, "troubles_dir": str(troubles),
            "intentions_dir": intentions, "tickets_dir": tickets,
            "firings_root": firings, "adjudications_dir": lap}


def test_resolve_reaches_every_lane_not_only_berths():
    """(1) a berths-only lookup answers nothing for an idea, a question, a trouble or an
    intention; the built one answers each in its own lane with a path that exists."""
    from cairn.tools.operator_inbox.inbox import resolve, lanes_searched, show_item
    with tempfile.TemporaryDirectory(prefix="a705-scratch-commons-") as td:
        f = _scratch_commons(Path(td))
        want = {
            "a-lot-of-things-look-alike": ("ideas", "2026-01-01-a-lot-of-things-look-alike"),
            "open-0123456789ab": ("questions", "open-0123456789ab"),
            "loop-not-beating": ("troubles", "loop-not-beating"),
            "aaaaaaaaaaaa": ("tickets", "aaaaaaaaaaaa"),
        }
        for token, (lane_prefix, ident) in want.items():
            hits = resolve(token, **f)
            assert len(hits) == 1, (token, hits)
            assert hits[0]["lane"].startswith(lane_prefix), (token, hits[0]["lane"])
            assert hits[0]["id"] == ident
            assert hits[0]["path"] and Path(hits[0]["path"]).exists(), (token, hits[0]["path"])
            assert not show_item(token, **f).startswith("no pending artifact")
        # a prefix of a hex id resolves too; a prefix of a slug does not (too loose)
        assert [h["id"] for h in resolve("open-0123", **f)] == ["open-0123456789ab"]
        assert resolve("loop", **f) == []
        lanes = lanes_searched(**f)
        for lane in ("ideas", "questions", "troubles", "intentions", "tickets",
                     "adjudications", "tickets_done", "ideas_all", "troubles_all"):
            assert lane in lanes, (lane, lanes)
        miss = show_item("does-not-exist-slug", **f)
        assert miss.startswith("no pending artifact")
        for lane in lanes:
            assert lane in miss, (lane, miss)


def test_a_moved_on_idea_still_resolves_to_its_file():
    """(2) the ticket cites `2026-01-01-a-lot-of-things-look-alike`, so read_ideas no
    longer lists it — and its file is on disk, so `show` must reach it. The same for a
    CLEARED trouble: left the inbox, still viewable."""
    from cairn.tools.operator_inbox.inbox import resolve, gather_all, show_item
    with tempfile.TemporaryDirectory(prefix="a705-scratch-commons-") as td:
        f = _scratch_commons(Path(td))
        open_ideas = [i["id"] for i in gather_all(**f)["ideas"]["items"]]
        assert "2026-01-01-a-lot-of-things-look-alike" not in open_ideas, open_ideas
        hits = resolve("a-lot-of-things-look-alike", **f)
        assert len(hits) == 1 and hits[0]["lane"] == "ideas_all", hits
        assert Path(hits[0]["path"]) == f["ideas_dir"] / "2026-01-01-a-lot-of-things-look-alike.json"
        text = show_item("a-lot-of-things-look-alike", **f)
        assert "[ideas_all]" in text and "2026-01-01-a-lot-of-things-look-alike" in text
        assert "no pending artifact" not in text
        cleared = resolve("boat-stuck-at-buildme", **f)
        assert len(cleared) == 1 and cleared[0]["lane"] == "troubles_all", cleared
        assert cleared[0]["record"]["standing"] == "CLEARED"


def test_a_collision_is_announced_never_picked():
    """(3) `ticket-and-task` is two ideas; resolve returns both, show names both and
    starts with `ambiguous`, and main() exits 1 on that shape. A token that names one
    thing exactly outranks a slug that also matches it loosely — that is not a collision."""
    from cairn.tools.operator_inbox import inbox
    with tempfile.TemporaryDirectory(prefix="a705-scratch-commons-") as td:
        f = _scratch_commons(Path(td))
        hits = inbox.resolve("ticket-and-task", **f)
        assert sorted(h["id"] for h in hits) == ["2026-01-05-ticket-and-task",
                                                  "2026-01-06-ticket-and-task"], hits
        text = inbox.show_item("ticket-and-task", **f)
        assert text.startswith("ambiguous — 2 match 'ticket-and-task'"), text
        assert "2026-01-05-ticket-and-task" in text and "2026-01-06-ticket-and-task" in text
        # the exact id of one of the pair is NOT ambiguous: exact outranks loose
        one = inbox.resolve("2026-01-05-ticket-and-task", **f)
        assert [h["id"] for h in one] == ["2026-01-05-ticket-and-task"], one
        # main() carries the refusal to the exit code — monkeypatched so the verb is
        # exercised over the scratch commons, never the live one
        saved = inbox.show_item
        try:
            inbox.show_item = lambda tok, **kw: saved(tok, **f)
            assert inbox.main(["show", "ticket-and-task"]) == 1
            assert inbox.main(["show", "does-not-exist-slug"]) == 1
            assert inbox.main(["show", "loop-not-beating"]) == 0
        finally:
            inbox.show_item = saved


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
