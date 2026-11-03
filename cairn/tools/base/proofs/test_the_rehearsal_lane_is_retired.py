"""Proof for ticket a0b0231dde70: a ticket crosses into BUILDME without a rehearsal until a
learner reads the rehearsal records (Akien 2026-11-02, outline 17.6).

Rehearsal makes training data for graph trees that judge "buildable as written" without an
LLM call. No such learner was built, nothing read the records but the BUILDME lane
``the_ticket_was_rehearsed``, and the passes cost more than building. So the entry gate stops
composing that lane, the sieve (build_inspector.buildme_rides_the_rehearsal) stays for the
learner, and the two places that told a builder the lane holds the crossing (/sail 0c and the
rehearsal charter) say it is retired.

One clause, one tooth. It lives in its own file, not in test_transitions.py, because hollow
runs a proof whole. In a worktree with no commons beside it, test_transitions.py crashes at an
older tooth before this one runs (FIXME 1). This file reads no commons: the tickets and chart
berths are scratch, and the inspector's globals point at them.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "a0b0231dde70": {
        "all": "test_a_ticket_with_no_rehearsal_crosses_with_no_rehearsal_lane",
    },
}

RETIRED = "retired until a learner reads the records"


def _scratch_world(d: Path) -> tuple[Path, Path]:
    """One cast ticket, ``widget``, claimed by one berthed validate packet; and a crossings
    journal in which it crossed BUILDME before any verdict, so only the lanes decide."""
    tickets = d / "tickets"
    tickets.mkdir()
    (tickets / "widget.json").write_text("{}")
    berths = d / "berths"
    (berths / "0" / "packets").mkdir(parents=True)
    (berths / "0" / "packets" / "validate-20260729T000000-feed.json").write_text(
        json.dumps({"ticket": "widget"}))
    journal = d / "crossings"
    journal.mkdir()
    (journal / "history.json").write_text(json.dumps([
        {"ticket": "widget", "at": "2026-07-29T00:00:00", "from": "TICKETME", "to": "BUILDME",
         "direction": "forward", "by": "fixture"}]))
    return tickets, berths


def test_a_ticket_with_no_rehearsal_crosses_with_no_rehearsal_lane():
    """A cast ticket no rehearsal has run over gets an entry record with no
    the_ticket_was_rehearsed lane, and only that lane is gone (five remain). The sieve is
    still importable, and /sail and the rehearsal charter both say the lane is retired."""
    from cairn.tools.base import transitions
    from cairn.tools.base import ticket_file
    import cairn.machines.build_inspector.inspector as insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _scratch_world(Path(d))
        journal = Path(d) / "crossings"
        saved = ticket_file._TICKETS, insp._CHART_BERTHS, insp._crossing_roots
        ticket_file._TICKETS, insp._CHART_BERTHS = tickets, berths
        insp._crossing_roots = lambda: {"repo": journal, "commons": journal}
        try:
            names = [e["identity"] for e in transitions.inspect_entry("widget")]
        finally:
            ticket_file._TICKETS, insp._CHART_BERTHS, insp._crossing_roots = saved
    assert "the_ticket_was_rehearsed" not in names, f"the retired lane still composes: {names}"
    assert len(names) == 5, f"exactly the rehearsal lane is gone, no other: {names}"
    assert callable(insp.buildme_rides_the_rehearsal), "the sieve stays for the learner"
    sail = (_REPO_ROOT / "skills" / "sail" / "SKILL.md").read_text(encoding="utf-8")
    assert RETIRED in sail, "/sail still tells the builder the rehearsal lane holds the crossing"
    charter = (_REPO_ROOT / "cairn" / "machines" / "rehearsal" / "intention+why.json").read_text(
        encoding="utf-8")
    assert RETIRED in charter, "the rehearsal charter still states the lane as live"


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    assert len(teeth) == 1, len(teeth)
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
    print("green — 1 tooth: the entry gate composes five lanes and no rehearsal lane; the sieve "
          "stays; /sail and the rehearsal charter say the lane is retired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
