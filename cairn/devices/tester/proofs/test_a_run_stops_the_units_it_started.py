"""A tester run stops the units it started (ticket c64adc092835; sibling of bf3c16162827, which made a run own what it
started; found by f04d5ef26a48's seal).

bf3c16162827's kill finds what the run started by reading /proc/<pid>/environ for the run's
CAIRN_TESTER_TEST_ID. That read is blind in two places, both measured 2026-10-05:

  - A UNIT THAT FAILED has no process left to read, and a transient systemd unit that failed
    lingers in the user manager until somebody runs reset-failed.
  - INSIDE THE SEAL the read is refused. The seal is a bwrap user namespace, and from inside it
    /proc/<pid>/environ of every process outside it — every unit the user manager started —
    reads "Permission denied" (measured: `bwrap --dev-bind / / --unshare-net head
    /proc/<systemd --user>/environ`). So a run nested inside a sealed proof (any proof that
    drives `cairn test`) cannot see the units its subject started: f04d5ef26a48's seal came
    back red with the launcher's loop unit, carrying the inner run's id, left running.

The user manager keeps its own record of what each unit was handed — `systemctl --user show -p
Environment` — and that record reads through the seal (the bus is a socket, which is a file,
and the seal keeps the filesystem). So the run asks the manager too:

  1. A UNIT THE RUN STARTED IS STOPPED: a service the subject starts with systemd-run --setenv
     of the run's id is gone from the user manager after the run, and evidence "killed" names
     it under "unit".
  2. A FAILED UNIT OF THE RUN IS CLEARED: a service carrying the run's id that exited 1 (no
     process left, so nothing for /proc to find) is gone from the user manager after the run,
     and evidence "killed" names it.
  3. A TIMED-OUT RUN LEAVES NO UNIT: the same as 1, when the subject hangs past its budget.
  4. A UNIT NOT CARRYING THE ID IS LEFT ALONE: a service started beside the run with no id, or
     with another run's id, is still running afterwards.

Every unit is named cairn-proof-unitstop-<pid>-<n> and stopped and reset-failed at the end.
Each tooth imports the tester inside its body, so a reverted file reds teeth rather than this
file's import.

    python3 cairn/devices/tester/proofs/test_a_run_stops_the_units_it_started.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"c64adc092835": {
    "1": "test_a_unit_the_run_started_is_stopped",
    "2": "test_a_failed_unit_of_the_run_is_cleared",
    "3": "test_a_timed_out_run_leaves_no_unit",
    "4": "test_a_unit_not_carrying_the_id_is_left_alone",
}}

_ENV = "CAIRN_TESTER_TEST_ID"
_TAG = str(os.getpid())
_UNITS: list[str] = []

_STARTS_A_UNIT = '''import os, subprocess, sys
unit = sys.argv[0] + ".unit"
name = open(unit).read().strip()
subprocess.run(["systemd-run", "--user", "--quiet", "--unit", name,
                "--setenv={env}=" + os.environ["{env}"], {cmd}], check=True)
print("ok   test_fixture_tooth")
{tail}'''


def _unit(n: int) -> str:
    name = f"cairn-proof-unitstop-{_TAG}-{n}"
    _UNITS.append(name)
    return name


def _proof(n: int, unit: str, cmd: str, tail: str = "") -> Path:
    root = scratch_dir(f"cairn-unitstop-{n}-") / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    proof = root / "proofs" / "test_fixture.py"
    proof.write_text(_STARTS_A_UNIT.format(env=_ENV, cmd=cmd, tail=tail))
    Path(str(proof) + ".unit").write_text(unit)
    return proof


def _run(proof: Path, timeout: int = 60) -> dict:
    from cairn.devices.tester.device import TesterDevice
    return TesterDevice().run_proof(proof, sink="none", caller="proof-fixture-unitstop",
                                    timeout=timeout, isolation="none")


def _show(unit: str, prop: str) -> str:
    return subprocess.run(["systemctl", "--user", "show", "-p", prop, "--value", f"{unit}.service"],
                          capture_output=True, text=True, timeout=30).stdout.strip()


def _gone(unit: str) -> bool:
    return _show(unit, "LoadState") == "not-found"


def _wait_gone(unit: str, timeout: float = 5.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if _gone(unit):
            return True
        time.sleep(0.2)
    return _gone(unit)


def _named(rec: dict, unit: str) -> bool:
    return any(k.get("unit") == f"{unit}.service" for k in rec["evidence"].get("killed") or [])


def test_a_unit_the_run_started_is_stopped():
    unit = _unit(1)
    rec = _run(_proof(1, unit, '"sleep", "300"'))
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert _wait_gone(unit), f"{unit} outlived the run: {_show(unit, 'ActiveState')!r}"
    assert _named(rec, unit), f"evidence does not name the unit: {rec['evidence'].get('killed')!r}"


def test_a_failed_unit_of_the_run_is_cleared():
    unit = _unit(2)
    rec = _run(_proof(2, unit, '"false"', tail="import time; time.sleep(1)\n"))
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert _wait_gone(unit), f"{unit} left behind: {_show(unit, 'ActiveState')!r}"
    assert _named(rec, unit), f"evidence does not name the unit: {rec['evidence'].get('killed')!r}"


def test_a_timed_out_run_leaves_no_unit():
    unit = _unit(3)
    rec = _run(_proof(3, unit, '"sleep", "300"', tail="import time; time.sleep(300)\n"), timeout=5)
    assert rec["verdict"] == "red" and "timed out" in str(rec["evidence"].get("stderr_tail")), rec["evidence"]
    assert _wait_gone(unit), f"{unit} outlived a timed-out run: {_show(unit, 'ActiveState')!r}"
    assert _named(rec, unit), f"evidence does not name the unit: {rec['evidence'].get('killed')!r}"


def test_a_unit_not_carrying_the_id_is_left_alone():
    bare, other, ran = _unit(4), _unit(5), _unit(6)
    subprocess.run(["systemd-run", "--user", "--quiet", "--unit", bare, "sleep", "300"], check=True)
    subprocess.run(["systemd-run", "--user", "--quiet", "--unit", other,
                    f"--setenv={_ENV}=test-000000000000", "sleep", "300"], check=True)
    rec = _run(_proof(6, ran, '"sleep", "300"'))
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    states = {u: _show(u, "ActiveState") for u in (bare, other)}
    assert all(s == "active" for s in states.values()), f"a unit the run did not start was touched: {states}"


def main() -> int:
    fails = 0
    try:
        for name, fn in list(globals().items()):
            if name.startswith("test_") and callable(fn):
                try:
                    fn()
                    print(f"  ok   {name}")
                except Exception as exc:  # noqa: BLE001
                    fails += 1
                    print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    finally:
        for u in _UNITS:
            for verb in ("stop", "reset-failed"):
                subprocess.run(["systemctl", "--user", verb, f"{u}.service"],
                               capture_output=True, timeout=30)
    print(f"\n{'GREEN' if not fails else 'RED'} — {4 - fails}/4")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
