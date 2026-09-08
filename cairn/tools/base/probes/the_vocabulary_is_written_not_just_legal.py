"""PROBE — did the five-word pickup vocabulary reach USE, or only legality?

Berth for the WATCHME that ticket ``6ec9b384b451`` (the-pickup-phase-says-why-a-ticket-is-
not-moving) carries. Berthed beside ``cairn/tools/base`` because that is WHAT IT WATCHES:
the phase vocabulary lives in ``cairn/tools/base/transitions.py``.

THE EFFICACY QUESTION, AND WHY IT IS A RATE. The grammar can carry five words and the
corpus can go on wearing two. That failure leaves every deterministic check green — the
tuple is right, the door refuses what it should, the proofs pass — while the thing the
ticket was for never happens: a reader still cannot tell "this needs Akien" from "CC has
not got to it", because nothing but ``waiting`` was ever written. So the measure is the
WRITE RATE of the four non-default phases, never their existence.

THIS PROBE IS SHAPED BY THE FAILURE OF ITS OWN SIBLING, MEASURED. Beside this file sits
``a_pickup_is_witnessed.py``, whose clear condition was ``pickups >= 1``. It took its one
record in August 2026 and read green ever after, off a historical fact, while the door it
watched sat with no caller in the live system for a month. An existence claim cannot
regress, so a watch built on one stops watching the moment it clears. Every clause below
is a quantity that can go back down.

MEMOIZED, NON-NEGOTIABLY. Live trouble ``beat-tail-re-walks-corpora-no-sieve-counts``:
roughly 78 probes re-walk corpora that did not move, once per beat, forever, and nothing
would red the 79th. The corpus walk here goes through ``settled()`` on the tickets tree, so
a beat where no ticket moved costs a fingerprint and no read. This probe is not the 79th.

FILES ONLY: it walks ``CairnCommons/tickets/*.json`` — no device, no bus, no network.

AUTHORITY: none. It deposits and pokes; re-opening the design is the owner's act (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket, once
from cairn.tools.base.settled import settled
from cairn.tools.base.transitions import MalformedWorkflow, parse_workflow, release_lack

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TICKETS = _REPO_ROOT.parent / "CairnCommons" / "tickets"

_OWNING_TICKET = "the-pickup-phase-says-why-a-ticket-is-not-moving"

# The four phases that are not the default. ``in-process`` is deliberately absent: it is
# DERIVED, never written to a ticket, so counting it here would be counting something the
# corpus is incapable of holding — a clause that can never rise is as dead as one that can
# never fall.
_NON_DEFAULT = ("queued", "hold", "blocked")

# THE CLEAR, both clauses load-bearing and both able to regress. The first says the
# vocabulary is EXERCISED — every word used at least once, so a five-word grammar that
# collapsed to three in practice does not read as success. The second says it is USED, not
# demonstrated: ten distinct tickets is past the handful an author writes to prove a point.
_ENOUGH_DISTINCT = 10

# THE TRIGGER FLOOR. Below this many live tickets there is no corpus to judge — a young
# vocabulary written on nothing is a vocabulary nobody has had reason to write yet.
_TRIGGER_FLOOR = 25

# THE HORIZON. Same tracked debt as the siblings at this address: the beat rate is not yet a
# real number, so 1000 pulses stands for "clearly a long standing" and MUST be re-tuned when
# it becomes one.
_HORIZON = 1000


def _walk_tickets() -> dict:
    """The uncached walk: every ticket's cursor phase, over the live corpus."""
    by_phase: dict[str, list[str]] = {}
    stale_or_lacking: list[dict] = []
    live = 0
    unparsed = 0
    for path in sorted(_TICKETS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a ticket this probe cannot read is not a finding
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("workflow_and_state"), str):
            continue
        try:
            wf = parse_workflow(doc["workflow_and_state"])
        except MalformedWorkflow:
            unparsed += 1
            continue
        from cairn.tools.base.transitions import is_terminal
        if is_terminal(wf.here):
            continue
        live += 1
        tid = doc.get("id") or path.stem[:12]
        by_phase.setdefault(wf.phase or "(bare)", []).append(tid)
        # AT REST, NOT ONLY AT THE DOOR. set_phase refuses a bad release when it is written;
        # nothing yet re-checks one already sitting on disk, and a queued whose dependency
        # has since reached a terminal goes stale WITHOUT anybody writing anything. That is
        # the self-clearing clause, and it only means something if somebody looks.
        lack = release_lack(wf.phase, doc.get("release"))
        if lack is not None:
            stale_or_lacking.append({"ticket": tid, "phase": wf.phase, "lack": lack})
    written = sorted({t for p in _NON_DEFAULT for t in by_phase.get(p, [])})
    return {
        "live_tickets": live,
        "unparsed": unparsed,
        "by_phase": {k: len(v) for k, v in sorted(by_phase.items())},
        "non_default_tickets": written,
        # THE RATE, not the count — a denominator is what makes the number readable as
        # "the vocabulary is decoration" rather than as a bare tally that only ever grows.
        "write_rate": (len(written) / live) if live else 0.0,
        "words_used": sorted(p for p in _NON_DEFAULT if by_phase.get(p)),
        "words_unused": sorted(p for p in _NON_DEFAULT if not by_phase.get(p)),
        # Written phases whose release is absent, unresolvable, or (for queued) already
        # satisfied. A non-empty list is a corpus telling on itself.
        "releases_lacking": stale_or_lacking,
    }


def survey_the_corpus() -> dict:
    """The walk, MEMOIZED on the tickets tree's ``(path, mtime_ns, size)`` fingerprint. A
    beat where no ticket moved re-reads nothing."""
    return settled("pickup_phase_write_rate", _TICKETS, _walk_tickets)


def _trigger(now, context: dict) -> bool:
    """TRUE when the corpus is big enough to judge and the vocabulary is going UNWRITTEN —
    the words are legal and nobody uses them. Mutually exclusive with ``_enough`` by
    construction: this fires while every non-default word is unused, that clears only once
    all three are used."""
    s = once(context, "corpus", survey_the_corpus)
    return s["live_tickets"] >= _TRIGGER_FLOOR and not s["words_used"]


def _enough(context: dict) -> bool:
    """CLEARED when the vocabulary is genuinely in use: every non-default word written on at
    least one live ticket, non-default phases standing on ten or more distinct live tickets,
    and every one of those releases still resolving.

    BOTH CLAUSES CAN GO BACK DOWN, which is the whole design. Tickets reach terminals and
    leave the live corpus, so a vocabulary that stops being written un-clears this watch
    instead of coasting on a historical fact — the exact rot measured in the sibling probe
    at this address."""
    s = once(context, "corpus", survey_the_corpus)
    return (not s["words_unused"]
            and len(s["non_default_tickets"]) >= _ENOUGH_DISTINCT
            and not s["releases_lacking"])


def _carry(context: dict) -> dict:
    s = once(context, "corpus", survey_the_corpus)
    return {
        "finding": "the five-word pickup vocabulary is legal but not written — the corpus "
                   "still wears the two words it wore before the ruling",
        "counts": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the words landed but nothing writes them: a corpus still ~100% "
                             ":waiting means the five collapsed to two and the vocabulary is "
                             "decoration — the same hollow shape as a door with no caller",
        "suggests": "back-edge the ticket to WATCHME and ask which is true: the phases cost "
                    "more to write than the answer is worth, or nothing PROMPTS the write at "
                    "the moment a ticket actually stops moving. The second is a missing "
                    "firing event, not a missing vocabulary.",
    }


PROBE = Probe(
    why="did the five-word pickup vocabulary reach USE, or only legality? — the grammar can "
        "carry five words while the corpus wears two, and every deterministic check stays "
        "green while the reader still cannot tell 'needs Akien' from 'CC has not got to it'",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_corpus()
    print(json.dumps({"corpus": s,
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2))
