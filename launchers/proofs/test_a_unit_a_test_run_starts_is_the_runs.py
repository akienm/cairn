"""A unit the launcher starts inside a test run is the run's (ticket f04d5ef26a48; sibling of
bf3c16162827, which made a tester run own what it started).

Akien, 2026-10-05 (/home/akien/.cairn/foreground-decisions.md 8g): the cairn-proof-web-* unit
leak — "i don't care which way we deal with it. as long as it gets fixed". Measured 2026-10-06
01:35Z: a run of test_ground_loop_survives_its_caller.py left cairn-proof-loop-1637418-2.service
running and cairn-proof-web-1637418-{1,2,3}.service failed in the live user manager. Measured
again 2026-10-05 by killing that proof at a 25s tester timeout: cairn-proof-loop-<n>-1.service
was left running.

The cause is the launcher's two systemd-run blocks: systemd-run hands a unit the MANAGER's
environment, so the run's CAIRN_TESTER_TEST_ID stops at the launcher's shell, and the tester's
kill (which finds what carries the id) cannot reach the units the run caused. A unit that FAILED
has no process left to kill at all, and a transient unit that failed lingers until somebody runs
reset-failed — which the proof's own cleanup does, unless the proof was killed first.

  1. A UNIT THE LAUNCHER STARTS IN A RUN CARRIES ITS TEST ID: the user manager records the
     ground-loop unit as handed the CAIRN_TESTER_TEST_ID the launcher was given.
  2. A FAILED UNIT OF A RUN COLLECTS ITSELF: the ground-loop unit killed with SIGKILL, and the web
     unit failing to bind its port, are both gone from the user manager afterwards — not left
     behind as failed corpses.
  3. A RUN KILLED BY ITS TIMEOUT LEAVES NO UNIT: `cairn test --timeout 25` over the launcher
     proof that drives the real launcher leaves no cairn-proof-* unit that it created. Under
     the seal the inner run's kill can reach the unit only through the user manager, which is
     ticket c64adc092835's half; this tooth measures the two together.
  4. OUTSIDE A RUN THE UNITS ARE UNCHANGED: with no test id, the ground-loop unit carries none
     and keeps the manager's default CollectMode, so a live unit that fails stays where a human
     looks.
  5. A KILLED RUN LEAVES NO UNIT OF ITS OWN (ticket d50d162c5428): teeth 1 and 2 hand the
     launcher the OUTER run's CAIRN_TESTER_TEST_ID when one is set, so the run's kill reaches
     every unit the proof starts. Measured 2026-10-10: with the proof's own inner id
     (test-unitmark<pid>), cairn-proof-unitmark-loop-3805307-1 ran a second live ground loop for
     days after its run died before the finally. This tooth runs `cairn test` over this file
     with CAIRN_LAUNCHERS_UNITMARK_HOLD set — tooth 1 then holds its unit until the inner run's
     timeout kills it — and asserts the unit it saw start is gone afterwards.

Every unit this proof creates is named cairn-proof-unitmark-<pid>-<n> and stopped and
reset-failed at the end. The web unit is reached by a PATH shim whose `ss` reports port 80 free
(the live web server holds it), so the launcher starts the unit and its listener fails to bind:
exactly the failure that left the measured corpses.

    python3 launchers/proofs/test_a_unit_a_test_run_starts_is_the_runs.py
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

SUPERCLAUDE = REPO / "launchers" / "superclaude"
TEST_ID_ENV = "CAIRN_TESTER_TEST_ID"
HOLD_ENV = "CAIRN_LAUNCHERS_UNITMARK_HOLD"

PROVES = {"f04d5ef26a48": {
    "1": "test_a_unit_the_launcher_starts_in_a_run_carries_its_test_id",
    "2": "test_a_failed_unit_of_a_run_collects_itself",
    "3": "test_a_run_killed_by_its_timeout_leaves_no_unit",
    "4": "test_outside_a_run_the_units_are_unchanged",
}, "d50d162c5428": {
    "all": "test_a_killed_run_leaves_no_unit_of_its_own",
}}
_TAG = f"{os.getpid()}"
_SCRATCH = scratch_dir("cairn-proof-unitmark-")
_UNITS: list[str] = []
FAILED: list[str] = []

_STAND_IN = """#!/usr/bin/env bash
echo "STAND_IN_REACHED"
sleep 60
"""


def ok(name: str, good: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if good else 'FAIL'} {name}" + (f"  — {detail}" if detail else ""))
    if not good:
        FAILED.append(name)


def _run(*argv: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(list(argv), capture_output=True, text=True, timeout=timeout)


def _unit(kind: str, n: int) -> str:
    name = f"cairn-proof-unitmark-{kind}-{_TAG}-{n}"
    _UNITS.append(name)
    return name


def _show(unit: str, prop: str) -> str:
    return _run("systemctl", "--user", "show", "-p", prop, "--value", f"{unit}.service").stdout.strip()


def _environ(unit: str) -> dict:
    """What the user manager handed the unit, read from the manager's own record. Never
    /proc/<pid>/environ: inside the tester's seal (a bwrap user namespace) that read is refused
    for every process outside it, and a unit's process is always outside it (measured
    2026-10-05: this tooth read None under the seal and the right id bare)."""
    raw = _show(unit, "Environment")
    return dict(kv.split("=", 1) for kv in raw.split() if "=" in kv)


def _ss_shim() -> str:
    """A PATH whose first entry holds an `ss` that reports nothing listening."""
    d = _SCRATCH / "ss-reports-port-80-free"
    d.mkdir(exist_ok=True)
    ss = d / "ss"
    ss.write_text("#!/bin/sh\nexit 0\n")
    ss.chmod(0o755)
    return f"{d}:{os.environ.get('PATH', '')}"


def _drive(n: int, *, test_id: str | None, web: bool = False) -> tuple[subprocess.Popen, str, str, Path]:
    home = _SCRATCH / f"home-{n}"
    (home / ".cairn" / "logs").mkdir(parents=True, exist_ok=True)
    stand_in = _SCRATCH / f"claude-stand-in-{n}"
    stand_in.write_text(_STAND_IN)
    stand_in.chmod(0o755)
    loop, webu, scope = _unit("loop", n), _unit("web", n), _unit("caller", n)
    env = {k: v for k, v in os.environ.items() if k != TEST_ID_ENV}
    if test_id:
        env[TEST_ID_ENV] = test_id
    env.update({"HOME": str(home), "CLAUDE_BIN": str(stand_in), "SUPERCLAUDE_NO_SCOPE": "1",
                "CAIRN_BOOT_LOG": str(home / ".cairn" / "logs" / "boot"),
                "SUPERCLAUDE_GROUND_LOOP_UNIT": loop, "SUPERCLAUDE_WEB_UNIT": webu})
    env["CAIRN_LOGTARGET"] = env["CAIRN_BOOT_LOG"]
    if web:
        env["PATH"] = _ss_shim()
    out = _SCRATCH / f"drive-{n}.out"
    proc = subprocess.Popen(
        ["systemd-run", "--user", "--scope", "--quiet", "--unit", scope,
         "--", "script", "-qec", f"{SUPERCLAUDE} --no-preflight", "/dev/null"],
        stdout=out.open("w"), stderr=subprocess.STDOUT, env=env, cwd=str(REPO),
        start_new_session=True)
    return proc, loop, webu, out


def _wait(pred, timeout: float = 45.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.3)
    return False


def _main_pid(unit: str) -> str:
    pid = _show(unit, "MainPID")
    return pid if pid and pid != "0" else ""


def _gone(unit: str) -> bool:
    return _show(unit, "LoadState") == "not-found" or (
        _show(unit, "ActiveState") == "inactive" and _show(unit, "LoadState") != "loaded")


def _stop_caller(proc: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except OSError:
        pass


def _run_id(fallback: str) -> str:
    """The OUTER run's id when this proof runs inside one, so the run's kill reaches every unit
    the proof starts (d50d162c5428); the proof's own id only when it runs bare."""
    return os.environ.get(TEST_ID_ENV) or fallback


def test_a_unit_the_launcher_starts_in_a_run_carries_its_test_id() -> tuple[str, str]:
    test_id = _run_id(f"test-unitmark{_TAG}")
    proc, loop, _web, _out = _drive(1, test_id=test_id)
    started = _wait(lambda: bool(_main_pid(loop)))
    env = _environ(loop) if started else {}
    ok("test_a_unit_the_launcher_starts_in_a_run_carries_its_test_id",
       env.get(TEST_ID_ENV) == test_id,
       f"loop unit started={started}, its {TEST_ID_ENV}={env.get(TEST_ID_ENV)!r}, want {test_id!r}")
    if os.environ.get(HOLD_ENV):
        print(f"  HELD {loop}", flush=True)
        time.sleep(600)   # tooth 5's inner run: its timeout kills this process, not the finally
    _stop_caller(proc)
    return loop, test_id


def test_a_failed_unit_of_a_run_collects_itself(loop: str) -> None:
    pid = _main_pid(loop)
    if pid:
        _run("systemctl", "--user", "kill", "-s", "KILL", f"{loop}.service")
    loop_gone = _wait(lambda: _gone(loop), timeout=10)
    proc, _loop2, web, out = _drive(2, test_id=_run_id(f"test-unitmark{_TAG}w"), web=True)
    web_tried = _wait(lambda: _show(web, "LoadState") == "loaded" or "web_server" in
                      (out.read_text(errors="replace") if out.exists() else ""), timeout=45)
    # The listener reaches its bus before it binds, and under a scratch HOME that bus never
    # answers, so the failed bind lands after the bus's 15s wait (measured 2026-10-11, d50d162c5428).
    _wait(lambda: _gone(web), timeout=40)
    web_state = (_show(web, "LoadState"), _show(web, "ActiveState"))
    _stop_caller(proc)
    ok("test_a_failed_unit_of_a_run_collects_itself",
       pid != "" and loop_gone and web_tried and _gone(web),
       f"loop killed (pid {pid or 'none'}) gone={loop_gone} state={_show(loop, 'ActiveState')!r}; "
       f"web launched={web_tried} state={web_state}")


def test_a_run_killed_by_its_timeout_leaves_no_unit() -> None:
    def proof_units() -> set[str]:
        r = _run("systemctl", "--user", "list-units", "--all", "--no-legend", "--plain",
                 "cairn-proof-*")
        return {line.split()[0] for line in r.stdout.splitlines() if line.strip()}
    before = proof_units()
    run = _run(str(REPO / "bin" / "cairn"), "test", "--timeout", "25",
               "launchers/proofs/test_ground_loop_survives_its_caller.py", timeout=180)
    time.sleep(4)
    left = sorted(u for u in proof_units() - before if "unitmark" not in u)
    ok("test_a_run_killed_by_its_timeout_leaves_no_unit",
       "  TIMEOUT " in run.stdout + run.stderr and not left,   # the column since 3dfceaa272ec
       f"the inner run timed out={'  TIMEOUT ' in run.stdout + run.stderr}; units it left: {left}")
    for u in left:   # never leave the live manager holding what this tooth measured
        _run("systemctl", "--user", "stop", u, timeout=30)
        _run("systemctl", "--user", "reset-failed", u, timeout=30)


def test_a_killed_run_leaves_no_unit_of_its_own() -> None:
    def inner_loops() -> set[str]:
        r = _run("systemctl", "--user", "list-units", "--all", "--no-legend", "--plain",
                 "cairn-proof-unitmark-loop-*")
        return {line.split()[0].removesuffix(".service") for line in r.stdout.splitlines()
                if line.strip() and f"-{_TAG}-" not in line.split()[0]}
    before = inner_loops()
    env = {k: v for k, v in os.environ.items() if k != TEST_ID_ENV}
    env[HOLD_ENV] = "1"
    inner = subprocess.Popen([str(REPO / "bin" / "cairn"), "test", "--timeout", "40",
                              str(Path(__file__).resolve())],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             env=env, cwd=str(REPO))
    seen: set[str] = set()
    while inner.poll() is None:
        seen |= inner_loops() - before
        time.sleep(0.5)
    said = inner.stdout.read() if inner.stdout else ""
    time.sleep(4)
    left = sorted(u for u in seen if not _gone(u))
    ok("test_a_killed_run_leaves_no_unit_of_its_own",
       "  TIMEOUT " in said and bool(seen) and not left,   # the column since 3dfceaa272ec
       f"the inner run timed out={'  TIMEOUT ' in said}; units it started={sorted(seen)}; "
       f"left after its kill={left}")
    for u in sorted(seen):   # never leave the live manager holding what this tooth measured
        _UNITS.extend([u, u.replace("-loop-", "-caller-", 1)])


# Tooth 4 hands no id by design: only this file's finally reaches its unit.
def test_outside_a_run_the_units_are_unchanged() -> None:
    proc, loop, _web, _out = _drive(3, test_id=None)
    started = _wait(lambda: bool(_main_pid(loop)))
    env = _environ(loop) if started else {}
    collect = _show(loop, "CollectMode")
    _stop_caller(proc)
    ok("test_outside_a_run_the_units_are_unchanged",
       started and TEST_ID_ENV not in env and collect == "inactive",
       f"loop unit started={started}, carries id={TEST_ID_ENV in env}, CollectMode={collect!r}")


def _clear_scratch_buses() -> None:
    """Tooth 2's web unit spawns a bus homed under this proof's scratch, and bus_client does not
    mark it as the run's (trouble a-bus-a-test-run-spawns-is-not-the-runs), so it fails and
    lingers. Never leave the live manager holding what this proof caused."""
    r = _run("systemctl", "--user", "list-units", "--all", "--no-legend", "--plain", "cairn-bus-*")
    for line in r.stdout.splitlines():
        unit = line.split()[0] if line.strip() else ""
        if unit and str(_SCRATCH) in _run("systemctl", "--user", "show", "-p", "ExecStart",
                                          "--value", unit).stdout:
            for verb in ("stop", "reset-failed"):
                _run("systemctl", "--user", verb, unit, timeout=30)


def main() -> int:
    try:
        loop, _ = test_a_unit_the_launcher_starts_in_a_run_carries_its_test_id()
        if os.environ.get(HOLD_ENV):
            return 0   # unreachable while held; a hold that returns has nothing more to run
        test_a_failed_unit_of_a_run_collects_itself(loop)
        test_a_run_killed_by_its_timeout_leaves_no_unit()
        test_outside_a_run_the_units_are_unchanged()
        test_a_killed_run_leaves_no_unit_of_its_own()
    finally:
        for u in _UNITS:
            for verb in ("stop", "reset-failed"):
                suffix = ".scope" if "-caller-" in u else ".service"
                try:
                    _run("systemctl", "--user", verb, u + suffix, timeout=30)
                except subprocess.TimeoutExpired:
                    print(f"  cleanup: systemctl {verb} {u}{suffix} timed out")
        _clear_scratch_buses()
    print(f"\n{'GREEN' if not FAILED else 'RED'} — {5 - len(FAILED)}/5")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
