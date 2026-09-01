"""PROBE — does a second hand ever meet the per-intention gate?

Berth for the WATCHME that ticket ``an-intention-declares-its-gated-hands`` carries
(object ``a-second-hand-meets-the-gate``). Berthed beside ``harbor_master`` because that
is WHAT IT WATCHES: the clearance gate reads ``gated_by`` from each intention's charter,
and until a SECOND actor crosses, the per-intention check is indistinguishable from a
constant.

THE HORIZON IS SHARED with the parent ticket (``boat-owner-is-read-not-stated``) and with
the sibling probe (``boat_owner_comes_from_the_boat``): one event — the first crossing by
a hand that is not this box's single hand — answers both, which is why the child ticket
was filed rather than built at the parent's crossing.

NOT SATISFIABLE BY VOLUME: a thousand crossings by one hand cannot distinguish a working
per-intention gate from a constant. ``enough`` requires at least one cleared crossing with
a distinct second actor.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket
from cairn.devices.cairn.machines.harbor_master.clearance import OwnerUnresolvable, boat_owner_of

_REPO_ROOT = Path(__file__).resolve().parents[6]
_CLASS_SPACE = _REPO_ROOT / "cairn"

_OWNING_TICKET = "an-intention-declares-its-gated-hands"

_ERA_FLOOR = "2026-09-01T00:00:00"


def _survey_cleared_crossings() -> dict:
    """Census every cleared crossing since the era floor, counting distinct actors."""
    actors: set[str] = set()
    cleared_count = 0
    crossings: list[dict] = []

    for hist in sorted(_CLASS_SPACE.rglob("history.json")):
        if ".git" in hist.parts:
            continue
        try:
            records = json.loads(hist.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(records, list):
            continue
        component = str(hist.resolve().parent.relative_to(_REPO_ROOT))
        for rec in records:
            if not isinstance(rec, dict) or not rec.get("cleared_by"):
                continue
            if str(rec.get("at", "")) < _ERA_FLOOR:
                continue
            actor = str(rec.get("actor", ""))
            actors.add(actor)
            cleared_count += 1
            crossings.append({
                "component": component,
                "seq": rec.get("seq"),
                "at": rec.get("at"),
                "actor": actor,
                "boat": rec.get("ticket"),
            })

    return {
        "era_floor": _ERA_FLOOR,
        "cleared_since_floor": cleared_count,
        "distinct_actors": sorted(actors),
        "crossings": crossings,
    }


_ENOUGH_CROSSINGS = 20


def _trigger(now, context: dict) -> bool:
    s = context.get("crossings") or _survey_cleared_crossings()
    return (s["cleared_since_floor"] >= _ENOUGH_CROSSINGS
            and len(s["distinct_actors"]) <= 1)


def _enough(context: dict) -> bool:
    s = context.get("crossings") or _survey_cleared_crossings()
    return len(s["distinct_actors"]) >= 2 and s["cleared_since_floor"] >= _ENOUGH_CROSSINGS


def _carry(context: dict) -> dict:
    s = context.get("crossings") or _survey_cleared_crossings()
    return {
        "finding": "per-intention gated_by is declared fleet-wide; whether the gate "
                   "discriminates requires a second hand — "
                   + ("%d cleared crossings by %d distinct actor(s) since %s"
                      % (s["cleared_since_floor"], len(s["distinct_actors"]), s["era_floor"])),
        "census": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's HORIZON is the first crossing by an actor that "
                             "is NOT the box's single hand. Until one exists the per-intention "
                             "gate has not been observed discriminating anything real.",
    }


_HORIZON = 1000

PROBE = Probe(
    why="gated_by is now declared on every intention and the clearance gate reads it — "
        "but every crossing in this system is made by one hand. A gate that admits exactly "
        "that hand and a gate that admits everyone are indistinguishable until a second "
        "actor crosses. Fires when enough crossings have passed with only one distinct actor.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = _survey_cleared_crossings()
    print(json.dumps({"census": s,
                      "would_trigger": _trigger(None, {"crossings": s}),
                      "enough": _enough({"crossings": s})}, indent=2))
