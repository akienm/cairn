"""PROBE — is the ticket write door still being used after its first batch, or was the
batch the only thing that ever called it?

Berth for the WATCHME that ticket ``9e7867aa1056`` (a-phase-write-records-at-the-ticket's-
own-address) carries. Berthed beside ``cairn/tools/base`` because that is WHAT IT WATCHES:
``set_phase``'s ``ticket=`` door lives in ``cairn/tools/base/transitions.py``.

THE FAILURE THIS EXISTS TO CATCH IS ONE THIS ADDRESS HAS ALREADY SUFFERED TWICE, MEASURED.
``a_pickup_is_witnessed.py`` beside this file cleared on ``pickups >= 1``: it took its one
record in August 2026 and read green ever after while the door it watched sat with no caller
in the live system for a month. And the door THIS probe watches was built because a grep for
ticket writes across ``cairn/``, ``skills/`` and ``bin/`` returned ZERO hits — 259 tickets'
worth of crossings and cursors, all hand-edited, because no door existed. A door built and
then not called is the identical shape wearing a newer coat. So neither clause below is an
existence claim; both are quantities that can go back DOWN.

WHY BOTH HALVES ARE REQUIRED, AND THEY MEASURE DIFFERENT THINGS.

  * The FIRST half — records after the batch day — says the door is still ALIVE. A door
    called 34 times on the day it shipped and never again is a migration script, not a door.
  * The SECOND half — every written phase on a live ticket backed by a matching
    ``phase_writes`` entry — says nothing SLIPPED PAST it. A door can be called faithfully
    and still fail its purpose if hand-edits go on happening beside it, because then the
    ticket's cursor and the record of how the cursor got there disagree, which is exactly
    the Law 5 defect the door was built to end.

A door can pass either half alone. The intention needs both, so the clear needs both.

MEMOIZED, NON-NEGOTIABLY. Live trouble ``beat-tail-re-walks-corpora-no-sieve-counts``:
roughly 78 probes re-walk corpora that did not move, once per beat, forever, and nothing
would red the 79th. This walk goes through ``settled()`` on the tickets tree, so a beat where
no ticket moved costs a fingerprint and no read. This probe is not the 79th.

FILES ONLY: it walks ``CairnCommons/tickets/*.json`` — no device, no bus, no network.

AUTHORITY: none. It deposits and pokes; re-opening the design is the owner's act (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket, once
from cairn.tools.base.settled import settled
from cairn.tools.base.transitions import (
    MalformedWorkflow,
    is_terminal,
    parse_workflow,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TICKETS = _REPO_ROOT.parent / "CairnCommons" / "tickets"

_OWNING_TICKET = "a-phase-write-records-at-the-tickets-own-address"

# THE CLEAR, first half. Three records is past "somebody demonstrated it once"; two distinct
# days is what separates a live door from a migration that ran and finished. Both are small
# on purpose — the question is whether the door is CALLED AT ALL after its batch, and a high
# bar here would just mean the watch stays open on a door working perfectly at a low rate.
_ENOUGH_AFTER_BATCH = 3
_ENOUGH_DISTINCT_DAYS = 2

# THE TRIGGER FLOOR. Below this many phase_writes records anywhere, the batch itself has not
# landed yet and there is nothing to ask about — a door reds for having no callers only once
# it has had the chance to have some.
_TRIGGER_FLOOR = 10

# THE HORIZON. Same tracked debt as the siblings at this address: the beat rate is not yet a
# real number, so 1000 pulses stands for "clearly a long standing" and MUST be re-tuned when
# it becomes one. The spec's "sustained one week after the batch" is the intent behind it.
_HORIZON = 1000


def _day(record: object) -> str | None:
    """The calendar day of one phase_writes record, or None if it carries no readable time.

    A record with no ``at`` is not counted rather than guessed at — an invented date would
    make the distinct-days clause clear on nothing, which is the hollow pass this whole probe
    is shaped against."""
    if not isinstance(record, dict):
        return None
    at = record.get("at")
    if not isinstance(at, str) or len(at) < 10:
        return None
    return at[:10]


def _walk_tickets() -> dict:
    """The uncached walk: every ticket's phase_writes records and every live written phase.

    THE BATCH DAY IS DERIVED, NEVER HARD-CODED. It is the EARLIEST day on which any
    phase_writes record stands — which is the day the backlog was written through the door
    for the first time. Deriving it means this probe needs no editing when the batch moves,
    and it cannot be quietly re-pointed at a friendlier date to make the watch clear."""
    records: list[dict] = []
    unbacked: list[dict] = []
    written_live = 0
    total_live = 0
    for path in sorted(_TICKETS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a ticket this probe cannot read is not a finding
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("workflow_and_state"), str):
            continue
        tid = doc.get("id") or path.stem[:12]
        writes = doc.get("phase_writes")
        if isinstance(writes, list):
            for r in writes:
                if isinstance(r, dict):
                    records.append({"ticket": tid, "day": _day(r),
                                    "workflow": r.get("workflow")})
        try:
            wf = parse_workflow(doc["workflow_and_state"])
        except MalformedWorkflow:
            continue
        if is_terminal(wf.here):
            continue
        total_live += 1
        if wf.phase is None:
            continue
        written_live += 1
        # THE SECOND HALF, per ticket: the cursor says a phase was written, so SOME record of
        # writing it must stand at this address and must name the string the cursor now
        # carries. A record naming an older string is a later hand-edit — the door was used
        # once and then walked around, which is worse than never using it, because the
        # phase_writes list makes the ticket LOOK gated.
        backing = [r for r in (writes or [])
                   if isinstance(r, dict) and r.get("workflow") == doc["workflow_and_state"]]
        if not backing:
            unbacked.append({
                "ticket": tid,
                "phase": wf.phase,
                "cursor": doc["workflow_and_state"],
                "why": ("no phase_writes record names this cursor — the phase was written by "
                        "hand, or written through the door and then hand-edited after"),
            })
    days = sorted({r["day"] for r in records if r["day"]})
    batch_day = days[0] if days else None
    after = [r for r in records if r["day"] and batch_day and r["day"] > batch_day]
    return {
        "records": len(records),
        "batch_day": batch_day,
        "days_seen": days,
        "records_after_batch": len(after),
        "days_after_batch": sorted({r["day"] for r in after}),
        "live_tickets": total_live,
        "live_tickets_with_a_written_phase": written_live,
        # A non-empty list is the corpus telling on itself: the door exists and was walked
        # around anyway.
        "unbacked_written_phases": unbacked,
    }


def survey_the_door() -> dict:
    """The walk, MEMOIZED on the tickets tree's ``(path, mtime_ns, size)`` fingerprint. A beat
    where no ticket moved re-reads nothing."""
    return settled("ticket_write_door_callers", _TICKETS, _walk_tickets)


def _trigger(now, context: dict) -> bool:
    """TRUE when the batch has landed and the door has gone quiet since, or when hand-edits
    are standing beside it.

    The first disjunct is the door-with-no-caller shape this address has measured twice; the
    second is the door-walked-around shape. Either is the finding, and they want the same
    escalation, so they share one probe rather than splitting into two that both stay silent
    about the half they do not watch."""
    s = once(context, "door", survey_the_door)
    if s["records"] < _TRIGGER_FLOOR:
        return False
    gone_quiet = (s["records_after_batch"] < _ENOUGH_AFTER_BATCH
                  or len(s["days_after_batch"]) < _ENOUGH_DISTINCT_DAYS)
    return gone_quiet or bool(s["unbacked_written_phases"])


def _enough(context: dict) -> bool:
    """CLEARED when both halves hold: the door has been called at least three times across at
    least two distinct days that are NOT the batch day, AND every live ticket carrying a
    written phase has a phase_writes record naming its current cursor.

    BOTH CLAUSES CAN GO BACK DOWN. The second obviously so — one hand-edit re-opens it. The
    first is subtler and is the point: tickets reach terminals and leave the live corpus, and
    a corpus whose remaining written phases are all unbacked un-clears this watch instead of
    coasting on records that were true last month. That is the property ``pickups >= 1``
    never had."""
    s = once(context, "door", survey_the_door)
    return (s["records_after_batch"] >= _ENOUGH_AFTER_BATCH
            and len(s["days_after_batch"]) >= _ENOUGH_DISTINCT_DAYS
            and not s["unbacked_written_phases"])


def _carry(context: dict) -> dict:
    s = once(context, "door", survey_the_door)
    quiet = (s["records_after_batch"] < _ENOUGH_AFTER_BATCH
             or len(s["days_after_batch"]) < _ENOUGH_DISTINCT_DAYS)
    return {
        "finding": ("the ticket write door has gone quiet since its first batch"
                    if quiet else
                    "the ticket write door is being walked around — written phases stand on "
                    "tickets with no record of how they got there"),
        "counts": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": ("WRONG INTENT: the door landed and hand-edits continue anyway. "
                              "A door called only by the batch that shipped it is a migration "
                              "script, and a door called faithfully while hand-edits go on "
                              "beside it leaves the cursor and the record of the cursor "
                              "disagreeing — which is the Law 5 defect it was built to end."),
        "suggests": ("ask which is true: writing through the door costs more than editing the "
                     "file, or nothing PROMPTS the write at the moment a ticket actually "
                     "stops moving. The second is a missing firing event, not a missing door "
                     "— and it is the same answer the pickup door earned in August 2026."),
    }


PROBE = Probe(
    why="is the ticket write door still called after its first batch, and does anything still "
        "slip past it? — this address has twice built a door that took a handful of records "
        "and then sat with no caller, reading green off a historical fact",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_door()
    print(json.dumps({"door": s,
                      "would_trigger": _trigger(None, {"door": s}),
                      "enough": _enough({"door": s})}, indent=2))
