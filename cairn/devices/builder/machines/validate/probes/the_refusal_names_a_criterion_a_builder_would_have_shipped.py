"""PROBE — the_refusal_names_a_criterion_a_builder_would_have_shipped

Berth for the WATCHME that ticket
``a-validate-criterion-is-runnable-before-the-crossing`` carries.
Berthed beside ``cairn/devices/builder/machines/validate`` because that
is WHAT IT WATCHES — whether the time-judge fires on real validate packets.

THE QUESTION: does the validate_criterion_is_runnable_before_the_crossing
judge catch post-crossing instruments in packets that builders actually
write? The proof shows the judge CAN bite a fixture; this probe watches
whether it bites what people actually write.

A VACUOUS RUN IS A RED. Zero packets checked means the probe has stopped
seeing its subject.
"""

from __future__ import annotations

import glob
import json
import os

from cairn.tools.base.probe import Probe, owning_ticket
from cairn.tools.base.address import instance_path
from cairn.tools.chain.grammar import ticket_path

_OWNING_TICKET = "a-validate-criterion-is-runnable-before-the-crossing"
_PACKETS = str(instance_path("chart") / "packets")
_JUDGE_NAME = "validate_criterion_is_runnable_before_the_crossing"
_ENOUGH_PACKETS = 30
_SAMPLE_SIZE = 50


def survey() -> dict:
    """Check the last N validate berths for time-judge firings."""
    from cairn.machines.build_inspector.inspector import judge_validate

    berth_files = sorted(glob.glob(f"{_PACKETS}/validate-*.json"))
    sample = berth_files[-_SAMPLE_SIZE:]

    examined = 0
    real_examined = 0
    time_judge_firings = 0
    real_refusals = 0
    fixture_refusals = 0
    refusal_details = []

    for bf in sample:
        try:
            with open(bf, encoding="utf-8") as fh:
                pkt = json.load(fh)
        except (OSError, ValueError):
            continue

        examined += 1
        claim = pkt.get("ticket", "")
        is_real = bool(isinstance(claim, str) and claim
                       and ticket_path(claim) is not None)
        if is_real:
            real_examined += 1

        attendance = judge_validate(pkt)
        for rec in attendance:
            if not isinstance(rec, dict):
                continue
            if rec.get("judge") != _JUDGE_NAME:
                continue
            findings = rec.get("findings", [])
            if not findings:
                continue
            time_judge_firings += 1
            if is_real:
                real_refusals += 1
            else:
                fixture_refusals += 1
            for f in findings[:3]:
                refusal_details.append({
                    "berth": os.path.basename(bf),
                    "is_real": is_real,
                    "ticket": claim,
                    "finding": f.get("finding", "")[:200] if isinstance(f, dict) else str(f)[:200],
                })

    return {
        "packets_examined": examined,
        "real_packets": real_examined,
        "time_judge_firings": time_judge_firings,
        "real_refusals": real_refusals,
        "fixture_refusals": fixture_refusals,
        "refusal_details": refusal_details[:10],
    }


def _trigger(now, context: dict) -> bool:
    s = context.get("survey") or survey()
    if s["packets_examined"] == 0:
        return True
    if s["time_judge_firings"] > 0:
        return True
    return False


def _enough(context: dict) -> bool:
    s = context.get("survey") or survey()
    if s["packets_examined"] < _ENOUGH_PACKETS:
        return False
    if s["real_refusals"] < 1:
        return False
    return True


def _carry(context: dict) -> dict:
    s = context.get("survey") or survey()
    if s["packets_examined"] == 0:
        finding = "VACUITY — zero validate packets examined"
    elif s["real_refusals"] > 0:
        finding = (
            f"TIME-JUDGE BITING LIVE — {s['real_refusals']} real refusal(s) "
            f"across {s['real_packets']} real packets, "
            f"{s['fixture_refusals']} fixture refusal(s) across "
            f"{s['packets_examined'] - s['real_packets']} fixture packets"
        )
    elif s["time_judge_firings"] > 0:
        finding = (
            f"TIME-JUDGE FIRING ON FIXTURES ONLY — {s['fixture_refusals']} "
            f"fixture refusal(s), zero real refusals across "
            f"{s['real_packets']} real packets"
        )
    else:
        finding = (
            f"HOLDING — {s['packets_examined']} packets examined, zero "
            f"time-judge firings (the judge has not needed to bite)"
        )
    return {
        "finding": finding,
        "survey": s,
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="the validate door's time-judge catches criteria that read "
        "post-crossing state — this probe watches whether it bites "
        "what builders actually write, not just fixtures",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "validate", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "the_refusal_names_a_criterion_a_builder_would_have_shipped"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)


if __name__ == "__main__":
    s = survey()
    print(json.dumps({
        "survey": s,
        "would_trigger": _trigger(None, {"survey": s}),
        "enough": _enough({"survey": s}),
        "carry": _carry({"survey": s}),
    }, indent=2, default=str))
