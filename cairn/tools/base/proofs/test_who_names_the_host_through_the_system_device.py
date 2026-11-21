#!/usr/bin/env python3
"""Proof for ticket 5ccc7f05c932, clauses 1-2: claude_identity.who() names the host on a box
with no os.uname, and asks the system device only through the tool that device publishes.

Measured 2026-11-20: saveslate crashed on akiendell (Windows) at claude_identity.py:108,
'"host": os.uname().nodename', because os.uname does not exist there. Saveslate auto-commit
4794006a7 moved the call to cairn.devices.system_rackmount.rackmount.host_name, which is the
right home but an unpublished path: encapsulation_breaches read claude_identity.py line 105 into
system_rackmount on 2026-11-21 (RULE 1). Akien, 2026-11-21: "hostname should come from the
system device."

  (1) with os.uname deleted, who() over a scratch sessions dir names a host that is non-empty,
      short and lowercased, equal to the published tool's host_name();
  (2) encapsulation_breaches lists no row from claude_identity.py, and claude_identity imports
      the published host module and no other cairn.devices module.

The subject is imported inside each tooth, so a hollow build reds per tooth. The live
~/.claude/sessions is never read.

    bin/cairn test cairn/tools/base/proofs/test_who_names_the_host_through_the_system_device.py
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"5ccc7f05c932": {
    "1": "test_who_names_the_host_with_os_uname_absent",
    "2": "test_claude_identity_reaches_the_system_device_only_through_its_published_tool",
}}

_SUBJECT = REPO / "cairn" / "tools" / "base" / "claude_identity.py"
_REL = "cairn/tools/base/claude_identity.py"
_PUBLISHED = "cairn.devices.system_rackmount.tools.host.host"


def test_who_names_the_host_with_os_uname_absent() -> None:
    from cairn.tools.base.claude_identity import who
    from cairn.devices.system_rackmount.tools.host.host import host_name
    saved = getattr(os, "uname", None)
    if saved is not None:
        delattr(os, "uname")
    try:
        w = who("sid-none", sessions_dir=scratch_dir("who-host-"), environ={})
        expected = host_name()
    finally:
        if saved is not None:
            os.uname = saved
    h = w.get("host")
    assert isinstance(h, str) and h and "." not in h and h == h.lower(), w
    assert h == expected, (h, expected)


def test_claude_identity_reaches_the_system_device_only_through_its_published_tool() -> None:
    from cairn.devices.codemother.machines.build_inspector import inspector
    rows = [r for r in inspector.encapsulation_breaches(str(REPO)) if r["file"] == _REL]
    devices = set()
    for node in ast.walk(ast.parse(_SUBJECT.read_text())):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        devices |= {n for n in names if n.startswith("cairn.devices.")}
    assert not rows, f"claude_identity breaches RULE 1: {rows}"
    assert devices == {_PUBLISHED}, f"claude_identity imports {sorted(devices)}, not exactly {_PUBLISHED}"


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
