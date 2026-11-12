"""Proof for ticket 3264ef726e35 — `cairn start`, `cairn stop` and `cairn restart` cycle the system.

Measured 2026-11-10 before the build: `cairn restart` answered "no such device or command", and
cairn/devices/cairn/bin/ did not exist. Outline 5.3.4: "`cairn start` (= cairn cairn start) brings
the system up: ground loop, bus, shims. `cairn stop` takes it down." The shims live in the one bus
process, so the system's parts are two: the instance's ground loop and its bus.

Every verb runs as `bin/cairn <verb>` in a subprocess whose HOME is a scratch folder from the
scratch door, so the ground loop and bus it cycles are that HOME's, never the live ones: the loop's
home, its lock and the bus home are all read from HOME. Units are proof-named, so a leak explains
itself, and the teardown stops both whatever happened.

Teeth, one per falsifier clause:

  1. from nothing, `cairn start` exits 0; the scratch loop lock is held and the scratch bus answers stats;
  2. from up, `cairn stop` exits 0; the lock is free and the bus is silent; a second stop exits 0
     and says "already down" for both parts;
  3. from up, `cairn restart` exits 0; the bus answers with a new pid and the lock is held by a new pid;
  4. the live bus pid and live loop pid are the same before and after;
  5. start, stop and restart are Python scripts in cairn/devices/cairn/bin/, and cycle.py imports
     no other device's code (RULE 1).

    python3 cairn/devices/cairn/proofs/test_start_stop_restart_cycle_the_system.py   # exit 0 = green
"""
from __future__ import annotations

import ast
import os
import pwd
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
CAIRN = REPO / "bin" / "cairn"
BIN = REPO / "cairn" / "devices" / "cairn" / "bin"
CYCLE = REPO / "cairn" / "devices" / "cairn" / "cycle.py"
ACCOUNT = Path(pwd.getpwuid(os.getuid()).pw_dir)
LOOP_UNIT = f"cairn-ground-loop-proof-{os.getpid()}"
BUS_UNIT = f"cairn-bus-proof-{os.getpid()}"

PROVES = {
    "3264ef726e35": {
        "1": "start_brings_the_loop_and_the_bus_up",
        "2": "stop_takes_both_down_and_says_so_when_already_down",
        "3": "restart_brings_both_back_with_new_pids",
        "4": "the_live_system_is_untouched",
        "5": "the_shortcuts_are_python_in_the_cairn_bin_and_import_no_other_device",
    },
    # a817fce02520 clause 4: behind its argument check, a bare verb still acts.
    "a817fce02520": {
        "4": "restart_brings_both_back_with_new_pids",
    },
}

FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1600]}", flush=True)
        FAILURES.append(name)


def _loop_home(home: Path) -> Path:
    return home / ".cairn" / "devices" / "cairn" / "0" / "machines" / "ground_loop"


def _bus_home(home: Path) -> Path:
    return home / ".cairn" / "devices" / "cairn" / "machines" / "bus" / "0"


def _loop(home: Path) -> tuple[bool, int | None]:
    """(lock held, the pid its record names) for the loop under ``home``."""
    from cairn.devices.cairn.machines.ground_loop.guard import held
    from cairn.devices.cairn.machines.ground_loop.heartbeat import read_record
    lh = _loop_home(home)
    return held(lh), (read_record(lh).get("record") or {}).get("pid")


def _bus_pid(home: Path) -> int | None:
    """The pid the bus under ``home`` answers stats with, or None when nothing answers. Never wakes it."""
    from cairn.tools.bus_client.remote import exchange
    try:
        r = exchange({"op": "stats"}, _bus_home(home), timeout=10)
    except (OSError, ConnectionError, ValueError):
        return None
    return (r.get("json") or {}).get("pid") if r.get("ok") else None


def _cairn(home: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "HOME": str(home), "CAIRN_VENV": str(ACCOUNT / ".cairn" / "venv"),
           "CAIRN_GROUND_LOOP_UNIT": LOOP_UNIT, "CAIRN_BUS_UNIT": BUS_UNIT}
    env.pop("CAIRN_BUS_HOME", None)
    env.pop("CAIRN_INSTANCE_ROOT", None)
    return subprocess.run([str(CAIRN), *args], capture_output=True, text=True, env=env, timeout=400)


def _said(r: subprocess.CompletedProcess) -> str:
    return f"rc={r.returncode} out={r.stdout[-700:]!r} err={r.stderr[-700:]!r}"


def _teardown() -> None:
    for unit in (LOOP_UNIT, BUS_UNIT):
        subprocess.run(["systemctl", "--user", "stop", unit], capture_output=True, timeout=60)


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("3264-home-")
    live_bus_before = _bus_pid(ACCOUNT)
    live_loop_before = _loop(ACCOUNT)
    try:
        r = _cairn(home, "start")
        held, lpid = _loop(home)
        bpid = _bus_pid(home)
        _check("start_brings_the_loop_and_the_bus_up",
               r.returncode == 0 and held and bpid is not None,
               f"{_said(r)} held={held} bus_pid={bpid}")

        r = _cairn(home, "stop")
        held2, _ = _loop(home)
        b2 = _bus_pid(home)
        r2 = _cairn(home, "stop")
        _check("stop_takes_both_down_and_says_so_when_already_down",
               r.returncode == 0 and not held2 and b2 is None
               and r2.returncode == 0 and r2.stdout.count("already down") == 2,
               f"first {_said(r)} held={held2} bus_pid={b2}; second {_said(r2)}")

        _cairn(home, "start")
        held3, lpid3 = _loop(home)
        bpid3 = _bus_pid(home)
        r = _cairn(home, "restart")
        time.sleep(2)
        held4, lpid4 = _loop(home)
        bpid4 = _bus_pid(home)
        _check("restart_brings_both_back_with_new_pids",
               r.returncode == 0 and held3 and held4 and None not in (lpid3, lpid4, bpid3, bpid4)
               and lpid4 != lpid3 and bpid4 != bpid3,
               f"{_said(r)} loop {lpid3}->{lpid4} held {held3}/{held4}; bus {bpid3}->{bpid4}")

        _cairn(home, "stop")
    finally:
        _teardown()

    live_bus_after = _bus_pid(ACCOUNT)
    live_loop_after = _loop(ACCOUNT)
    _check("the_live_system_is_untouched",
           live_bus_after == live_bus_before and live_loop_after[1] == live_loop_before[1]
           and live_loop_after[0] == live_loop_before[0],
           f"bus {live_bus_before}->{live_bus_after}; loop {live_loop_before}->{live_loop_after}")

    bad = []
    for name in ("start", "stop", "restart"):
        p = BIN / name
        if not (p.is_file() and os.access(p, os.X_OK)):
            bad.append(f"{name}: not an executable file at {p}")
            continue
        src = p.read_text(encoding="utf-8")
        if not src.startswith("#!/usr/bin/env python3"):
            bad.append(f"{name}: not a python3 script")
        try:
            ast.parse(src)
        except SyntaxError as exc:
            bad.append(f"{name}: does not parse as python ({exc})")
    if CYCLE.is_file():
        for node in ast.walk(ast.parse(CYCLE.read_text(encoding="utf-8"))):
            mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                    else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            for m in mods:
                if m.startswith("cairn.devices.") and not m.startswith("cairn.devices.cairn."):
                    bad.append(f"cycle.py imports {m}")
    else:
        bad.append(f"no {CYCLE}")
    _check("the_shortcuts_are_python_in_the_cairn_bin_and_import_no_other_device", not bad, "; ".join(bad))

    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
