"""Proof for ticket 0c2c3f53c2be, clause 4 (scratch's half): a process can tell a scratch HOME
from the account's own home, whatever its environment says.

The inspector lets its environment name its roots only under a scratch HOME (the orchestrator,
2026-11-13: "Otherwise the d2ecdb867bc9 hole just moves into the environment"). That needs a
read of the account's home that HOME and USERPROFILE cannot bend. MEASURED 2026-11-13 on
akiendell: SHGetKnownFolderPath(FOLDERID_Profile) answered C:\\Users\\akien with both set to a
fake folder; POSIX reads the password database.

  1. A child given home_env(<scratch>) answers is_scratch_home() True, and account_home() is
     the parent's account_home() — not the scratch folder.
  2. A child given the caller's own environment answers is_scratch_home() False.

    python3 cairn/tools/scratch/proofs/test_a_scratch_home_is_told_from_the_account_home.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"0c2c3f53c2be": {
    "4": "test_a_scratch_home_child_knows_it_and_still_finds_the_account_home",
    "4b": "test_a_child_on_the_account_home_is_not_scratch",
}}

_CHILD = ("import json; from cairn.tools.scratch.scratch import account_home, is_scratch_home; "
          "print(json.dumps({'scratch': is_scratch_home(), 'account': str(account_home())}))")


def _ask(env: dict) -> dict:
    done = subprocess.run([sys.executable, "-c", _CHILD], env={**env, "PYTHONPATH": str(REPO)},
                          capture_output=True, text=True, timeout=60, cwd=str(REPO))
    assert done.returncode == 0, done.stderr[-800:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_a_scratch_home_child_knows_it_and_still_finds_the_account_home():
    from cairn.tools.scratch.scratch import account_home, home_env, scratch_dir
    home = scratch_dir("scratch-home-0c2c-")
    got = _ask(home_env(home))
    assert got["scratch"] is True, got
    assert Path(got["account"]).resolve() == account_home().resolve(), (got, account_home())
    assert Path(got["account"]).resolve() != home.resolve(), got


def test_a_child_on_the_account_home_is_not_scratch():
    from cairn.tools.scratch.scratch import account_home
    env = {k: v for k, v in os.environ.items()}
    env["HOME"] = env["USERPROFILE"] = str(account_home())
    got = _ask(env)
    assert got["scratch"] is False, got


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
