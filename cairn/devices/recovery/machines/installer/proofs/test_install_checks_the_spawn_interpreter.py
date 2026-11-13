"""Proof: an install check measures that the spawn interpreter shares its caller's prefix (ticket 404f193284ac).

background_python() once returned the base interpreter, a child died at `import psycopg2`, and
nothing on the box said so before it ran. check_spawn_interpreter asks the spawn interpreter for its
sys.prefix and compares it with the caller's. One tooth per falsifier clause; the OS is a recording
stub (`run`), so nothing is spawned:

  1. a spawn interpreter reporting a different prefix makes the check return offered (a dry run), naming
     both prefixes, a failed result when not a dry run, and the check is registered in CHECKS.
  2. a spawn interpreter reporting the caller's own prefix returns already_applied.

    python3 cairn/devices/recovery/machines/installer/proofs/test_install_checks_the_spawn_interpreter.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT))
assert (ROOT / "bin" / "cairn").exists(), f"ROOT {ROOT} does not hold bin/cairn"

PROVES = {"404f193284ac": {
    "1": "tooth_a_different_prefix_is_offered_naming_both",
    "2": "tooth_the_callers_own_prefix_is_already_applied",
}}

CALLER = "C:/venvs/caller"
OTHER = "C:/base/python3"
STUB_PY = "stub-python.exe"


def _runner(stdout: str, returncode: int = 0, stderr: str = ""):
    seen = []

    def run(argv, **kw):
        seen.append((list(argv), kw))
        return subprocess.CompletedProcess(argv, returncode, stdout, stderr)

    run.seen = seen
    return run


def _check():
    from cairn.devices.recovery.machines.installer import installer
    return installer.check_spawn_interpreter


def tooth_a_different_prefix_is_offered_naming_both():
    run = _runner(OTHER + "\r\n")
    dry = _check()(dry_run=True, run=run, python=STUB_PY, caller_prefix=CALLER)
    assert dry["status"] == "offered", dry
    assert OTHER in dry["detail"] and CALLER in dry["detail"] and STUB_PY in dry["detail"], dry
    argv = run.seen[0][0]
    assert argv[0] == STUB_PY and "sys.prefix" in " ".join(argv), argv  # it asked the spawn interpreter
    live = _check()(dry_run=False, run=_runner(OTHER), python=STUB_PY, caller_prefix=CALLER)
    assert live["status"] == "failed" and OTHER in live["detail"], live  # nothing here applies a fix
    broken = _check()(dry_run=True, run=_runner("", 1, "no module"), python=STUB_PY, caller_prefix=CALLER)
    assert broken["status"] == "failed" and "no module" in broken["detail"], broken
    from cairn.devices.recovery.machines.install_inspector.inspector import CHECKS
    assert any(str(c).endswith(":check_spawn_interpreter") for c in CHECKS), CHECKS


def tooth_the_callers_own_prefix_is_already_applied():
    res = _check()(dry_run=True, run=_runner(CALLER + "\n"), python=STUB_PY, caller_prefix=CALLER)
    assert res["status"] == "already_applied" and res["id"] == "spawn_interpreter", res


TEETH = [tooth_a_different_prefix_is_offered_naming_both, tooth_the_callers_own_prefix_is_already_applied]


def test_install_checks_the_spawn_interpreter():
    reds = []
    for t in TEETH:
        try:
            t()
            print(f"  GREEN  {t.__name__}")
        except Exception as e:  # every tooth prints; none stops the rest
            reds.append(t.__name__)
            print(f"  RED    {t.__name__}")
            print(f"         {type(e).__name__}: {e}")
    assert not reds, f"red teeth: {reds}"


if __name__ == "__main__":
    try:
        test_install_checks_the_spawn_interpreter()
    except AssertionError as e:
        print(e)
        sys.exit(1)
