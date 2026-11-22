#!/usr/bin/env python3
"""Proof for ticket 5ccc7f05c932, clause 3: the host tool the system device publishes names the
box on any OS, measured at its own address.

Measured 2026-11-20: saveslate crashed on akiendell (Windows) because os.uname does not exist
there. Akien, 2026-11-21: "hostname should come from the system device." So the system device
publishes cairn.devices.system_rackmount.tools.host.host, and this proof measures that tool
alone: with os.uname deleted, host_name() is the short lowercased name; os_id() names an OS
family; the module imports no socket; and its charter publishes exactly its one module, which
is what lets the encapsulation sieve admit a reach into the device through it (RULE 1).

The tool is imported inside the tooth, so an absent or hollow build reds the tooth, not the run.

    bin/cairn test cairn/devices/system_rackmount/tools/host/proofs/test_the_host_tool_names_the_box.py
"""
from __future__ import annotations

import ast
import importlib
import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_TOOL_DIR = _REPO / "cairn" / "devices" / "system_rackmount" / "tools" / "host"
_MODULE = "cairn.devices.system_rackmount.tools.host.host"

PROVES = {"5ccc7f05c932": {
    "3": "test_the_published_tool_names_the_box_without_os_uname",
    "4": "test_rackmount_keeps_neither_host_function",
    "5": "test_the_system_device_charter_publishes_the_host_tool",
}}


def _without_uname(fn):
    """Call fn with os.uname absent, as on Windows; restore it whatever happens."""
    saved = getattr(os, "uname", None)
    if saved is not None:
        delattr(os, "uname")
    try:
        return fn()
    finally:
        if saved is not None:
            os.uname = saved


def test_the_published_tool_names_the_box_without_os_uname() -> None:
    lacks = []
    try:
        host = importlib.import_module(_MODULE)
        name = _without_uname(host.host_name)
        fam = _without_uname(host.os_id)
        if not (isinstance(name, str) and name and "." not in name and name == name.lower()):
            lacks.append(f"host_name() with os.uname absent read {name!r}, not a short lowercased name")
        if fam not in ("windows", "linux", "darwin"):
            lacks.append(f"os_id() read {fam!r}, not windows/linux/darwin")
    except Exception as exc:  # noqa: BLE001 — a missing tool is this tooth's red, not a crash
        lacks.append(f"the tool would not run: {type(exc).__name__}: {exc}")
    src = _TOOL_DIR / "host.py"
    if src.is_file():
        mods = set()
        for node in ast.walk(ast.parse(src.read_text())):
            if isinstance(node, ast.Import):
                mods |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        if "socket" in mods:
            lacks.append("host.py imports socket")
    else:
        lacks.append(f"{src} is absent")
    try:
        charter = json.loads((_TOOL_DIR / "intention+why.json").read_text())
        if charter.get("published_by_device") is not True:
            lacks.append(f"the charter's published_by_device reads {charter.get('published_by_device')!r}")
        if charter.get("public_interface") != [_MODULE]:
            lacks.append(f"the charter's public_interface reads {charter.get('public_interface')!r}")
    except (OSError, ValueError) as exc:
        lacks.append(f"the charter would not read: {type(exc).__name__}: {exc}")
    assert not lacks, "; ".join(lacks)



def test_rackmount_keeps_neither_host_function() -> None:
    """Clause 4 (D2): the os calls live in the published tool alone, so rackmount.py defines neither."""
    src = _REPO / "cairn" / "devices" / "system_rackmount" / "rackmount.py"
    defined = {n.name for n in ast.walk(ast.parse(src.read_text()))
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    kept = sorted(defined & {"host_name", "os_id"})
    assert not kept, f"rackmount.py still defines {kept}"


def test_the_system_device_charter_publishes_the_host_tool() -> None:
    """Clause 5 (D4): the holder's charter names the tool it publishes."""
    charter = json.loads((_REPO / "cairn" / "devices" / "system_rackmount" / "intention+why.json").read_text())
    pi = charter.get("public_interface") or []
    assert _MODULE in pi, f"the system_rackmount charter's public_interface reads {pi!r}"

def _main() -> int:
    failed = []
    for name in PROVES["5ccc7f05c932"].values():
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print("RED" if failed else "GREEN")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
