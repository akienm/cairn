"""instanceizer — the minimum bridge between class-space and instance-space.

A folder (a component that is not a device, machine, or tool) has code in class-space
and may need runtime state in instance-space. The instanceizer is a JSON declaration at
``~/.cairn/folders/<name>/instanceizer.json`` that says: use THIS tool class, configured
THIS way, operating on THIS data path.

The declaration answers three questions:
  - tool_class: dotted import path to the tool class (e.g. "cairn.tools.data_recorder.data_recorder.DataRecorder")
  - config: kwargs passed to the tool class constructor
  - data_path: where the tool's output lives (relative to the folder's instance-space root)

``load()`` reads the declaration, imports the class, instantiates it, and returns it.
``ensure()`` creates the declaration if it doesn't exist yet — the first-write provisioner.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


INSTANCEIZER_FILE = "instanceizer.json"


def load(folder_path: Path) -> Any:
    """Read the instanceizer declaration and return the instantiated tool."""
    decl_path = folder_path / INSTANCEIZER_FILE
    if not decl_path.exists():
        raise FileNotFoundError(
            f"no instanceizer at {decl_path} — the folder has no instance-space wiring")
    decl = json.loads(decl_path.read_text(encoding="utf-8"))
    tool_class = _import_class(decl["tool_class"])
    config = dict(decl.get("config", {}))
    if "data_path" in decl:
        data_dir = folder_path / decl["data_path"]
        config.setdefault("base_dir", str(data_dir))
    return tool_class(**config)


def ensure(folder_path: Path, *, tool_class: str, data_path: str = "data",
           config: dict | None = None) -> Path:
    """Write the instanceizer declaration if it doesn't exist. Returns the path."""
    folder_path.mkdir(parents=True, exist_ok=True)
    decl_path = folder_path / INSTANCEIZER_FILE
    if decl_path.exists():
        return decl_path
    decl = {
        "tool_class": tool_class,
        "data_path": data_path,
        "config": config or {},
    }
    decl_path.write_text(json.dumps(decl, indent=2) + "\n", encoding="utf-8")
    return decl_path


def _import_class(dotted: str) -> type:
    """Import 'module.path.ClassName' and return the class."""
    module_path, _, class_name = dotted.rpartition(".")
    if not module_path:
        raise ValueError(f"tool_class must be a dotted path, got {dotted!r}")
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)
