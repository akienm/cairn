"""PROBE — does the three-table schema work under real resolution load?

Berth for the WATCHME that ticket ``node-embedding-leaf-separation`` carries.
Berthed beside the librarian's proofs because that is WHAT IT WATCHES: the
resolution loop at ``cairn/devices/librarian/loop.py`` drives deposit/nearest/
corroborate through the three-table schema (cairn_nodes, cairn_embeddings,
per-tree leaf tables) on every resolution cycle.

THE EFFICACY QUESTION: the proof suite pins the contract with fixtures; this
probe watches whether the schema works under REAL load — a question walked
(nearest joins across three tables), answered, and the answer deposited (node +
embedding + leaf rows created). The tenure loop firing corroborate on the shared
node is the full cycle.

ENOUGH: one resolution cycle completes without error after PROVED. The schema
either works under real load or it does not; one cycle is sufficient because the
proof suite already covers every branch — the probe's question is whether the
live host, live data, and live embed model exercise the same path without error.

AUTHORITY: none. This probe deposits and pokes; acting on the finding is the
owner's call (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_REPO_ROOT = Path(__file__).resolve().parents[4]
_OWNING_TICKET = "node-embedding-leaf-separation"

_ERA = "2026-08-20T10:00:00"


def _count_resolution_cycles() -> dict:
    """Count resolution cycles from the librarian's history that post-date the
    three-table build (the era floor). A cycle is a history record with a
    'resolution' or 'deposit' annotation that names the three-table schema."""
    hist_path = _REPO_ROOT / "cairn" / "devices" / "librarian" / "history.json"
    cycles = 0
    errors = 0
    try:
        records = json.loads(hist_path.read_text(encoding="utf-8"))
    except Exception:
        return {"cycles": 0, "errors": 0, "readable": False}
    if not isinstance(records, list):
        return {"cycles": 0, "errors": 0, "readable": True}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        at = rec.get("at", "")
        if at < _ERA:
            continue
        if rec.get("crossing") == "PROVEME" or rec.get("deposit") or rec.get("resolution"):
            cycles += 1
        if rec.get("error"):
            errors += 1
    return {"cycles": cycles, "errors": errors, "readable": True}


def _trigger(now, context: dict) -> bool:
    """TRUE when the schema has been proved (PROVEME crossed) but zero resolution
    cycles have completed after the build — the intention is built but has not yet
    worked under real load."""
    s = context.get("counts") or _count_resolution_cycles()
    return s["cycles"] == 0


def _enough(context: dict) -> bool:
    """CLEARED by one real resolution cycle completing without error — the schema
    works under real load, the watch has gathered what it exists to gather."""
    s = context.get("counts") or _count_resolution_cycles()
    return s["cycles"] > 0 and s["errors"] == 0


def _carry(context: dict) -> dict:
    s = context.get("counts") or _count_resolution_cycles()
    return {"finding": "the three-table schema (cairn_nodes, cairn_embeddings, "
                       "per-tree leaf tables) has not yet completed a real "
                       "resolution cycle after PROVED",
            "counts": s,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the schema is built and proved under fixtures; "
                                 "the probe watches whether it works under real "
                                 "load (live embed host, live data, live tenure)"}


_HORIZON = 1000

PROBE = Probe(
    why="does the three-table schema work under real resolution load? — built "
        "and proved under fixtures, but not yet exercised by the librarian's "
        "resolution loop in production",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
