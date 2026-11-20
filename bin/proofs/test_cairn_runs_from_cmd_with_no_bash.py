"""Proof for ticket 380d524e6e9c — the cairn launcher runs from Windows cmd with no bash on PATH.

Measured 2026-11-19 on akiendell: bin/cairn is 479 lines of bash and bin/cairn.cmd runs it through the
hardcoded "C:\\Program Files\\Git\\bin\\bash.exe", so typing `cairn` works only because Git Bash is installed.
Outline 5.4.3.8: the launcher is Python, run by Cairn's own interpreter, so Windows needs no bash.

  1. `cairn help` through cairn.cmd with every bash.exe directory taken off PATH exits 0 and prints the
     same lines the bash launcher prints.
  2. cairn.cmd names no bash and no Git install path.
  3. a verb the launcher exits 1 on (`cast` with no packet) exits 1 through cairn.cmd with the same stderr
     first line as the bash launcher.

    python3 bin/proofs/test_cairn_runs_from_cmd_with_no_bash.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROOF_TIMEOUT_S = 240

PROVES = {"380d524e6e9c": {
    "1": "tooth_1_help_runs_from_cmd_with_no_bash_on_path",
    "2": "tooth_2_cairn_cmd_names_no_bash",
    "3": "tooth_3_a_verb_that_exits_1_exits_1",
}}

_CMD = REPO / "bin" / "cairn.cmd"
_CMD_EXE = os.environ.get("COMSPEC", "cmd.exe")


def _windows_only() -> None:
    if os.name != "nt":
        raise AssertionError("UNRAN: cairn.cmd is Windows-only; run this on a Windows box")


def _path_without_bash() -> str:
    keep = [d for d in os.environ.get("PATH", "").split(os.pathsep)
            if d and not (Path(d) / "bash.exe").exists() and not (Path(d) / "bash").exists()]
    return os.pathsep.join(keep)


def _through_cmd(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PATH=_path_without_bash())
    return subprocess.run([_CMD_EXE, "/c", str(_CMD), *args], capture_output=True, text=True,
                          env=env, cwd=str(REPO), timeout=120)


def _through_bash(*args: str) -> subprocess.CompletedProcess:
    from cairn.tools.base.script_argv import bash_script_argv
    return subprocess.run(bash_script_argv(REPO / "bin" / "cairn") + list(args), capture_output=True,
                          text=True, cwd=str(REPO), timeout=120)


def _lines(r: subprocess.CompletedProcess) -> list[str]:
    return [ln.rstrip() for ln in r.stdout.splitlines() if ln.strip()]


def tooth_1_help_runs_from_cmd_with_no_bash_on_path() -> None:
    _windows_only()
    import shutil
    found = shutil.which("bash", path=_path_without_bash())
    assert found is None, f"the stripped PATH still finds bash: {found}"
    assert (REPO / "bin" / "cairn.py").is_file(), "bin/cairn.py (the Python launcher, outline 5.4.3.8) is absent"
    assert "cairn.py" in _CMD.read_text(encoding="utf-8", errors="replace"), "bin/cairn.cmd does not run bin/cairn.py"
    cmd = _through_cmd("help")
    assert cmd.returncode == 0, f"cairn.cmd help rc={cmd.returncode}: {(cmd.stderr or cmd.stdout)[:300]}"
    want = _lines(_through_bash("help"))
    assert want and _lines(cmd) == want, f"cmd printed {_lines(cmd)[:3]}, the bash launcher {want[:3]}"


def tooth_2_cairn_cmd_names_no_bash() -> None:
    text = _CMD.read_text(encoding="utf-8", errors="replace").lower()
    assert "bash" not in text, "bin/cairn.cmd names bash"
    assert "program files\\git" not in text, "bin/cairn.cmd names a Git install path"


def tooth_3_a_verb_that_exits_1_exits_1() -> None:
    _windows_only()
    bash = _through_bash("cast")
    assert bash.returncode == 1, f"the reference verb no longer exits 1 under bash: rc={bash.returncode}"
    cmd = _through_cmd("cast")
    assert cmd.returncode == 1, f"cairn.cmd cast rc={cmd.returncode}, bash launcher rc=1: {(cmd.stderr or cmd.stdout)[:200]}"
    first = lambda r: ((r.stderr or r.stdout).strip().splitlines() or [""])[0].strip()
    assert first(cmd) == first(bash), (first(cmd), first(bash))


TEETH = [tooth_1_help_runs_from_cmd_with_no_bash_on_path, tooth_2_cairn_cmd_names_no_bash,
         tooth_3_a_verb_that_exits_1_exits_1]


def main() -> int:
    fails = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
