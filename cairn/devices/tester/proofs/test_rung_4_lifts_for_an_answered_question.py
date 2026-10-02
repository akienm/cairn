"""Teeth for ticket 37ddc47686c2 — rung 4 of the reseal door lifts for Akien's answered question.

MEASURED 2026-10-02 at ticket fe1cba85cb12's reseal: test_hollow's live tooth redded when the
store moved, and the one-line repair to the proof was refused at rung 4 — "no ruling id was
given". No ruling CAN be given: ``ruling_refusal`` reads only CairnCommons/decisions/, frozen
at 2026-09-13, and since ticket 9adc6fddf185 a decision is an answered question (`cairn ruling
open` refuses). Zero seals in the repo had ever carried ``reseal_ruling``. So the door was
unreachable for every decision made after the store froze.

The question records here are fixtures in a scratch root, written as plain JSON: they are the
shape ``cairn.tools.question.question.answer`` writes, and the proof reads them back through
that tool's declared interface, never through its door (which would link a real ticket).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.reseal import ruling_refusal  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "37ddc47686c2": {
        "1": "test_a_question_akien_answered_lifts_rung_4",
        "2": "test_an_open_a_measured_or_an_unknown_question_does_not",
        "3": "test_a_confirmed_legacy_ruling_still_lifts_it",
    },
}


def _question(root: Path, qid: str, *, resolved: bool, answered_by: str | None) -> str:
    record = {
        "id": qid, "date": "2026-10-02", "ticket": "f1x7r4ng0001",
        "question": "may the tooth read moved files back through the run's report?",
        "why_it_blocks": "fixture", "raised_by": "fixture", "born_of": None, "source": None,
        "resolved": resolved, "answer": "yes" if resolved else None,
        "answered_by": answered_by, "answered_at": "2026-10-02T09:00:00" if resolved else None,
        "spawned": [] if resolved else None,
    }
    (root / f"{qid}.json").write_text(json.dumps(record), encoding="utf-8")
    return qid


def test_a_question_akien_answered_lifts_rung_4():
    root = scratch_dir("cairn-rung4-")
    qid = _question(root, "open-f1x7a0000001", resolved=True,
                    answered_by="Akien, recorded by caller class cc")
    assert ruling_refusal(qid, question_root=root) is None


def test_an_open_a_measured_or_an_unknown_question_does_not():
    root = scratch_dir("cairn-rung4-")
    still_open = _question(root, "open-f1x7a0000002", resolved=False, answered_by=None)
    measured = _question(root, "open-f1x7a0000003", resolved=True,
                         answered_by="measurement: /tmp/x.json, recorded by caller class cc")
    for qid in (still_open, measured, "open-f1x7a0000404"):
        why = ruling_refusal(qid, question_root=root)
        assert isinstance(why, str) and why.strip(), (qid, why)
        assert qid in why, f"the refusal must name the id it read: {why}"


def test_a_confirmed_legacy_ruling_still_lifts_it():
    """Over the live decisions/ store, an invariant and never a snapshot: every confirmed
    ruling lifts rung 4 and every unconfirmed one does not."""
    from cairn.machines.ruling import ruling as ruling_mod
    records = ruling_mod.load_all()
    confirmed = [r["id"] for r in records if r.get("confirmed")]
    unconfirmed = [r["id"] for r in records if not r.get("confirmed")]
    assert confirmed, "the decisions/ store carries no confirmed ruling to read"
    assert all(ruling_refusal(i, question_root=scratch_dir("cairn-rung4-")) is None for i in confirmed)
    assert all(ruling_refusal(i, question_root=scratch_dir("cairn-rung4-")) is not None for i in unconfirmed)


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
