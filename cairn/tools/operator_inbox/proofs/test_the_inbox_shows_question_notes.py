"""The operator inbox shows an open question's notes under it (ticket abcad52a407e).

db99e97f7b4f gave an open question a `notes` list (cairn/tools/question/question.py note())
and rendered it in `cairn question show`, but left the inbox alone under RULE 1 — so the
QUESTIONS FOR OPERATOR section printed only id, ticket, question and born_of. Akien reads
questions in the inbox; a note taken to help him answer was invisible where he answers.

  1. NOTES RENDER UNDER THEIR QUESTION: an open question with two notes prints both note
     lines, oldest first, each naming who wrote it and when, directly under its question.
  2. NO NOTES, NO CHANGE: an open question with no notes renders exactly as before.

The world is a scratch questions dir handed to gather_all; every other lane reads live and
is not asserted on. Each tooth imports the inbox INSIDE its body, so a reverted inbox.py reds
teeth instead of breaking this file's import.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"abcad52a407e": {
    "1": "test_notes_render_under_their_question_oldest_first",
    "2": "test_a_question_with_no_notes_renders_as_before",
}}

_NOTES = [
    {"text": "NOTEMARKER-ONE measured 3 of 5", "by": "cc", "at": "2026-10-11T10:00:00+00:00"},
    {"text": "NOTEMARKER-TWO the second read agrees", "by": "akien", "at": "2026-10-11T11:00:00+00:00"},
]


def _rendered() -> str:
    from cairn.tools.operator_inbox import inbox
    from cairn.tools.scratch.scratch import scratch_dir
    qdir = scratch_dir("inbox-question-notes-")
    (qdir / "open-00000000000a.json").write_text(json.dumps({
        "id": "open-00000000000a", "ticket": "aaaaaaaaaaaa", "raised_by": "cc",
        "question": "a noted question?", "notes": _NOTES}))
    (qdir / "open-00000000000b.json").write_text(json.dumps({
        "id": "open-00000000000b", "ticket": "bbbbbbbbbbbb", "raised_by": "cc",
        "question": "a plain question?"}))
    return inbox.format_inbox(inbox.gather_all(questions_dir=qdir))


def test_notes_render_under_their_question_oldest_first() -> None:
    out = _rendered()
    want = ("    open-00000000000a  [aaaaaaaaaaaa]\n"
            "      a noted question?\n"
            "      note 2026-10-11T10:00:00+00:00 (cc): NOTEMARKER-ONE measured 3 of 5\n"
            "      note 2026-10-11T11:00:00+00:00 (akien): NOTEMARKER-TWO the second read agrees\n"
            "    open-00000000000b  [bbbbbbbbbbbb]\n")
    assert want in out, f"the notes did not render under their question, in order:\n{out}"


def test_a_question_with_no_notes_renders_as_before() -> None:
    out = _rendered()
    want = ("    open-00000000000b  [bbbbbbbbbbbb]\n"
            "      a plain question?\n"
            "\n"
            "  answer with:")
    assert want in out, f"a question with no notes changed shape:\n{out}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
