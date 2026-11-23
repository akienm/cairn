#!/usr/bin/env python3
"""Proof for ticket 4c9a6ec90b5d: the web server's pulse starts its listener with no console on Windows.

Sibling of ticket 8c829d9b38b8 (the heartbeat's pulse spawn). groundloop/pulse.py's ``ensure`` took
``python: str = sys.executable``, so a silent port started listener.py through the venv python
launcher under DETACHED_PROCESS, and the launcher's real python.exe allocates a visible console.

  1. On Windows, ensure() on a silent scratch port starts a listener tree holding no python.exe,
     no python3.exe, no conhost.exe and no visible console window (CIM tree plus EnumWindows).
     Off Windows this tooth reads UNRAN.
  2. Off Windows the listener argv[0] is sys.executable (read on every host: windowless_spawn is
     shown a posix os).
  3. An explicit ``python`` argument is used as given, and a held port spawns nothing.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import os
import random
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"4c9a6ec90b5d": {
    "1": "test_on_windows_the_listener_owns_no_python_exe_no_conhost_and_no_visible_console",
    "2": "test_off_windows_the_listener_argv_is_unchanged",
    "3": "test_an_explicit_python_is_used_as_given_and_a_held_port_spawns_nothing",
}}


def _pulse():
    from cairn.devices.web_server.groundloop import pulse
    return pulse


def _free_port(pulse) -> int:
    held = pulse._listen_ports()
    while True:
        port = random.randint(20000, 60000)
        if port not in held:
            return port


def _tree(needle: str) -> list[dict]:
    ps = ("$all = Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,CommandLine; "
          "$ids = @($all | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('%s') -and $_.CommandLine -notlike '*Get-CimInstance*' } | "
          "ForEach-Object { $_.ProcessId }); $n = 0; "
          "while ($n -ne $ids.Count) { $n = $ids.Count; "
          "$ids = @($ids + ($all | Where-Object { $ids -contains $_.ParentProcessId } | "
          "ForEach-Object { $_.ProcessId }) | Select-Object -Unique) }; "
          "$all | Where-Object { $ids -contains $_.ProcessId } | ForEach-Object { \"$($_.ProcessId)`t$($_.Name)\" }"
          % needle.replace("'", "''"))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                       creationflags=0x08000000, timeout=60)
    out = []
    for line in r.stdout.splitlines():
        if "\t" in line:
            pid, name = line.split("\t", 1)
            out.append({"pid": int(pid), "name": name.strip().lower()})
    return out


def _visible_console_pids() -> set[int]:
    import ctypes
    from ctypes import wintypes
    u = ctypes.windll.user32
    found: set[int] = set()
    cb_t = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(h, _l):
        if u.IsWindowVisible(h):
            buf = ctypes.create_unicode_buffer(256)
            u.GetClassNameW(h, buf, 256)
            if buf.value == "ConsoleWindowClass":
                pid = wintypes.DWORD()
                u.GetWindowThreadProcessId(h, ctypes.byref(pid))
                found.add(pid.value)
        return True
    u.EnumWindows(cb_t(cb), 0)
    return found


def test_on_windows_the_listener_owns_no_python_exe_no_conhost_and_no_visible_console():
    if os.name != "nt":
        raise AssertionError("UNRAN: a Windows console is measured on Windows only")
    if Path(sys.executable).name.lower() == "pythonw.exe":
        raise AssertionError("UNRAN: the proof must run under python.exe to stand in for a python.exe loop")
    pulse = _pulse()
    port = _free_port(pulse)
    with tempfile.TemporaryDirectory(prefix="web-pulse-console-proof-", ignore_cleanup_errors=True) as d:
        res = pulse.ensure(port, "127.0.0.1", unit=None, log=Path(d) / "pulse.log")
        assert res.get("spawned") == "setsid" and res.get("pid"), res
        needle = f"--port {port}"
        seen_visible: set[int] = set()
        tree: list[dict] = []
        try:
            end = time.monotonic() + 8
            while time.monotonic() < end:
                time.sleep(0.15)
                tree = _tree(needle) or tree
                seen_visible |= _visible_console_pids() & {p["pid"] for p in tree}
        finally:
            for p in tree:
                subprocess.run(["taskkill", "/F", "/PID", str(p["pid"])], capture_output=True,
                               creationflags=0x08000000)
    names = sorted({p["name"] for p in tree})
    assert tree, f"no listener process was seen: {res}"
    assert "python.exe" not in names and "python3.exe" not in names, f"the listener tree holds a console python: {names}"
    assert "conhost.exe" not in names, f"the listener tree holds a console host: {names}"
    assert not seen_visible, f"a visible console window is owned by the listener tree: {sorted(seen_visible)}"


def _argv_of(call):
    """Run ``call(pulse)`` with Popen and the port table stubbed; return the argv it started."""
    pulse = _pulse()
    argvs: list[list[str]] = []

    class _P:
        pid = 1

    real_popen, real_listening = pulse.subprocess.Popen, pulse.listening
    pulse.subprocess.Popen = lambda argv, **kw: (argvs.append(list(argv)), _P())[1]
    pulse.listening = lambda port: False
    try:
        with tempfile.TemporaryDirectory(prefix="web-pulse-console-proof-", ignore_cleanup_errors=True) as d:
            call(pulse, Path(d) / "pulse.log")
    finally:
        pulse.subprocess.Popen, pulse.listening = real_popen, real_listening
    return argvs


def test_off_windows_the_listener_argv_is_unchanged():
    from cairn.tools.windowless_spawn import windowless_spawn as ws
    real_os = ws.os
    ws.os = types.SimpleNamespace(name="posix", path=os.path)
    try:
        argvs = _argv_of(lambda p, log: p.ensure(45999, "127.0.0.1", unit=None, log=log))
    finally:
        ws.os = real_os
    assert len(argvs) == 1 and argvs[0][0] == sys.executable, argvs


def test_an_explicit_python_is_used_as_given_and_a_held_port_spawns_nothing():
    argvs = _argv_of(lambda p, log: p.ensure(45998, "127.0.0.1", unit=None, log=log, python="X-python"))
    assert len(argvs) == 1 and argvs[0][0] == "X-python", argvs
    pulse = _pulse()
    real, pulse.listening = pulse.listening, (lambda port: True)
    held: list = []
    real_popen = pulse.subprocess.Popen
    pulse.subprocess.Popen = lambda *a, **k: held.append(a)
    try:
        with tempfile.TemporaryDirectory(prefix="web-pulse-console-proof-", ignore_cleanup_errors=True) as d:
            res = pulse.ensure(45997, "127.0.0.1", unit=None, log=Path(d) / "pulse.log")
    finally:
        pulse.listening, pulse.subprocess.Popen = real, real_popen
    assert res["spawned"] == "none" and not held, (res, held)


TEETH = [test_on_windows_the_listener_owns_no_python_exe_no_conhost_and_no_visible_console,
         test_off_windows_the_listener_argv_is_unchanged,
         test_an_explicit_python_is_used_as_given_and_a_held_port_spawns_nothing]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}", flush=True)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {t.__name__}: {type(e).__name__}: {e}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
