#!/usr/bin/env python3
"""Proof for ticket 183f9389c5fa: the web server's ground-loop pulse names its host through the system device's host tool.

Measured 2026-11-21: cairn/devices/web_server/groundloop/pulse.py asked the OS for this box's name itself. Outline 6.6.3.7: nothing
else in Cairn asks the OS for the hostname; callers reach it through the client tool the system
device publishes (RULE 1). (1) an AST scan of the file finds no os.uname, platform.node,
platform.uname or socket.gethostname call, and the file names the box through host_name;
(2) with os.uname deleted, is_cairn_home(host_name().upper() + '.lan', addresses=()) is True and is_cairn_home('testing-web-not-this-box', addresses=()) is False.

The subject is imported inside each tooth, so a hollow build reds per tooth.

    bin/cairn test cairn/devices/web_server/proofs/test_the_pulse_names_its_host_through_the_system_device.py
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"183f9389c5fa": {"1": "test_it_asks_the_os_no_hostname",
                           "2": "test_the_pulse_knows_its_home_with_os_uname_gone"}}

SUBJECTS = ['cairn/devices/web_server/groundloop/pulse.py']
_OS_HOSTNAME_CALLS = {("os", "uname"), ("platform", "node"), ("platform", "uname"),
                      ("socket", "gethostname")}


def _os_hostname_calls(src: str) -> list:
    tree = ast.parse(src)
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
    return found


def test_it_asks_the_os_no_hostname() -> None:
    for rel in SUBJECTS:
        src = (_REPO_ROOT / rel).read_text(encoding="utf-8")
        assert not _os_hostname_calls(src), (rel, _os_hostname_calls(src))
        assert "cairn.devices.system_rackmount.tools.host.host" in src and "host_name" in src, (
            rel, "does not name the box through the system device's host tool")


class _NoUname:
    """os.uname deleted (as on Windows) and platform's uname cache cleared on the way in and out,
    so the answer is asked fresh and the uname-less answer never stays cached for later proofs."""

    def __enter__(self):
        import platform
        platform._uname_cache = None
        self.saved = getattr(os, "uname", None)
        if self.saved is not None:
            del os.uname
        return self

    def __exit__(self, *exc):
        import platform
        if self.saved is not None:
            os.uname = self.saved
        platform._uname_cache = None
        return False


class _Env:
    """Set (value) or unset (None) environment variables for the block, restored after."""

    def __init__(self, **kv):
        self.kv, self.saved = kv, {}

    def __enter__(self):
        for k, v in self.kv.items():
            self.saved[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


def test_the_pulse_knows_its_home_with_os_uname_gone() -> None:
    from cairn.devices.system_rackmount.tools.host.host import host_name
    from cairn.devices.web_server.groundloop.pulse import is_cairn_home
    with _NoUname():
        assert is_cairn_home(host_name().upper() + ".lan", addresses=()) is True
        assert is_cairn_home("testing-web-not-this-box", addresses=()) is False


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 2 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
