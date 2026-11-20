"""Proof for ticket ddc9957704d2 — a launcher failure files a trouble and falls over to Rescue.

Measured 2026-11-20 on akiendell: bin/cairn.cmd is a shim that runs bin/cairn.py and returns its exit code; it
files no trouble, has no fallover and no reserved exit code. Outline 5.4.3.8.1-4: the shell in front of the
launcher falls over to Rescue (Claude Code outside Cairn, 6.5: `claude --dangerously-skip-permissions "read this ..."`)
when the launcher fails, writes the trouble file itself when Python cannot run, only a launcher failure (a reserved
exit code) counts, and Rescue is launched only at a terminal.

Each tooth runs a COPY of bin/cairn.cmd beside a fixture cairn.py, with a stub `claude` first on a scratch PATH that
records its argv, a scratch trouble store (CAIRN_TROUBLE_STORE) and the terminal probe set by CAIRN_LAUNCHER_TTY.

  1. no Python (venv absent): a trouble file is written in the trouble format and a repeat increments it.
  2. the reserved exit code at a terminal: the trouble is filed and claude is exec'd with the permission flag and the trouble path.
  3. a verb that exits 1: no trouble, no claude, exit 1.
  4. the reserved exit code with no terminal: trouble filed, no claude, exit loud non-zero naming the trouble path.
  5. the reserved exit code at a terminal with claude not on PATH: trouble filed, exit loud naming that claude was not found.
  6. bin/cairn.py exits the reserved code when the launcher itself fails, and a verb's own 1 stays 1.

    python3 cairn/devices/recovery/proofs/test_a_launcher_failure_falls_over_to_rescue.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROOF_TIMEOUT_S = 300
RESERVED = 70          # bin/cairn.py's LAUNCHER_FAILURE_EXIT (ticket ddc9957704d2, hypothesis, named in the ticket)

PROVES = {"ddc9957704d2": {
    "1": "tooth_1_no_python_writes_and_increments_a_trouble",
    "2": "tooth_2_a_launcher_failure_at_a_terminal_execs_claude",
    "3": "tooth_3_a_verb_that_exits_1_files_nothing",
    "4": "tooth_4_a_launcher_failure_with_no_terminal_does_not_exec",
    "5": "tooth_5_no_claude_on_path_still_files_and_is_loud",
    "6": "tooth_6_the_python_launcher_marks_its_own_failure",
}}

_CMD_EXE = os.environ.get("COMSPEC", "cmd.exe")


def _windows_only() -> None:
    if os.name != "nt":
        raise AssertionError("UNRAN: cairn.cmd is Windows-only; run this on a Windows box")


def _real_venv() -> Path:
    v = Path(os.environ.get("CAIRN_VENV") or (Path.home() / ".cairn" / "venv"))
    if not (v / "Scripts" / "python.exe").is_file():
        raise AssertionError(f"UNRAN: no Cairn venv at {v}; lay it first")
    return v


def _path_without_claude() -> str:
    keep = [d for d in os.environ.get("PATH", "").split(os.pathsep)
            if d and not any((Path(d) / n).exists() for n in ("claude", "claude.exe", "claude.cmd", "claude.ps1"))]
    return os.pathsep.join(keep)


class _Rig:
    """A scratch bin/ with a copy of cairn.cmd, a fixture cairn.py and a stub claude."""

    def __init__(self, exit_code: int, *, venv: Path | None, tty: bool, claude: bool = True):
        from cairn.tools.scratch.scratch import scratch_dir
        self.root = scratch_dir("testing-ddc9957704d2-")
        (self.root / "bin").mkdir()
        shutil.copy(REPO / "bin" / "cairn.cmd", self.root / "bin" / "cairn.cmd")
        (self.root / "bin" / "cairn.py").write_text(f"import sys\nsys.exit({exit_code})\n", encoding="utf-8")
        self.store = self.root / "store"
        self.argv_file = self.root / "claude_argv.txt"
        stub = self.root / "stub"
        stub.mkdir()
        (stub / "claude.cmd").write_text(f"@echo off\r\necho %*> \"{self.argv_file}\"\r\nexit /b 0\r\n", encoding="utf-8")
        path = (str(stub) + os.pathsep if claude else "") + _path_without_claude()
        self.env = dict(os.environ, PATH=path, CAIRN_TROUBLE_STORE=str(self.store),
                        CAIRN_LAUNCHER_TTY="1" if tty else "0",
                        CAIRN_VENV=str(venv if venv else self.root / "no-venv"))

    def run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([_CMD_EXE, "/c", str(self.root / "bin" / "cairn.cmd"), *args], capture_output=True,
                              text=True, env=self.env, cwd=str(self.root), timeout=120)

    def troubles(self) -> list[Path]:
        return sorted(self.store.rglob("*.json")) if self.store.exists() else []

    def claude_argv(self) -> str | None:
        return self.argv_file.read_text(encoding="utf-8").strip() if self.argv_file.exists() else None


def tooth_1_no_python_writes_and_increments_a_trouble() -> None:
    _windows_only()
    rig = _Rig(0, venv=None, tty=False)
    first = rig.run("help")
    assert first.returncode != 0, "the launcher ran with no venv and exited 0"
    files = rig.troubles()
    assert len(files) == 1, f"expected one trouble file, found {[f.name for f in files]}"
    rec = json.loads(files[0].read_text(encoding="utf-8"))
    for key in ("id", "why", "count", "first_seen", "last_seen", "occurrences"):
        assert key in rec, f"the trouble file lacks {key!r}: {sorted(rec)}"
    assert rec["count"] == 1, rec["count"]
    rig.run("help")
    again = rig.troubles()
    assert len(again) == 1, f"a repeat wrote a second file: {[f.name for f in again]}"
    assert json.loads(again[0].read_text(encoding="utf-8"))["count"] == 2, "a repeat did not increment the count"


def tooth_2_a_launcher_failure_at_a_terminal_execs_claude() -> None:
    _windows_only()
    rig = _Rig(RESERVED, venv=_real_venv(), tty=True)
    rig.run("help")
    files = rig.troubles()
    assert len(files) == 1, f"the launcher failure filed {[f.name for f in files]}"
    argv = rig.claude_argv()
    assert argv is not None, "the shell did not exec claude"
    assert "--dangerously-skip-permissions" in argv, argv
    assert files[0].name in argv, f"the prompt does not carry the trouble file {files[0].name}: {argv}"


def tooth_3_a_verb_that_exits_1_files_nothing() -> None:
    _windows_only()
    rig = _Rig(1, venv=_real_venv(), tty=True)
    r = rig.run("probescan")
    assert r.returncode == 1, f"rc={r.returncode}"
    assert not rig.troubles(), f"a verb's own failure filed {[f.name for f in rig.troubles()]}"
    assert rig.claude_argv() is None, "a verb's own failure exec'd claude"


def tooth_4_a_launcher_failure_with_no_terminal_does_not_exec() -> None:
    _windows_only()
    rig = _Rig(RESERVED, venv=_real_venv(), tty=False)
    r = rig.run("help")
    assert r.returncode != 0, "a launcher failure with no terminal exited 0"
    files = rig.troubles()
    assert len(files) == 1, f"filed {[f.name for f in files]}"
    assert rig.claude_argv() is None, "claude was exec'd with no terminal"
    assert files[0].name in (r.stderr + r.stdout), f"the exit does not name the trouble path: {r.stderr[:200]}"


def tooth_5_no_claude_on_path_still_files_and_is_loud() -> None:
    _windows_only()
    rig = _Rig(RESERVED, venv=_real_venv(), tty=True, claude=False)
    r = rig.run("help")
    assert r.returncode != 0, "a launcher failure with no claude exited 0"
    files = rig.troubles()
    assert len(files) == 1, f"filed {[f.name for f in files]}"
    out = (r.stderr + r.stdout).lower()
    assert "claude" in out and "not found" in out, f"the exit does not say claude was not found: {r.stderr[:200]}"
    assert files[0].name in (r.stderr + r.stdout), "the exit does not name the trouble path"


def tooth_6_the_python_launcher_marks_its_own_failure() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir("testing-ddc9957704d2-py-")
    (root / "bin").mkdir()
    shutil.copy(REPO / "bin" / "cairn.py", root / "bin" / "cairn.py")
    (root / "cairn").mkdir()      # a package that will not import: the launcher's own failure, not a verb's
    (root / "cairn" / "__init__.py").write_text("raise RuntimeError('fixture: the cairn package will not import')\n", encoding="utf-8")
    broken = subprocess.run([sys.executable, str(root / "bin" / "cairn.py"), "help"], capture_output=True,
                            text=True, cwd=str(root), timeout=120, env=dict(os.environ, PYTHONPATH=""))
    assert broken.returncode == RESERVED, (
        f"a launcher whose cairn package will not import exited {broken.returncode}, not the reserved {RESERVED}: "
        f"{broken.stderr[-200:]}")
    verb = subprocess.run([sys.executable, str(REPO / "bin" / "cairn.py"), "probescan"], capture_output=True,
                          text=True, cwd=str(REPO), timeout=120)
    assert verb.returncode == 1, f"a verb's own failure exited {verb.returncode}, not 1"


TEETH = [tooth_1_no_python_writes_and_increments_a_trouble, tooth_2_a_launcher_failure_at_a_terminal_execs_claude,
         tooth_3_a_verb_that_exits_1_files_nothing, tooth_4_a_launcher_failure_with_no_terminal_does_not_exec,
         tooth_5_no_claude_on_path_still_files_and_is_loud, tooth_6_the_python_launcher_marks_its_own_failure]


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
