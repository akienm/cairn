#!/usr/bin/env python3
"""Proof that at build-open sail judges a plan not yet in outcomes into outcomes and
constraints, and writes it only through the cast door's admission (ticket 4d8a2c6e91f7,
parent 5c1e0a7d93b2, Q#100).

Measured 2026-11-14 at 2f64a7b02: nothing in skills/sail converts a plan — a decisions ticket,
or one the migration moved with outcomes awaiting their claims, reaches /chart as it stands.

  (1) a decisions ticket and a migrated ticket with no-claim outcomes, each given a packet
      judging every line, end with every outcome claimed, clause n still outcome n, each
      constraint's text verbatim in ``constraints``, each 'log' conflict whole in the log (and
      the falsifier whole beside it), a 'named' conflict standing and reported, and the plan
      admitted by the cast door's shape check;
  (2) a packet that leaves a line unjudged, or whose result the shape check refuses
      (a constraint mid-plan leaves outcomes numbered [2, 3], not 1..k), or that is malformed,
      writes nothing — plan, state and log byte-identical — and names each lack.

Every world is a scratch commons in a temporary directory carrying a copy of the store charter
(``CairnCommons/tickets/_charter+why.json`` beside this checkout), its roots handed to the
artifact door, so nothing here reads or writes the live corpus.

    PYTHONPATH=. python3 skills/sail/proofs/test_a_decisions_plan_is_judged_into_outcomes_at_build_open.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"4d8a2c6e91f7": {
    "1": "test_clause_1_a_judged_plan_becomes_outcomes_the_door_admits",
    "2": "test_clause_2_an_unjudged_or_refused_packet_writes_nothing",
}}

FAILURES: list[str] = []
TID = "4d8a5c7a7c40"
READ = "skills/sail/SKILL.md"  # a reads path that resolves in this checkout
CLAIMS = ["the reader sees every claim", "the old shape reads as before"]
HOW = "D3: keep the one door — Akien 2026-11-14: 'write it through rewrite_ticket'"
CONFLICT = "D4: also rewrite the inbox, superseded by 8f3d"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _decisions_plan() -> dict:
    return {"falsifier": {"clauses": [{"n": i, "claim": c} for i, c in enumerate(CLAIMS, 1)],
                          "horizon": "the next build"},
            "decisions": [
                {"n": 1, "text": "D1: read through the plan view", "writes_to": ["skills/x.py"],
                 "reads": [READ], "by": "CC at cast"},
                {"n": 2, "text": "D2: the red-first proof", "writes_to": ["skills/p.py"],
                 "reads": [READ]},
                {"n": 3, "text": HOW, "writes_to": [], "reads": [], "by": "Akien"},
                {"n": 4, "text": CONFLICT, "writes_to": ["skills/inbox.py"], "reads": []}]}


def _migrated_plan() -> dict:
    return {"constraints": ["standing: one writer"],
            "outcomes": [
                {"n": 1, "text": "D1: read through the plan view", "writes_to": ["skills/x.py"],
                 "reads": [READ], "after": []},
                {"n": 2, "claim": CLAIMS[1], "writes_to": ["skills/p.py"], "reads": [READ],
                 "after": [1]},
                {"n": 3, "text": HOW, "writes_to": [], "reads": [], "after": []}]}


@contextmanager
def _world(plan: dict):
    from cairn.tools.artifact import artifact as A
    charter = _REPO.parent / "CairnCommons" / "tickets" / "_charter+why.json"
    with tempfile.TemporaryDirectory(prefix="testing-4d8a2c6e91f7-") as tmp:
        t = Path(tmp)
        commons, cairn = t / "CairnCommons", t / "cairn"
        for d in (commons / "tickets", cairn):
            d.mkdir(parents=True)
        shutil.copy(charter, commons / "tickets" / "_charter+why.json")
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": t / "parked"})
        try:
            path = commons / "tickets" / f"{TID}-a-proof-ticket.json"
            A.write_json(path, {"id": TID, "title": "a proof ticket",
                                "bounds": {"in": ["skills/x.py"], "out": ["the rest"]},
                                "measured": [{"when": "2026-11-14", "saw": "a scratch ticket",
                                              "how": "written by this proof"}], **plan},
                         verb="cast", why="a scratch ticket for the judge-plan proof")
            yield path
        finally:
            A.set_diagnostic_roots(None)


def _bytes(path: Path) -> dict:
    return {p.name: p.read_bytes() for p in sorted(path.parent.glob(f"{TID}-*"))}


def _log(path: Path) -> list[dict]:
    from cairn.tools.base.ticket_log import read_log
    return read_log(path)


def _admitted(path: Path, doc: dict) -> list[str]:
    from cairn.tools.base.transitions import _shape_lacks
    return _shape_lacks(doc, path.parent / "_charter+why.json")


def test_clause_1_a_judged_plan_becomes_outcomes_the_door_admits() -> None:
    from cairn.tools.base import plan as P
    from cairn.tools.base.ticket_file import read_ticket
    from skills.sail import judge_plan as J
    bad = []
    # (a) the decisions ticket
    with _world(_decisions_plan()) as path:
        r = J.apply(path, {"1": {"claim": CLAIMS[0]}, "2": {"claim": CLAIMS[1]},
                           "3": {"constraint": True},
                           "conflicts": [{"n": 4, "disposition": "log", "why": "superseded"}]})
        doc = read_ticket(path)
        if not r["written"]:
            bad.append(f"decisions: not written: {r['lacks']}")
        if "decisions" in doc or "falsifier" in doc:
            bad.append("decisions: the old shape still stands beside the outcomes")
        if P.clauses(doc) != [{"n": i, "claim": c} for i, c in enumerate(CLAIMS, 1)]:
            bad.append(f"decisions: clause n is not outcome n: {P.clauses(doc)}")
        if P.awaiting(doc):
            bad.append(f"decisions: outcomes still await: {P.awaiting(doc)}")
        if doc.get("constraints") != [HOW]:
            bad.append(f"decisions: constraints {doc.get('constraints')}, want [{HOW!r}]")
        log = _log(path)
        ret = [x["decision"] for x in log if x.get("kind") == "decision_retired"]
        if len(ret) != 1 or {k: v for k, v in ret[0].items() if k != "retired"} != \
                _decisions_plan()["decisions"][3] or ret[0]["retired"].get("because") != "superseded":
            bad.append(f"decisions: the logged conflict is not whole in the log: {ret}")
        fal = [x["value"] for x in log if x.get("kind") == "field" and x.get("field") == "falsifier"]
        if fal != [_decisions_plan()["falsifier"]]:
            bad.append(f"decisions: the falsifier is not whole in the log: {fal}")
        if _admitted(path, doc):
            bad.append(f"decisions: the shape check refuses the written plan: {_admitted(path, doc)}")
    # (b) the migrated ticket
    with _world(_migrated_plan()) as path:
        r = J.apply(path, {"1": {"claim": CLAIMS[0]}, "3": {"constraint": True},
                           "conflicts": [{"n": 2, "disposition": "named", "why": "reads stale"}]})
        doc = read_ticket(path)
        if not r["written"]:
            bad.append(f"migrated: not written: {r['lacks']}")
        if [(o["n"], o.get("claim")) for o in doc.get("outcomes", [])] != [(1, CLAIMS[0]), (2, CLAIMS[1])]:
            bad.append(f"migrated: outcomes {doc.get('outcomes')}")
        if doc.get("constraints") != ["standing: one writer", HOW]:
            bad.append(f"migrated: constraints {doc.get('constraints')}")
        if [c.get("n") for c in r["named"]] != [2]:
            bad.append(f"migrated: the named conflict is not reported: {r['named']}")
        if _admitted(path, doc):
            bad.append(f"migrated: the shape check refuses the written plan: {_admitted(path, doc)}")
    check("test_clause_1_a_judged_plan_becomes_outcomes_the_door_admits", not bad, "; ".join(bad))


def test_clause_2_an_unjudged_or_refused_packet_writes_nothing() -> None:
    from skills.sail import judge_plan as J
    bad = []
    cases = [
        ("unjudged", _decisions_plan(),
         {"1": {"claim": CLAIMS[0]}, "3": {"constraint": True},
          "conflicts": [{"n": 4, "disposition": "log", "why": "superseded"}]},
         ["line 2 is unjudged"]),
        ("migrated unjudged", _migrated_plan(), {"1": {"claim": CLAIMS[0]}},
         ["line 3 is unjudged"]),
        ("shape refused", _decisions_plan(),
         {"1": {"constraint": True}, "2": {"claim": CLAIMS[1]}, "3": {"claim": "c3"},
          "4": {"claim": "c4"}},
         ["not 1..k"]),
        ("malformed", _decisions_plan(),
         {"1": {"claim": ""}, "2": {"claim": CLAIMS[1], "constraint": True}, "3": "yes",
          "9": {"claim": "x"},
          "conflicts": [{"n": 4, "disposition": "forget"}]},
         ["judgement for 1", "judgement for 2", "judgement for 3", "'9'", "disposition",
          "no why"]),
    ]
    for label, plan, packet, named in cases:
        with _world(plan) as path:
            before = _bytes(path)
            r = J.apply(path, packet)
            after = _bytes(path)
            if r["written"]:
                bad.append(f"{label}: written")
            if after != before:
                bad.append(f"{label}: the ticket's files changed: {sorted(set(after) ^ set(before)) or 'bytes'}")
            for want in named:
                if not any(want in lk for lk in r["lacks"]):
                    bad.append(f"{label}: no lack names {want!r}: {r['lacks']}")
    check("test_clause_2_an_unjudged_or_refused_packet_writes_nothing", not bad, "; ".join(bad))


def main() -> int:
    for fn in (test_clause_1_a_judged_plan_becomes_outcomes_the_door_admits,
               test_clause_2_an_unjudged_or_refused_packet_writes_nothing):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print("RED" if FAILURES else "GREEN")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
