"""WATCHME probe: unattributed-definitional-claims.

Fires when the claim_provenance sieve is registered but has not yet caught
a real unattributed claim BEFORE Akien reads it. Clears when the sieve
catches one before Akien reads it (the loop closing), or when it MISSES one
(the equally informative outcome that retires or reshapes the sieve).

Ticket: a-claim-carries-its-provenance.
"""
from __future__ import annotations

from pathlib import Path

from cairn.tools.base.probe import Probe

_SIEVE = "claim_provenance"
_CAUGHT_MARKER = (Path.home() / ".cairn" / "devices" / "build_inspector"
                  / "0" / "claim_provenance_caught.json")
_MISSED_MARKER = (Path.home() / ".cairn" / "devices" / "build_inspector"
                  / "0" / "claim_provenance_missed.json")


def _trigger(now, context: dict) -> bool:
    from cairn.machines.build_inspector.inspector import SIEVES
    registered = _SIEVE in SIEVES
    caught = _CAUGHT_MARKER.is_file()
    missed = _MISSED_MARKER.is_file()
    context["registered"] = registered
    context["caught"] = caught
    context["missed"] = missed
    return registered and not caught and not missed


def _carry(context: dict) -> dict:
    return {
        "registered": context.get("registered", False),
        "caught": context.get("caught", False),
        "missed": context.get("missed", False),
        "finding": ("claim_provenance sieve registered but no catch or miss yet"
                    if not context.get("caught") and not context.get("missed")
                    else "loop closed"),
    }


def _enough(context: dict) -> bool:
    return _CAUGHT_MARKER.is_file() or _MISSED_MARKER.is_file()


PROBE = Probe(
    why="the claim_provenance sieve may pass every charter and never once "
        "catch an unattributed claim before Akien reads it — a check that "
        "has never contributed. This probe fires while the sieve is live "
        "with no catch or miss, so the question 'is this check vacuous?' "
        "gets asked.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=500,
)
