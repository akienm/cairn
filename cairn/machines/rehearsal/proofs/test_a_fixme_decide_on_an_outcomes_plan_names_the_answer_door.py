#!/usr/bin/env python3
"""Proof that a FIXME decide on an outcomes plan names the answer door (ticket 7373983f9418).

Measured 2026-11-18: on dda0e72b9c67 (an outcomes plan) three `cairn rehearse --decide "FIXME n"`
calls were refused 'outcomes[3] has no claim' — the symptom of decide's own claimless append —
and the builder spent a peer round trip learning that a shaped plan answers a FIXME at
build_inspector's door (inspector.py --answer-fixme, ticket e1d5f00a2b6c).

  (1) decide(step='FIXME 1', writes_to, reads) on an outcomes-plan ticket carrying a fixme list,
      in a scratch commons, raises Refused naming 'inspector.py --answer-fixme', and the ticket
      file's bytes are unchanged;
  (2) the same decide on a decisions-plan ticket still appends its 'FIXME 1' line.

Every ticket lives in a scratch commons (testing-marked, removed at exit). Nothing reads the
live corpus.

    PYTHONPATH=. python3 cairn/machines/rehearsal/proofs/test_a_fixme_decide_on_an_outcomes_plan_names_the_answer_door.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

PROVES = {"7373983f9418": {
    "1": "test_clause_1_an_outcomes_fixme_decide_names_the_answer_door",
    "2": "test_clause_2_a_decisions_fixme_decide_still_appends",
}}

FAILURES: list[str] = []

TID = "7373f00dfeed"
STEM = f"{TID}-testing-7373983f9418-fixme-decide"
CLAUSES = {"clauses": [{"n": 1, "claim": "a"}, {"n": 2, "claim": "b"}]}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


class World:
    def __init__(self, plan: dict):
        from cairn.tools.scratch.scratch import scratch_dir
        self.dir = Path(scratch_dir("testing-7373983f9418-fixme-decide-"))
        self.commons = self.dir / "CairnCommons"
        tickets = self.commons / "tickets"
        tickets.mkdir(parents=True)
        (tickets / "_charter+why.json").write_text(json.dumps({
            "plan_fields": ["id", "title", "intention", "falsifier", "decisions", "outcomes"],
            "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}}) + "\n")
        self.ticket = tickets / f"{STEM}.json"
        self.ticket.write_text(json.dumps({
            "id": TID, "title": "testing-7373983f9418-fixme-decide",
            "intention": "testing: a fixture ticket for the 7373983f9418 proof",
            "fixme": [{"k": 1, "text": "the proof declares no PROVES for clause 1"}],
            **plan}, indent=2) + "\n", encoding="utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def doc(self):
        return json.loads(self.ticket.read_text(encoding="utf-8"))


OUTCOMES = {"outcomes": [
    {"n": 1, "claim": "x is built", "writes_to": ["x.py"], "reads": ["x.py"], "after": []},
    {"n": 2, "claim": "x is proved", "writes_to": ["proofs/test_x.py"], "reads": [], "after": [1]}]}
DECISIONS = {"falsifier": CLAUSES,
             "decisions": [{"n": 1, "text": "build it", "by": "cc", "writes_to": ["x.py"], "reads": ["x.py"]}]}


def test_clause_1_an_outcomes_fixme_decide_names_the_answer_door() -> None:
    from cairn.machines.rehearsal import rehearsal as R
    with World(OUTCOMES) as w:
        before = w.ticket.read_bytes()
        try:
            entry = R.decide(TID, "FIXME 1", "the proof keys clause 1", by="cc", root=w.commons,
                             writes_to=["proofs/test_x.py"], reads=[])
            ok, detail = False, f"landed {entry}"
        except R.Refused as e:
            ok, detail = "inspector.py --answer-fixme" in str(e), f"refused: {e}"
        same = w.ticket.read_bytes() == before
    check("test_clause_1_an_outcomes_fixme_decide_names_the_answer_door", ok and same,
          f"{detail[:600]}; bytes unchanged {same}")


def test_clause_2_a_decisions_fixme_decide_still_appends() -> None:
    from cairn.machines.rehearsal import rehearsal as R
    with World(DECISIONS) as w:
        try:
            entry = R.decide(TID, "FIXME 1", "the proof keys clause 1", by="cc", root=w.commons,
                             writes_to=["proofs/test_x.py"], reads=[])
        except R.Refused as e:
            check("test_clause_2_a_decisions_fixme_decide_still_appends", False, f"refused: {e}")
            return
        lines = [d for d in w.doc()["decisions"] if d.get("step") == "FIXME 1"]
        ok = len(lines) == 1 and lines[0]["n"] == entry["n"] == 2 and lines[0]["by"] == "cc" \
            and lines[0]["text"].startswith("the proof keys clause 1")
    check("test_clause_2_a_decisions_fixme_decide_still_appends", ok, f"lines {lines}")


def main() -> int:
    for fn in (test_clause_1_an_outcomes_fixme_decide_names_the_answer_door,
               test_clause_2_a_decisions_fixme_decide_still_appends):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print(f"{'FAIL' if FAILURES else 'PASS'}: {len(FAILURES)} failing")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
