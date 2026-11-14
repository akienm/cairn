"""Proof — test_a_commit_takes_only_the_paths_its_author_names.py hands the door LF on every box.

Measured 2026-11-13 on Windows: that proof's fixture piped its JSON record to
`cairn artifact write --stdin` through subprocess.run(text=True, input=...). A text-mode pipe on
Windows turns "\\n" into "\\r\\n", the door read the bytes raw and refused the record as not
canonical, and the proof aborted in its world before any tooth ran. On Linux it stayed green.

The door is right to refuse; the fixture is wrong. One tooth, read from the file, so it reds on
any box: no subprocess call in that proof passes input= while text=True.

    python3 cairn/tools/artifact/proofs/test_the_commit_proof_pipes_the_door_lf.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGET = Path(__file__).resolve().parent / "test_a_commit_takes_only_the_paths_its_author_names.py"

PROVES = {"56009ffbea93": {"1": "test_no_call_there_pipes_input_through_a_text_mode_pipe"}}


def _text_mode_input_calls(src: str) -> list[int]:
    lines = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        kw = {k.arg: k.value for k in node.keywords if k.arg}
        text = kw.get("text")
        if "input" in kw and isinstance(text, ast.Constant) and text.value is True:
            lines.append(node.lineno)
    return lines


def test_no_call_there_pipes_input_through_a_text_mode_pipe():
    bad = _text_mode_input_calls(TARGET.read_text(encoding="utf-8"))
    assert bad == [], (f"{TARGET.name} passes input= with text=True at lines {bad}: on Windows the "
                       "pipe writes CRLF and the door refuses the record")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
