"""The argv prefix that runs a bash script: the script itself on POSIX, ``bash <script>`` on Windows.

Windows cannot exec a shebang script (``OSError: [WinError 193] %1 is not a valid Win32
application``), so a caller that builds an argv for ``bin/cairn`` or a ``bin/cmd/*`` script
puts this in front instead of the bare path. On POSIX the result is ``[str(path)]`` -- the
argv every caller built before this existed.

``cairn_test_argv`` (ticket a29cf5216236) is the bash-free way to run ``cairn test``. On Windows,
MSYS bash cannot start at Low integrity (msys-2.0.dll's NtCreateDirectoryObject gets 0xC0000022,
and the process exits 0xC0000142). So a proof that runs ``bash bin/cairn test`` cannot run under
a prevent-kind instance seal. ``bin/cmd/test`` holds no logic of its own: it carries the caller's
cwd in CAIRN_TESTER_CALLER_CWD, cds to the repo, and execs ``python -m cairn.devices.tester.cli``.
On Windows this does the same with no bash. It starts the tester's public CLI as a process and
imports nothing from the tester (RULE 1). On POSIX it is ``bin/cairn test`` unchanged.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]   # cairn/tools/base/script_argv.py -> the repo


def bash_script_argv(path: Path | str) -> list[str]:
    """``[str(path)]`` on POSIX; ``[bash, str(path)]`` where ``os.name == 'nt'``."""
    if os.name != "nt":
        return [str(path)]
    return [shutil.which("bash") or "bash", str(path)]


def cairn_test_argv(*args: str, cwd: Path | str | None = None, windows: bool | None = None
                    ) -> tuple[list[str], dict[str, str], str]:
    """``(argv, env, run_cwd)`` that runs ``cairn test *args`` as if called from ``cwd`` (default:
    this process's cwd). On POSIX: ``bin/cairn test *args``, run where the caller stands. On
    Windows: ``python -m cairn.devices.tester.cli *args`` run from the repo, with the caller's cwd
    in CAIRN_TESTER_CALLER_CWD and Python in UTF-8 mode, as ``bin/cmd/test`` and ``bin/cairn`` set
    them. ``env`` is a full environment (this one plus those), ready to hand a spawn as its ``env`` keyword.
    ``windows`` defaults to this host; a proof passes it to measure the other shape."""
    caller = str(Path(cwd) if cwd is not None else Path.cwd())
    env = dict(os.environ)
    if windows if windows is not None else os.name == "nt":
        env.update(CAIRN_TESTER_CALLER_CWD=caller, PYTHONUTF8="1")
        return [sys.executable, "-m", "cairn.devices.tester.cli", *args], env, str(REPO)
    return [str(REPO / "bin" / "cairn"), "test", *args], env, caller
