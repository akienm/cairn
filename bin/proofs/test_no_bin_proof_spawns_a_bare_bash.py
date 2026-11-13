"""Proof for the bin bare-bash ticket — no bin proof spawns the bare word bash or execs a shebang script.

Measured 2026-11-12 on akiendell: a bare ``["bash", ...]`` argv resolves through CreateProcess to the WSL
launcher (C:\\Windows\\System32\\bash.exe), and a direct exec of ``bin/cairn`` raises WinError 193. Each bin
proof names the host's bash (shutil.which) or builds the argv with bash_script_argv.

    python3 bin/proofs/test_no_bin_proof_spawns_a_bare_bash.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

PROVES = {"69075b0e8212": {
    "1": "test_no_bin_proof_builds_a_bare_bash_argv",
    "2": "test_no_bin_proof_execs_the_cairn_script_directly",
}}


def _trees():
    for p in sorted(HERE.glob("test_*.py")):
        if p.name == Path(__file__).name:
            continue
        yield p, ast.parse(p.read_text(encoding="utf-8"))


def test_no_bin_proof_builds_a_bare_bash_argv():
    bad = [f"{p.name}:{n.lineno}" for p, t in _trees() for n in ast.walk(t)
           if isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.List) and n.args[0].elts
           and isinstance(n.args[0].elts[0], ast.Constant) and n.args[0].elts[0].value == "bash"]
    assert bad == [], f"bare 'bash' argv list(s): {bad}"
    print("no bin proof builds a bare bash argv")


def test_no_bin_proof_execs_the_cairn_script_directly():
    bad = []
    for p, t in _trees():
        for n in ast.walk(t):
            if (isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.List) and n.args[0].elts):
                first = n.args[0].elts[0]
                if (isinstance(first, ast.Call) and isinstance(first.func, ast.Name) and first.func.id == "str"
                        and first.args and isinstance(first.args[0], ast.Name)
                        and first.args[0].id in ("CAIRN", "BIN_CAIRN")):
                    bad.append(f"{p.name}:{n.lineno}")
    assert bad == [], f"direct exec of the cairn shebang script: {bad}"
    print("no bin proof execs bin/cairn directly")


def main() -> int:
    bad = 0
    for t in (test_no_bin_proof_builds_a_bare_bash_argv, test_no_bin_proof_execs_the_cairn_script_directly):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            bad += 1
            print(f"  FAIL  {t.__name__}\n        {type(exc).__name__}: {str(exc)[:300]}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
