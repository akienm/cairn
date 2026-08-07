"""PROBE — has anyone ever come through the pickup door?

Berth for the WATCHME that ticket ``a-summons-shows-its-pickup`` carries. Berthed beside
``cairn/base`` because that is WHAT IT WATCHES: the pickup door lives in
``cairn/base/transitions.py``, and the one way this design fails silently is the door
standing unused — every summons stamped ``:waiting`` by arrival, and not one pickup ever
journaled. That is a decorative door: the grammar would keep rendering phases, the board
would keep deriving "pending", and "is anyone on this?" would still be answered from side
channels, which is precisely the encapsulation failure the ruling
(the-ticket-is-the-source-period, 2026-08-07) exists to close.

THE EFFICACY QUESTION: did the pickup become a RECORDED ACT, or just a renderable one?
Arrival stamps ``:waiting`` mechanically — emit does it, nobody has to remember — so
arrivals accumulate for free. A pickup is the opposite: a hand must come through the door
on purpose. Counting the free half against the deliberate half is the honest measure of
whether the mechanism is alive: many arrivals and zero pickups is the summons carried by
nobody, the same silence ``does_optional_mean_never_carried`` (the sibling at this address)
watches for one layer up.

FILES ONLY, by construction: the probe walks class-space ``history.json`` files — no
device, no bus, no network — so it stays cheap enough to sit on a pulse. Refusals leave no
record (the door raises before it writes), so this probe reads only the half of the
evidence that exists: passes. That is the right half for THIS question — a witnessed
pickup is an existence claim, and one journaled record settles it.

AUTHORITY: none. This probe deposits and pokes; acting on the finding (making pickup a
crossing precondition, wiring the summons announcements) is the owner's call at the
register (Law 6) — both are named future dials in the definition, not this probe's rungs.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.base.probe import Probe, owning_ticket

_REPO_ROOT = Path(__file__).resolve().parents[3]

# The sample size below which the door's silence cannot be judged. A couple of :waiting
# arrivals with no pickup is a young mechanism; twelve arrivals and not one hand through
# the door is a pattern. Same floor, same reasoning, as the sibling probe beside this one.
_ENOUGH = 12

_OWNING_TICKET = "a-summons-shows-its-pickup"

# THE OWNING COMPONENT IS EXCLUDED from the corpus — both counts, both clauses. The sibling
# probe beside this one measured the failure live (2026-07-30): its first pulse counted its
# own author as the whole corpus, home-field advantage as a measurement. The analog here is
# sharper still, because the voyage that BUILT this door also sails through it: cairn/base's
# own history carries a pickup journaled by the door's builder minutes after the door
# landed, and counting it would clear the watch at birth. The question is whether ANYONE
# ELSE ever comes through; the author is not evidence for that.
_OWNING_COMPONENT = Path(__file__).resolve().parents[1]


def survey_the_corpus() -> dict:
    """Count, over every class-space history: records whose journaled workflow string
    carries a ``:waiting`` cursor (phased ARRIVALS — stamped for free by emit) and records
    journaled through the pickup door (``act == "pickup"`` — written on purpose by a hand).
    Also names which components' CURRENT cursor stands ``:waiting``, so the finding that
    rides back says where the unanswered summonses are, not just how many there were."""
    arrivals = pickups = 0
    waiting_now: list[str] = []
    for hist in sorted(_REPO_ROOT.rglob("history.json")):
        if ".git" in hist.parts or hist.parent == _OWNING_COMPONENT:
            continue
        try:
            records = json.loads(hist.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a corpus this probe cannot read is not a finding
            continue
        if not isinstance(records, list) or not records:
            continue
        for rec in records:
            if not isinstance(rec, dict):
                continue
            if rec.get("act") == "pickup":
                pickups += 1
            elif ":waiting]" in (rec.get("workflow") or ""):
                arrivals += 1
        last = records[-1]
        if isinstance(last, dict) and ":waiting]" in (last.get("workflow") or ""):
            waiting_now.append(str(hist.parent.relative_to(_REPO_ROOT)))
    return {"phased_arrivals": arrivals, "pickups": pickups,
            "waiting_cursors_by_component": waiting_now}


def _trigger(now, context: dict) -> bool:
    """TRUE when arrivals are many and pickups are ZERO. Both clauses load-bearing: firing
    early would poke the owner about a mechanism nobody has had reason to use yet; firing
    while any pickup stands journaled would poke about a door that demonstrably works."""
    s = context.get("corpus") or survey_the_corpus()
    return s["phased_arrivals"] >= _ENOUGH and s["pickups"] == 0


def _enough(context: dict) -> bool:
    """CLEARED by ONE witnessed pickup — an existence claim, settled by the first record.
    Mutually exclusive with the trigger BY CONSTRUCTION (``pickups >= 1`` vs
    ``pickups == 0``), with no floor asymmetry to rot in the quiet direction: the sibling
    probe's live fire proved a clear that can fire before the trigger can is the failure,
    so this pair shares the one variable and cannot both be true."""
    s = context.get("corpus") or survey_the_corpus()
    return s["pickups"] >= 1


def _carry(context: dict) -> dict:
    s = context.get("corpus") or survey_the_corpus()
    return {"finding": "summonses arrive :waiting and nobody has ever come through the "
                       "pickup door",
            "counts": s,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the pickup door is decorative — the phase renders but "
                                 "the act it exists to record never happens, so 'is "
                                 "anyone on this?' is still answered from side channels",
            "suggests": "back-edge a-summons-shows-its-pickup to WATCHME and re-open the "
                        "design: either the single-actor collapse means the door needs to "
                        "sit ON the crossing path (the named pickup-enforcement dial), or "
                        "picking up costs more than the answer is worth"}


# THE HORIZON (falsifier clause: armed, correct, and silent is indistinguishable from
# health without one). Same placeholder, same tracked debt, as the sibling probe at this
# address: the beat rate is not yet a real number, so 1000 pulses is "clearly a long
# standing" and MUST be re-tuned when it becomes one.
_HORIZON = 1000

PROBE = Probe(
    why="has anyone ever come through the pickup door? — arrivals stamp :waiting for "
        "free, a pickup is journaled on purpose, and many of the former with none of the "
        "latter is the ruled mechanism standing decorative",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the counts, and what the pair would do with them right now.
    s = survey_the_corpus()
    print(json.dumps({"corpus": s,
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2))
