"""Proof — the ticket-reader proof names paths by Path and runs the host's bash on a posix path.

Measured 2026-11-13 on Windows: three teeth of test_the_ticket_is_three_files.py were red for
spelling, not behaviour. r_whatsnext handed bash a backslash path (and a bare "bash" can resolve to
the WSL launcher); r_inbox cut a source on "/" though Windows spells it "\\"; r_skill_block looked
for a posix literal inside repr(got), where a resolved Windows path is spelled differently.

Three clauses, one tooth each. Each reads the reader-proof's own source, so it reds on Linux too.

    python3 cairn/tools/base/proofs/test_the_ticket_reader_proof_holds_on_windows.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGET = Path(__file__).resolve().parent / "test_the_ticket_is_three_files.py"

PROVES = {"349584bb8f69": {
    "1": "test_whatsnext_runs_the_hosts_bash_on_a_posix_path",
    "2": "test_inbox_names_the_source_by_path",
    "3": "test_skill_block_looks_for_the_resolved_path",
}}


def _fn(name):
    src = TARGET.read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node)
    raise AssertionError(f"{name} not found in {TARGET.name}")


def test_whatsnext_runs_the_hosts_bash_on_a_posix_path():
    s = _fn("r_whatsnext")
    assert "shutil.which" in s and "as_posix()" in s, s[-500:]
    assert '["bash", str(' not in s, s[-500:]


def test_inbox_names_the_source_by_path():
    s = _fn("r_inbox")
    assert 'rsplit("/"' not in s and "Path(" in s, s


def test_skill_block_looks_for_the_resolved_path():
    s = _fn("r_skill_block")
    assert "in repr(got)" not in s and ".resolve()" in s, s


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
