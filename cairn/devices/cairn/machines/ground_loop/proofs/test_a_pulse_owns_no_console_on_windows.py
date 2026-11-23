#!/usr/bin/env python3
"""Proof for ticket 8c829d9b38b8: the beat's pulse child owns no console on Windows.

Measured 2026-11-23 on akiendell: visible ConsoleWindowClass windows (EnumWindows, 20 ms) were all
``venv\\Scripts\\python3.exe .../groundloop/pulse.py`` -- heartbeat.spawn_pulses spawned
sys.executable (the venv python launcher) every beat; with DETACHED_PROCESS it has no console to
inherit, so the launcher's real python.exe allocates a new visible one.

  1. On Windows, a beat run under python.exe spawns a pulse whose process tree holds no
     python.exe, no conhost.exe and no visible console window (the instrument is EnumWindows over
     the tree). Off Windows this tooth reads UNRAN: it cannot be measured there.
  2. Off Windows the pulse argv[0] is still sys.executable (read on every host; the Windows host shows
     windowless_spawn a posix os).
  3. The pulse still runs and the beat's entry records its path, mtime and pid, as before.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.devices.cairn.machines.ground_loop import heartbeat as hb  # noqa: E402

PROVES = {"8c829d9b38b8": {
    "1": "test_on_windows_a_pulse_owns_no_python_exe_no_conhost_and_no_visible_console",
    "2": "test_off_windows_the_pulse_argv_is_unchanged",
    "3": "test_the_pulse_still_runs_and_the_beat_records_it",
}}

_SLEEP = "import time\ntime.sleep(12)\n"
_MARK = "import os\nopen({m!r}, 'a').write(str(os.getpid()) + '\\n')\n"


def _root(td: Path, src: str) -> Path:
    d = td / "cairn" / "devices" / "alpha" / "groundloop"
    d.mkdir(parents=True)
    (d / "pulse.py").write_text(src, encoding="utf-8")
    return td


def _tree(needle: str) -> list[dict]:
    """Every process whose command line names ``needle``, plus its descendants (CIM)."""
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


def test_on_windows_a_pulse_owns_no_python_exe_no_conhost_and_no_visible_console():
    if os.name != "nt":
        raise AssertionError("UNRAN: a Windows console is measured on Windows only")
    if Path(sys.executable).name.lower() == "pythonw.exe":
        raise AssertionError("UNRAN: the proof must run under python.exe to stand in for a python.exe loop")
    with tempfile.TemporaryDirectory(prefix="pulse-console-proof-", ignore_cleanup_errors=True) as d:
        root = _root(Path(d), _SLEEP)
        entries, held = hb.spawn_pulses(root)
        seen_visible: set[int] = set()
        tree: list[dict] = []
        try:
            end = time.monotonic() + 6
            while time.monotonic() < end:
                time.sleep(0.15)
                tree = _tree(str(root / "cairn" / "devices" / "alpha" / "groundloop" / "pulse.py")) or tree
                pids = {p["pid"] for p in tree}
                seen_visible |= _visible_console_pids() & pids
        finally:
            for p in tree:
                subprocess.run(["taskkill", "/F", "/PID", str(p["pid"])], capture_output=True,
                               creationflags=0x08000000)
        names = sorted({p["name"] for p in tree})
        assert tree, f"no pulse process was seen: {entries}"
        assert "python.exe" not in names and "python3.exe" not in names, f"the pulse tree holds a console python: {names}"
        assert "conhost.exe" not in names, f"the pulse tree holds a console host: {names}"
        assert not seen_visible, f"a visible console window is owned by the pulse tree: {sorted(seen_visible)}"


def test_off_windows_the_pulse_argv_is_unchanged():
    """Reads on every host: windowless_spawn is shown a non-nt ``os``, so the Windows host answers too
    (a tooth both hosts read UNRAN could never seal, ticket 8c829d9b38b8)."""
    import types
    from cairn.tools.windowless_spawn import windowless_spawn as ws
    argvs = []
    real = hb.subprocess.Popen
    real_os = ws.os
    ws.os = types.SimpleNamespace(name="posix", path=os.path)

    class _P:
        pid = 1

        def poll(self):
            return 0
    try:
        hb.subprocess.Popen = lambda argv, **kw: (argvs.append(list(argv)), _P())[1]
        with tempfile.TemporaryDirectory(prefix="pulse-console-proof-") as d:
            hb.spawn_pulses(_root(Path(d), "pass\n"))
    finally:
        hb.subprocess.Popen = real
        ws.os = real_os
    assert len(argvs) == 1 and argvs[0][0] == sys.executable, argvs


def test_the_pulse_still_runs_and_the_beat_records_it():
    with tempfile.TemporaryDirectory(prefix="pulse-console-proof-", ignore_cleanup_errors=True) as d:
        marker = Path(d) / "ran.txt"
        root = _root(Path(d), _MARK.format(m=str(marker)))
        entries, held = hb.spawn_pulses(root)
        end = time.monotonic() + 15
        while time.monotonic() < end and not marker.exists():
            time.sleep(0.1)
        e = entries[0]
        assert e["device"] == "alpha" and e["path"].endswith("pulse.py"), entries
        assert isinstance(e.get("mtime"), float) and isinstance(e.get("pid"), int), entries
        assert marker.exists() and marker.read_text().split(), "the pulse did not run"


TEETH = [test_on_windows_a_pulse_owns_no_python_exe_no_conhost_and_no_visible_console,
         test_off_windows_the_pulse_argv_is_unchanged, test_the_pulse_still_runs_and_the_beat_records_it]


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
