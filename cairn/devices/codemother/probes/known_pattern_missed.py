"""PROBE — did CodeMother miss a known pattern violation before code was written?

Watches for CC-- corrections on pattern types the device's library already
contains. A correction on a KNOWN type means the device had the type and
failed to surface it at challenge time. A correction on an UNKNOWN type is
the learning signal, not a failure.
"""

from __future__ import annotations

from cairn.tools.base.probe import Probe


def _trigger(now, context: dict) -> bool:
    return context.get("known_type_missed", False)


def _carry(context: dict) -> dict:
    return {
        "missed_type": context.get("missed_type", ""),
        "correction_source": context.get("correction_source", ""),
    }


def _enough(context: dict) -> bool:
    missed = context.get("known_type_missed_count", 0)
    caught = context.get("known_type_caught_count", 0)
    total = missed + caught
    return total >= 10 and missed / total < 0.1


PROBE = Probe(
    why="a correction on a pattern type the library already holds means challenge "
        "failed to surface it — the device had the answer and did not give it. "
        "Enough when the miss rate drops below 10% over 10+ events.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy", "object": "known-pattern-violation-caught-before-code"},
    carry=_carry,
    enough=_enough,
    horizon=200,
)
