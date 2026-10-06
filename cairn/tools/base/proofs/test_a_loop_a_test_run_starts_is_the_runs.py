"""A ground loop a shim starts inside a test run is the run's (ticket 2120e74dcf44; sibling of
f04d5ef26a48, which marked the launcher's two systemd-run blocks, and of c64adc092835, which made
a tester run stop the units carrying its id).

ensure_ground_loop (cairn/tools/base/shim.py) is "launchers/superclaude's systemd-run block,
spelled once here for python". f04d5ef26a48 marked the launcher's spelling; this one is the
other. systemd-run hands a unit the MANAGER's environment, so a run's CAIRN_TESTER_TEST_ID stops
at the shim's process, and a ground loop a shim starts inside a test run carries nothing the
tester's kill can find — the user manager's record is the only place c64adc092835 can look, and
the id is not in it. A loop that fails lingers as a failed unit until somebody runs reset-failed.

  1. A LOOP STARTED IN A RUN CARRIES ITS TEST ID: the user manager records the unit
     ensure_ground_loop starts as handed the CAIRN_TESTER_TEST_ID its caller was given.
  2. A LOOP STARTED IN A RUN COLLECTS ITSELF: that unit's CollectMode is inactive-or-failed, so
     a failed loop of a run is gone from the manager rather than left as a corpse.
  3. A TESTER RUN THAT STARTS A LOOP LEAVES NO UNIT: a proof run by the tester whose subject
     calls ensure_ground_loop leaves no unit behind — the id carried is what c64adc092835's
     stop finds.
  4. OUTSIDE A RUN THE LOOP IS UNCHANGED: with no test id the unit carries none and keeps the
     manager's default CollectMode (inactive), so the live loop that fails stays where a human
     looks.

ensure_ground_loop is called in a subprocess under a scratch HOME (the liveness it reads is
DEAD there, and the loop it spawns writes under the scratch, never the live instance), with the
proof's own unit name cairn-proof-loopmark-<pid>-<n> (CAIRN_GROUND_LOOP_UNIT), so the live
loop's unit is neither claimed nor stopped. Every unit is stopped and reset-failed at the end.

    python3 cairn/tools/base/proofs/test_a_loop_a_test_run_starts_is_the_runs.py
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

PROVES = {"2120e74dcf44": {
    "1": "test_a_loop_started_in_a_run_carries_its_test_id",
    "2": "test_a_loop_started_in_a_run_collects_itself",
    "3": "test_a_tester_run_that_starts_a_loop_leaves_no_unit",
    "4": "test_outside_a_run_the_loop_is_unchanged",
}}

_ENV = "CAIRN_TESTER_TEST_ID"
_TAG = str(os.getpid())
_UNITS: list[str] = []

_CALL = ("import json, sys; from datetime import datetime, timezone; sys.path.insert(0, %r); "
         "from cairn.tools.base.shim import ensure_ground_loop; "
         "print(json.dumps(ensure_ground_loop(datetime.now(timezone.utc))))")


def _unit(n: int) -> str:
    name = f"cairn-proof-loopmark-{_TAG}-{n}"
    _UNITS.append(name)
    return name


def _env(n: int, unit: str, test_id: str | None) -> dict:
    home = scratch_dir(f"cairn-proof-loopmark-home-{n}-")
    env = {k: v for k, v in os.environ.items() if k != _ENV}
    env.update({"HOME": str(home), "CAIRN_GROUND_LOOP_UNIT": unit, "PYTHONPATH": str(ROOT)})
    if test_id:
        env[_ENV] = test_id
    return env


def _start(n: int, test_id: str | None) -> str:
    unit = _unit(n)
    r = subprocess.run([sys.executable, "-c", _CALL % str(ROOT)], env=_env(n, unit, test_id),
                       capture_output=True, text=True, timeout=120, cwd=str(ROOT))
    assert r.returncode == 0 and '"spawned": "unit"' in r.stdout, (r.stdout[-400:], r.stderr[-400:])
    return unit


def _show(unit: str, prop: str) -> str:
    return subprocess.run(["systemctl", "--user", "show", "-p", prop, "--value", f"{unit}.service"],
                          capture_output=True, text=True, timeout=30).stdout.strip()


def _environ(unit: str) -> dict:
    """The manager's own record of what the unit was handed — readable through the tester's seal,
    where /proc/<pid>/environ of a unit's process is refused (measured 2026-10-05, f04d5ef26a48)."""
    return dict(kv.split("=", 1) for kv in _show(unit, "Environment").split() if "=" in kv)


def _gone(unit: str, timeout: float = 5.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if _show(unit, "LoadState") == "not-found":
            return True
        time.sleep(0.2)
    return _show(unit, "LoadState") == "not-found"


def test_a_loop_started_in_a_run_carries_its_test_id():
    test_id = f"test-loopmark{_TAG}"
    unit = _start(1, test_id)
    got = _environ(unit).get(_ENV)
    assert got == test_id, f"{unit} carries {_ENV}={got!r}, want {test_id!r}"


def test_a_loop_started_in_a_run_collects_itself():
    unit = _start(2, f"test-loopmark{_TAG}c")
    mode = _show(unit, "CollectMode")
    assert mode == "inactive-or-failed", f"{unit} CollectMode={mode!r}"


def test_a_tester_run_that_starts_a_loop_leaves_no_unit():
    unit = _unit(3)
    root = scratch_dir("cairn-proof-loopmark-run-") / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    proof = root / "proofs" / "test_fixture.py"
    home = scratch_dir("cairn-proof-loopmark-home-3-")
    proof.write_text(
        "import os, subprocess, sys\n"
        f"env = dict(os.environ, HOME={str(home)!r}, CAIRN_GROUND_LOOP_UNIT={unit!r}, PYTHONPATH={str(ROOT)!r})\n"
        f"r = subprocess.run([sys.executable, '-c', {(_CALL % str(ROOT))!r}], env=env, capture_output=True, text=True)\n"
        "assert r.returncode == 0 and '\"spawned\": \"unit\"' in r.stdout, r.stdout + r.stderr\n"
        "print('ok   test_fixture_tooth')\n")
    from cairn.devices.tester.device import TesterDevice
    rec = TesterDevice().run_proof(proof, sink="none", caller="proof-fixture-loopmark",
                                   timeout=120, isolation="none")
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert _gone(unit), f"{unit} outlived the run: {_show(unit, 'ActiveState')!r}; killed={rec['evidence'].get('killed')!r}"


def test_outside_a_run_the_loop_is_unchanged():
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
        for u in _UNITS:
            for verb in ("stop", "reset-failed"):
                subprocess.run(["systemctl", "--user", verb, f"{u}.service"], capture_output=True, timeout=30)
    print(f"\n{'GREEN' if not fails else 'RED'} — {4 - fails}/4")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
