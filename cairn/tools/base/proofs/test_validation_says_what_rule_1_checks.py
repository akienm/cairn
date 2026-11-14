"""Proof for ticket 04937a56538f — validation.py's docstring says what the RULE 1 check checks today.

Measured 2026-11-13 on akienyoga9i at main: validation.py lines 8-10 said "Tools can import from
any device (the device_isolation sieve checks only cairn/devices/<X>/ files ...). So the imports
here are legal". Neither half holds: the RULE 1 check is build_inspector's encapsulation_holds,
which since ticket 124c0312c2d8 reds code OUTSIDE every device reaching into one; and
device_isolation, the import_sieve kind, is deleted by ticket 27f5ad6f62dc. The module itself
imports nothing from any device (ticket 67b78ae59c1d).

  1. the docstring names no retired check and no longer says a tool may import a device;
  2. what it now says holds: validation.py imports nothing under cairn.devices, at any depth of the file.

    bin/cairn test cairn/tools/base/proofs/test_validation_says_what_rule_1_checks.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"04937a56538f": {
    "1": "test_the_docstring_names_no_retired_check",
    "2": "test_validation_imports_nothing_from_a_device"}}

SRC = ROOT / "cairn" / "tools" / "base" / "validation.py"
RETIRED = "device" + "_isolation"


def test_the_docstring_names_no_retired_check():
    doc = ast.get_docstring(ast.parse(SRC.read_text(encoding="utf-8"))) or ""
    assert doc.strip(), "validation.py has no docstring to read"
    assert RETIRED not in doc, f"the docstring still names {RETIRED}"
    assert "Tools can import from any device" not in doc, "the docstring still says a tool may import a device"
    assert "encapsulation_holds" in doc, "the docstring does not name the check that holds today"


def test_validation_imports_nothing_from_a_device():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    mods = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    mods += [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert len(mods) >= 3, f"read only {mods}: the walk did not see the file's imports"
    assert [m for m in mods if m.startswith("cairn.devices")] == [], mods


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
