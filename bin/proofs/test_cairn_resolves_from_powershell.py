"""Proof for ticket dc945eb1f072: from PowerShell on Windows, `cairn` reaches bin/cairn through cairn.cmd.

Measured 2026-11-12: Get-Command cairn lists bin\\cairn.cmd first; the ticket's hypothesis that
PowerShell does not reach the .cmd was falsified, so bin/cairn.cmd needs no change. This proof pins it.

  1. cairn resolves to bin/cairn.cmd: the PATHEXT search over bin/ (no process spawned) picks the .cmd, and
     a scratch dir holding only the extensionless script resolves to nothing (the tooth can fail).
  2. a read-only verb through cairn.cmd exits 0 and prints the same first line as Git Bash. This SPAWNS
     windows, so it runs only with CAIRN_PROOF_MAY_SPAWN=1 (Akien's windows word); without it the tooth is RED
     (a gate is hard, never advisory), not skipped.

    python3 bin/proofs/test_cairn_resolves_from_powershell.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"dc945eb1f072": {"1": "tooth_1_cairn_resolves_to_the_cmd",
                           "2": "tooth_2_a_read_only_verb_matches_git_bash"}}
PATHEXT = ".COM;.EXE;.BAT;.CMD"
VERB = "help"


def _resolve(directory: Path) -> str | None:
    old = os.environ.get("PATHEXT")
    os.environ["PATHEXT"] = PATHEXT
    try:
        return shutil.which("cairn", path=str(directory))
    finally:
        if old is None:
            os.environ.pop("PATHEXT", None)
        else:
            os.environ["PATHEXT"] = old


def tooth_1_cairn_resolves_to_the_cmd() -> None:
    if os.name != "nt":
        raise AssertionError("UNRAN: PATHEXT resolution is Windows-only; run this on a Windows box")
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "cairn").write_text("#!/bin/sh\n")
        assert _resolve(Path(d)) is None, "a lone extensionless script must not resolve"
        (Path(d) / "cairn.cmd").write_text("@echo off\n")
        assert (_resolve(Path(d)) or "").lower().endswith("cairn.cmd"), "a .cmd beside it must resolve"
    got = _resolve(REPO / "bin")
    assert got and Path(got).name.lower() == "cairn.cmd", f"bin/ resolves cairn to {got!r}"


def tooth_2_a_read_only_verb_matches_git_bash() -> None:
    assert os.environ.get("CAIRN_PROOF_MAY_SPAWN") == "1", "RED: spawns windows; needs Akien's windows word (CAIRN_PROOF_MAY_SPAWN=1)"
    from cairn.tools.base.script_argv import bash_script_argv
    cmd = subprocess.run(["cmd.exe", "/c", str(REPO / "bin" / "cairn.cmd"), VERB], capture_output=True, text=True)
    bash = subprocess.run(bash_script_argv(REPO / "bin" / "cairn") + [VERB], capture_output=True, text=True)
    assert cmd.returncode == 0, f"cairn.cmd {VERB} rc={cmd.returncode}: {cmd.stderr[:300]}"
    first = lambda r: (r.stdout.strip().splitlines() or [""])[0].strip()
    assert first(cmd) and first(cmd) == first(bash), (first(cmd), first(bash))


TEETH = [tooth_1_cairn_resolves_to_the_cmd, tooth_2_a_read_only_verb_matches_git_bash]


def test_cairn_resolves_from_powershell() -> None:
    reds = []
    for t in TEETH:
        try:
            t()
            print(f"  GREEN  {t.__name__}")
        except Exception as e:  # every tooth prints; none stops the rest
            reds.append(t.__name__)
            print(f"  RED    {t.__name__}\n         {type(e).__name__}: {e}")
    assert not reds, f"red teeth: {reds}"


if __name__ == "__main__":
    try:
        test_cairn_resolves_from_powershell()
    except AssertionError as e:
        print(e)
        sys.exit(1)
