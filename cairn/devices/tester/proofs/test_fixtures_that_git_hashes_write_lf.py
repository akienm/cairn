"""Proof for ticket 3d796b46f449 — a fixture that writes a proof file which git then commits,
or which a seal then hashes, writes it with ``newline="\\n"``.

Measured 2026-11-13 on Windows: ``Path.write_text`` writes CRLF there and the system gitconfig
has ``core.autocrlf=true``, so the blob git commits is LF and the bytes on disk are CRLF. The
tester then reads "the file the ladder bounded" back from git by sha256, finds no blob of that
hash, and refuses rung 4. Re-running with ``write_text`` forced to LF turned
``test_rung_4_follows_the_ticket_kind`` and the three clearance proofs that run
``test_clearance.py`` from red to green. On Linux ``write_text`` already writes LF, so only a
read of the fixtures' own source can red there.

Neither tooth spawns a process. Tooth 1 runs the scanner over a fixture first, so it cannot
read green by finding nothing.

    python <this file>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
RUNG4 = REPO / "cairn/devices/tester/proofs/test_rung_4_follows_the_ticket_kind.py"
CLEARANCE = REPO / "cairn/devices/codemother/machines/clearance/proofs/test_clearance.py"

PROVES = {
    "3d796b46f449": {
        "1": "rung_4_world_writes_its_proof_with_lf",
        "2": "clearance_proof_builders_write_their_proof_with_lf",
    },
}


def write_text_calls_without_lf(source: str, func: str) -> list[int]:
    """Line numbers of ``<x>.write_text(...)`` calls inside ``func`` that do not carry
    ``newline="\\n"``, restricted to calls on a bare name ``proof`` (the file the fixture
    commits or seals). Raises when ``func`` is absent, so a rename cannot read green."""
    tree = ast.parse(source)
    fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func), None)
    if fn is None:
        raise AssertionError(f"{func} is gone from the fixture file")
    bad, seen = [], 0
    for n in ast.walk(fn):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "write_text"
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "proof"):
            continue
        seen += 1
        kw = {k.arg: k.value for k in n.keywords}
        v = kw.get("newline")
        if not (isinstance(v, ast.Constant) and v.value == "\n"):
            bad.append(n.lineno)
    if not seen:
        raise AssertionError(f"{func} writes no proof file any more — the scan has nothing to hold")
    return bad


def _the_scanner_reds_a_bare_write_and_passes_an_lf_one() -> None:
    bare = "def f():\n    proof.write_text('x', encoding='utf-8')\n"
    fixed = "def f():\n    proof.write_text('x', encoding='utf-8', newline='\\n')\n"
    assert write_text_calls_without_lf(bare, "f") == [2], write_text_calls_without_lf(bare, "f")
    assert write_text_calls_without_lf(fixed, "f") == [], write_text_calls_without_lf(fixed, "f")


def rung_4_world_writes_its_proof_with_lf():
    _the_scanner_reds_a_bare_write_and_passes_an_lf_one()
    bad = write_text_calls_without_lf(RUNG4.read_text(encoding="utf-8"), "_world")
    assert not bad, f"_world writes the committed proof without newline=\"\\n\" at lines {bad}"


def clearance_proof_builders_write_their_proof_with_lf():
    src = CLEARANCE.read_text(encoding="utf-8")
    bad = {f: write_text_calls_without_lf(src, f) for f in ("_component", "_covering_proof")}
    bad = {f: ls for f, ls in bad.items() if ls}
    assert not bad, f"proof files written without newline=\"\\n\": {bad}"


TEETH = [rung_4_world_writes_its_proof_with_lf,
         clearance_proof_builders_write_their_proof_with_lf]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {type(e).__name__}: {e}  [{t.__name__}]")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
