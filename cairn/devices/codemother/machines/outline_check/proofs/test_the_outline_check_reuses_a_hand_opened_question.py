"""Proof for ticket e1d3fd0f2aab — the outline check reuses a hand-opened question on the same Q#n.

Measured 2026-11-16: Q#119 on e56a68e651c2 and Q#116 on 312be610152e each stood twice in the
inbox, once opened by hand (``cairn question open``, source None) and once by ``cairn
outlinecheck``, because the check reused only questions it had opened itself.

The teeth, one per falsifier clause:

  1. with a hand-opened question naming Q#7 open on the fixture ticket, a check touching 2.1.2
     opens no question and lists the hand question under questions_already_open;
  2. a hand question naming Q#70 on the ticket, or naming Q#7 on another ticket, does not stop
     the check opening its Q#7 question;
  3. with a hand-opened question on the ticket, a conflict still opens its own question:
     conflict reuse reads only outline_check's questions.

Every tooth runs over the scratch World of the neighbouring proof
(test_the_outline_check_opens_a_question_per_conflict.py): a fixture commons and outline handed
to the artifact door, and a stub reader. Nothing reads or writes the live commons.

Run bare:  PYTHONPATH=. python3 cairn/devices/codemother/machines/outline_check/proofs/test_the_outline_check_reuses_a_hand_opened_question.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_the_outline_check_opens_a_question_per_conflict as N  # noqa: E402  the World fixture

PROVES = {
    "e1d3fd0f2aab": {
        "1": "test_a_hand_opened_question_on_the_same_q_n_is_reused",
        "2": "test_a_hand_question_on_another_number_or_another_ticket_is_not_reused",
        "3": "test_a_conflict_still_opens_beside_a_hand_question",
    },
}
OTHER = "0badc0ffee03"


def _hand(w, ticket: str, text: str) -> dict:
    """A question opened the way `cairn question open` opens one: no source."""
    from cairn.tools.question import question as Q
    return Q.open_question(ticket, text, "a hand-opened fixture question",
                           root=w.commons / "questions")


def _other_ticket(w) -> None:
    doc = dict(N.TICKET, id=OTHER, title="another fixture ticket")
    (w.commons / "tickets" / f"{OTHER}-another-fixture-ticket.json").write_text(
        json.dumps(doc, indent=2) + "\n")


def test_a_hand_opened_question_on_the_same_q_n_is_reused():
    with N.World() as w:
        hand = _hand(w, N.TID, "Q#7 (outline 2.1.2): does the widget live in the rack?")
        rec = w.check(N.Stub(N._read(touches=["2.1.2"])))["record"]
        assert rec["questions_opened"] == [], rec["questions_opened"]
        assert rec["questions_already_open"] == [hand["id"]], rec["questions_already_open"]
        assert [q["id"] for q in w.questions()] == [hand["id"]], w.questions()


def test_a_hand_question_on_another_number_or_another_ticket_is_not_reused():
    with N.World() as w:
        _other_ticket(w)
        near = _hand(w, N.TID, "Q#70 (outline 2.1.2): is the widget's rack its own?")
        far = _hand(w, OTHER, "Q#7 (outline 2.1.2): does the widget live in the rack?")
        rec = w.check(N.Stub(N._read(touches=["2.1.2"])))["record"]
        assert len(rec["questions_opened"]) == 1, rec
        assert rec["questions_already_open"] == [], rec["questions_already_open"]
        opened = next(q for q in w.questions() if q["id"] == rec["questions_opened"][0])
        assert opened["ticket"] == N.TID and "where Q#7 stands open" in opened["question"], opened
        assert {near["id"], far["id"]}.isdisjoint(rec["questions_opened"]), rec


def test_a_conflict_still_opens_beside_a_hand_question():
    with N.World() as w:
        hand = _hand(w, N.TID, f'Is "{N.LINE_21}" still the widget\'s rule?')
        rec = w.check(N.Stub(N._read(conflicts=[N.CONFLICT])))["record"]
        assert len(rec["questions_opened"]) == 1, rec
        assert hand["id"] not in rec["questions_opened"] + rec["questions_already_open"], rec


def main() -> int:
    teeth = [test_a_hand_opened_question_on_the_same_q_n_is_reused,
             test_a_hand_question_on_another_number_or_another_ticket_is_not_reused,
             test_a_conflict_still_opens_beside_a_hand_question]
    failed = []
    for tooth in teeth:
        try:
            tooth()
        except Exception as e:                       # noqa: BLE001 — the reason is the record
            failed.append(tooth.__name__)
            print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {str(e)[:300]}")
            continue
        print(f"  PASS  {tooth.__name__}")
    if failed:
        print(f"red — {len(failed)} of {len(teeth)} teeth: {', '.join(failed)}")
        return 1
    print(f"green — {len(teeth)} teeth: the outline check reuses a question already open on the "
          "same ticket and Q#n whoever opened it, and only that one")
    return 0


if __name__ == "__main__":
    sys.exit(main())
