#!/usr/bin/env python3
"""`cairn test --exec` refuses the flags it cannot honour (d181339da3c3).

WHAT THIS DEFENDS. Measured 2026-10-10: `cairn test --netns --seal --exec "<python> <proof>"`
exited 0 and persisted no VALIDATION — cli.main returned run_exec before --seal or --netns was
read, so a caller who asked for a seal was told nothing and got none. --exec runs a command
and mints no validation; a flag it cannot honour is refused by name, exit 2, before anything
runs.

THE CLAIM, clause by clause of the ticket's falsifier:
  (1) cli.main with --exec plus --seal, --netns, --hollow, --reseal or a proof path returns 2,
      names the flag, and runs nothing (the marker the command would touch is absent);
  (2) cli.main(['--exec', <touch marker>]) alone returns 0 and the command ran.

Each call runs cli.main in a child python so its exit and stderr are its own.

    bin/cairn test cairn/devices/tester/proofs/test_exec_refuses_what_it_cannot_honour.py
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

_FIXTURE = "cairn/devices/tester/proofs/fixtures/green_proof.py"

PROVES = {"d181339da3c3": {
    "1": "test_exec_refuses_each_flag_it_cannot_honour",
    "2": "test_exec_alone_still_runs",
}}

_MAIN = ("import sys\nfrom cairn.devices.tester.cli import main\n"
         "sys.exit(main(sys.argv[1:]))\n")


def _main(*argv: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONPATH=str(_REPO_ROOT))
    return subprocess.run([sys.executable, "-c", _MAIN, *argv], capture_output=True, text=True,
                          timeout=240, cwd=str(_REPO_ROOT), env=env)


def _marker(tag: str) -> Path:
    return Path(scratch_dir(f"exec_refuses_proof_fixture_{tag}_")) / "ran"


def test_exec_refuses_each_flag_it_cannot_honour():
    cases = {
        "--seal": ["--seal"],
        "--netns": ["--netns"],
        "--hollow": ["--hollow", "d181339da3c3"],
        "--reseal": ["--reseal"],
        _FIXTURE: [_FIXTURE],
    }
    wrong = []
    for name, extra in cases.items():
        m = _marker(name.strip("-").replace("/", "_")[-20:])
        r = _main(*extra, "--exec", f"touch {m}")
        if r.returncode != 2:
            wrong.append(f"{name}: exit {r.returncode}, not 2")
        elif name not in r.stderr:
            wrong.append(f"{name}: the refusal does not name it: {r.stderr[-200:]!r}")
        if m.exists():
            wrong.append(f"{name}: the command ran (marker {m} exists)")
    assert not wrong, "; ".join(wrong)


def test_exec_alone_still_runs():
    m = _marker("alone")
    r = _main("--exec", f"touch {m}")
    assert r.returncode == 0, f"--exec alone exit {r.returncode}: {r.stderr[-400:]}"
    assert m.exists(), "--exec alone returned 0 but the command did not run"


def _run() -> int:
    checks = [test_exec_refuses_each_flag_it_cannot_honour, test_exec_alone_still_runs]
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
    print("green — cairn test --exec refuses the flags it cannot honour")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
