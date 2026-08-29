"""PROBE — are crossing fingerprints actually verified in practice?

Berth for the WATCHME that ticket ``crossing-fingerprints-are-verified`` carries.
Berthed here, beside ``cairn/tools/base``, because that is WHAT IT WATCHES; the
ticket it was compiled from lives in CairnCommons.

THE EFFICACY QUESTION: fingerprints are computed on every crossing and a verifier
exists, but does anything actually call the verifier? A fingerprint nobody checks
is a hash nobody has (the ticket's own falsifier). This probe watches the live
traffic: after enough crossings carry fingerprints, has at least one verification
run against them?

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge
that re-opens a node whose intention did not work is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket
from cairn.tools.base.transitions import verify_crossing_fingerprint
from cairn.tools.charter import projector

_REPO_ROOT = Path(__file__).resolve().parents[4]

_OWNING_TICKET = "crossing-fingerprints-are-verified"
_ENOUGH_CROSSINGS = 50
_ENOUGH_VERIFIED = 200


def _count_fingerprinted_crossings() -> dict:
    fingerprinted = 0
    verified = 0
    failed = 0
    total = 0
    for h in sorted(_REPO_ROOT.rglob("history.json")):
        if "__pycache__" in str(h) or ".cairn" in str(h):
            continue
        try:
            entries = projector.read_history(str(h))
        except Exception:
            continue
        for entry in entries:
            total += 1
            if "fingerprint" in entry:
                fingerprinted += 1
                if verify_crossing_fingerprint(entry):
                    verified += 1
                else:
                    failed += 1
    return {"total": total, "fingerprinted": fingerprinted,
            "verified": verified, "failed": failed}


def _trigger(now, context: dict) -> bool:
    c = context.get("counts") or _count_fingerprinted_crossings()
    return c["fingerprinted"] >= _ENOUGH_CROSSINGS and c["failed"] > 0


def _enough(context: dict) -> bool:
    c = context.get("counts") or _count_fingerprinted_crossings()
    return (c["fingerprinted"] >= _ENOUGH_VERIFIED and c["failed"] == 0) or c["verified"] > 0


def _carry(context: dict) -> dict:
    c = context.get("counts") or _count_fingerprinted_crossings()
    return {"finding": "crossing fingerprint verification failure detected",
            "counts": c,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "a fingerprint that fails verification means either "
                                 "tampering or a bug in the fingerprint computation"}


PROBE = Probe(
    why="are crossing fingerprints actually verified in practice? — a fingerprint "
        "nobody checks is a hash nobody has, which is the ticket's own falsifier",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)
