"""Proof for ticket 9b8c7bdfa853: the question tool's both-ends probe reads its events from the
artifact TRAIL, not the index.

Since b15da5656579 the commons journal is an index holding only each path's newest entry, and
every entry lands in a day trail under this box's logs for 30 days. Akien, 2026-11-16: "the
latest entry remains in cairn commons, and everything else broken into... per day? per week?
inside of our .cairn/logs folder". A question is one file: opened, then answered, it leaves
only the answer in the index, so a probe reading the index counts half its events.

  1. one question opened and answered through a scratch world's door gives
     both_ends_agree._events both events, the question and the answer;
  2. the probe's finding names the 30-day horizon.

Every clause runs in a scratch diagnostic world (set_diagnostic_roots, with its own "trail"
key); the question door writes there. No live journal, trail or commons is touched, and the
inspector is not asked: the carry is read over a context this proof hands it.

Run bare:  PYTHONPATH=. python3 cairn/tools/question/proofs/test_both_ends_reads_the_artifact_trail.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {
    "9b8c7bdfa853": {
        "1": "test_an_open_and_its_answer_are_both_events",
        "2": "test_the_finding_names_the_horizon",
    },
}

TID = "0badc0ffee9b"
PASS = 0
FAIL = 0


def _world() -> Path:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = Path(scratch_dir("cairn-9b8c-"))
    commons = tmp / "CairnCommons"
    (commons / "questions").mkdir(parents=True)
    (commons / "tickets").mkdir()
    (tmp / "cairn").mkdir()
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn",
                            "parked": tmp / "parked", "trail": tmp / "trail"})
    doc = {"id": TID, "questions": "none, because the proof opens them through the door"}
    (commons / "tickets" / "_charter+why.json").write_text(json.dumps({"plan_fields": sorted(doc)}) + "\n")
    A.write_json(commons / "tickets" / f"{TID}-a-proof-world-ticket.json", doc,
                 verb="cast", why="the scratch ticket the proof's question is about")
    return commons


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {fn.__name__}")


def test_an_open_and_its_answer_are_both_events():
    from cairn.tools.question import question as Q
    from cairn.tools.question.probes import both_ends_agree as P
    commons = _world()
    rec = Q.open_question(TID, "is the open still counted once it is answered?",
                          "the probe counts events", root=commons / "questions")
    Q.answer(rec["id"], "it is", spawned=[], root=commons / "questions")
    got = [e["verb"] for e in P._events(commons) if rec["id"] in e["path"]]
    assert sorted(got) == ["answer", "question"], f"events for {rec['id']}: {got}"


def test_the_finding_names_the_horizon():
    from cairn.tools.question.probes import both_ends_agree as P
    ctx = {"events": 2, "answers": 1, "lacks": [], "wrong_intent": [], "with_spawned": 0,
           "questions": 1}
    finding = P._carry(ctx)["finding"]
    assert "30 days" in finding, f"the finding does not name its horizon: {finding!r}"


TEETH = [test_an_open_and_its_answer_are_both_events, test_the_finding_names_the_horizon]

if __name__ == "__main__":
    from cairn.tools.artifact import artifact as _A
    try:
        for fn in TEETH:
            _tooth(fn)
    finally:
        _A.set_diagnostic_roots(None)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
