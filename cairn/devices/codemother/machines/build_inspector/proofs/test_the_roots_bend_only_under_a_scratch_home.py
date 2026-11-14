"""Proof for ticket 0c2c3f53c2be, clause 4 (the inspector's half): the inspector's roots bend to
its environment only under a scratch HOME.

A scratch CodeMother is launched with her roots named by CAIRN_BUILD_INSPECTOR_CHART_BERTHS,
_TICKETS_ROOT and _CROSSING_ROOTS (inspect_wire.launch). The orchestrator's guard, 2026-11-13:
"a live HOME with the override env set still reads the live roots. Otherwise the d2ecdb867bc9
hole just moves into the environment." Each tooth reads the roots in a child process, because
the roots are read when the inspector is imported.

  1. Under a scratch HOME (scratch.home_env) with the three set as inspect_wire.launch names
     them, the inspector reads them.
  2. Under the account's own HOME with the same three set, it reads the live roots, and says
     so on stderr.

    python3 cairn/devices/codemother/machines/build_inspector/proofs/test_the_roots_bend_only_under_a_scratch_home.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"0c2c3f53c2be": {
    "4c": "test_a_scratch_home_bends_all_three_roots",
    "4d": "test_the_account_home_keeps_the_live_roots_with_the_env_set",
}}

_CHILD = ("import json\n"
          "from cairn.devices.codemother.machines.build_inspector import inspector as i\n"
          "r = i._crossing_roots()\n"
          "print(json.dumps({'berths': str(i._CHART_BERTHS), 'tickets': str(i._TICKETS_ROOT),\n"
          "                  'roots': None if r is None else {k: str(v) for k, v in r.items()}}))\n")


def _bent(world: Path) -> dict:
    # the environment inspect_wire.launch hands a scratch CodeMother, so the tool's root names
    # are measured bending these roots rather than compared with a list of the inspector's
    from cairn.tools.inspect_wire.inspect_wire import _launch_env
    return _launch_env(world / "berths", world / "tickets",
                       {"repo": world / "repo", "commons": world / "commons"})


def _read(env: dict) -> tuple[dict, str]:
    done = subprocess.run([sys.executable, "-c", _CHILD], env={**env, "PYTHONPATH": str(REPO)},
                          capture_output=True, text=True, timeout=300, cwd=str(REPO))
    assert done.returncode == 0, done.stderr[-1500:]
    return json.loads(done.stdout.strip().splitlines()[-1]), done.stderr


def test_a_scratch_home_bends_all_three_roots():
    from cairn.tools.scratch.scratch import home_env, scratch_dir
    world = scratch_dir("roots-bend-0c2c-")
    got, _ = _read(home_env(world, **_bent(world)))
    assert Path(got["berths"]) == world / "berths", got
    assert Path(got["tickets"]) == world / "tickets", got
    assert got["roots"] == {"repo": str(world / "repo"), "commons": str(world / "commons")}, got


def test_the_account_home_keeps_the_live_roots_with_the_env_set():
    from cairn.tools.scratch.scratch import account_home, scratch_dir
    world = scratch_dir("roots-stand-0c2c-")
    env = dict(os.environ)
    env["HOME"] = env["USERPROFILE"] = str(account_home())
    live, _ = _read(env)
    got, err = _read({**env, **_bent(world)})
    assert got == live, ("a live HOME read the environment's roots", got, live)
    assert got["roots"] is None and str(world) not in got["berths"] + got["tickets"], got
    assert "the live root stands" in err, err[-800:]


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
