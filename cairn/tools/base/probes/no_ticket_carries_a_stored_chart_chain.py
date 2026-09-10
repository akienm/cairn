"""PROBE — has a hand written a ``chart_chain`` key back onto a ticket?

Berth for the WATCHME that ticket ``95e3b9911dd0`` carries. Berthed beside
``cairn/tools/base`` because that is WHAT IT WATCHES: the ticket corpus, and the one reader
(``cairn/devices/tester/hollow.py``) that used to take a gate's evidence off the very ticket
the gate was judging.

THE DEFECT THIS EXISTS TO CATCH, AND IT IS NOT A HYPOTHETICAL. On 2026-09-10, 24 tickets
carried a ``chart_chain`` key — 22 a mapping of stage to berth path, 2 a bare STRING of prose
where the single reader called ``.get`` on it, so those two reached the reader as an
``AttributeError`` rather than as a named lack. Nothing in the tree wrote any of them: one
reader, zero writers, twenty-four hands. Meanwhile the BUILDME entry gate had been DERIVING
the same chain from the berth store for months, so one field had two readings and only one of
them could be wrong without anybody noticing.

ONE REAPPEARANCE IS THE WHOLE FAILURE, which is why this probe has no floor and no warm-up.
The siblings at this address measure RATES because their subject is a door that might go
quiet. This one measures an ABSENCE, and an absence has no healthy non-zero value.

AND THE CLEAR IS NOT "ZERO TODAY" — that is the hollow shape this address has now built twice
(``a_pickup_is_witnessed`` cleared on ``pickups >= 1`` in August 2026 and read green off a
historical fact for a month afterward). Zero is the state the migration LEFT BEHIND; it proves
nothing about whether the door holds under traffic. So the clear needs zero AND evidence that
voyages actually sailed during the silence. Silence with no sailing is not a held door, it is
an idle system.

THE SECOND CLAUSE IS THE FALSIFIER'S OTHER DIRECTION. A reader that consults the ticket-side
key as a FALLBACK is the same hand at one remove, and would read green forever off tickets
that already carry one. A fallback cannot be seen by counting keys, so the reader is read
directly and any mention of the ticket-side key inside it is the finding.

MEMOIZED on the tickets tree. Live trouble ``beat-tail-re-walks-corpora-no-sieve-counts``:
~78 probes re-walk corpora that did not move, once per beat, forever. This is not the 79th.

FILES ONLY: ``CairnCommons/tickets/*.json``, the journals, and one source file. No device, no
bus, no network, no inference — the base tool's charter forbids an oracle reach from this
address, and the question here is a corpus read and a comparison, which needs none.

AUTHORITY: none. It deposits and pokes; re-opening the design is the owner's act (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, once, owning_ticket
from cairn.tools.base.settled import settled

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TICKETS = _REPO_ROOT.parent / "CairnCommons" / "tickets"
_READER = _REPO_ROOT / "cairn" / "devices" / "tester" / "hollow.py"

_OWNING_TICKET = "hollow-derives-the-chart-chain-from-the-berths-never-from-a-stored-copy"

# THE MIGRATION DAY. Crossings journalled on or after it are the traffic the silence is
# measured against — before it, the key was standing and silence meant nothing.
_MIGRATED_ON = "2026-09-10"

# THE CLEAR's second half. Three PROVED crossings since the migration is "voyages actually
# sailed", not "the corpus sat still". Same floor and same reasoning as the sibling probe
# beside this one, deliberately: the question is whether the door held under ANY traffic.
_ENOUGH_VOYAGES = 3

# THE HORIZON. Same tracked debt as every sibling at this address: the beat rate is not yet a
# real number, so 1000 pulses stands for "clearly a long standing" and MUST be re-tuned when
# it becomes one.
_HORIZON = 1000


def _walk() -> dict:
    """Every ticket carrying the key, every PROVED crossing since the migration, and whether
    the reader has grown a fallback to the stored copy."""
    carriers: list[dict] = []
    for path in sorted(_TICKETS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a ticket this probe cannot read is not a finding
            continue
        if isinstance(doc, dict) and "chart_chain" in doc:
            value = doc["chart_chain"]
            carriers.append({
                "ticket": doc.get("id") or path.stem[:12],
                "file": path.name,
                "kind": type(value).__name__,
                "entries": len(value) if isinstance(value, (dict, list, str)) else None,
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

    # THE FALLBACK CHECK — measured rather than trusted. A reading verb that consults the
    # ticket-side key is the same hand at one remove.
    fallback = []
    try:
        source = _READER.read_text(encoding="utf-8")
    except OSError as exc:
        fallback.append({"why": f"the reader module could not be read: {exc}"})
    else:
        for lineno, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if 'ticket.get("chart_chain")' in line or "ticket['chart_chain']" in line \
                    or 'get("chart_chain")' in line:
                fallback.append({"line": lineno, "text": stripped[:120]})

    # DISTINCT TICKETS, NOT CROSSINGS — and the difference is the whole anti-hollow clause.
    # A ticket may cross PROVED many times: 9579a6f9cec6 carries FIVE forward PROVED crossings,
    # each naming a different proof, which is why crossings.proven_by_since_buildme unions
    # across them instead of taking the latest. Counting crossings would therefore let ONE
    # ticket re-crossing three times satisfy "3 voyages have sailed since the migration" —
    # the clause would clear on a single voyage's bookkeeping, which is precisely the
    # a_pickup_is_witnessed failure it was written against. Caught 2026-09-10 by firing the
    # probe and reading a count of 2 beside a ticket list of 1.
    sailed = sorted({v["ticket"] for v in voyages if v["ticket"]})
    return {
        "carriers": carriers,
        "carrier_count": len(carriers),
        "voyages_since_migration": len(sailed),
        "voyage_tickets": sailed,
        "proved_crossings_since_migration": len(voyages),
        "reader_reads_the_stored_key": fallback,
    }


def survey_the_corpus() -> dict:
    """The walk, MEMOIZED on the tickets tree's ``(path, mtime_ns, size)`` fingerprint."""
    return settled("no_ticket_carries_a_stored_chart_chain", _TICKETS, _walk)


def _trigger(now, context: dict) -> bool:
    """TRUE the moment ANY ticket carries the key, or the reader grows a fallback to it.

    No floor and no warm-up, and that is the design rather than an oversight: this measures an
    absence, and an absence has no healthy non-zero value."""
    s = once(context, "corpus", survey_the_corpus)
    return bool(s["carrier_count"]) or bool(s["reader_reads_the_stored_key"])


def _enough(context: dict) -> bool:
    """CLEARED when no ticket carries the key, the reader names no fallback to it, AND at least
    three voyages have crossed PROVED since the migration.

    THE THIRD CLAUSE IS THE ANTI-HOLLOW ONE. Zero carriers is what the migration left behind;
    without traffic it says nothing about whether the door holds. And every clause can go back
    DOWN — one hand-written key re-opens this watch, which is the property ``pickups >= 1``
    never had."""
    s = once(context, "corpus", survey_the_corpus)
    return (s["carrier_count"] == 0
            and not s["reader_reads_the_stored_key"]
            and s["voyages_since_migration"] >= _ENOUGH_VOYAGES)


def _carry(context: dict) -> dict:
    s = once(context, "corpus", survey_the_corpus)
    if s["reader_reads_the_stored_key"]:
        finding = ("hollow itself reads the ticket-side chart_chain key again — a silent "
                   "preference for the stored copy, which is the same hand at one remove")
    else:
        finding = (f"{s['carrier_count']} ticket(s) carry a hand-written chart_chain key "
                   f"again; the instrument that gates PROVED would take its evidence from "
                   f"the ticket it is judging")
    return {
        "finding": finding,
        "counts": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "WRONG INTENT: the measurement is that ticket JSON no longer contains the key at "
            "all, not that a derivation exists. A key written back — or a fallback inside "
            "hollow — means a gate is reading evidence a hand typed, which is the whole "
            "defect: on 2026-09-10, 24 tickets carried the key with ZERO writers anywhere in "
            "the tree, while the BUILDME entry gate derived the same chain correctly."),
        "suggests": (
            "ask what wrote it. If a hand did, the answer is that nothing needs to — "
            "chain_for_ticket resolves the standing chain from the berths. If a TOOL did, "
            "that tool is writing a gate's own input and the finding is against the tool."),
    }


PROBE = Probe(
    why="has a hand written a chart_chain key back onto a ticket, or has hollow grown a "
        "fallback to the stored copy? — 24 tickets carried the key on 2026-09-10 with no "
        "writer anywhere in the tree, and the instrument gating PROVED believed them",
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
