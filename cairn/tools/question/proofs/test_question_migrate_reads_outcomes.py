#!/usr/bin/env python3
"""Proof that question migrate walks a plan's outcomes as it walks its decisions
(ticket b3f0952c7e1d, parent 5c1e0a7d93b2, Q#100).

Measured 2026-11-14 at 2f64a7b02: ``decision_lines`` walks ``doc.get("decisions")`` alone and
``_set_line_question`` writes ``doc["decisions"][index]``, so an outcomes plan's lines that name
Akien are never found, and could not be written back if they were.

  (1) over an outcomes plan, migrate finds the same lines, of the same kinds, with the same
      question text and source, as over the same content written as decisions (an outcome's
      text is its claim, else its migrated text), and the record id is written back onto the
      outcome line — the plan grows no ``decisions`` key;
  (2) over a decisions plan, the finds and the writes are what main gives (measured
      2026-11-14 at 2f64a7b02): copy / delegated / no_words skipped / CC skipped, the copy's
      record named on decisions[0], and the plan grows no ``outcomes`` key.

Every world is a scratch commons in a temporary directory, its roots handed to the artifact
door, so nothing here reads or writes the live corpus.

    PYTHONPATH=. python3 cairn/tools/question/proofs/test_question_migrate_reads_outcomes.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"b3f0952c7e1d": {
    "1": "test_clause_1_an_outcomes_plan_migrates_as_its_decisions_twin",
    "2": "test_clause_2_a_decisions_plan_migrates_as_on_main",
}}

FAILURES: list[str] = []
TID = "b3f05c7a7c40"
QUOTED = "the answer is the decision"
# (text, by): the four kinds a line can be, plus one CC line that is not his
LINES = [
    ("Copy it.", f"Akien verbatim 2026-09-15: '{QUOTED}'"),
    ("Delegated.", "cc (CC's call, per Akien 2026-10-09)"),
    ("No words.", "akien"),
    ("Not his.", "CC at cast"),
]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _decisions():
    return {"decisions": [{"n": i, "text": t, "by": b, "writes_to": [], "reads": []}
                          for i, (t, b) in enumerate(LINES, 1)]}


def _outcomes():
    # the first is a migrated outcome (text, no claim yet); the rest carry their text as a claim
    out = []
    for i, (t, b) in enumerate(LINES, 1):
        o = {"n": i, "by": b, "writes_to": [], "reads": [], "after": []}
        o["text" if i == 1 else "claim"] = t
        out.append(o)
    return {"outcomes": out}


@contextmanager
def _world(plan: dict):
    from cairn.tools.artifact import artifact as A
    with tempfile.TemporaryDirectory(prefix="testing-b3f0952c7e1d-") as tmp:
        t = Path(tmp)
        commons, cairn = t / "CairnCommons", t / "cairn"
        for d in (commons / "questions", commons / "tickets", commons / "decisions", cairn):
            d.mkdir(parents=True)
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": t / "parked"})
        try:
            doc = {"id": TID, "date": "2026-09-01", "title": "a proof ticket",
                   "questions": "none, because a proof world", **plan}
            (commons / "tickets" / "_charter+why.json").write_text(json.dumps({
                "plan_fields": sorted(doc), "state_fields": ["date", "questions"],
                "log_kinds": {"field": {"field": "the top-level key", "value": "its value, whole"}}}) + "\n")
            path = commons / "tickets" / f"{TID}-a-proof-ticket.json"
            A.write_json(path, doc, verb="cast", why="a scratch ticket for the migrate proof")
            yield commons, path
        finally:
            A.set_diagnostic_roots(None)


def _run(plan: dict):
    """Migrate one plan; returns (the found lines, reduced; the ticket after; the records)."""
    from cairn.tools.base.ticket_file import read_ticket
    from cairn.tools.question import migrate as M
    with _world(plan) as (commons, path):
        found = [(x["index"], x["kind"], (x.get("args") or {}).get("question"),
                  (x.get("args") or {}).get("source"), (x.get("args") or {}).get("answer_words"))
                 for x in M.decision_lines(commons, set())]
        M.run(transcripts=None, root=commons / "questions")
        after = read_ticket(path)
        recs = {json.loads(p.read_text())["id"]: json.loads(p.read_text())
                for p in (commons / "questions").glob("open-*.json")}
        return found, after, recs


def _writes(after: dict, field: str, recs: dict) -> list[str]:
    bad = []
    lines = after.get(field) or []
    qid = lines[0].get("question") if lines else None
    if qid not in recs:
        bad.append(f"{field}[0] names no corpus record: {lines[:1]}")
    elif recs[qid].get("answer") != QUOTED:
        bad.append(f"the record holds {recs[qid].get('answer')!r}")
    if any("question" in x for x in lines[1:]):
        bad.append(f"a delegated, wordless or CC line was written: {lines[1:]}")
    if len(recs) != 1:
        bad.append(f"{len(recs)} records written, want 1")
    return bad


def test_clause_1_an_outcomes_plan_migrates_as_its_decisions_twin() -> None:
    bad = []
    f_old, _, _ = _run(_decisions())
    f_new, after, recs = _run(_outcomes())
    if not f_old:
        bad.append("the decisions twin found nothing to compare")
    if f_new != f_old:
        bad.append(f"finds differ: outcomes {f_new} vs decisions {f_old}")
    bad += _writes(after, "outcomes", recs)
    if "decisions" in after:
        bad.append(f"the outcomes plan grew a decisions key: {after.get('decisions')}")
    check("test_clause_1_an_outcomes_plan_migrates_as_its_decisions_twin", not bad, "; ".join(bad))


def test_clause_2_a_decisions_plan_migrates_as_on_main() -> None:
    bad = []
    found, after, recs = _run(_decisions())
    want = [(0, "copy", "Copy it — is that the decision?",
             f"tickets/{TID}-a-proof-ticket.json#D1", QUOTED),
            (1, "delegated", None, None, None),
            (2, "no_words", None, None, None)]
    if found != want:
        bad.append(f"finds {found}, main gives {want}")
    bad += _writes(after, "decisions", recs)
    if "outcomes" in after:
        bad.append(f"the decisions plan grew an outcomes key: {after.get('outcomes')}")
    check("test_clause_2_a_decisions_plan_migrates_as_on_main", not bad, "; ".join(bad))


def main() -> int:
    for fn in (test_clause_1_an_outcomes_plan_migrates_as_its_decisions_twin,
               test_clause_2_a_decisions_plan_migrates_as_on_main):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print("RED" if FAILURES else "GREEN")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
