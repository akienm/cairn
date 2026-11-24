#!/usr/bin/env python3
"""Proof for ticket 7bb0d4894a62: a unit a test run asks service_spawn for is collected when it
fails; a unit started outside a run keeps the manager's default and stays where a human looks.

Measured 2026-11-23: the shell superclaude passed `-p CollectMode=inactive-or-failed` under
CAIRN_TESTER_TEST_ID (commit ef541167c, lines 623-624 of the shell launcher). service_spawn does not, and
`systemctl --user set-property` refuses CollectMode after start, so once superclaude.py launched
through service_spawn a failed test unit stayed loaded and failed.

  1. with CAIRN_TESTER_TEST_ID in the env passed to service_spawn, a unit whose process exits
     non-zero is gone (LoadState not-found) within 10s;
  2. with no CAIRN_TESTER_TEST_ID in that env, the same failing unit stays loaded with
     ActiveState failed.

Off a box with systemd --user both teeth print UNMEASURED: a state, never a green. The tool is
imported inside each tooth, so an absent or hollow build reds the tooth, not the run.

    bin/cairn test cairn/devices/system_rackmount/tools/launch/proofs/test_a_test_run_unit_is_collected_when_it_fails.py
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
TEST_ID_ENV = "CAIRN_TESTER_TEST_ID"
_FAIL = [sys.executable, "-c", "import sys; sys.exit(3)"]

PROVES = {"7bb0d4894a62": {
    "1": "test_a_test_run_unit_is_collected_when_it_fails",
    "2": "test_a_unit_outside_a_run_stays_failed",
}}


class Unmeasured(Exception):
    """The tooth cannot run here; that is a state, never a green."""


def _need_user_systemd() -> None:
    if os.name == "nt" or not shutil.which("systemd-run"):
        raise Unmeasured("no systemd-run on this box")
    got = subprocess.run(["systemctl", "--user", "is-system-running"], capture_output=True,
                         text=True, timeout=30)
    if not got.stdout.strip():
        raise Unmeasured("no systemd --user manager answers here")


def _show(unit: str) -> tuple[str, str]:
    got = subprocess.run(["systemctl", "--user", "show", "-p", "LoadState", "-p", "ActiveState",
                          f"{unit}.service"], capture_output=True, text=True, timeout=30)
    kv = dict(line.split("=", 1) for line in got.stdout.splitlines() if "=" in line)
    return kv.get("LoadState", ""), kv.get("ActiveState", "")


def _clear(unit: str) -> None:
    for verb in ("stop", "reset-failed"):
        subprocess.run(["systemctl", "--user", verb, f"{unit}.service"], capture_output=True, timeout=30)


def _spawn_failing(n: int, env: dict) -> tuple[str, dict]:
    launch = importlib.import_module(_MODULE)
    unit = f"cairn-proof-collect-{os.getpid()}-{n}"
    with tempfile.TemporaryDirectory(prefix="cairn-proof-collect-") as d:
        got = launch.service_spawn(unit, _FAIL, Path(d) / "unit.log", cwd=d, env=env)
    return unit, got


def _settled(unit: str, want, timeout: float = 10.0) -> tuple[bool, tuple[str, str]]:
    end = time.time() + timeout
    state = _show(unit)
    while time.time() < end:
        state = _show(unit)
        if want(state):
            return True, state
        time.sleep(0.25)
    return False, state


def test_a_test_run_unit_is_collected_when_it_fails() -> tuple[bool, str]:
    _need_user_systemd()
    # The outer run's id when there is one, so the run's own kill reaches the unit too.
    tid = os.environ.get(TEST_ID_ENV) or f"test-collect{os.getpid()}"
    unit, got = _spawn_failing(1, {TEST_ID_ENV: tid})
    try:
        ok, state = _settled(unit, lambda s: s[0] == "not-found")
        return (got.get("ok") is True and got.get("how") == "systemd" and ok,
                f"spawn={got} state after 10s={state}")
    finally:
        _clear(unit)


def test_a_unit_outside_a_run_stays_failed() -> tuple[bool, str]:
    _need_user_systemd()
    unit, got = _spawn_failing(2, {})
    try:
        ok, state = _settled(unit, lambda s: s == ("loaded", "failed"))
        if ok:   # it must still be there a moment later, not merely on its way out
            time.sleep(2)
            state = _show(unit)
            ok = state == ("loaded", "failed")
        return (got.get("ok") is True and got.get("how") == "systemd" and ok,
                f"spawn={got} state={state}")
    finally:
        _clear(unit)


def main() -> int:
    reds = 0
    for name, fn in [(k, v) for k, v in globals().items() if k.startswith("test_") and callable(v)]:
        try:
            ok, detail = fn()
        except Unmeasured as e:
            print(f"  UNMEASURED  {name}  — {e}")
            continue
        except Exception as e:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            ok, detail = False, f"raised {type(e).__name__}: {e}"
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail}"))
        reds += not ok
    print("\nGREEN" if not reds else f"\nRED — {reds} failure(s)")
    return 1 if reds else 0


if __name__ == "__main__":
    raise SystemExit(main())
