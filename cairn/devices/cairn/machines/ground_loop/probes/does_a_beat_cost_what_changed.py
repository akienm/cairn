"""PROBE — does a beat cost what CHANGED, or does it re-derive the whole corpus?

Berth for the WATCHME that ticket ``2f0a6ea8c966-a-beat-costs-what-changed`` carries, at the
path that ticket's ``watchme.probe`` names. Berthed beside
``cairn/devices/cairn/machines/ground_loop`` because that is WHAT IT WATCHES.

THE DATUM, and it is one subtraction of numbers the beat already has (the watchme spec's own
words: "No new clock, no scan"). The probe fires DURING the beat, before the liveness record
is written, so the record on disk is the PREVIOUS beat's and ``age_s`` is the inter-beat
interval. The runner does ``beat(); sleep(CADENCE_S)``, so

    beat_cost_s = age_s - CADENCE_S

is the beat's own work, with the sleep subtracted off. That is the number this ticket is
about: 104.8s measured 2026-09-07, 23.7s steady state after the four fixes.

WHY THE BOUND IS A FRACTION OF THE CADENCE AND NOT THE CADENCE ITSELF. A beat costing exactly
one cadence still "fits" in the trivial sense — the loop never sleeps and the period doubles.
The margin is the point of the ticket: the marginal cost of the NEXT watch armed has to be
affordable, and it is not affordable out of a budget already spent. ``_HEADROOM`` is the
fraction of the cadence a beat may spend before this probe says so.

WHAT THIS PROBE DOES NOT MEASURE, stated because a watch that hides its bound is worse than
none: it sees the beat's TOTAL cost, not its attribution. When it fires, the per-shim split
comes from ``state()["pulse_events"]`` and the profile is re-run by hand; the sibling watch
``the_beat_stays_inside_its_cadence`` reads the same record for the cadence question. The two
are deliberately separate — "did the beat fit" and "did the beat re-derive the settled" go
red for different reasons and route to different fixes.

AUTHORITY: none. This probe deposits and pokes. Widening CADENCE_S or ``_HEADROOM`` is
Akien's ruling, not CC's — the ticket's ``owner`` field says so in as many words, and the
2026-09-08 ruling (``the-60s-cadence-is-the-bound-a-beat-is-measured-against``) is what moved
the cadence to 60.0s.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from cairn.tools.base.probe import Probe, owning_ticket, once

_OWNING_TICKET = "a-beat-costs-what-changed"

CADENCE_S = 60.0

# The share of the cadence a beat may spend on its own work. At 60.0s that is 30.0s, and the
# measured steady state is 23.7s — so the watch stands with margin rather than resting on the
# number it was born against (Law 9: green is earned, and a bound set AT the measurement is a
# bound that can only ever go red).
_HEADROOM = 0.5

# Enough when the beat has stayed inside its budget across a long run. Same honest bound as
# the sibling probe: a stateless probe sees one snapshot, so this is total beats, not
# consecutive ones, and the docstring says which.
_ENOUGH_BEATS = 5000

# How stale the liveness record may be and still be read as an inter-beat interval. Three
# cadences: one beat overrunning by 2x is still a beat; a record older than that is a loop
# that stopped, which is a different watch's finding.
_MEASURABLE_CADENCES = 3.0


def survey_the_corpus() -> dict:
    """The live read: the liveness record at this instant."""
    from cairn.devices.cairn.machines.ground_loop.liveness import read_liveness
    return read_liveness(datetime.now(timezone.utc).astimezone())


def judge(survey: dict) -> dict:
    """The pure judgement: what did the beat itself cost, sleep subtracted off?"""
    record = survey.get("record") or {}
    state = record.get("state") or {}
    age_s = survey.get("age_s")
    beats = state.get("beats", 0)

    budget_s = CADENCE_S * _HEADROOM
    beat_cost_s = None if age_s is None else max(0.0, age_s - CADENCE_S)

    # THE READING IS ONLY A BEAT COST WHILE THE LOOP IS BEATING. Measured 2026-09-08 the first
    # time this probe was run by hand: the loop was down, age_s was 312,173s, and the naive
    # subtraction reported a "beat cost" of 3.6 days. A stopped loop is the LIVENESS watch's
    # finding, not this one's, and a probe that fires on someone else's defect is noise at the
    # one surface Law 7 says must stay loud. So the reading is measurable only while age_s is
    # inside a small number of cadences; outside that this probe has nothing to say and says
    # nothing, rather than saying something false.
    measurable = age_s is not None and age_s <= CADENCE_S * _MEASURABLE_CADENCES
    inside_budget = (not measurable) or beat_cost_s <= budget_s

    return {
        "verdict": survey.get("verdict"),
        "age_s": age_s,
        "beat_cost_s": beat_cost_s if measurable else None,
        "measurable": measurable,
        "budget_s": budget_s,
        "cadence_s": CADENCE_S,
        "headroom": _HEADROOM,
        "beats": beats,
        "inside_budget": inside_budget,
        "pid": record.get("pid"),
        "last_pulsed_count": state.get("last_pulsed_count"),
    }


def _corpus(context: dict) -> dict:
    return context.get("corpus") or judge(once(context, "survey", survey_the_corpus))


def _trigger(now, context: dict) -> bool:
    """TRUE when the beat's own work exceeds its share of the cadence.

    A beat that has crept back over budget is the finding. This is the silent kind of decay —
    nothing breaks, the box just gets slower — which is exactly why it needs a watch rather
    than a reader who remembers to look.
    """
    s = _corpus(context)
    return not s["inside_budget"]


def _enough(context: dict) -> bool:
    """CLEARED when the loop has run long and the current beat is inside its budget.

    Honestly bounded, and the bound is the ticket's own: it asks for the beat to survive a
    real corpus change AND a new probe being armed. A stateless probe cannot see either from
    one snapshot, so this checks the weaker measurable condition (many beats, currently inside
    budget) and says so rather than claiming the stronger one.
    """
    s = _corpus(context)
    if not s["measurable"] or not s["inside_budget"]:
        return False
    return s["beats"] >= _ENOUGH_BEATS


def _carry(context: dict) -> dict:
    s = _corpus(context)
    cost = s["beat_cost_s"]
    shown = "unknown" if cost is None else f"{cost:.1f}s"

    if not s["measurable"]:
        finding = (f"no beat cost to read — the liveness record is {s['age_s']}s old, past "
                   f"{_MEASURABLE_CADENCES:g} cadences, so the loop is not beating. That is "
                   f"the liveness watch's finding, not this one's")
    elif s["inside_budget"]:
        finding = (f"the beat costs {shown} of its {s['budget_s']:.1f}s budget "
                   f"({s['headroom']:.0%} of a {s['cadence_s']}s cadence)")
    else:
        finding = (f"the beat's own work is {shown} against a {s['budget_s']:.1f}s budget — "
                   f"a corpus answer is being re-derived that did not change")

    return {
        "finding": finding,
        "beat_cost_s": cost,
        "measurable": s["measurable"],
        "budget_s": s["budget_s"],
        "cadence_s": s["cadence_s"],
        "age_s": s["age_s"],
        "beats": s["beats"],
        "inside_budget": s["inside_budget"],
        "pid": s["pid"],
        "last_pulsed_count": s["last_pulsed_count"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's falsifier reds on WRONG INTENT — buying the number "
                             "by firing probes LESS OFTEN (a time-to-live, an every-Nth-beat "
                             "probe, a staggered schedule). The point is that the answers are "
                             "cheap when nothing changed, not that they are asked for less. It "
                             "also reds on widening CADENCE_S to make the number look better; "
                             "that bound is Akien's, ruled 2026-08-22 and recorded 2026-09-08.",
        "suggests": "read state()['pulse_events'] and re-run the per-shim timing — the cost is "
                    "attributed per probe, and the four fixes this ticket carries "
                    "(claiming_packets index, once(), settled(), the pulse context every shim "
                    "was swapping out) are each a place it can regress",
    }


_HORIZON = 1000

PROBE = Probe(
    why="does a beat cost what CHANGED, or the whole corpus? — the beat was 104.8s against a "
        "60s cadence because every probe re-derived its own survey on a clock; it is 23.7s "
        "now, and nothing but this watch would notice it creeping back",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "ground_loop", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_corpus()
    j = judge(s)
    print(json.dumps({"corpus": j,
                      "would_trigger": _trigger(None, {"corpus": j}),
                      "enough": _enough({"corpus": j})}, indent=2, default=str))
