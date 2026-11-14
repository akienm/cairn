"""Proof for ticket a29cf5216236: cairn/tools/base publishes cairn_test_argv, a bash-free
``cairn test`` entry on Windows.

Measured 2026-11-14 on akienyoga9i (ticket 56b61c10bdbe, ruling C): MSYS bash cannot start at Low
integrity. msys-2.0.dll's NtCreateDirectoryObject gets 0xC0000022 and the process exits 0xC0000142,
so a proof that runs ``bash bin/cairn test`` cannot run under a prevent-kind seal. ``bin/cmd/test``
holds no logic of its own (carry the caller's cwd, cd to the repo, exec the tester's CLI), so a
python entry does the same thing without bash.

1. clause_1_windows_names_no_bash_and_carries_the_callers_cwd: the Windows shape is
   ``python -m cairn.devices.tester.cli *args`` from the repo, with no bash anywhere in the argv,
   CAIRN_TESTER_CALLER_CWD set to the caller's cwd, and PYTHONUTF8=1. On a Windows host it runs
   for real (``--help``) and reaches the tester's CLI;
2. clause_2_posix_is_bin_cairn_test_unchanged: the POSIX shape is ``bin/cairn test *args``, with
   the args verbatim, run where the caller stands. On a POSIX host it runs for real.

Hollow: remove cairn_test_argv, and both clauses red on the import.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_cairn_test_argv_names_no_bash_on_windows.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "a29cf5216236": {
        "1": "clause_1_windows_names_no_bash_and_carries_the_callers_cwd",
        "2": "clause_2_posix_is_bin_cairn_test_unchanged",
    },
}

ARGS = ("some proof.py", "--timeout", "30")   # a space and a flag: both must ride verbatim


def _names_bash(argv: list[str]) -> list[str]:
    return [a for a in argv if Path(a).name.lower() in ("bash", "bash.exe", "sh", "sh.exe")
            or a.lower().endswith(".sh")]


def _caller() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("testing-a29c-caller-")


def clause_1_windows_names_no_bash_and_carries_the_callers_cwd():
    from cairn.tools.base.script_argv import cairn_test_argv
    caller = _caller()
    argv, env, run_cwd = cairn_test_argv(*ARGS, cwd=caller, windows=True)
    assert not _names_bash(argv), f"the Windows argv names bash: {argv}"
    assert argv == [sys.executable, "-m", "cairn.devices.tester.cli", *ARGS], f"not the tester CLI: {argv}"
    assert Path(run_cwd) == REPO, f"the Windows entry does not run from the repo: {run_cwd}"
    assert env.get("CAIRN_TESTER_CALLER_CWD") == str(caller), (
        f"the caller's cwd is not carried: {env.get('CAIRN_TESTER_CALLER_CWD')!r} != {str(caller)!r}")
    assert env.get("PYTHONUTF8") == "1", "UTF-8 mode is not set, as bin/cairn sets it on Windows"
    if os.name == "nt":
        argv, env, run_cwd = cairn_test_argv("--help", cwd=caller)
        assert not _names_bash(argv), f"this host's argv names bash: {argv}"
        p = subprocess.run(argv, env=env, cwd=run_cwd, capture_output=True, text=True, timeout=120)
        assert p.returncode == 0 and "--exec" in p.stdout, (
            f"the bash-free entry did not reach the tester CLI: rc {p.returncode} {p.stderr[-400:]}")


def clause_2_posix_is_bin_cairn_test_unchanged():
    from cairn.tools.base.script_argv import cairn_test_argv
    caller = _caller()
    argv, env, run_cwd = cairn_test_argv(*ARGS, cwd=caller, windows=False)
    assert argv == [str(REPO / "bin" / "cairn"), "test", *ARGS], f"the POSIX argv changed: {argv}"
    assert Path(run_cwd) == caller, f"the POSIX entry does not run where the caller stands: {run_cwd}"
    if os.name != "nt":
        argv, env, run_cwd = cairn_test_argv("--help", cwd=caller)
        p = subprocess.run(argv, env=env, cwd=run_cwd, capture_output=True, text=True, timeout=120)
        assert p.returncode == 0 and "--exec" in p.stdout, (
            f"bin/cairn test --help did not answer: rc {p.returncode} {p.stderr[-400:]}")


def _main() -> int:
    checks = [clause_1_windows_names_no_bash_and_carries_the_callers_cwd,
              clause_2_posix_is_bin_cairn_test_unchanged]
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as e:  # noqa: BLE001 - a crash in a tooth is that tooth's red
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {type(e).__name__}: {e}")
    if failed:
        print(f"red - {len(failed)} of {len(checks)} teeth failed")
        return 1
    print("green - cairn_test_argv names no bash on Windows and is bin/cairn test on POSIX")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
