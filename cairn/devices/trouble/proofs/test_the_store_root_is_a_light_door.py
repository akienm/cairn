#!/usr/bin/env python3
"""Proof that the trouble store's root is answered by a door that imports nothing heavy.

Measured 2026-10-13: 4ddc9df3369e's build (3024a302) had cairn/tools/base/transitions.py ask
``cairn.devices.trouble.trouble.store_root`` for the store's path. trouble.py reaches
trouble/shim.py (the fold before a read), which imports base/shim.py, which reaches
bus_client/remote.py and its socket — so the inspector's verdict path could reach a host,
and test_inspector_nexus.py's fire-path tooth went red. The root is one line of address
arithmetic; it moves to trouble/store.py, which imports only the address door, and every
caller outside the component asks there, through the charter's declared public interface.

Teeth, one per falsifier clause (PROVES below), each binding store.py at call time so the
hollow reading (no store.py) reds the tooth instead of crashing the reader:
  (1) store.py imports nothing beyond the standard library and cairn.tools.base.address,
      at any depth in the file, so the fire path cannot grow back through it;
  (2) store_root() is log_path('cairn', 0)/'troubletickets', and with injected roots it
      follows them;
  (3) trouble.py's store_root IS store.py's (one root, re-exported, never spelled twice);
  (4) the trouble charter's public_interface names cairn.devices.trouble.store.
Hollow: before the build, store.py is absent and 1-4 red.

    bin/cairn test cairn/devices/trouble/proofs/test_the_store_root_is_a_light_door.py
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_COMP = _REPO / "cairn" / "devices" / "trouble"
_STORE = _COMP / "store.py"
_ALLOWED = {"cairn.tools.base.address"}

PROVES = {"03ea6f93df03": {
    "1": "test_the_store_imports_only_the_address_door",
    "2": "test_the_root_is_the_log_path",
    "3": "test_the_device_reexports_the_one_root",
    "4": "test_the_charter_declares_the_door",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_store_imports_only_the_address_door() -> None:
    tree = ast.parse(_STORE.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add("." * node.level + (node.module or ""))
    stray = sorted(n for n in names
                   if n not in _ALLOWED and n != "__future__"
                   and n.split(".")[0] not in sys.stdlib_module_names)
    check("test_the_store_imports_only_the_address_door", not stray and bool(names), f"stray {stray}")


def test_the_root_is_the_log_path() -> None:
    from cairn.devices.trouble.store import store_root
    from cairn.tools.base.address import log_path
    live = store_root() == log_path("cairn", 0) / "troubletickets"
    roots = {"instance": Path("/nonexistent-trouble-store/.cairn")}
    try:
        injected = store_root(roots) == log_path("cairn", 0, roots) / "troubletickets"
    except Exception as exc:  # noqa: BLE001 — a roots shape the address door refuses
        injected, roots = False, f"{type(exc).__name__}: {exc}"
    check("test_the_root_is_the_log_path", live and injected, f"roots={roots}")


def test_the_device_reexports_the_one_root() -> None:
    from cairn.devices.trouble import store, trouble
    check("test_the_device_reexports_the_one_root", trouble.store_root is store.store_root)


def test_the_charter_declares_the_door() -> None:
    charter = json.loads((_COMP / "intention+why.json").read_text(encoding="utf-8"))
    pi = charter.get("public_interface") or []
    check("test_the_charter_declares_the_door", "cairn.devices.trouble.store" in pi, repr(pi))


def main() -> int:
    for tooth in (test_the_store_imports_only_the_address_door, test_the_root_is_the_log_path,
                  test_the_device_reexports_the_one_root, test_the_charter_declares_the_door):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
