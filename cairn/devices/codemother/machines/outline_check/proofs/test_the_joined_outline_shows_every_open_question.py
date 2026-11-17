"""Proof for ticket b3472c7ee794 — `cairn codemother outline` writes the requirements pieces
joined into one file with every open question visible in it (Akien 2026-11-17: the joined
outline is "the ideal surface for me to field questions from").

The teeth, one per clause:

  1. `cairn codemother outline <out>` writes the pieces joined exactly as outline_bytes joins
     them, followed by an open-questions section, and prints the path it wrote;
  2. over a scratch questions corpus and scratch pieces, a numbered open question is listed
     under its Q# with its marker's section, an unnumbered one with its full text, an answered
     one not at all, and an open Q# with no marker in the pieces is flagged; a Q# quoted inside
     a record's text is never read as its number;
  3. over the live corpus, every unresolved question id appears in the joined file;
  4. every live unresolved question carries a Q#; each such Q# has a marker in the pieces or
     is flagged in the joined file; and every marked Q# is below the next number 0.6 names.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
REQ = REPO / "cairn" / "devices" / "cairn" / "requirements"
SHORTCUT = REPO / "cairn" / "devices" / "codemother" / "bin" / "outline"


class _CallTime:
    """A module under proof, bound at CALL time: the hollow reading takes it away."""

    def __init__(self, mod):
        self._mod = mod

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._mod), name)


J = _CallTime("cairn.devices.codemother.machines.outline_check.joined")
OC = _CallTime("cairn.devices.codemother.machines.outline_check.outline_check")
Q = _CallTime("cairn.tools.question.question")

PROVES = {
    "b3472c7ee794": {
        "1": "test_the_shortcut_writes_the_pieces_then_the_questions_and_prints_the_path",
        "2": "test_the_section_lists_numbered_unnumbered_and_flags_a_missing_marker",
        "3": "test_every_live_open_question_appears_in_the_joined_file",
        "4": "test_every_live_open_question_has_a_number_and_its_marker_or_a_flag",
    },
}


def test_the_shortcut_writes_the_pieces_then_the_questions_and_prints_the_path():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "joined.md"
        r = subprocess.run([sys.executable, str(SHORTCUT), str(out)], capture_output=True,
                           text=True, cwd=REPO, timeout=120)
        assert r.returncode == 0, r.stderr
        assert str(out) in r.stdout, r.stdout
        body = out.read_bytes()
        head = OC.outline_bytes(REQ)
        assert body.startswith(head), "the joined file does not open with outline_bytes"
        rest = body[len(head):].decode("utf-8")
        assert rest.lstrip().startswith(J.SECTION_HEAD), rest[:200]


PIECE = """\
# 7 THE YARD
- 7.1 The gate is green.
  - 7.1.1 [Q#5: is the gate green or blue?]
- 7.2 The hedge is low.
"""


def _rec(qid, question, *, resolved=False, notes=None, ticket="aaaaaaaaaaaa"):
    return {"id": qid, "date": "2026-11-17", "ticket": ticket, "question": question,
            "why_it_blocks": "x", "raised_by": "cc", "source": "test", "resolved": resolved,
            "answer": "blue" if resolved else None, "notes": notes or []}


def test_the_section_lists_numbered_unnumbered_and_flags_a_missing_marker():
    with tempfile.TemporaryDirectory() as td:
        pieces = Path(td) / "req"; pieces.mkdir()
        (pieces / "07-the-yard.md").write_text(PIECE)
        qd = Path(td) / "questions"; qd.mkdir()
        recs = [
            _rec("open-000000000001", "Q#5 (outline 7.1.1): is the gate green or blue?"),
            _rec("open-000000000002", "Ticket x touches 7.1, where Q#5 stands open: same?"),
            _rec("open-000000000003", "The hedge reads low; answering Q#2 it said high. Which?"),
            _rec("open-000000000004", "Q#9 (outline 7.2): is the hedge low?"),
            _rec("open-000000000005", "Q#5 (outline 7.1.1): an answered one", resolved=True),
            _rec("open-000000000006", "Does the yard need a gate at all?",
                 notes=[{"at": "x", "by": "CC", "text": "outline: Q#5 at 7.1.1"}]),
        ]
        for r in recs:
            (qd / f"{r['id']}.json").write_text(json.dumps(r))
        text = J.join(pieces, qd)
        assert text.startswith(PIECE), "the pieces do not open the joined text"
        sec = text[text.index(J.SECTION_HEAD):]
        # numbered: one entry under Q#5 at 7.1.1 naming all three of its records
        blocks = re.split(r"(?m)^## ", sec)[1:]
        q5 = [b for b in blocks if b.startswith("Q#5 ")]
        assert len(q5) == 1, blocks
        assert "7.1.1" in q5[0].splitlines()[0], q5[0]
        for qid in ("open-000000000001", "open-000000000002", "open-000000000006"):
            assert qid in q5[0], (qid, q5[0])
        # the quoted Q#2 is not a number: the record is unnumbered and listed in full
        assert not any(b.startswith("Q#2 ") for b in blocks), blocks
        assert "open-000000000003" in sec
        assert "The hedge reads low; answering Q#2 it said high. Which?" in sec
        # an open Q# with no marker is flagged, with its words
        q9 = [b for b in blocks if b.startswith("Q#9 ")]
        assert len(q9) == 1 and J.NO_MARKER in q9[0] and "is the hedge low?" in q9[0], blocks
        # the answered record is not listed
        assert "open-000000000005" not in sec


def _live():
    return J.join(REQ, None)


def test_every_live_open_question_appears_in_the_joined_file():
    text = _live()
    sec = text[text.index(J.SECTION_HEAD):]
    opens = Q.list_open()
    assert opens, "no open questions to measure"
    missing = [q["id"] for q in opens if q["id"] not in sec]
    assert not missing, missing


def test_every_live_open_question_has_a_number_and_its_marker_or_a_flag():
    pieces = OC.outline_bytes(REQ).decode("utf-8")
    marks = J.markers(pieces)
    text = _live()
    blocks = re.split(r"(?m)^## ", text[text.index(J.SECTION_HEAD):])[1:]
    flagged = {int(b.split()[0][2:]) for b in blocks if b.startswith("Q#") and J.NO_MARKER in b}
    unnumbered = [q["id"] for q in Q.list_open() if J.qnum(q) is None]
    assert not unnumbered, f"open questions with no Q#: {unnumbered}"
    unplaced = {J.qnum(q) for q in Q.list_open()} - set(marks) - flagged
    assert not unplaced, f"Q# with neither a marker nor a flag: {sorted(unplaced)}"
    m = re.search(r"next unused number,\s+which is (\d+)", pieces)
    assert m, "0.6 names no next number"
    assert max(marks) < int(m.group(1)), (max(marks), m.group(1))
