"""Proof for ticket a817fce02520 — the cycle verbs answer --help and refuse what they do not know.

Measured 2026-11-10 before the build: `cairn stop --help` took the live system down, because the
stop shortcut ignored its arguments. The ground loop (pid 4730) and the bus stopped, and
`cairn start` was needed to bring them back.

Every verb runs as `bin/cairn <verb> <arg>` in a subprocess whose HOME is a scratch folder from
the scratch door. So the ground loop and bus it could touch are that HOME's, never the live ones.
Units are proof-named, and the teardown stops both whatever happened.

Teeth, one per falsifier clause (clause 4 is the cycle proof itself, run beside this one):

  1. with the scratch system up, `stop --help`, `stop -h` and `restart --help` exit 0, print
     `usage: cairn <verb>` and leave the loop pid and bus pid unchanged;
  2. with nothing up, `start --help` exits 0, prints the usage line, and nothing comes up;
  3. `stop now` and `restart now` (up) and `start now` (nothing up) exit 2 with stderr naming
     `now`; no pid changes and nothing comes up;
  5. the live bus pid and live loop pid are the same before and after.

    python3 cairn/devices/cairn/proofs/test_the_cycle_verbs_refuse_what_they_do_not_know.py   # exit 0 = green
"""
from __future__ import annotations

import os
import pwd
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
CAIRN = REPO / "bin" / "cairn"
ACCOUNT = Path(pwd.getpwuid(os.getuid()).pw_dir)
LOOP_UNIT = f"cairn-ground-loop-proof-a817-{os.getpid()}"
BUS_UNIT = f"cairn-bus-proof-a817-{os.getpid()}"

PROVES = {
    "a817fce02520": {
        "1": "help_on_an_up_system_prints_usage_and_changes_nothing",
        "2": "start_help_on_a_down_system_brings_nothing_up",
        "3": "an_unknown_argument_exits_2_naming_it_and_changes_nothing",
        "5": "the_live_system_is_untouched",
    },
}

FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:2000]}", flush=True)
        FAILURES.append(name)


def _loop(home: Path) -> tuple[bool, int | None]:
    """(lock held, the pid its record names) for the loop under ``home``."""
    from cairn.devices.cairn.machines.ground_loop.guard import held
    from cairn.devices.cairn.machines.ground_loop.heartbeat import read_record
    lh = home / ".cairn" / "devices" / "cairn" / "0" / "machines" / "ground_loop"
    return held(lh), (read_record(lh).get("record") or {}).get("pid")


def _bus_pid(home: Path) -> int | None:
    """The pid the bus under ``home`` answers stats with, or None. Never wakes it."""
    from cairn.tools.bus_client.remote import exchange
    try:
        r = exchange({"op": "stats"}, home / ".cairn" / "devices" / "cairn" / "machines" / "bus" / "0",
                     timeout=10)
    except (OSError, ConnectionError, ValueError):
        return None
    return (r.get("json") or {}).get("pid") if r.get("ok") else None


def _state(home: Path) -> tuple:
    held, lpid = _loop(home)
    return held, lpid, _bus_pid(home)


def _cairn(home: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "HOME": str(home), "CAIRN_VENV": str(ACCOUNT / ".cairn" / "venv"),
           "CAIRN_GROUND_LOOP_UNIT": LOOP_UNIT, "CAIRN_BUS_UNIT": BUS_UNIT}
    env.pop("CAIRN_BUS_HOME", None)
    env.pop("CAIRN_INSTANCE_ROOT", None)
    return subprocess.run([str(CAIRN), *args], capture_output=True, text=True, env=env, timeout=400)


def _said(r: subprocess.CompletedProcess) -> str:
    return f"rc={r.returncode} out={r.stdout[-500:]!r} err={r.stderr[-500:]!r}"


def _teardown() -> None:
    for unit in (LOOP_UNIT, BUS_UNIT):
        subprocess.run(["systemctl", "--user", "stop", unit], capture_output=True, timeout=60)


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("a817-home-")
    live_before = (_bus_pid(ACCOUNT), _loop(ACCOUNT))
    try:
        # (2) and (3, start half) over nothing up, before anything has been started here.
        down = _state(home)
        r = _cairn(home, "start", "--help")
        after = _state(home)
        _check("start_help_on_a_down_system_brings_nothing_up",
               r.returncode == 0 and r.stdout.startswith("usage: cairn start")
               and not after[0] and after[2] is None,
               f"{_said(r)} before={down} after={after}")

        r_start_now = _cairn(home, "start", "now")
        after_start_now = _state(home)

        # (1) and (3, stop/restart half) over a scratch system that is up.
        up = _cairn(home, "start")
        before = _state(home)
        bad = []
        if up.returncode != 0 or not before[0] or before[2] is None:
            bad.append(f"the scratch system did not come up: {_said(up)} state={before}")
        for verb, flag in (("stop", "--help"), ("stop", "-h"), ("restart", "--help")):
            r = _cairn(home, verb, flag)
            now = _state(home)
            if not (r.returncode == 0 and r.stdout.startswith(f"usage: cairn {verb}") and now == before):
                bad.append(f"{verb} {flag}: {_said(r)} state {before}->{now}")
        _check("help_on_an_up_system_prints_usage_and_changes_nothing", not bad, "; ".join(bad))

        bad = []
        if not (r_start_now.returncode == 2 and "now" in r_start_now.stderr
                and not after_start_now[0] and after_start_now[2] is None):
            bad.append(f"start now: {_said(r_start_now)} state after={after_start_now}")
        for verb in ("stop", "restart"):
            r = _cairn(home, verb, "now")
            now = _state(home)
            if not (r.returncode == 2 and "now" in r.stderr and now == before):
                bad.append(f"{verb} now: {_said(r)} state {before}->{now}")
        _check("an_unknown_argument_exits_2_naming_it_and_changes_nothing", not bad, "; ".join(bad))

        _cairn(home, "stop")
    finally:
        _teardown()

    live_after = (_bus_pid(ACCOUNT), _loop(ACCOUNT))
    _check("the_live_system_is_untouched", live_after == live_before,
           f"bus/loop {live_before} -> {live_after}")

    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
