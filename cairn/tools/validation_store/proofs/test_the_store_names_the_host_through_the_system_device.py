#!/usr/bin/env python3
"""Proof for ticket cffb99063d09: validation_store names this box through the system device's
published host tool, and asks the OS for no hostname itself.

Measured 2026-11-21: validation_store.py:165-171 carried its own host_name, platform.node()
under another name. Outline 6.6.3.7: "nothing else in Cairn asks the OS for the hostname";
callers reach it through the client tool the system device publishes.

  (1) an AST scan of validation_store.py finds no os.uname, platform.node, platform.uname or
      socket.gethostname call, and the store's host_name IS the host tool's;
  (2) with os.uname deleted, host_name() and host_facts()["hostname"] equal the tool's answer;
  (3) host_name stays a module attribute the store's own calls read: rebinding it moves the
      host-seam seal path, as the tester's fake-a-box seam relies on.

The subject is imported inside each tooth, so a hollow build reds per tooth.

    bin/cairn test cairn/tools/validation_store/proofs/test_the_store_names_the_host_through_the_system_device.py
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"cffb99063d09": {"1": "test_the_store_asks_the_os_no_hostname",
                           "2": "test_the_store_names_the_box_with_os_uname_gone",
                           "3": "test_a_rebound_host_name_moves_the_host_seam_seal"}}

STORE = _REPO_ROOT / "cairn/tools/validation_store/validation_store.py"
_OS_HOSTNAME_CALLS = {("os", "uname"), ("platform", "node"), ("platform", "uname"),
                      ("socket", "gethostname")}


def test_the_store_asks_the_os_no_hostname() -> None:
    tree = ast.parse(STORE.read_text(encoding="utf-8"))
    bare = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
            for a in n.names if (n.module, a.name) in _OS_HOSTNAME_CALLS}
    found = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                and (f.value.id, f.attr) in _OS_HOSTNAME_CALLS):
            found.append((n.lineno, f.value.id + "." + f.attr))
        elif isinstance(f, ast.Name) and f.id in bare:
            found.append((n.lineno, f.id))
    assert not found, f"the store asks the OS which box: {found}"
    from cairn.devices.system_rackmount.tools.host import host
    from cairn.tools.validation_store import validation_store as vs
    assert vs.host_name is host.host_name, (vs.host_name, host.host_name)


def test_the_store_names_the_box_with_os_uname_gone() -> None:
    from cairn.devices.system_rackmount.tools.host import host
    from cairn.tools.validation_store import validation_store as vs
    had, saved = hasattr(os, "uname"), getattr(os, "uname", None)
    import platform
    platform._uname_cache = None   # platform caches uname(): ask it fresh, with os.uname gone
    if had:
        del os.uname
    try:
        want = host.host_name()
        assert want and want == want.lower() and "." not in want, want
        assert vs.host_name() == want, (vs.host_name(), want)
        assert vs.host_facts()["hostname"] == want, vs.host_facts()
    finally:
        if had:
            os.uname = saved
        platform._uname_cache = None   # never leave the uname-less answer cached for later proofs


def test_a_rebound_host_name_moves_the_host_seam_seal() -> None:
    from cairn.tools.validation_store import validation_store as vs
    real = vs.host_name
    vs.host_name = lambda: "testing-vs-other-box"
    try:
        p = vs.validations_path_for_host_seam("/nowhere/intention+why.json")
        assert p.endswith(os.path.join("validations", "intention+why", "testing-vs-other-box.json")), p
        assert vs.host_facts()["hostname"] == "testing-vs-other-box", vs.host_facts()
    finally:
        vs.host_name = real


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 3 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
