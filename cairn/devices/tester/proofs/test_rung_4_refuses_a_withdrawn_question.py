"""Tooth for ticket 79ce45551d60 — rung 4 of the reseal door refuses a question withdrawn as a duplicate.

``cairn question withdraw`` (ticket e1fb0e0bc945) resolves a duplicate with no answer, so it stops holding the BUILDME
lane. Rung 4 (``ruling_refusal``) lifted for any resolved ``open-`` question, so before this a
withdrawn duplicate, which decided nothing, would have passed as the decision behind a reseal.
The refusal names the question that stands in its place, whose answer is the decision.

The record is a fixture in a scratch root, written as plain JSON in the shape
``cairn.tools.question.question.withdraw`` writes, and read back through ``ruling_refusal``'s
``question_root`` seam (the pattern of test_rung_4_lifts_for_an_answered_question.py).

    bin/cairn test cairn/devices/tester/proofs/test_rung_4_refuses_a_withdrawn_question.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"79ce45551d60": {"1": "test_a_withdrawn_question_does_not_lift_rung_4"}}


def test_a_withdrawn_question_does_not_lift_rung_4():
    from cairn.devices.tester.reseal import ruling_refusal
    from cairn.tools.scratch.scratch import scratch_dir
    root = Path(scratch_dir("cairn-rung4wd-"))
    qid, keep = "open-f1x7a00000d1", "open-f1x7a00000d0"
    (root / f"{qid}.json").write_text(json.dumps({
        "id": qid, "date": "2026-11-19", "ticket": "f1x7r4ng0002",
        "question": "[Q#7] does the fixture hold?", "why_it_blocks": "fixture",
        "raised_by": "fixture", "born_of": None, "source": None,
        "resolved": True, "answer": None, "answered_by": None, "answered_at": None, "spawned": [],
        "withdrawn": {"duplicate_of": keep, "why": "the same [Q#7], opened twice",
                      "by": "caller class cc", "at": "2026-11-19T09:00:00-07:00"},
    }), encoding="utf-8")
    why = ruling_refusal(qid, question_root=root)
    assert isinstance(why, str) and qid in why and keep in why, why


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
