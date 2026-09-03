"""PROBE — did the floor's bulk push the ceiling's judgement out of the packet?

Berth for the WATCHME that ticket ``constrain-floor-authors-and-provenance-is-measured``
carries (object ``the-floor-does-not-crowd-out-the-ceiling``). Berthed here, beside the
machine, because that is WHAT IT WATCHES; the ticket it was compiled from lives in
CairnCommons and this probe deliberately does not follow it there.

THE EFFICACY QUESTION, and why it is this one and not orient's. At orient the open
question was whether the floor's answer would ever be REUSED — the risk was that the
floor did nothing. Here the floor's output is bulky by construction: three constraints
per grounded component, and a real request grounds five to ten of them. So constrain's
worst failure runs the OTHER WAY. A ceiling handed twenty ready-made charter constraints
writes fewer of its own, the packet loses the law, ruling, ticket and memory constraints
that were the reason a mind was in the loop at all, and THE DIAL READS THAT AS PROGRESS —
the floor fraction climbs while the packet gets worse. It is the one failure where every
instrument in the system says the build worked.

THE BASELINE IS THE PRE-BUILD CORPUS AND IS RECOMPUTED, NEVER FROZEN. Over the 41 berths
that predate the door: 394 constraints, 148 charter and 246 of other kinds, a median of 6
non-charter constraints per packet and A MINIMUM OF 2 — no packet the ceiling ever wrote
carried fewer than two constraints of its own. That minimum is the threshold, and it is
the corpus's number rather than a constant someone chose: a hand-set gate is a learned
value stranded in a human's head. The pre-build population is closed (nothing will ever
be added to it), so recomputing it each read costs nothing and keeps the number honest if
a berth is ever found to be unreadable.

WHY NON-FLOOR AND NOT TOTAL. The floor produces only the kinds it declares in
``FLOOR_KINDS``, so the total count rises the moment the build works, and rises fastest
exactly when crowding-out is worst. Counting totals would make this probe fire never. The
ceiling's contribution is what is at risk and it is what is counted — and the set of kinds
that belong to the floor is ASKED of the floor, so a floor that gains a kind does not
silently move the line this probe is drawn on.

THE POPULATION IS POST-BUILD BERTHS ONLY, by filename stamp. The 41 that predate the door
were written under a floor that discarded 86% of its refs; counting them here would mix
two populations and guarantee the watch reads whatever the old corpus says (Law 7 — a
record of truth is not re-judged by a later rule).

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that
re-opens a node whose intention did not work is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import median

from cairn.tools.base.probe import Probe, owning_ticket
from cairn.devices.codemonkey.machines.constrain.constrain import FLOOR_AUTHORED, FLOOR_KINDS

# Instance-space, resolved per call and never captured at import — a probe that froze the
# path would keep reading a root the system had already left.
_BERTH_ENV = "CAIRN_CHART_PACKETS"
_BERTH_DEFAULT = Path.home() / ".cairn/devices/chart/0/packets"

# The door landed on 2026-08-14. Berths are named ``constrain-<YYYYmmddTHHMMSS>-<digest>``,
# so the stamp IS the population filter.
_DOOR_LANDED = "20260814T000000"

# The sample below which a shifted median says nothing. The chain fires once per voyage
# and the corpus grew 41 constrain packets in three weeks, so twelve post-build berths is
# roughly a working week of real voyages.
_ENOUGH = 12

_TICKET = owning_ticket("constrain-floor-authors-and-provenance-is-measured")


def _kinds(packet: dict) -> tuple[int, int]:
    """(floor-kind, other-kind) constraint counts for one packet. A constraint that is
    not a dict, or carries no ``kind``, counts as OTHER — the floor always stamps its
    own, so anything unstamped came from the ceiling.

    THE FLOOR'S KINDS ARE ASKED FOR, NOT SPELLED HERE, and correcting that is why this
    probe was touched at all. It read ``kind == "charter"`` — true for as long as the
    floor had exactly one kind, and wrong in the floor's FAVOUR the instant it gained a
    second: every ``check`` constraint the floor authored would have been counted as the
    ceiling's own contribution, so a packet in which the ceiling had gone completely
    silent would read as healthy on the strength of the floor's bulk. That is this
    probe's own failure mode — the instrument flattering the thing it measures — and it
    would have arrived armed, which is worse than arriving absent.

    Asking ``FLOOR_KINDS`` also means the next kind needs no edit here. A probe that must
    be remembered when the thing it watches changes is a probe that will be wrong exactly
    once, silently, at the moment that matters.
    """
    floor = other = 0
    for c in packet.get("constraints") or []:
        if isinstance(c, dict) and c.get("kind") in FLOOR_KINDS:
            floor += 1
        else:
            other += 1
    return floor, other


def survey_the_berths() -> dict:
    """Both populations in one pass: the closed pre-build corpus that sets the threshold,
    and the post-build berths the watch is actually about.

    A berth this probe cannot read is skipped rather than counted in either direction —
    the counts are a claim (Law 3), and a claim resting on a parse failure is worse than
    a smaller n.
    """
    berths = Path(os.environ.get(_BERTH_ENV) or _BERTH_DEFAULT)
    before: list[int] = []
    after: list[int] = []
    after_named: list[tuple[str, int]] = []
    floor_after = 0
    earned_floor = 0
    per_field = {f: 0 for f in FLOOR_AUTHORED}

    for path in sorted(berths.glob("constrain-*.json")) if berths.is_dir() else []:
        stamp = path.name.split("-")[1] if path.name.count("-") >= 2 else ""
        try:
            packet = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(packet, dict):
            continue
        floor_kind, other = _kinds(packet)
        if stamp < _DOOR_LANDED:
            before.append(other)
            continue
        after.append(other)
        after_named.append((path.name, other))
        floor_after += floor_kind
        prov = packet.get("provenance") or {}
        if any(prov.get(f) == "floor" for f in FLOOR_AUTHORED):
            earned_floor += 1
        for f in FLOOR_AUTHORED:
            if prov.get(f) == "floor":
                per_field[f] += 1
    # After the loop, never inside it: the threshold is a property of the WHOLE pre-build
    # corpus, and computing it mid-walk would make the answer depend on the order the
    # berths were read — true today because the stamps happen to sort, and silently wrong
    # the first time they do not.
    bar = min(before) if before else 2
    starved = [name for name, other in after_named if other < bar]

    return {
        "pre_build_berths": len(before),
        "pre_build_other_median": median(before) if before else None,
        "pre_build_other_min": min(before) if before else None,
        "post_build_berths": len(after),
        "post_build_other_median": median(after) if after else None,
        "post_build_other_min": min(after) if after else None,
        "post_build_floor_total": floor_after,
        "earned_floor": earned_floor,
        "per_field": per_field,
        "starved_berths": starved[:10],
        "starved_count": len(starved),
    }


def _floor(survey: dict) -> int:
    """The threshold, read off the closed pre-build corpus. The literal is the fallback
    for a corpus this probe cannot read at all, and it is the number that corpus in fact
    holds — stated so a reader can tell a fallback from a measurement."""
    got = survey.get("pre_build_other_min")
    return got if isinstance(got, int) else 2


def _trigger(now, context: dict) -> bool:
    """TRUE when enough packets have been written under the new door AND their median
    non-charter constraint count has fallen below anything the pre-build ceiling ever
    wrote. Both clauses carry weight: firing on a small corpus pokes the owner about
    noise, and firing while the ceiling is still writing its own constraints pokes about
    a build that is working."""
    s = context.get("berths") or survey_the_berths()
    if s["post_build_berths"] < _ENOUGH:
        return False
    return (s["post_build_other_median"] or 0) < _floor(s)


def _enough(context: dict) -> bool:
    """CLEARED when the corpus is big enough to judge and the ceiling's own contribution
    is holding at or above the pre-build floor — the claim this build has to survive.

    NOT cleared on 'the floor earned its label', which is the tempting clause and the
    wrong one: the label going up is what crowding-out LOOKS like, so clearing on it
    would retire the watch precisely when it should bite."""
    s = context.get("berths") or survey_the_berths()
    return (s["post_build_berths"] >= _ENOUGH
            and (s["post_build_other_median"] or 0) >= _floor(s))


def _carry(context: dict) -> dict:
    """The datum that rides back — every count needed to resolve it on the first pass,
    and a POINTER to the ticket rather than a copy of it (Law 6 — the ticket is the
    commons')."""
    s = context.get("berths") or survey_the_berths()
    return {
        "finding": "since the floor started authoring constraints, the ceiling's own "
                   "constraints have thinned below anything the pre-build corpus shows",
        "counts": s,
        "threshold": {"non_charter_per_packet_floor": _floor(s),
                      "derived_from": "the minimum over the closed pre-build corpus"},
        "ticket": _TICKET,
        "against_falsifier": "clause (2): the derived floor fraction goes UP while the "
                             "packets get thinner — the one failure mode where the dial "
                             "reads the damage as progress",
        "suggests": "read skills/chart/SKILL.md stage 2 first: the ceiling is instructed "
                    "to carry the floor's constraints through and ADD the law, ruling, "
                    "ticket and memory constraints that need judgement. A thin packet "
                    "usually means that instruction now reads as 'the list is already "
                    "full'. Check 'post_build_floor_total' against "
                    "'post_build_berths' — a large ratio is the floor's bulk doing it, a "
                    "small one means the ceiling went quiet for some other reason, and "
                    "those are different fixes",
    }


# THE HORIZON, in pulses because the shim counts pulses. Nothing pulses this shim yet (the
# wall-clock backing is a filed edge in cairn/devices/cairn/machines/ground_loop/loop.py, not built), so
# the loudness rides the read-side door (``BaseShim.overdue()``) alone. Honest as a
# placeholder, dishonest as a measurement, and MUST be re-tuned when the beat is real.
_HORIZON = 1000

PROBE = Probe(
    why="did the floor's bulk crowd the ceiling's judgement out of the packet? — the "
        "floor now writes three constraints per grounded component, and the failure this "
        "build can cause is a packet that loses its law, ruling and memory constraints "
        "while the dial reads the loss as a rising floor fraction. Cleared when the "
        "ceiling's own contribution holds at or above what the pre-build corpus shows.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
