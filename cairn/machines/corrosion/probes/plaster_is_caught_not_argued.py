"""WATCHME probe: plaster-is-caught-not-argued.

Fires when the corrosion sieve has been live for 30+ commits touching
constraint-bearing artifacts and has never once fired. Clears when it has
fired at least once on a real weakening AND at least one firing was
dispositioned as a genuine catch.

Ticket: a-constraint-that-stopped-constraining-carries-a-ruling.
"""
from __future__ import annotations

from pathlib import Path

from cairn.tools.base import address
from cairn.tools.base.probe import Probe

_ACTED_MARKER = address.instance_path("corrosion", 0) / "genuine_catch.json"


def _trigger(now, context: dict) -> bool:
    context["acted"] = _ACTED_MARKER.is_file()
    return not _ACTED_MARKER.is_file()


def _carry(context: dict) -> dict:
    return {
        "acted": context.get("acted", False),
        "finding": "corrosion sieve live but no genuine catch dispositioned yet"
        if not context.get("acted", False)
        else "at least one genuine catch dispositioned",
    }


def _enough(context: dict) -> bool:
    return _ACTED_MARKER.is_file()


PROBE = Probe(
    why="the corrosion sieve (constraint_enforcement_holds) may pass every "
        "crossing and never once fire — a check that has never redded. This "
        "probe fires when the sieve has been live with no genuine catch, so "
        "the question 'is this check vacuous?' gets asked.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)
