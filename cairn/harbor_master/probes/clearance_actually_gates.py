"""PROBE — the sixth seat is wired; do real crossings actually go THROUGH it?

Berth for the WATCHME that ticket ``emit-refuses-an-uncleared-crossing`` carries
(object ``clearance-actually-gates``). Berthed beside ``cairn/harbor_master`` because
that is WHAT IT WATCHES: harbor_master owns the authority rung, its charter states
its own falsifier — *"if devices advance workflows AROUND it once the clearance gate
lands (ambient transitions), the authority rung has failed (Law 6)"* — and Law 6 says
the back-edge that re-opens this node is the OWNER's act. The door being watched
berths in ``cairn/base/transitions.py``; the *authority* being watched is here.

THE HISTORY THIS EXISTS TO STOP REPEATING. The gate landed 2026-07-21 and was
measured 2026-08-05: of 229 records across 21 component histories, 146 were
emit-shaped and ZERO carried ``cleared_by``. By 2026-08-10 that was 186 and still
zero. The cause turned out not to be indiscipline — ``clear()`` had been
structurally UNCALLABLE for every gated crossing since 2026-07-29, because three
gates inside ``emit`` read ``journal_extra["ticket"]`` and ``clear()`` accepted no
``**journal_extra``. Nobody found out for a year because nobody was calling it. That
is the exact shape this probe is aimed at: a gate that is never exercised is
indistinguishable from a gate that works.

THE DEMANDED SET — and why this probe counts a NARROWER set than the ticket's spec
names. The ticket, authored before the build derived it, says "any journaled forward
crossing". What actually landed demands clearance of **a forward journaled crossing
INTO A REST** — ``not is_summons(target)``, the move that ENTERS proven-space —
derived from the grammar rather than from a component list, which is what let the
exemption roster stay EMPTY. Censusing every forward crossing would therefore red on
every ``BUILDME``/``PROVEME`` in the corpus at this probe's own birth: the check
going red at the moment its condition is satisfied. **A probe watches what the gate
DEMANDS.** The narrowing is named here rather than taken quietly, and the ticket's
own text carries the same correction.

WHAT A REFUSAL COSTS TO COUNT — THE IOU THIS PROBE FILED, AND ITS PAYMENT. Clause
(c) and the refusal half of ``enough`` both ask whether clearance has ever said NO
to a real crossing. When this probe was armed on 2026-08-10 **nothing recorded
that**: every refusal raised before ``emit`` was reached, so a refused move left no
record at all, and this file reported ``refusals_recorded: 0`` with the absence
named rather than faked — an IOU pointing at ticket ``clearance-leaves-a-trace``
(cast 2026-07-26) as the one build that would make its own horizon countable.

That ticket landed the same day, and the number is now READ rather than asserted:
``survey_the_refusals`` below counts what the gate actually answered, by reason
class. The IOU is retired at the address that filed it — a SECOND probe over the
same store, with this one still hard-coding a zero beside it, would have been the
parallel-roster failure with the answer sitting one file away. The reading itself
belongs to the gate (``clearance.read_attempts``), which owns the queue and is
therefore the one place its block name and event names are spelled; what lives here
is the counting, which is nobody's but this watch's.

WHAT THE QUEUE CANNOT TELL US, and it is the same shape as the caveat above. The
queue records attempts at the GATE; the census above counts crossings in the
JOURNAL. A refusal never becomes a journaled crossing (that is what a refusal is),
so the two are not two views of one population and are never divided into each
other here. Refusals are an existence signal for clause (c) — has the door ever
said no — not a rate.

A COUNTED FIXTURE REFUSAL WOULD BE A LIE. ``cairn/base/proofs/test_transitions.py``
holds teeth that make the gate refuse, and they are sealed green — but a refusal
manufactured by its own proof is not evidence that the gate ever stood in a real
crossing's way. The seal answers "is the code correct"; this probe answers "did it
ever have to be". Now that refusals are recorded, that sentence has teeth of its
own: every proof that exercises ``clear()`` redirects ``CAIRN_LB_TRACE_ROOT`` at a
scratch root, and ``proofs/test_clearance.py`` carries a tooth asserting the LIVE
queue file came out of the run byte-identical. So the corpus this probe reads is the
live one by construction, not by anybody remembering.

FILES ONLY, by construction: class-space ``history.json`` files under ``cairn/`` —
no device, no bus, no network — cheap enough to sit on a pulse. Same discipline as
the three siblings at ``cairn/base/probes/``.

AUTHORITY: none. This probe deposits and pokes; acting on the finding — widening the
roster, back-edging the ticket, or building the trace — is the owner's call at the
register (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.base.probe import Probe, owning_ticket
from cairn.harbor_master.clearance import GRANTED, read_attempts

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CLASS_SPACE = _REPO_ROOT / "cairn"

# How many refused attempts ride back verbatim. NOT a silent cap: the carry states the
# window and the total beside it, so a consumer can never mistake the tail for the whole.
# The complete-diagnostic rule wants everything needed to resolve the finding in the first
# report; the finding is "the door has never refused", and for that the RECENT refusals
# are what a reader acts on.
_VERBATIM = 20

_OWNING_TICKET = "emit-refuses-an-uncleared-crossing"

# THE ERA FLOOR — set at arming time, 2026-08-10, between this voyage's PROVEME
# crossing (16:35:23, made before the seat could clear anything) and its PROVED
# crossing (the first cleared crossing in the system's recorded life, and the one the
# ticket's falsifier demands). Everything before it is the 186 uncleared records the
# ticket exists to close, and they are a RECORD OF TRUTH (Law 7): never rewritten,
# never backfilled, and never counted against a gate that did not exist when they
# were made. A date is provenance here — when the seat began demanding — not a dial.
_ERA_FLOOR = "2026-08-10T16:40:00"

# The sample size below which silence cannot be judged, and it is the ticket's own
# HORIZON transcribed rather than a fresh number: "the next 20 journaled crossings
# after PROVED. If fewer than all 20 carry cleared_by or a NAMED exemption, the gate
# did not land." Same floor for the trend clause and for `enough`, so the pair cannot
# drift apart. A hand-set constant in a gate is a learns-its-gates IOU; this one is
# owed to the ticket that set it.
_ENOUGH = 20

# Falsifier clause (1), caught while it is still a TREND: "the gate is wired but every
# real crossing takes a named exemption — an exemption roster that grows to cover the
# fleet is the gate not landing, wearing a roster's clothes." One exemption in four is
# the line the ticket's watchme spec drew.
_EXEMPT_IN = 4


def _is_summons(state: str) -> bool:
    """A summons is a state whose name ends in ME. Spelled through the chokepoint's own
    predicate so this probe cannot develop a second opinion about what the gate demands
    (Law 1 — one implementation of a settled question)."""
    from cairn.base.transitions import is_summons
    return is_summons(state)


def survey_the_refusals() -> dict:
    """THE READER of the gate's queue (ticket clearance-leaves-a-trace): how often the gate
    was asked, how often it said no, and by which reason class.

    THE READING IS THE GATE'S OWN (``clearance.read_attempts``); only the COUNTING is here.
    That split is Law 6 and Law 1 together: harbor_master owns the queue, so the one place
    that knows its block name, its two event names and its consumer is the gate — a probe
    with its own copy of that vocabulary is a probe that can silently stop matching the
    writer, and the day it does it reports zero refusals, which is exactly the wrong answer
    to be confident about. Aggregation is not the store's business, so it is not down there."""
    q = read_attempts()
    granted = refused = 0
    by_reason: dict[str, int] = {}
    recent: list[dict] = []
    for a in q["attempts"]:
        if a["event"] == GRANTED:
            granted += 1
        else:
            refused += 1
            by_reason[a["reason_type"]] = by_reason.get(a["reason_type"], 0) + 1
            recent.append(a)
    return {"queue": q["queue"],
            "asked": granted + refused,
            "granted": granted,
            "refused": refused,
            "by_reason": by_reason,
            "recent_refusals": recent[-_VERBATIM:],
            "recent_refusals_window": min(len(recent), _VERBATIM),
            "unreadable_lines": q["unreadable_lines"]}


def survey_the_crossings() -> dict:
    """Census the DEMANDED SET since the era floor: forward journaled crossings into a
    rest, across every component history in class-space, each classified as cleared,
    exempt, or bypassed.

    Every offending crossing rides back VERBATIM with its component, seq, actor and
    date, so the consumer never re-derives them (the complete-diagnostic rule: a
    finding delivers everything needed to resolve it in its first report)."""
    queue = survey_the_refusals()
    cleared: list[dict] = []
    exempt: list[dict] = []
    bypassed: list[dict] = []

    for hist in sorted(_CLASS_SPACE.rglob("history.json")):
        if ".git" in hist.parts:
            continue
        try:
            records = json.loads(hist.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a corpus this probe cannot read is not a finding
            continue
        if not isinstance(records, list):
            continue
        component = str(hist.resolve().parent.relative_to(_REPO_ROOT))
        for rec in records:
            if not isinstance(rec, dict):
                continue
            target = rec.get("to")
            if not (rec.get("from") and isinstance(target, str)):
                continue                                   # not emit-shaped
            if rec.get("direction") != "forward":
                continue                                   # a retreat is ungated by design
            if _is_summons(target):
                continue                                   # outside the demanded set
            if str(rec.get("at", "")) < _ERA_FLOOR:
                continue                                   # Law 7: the record stands, uncounted
            row = {"component": component, "seq": rec.get("seq"), "at": rec.get("at"),
                   "actor": rec.get("actor"), "to": target, "ticket": rec.get("ticket")}
            note = str(rec.get("clearance_gate") or "")
            if rec.get("cleared_by"):
                cleared.append({**row, "cleared_by": rec.get("cleared_by"),
                                "proven_by": rec.get("proven_by")})
            elif note.startswith("exempt"):
                exempt.append({**row, "clearance_gate": note})
            else:
                bypassed.append(row)

    total = len(cleared) + len(exempt) + len(bypassed)
    recent = sorted(cleared + exempt + bypassed,
                    key=lambda r: str(r.get("at") or ""))[-_ENOUGH:]
    recent_exempt = sum(1 for r in recent if "clearance_gate" in r)
    recent_cleared = sum(1 for r in recent if "cleared_by" in r)
    return {"era_floor": _ERA_FLOOR,
            "demanded_total": total,
            "cleared": cleared,
            "exempt": exempt,
            "bypassed": bypassed,
            "recent_window": len(recent),
            "recent_exempt": recent_exempt,
            "recent_cleared": recent_cleared,
            # READ, not asserted, since 2026-08-10 (ticket clearance-leaves-a-trace). A zero
            # here now MEANS something — before the queue existed it only meant nobody was
            # recording, which is why it was labeled and never used as evidence.
            "refusals_recorded": queue["refused"],
            "refusal_source": queue["queue"],
            "queue": queue}


def _roster_covers_the_fleet(s: dict) -> bool:
    """Falsifier clause (1) as a trend: over the last 20 demanded crossings, more than
    one exemption per four clearances. Zero clearances with any exemption at all is the
    limiting case and fires — that is the roster BEING the mechanism."""
    if s["recent_window"] < _ENOUGH:
        return False
    return s["recent_exempt"] * _EXEMPT_IN > s["recent_cleared"]


def _never_said_no(s: dict) -> bool:
    """The hollow-gate signal: enough crossings have accumulated and clearance has never
    once refused one. A door that has never said no is not yet KNOWN to be a door."""
    return s["demanded_total"] >= _ENOUGH and s["refusals_recorded"] == 0


def _trigger(now, context: dict) -> bool:
    """TRUE on any of the ticket's three conditions. (a) is the sharpest and has no
    floor — one bypassed crossing after the era floor is the gate having been walked
    around, and waiting for a sample would be waiting to confirm what one record already
    proves. (b) and (c) need the sample, and carry it."""
    s = context.get("crossings") or survey_the_crossings()
    return bool(s["bypassed"]) or _roster_covers_the_fleet(s) or _never_said_no(s)


def _enough(context: dict) -> bool:
    """CLEARED when the ticket's horizon is met AND the gate is known to be a door: 20
    post-era demanded crossings, every one cleared or exempt, the roster not covering
    the fleet, and at least one REAL refusal on record.

    MUTUALLY EXCLUSIVE WITH THE TRIGGER BY CONSTRUCTION, and the roster clause is what
    makes that true. The ticket's authored ``enough`` said only "all of them carrying
    cleared_by or a named exemption" — under which a corpus whose every crossing took an
    exemption would CLEAR the watch at exactly the moment falsifier clause (1) was met.
    That is the check going green for the wrong reason, so the clause is transcribed
    here and the correction recorded on the ticket in the same act.

    The refusal half cannot be satisfied today; see the header. That is the watch's
    standing pressure toward ``clearance-leaves-a-trace``, not an oversight."""
    s = context.get("crossings") or survey_the_crossings()
    return (s["demanded_total"] >= _ENOUGH
            and not s["bypassed"]
            and not _roster_covers_the_fleet(s)
            and s["refusals_recorded"] >= 1)


def _carry(context: dict) -> dict:
    s = context.get("crossings") or survey_the_crossings()
    which = []
    if s["bypassed"]:
        which.append("(a) a crossing into a rest landed carrying NEITHER cleared_by NOR a "
                     "named exemption — the gate was walked around after it was built")
    if _roster_covers_the_fleet(s):
        which.append("(b) named exemptions exceed one in four over the last %d crossings — "
                     "the roster growing to cover the fleet, which is falsifier clause (1) "
                     "caught as a trend" % _ENOUGH)
    if _never_said_no(s):
        which.append("(c) %d demanded crossings since the era floor and clearance has never "
                     "REFUSED one — a door that has never said no is not yet known to be a "
                     "door" % s["demanded_total"])
    return {"finding": "the clearance seat is wired into emit; whether real crossings go "
                       "THROUGH it is the question, and " + (" / ".join(which) or
                                                             "no condition fired"),
            "conditions_fired": which,
            "census": s,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket's DONE requires that at least one real voyage "
                                 "crossing has passed THROUGH clearance and carries "
                                 "cleared_by on disk, and its HORIZON is the next 20 "
                                 "journaled crossings after PROVED",
            "suggests": "read the bypassed crossings verbatim above — each names the "
                        "component, seq and actor that made it. A bypass means a caller "
                        "reached emit directly; the fix is at that caller, not in the gate. "
                        "For (c), the queue named in census.refusal_source is now the "
                        "instrument — read census.queue.by_reason before concluding "
                        "anything: a door that is asked and always says yes is a different "
                        "finding from a door nobody asks."}


# THE HORIZON (falsifier clause: armed, correct, and silent is indistinguishable from
# health without one). Same placeholder, same tracked debt, as the three siblings at
# cairn/base/probes/: the beat rate is not yet a real number, so 1000 pulses is "clearly
# a long standing" and MUST be re-tuned when it becomes one.
_HORIZON = 1000

PROBE = Probe(
    why="the sixth seat refuses an uncleared crossing into a rest — do real crossings "
        "actually go THROUGH it? A bypassed crossing, a roster growing to cover the "
        "fleet, or a gate that has never once refused are the three ways it lands wired "
        "and hollow",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the census, and what the pair would do with it right now.
    s = survey_the_crossings()
    print(json.dumps({"census": s,
                      "would_trigger": _trigger(None, {"crossings": s}),
                      "enough": _enough({"crossings": s})}, indent=2))
