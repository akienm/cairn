"""Tooth for ticket 3d796b46f449, clause 2 — test_clearance.py's fixtures write their proof LF.

Measured 2026-11-12 on akiendell: ``Path.write_text`` without ``newline`` writes CRLF on Windows,
so a fixture proof's committed blob and the bytes a seal hashed disagree;
test_clearance.py's _accepts_a_recorded_approval and _reads_a_plan_approval went FAIL to PASS
with write_text forced to newline LF.

WHY THE TOOTH IS AN AST READ. The failure shows only on Windows; this tooth reds on Linux too,
because it reads the fixtures' source: every ``proof.write_text(...)`` inside ``_component`` and
``_covering_proof`` passes ``newline="\\n"``, and ``_component`` reads its fixture as utf-8 (a
locale read on Windows is the other half of the same drift).

Clause 1 (the rung-4 fixture) is measured at its own component, by
cairn/devices/tester/proofs/test_fixtures_that_git_hashes_write_lf.py (RULE 1).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[5]))

from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "3d796b46f449": {
        "2": "test_the_clearance_fixtures_write_their_proof_lf",
    },
}

_SRC = _HERE / "test_clearance.py"


def _fn(name: str) -> ast.FunctionDef:
    tree = ast.parse(_SRC.read_text(encoding="utf-8"))
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert fns, f"test_clearance.py holds no function {name}"
    return fns[0]


def _calls(fn: ast.FunctionDef, attr: str, target: str | None = None) -> list[ast.Call]:
    return [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == attr
            and (target is None or (isinstance(n.func.value, ast.Name) and n.func.value.id == target))]


def _kw(call: ast.Call, arg: str):
    got = [k.value for k in call.keywords if k.arg == arg]
    return got[0].value if got and isinstance(got[0], ast.Constant) else None


def test_the_clearance_fixtures_write_their_proof_lf():
    bad = []
    for name in ("_component", "_covering_proof"):
        writes = _calls(_fn(name), "write_text", "proof")
        assert writes, f"{name} writes no proof; this tooth reads its proof.write_text"
        bad += [f"{name}:{c.lineno}" for c in writes if _kw(c, "newline") != "\n"]
    reads = _calls(_fn("_component"), "read_text")
    bad += [f"_component:{c.lineno} read_text without utf-8" for c in reads if _kw(c, "encoding") != "utf-8"]
    assert not bad, f"fixture writes git hashes without newline LF (or locale reads): {bad}"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
