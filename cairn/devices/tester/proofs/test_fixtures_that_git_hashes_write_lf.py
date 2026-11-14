"""Tooth for ticket 3d796b46f449, clause 1 — the rung-4 fixture writes its committed proof LF.

Measured 2026-11-12 on akiendell: ``Path.write_text`` without ``newline`` writes CRLF on Windows,
so the bytes the ladder bound (hashed off the written file) and the blob git commits (CRLF→LF
under autocrlf, or not) disagree and test_rung_4_follows_the_ticket_kind reads FAIL there. With
write_text forced to newline LF it went FAIL to PASS.

WHY THE TOOTH IS AN AST READ. The failure shows only on Windows; this tooth reds on Linux too,
because it reads the fixture's source: every ``proof.write_text(...)`` inside ``_world`` must
pass ``newline="\\n"``. A hollow build (one call fixed, one left) fails it.

The renamed-proof twin (ticket 6eb235ee813d, test_rung_4_follows_a_renamed_proof.py) binds a
ladder to the same kind of hash, over files its ``_world`` names ``old`` and ``new``; its
tooth reads those writes too. It declares no clause: 6eb2's falsifier holds none for line
endings, and this only keeps its fixture from regressing to CRLF on Windows.

Clause 2 (test_clearance.py's fixtures) is measured at its own component, by
cairn/devices/codemother/machines/clearance/proofs/test_fixtures_that_git_hashes_write_lf.py
(RULE 1: a proof measures only its own component).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[3]))

from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "3d796b46f449": {
        "1": "test_the_rung_4_world_writes_its_proof_lf",
    },
}


def _unforced_writes(src: Path, fn_name: str, target: str) -> tuple[int, list[int]]:
    """(count of ``<target>.write_text`` calls in ``fn_name``, lines of those without newline LF)."""
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == fn_name]
    assert fns, f"{src.name} holds no function {fn_name}"
    seen, bad = 0, []
    for node in ast.walk(fns[0]):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "write_text" and isinstance(node.func.value, ast.Name)
                and node.func.value.id == target):
            seen += 1
            nl = [k.value for k in node.keywords if k.arg == "newline"]
            if not (nl and isinstance(nl[0], ast.Constant) and nl[0].value == "\n"):
                bad.append(node.lineno)
    return seen, bad


def test_the_rung_4_world_writes_its_proof_lf():
    seen, bad = _unforced_writes(_HERE / "test_rung_4_follows_the_ticket_kind.py", "_world", "proof")
    assert seen >= 2, f"_world writes its proof {seen} time(s); this tooth reads the v1 and v2 writes"
    assert not bad, f"_world writes its committed proof without newline LF at line(s) {bad}"


def test_the_renamed_proof_world_writes_its_proof_lf():
    src = _HERE / "test_rung_4_follows_a_renamed_proof.py"
    old_seen, old_bad = _unforced_writes(src, "_world", "old")
    new_seen, new_bad = _unforced_writes(src, "_world", "new")
    assert old_seen >= 1 and new_seen >= 2, (
        f"_world writes old {old_seen} and new {new_seen} time(s); this tooth reads the v1 write"
        " at the old name and the rename and v2 writes at the new one")
    assert not (old_bad or new_bad), (
        f"_world writes its committed proof without newline LF at line(s) {sorted(old_bad + new_bad)}")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
