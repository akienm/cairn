"""A bus a test run spawns is the run's (the bus twin of 2120e74dcf44, which marked
ensure_ground_loop, and of f04d5ef26a48, which marked launchers/superclaude; c64adc092835 made a
tester run stop the units carrying its id).

remote.py ``_spawn`` is "``ensure_ground_loop``'s systemd-run block, spelled again for the bus".
2120e74dcf44 marked that block; this spelling was left unmarked. systemd-run hands a unit the
MANAGER's environment, so a run's CAIRN_TESTER_TEST_ID stops at the caller's process, and a bus
a test run causes carries nothing the tester's stop can find. One that fails lingers as a failed
unit. Measured 2026-10-11: eight cairn-bus-<hash> corpses left loaded/failed by
launchers/proofs/test_a_unit_a_test_run_starts_is_the_runs.py tooth 2.

  1. A BUS STARTED IN A RUN CARRIES ITS TEST ID: the user manager records the unit
     ``ensure_bus`` starts as handed the CAIRN_TESTER_TEST_ID its caller was given.
  2. A BUS STARTED IN A RUN COLLECTS ITSELF: that unit's CollectMode is inactive-or-failed, so a
     failed bus of a run is gone from the manager rather than left as a corpse.
  3. A TESTER RUN THAT STARTS A BUS LEAVES NO UNIT: a proof run by the tester whose subject
     calls ``ensure_bus`` leaves no unit behind — the id carried is what c64adc092835's stop
     finds.
  4. OUTSIDE A RUN THE BUS IS UNCHANGED: with no test id the unit carries none and keeps the
     manager's default CollectMode (inactive).

``ensure_bus`` is called in a subprocess under a scratch HOME, at a scratch bus home (so the bus
rides a throwaway table, never the live instance), with the proof's own unit name
cairn-proof-busmark-<pid>-<n> (CAIRN_BUS_UNIT), so the live bus's unit is neither claimed nor
stopped. Every unit is stopped and reset-failed at the end.

    python3 cairn/tools/bus_client/proofs/test_a_bus_a_test_run_spawns_is_the_runs.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402

PROVES = {"6c9db321d638": {
    "1": "test_a_bus_started_in_a_run_carries_its_test_id",
    "2": "test_a_bus_started_in_a_run_collects_itself",
    "3": "test_a_tester_run_that_starts_a_bus_leaves_no_unit",
    "4": "test_outside_a_run_the_bus_is_unchanged",
}}

_ENV = "CAIRN_TESTER_TEST_ID"
_TAG = str(os.getpid())
_UNITS: list[str] = []

_CALL = ("import json, sys; sys.path.insert(0, %r); "
         "from cairn.tools.bus_client.remote import ensure_bus; "
         "print(json.dumps(ensure_bus(sys.argv[1])))")


def _unit(n: int) -> str:
    name = f"cairn-proof-busmark-{_TAG}-{n}"
    _UNITS.append(name)
    return name


def _caller(unit: str, home: Path, test_id: str | None) -> list[str]:
    """argv that calls ``ensure_bus`` from inside a unit of its own — beside the user manager,
    where a run's units live (f04d5ef26a48 marks them with the run's id). Inside the tester's
    seal ``ensure_bus`` is not beside the manager and spawns with setsid, so the unit path this
    proof is about is reached only from a unit (measured 2026-10-18: 0 units started from the
    seal)."""
    argv = ["systemd-run", "--user", "--wait", "--pipe", "--quiet",
            "--unit", f"{unit}-caller", "-p", "CollectMode=inactive-or-failed",
            "--working-directory", str(ROOT),
            f"--setenv=HOME={home}", f"--setenv=CAIRN_BUS_UNIT={unit}",
            f"--setenv=PYTHONPATH={ROOT}", f"--setenv=PATH={os.environ.get('PATH', '')}"]
    if test_id:
        argv.append(f"--setenv={_ENV}={test_id}")
    return argv + ["--", sys.executable, "-c", _CALL % str(ROOT), str(home / "bus")]


def _start(n: int, test_id: str | None) -> str:
    unit = _unit(n)
    home = scratch_dir(f"cairn-proof-busmark-{n}-")
    r = subprocess.run(_caller(unit, home, test_id), capture_output=True, text=True,
                       timeout=120, cwd=str(ROOT))
    assert r.returncode == 0, (r.stdout[-400:], r.stderr[-400:])
    assert _show(unit, "LoadState") == "loaded", f"ensure_bus answered but no {unit}.service was started"
    return unit


def _show(unit: str, prop: str) -> str:
    return subprocess.run(["systemctl", "--user", "show", "-p", prop, "--value", f"{unit}.service"],
                          capture_output=True, text=True, timeout=30).stdout.strip()


def _environ(unit: str) -> dict:
    """The manager's own record of what the unit was handed — readable through the tester's seal
    (measured 2026-10-05, f04d5ef26a48)."""
    return dict(kv.split("=", 1) for kv in _show(unit, "Environment").split() if "=" in kv)


def _gone(unit: str, timeout: float = 5.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if _show(unit, "LoadState") == "not-found":
            return True
        time.sleep(0.2)
    return _show(unit, "LoadState") == "not-found"


def test_a_bus_started_in_a_run_carries_its_test_id():
    test_id = f"test-busmark{_TAG}"
    unit = _start(1, test_id)
    got = _environ(unit).get(_ENV)
    assert got == test_id, f"{unit} carries {_ENV}={got!r}, want {test_id!r}"


def test_a_bus_started_in_a_run_collects_itself():
    unit = _start(2, f"test-busmark{_TAG}c")
    mode = _show(unit, "CollectMode")
    assert mode == "inactive-or-failed", f"{unit} CollectMode={mode!r}"


def test_a_tester_run_that_starts_a_bus_leaves_no_unit():
    unit = _unit(3)
    root = scratch_dir("cairn-proof-busmark-run-") / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    proof = root / "proofs" / "test_fixture.py"
    home = scratch_dir("cairn-proof-busmark-3-")
    # The fixture calls ensure_bus from a unit carrying the run's own id, as a marked unit of the
    # run does (f04d5ef26a48); the bus that unit spawns is what the run must take with it.
    proof.write_text(
        "import os, subprocess, sys\n"
        f"sys.path.insert(0, {str(Path(__file__).parent)!r})\n"
        "from test_a_bus_a_test_run_spawns_is_the_runs import _caller, _show\n"
        "from pathlib import Path\n"
        f"r = subprocess.run(_caller({unit!r}, Path({str(home)!r}), os.environ[{_ENV!r}]),"
        " capture_output=True, text=True)\n"
        "assert r.returncode == 0, r.stdout + r.stderr\n"
        f"assert _show({unit!r}, 'LoadState') == 'loaded', 'no bus unit was started'\n"
        "print('ok   test_fixture_tooth')\n")
    # The tester is reached only through its interface, bin/cairn test (45c168cc1ff1).
    r = subprocess.run([*bash_script_argv(ROOT / "bin" / "cairn"), "test", str(proof)],
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0 and f"  green  {proof}" in r.stdout.splitlines(), r.stdout + r.stderr
    assert _gone(unit), f"{unit} outlived the run: {_show(unit, 'ActiveState')!r}"


def test_outside_a_run_the_bus_is_unchanged():
    unit = _start(4, None)
    env, mode = _environ(unit), _show(unit, "CollectMode")
    assert _ENV not in env and mode == "inactive", f"{unit} carries id={_ENV in env}, CollectMode={mode!r}"


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
        for u in _UNITS + [f"{u}-caller" for u in _UNITS]:
            for verb in ("stop", "reset-failed"):
                subprocess.run(["systemctl", "--user", verb, f"{u}.service"], capture_output=True, timeout=30)
    print(f"\n{'GREEN' if not fails else 'RED'} — {4 - fails}/4")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
