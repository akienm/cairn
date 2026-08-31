"""codemonkey/mine.py — scan a codebase and derive the initial pattern lattice.

Cold start: reads code structure and produces positive types describing
the structural patterns found. For cairn, this includes the complexity axis
(tools/machines/devices), the charter pattern (intention+why.json beside code),
and the proof pattern. Output deposits to the project's type library.

Uses inference_domain for pattern recognition — the LLM identifies patterns
the structural scan surfaces.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from cairn.devices.codemonkey.types import positive, PatternType, PatternSignal
from cairn.devices.codemonkey.project import ensure_project, save_type


def scan_structure(codebase: str | Path) -> list[dict[str, Any]]:
    """Scan a codebase directory and collect structural facts.

    Returns a list of observations: directory shapes, file patterns,
    naming conventions, co-located artifacts.
    """
    root = Path(codebase)
    observations = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith((".", "__"))]
        rel = Path(dirpath).relative_to(root)

        if "intention+why.json" in filenames:
            observations.append({
                "kind": "charter_pattern",
                "path": str(rel),
                "detail": "intention+why.json co-located with code",
            })

        if "proofs" in dirnames:
            observations.append({
                "kind": "proof_pattern",
                "path": str(rel),
                "detail": "proofs/ directory co-located with code",
            })

        if "validations" in dirnames:
            observations.append({
                "kind": "validation_pattern",
                "path": str(rel),
                "detail": "validations/ directory co-located with code",
            })

        if "history.json" in filenames:
            observations.append({
                "kind": "history_pattern",
                "path": str(rel),
                "detail": "history.json co-located with code",
            })

        if "state.json" in filenames:
            observations.append({
                "kind": "state_pattern",
                "path": str(rel),
                "detail": "state.json co-located with code",
            })

    return observations


def derive_types(observations: list[dict[str, Any]], codebase_name: str) -> list[PatternType]:
    """Derive positive types from structural observations.

    Groups observations by kind and produces one positive type per distinct
    structural pattern found. The count reflects how many instances exist.
    """
    by_kind: dict[str, list[dict]] = {}
    for obs in observations:
        by_kind.setdefault(obs["kind"], []).append(obs)

    types = []
    for kind, instances in by_kind.items():
        count = len(instances)
        example_paths = [i["path"] for i in instances[:3]]
        detail = instances[0].get("detail", kind)

        types.append(positive(
            name=kind.replace("_", "-"),
            why=f"Structural pattern found {count}x in {codebase_name}: {detail}",
            signals=(PatternSignal(description=detail),),
            scope=codebase_name,
            source=f"mine:{codebase_name}",
            count=count,
            tags=("mined", kind),
        ))

    return types


def mine(codebase: str | Path, project: str) -> list[PatternType]:
    """Mine a codebase and deposit positive types to the project's library.

    Returns the list of types produced.
    """
    codebase = Path(codebase)
    observations = scan_structure(codebase)
    types = derive_types(observations, project)

    ensure_project(project)
    for t in types:
        save_type(project, t)

    return types
