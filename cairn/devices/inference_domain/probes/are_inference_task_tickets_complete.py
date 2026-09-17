"""PROBE — every inference call now writes a task ticket; are the tickets actually COMPLETE?

Berth for the WATCHME that ticket ``ea4a6151300f`` carries (object
``inference-task-tickets-are-complete``). Berthed beside ``cairn/devices/inference_domain``
because that is WHAT IT WATCHES: since this build every ``domain.resolve`` writes one JSON
artifact into the device's own instance-space (``devices/inference_domain/0/tickets/``)
carrying who asked, what they asked for versus what the route selected, how the call ended,
and — on a refusal — the trouble it raised. The proof enforces the shape on a stub resolver.
The one place the shape can still fail is LIVE, where the callers are real: a call that
arrives with no sender and no class-space frame records ``unknown``, and a caller population
that is ALL ``unknown`` is a field that exists and measures nothing.

THE FINDING (trigger): after the tickets have accumulated past the ticket's own floor of 20,
a ticket that ``domain.ticket_lacks`` judges incomplete — one predicate, shared with the proof,
so the probe and the proof cannot disagree about the word "complete". A refusal with no
trouble beside it is the same finding (the ticket's WRONG INTENT clause: a parallel path that
duplicates or skips the trouble lane).

THE CLEAR (enough), verbatim from the watch spec: at least 10 tickets carry a caller identity
that is not ``unknown`` AND at least one failure has raised a trouble; OR 100 tickets stand
with zero trouble integrations — that second arm is not a pass, it is the watch giving up on
waiting for a refusal that live traffic never produced, and the carry says which arm cleared.

THE ERA FLOOR: the tickets folder did not exist before this build, so there is no pre-era
population to floor out; every file in it is post-era by construction.

AUTHORITY: none. This probe deposits and pokes; back-edging the ticket is the owner's act.
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket, once

_OWNING_TICKET = "ea4a6151300f"

# The watch spec's own numbers (ticket ea4a6151300f, watchme): the trigger floor, the
# non-vacuity floors of the clear, and the give-up arm. Hand-set from the ticket, a
# learns-its-gates IOU like every constant in this folder.
_TRIGGER_FLOOR = 20
_ENOUGH_NAMED = 10
_ENOUGH_TROUBLED = 1
_GIVE_UP_AT = 100


def judge_tickets(tickets: list[dict]) -> dict:
    """The pure judgement, separable from the read so the proof can feed it fixtures.

    Offenders carry the ticket id and its lacks verbatim — the complete first report."""
    from cairn.devices.inference_domain.domain import ticket_lacks
    incomplete = []
    named = 0
    troubled = 0
    refused = 0
    for t in tickets:
        if t.get("unreadable"):
            incomplete.append({"id": t.get("id"), "lacks": [t["unreadable"]]})
            continue
        lacks = ticket_lacks(t)
        if lacks:
            incomplete.append({"id": t.get("id"), "lacks": lacks})
        caller = (t.get("caller") or {}).get("identity")
        if caller and caller != "unknown":
            named += 1
        if (t.get("outcome") or {}).get("kind") == "refused":
            refused += 1
            if t.get("trouble"):
                troubled += 1
    return {"tickets": len(tickets), "incomplete": incomplete, "named": named,
            "refused": refused, "troubled": troubled}


def survey_the_tickets() -> dict:
    """The live read — the device's own tickets folder, through its own reader."""
    from cairn.devices.inference_domain.domain import read_task_tickets
    return judge_tickets(read_task_tickets())


def _corpus(context: dict) -> dict:
    return once(context, "corpus", survey_the_tickets)


def _trigger(now, context: dict) -> bool:
    """TRUE on the first incomplete ticket once the population has passed the floor."""
    s = _corpus(context)
    return s["tickets"] >= _TRIGGER_FLOOR and bool(s["incomplete"])


def _enough(context: dict) -> bool:
    s = _corpus(context)
    if s["incomplete"]:
        return False
    if s["named"] >= _ENOUGH_NAMED and s["troubled"] >= _ENOUGH_TROUBLED:
        return True
    return s["tickets"] >= _GIVE_UP_AT and s["troubled"] == 0


def _carry(context: dict) -> dict:
    s = _corpus(context)
    n = s["tickets"] or 1
    return {"finding": "an inference task ticket is incomplete live — a field the proof "
                       "pins on a stub is missing on a real call, or a refusal raised no trouble",
            "field_population_rate": {"caller_named": round(s["named"] / n, 3),
                                      "complete": round((n - len(s["incomplete"])) / n, 3)},
            "trouble_integrations": s["troubled"],
            "counts": {"tickets": s["tickets"], "named": s["named"],
                       "refused": s["refused"], "troubled": s["troubled"],
                       "incomplete": len(s["incomplete"])},
            "cleared_by": ("named-and-troubled"
                           if s["named"] >= _ENOUGH_NAMED and s["troubled"] >= _ENOUGH_TROUBLED
                           else "gave-up-at-100-with-no-trouble"
                           if s["tickets"] >= _GIVE_UP_AT and s["troubled"] == 0 else None),
            "incomplete": s["incomplete"][:50],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "DONE when every inference call produces a complete task "
                                 "ticket with caller, request, response, model/provider "
                                 "selection and outcome, and failures raise trouble tickets",
            "suggests": "read domain.resolve()'s _close and the refusal branch: an incomplete "
                        "ticket names its lacks; a refused ticket without a trouble means "
                        "raise_trouble raised or the sink handed in has no raise_trouble"}


_HORIZON = 1000

PROBE = Probe(
    why="every inference call now writes a task ticket — one incomplete ticket live, or one "
        "refusal that raised no trouble, is the build failing where the stub could not show "
        "it; ten named callers beside one real trouble is it proven real",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_tickets()
    print(json.dumps({"corpus": s,
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2, default=str))
