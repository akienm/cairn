#!/usr/bin/env python3
"""Proof that a plan line judged a constraint at build-open keeps its paths (ticket 609529c846ca).

Measured 2026-11-16: ``judge_plan`` turned a line judged ``{"constraint": true}`` into a bare
string in ``constraints`` and dropped its ``writes_to`` and ``reads``. Three live tickets
(149b9a1ab9c4, 044020db63c0, 95557c2ed44f) lost 84 writes_to and 84 reads paths that way; the
writes survived only in ``bounds.in``, the reads in no field and no log. 149b's own proof then
read an empty plan and sealed red.

  (1) a line judged a constraint that names writes_to or reads leaves exactly one log line, kind
      ``field``, field ``constraint_paths``, value ``{n, writes_to, reads}`` equal to the line's,
      and its text still joins ``constraints`` verbatim;
  (2) a constraint line naming no paths logs no ``constraint_paths`` line, and a refused packet
      logs none at all (plan, state and log byte-identical);
  (3) in the live commons beside this checkout, each of the three tickets above carries
      ``constraint_paths`` lines (the re-fill), and every path in its ``bounds.in`` is named by an
      outcome's writes_to or a ``constraint_paths`` line.

Clauses 1 and 2 run in a scratch commons carrying a copy of the store charter, its roots handed to
the artifact door; clause 3 only reads the live corpus.

    PYTHONPATH=. python3 skills/sail/proofs/test_a_constraint_line_keeps_its_paths_in_the_log.py
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

PROVES = {"609529c846ca": {
    "1": "test_a_constraint_line_logs_its_paths",
    "2": "test_a_pathless_constraint_or_a_refused_packet_logs_no_paths",
    "3": "test_the_three_live_tickets_name_every_bound_path",
}}

FAILURES: list[str] = []
TID = "60952a7a7c40"
READ = "skills/sail/SKILL.md"  # a reads path that resolves in this checkout
CLAIM = "the reader sees every claim"
HOW = "D2: every listed proof asks over the bus"
PATHLESS = "D3: ORDER, after the verb child"
LIVE = ("149b9a1ab9c4", "044020db63c0", "95557c2ed44f")


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _plan() -> dict:
    return {"falsifier": {"clauses": [{"n": 1, "claim": CLAIM}]},
            "decisions": [
                {"n": 1, "text": "D1: read through the plan view", "writes_to": ["skills/x.py"],
                 "reads": [READ]},
                {"n": 2, "text": HOW, "writes_to": ["skills/p.py", "skills/q.py"],
                 "reads": [READ]},
                {"n": 3, "text": PATHLESS, "writes_to": [], "reads": []}]}


@contextmanager
def _world(plan: dict):
    from cairn.tools.artifact import artifact as A
    charter = _REPO.parent / "CairnCommons" / "tickets" / "_charter+why.json"
    with tempfile.TemporaryDirectory(prefix="testing-609529c846ca-") as tmp:
        t = Path(tmp)
        commons, cairn = t / "CairnCommons", t / "cairn"
        for d in (commons / "tickets", cairn):
            d.mkdir(parents=True)
        shutil.copy(charter, commons / "tickets" / "_charter+why.json")
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": t / "parked"})
        try:
            path = commons / "tickets" / f"{TID}-a-proof-ticket.json"
            A.write_json(path, {"id": TID, "title": "a proof ticket",
                                "bounds": {"in": ["skills/x.py", "skills/p.py", "skills/q.py"],
                                           "out": ["the rest"]},
                                "measured": [{"when": "2026-11-16", "saw": "a scratch ticket",
                                              "how": "written by this proof"}], **plan},
                         verb="cast", why="a scratch ticket for the constraint-paths proof")
            yield path
        finally:
            A.set_diagnostic_roots(None)


def _paths_lines(path: Path) -> list[dict]:
    from cairn.tools.base.ticket_log import read_log
    return [x["value"] for x in read_log(path)
            if x.get("kind") == "field" and x.get("field") == "constraint_paths"]


def test_a_constraint_line_logs_its_paths() -> None:
    from cairn.tools.base.ticket_file import read_ticket
    from skills.sail import judge_plan as J
    bad = []
    with _world(_plan()) as path:
        r = J.apply(path, {"1": {"claim": CLAIM}, "2": {"constraint": True},
                           "3": {"constraint": True}})
        if not r["written"]:
            bad.append(f"not written: {r['lacks']}")
        got = _paths_lines(path)
        want = [{"n": 2, "writes_to": ["skills/p.py", "skills/q.py"], "reads": [READ]}]
        if got != want:
            bad.append(f"constraint_paths lines {got}, want {want}")
        if read_ticket(path).get("constraints") != [HOW, PATHLESS]:
            bad.append(f"constraints {read_ticket(path).get('constraints')}, want verbatim texts")
    check("test_a_constraint_line_logs_its_paths", not bad, "; ".join(bad))


def test_a_pathless_constraint_or_a_refused_packet_logs_no_paths() -> None:
    from skills.sail import judge_plan as J
    bad = []
    with _world(_plan()) as path:
        before = {p.name: p.read_bytes() for p in sorted(path.parent.glob(f"{TID}-*"))}
        r = J.apply(path, {"2": {"constraint": True}})  # lines 1 and 3 unjudged: refused
        after = {p.name: p.read_bytes() for p in sorted(path.parent.glob(f"{TID}-*"))}
        if r["written"] or before != after:
            bad.append(f"a refused packet wrote: written={r['written']}")
    plan = _plan()
    plan["decisions"] = [plan["decisions"][0], plan["decisions"][2]]
    plan["decisions"][1]["n"] = 2
    with _world(plan) as path:
        r = J.apply(path, {"1": {"claim": CLAIM}, "2": {"constraint": True}})
        if not r["written"]:
            bad.append(f"pathless: not written: {r['lacks']}")
        if _paths_lines(path):
            bad.append(f"a pathless constraint logged paths: {_paths_lines(path)}")
    check("test_a_pathless_constraint_or_a_refused_packet_logs_no_paths", not bad, "; ".join(bad))


def test_the_three_live_tickets_name_every_bound_path() -> None:
    from cairn.tools.base.ticket_file import find_ticket, read_ticket
    bad = []
    for tid in LIVE:
        plan = find_ticket(tid)
        if plan is None:
            bad.append(f"{tid}: not in the store beside this checkout")
            continue
        doc = read_ticket(plan)
        lines = _paths_lines(Path(plan))
        if not lines:
            bad.append(f"{tid}: no constraint_paths line (the re-fill is absent)")
        named = set()
        for o in doc.get("outcomes") or []:
            named.update(o.get("writes_to") or [])
        for v in lines:
            named.update(v.get("writes_to") or [])
        missing = sorted(set((doc.get("bounds") or {}).get("in") or []) - named)
        if missing:
            bad.append(f"{tid}: {len(missing)} bounds.in path(s) named nowhere: {missing[:3]}")
    check("test_the_three_live_tickets_name_every_bound_path", not bad, "; ".join(bad))


def main() -> int:
    for fn in (test_a_constraint_line_logs_its_paths,
               test_a_pathless_constraint_or_a_refused_packet_logs_no_paths,
               test_the_three_live_tickets_name_every_bound_path):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print("RED" if FAILURES else "GREEN")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
