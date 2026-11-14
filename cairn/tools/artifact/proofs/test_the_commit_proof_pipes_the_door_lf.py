"""Proof for ticket 56009ffbea93 — the commit-paths proof hands the artifact door LF on every box.

``test_a_commit_takes_only_the_paths_its_author_names.py`` fed the door its record through a text-mode pipe
(``subprocess.run(..., text=True, input=...)``), which writes CRLF on Windows; the door reads stdin raw and refuses a
non-canonical body, so the proof reded in its own fixture before any tooth ran. This tooth reads that proof's SOURCE
(an ast walk), so it is red on the unfixed proof on any box and green on the fixed one, and it starts nothing.

    python <this file>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
TARGET = REPO / "cairn" / "tools" / "artifact" / "proofs" / "test_a_commit_takes_only_the_paths_its_author_names.py"

PROVES = {
    "56009ffbea93": {
        "1": "the_commit_paths_proof_has_no_text_mode_input_call",
        "2": "the_door_write_pipes_bytes",
    },
}


def _calls():
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call)]


def _kw(call: ast.Call, name: str):
    return next((k.value for k in call.keywords if k.arg == name), None)


def the_commit_paths_proof_has_no_text_mode_input_call() -> None:
    bad = []
    for c in _calls():
        text = _kw(c, "text")
        if _kw(c, "input") is not None and isinstance(text, ast.Constant) and text.value is True:
            bad.append(c.lineno)
    assert not bad, f"a call passes input= with text=True (a text-mode pipe writes CRLF on Windows): lines {bad}"


def the_door_write_pipes_bytes() -> None:
    inputs = []
    for c in _calls():
        inp = _kw(c, "input")
        if inp is not None:
            inputs.append(inp)
    assert inputs, "the proof pipes nothing to the door: this tooth would pass over nothing"
    not_bytes = [i.lineno for i in inputs
                 if not (isinstance(i, ast.Call) and isinstance(i.func, ast.Attribute) and i.func.attr == "encode")]
    assert not not_bytes, f"an input= is not an .encode(...) call, so it is text: lines {not_bytes}"


TEETH = [the_commit_paths_proof_has_no_text_mode_input_call, the_door_write_pipes_bytes]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
