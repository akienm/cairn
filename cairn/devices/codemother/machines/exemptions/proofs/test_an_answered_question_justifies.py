#!/usr/bin/env python3
"""The answered-question tooth of ticket 9adc6fddf185 (clause 5), moved from
cairn/tools/question/proofs/test_question.py by ticket 6560fdb5b935: the question tool's proof
measured two machines, and RULE 1 has a proof measure only its own component.

  5. the two sieves (corrosion's citation, exemptions' justification) take an answered question
     id as same-act evidence and refuse an unanswered one and a cite of neither.

Over a scratch world the proof owns (``artifact.set_diagnostic_roots`` for the question door's
writes, ``CAIRN_QUESTIONS_DIR`` for the readers).

    bin/cairn test cairn/devices/codemother/machines/exemptions/proofs/test_an_answered_question_justifies.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

TICKET = "9adc6fddf185"
PROVES = {TICKET: {"5": "test_an_answered_question_is_same_act_evidence_for_the_sieves"}}


def test_an_answered_question_is_same_act_evidence_for_the_sieves() -> None:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.question import question as Q
    from cairn.devices.codemother.machines.corrosion import citation   # corrosion moves into codemother at 47f5765e52a8
    from cairn.devices.codemother.machines.exemptions import justification
    with tempfile.TemporaryDirectory(prefix="cairn-answered-justifies-") as d:
        tmp = Path(d)
        commons = tmp / "CairnCommons"
        qdir = commons / "questions"
        qdir.mkdir(parents=True)
        (commons / "tickets").mkdir()
        (tmp / "cairn").mkdir()
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn", "parked": tmp / "parked"})
        os.environ["CAIRN_QUESTIONS_DIR"] = str(qdir)
        try:
            qid = Q.open_question(TICKET, "is an answered question evidence?",
                                  "the sieves read it", root=qdir)["id"]
            Q.answer(qid, "yes", spawned=[], root=qdir)
            ok_ans, _ = citation.answered_question(qid)
            open_q = Q.open_question(TICKET, "still open?", "unanswered — must not count", root=qdir)
            ok_open, why_open = citation.answered_question(open_q["id"])
            base = {"id": "x", "path": "cairn/tools/question/question.py"}
            lack_ans = justification.justification_lack(dict(base, justification_kind="question", evidence=qid))
            lack_open = justification.justification_lack(dict(base, justification_kind="question",
                                                              evidence=open_q["id"]))
            lack_none = justification.justification_lack(dict(base, justification_kind="none", evidence="because"))
        finally:
            os.environ.pop("CAIRN_QUESTIONS_DIR", None)
            A.set_diagnostic_roots(None)
    assert ok_ans and not ok_open and lack_ans == "" and lack_open != "" and lack_none != "", (
        f"answered={ok_ans} open={ok_open} ({why_open[:40]}) lacks: ans={lack_ans!r} "
        f"open={lack_open[:40]!r} none={lack_none[:40]!r}")


def main() -> int:
    try:
        test_an_answered_question_is_same_act_evidence_for_the_sieves()
        print("  green  test_an_answered_question_is_same_act_evidence_for_the_sieves")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"  RED    test_an_answered_question_is_same_act_evidence_for_the_sieves: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
