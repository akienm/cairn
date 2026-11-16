"""/design pokes the recompile gate of the checkout it is run from, never the house's
(ticket 40e40e8e5d53).

Measured 2026-11-16: skills/design/SKILL.md named $HOME/dev/src/cairn/.../recompile_gate.sh, the
house tree's copy, and the gate derives its repo from its own path, so a poke from a worktree
rewrote the HOUSE commons' intentions-congruency-lab/ (the dirt that landed as 5bb9c1c6). This
reads every gate command the SKILL.md names and runs it with bash from a scratch git checkout
holding a stub gate, under a scratch HOME holding a decoy house gate. The stub must answer.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_MD = Path(__file__).resolve().parents[1] / "SKILL.md"
GATE = "cairn/tools/intentions_model_compiler/recompile_gate.sh"

PROVES = {"40e40e8e5d53": {"3": "test_the_design_skill_pokes_its_own_checkouts_gate"}}


def gate_commands(text: str) -> list[str]:
    """Every gate command SKILL.md names: a backtick span, or a bare code line, ending in
    recompile_gate.sh and carrying a shell expansion (a relative mention is prose, not a call)."""
    found = [m.group(1) for m in re.finditer(r"`([^`\n]*recompile_gate\.sh)`", text)]
    for line in text.splitlines():
        bare = line.strip()
        if "`" not in bare and bare.endswith("recompile_gate.sh"):
            found.append(bare)
    return [c for c in found if "$" in c]


def _gate(path: Path, word: str) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(f"#!/usr/bin/env bash\necho {word}\n")
    path.chmod(0o755)


def test_the_design_skill_pokes_its_own_checkouts_gate():
    cmds = gate_commands(SKILL_MD.read_text(encoding="utf-8"))
    assert cmds, f"{SKILL_MD} names no recompile gate command; this tooth would read nothing"
    with tempfile.TemporaryDirectory(prefix="recompile-own-") as d:
        checkout, home = Path(d) / "checkout", Path(d) / "home"
        _gate(checkout / GATE, "OWN")
        _gate(home / "dev/src/cairn" / GATE, "HOUSE")
        subprocess.run(["git", "init", "-q", str(checkout)], check=True)
        env = {**os.environ, "HOME": str(home)}
        for cmd in cmds:
            p = subprocess.run(["bash", "-c", cmd], cwd=checkout, env=env,
                               capture_output=True, text=True, timeout=30)
            assert p.stdout.strip() == "OWN", (
                f"{cmd!r} ran {'the HOUSE gate' if 'HOUSE' in p.stdout else 'no gate'} "
                f"from a scratch checkout: stdout={p.stdout.strip()!r} stderr={p.stderr.strip()[-200:]!r}")


def _main() -> int:
    try:
        test_the_design_skill_pokes_its_own_checkouts_gate()
    except AssertionError as exc:
        print(f"  RED    test_the_design_skill_pokes_its_own_checkouts_gate: {exc}")
        return 1
    print("  PASS   test_the_design_skill_pokes_its_own_checkouts_gate")
    print("green — /design pokes its own checkout's recompile gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
