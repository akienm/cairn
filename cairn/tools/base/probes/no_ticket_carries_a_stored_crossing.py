"""PROBE — has a hand written a ``crossings`` key back onto a ticket?

Berth for the WATCHME that ticket ``d2ecdb867bc9`` carries. Berthed beside
``cairn/tools/base`` because that is WHAT IT WATCHES: the derivation
(``cairn/tools/base/crossings.py``) and the ``emit`` chokepoint whose journals it reads.

THE DEFECT THIS EXISTS TO CATCH, AND IT IS NOT A HYPOTHETICAL. On 2026-09-10, 45 tickets
carried a ``crossings`` key — 42 a list of 99 hand-written records, 2 an empty list, 1 a
PARAGRAPH where four gate-reading sites parsed a list of dicts. Nothing wrote any of them.
Four readers (the clearance gate through proof_coverage, hollow twice, codemother's shim)
decided things by reading evidence a hand had typed, which is a gate reading its own input.
The migration removed the key and pointed every reader at the journals.

ONE REAPPEARANCE IS THE WHOLE FAILURE, which is why this probe has no floor and no warm-up.
The other probes at this address measure RATES because their subject is a door that might go
quiet. This one measures an ABSENCE, and an absence has no healthy non-zero value: a single
ticket carrying the key means a hand wrote gate evidence again and four readers would have
believed it. So the trigger is ``count > 0`` and nothing else.

AND THE CLEAR IS NOT "ZERO TODAY" — that is exactly the hollow shape this address has built
twice (``a_pickup_is_witnessed`` cleared on ``pickups >= 1`` in August 2026 and read green off
a historical fact for a month). Zero is the state the migration LEFT BEHIND; it proves nothing
about whether the door holds under traffic. So the clear needs zero AND evidence that voyages
actually sailed during the silence: three forward crossings into PROVED, journalled, since the
migration. Silence with no sailing is not a held door, it is an idle system.

THE SECOND CLAUSE IS WHAT THE FALSIFIER ASKED FOR IN THE OTHER DIRECTION. The ticket's WRONG
INTENT clause reads: "if the derivation reads the stored array as a fallback — a silent
preference for the stored copy is the same hand at one remove and would read green forever off
the 43 that already have one." A fallback cannot be seen by counting keys, so it is measured
directly: the derivation module is read and any mention of the ticket-side key in a reading
verb is the finding.

MEMOIZED on the tickets tree. Live trouble ``beat-tail-re-walks-corpora-no-sieve-counts``:
~78 probes re-walk corpora that did not move, once per beat, forever. This is not the 79th.

FILES ONLY: ``CairnCommons/tickets/*.json`` and the journals. No device, no bus, no network.

AUTHORITY: none. It deposits and pokes; re-opening the design is the owner's act (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, once, owning_ticket
from cairn.tools.base.settled import settled

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TICKETS = _REPO_ROOT.parent / "CairnCommons" / "tickets"
_DERIVATION = _REPO_ROOT / "cairn" / "tools" / "base" / "crossings.py"

_OWNING_TICKET = "a-crossing-is-derived-from-the-journal-never-stored-on-the-ticket"

# THE MIGRATION DAY. Crossings journalled on or after it are the traffic the silence is
# measured against — before it, the key was standing and silence meant nothing.
_MIGRATED_ON = "2026-09-10"

# THE CLEAR's second half. Three PROVED crossings since the migration is "voyages actually
# sailed", not "the corpus sat still". Small on purpose: the question is whether the door held
# under ANY traffic, and a high bar would just keep the watch open on a door working fine.
_ENOUGH_VOYAGES = 3

# THE HORIZON. Same tracked debt as the siblings at this address: the beat rate is not yet a
# real number, so 1000 pulses stands for "clearly a long standing" and MUST be re-tuned when it
# becomes one. The spec's "30 consecutive days" is the intent behind it.
_HORIZON = 1000


def _walk() -> dict:
    """Every ticket carrying the key, every PROVED crossing since the migration, and whether
    the derivation has grown a fallback to the stored copy."""
    carriers: list[dict] = []
    for path in sorted(_TICKETS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a ticket this probe cannot read is not a finding
            continue
        if isinstance(doc, dict) and "crossings" in doc:
            value = doc["crossings"]
            carriers.append({
                "ticket": doc.get("id") or path.stem[:12],
                "file": path.name,
                "kind": type(value).__name__,
                "entries": len(value) if isinstance(value, (list, str)) else None,
            })

    # The traffic the silence is measured against, read from the journals — the record of
    # truth, never from a cursor, which is a claim about a crossing rather than the crossing.
    from cairn.tools.base.crossings import journals

    voyages: list[dict] = []
    for jpath in journals():
        try:
            doc = json.loads(jpath.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        entries = doc.get("entries") if isinstance(doc, dict) else doc
        for entry in entries if isinstance(entries, list) else []:
            if (isinstance(entry, dict) and entry.get("to") == "PROVED"
                    and entry.get("direction") == "forward"
                    and str(entry.get("at") or "")[:10] >= _MIGRATED_ON):
                voyages.append({"ticket": entry.get("ticket"), "at": entry.get("at")})

    # THE FALLBACK CHECK — the falsifier's WRONG INTENT clause, measured rather than trusted.
    # A reading verb that consults the ticket-side key is the same hand at one remove.
    fallback = []
    try:
        source = _DERIVATION.read_text(encoding="utf-8")
    except OSError as exc:
        fallback.append({"why": f"the derivation module could not be read: {exc}"})
    else:
        for lineno, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if 'ticket.get("crossings")' in line or "ticket['crossings']" in line:
                fallback.append({"line": lineno, "text": stripped[:120]})

    return {
        "carriers": carriers,
        "carrier_count": len(carriers),
        "voyages_since_migration": len(voyages),
        "voyage_tickets": sorted({v["ticket"] for v in voyages if v["ticket"]}),
        "derivation_reads_the_stored_key": fallback,
    }


def survey_the_corpus() -> dict:
    """The walk, MEMOIZED on the tickets tree's ``(path, mtime_ns, size)`` fingerprint."""
    return settled("no_ticket_carries_a_stored_crossing", _TICKETS, _walk)


def _trigger(now, context: dict) -> bool:
    """TRUE the moment ANY ticket carries the key, or the derivation grows a fallback to it.

    No floor and no warm-up, and that is the design rather than an oversight: this measures an
    absence, and an absence has no healthy non-zero value."""
    s = once(context, "corpus", survey_the_corpus)
    return bool(s["carrier_count"]) or bool(s["derivation_reads_the_stored_key"])


def _enough(context: dict) -> bool:
    """CLEARED when no ticket carries the key, the derivation names no fallback to it, AND at
    least three voyages have crossed PROVED since the migration.

    THE THIRD CLAUSE IS THE ANTI-HOLLOW ONE. Zero carriers is what the migration left behind;
    without traffic it says nothing about whether the door holds. And every clause can go back
    DOWN — one hand-written key re-opens this watch, which is the property ``pickups >= 1``
    never had."""
    s = once(context, "corpus", survey_the_corpus)
    return (s["carrier_count"] == 0
            and not s["derivation_reads_the_stored_key"]
            and s["voyages_since_migration"] >= _ENOUGH_VOYAGES)


def _carry(context: dict) -> dict:
    s = once(context, "corpus", survey_the_corpus)
    if s["derivation_reads_the_stored_key"]:
        finding = ("the derivation itself reads the ticket-side crossings key — a silent "
                   "preference for the stored copy, which is the same hand at one remove")
    else:
        finding = (f"{s['carrier_count']} ticket(s) carry a hand-written crossings key again; "
                   f"four gate-reading sites would believe it")
    return {
        "finding": finding,
        "counts": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "WRONG INTENT: the measurement is that ticket JSON no longer contains the key at "
            "all, not that a function exists. A key written back — or a fallback inside the "
            "derivation — means a gate is reading evidence a hand typed, which is the whole "
            "defect: on 2026-09-10, 99 such records stood across 42 tickets and NOTHING had "
            "written any of them."),
        "suggests": (
            "ask what wrote it. If a hand did, the answer is the door it should have ridden — "
            "emit journals the crossing already. If a TOOL did, that tool is writing a gate's "
            "own input and the finding is against the tool, not the ticket."),
    }


PROBE = Probe(
    why="has a hand written a crossings key back onto a ticket, or has the derivation grown a "
        "fallback to the stored copy? — 99 hand-written crossing records stood across 42 "
        "tickets on 2026-09-10 with no writer anywhere, and four gate-reading sites believed "
        "them",
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
