"""codemonkey/project.py — per-project data structure and isolation.

Each project gets its own learned state at:
  ~/.cairn/devices/codemonkey/0/projects/<project>/
    types/        — the pattern library (positive + negative types as JSON)
    constraints/  — compiled constraints lab surface
    mining/       — mining output and intermediate state

Projects are isolated — writing to project 'cairn' does not affect 'abc'.
The structure is created on first use by the device, not by hand.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from cairn.tools.base.address import instance_path
from cairn.devices.codemonkey.types import PatternType

_INSTANCE_ROOT = instance_path("codemonkey", 0)
_PROJECTS_ROOT = _INSTANCE_ROOT / "projects"

_SUBDIRS = ("types", "constraints", "mining")


def project_root(project: str) -> Path:
    """The root directory for a project's learned state."""
    return _PROJECTS_ROOT / project


def ensure_project(project: str) -> Path:
    """Create the project directory structure on first use. Returns the root."""
    root = project_root(project)
    for sub in _SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def list_projects() -> list[str]:
    """List all projects with learned state."""
    if not _PROJECTS_ROOT.is_dir():
        return []
    return sorted(
        d.name for d in _PROJECTS_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


def save_type(project: str, pattern: PatternType) -> Path:
    """Save a typed pattern to the project's type library."""
    root = ensure_project(project)
    types_dir = root / "types"
    safe_name = pattern.name.replace("/", "_").replace(" ", "_").lower()
    path = types_dir / f"{safe_name}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(pattern.to_dict(), indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    return path


def load_types(project: str) -> list[PatternType]:
    """Load all typed patterns from the project's type library."""
    root = project_root(project)
    types_dir = root / "types"
    if not types_dir.is_dir():
        return []
    patterns = []
    for p in sorted(types_dir.glob("*.json")):
        try:
            d = json.loads(p.read_text())
            patterns.append(PatternType.from_dict(d))
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return patterns


def save_constraint(project: str, name: str, data: dict[str, Any]) -> Path:
    """Save a compiled constraint to the project's constraints lab."""
    root = ensure_project(project)
    constraints_dir = root / "constraints"
    safe_name = name.replace("/", "_").replace(" ", "_").lower()
    path = constraints_dir / f"{safe_name}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    return path


def load_constraints(project: str) -> list[dict[str, Any]]:
    """Load all compiled constraints from the project's constraints lab."""
    root = project_root(project)
    constraints_dir = root / "constraints"
    if not constraints_dir.is_dir():
        return []
    constraints = []
    for p in sorted(constraints_dir.glob("*.json")):
        try:
            constraints.append(json.loads(p.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return constraints
