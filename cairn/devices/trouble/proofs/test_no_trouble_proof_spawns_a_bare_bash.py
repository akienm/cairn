"""Proof for ticket 979317aff085 — no trouble proof spawns the bare word bash.

Measured 2026-11-12 on akiendell: a bare ``["bash", ...]`` argv resolves through CreateProcess to the WSL
launcher (C:\\Windows\\System32\\bash.exe). Each trouble proof names the host's bash (shutil.which on nt).

    python3 cairn/devices/trouble/proofs/test_no_trouble_proof_spawns_a_bare_bash.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

PROVES = {"979317aff085": {
    "1": "test_no_trouble_proof_builds_a_bare_bash_argv",
    "2": "test_the_edited_proofs_name_the_hosts_bash",
}}

EDITED = ('test_a_cli_clear_carries_the_hand.py', 'test_launcher_words_are_scripts.py', 'test_trouble_never_rides_the_bus.py')


def _trees():
    for p in sorted(HERE.glob("test_*.py")):
        if p.name == Path(__file__).name:
            continue
        yield p, ast.parse(p.read_text(encoding="utf-8"))


def test_no_trouble_proof_builds_a_bare_bash_argv():
    bad = [f"{p.name}:{n.lineno}" for p, t in _trees() for n in ast.walk(t)
           if isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.List) and n.args[0].elts
           and isinstance(n.args[0].elts[0], ast.Constant) and n.args[0].elts[0].value == "bash"]
    assert bad == [], f"bare 'bash' argv list(s): {bad}"
    print("no trouble proof builds a bare bash argv")


def test_the_edited_proofs_name_the_hosts_bash():
    missing = [n for n in EDITED if "_BASH" not in (HERE / n).read_text(encoding="utf-8")]
    assert missing == [], f"proofs without a _BASH head: {missing}"
    print("the edited proofs name the host's bash")


def main() -> int:
    bad = 0
    for t in (test_no_trouble_proof_builds_a_bare_bash_argv, test_the_edited_proofs_name_the_hosts_bash):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            bad += 1
            print(f"  FAIL  {t.__name__}\n        {type(exc).__name__}: {str(exc)[:300]}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
