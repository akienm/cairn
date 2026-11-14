#!/usr/bin/env python3
"""`cairn test --exec '<command>'` runs the command where the caller stood.

WHAT THIS DEFENDS (ticket 5bc3a4b1ab27, child of 68cef2ddd8ef). The sealed exec is the one door
codemother's verdict and CC's tool calls are rewritten onto, as a drop-in for bare ``bash -c``.
bin/cmd/test runs ``cd "$REPO"`` before it hands off, so run_exec's ``os.getcwd()`` default only
ever saw the repo root: measured 2026-10-07, ``bin/cairn test --exec pwd`` from a mktemp dir
printed /home/akien/dev/src/cairn, and the verdict's ``bash proofs/exits.sh 7`` instruments
exited 127. The launcher now carries $PWD across its cd as CAIRN_TESTER_CALLER_CWD.

THE CLAIM, clause by clause of the ticket's falsifier:
  (1) --exec run from another directory runs the command there;
  (2) an explicit cwd= handed to run_exec still wins over the carried directory;
  (3) a proof-path run from another directory still resolves its target repo-relative.

Proof: exit 0 = green.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROOF_TIMEOUT_S = 300

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))
from cairn.tools.scratch.scratch import scratch_dir
from cairn.tools.base.script_argv import cairn_test_argv

_CARRIED = "CAIRN_TESTER_CALLER_CWD"
_FIXTURE = "cairn/devices/tester/proofs/fixtures/green_proof.py"

PROVES = {"5bc3a4b1ab27": {
    "1": "test_exec_from_another_dir_runs_there",
    "2": "test_an_explicit_cwd_still_wins",
    "3": "test_a_proof_path_run_still_resolves_from_the_repo",
}}


# WHERE AM I, asked bash-free on Windows (ticket 21acc004c1fa). ``pwd`` there is an MSYS program
# and answers in its own /tmp spelling. This python answers in the caller's own spelling, and runs
# prevent-kind at Low. POSIX keeps ``pwd``.
_PWD = (f'"{sys.executable}" -c "import os; print(os.path.realpath(os.getcwd()))"'
        if os.name == "nt" else "pwd")


def _cairn_test(*args: str, cwd: str) -> subprocess.CompletedProcess:
    argv, env, run_cwd = cairn_test_argv(*args, cwd=cwd)
    return subprocess.run(argv, env=env, cwd=run_cwd, capture_output=True, text=True, timeout=240)


def _elsewhere(tag: str) -> str:
    return os.path.realpath(scratch_dir(f"exec_cwd_proof_fixture_{tag}_"))


def test_exec_from_another_dir_runs_there():
    here = _elsewhere("caller")
    r = _cairn_test("--exec", _PWD, cwd=here)
    assert r.returncode == 0, f"--exec exit {r.returncode}: {r.stderr[-400:]}"
    assert r.stdout.strip() == here, (
        f"--exec ran at {r.stdout.strip()!r}, not where the caller stood ({here!r})")


def test_an_explicit_cwd_still_wins():
    carried, explicit = _elsewhere("carried"), _elsewhere("explicit")
    code = ("import sys\nfrom cairn.devices.tester.device import TesterDevice\n"
            "sys.exit(TesterDevice().run_exec(sys.argv[2], timeout=120, cwd=sys.argv[1]))\n")
    env = dict(os.environ, PYTHONPATH=str(_REPO_ROOT), **{_CARRIED: carried})
    r = subprocess.run([sys.executable, "-c", code, explicit, _PWD], capture_output=True, text=True,
                       timeout=240, cwd=carried, env=env)
    assert r.returncode == 0, f"run_exec exit {r.returncode}: {r.stderr[-400:]}"
    assert r.stdout.strip() == explicit, (
        f"run_exec ran at {r.stdout.strip()!r}; the explicit cwd {explicit!r} must win")


def test_a_proof_path_run_still_resolves_from_the_repo():
    r = _cairn_test(_FIXTURE, cwd=_elsewhere("proofpath"))
    out = r.stdout + r.stderr
    assert "found no proofs" not in out, f"a repo-relative proof path stopped resolving: {out[-400:]}"
    assert r.returncode == 0 and "1 green" in out, (
        f"the fixture proof did not run green from elsewhere (exit {r.returncode}): {out[-400:]}")


def _main() -> int:
    checks = [
        test_exec_from_another_dir_runs_there,
        test_an_explicit_cwd_still_wins,
        test_a_proof_path_run_still_resolves_from_the_repo,
    ]
    # EVERY TOOTH PRINTS, red ones too, so a red names which clause fell.
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as e:  # noqa: BLE001 — a crash in a tooth is that tooth's red
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {type(e).__name__}: {e}")
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed")
        return 1
    print("green — cairn test --exec runs the command where the caller stood")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
