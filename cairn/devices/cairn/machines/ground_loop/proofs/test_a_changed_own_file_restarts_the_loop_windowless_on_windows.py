#!/usr/bin/env python3
"""Proof for ticket 46b04f7a0563: a changed own file restarts the ground loop windowless on Windows.

os.execv on Windows is not in place: it starts a new process and the old one exits, and the new one
runs under python.exe with a console. So on nt the restart is a detached background_pythonw successor.

  1. On Windows a changed own file leaves a successor that writes a new ``started`` to beat.json, with a
     new live pid, the old pid gone, and no python.exe, conhost.exe or visible console in its tree.
     Off Windows this tooth reads UNRAN.
  2. Off Windows the restart is os.execv(sys.executable, orig_argv) (read on every host: the helper is
     shown a posix os).
  3. COMMAND_DO_NOT_RESTART still suppresses the restart and COMMAND_EXIT still stops the loop with rc 0.
  5. A transient refused replace of beat.json (WinError 5) is retried, not fatal.
  4. On Windows the hand-off holds no gap and no overlap: the old loop writes no beat after it releases
     run.lock, and the measured release-to-claim interval (10 ms samples) is reported beside the cadence
     and stays below it. Off Windows this tooth reads UNRAN.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"46b04f7a0563": {
    "1": "test_on_windows_a_changed_own_file_leaves_a_windowless_successor_and_the_old_pid_is_gone",
    "2": "test_off_windows_the_restart_is_execv_of_the_same_command_line",
    "3": "test_do_not_restart_still_suppresses_and_exit_still_stops_with_rc_0",
    "5": "test_the_beat_record_survives_a_transient_refused_replace",
    "4": "test_on_windows_the_hand_off_has_no_overlap_and_the_interval_stays_below_the_cadence",
}}

CADENCE = 0.5          # tooth 1 and 3 (reads are spaced: beat.json is replaced under the reader, see heartbeat.write_record)
HAND_CADENCE = 5.0     # tooth 4: the interval is read against a cadence long enough to be meaningful


def _src(td: Path, class_root: Path, watch: Path, cadence: float) -> str:
    return (
        "import sys; sys.path.insert(0, %r)\n"
        "from pathlib import Path\n"
        "from cairn.tools.base.address import ROOTS\n"
        "from cairn.devices.cairn.machines.ground_loop.__main__ import main\n"
        "roots = dict(ROOTS); roots['instance'] = Path(%r)\n"
        "raise SystemExit(main(roots=roots, cadence=%r, watch=Path(%r), class_root=Path(%r)))\n"
        % (str(_REPO), str(td / "inst"), cadence, str(watch), str(class_root)))


def _home(td: Path) -> Path:
    return td / "inst" / "devices" / "cairn" / "0" / "machines" / "ground_loop"


def _read_shared(path: Path) -> bytes:
    """Read ``path`` without blocking a replace of it: heartbeat.write_record's os.replace fails with
    WinError 5 against a plain open() reader, and a loop that died of that would read as a restart bug."""
    if os.name != "nt":
        return path.read_bytes()
    import ctypes
    from ctypes import wintypes
    k = ctypes.windll.kernel32
    k.CreateFileW.restype = wintypes.HANDLE
    h = k.CreateFileW(str(path), 0x80000000, 7, None, 3, 0x80, None)   # GENERIC_READ, share R/W/DELETE, OPEN_EXISTING
    if h in (None, wintypes.HANDLE(-1).value, 0xFFFFFFFF, 2 ** 64 - 1):
        raise OSError("open failed")
    try:
        buf = ctypes.create_string_buffer(1 << 20)
        n = wintypes.DWORD()
        k.ReadFile(h, buf, len(buf), ctypes.byref(n), None)
        return buf.raw[:n.value]
    finally:
        k.CloseHandle(h)


def _record(td: Path) -> dict:
    try:
        return json.loads(_read_shared(_home(td) / "beat.json"))
    except (OSError, json.JSONDecodeError):
        return {}


def _wait(pred, secs=90.0, gap=0.1) -> bool:
    end = time.monotonic() + secs
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(gap)
    return False


def _fixture(td: Path):
    class_root, watch = td / "class", td / "watch"
    watch.mkdir()
    (watch / "loop_file.py").write_text("")
    (class_root / "cairn" / "devices" / "rack_one").mkdir(parents=True)
    return class_root, watch


def _spawn(src: str) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-c", src], cwd=str(_REPO),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                            env={**os.environ, "PYTHONPATH": str(_REPO)},
                            creationflags=0x08000000 if os.name == "nt" else 0)


def _touch_later(p: Path) -> None:
    t0 = os.stat(p).st_mtime
    os.utime(p, (t0 + 5, t0 + 5))


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


def _kill_tree(needle: str) -> None:
    for p in _tree(needle):
        subprocess.run(["taskkill", "/F", "/PID", str(p["pid"])], capture_output=True, creationflags=0x08000000)


def _alive(pid: int) -> bool:
    import ctypes
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, int(pid))   # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    try:
        code = ctypes.c_ulong()
        return bool(k.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == 259   # STILL_ACTIVE
    finally:
        k.CloseHandle(h)


def _need_windows() -> None:
    if os.name != "nt":
        raise AssertionError("UNRAN: the successor and its console are measured on Windows only")
    if Path(sys.executable).name.lower() == "pythonw.exe":
        raise AssertionError("UNRAN: the proof must run under python.exe to stand in for a python.exe loop")


def test_on_windows_a_changed_own_file_leaves_a_windowless_successor_and_the_old_pid_is_gone():
    _need_windows()
    with tempfile.TemporaryDirectory(prefix="loop-restart-proof-", ignore_cleanup_errors=True) as t:
        td = Path(t)
        class_root, watch = _fixture(td)
        proc = _spawn(_src(td, class_root, watch, CADENCE))
        needle = td.name
        try:
            assert _wait(lambda: _record(td).get("state", {}).get("beats", 0) >= 2), "the loop never beat"
            before = _record(td)
            old_pid, started = before["pid"], before["state"]["started"]
            _touch_later(watch / "loop_file.py")
            assert _wait(lambda: _record(td).get("state", {}).get("started") not in (None, started)), \
                "no successor wrote a new started"
            after = _record(td)
            assert after["pid"] != old_pid and _alive(after["pid"]), (old_pid, after["pid"])
            assert _wait(lambda: not _alive(old_pid), 20), f"the old pid {old_pid} is still alive"
            seen: set[int] = set()
            tree: list[dict] = []
            end = time.monotonic() + 3
            while time.monotonic() < end:
                time.sleep(0.15)
                tree = [p for p in _tree(needle) if p["pid"] != proc.pid] or tree
                seen |= _visible_console_pids() & {p["pid"] for p in tree}
            names = sorted({p["name"] for p in tree})
            assert tree, "no successor process was seen"
            assert "python.exe" not in names and "python3.exe" not in names, f"the successor tree holds a console python: {names}"
            assert "conhost.exe" not in names, f"the successor tree holds a console host: {names}"
            assert not seen, f"a visible console window is owned by the successor tree: {sorted(seen)}"
        finally:
            (_home(td) / "COMMAND_EXIT.flag").touch()
            _wait(lambda: not _record(td) or not _alive(_record(td).get("pid", 0)), 10)
            _kill_tree(needle)
            if proc.poll() is None:
                proc.kill()


def test_off_windows_the_restart_is_execv_of_the_same_command_line():
    from cairn.devices.cairn.machines.ground_loop import __main__ as m
    calls = []
    real_os, real_orig = m.os, getattr(sys, "orig_argv", None)
    m.os = types.SimpleNamespace(name="posix", execv=lambda exe, argv: calls.append((exe, list(argv))))
    sys.orig_argv = ["python", "-c", "src-marker"]
    try:
        m._restart(None)
    finally:
        m.os = real_os
        sys.orig_argv = real_orig
    assert calls == [(sys.executable, ["python", "-c", "src-marker"])], calls


def test_do_not_restart_still_suppresses_and_exit_still_stops_with_rc_0():
    with tempfile.TemporaryDirectory(prefix="loop-restart-proof-", ignore_cleanup_errors=True) as t:
        td = Path(t)
        class_root, watch = _fixture(td)
        proc = _spawn(_src(td, class_root, watch, CADENCE))
        try:
            assert _wait(lambda: _record(td).get("state", {}).get("beats", 0) >= 2), "the loop never beat"
            started = _record(td).get("state", {}).get("started")
            (_home(td) / "COMMAND_DO_NOT_RESTART.flag").touch()
            _touch_later(watch / "loop_file.py")
            assert _wait(lambda: _record(td).get("state", {}).get("changed")), "the change was not recorded"
            time.sleep(CADENCE * 4)
            assert _record(td).get("state", {}).get("started") == started and proc.poll() is None, "it restarted anyway"
            (_home(td) / "COMMAND_EXIT.flag").touch()
            rc = proc.wait(timeout=30)
            assert rc == 0, (rc, proc.stderr.read()[-600:])
        finally:
            if proc.poll() is None:
                proc.kill()


def test_on_windows_the_hand_off_has_no_overlap_and_the_interval_stays_below_the_cadence():
    _need_windows()
    from cairn.devices.cairn.machines.ground_loop.guard import held
    with tempfile.TemporaryDirectory(prefix="loop-restart-proof-", ignore_cleanup_errors=True) as t:
        td = Path(t)
        class_root, watch = _fixture(td)
        proc = _spawn(_src(td, class_root, watch, HAND_CADENCE))
        lock = _home(td) / "run.lock"
        needle = td.name
        try:
            assert _wait(lambda: _record(td).get("state", {}).get("beats", 0) >= 1, 120), "the loop never beat"
            old = _record(td)
            old_pid, old_beats = old["pid"], old["state"]["beats"]
            _touch_later(watch / "loop_file.py")
            samples = []          # (t, held, pid, beats); held is probed ONLY until the release is seen, because a
            released = None       # probe takes the lock for an instant and would race the successor's claim
            end = time.monotonic() + HAND_CADENCE * 3 + 40
            while time.monotonic() < end:
                rec = _record(td)
                h = True if released else held(_home(td))
                samples.append((time.monotonic(), h, rec.get("pid"), rec.get("state", {}).get("beats")))
                if not h and released is None:
                    released = samples[-1]
                if released and rec.get("pid") not in (None, old_pid):
                    break
                time.sleep(0.01)
            new_pid = _record(td).get("pid")
            assert new_pid not in (None, old_pid), "no successor claimed the lock and beat"
            rel = released
            assert rel is not None, "the lock was never seen released"
            claim = samples[-1]
            interval = claim[0] - rel[0]
            late = [s for s in samples if s[0] > rel[0] and s[2] == old_pid and s[3] != samples[0][3]
                    and (s[3] or 0) > (rel[3] or 0)]
            print(f"  hand-off interval {interval:.3f}s against cadence {HAND_CADENCE}s", flush=True)
            assert not late, f"the old loop beat after releasing the lock: {late[:3]}"
            assert interval < HAND_CADENCE, f"hand-off {interval:.3f}s is not below the cadence {HAND_CADENCE}s"
        finally:
            (_home(td) / "COMMAND_EXIT.flag").touch()
            _wait(lambda: not _record(td) or not _alive(_record(td).get("pid", 0)), 15)
            _kill_tree(needle)
            if proc.poll() is None:
                proc.kill()


def test_the_beat_record_survives_a_transient_refused_replace():
    from cairn.devices.cairn.machines.ground_loop import heartbeat as hb
    from datetime import datetime
    real, calls = hb.os.replace, []

    def flaky(a, b):
        calls.append(1)
        if len(calls) < 3:
            raise PermissionError(5, "Access is denied")
        return real(a, b)
    with tempfile.TemporaryDirectory(prefix="loop-restart-proof-", ignore_cleanup_errors=True) as t:
        hb.os.replace = flaky
        try:
            final = hb.write_record(datetime.now(), {"beats": 1}, 7, Path(t))
        finally:
            hb.os.replace = real
        assert json.loads(final.read_text())["pid"] == 7 and len(calls) == 3, calls


TEETH = [test_the_beat_record_survives_a_transient_refused_replace,
         test_on_windows_a_changed_own_file_leaves_a_windowless_successor_and_the_old_pid_is_gone,
         test_off_windows_the_restart_is_execv_of_the_same_command_line,
         test_do_not_restart_still_suppresses_and_exit_still_stops_with_rc_0,
         test_on_windows_the_hand_off_has_no_overlap_and_the_interval_stays_below_the_cadence]


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
