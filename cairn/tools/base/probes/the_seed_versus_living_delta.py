"""PROBE — the seed versus living delta.

Berth for the WATCHME that ticket a-gate-is-a-class (13758831632c) carries.
Watches whether gate construction produces a delta between the git-JSON seed
and the instance-space living tree — the founding question of whether sieve
dials actually move through evidence.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge
that re-opens a node whose intention did not work is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.address import tool_path
from cairn.tools.base.probe import Probe, by_copy, owning_ticket
from cairn.tools.base.transitions import BUILD_GATE

_SEEDS_DIR = Path(__file__).resolve().parents[3] / "machines" / "build_inspector" / "sieves"
_INSTANCE_TREE = tool_path("builder", 0, "gate") / "build_gate"

_OWNING_TICKET = "a-gate-is-a-class"


def _compute_delta() -> dict:
    deltas = {}
    if not _INSTANCE_TREE.is_dir():
        return {"status": "SEEDED", "deltas": {}}
    for seed_file in sorted(_SEEDS_DIR.glob("*.json")):
        living = _INSTANCE_TREE / seed_file.name
        if not living.exists():
            deltas[seed_file.stem] = {"status": "missing_from_tree"}
            continue
        try:
            seed_data = json.loads(seed_file.read_text())
            live_data = json.loads(living.read_text())
        except (json.JSONDecodeError, OSError):
            deltas[seed_file.stem] = {"status": "unreadable"}
            continue
        if seed_data != live_data:
            diff = {}
            all_keys = set(seed_data) | set(live_data)
            for k in sorted(all_keys):
                if seed_data.get(k) != live_data.get(k):
                    diff[k] = {"seed": seed_data.get(k), "living": live_data.get(k)}
            deltas[seed_file.stem] = {"status": "diverged", "fields": diff}
    return {"status": "NONE" if not deltas else "DELTA", "deltas": deltas}


def _trigger(now, context: dict) -> bool:
    d = context.get("delta") or _compute_delta()
    return d["status"] == "DELTA"


def _enough(context: dict) -> bool:
    d = context.get("delta") or _compute_delta()
    if d["status"] == "DELTA":
        return any(
            v.get("status") == "diverged"
            for v in d["deltas"].values()
        )
    return False


def _carry(context: dict) -> dict:
    d = context.get("delta") or _compute_delta()
    return {
        "finding": "seed-versus-living delta detected",
        "delta": d,
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="does the gate's living tree ever diverge from its seed through evidence? "
        "a delta answers the founding question of whether sieve dials actually move",
    trigger=_trigger,
    to=BUILD_GATE.notifies,
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=500,
)
