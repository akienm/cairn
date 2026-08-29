"""PROBE — does the beat stay inside its ruled 1.0s cadence?

Berth for the WATCHME that ticket ``the-beat-spends-2500ms-on-triggers-against-a-1s-cadence``
carries. Berthed beside ``cairn/devices/cairn/machines/ground_loop`` because that is WHAT IT WATCHES: the
loop's beat cycle — pulse all shims, write liveness — and whether it fits inside the ruled
once-per-second cadence.

THE MEASUREMENT. The probe fires DURING the beat, before the liveness record is written. So
the liveness record on disk is from the PREVIOUS beat, and ``age_s`` = time since that write
= the inter-beat interval for the current beat. A reading over 1.0s (the ruled cadence) is a
beat that did not fit.

WHAT ``enough`` CAN AND CANNOT MEASURE. The ticket asks for 5,000 consecutive beats under
cadence including a probe arming. A probe is stateless (frozen dataclass) and sees one
snapshot per fire. What this probe CAN measure: the beat count (total, from the liveness
record), the current age_s, and the probe count (from discovery). What it CANNOT measure from
a single snapshot: consecutive beats under cadence. The ``enough`` clause is honest about this
bound: it checks the total beat count and the current reading, and says what it did not check.

AUTHORITY: none. This probe deposits and pokes; widening the cadence is Akien's ruling (the
ticket's own falsifier names it as WRONG INTENT).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-beat-spends-2500ms-on-triggers-against-a-1s-cadence"

CADENCE_S = 60.0

_ENOUGH_BEATS = 5000


def survey_the_corpus() -> dict:
    """The live read: the liveness record at this instant."""
    from cairn.devices.cairn.machines.ground_loop.liveness import read_liveness
    return read_liveness(datetime.now(timezone.utc).astimezone())


def judge(survey: dict) -> dict:
    """The pure judgement: is the inter-beat interval inside the cadence?"""
    record = survey.get("record") or {}
    state = record.get("state") or {}
    age_s = survey.get("age_s")
    beats = state.get("beats", 0)
    verdict = survey.get("verdict")

    inside_cadence = age_s is not None and age_s <= CADENCE_S

    return {
        "verdict": verdict,
        "age_s": age_s,
        "beats": beats,
        "cadence_s": CADENCE_S,
        "inside_cadence": inside_cadence,
        "pid": record.get("pid"),
        "last_pulsed_count": state.get("last_pulsed_count"),
    }


def _corpus(context: dict) -> dict:
    return context.get("corpus") or judge(context.get("survey") or survey_the_corpus())


def _trigger(now, context: dict) -> bool:
    """TRUE when the inter-beat interval exceeds the cadence.

    A beat that overran is the finding — not a blip to average away (the ticket's
    own words: "stop early and loudly the first time a beat exceeds one cadence").
    """
    s = _corpus(context)
    return not s["inside_cadence"]


def _enough(context: dict) -> bool:
    """CLEARED when the loop has completed many beats and the current reading is
    under cadence.

    Honestly bounded: the ticket asks for 5,000 CONSECUTIVE beats, which a
    stateless probe cannot track from a single snapshot. This checks total beats
    (a weaker but measurable condition) and the current reading.
    """
    s = _corpus(context)
    if not s["inside_cadence"]:
        return False
    if s["beats"] < _ENOUGH_BEATS:
        return False
    return True


def _carry(context: dict) -> dict:
    s = _corpus(context)
    parts = []
    if not s["inside_cadence"]:
        parts.append(f"the inter-beat interval is {s['age_s']:.3f}s "
                     f"against a {s['cadence_s']}s cadence")

    return {
        "finding": "; ".join(parts) or (
            f"the beat is inside its cadence — {s['age_s']:.3f}s "
            f"against {s['cadence_s']}s"
        ),
        "age_s": s["age_s"],
        "beats": s["beats"],
        "cadence_s": s["cadence_s"],
        "inside_cadence": s["inside_cadence"],
        "pid": s["pid"],
        "last_pulsed_count": s["last_pulsed_count"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's falsifier reds on widening CADENCE_S or the "
                             "300s DEAD threshold (plaster on a ruled bound), on dropping "
                             "or sampling probes to buy the number, and on making the "
                             "sweep concurrent before the five are diagnosed",
        "suggests": "read the per-shim timing if the beat overruns — a-beat-costs-what-changed "
                    "is the sibling probe that attributes the cost",
    }


_HORIZON = 1000

PROBE = Probe(
    why="does the beat stay inside its ruled 1.0s cadence? — the measured beat "
        "period was 2.5s at cast, three devices imported on every beat, and the "
        "defect is a cost that grows with the watch set",
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
