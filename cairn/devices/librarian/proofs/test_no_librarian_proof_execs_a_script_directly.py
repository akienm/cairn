"""Proof for ticket dd6be87bdb7e — no librarian proof execs a bin script directly.

Measured 2026-11-12 on akiendell: ``subprocess.run([str(BIN), ...])`` over the shebang script
cairn/devices/librarian/0/bin/question raises WinError 193. The argv is built with
cairn.tools.base.script_argv.bash_script_argv.

    python3 cairn/devices/librarian/proofs/test_no_librarian_proof_execs_a_script_directly.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

PROVES = {"dd6be87bdb7e": {
    "1": "test_the_harvest_proofs_tooth_8_runs_the_script_through_bash_script_argv",
    "2": "test_no_librarian_proof_execs_a_bin_script_directly",
}}


def _trees():
    for p in sorted(HERE.glob("test_*.py")):
        if p.name == Path(__file__).name:
            continue
        yield p, ast.parse(p.read_text(encoding="utf-8"))


def test_the_harvest_proofs_tooth_8_runs_the_script_through_bash_script_argv():
    src = (HERE / "test_the_librarian_harvests_cross_domain_questions.py").read_text(encoding="utf-8")
    assert "bash_script_argv" in src, "tooth 8 does not use bash_script_argv"
    print("tooth 8 builds its argv with bash_script_argv")


def test_no_librarian_proof_execs_a_bin_script_directly():
    bad = []
    for p, t in _trees():
        for n in ast.walk(t):
            if isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.List) and n.args[0].elts:
                first = n.args[0].elts[0]
                if (isinstance(first, ast.Call) and isinstance(first.func, ast.Name) and first.func.id == "str"
                        and first.args and isinstance(first.args[0], ast.Name) and first.args[0].id == "BIN"):
                    bad.append(f"{p.name}:{n.lineno}")
    assert bad == [], f"direct exec of a shebang script: {bad}"
    print("no librarian proof execs a bin script directly")


def main() -> int:
    bad = 0
    for t in (test_the_harvest_proofs_tooth_8_runs_the_script_through_bash_script_argv,
              test_no_librarian_proof_execs_a_bin_script_directly):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            bad += 1
            print(f"  FAIL  {t.__name__}\n        {type(exc).__name__}: {str(exc)[:300]}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
