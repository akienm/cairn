#!/usr/bin/env python3
"""Proof for ticket 60f16ffccd43: the launch tool the system device publishes answers the launch
path's OS questions, measured at its own address.

Measured 2026-11-22: the shell superclaude (retired by e179281f6eff) answered eight OS questions in bash (uname,
hostname -I, sudo, systemd-run units, ss -tlnH, systemd-run --scope). A Python launcher must ask
them somewhere, and RULE 1 puts every OS answer in the system device.

  1. on Linux, venv_bin_dir, box_addresses, port_listening, stream_is_console and
     runs_shell_scripts return what the bash computes on this box for the same input.
  2. service_spawn starts a uniquely named transient user unit, and a second call while it runs
     returns held and starts nothing.
  3. scoped_exec runs a child whose own cgroup memory.max equals the MemoryMax passed.
  4. every result names how it was answered, from the stated set, and none is empty.

Off a box with systemd --user, teeth 2 and 3 print UNMEASURED: a state, never a green. The tool is
imported inside each tooth, so an absent or hollow build reds the tooth, not the run.

    bin/cairn test cairn/devices/system_rackmount/tools/launch/proofs/test_the_launch_tool_answers_the_launch_paths_os_questions.py
"""
from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_MODULE = "cairn.devices.system_rackmount.tools.launch.launch"
_HOWS = {"systemd", "setsid", "detached", "held", "scope", "plain", "passwordless", "password-held",
         "none", "elevated", "not-elevated", "not-on-this-box"}

PROVES = {"60f16ffccd43": {
    "1": "test_the_answers_equal_the_bash_on_this_box",
    "2": "test_a_service_spawn_holds_its_unit_name",
    "3": "test_a_scoped_exec_runs_under_the_memory_max_passed",
    "4": "test_every_result_names_how_it_was_answered",
}, "4aafe74aff69": {"2": "test_a_scoped_exec_runs_under_the_memory_max_passed"}}


class Unmeasured(Exception):
    """The tooth cannot run here; that is a state, never a green."""


def _launch():
    return importlib.import_module(_MODULE)


def _bash(script: str, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60, **kw)


def _need_user_systemd():
    if os.name == "nt" or not shutil.which("systemd-run"):
        raise Unmeasured("no systemd-run on this box")
    if subprocess.run(["systemctl", "--user", "is-system-running"], capture_output=True,
                      text=True, timeout=30).stdout.strip() in ("", "offline"):
        raise Unmeasured("no systemd --user manager on this box")


def test_the_answers_equal_the_bash_on_this_box():
    if os.name == "nt":
        raise Unmeasured("the bash it is compared with does not run on nt")
    L = _launch()
    with tempfile.TemporaryDirectory() as d:
        venv = Path(d) / "venv"
        sub = _bash('case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) echo Scripts;; *) echo bin;; esac').stdout.strip()
        assert Path(L.venv_bin_dir(venv)) == venv / sub, f"venv_bin_dir {L.venv_bin_dir(venv)!r}, bash says {sub!r}"
    want = _bash("hostname -I 2>/dev/null").stdout.split()
    assert list(L.box_addresses()) == want, f"box_addresses {L.box_addresses()!r}, hostname -I {want!r}"
    # A listener in a child (http.server), so the proof imports no module that can dial.
    srv = subprocess.Popen([sys.executable, "-u", "-m", "http.server", "--bind", "127.0.0.1", "0"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        line = srv.stdout.readline()
        held = int(line.split(" port ")[1].split()[0])
        for _ in range(50):
            if _bash(f"ss -tlnH 2>/dev/null | grep -q ':{held}\\b'").returncode == 0:
                break
            time.sleep(0.1)
        bash = _bash(f"ss -tlnH 2>/dev/null | grep -q ':{held}\\b'").returncode == 0
        assert bash, f"ss does not see the child's listener on {held}: {line!r}"
        assert L.port_listening(held) is True, f"port_listening({held}) reads a listening port as free"
    finally:
        srv.kill(); srv.wait(timeout=30)
    for _ in range(50):
        if _bash(f"ss -tlnH 2>/dev/null | grep -q ':{held}\\b'").returncode != 0:
            break
        time.sleep(0.1)
    bash = _bash(f"ss -tlnH 2>/dev/null | grep -q ':{held}\\b'").returncode == 0
    assert L.port_listening(held) is bash, f"port_listening({held}) {L.port_listening(held)!r} after the close, ss says {bash!r}"
    master, slave = os.openpty()
    r, w = os.pipe()
    try:
        for fd, label in ((slave, "pty"), (r, "pipe")):
            bash = _bash("[ -t 0 ]", stdin=fd).returncode == 0
            got = L.stream_is_console(os.fdopen(os.dup(fd), "rb", buffering=0))
            assert got is bash, f"stream_is_console({label}) {got!r}, [ -t 0 ] says {bash!r}"
    finally:
        for fd in (master, slave, r, w):
            os.close(fd)
    win = _bash('case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) echo no;; *) echo yes;; esac').stdout.strip() == "yes"
    assert L.runs_shell_scripts() is win, f"runs_shell_scripts {L.runs_shell_scripts()!r}, bash says {win!r}"


def _unit_main_pid(unit: str) -> str:
    return subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value", f"{unit}.service"],
                          capture_output=True, text=True, timeout=30).stdout.strip()


def test_a_service_spawn_holds_its_unit_name():
    _need_user_systemd()
    L = _launch()
    unit = f"cairn-launch-proof-{os.getpid()}-{int(time.time())}"
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "unit.log"
        argv = [sys.executable, "-c", "import time; print('launch-proof-up', flush=True); time.sleep(120)"]
        try:
            first = L.service_spawn(unit, argv, log=log, cwd=d)
            assert first["ok"] and first["how"] == "systemd", f"the first spawn: {first!r}"
            for _ in range(50):
                pid = _unit_main_pid(unit)
                if pid not in ("", "0"):
                    break
                time.sleep(0.1)
            assert pid not in ("", "0"), f"{unit}.service has no main pid after the spawn: {first!r}"
            second = L.service_spawn(unit, argv, log=log, cwd=d)
            assert second["ok"] and second["how"] == "held", f"the second spawn did not read held: {second!r}"
            assert _unit_main_pid(unit) == pid, "the second spawn replaced the running unit"
        finally:
            subprocess.run(["systemctl", "--user", "stop", f"{unit}.service"], capture_output=True, timeout=30)
            subprocess.run(["systemctl", "--user", "reset-failed", f"{unit}.service"], capture_output=True, timeout=30)


# The scoped child asks the cgroup tool for its own cgroup (ticket 4aafe74aff69): the tool is the
# one reader of a process's cgroup file, which the ground loop's proof holds the corpus to.
_READ_MAX = ("import pathlib, sys; sys.path.insert(0, %r); "
             "from cairn.tools.cgroup.cgroup import cgroup_of; "
             "print('memory.max', pathlib.Path('/sys/fs/cgroup' + cgroup_of(), 'memory.max').read_text().strip())"
             ) % str(_REPO)


def test_a_scoped_exec_runs_under_the_memory_max_passed():
    _need_user_systemd()
    child = ("import sys; sys.path.insert(0, %r); "
             "from cairn.devices.system_rackmount.tools.launch import launch; "
             "launch.scoped_exec([sys.executable, '-c', %r], mem_high='90M', mem_max='100M', swap_max='0', "
             "unit='cairn-launch-proof-scope-%d')") % (str(_REPO), _READ_MAX, os.getpid())
    got = subprocess.run([sys.executable, "-c", child], capture_output=True, text=True, timeout=120)
    lines = [l for l in got.stdout.splitlines() if l.startswith("memory.max ")]
    assert lines, f"the scoped child printed no memory.max (rc {got.returncode}): {got.stdout[-300:]!r} {got.stderr[-300:]!r}"
    assert lines[-1].split()[1] == str(100 * 1024 * 1024), f"the child's memory.max is {lines[-1]!r}, not 100M"


def test_every_result_names_how_it_was_answered():
    L = _launch()
    results = {"elevation": L.elevation(), "scoped_argv": L.scoped_argv(["true"], mem_high="90M", mem_max="100M", swap_max="0")}
    for name, res in results.items():
        assert isinstance(res, dict) and set(res) >= {"ok", "how", "detail"}, f"{name} returned {res!r}"
        assert res["how"] in _HOWS, f"{name}'s how {res['how']!r} is not in the stated set"
        assert str(res["detail"]).strip(), f"{name} names no detail: {res!r}"
    assert results["scoped_argv"].get("argv"), f"scoped_argv returned no argv: {results['scoped_argv']!r}"


TEETH = [test_the_answers_equal_the_bash_on_this_box,
         test_a_service_spawn_holds_its_unit_name,
         test_a_scoped_exec_runs_under_the_memory_max_passed,
         test_every_result_names_how_it_was_answered]


def main() -> int:
    failed = unmeasured = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}", flush=True)
        except Unmeasured as e:
            unmeasured += 1
            print(f"  UNMEASURED  {t.__name__}: {e}", flush=True)
        except Exception as e:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {e}", flush=True)
    print(f"\n{len(TEETH) - failed - unmeasured}/{len(TEETH)} teeth green, {unmeasured} unmeasured")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
