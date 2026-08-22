"""PROBE — the trail and the meter both record every inference call; do they go on AGREEING?

Berth for the WATCHME that ticket ``an-inference-call-logs-that-it-started`` carries. Berthed
beside ``cairn/devices/inference_domain`` because that is WHAT IT WATCHES: as of 2026-08-18
``domain.resolve`` writes one emission file per call into ``~/.cairn/logs/inference_domain/0/``
at each of its three branches, pointer carried as a canonical digest, beside the row it has
always written into ``inference_calls``.

WHY AGREEMENT IS THE QUESTION, AND NOT "IS THERE A LOG". The store has recorded every call at
this door since long before the trail existed, so the trail is a SECOND record of the same
events — and two records of one event that disagree are worse than one record (Law 7). That is
also what makes the ticket falsifiable rather than merely satisfiable: a hollow trail can be
made to say anything, but it cannot be made to match a store it does not write. The proof
beside the code settles that the two agree in a fixture world on the day it shipped. Whether
they keep agreeing over live traffic is a fact about live traffic, and this system has already
watched a sealed door with green proofs get routed around by six voyages in two days.

THE FINDING (trigger), three shapes, matched by CANONICAL rather than by clock:

  1. A post-era ``verdict='miss'`` row with no matching miss line on the trail. The call
     happened and the picture does not show it — the emitter stopped firing, or fired into a
     different world.
  2. A post-era miss LINE naming a call the store never got. The opposite drift: a record of
     something that, as far as the meter is concerned, never occurred.
  3. THE ABSENCE THAT LOOKS LIKE NOTHING — post-era misses standing in the store and NO TRAIL
     FILE AT ALL. Reported as its own field rather than only as N instances of shape 1,
     because "the trail is gone" and "four calls slipped past it" are different failures with
     different first moves, and a reader handed a list of 400 canonicals will not see which
     one they are looking at.

MATCHED BY CANONICAL, NOT BY TIME, and the reason is measured. The trail line is stamped at the
moment ``resolve`` STARTS (its ``moment``); the row's ``created`` is stamped after the host has
answered. On the very first live call those differed by six seconds — 14:27:47 against
14:27:53 — so any window arithmetic tight enough to be useful would report the same call as
missing from one side. The canonical is the same string in both records, which is why it is the
join, and per-canonical COUNTS are compared rather than sets: one question can legitimately
miss twice once its horizon expires, and a set comparison would call that agreement.

THE ERA FLOOR IS PLACED IN A MEASURED GAP, not on the day. Every one of the 2,616 rows written
before this build has no trail line and never could have; counting them would make shape 1 fire
forever on a question nobody is asking — the same day-wide-cutoff error that made a sibling
probe report five imaginary offenders on the morning its mechanism shipped. Measured at the
close: the last pre-seam row landed at 14:18:33-06:00 and the first post-seam row at
14:27:53-06:00, with nothing in between, so any floor inside that gap picks out exactly the
same population and the exact minute is not load-bearing.

WHAT THIS PROBE PARTLY WATCHES IS THE VOYAGE THAT ARMED IT, said out loud rather than glossed:
the first two records it counts are this build's own live fire. They are honest evidence — a
real call to a real host — but they are the author's own participation, and the ``enough``
floor is what keeps them from being mistaken for an answer.

AUTHORITY: none. This probe deposits and pokes; fixing a stopped emitter or back-edging the
ticket is the owner's act (Law 6).

FILES AND ONE STORE READ — no device, no bus, no network, so it stays cheap enough for a pulse.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "an-inference-call-logs-that-it-started"

# The moment the emit sites went live, placed in the measured gap described above.
_ERA = datetime.fromisoformat("2026-08-18T14:20:00-06:00")

# The sample size below which the question cannot be answered: agreement between two empty
# records is not agreement. A hand-set constant, and therefore a learns-its-gates IOU named at
# the ticket's horizon — the same debt the three sibling probes at this address carry. Twelve
# because organic traffic here is the graph-tree's embed calls, which arrive in the dozens per
# working session, so it is most of a session rather than a wait.
_ENOUGH = 12


def _post_era_row(row: dict) -> bool:
    created = row.get("created")
    if not isinstance(created, datetime) or created.tzinfo is None:
        return False            # a dateless row cannot be placed against the era
    return created >= _ERA


def _post_era_line(record: dict) -> bool:
    try:
        return datetime.fromisoformat(str(record.get("ts"))) >= _ERA
    except (TypeError, ValueError):
        return False            # an unparseable stamp cannot be placed against the era


def judge(trail_records: list[dict], rows: list[dict], *, trail_exists: bool = True) -> dict:
    """The pure judgement, separable from both reads so the proof can feed it fixtures.

    OFFENDERS ARE NAMED, NOT COUNTED. The ticket's carrier clause says why in its own words:
    "they disagree by 4" is a finding nobody can act on and "these four calls are in the store
    and not the trail" is one somebody can open. So each side reports the canonicals and how
    many times each is short.
    """
    rows_post = [r for r in rows if _post_era_row(r)]
    lines_post = [rec for rec in trail_records if _post_era_line(rec)]

    from cairn.devices.inference_domain.domain import canonical_digest
    row_misses = Counter(canonical_digest(str(r.get("canonical"))) for r in rows_post if r.get("verdict") == "miss")
    line_misses = Counter(str(rec.get("pointer")) for rec in lines_post if rec.get("gate") == "miss")

    in_store_not_in_trail = [
        {"canonical": c, "short_by": n - line_misses.get(c, 0)}
        for c, n in sorted(row_misses.items()) if n > line_misses.get(c, 0)
    ]
    in_trail_not_in_store = [
        {"canonical": c, "short_by": n - row_misses.get(c, 0)}
        for c, n in sorted(line_misses.items()) if n > row_misses.get(c, 0)
    ]

    return {"era": _ERA.isoformat(),
            "trail_exists": trail_exists,
            "post_era_rows": len(rows_post),
            "post_era_lines": len(lines_post),
            "store_misses": sum(row_misses.values()),
            "trail_misses": sum(line_misses.values()),
            # Shape 3: the store saw calls and there is no trail to have missed them.
            "no_trail_at_all": bool(not trail_exists and row_misses),
            "in_store_not_in_trail": in_store_not_in_trail,
            "in_trail_not_in_store": in_trail_not_in_store}


def survey_the_corpus() -> dict:
    """The live read: the store through its one door, and the trail at the address the DEVICE
    declares rather than one spelled here.

    Asking ``domain.diagnostic_trail()`` rather than rebuilding the path is the point — if the
    device's berth ever moves, a probe carrying its own copy of the address goes on reading an
    empty directory and reports a catastrophe that is really a stale constant. A DB this probe
    cannot reach raises rather than reporting a clean zero, because a silent 0/0 reads as both
    "no finding" and "not yet enough".
    """
    from cairn.devices.db_domain import store            # late: imports clean without a DB
    from cairn.devices.inference_domain import domain
    from cairn.tools.base.breadcrumb_log import BreadcrumbLog, LogUnreadable

    trail = domain.diagnostic_trail()
    exists = trail is not None and trail.exists()
    records: list[dict] = []
    if exists:
        try:
            log = BreadcrumbLog("inference_domain", 0)
            records = log.records()
        except LogUnreadable:
            records.append({"ts": None, "gate": "(unparseable)", "pointer": None})
    return judge(records, store.read("inference_calls"), trail_exists=exists)


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE on the FIRST disagreement, in either direction. There is no rate to be patient
    about here: every call is supposed to be in both records, so one that is not is the
    finding. Volume is never the trigger — a busy day is not a defect."""
    s = _corpus(context)
    return bool(s["in_store_not_in_trail"]) or bool(s["in_trail_not_in_store"])


def _enough(context: dict) -> bool:
    """CLEARED once enough real calls have crossed to judge AND every one of them is in both
    records. The floor is the non-vacuity tooth and it is doing real work: without it this
    clears at n=0, because an empty store disagrees with an empty trail about nothing — a
    watch that can clear before it can fire is not a watch."""
    s = _corpus(context)
    return (s["store_misses"] >= _ENOUGH
            and not s["in_store_not_in_trail"]
            and not s["in_trail_not_in_store"])


def _carry(context: dict) -> dict:
    s = _corpus(context)
    parts = []
    if s["no_trail_at_all"]:
        parts.append(f"THERE IS NO TRAIL FILE, and the store holds {s['store_misses']} "
                     f"post-era misses — the emitter is not writing at all")
    elif s["in_store_not_in_trail"]:
        parts.append(f"{len(s['in_store_not_in_trail'])} canonical(s) the store recorded as "
                     f"misses have no matching line on the trail")
    if s["in_trail_not_in_store"]:
        parts.append(f"{len(s['in_trail_not_in_store'])} canonical(s) on the trail name calls "
                     f"the store never got")
    return {"finding": "; ".join(parts) or "the trail and the meter disagree",
            "window": {"era": s["era"], "post_era_rows": s["post_era_rows"],
                       "post_era_lines": s["post_era_lines"]},
            "counts": {"store_misses": s["store_misses"], "trail_misses": s["trail_misses"]},
            "trail_exists": s["trail_exists"],
            "in_store_not_in_trail": s["in_store_not_in_trail"],
            "in_trail_not_in_store": s["in_trail_not_in_store"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket's clause (c) is that the count of miss records in "
                                 "the trail EQUALS the count of verdict='miss' rows over the "
                                 "same window — a standing inequality kills it, and the "
                                 "specific canonicals above are which calls it is about",
            "suggests": "open domain.resolve()'s miss branch first: an emit that stopped firing "
                        "and an emit whose records went to another world look identical from "
                        "the store's side. If the trail file is missing entirely, check whether "
                        "something called set_diagnostic_roots or silenced the receiver and did "
                        "not put it back — a proof leaving the device pointed at a deleted temp "
                        "tree is the shape that has already been reached for once"}


# Same placeholder horizon and same tracked debt as the three sibling probes in this folder:
# the unit is PULSES because the shim counts pulses, nothing pulses this shim today, and 1000
# is "clearly a long standing" against any beat rate we would plausibly pick. Honest as a
# placeholder and dishonest as a measurement.
_HORIZON = 1000

PROBE = Probe(
    why="the store has recorded every call at this door for months and the trail is a second "
        "record of the same events; the proofs settle that they agree in a fixture world on "
        "the day it shipped, and whether they keep agreeing is a fact about live traffic",
    trigger=_trigger,
    to="inference_domain",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
