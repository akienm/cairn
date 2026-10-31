"""Proof for ticket c66b25d122e6 — BUILDME refuses a ticket no outline check has read, and
/sorted runs the check at every cast.

Every sieve tooth runs over a SCRATCH commons handed to the artifact door
(``set_diagnostic_roots``) and passed as ``root``: one ticket file and an outline_checks/ dir
the tooth fills by hand. No tooth calls the reader — the sieve reads only what
``outline_check.standing`` reads, so a hand-written record is the whole world it sees.

The teeth, one per falsifier clause:

  1. the entry gate lists six lanes, the sixth ``the_ticket_was_checked_against_the_outline``;
  2. with no record, ``buildme_rides_the_outline_check`` returns ONE finding whose
     check_with is ``cairn outlinecheck <id>``;
  3. with only a ran:false record, it returns one finding;
  4. with a ran:true record, it returns none;
  5. a ticket the store does not hold returns none (the chokepoint's own refusal covers it);
  6. skills/sorted/SKILL.md tells the caster to run ``cairn outlinecheck``.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "c66b25d122e6": {
        "1": "test_1_the_entry_gate_lists_six_lanes_and_the_sixth_is_the_outline_check",
        "2": "test_2_no_record_is_one_finding_naming_the_command",
        "3": "test_3_a_run_that_did_not_read_is_still_red",
        "4": "test_4_a_run_that_read_is_green",
        "5": "test_5_a_ticket_not_on_file_is_not_this_sieves_refusal",
        "6": "test_6_sorted_runs_the_check_at_every_cast",
    },
}

TID = "a1b2c3d4e5f6"
LANE = "the_ticket_was_checked_against_the_outline"


class _World:
    """A scratch commons the door is pointed at: tickets/<TID>-x.json and an empty
    outline_checks/. Closed in a finally, so a failed tooth never leaves the door aimed here."""

    def __init__(self):
        from cairn.tools.artifact import artifact as door
        self.door = door
        self.dir = scratch_dir("outline-lane-proof-")
        self.commons = self.dir / "CairnCommons"
        self.cairn = self.dir / "cairn"
        (self.commons / "tickets").mkdir(parents=True)
        (self.commons / "outline_checks").mkdir()
        self.cairn.mkdir()
        (self.commons / "tickets" / f"{TID}-x.json").write_text("{}")
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def record(self, stamp: str, ran: bool):
        p = self.commons / "outline_checks" / f"{TID}-{stamp}.json"
        p.write_text(json.dumps({"ticket": TID, "ran": ran}, indent=2) + "\n")

    def sieve(self, ticket: str = TID):
        from cairn.machines.build_inspector.inspector import buildme_rides_the_outline_check
        return buildme_rides_the_outline_check(ticket, root=self.commons)

    def close(self):
        self.door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)


def test_1_the_entry_gate_lists_six_lanes_and_the_sixth_is_the_outline_check():
    from cairn.tools.base import transitions
    from cairn.tools.base import ticket_file
    import cairn.machines.build_inspector.inspector as I
    w = _World()
    try:
        tickets = w.dir / "gate-tickets"
        tickets.mkdir()
        (tickets / "widget.json").write_text("{}")
        berths = w.dir / "gate-berths"
        (berths / "0" / "packets").mkdir(parents=True)
        saved = ticket_file._TICKETS, I._CHART_BERTHS
        ticket_file._TICKETS, I._CHART_BERTHS = tickets, berths
        try:
            record = transitions.inspect_entry("widget")
        finally:
            ticket_file._TICKETS, I._CHART_BERTHS = saved
        names = [e["identity"] for e in record]
        assert len(names) == 6 and names[-1] == LANE, names
    finally:
        w.close()


def test_2_no_record_is_one_finding_naming_the_command():
    w = _World()
    try:
        f = w.sieve()
        assert len(f) == 1, f
        assert f[0]["values"]["check_with"] == f"cairn outlinecheck {TID}", f[0]
    finally:
        w.close()


def test_3_a_run_that_did_not_read_is_still_red():
    w = _World()
    try:
        w.record("20261027T000000", ran=False)
        f = w.sieve()
        assert len(f) == 1, f
    finally:
        w.close()


def test_4_a_run_that_read_is_green():
    w = _World()
    try:
        w.record("20261027T000000", ran=False)
        w.record("20261027T000100", ran=True)
        assert w.sieve() == [], w.sieve()
    finally:
        w.close()


def test_5_a_ticket_not_on_file_is_not_this_sieves_refusal():
    w = _World()
    try:
        assert w.sieve("ffffffffffff") == []
    finally:
        w.close()


def test_6_sorted_runs_the_check_at_every_cast():
    text = (REPO / "skills/sorted/SKILL.md").read_text()
    assert "cairn outlinecheck" in text, "skills/sorted/SKILL.md never names cairn outlinecheck"


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    assert len(teeth) == 6, len(teeth)
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
    print(f"green — {len(teeth)} teeth: the sixth BUILDME lane reds a ticket no outline check has "
          "read, greens one a check has read, leaves an unfiled ticket to the chokepoint, and /sorted "
          "sends the caster to cairn outlinecheck")
    return 0


if __name__ == "__main__":
    sys.exit(main())
