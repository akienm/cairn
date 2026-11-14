#!/usr/bin/env python3
"""Proof that sail's tool-call scorer reads the plan's foreseen paths from outcomes as from
decisions (ticket e9c2a17f5b30, parent 5c1e0a7d93b2, Q#100).

Measured 2026-11-14 at 2f64a7b02: ``observe`` collects foreseen paths from
``ticket_doc.get("decisions")`` alone, so over an outcomes ticket every read outside
``bounds.in`` is a miss, even a read an outcome names.

  (1) over an outcomes ticket, a read of a path some outcome reads or writes (or under one) is
      foreseen and makes no finding, and any other read is a miss — the same misses its
      decisions twin draws, named against ``outcomes.reads``;
  (2) over a decisions ticket the hits and misses are what main gives (measured 2026-11-14 at
      2f64a7b02), each miss named against ``decisions.reads``.

``observe`` is a pure read of the ticket dict and the calls handed to it; the calls are built
here, with their paths under a fixture root, so no transcript and no live tree is read.

    PYTHONPATH=. python3 skills/sail/proofs/test_toolcalls_read_outcomes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"e9c2a17f5b30": {
    "1": "test_clause_1_an_outcomes_ticket_foresees_what_its_outcomes_name",
    "2": "test_clause_2_a_decisions_ticket_scores_as_on_main",
}}

FAILURES: list[str] = []
TID = "e9c25c7a7c40"
ROOT = "/repo/cairn/"
BOUNDS = {"in": ["skills/x/mod.py"], "out": ["cairn/devices/codemother"]}
# (writes_to, reads) per step; the second step's read is a directory, so a read under it is foreseen
STEPS = [(["skills/x/mod.py"], ["skills/x/README.md"]),
         (["skills/x/proofs/test_mod.py"], ["cairn/tools/base"])]
READS = ["skills/x/README.md",            # read by step 1: foreseen
         "skills/x/proofs/test_mod.py",   # written by step 2: foreseen
         "cairn/tools/base/plan.py",      # under a path step 2 reads: foreseen
         "skills/x/mod.py",               # in bounds.in: foreseen
         "skills/y/other.py",             # named by nothing: a miss
         "cairn/tools/base_other.py"]     # a sibling of a foreseen dir, not under it: a miss
MISSES = ["skills/y/other.py", "cairn/tools/base_other.py"]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _calls() -> list[dict]:
    return [{"name": "Read", "input": {"file_path": ROOT + p}, "at": f"2026-11-14T10:0{i}:00Z"}
            for i, p in enumerate(READS)]


def _decisions() -> dict:
    return {"id": TID, "bounds": BOUNDS,
            "decisions": [{"n": i, "text": f"D{i}", "writes_to": w, "reads": r}
                          for i, (w, r) in enumerate(STEPS, 1)]}


def _outcomes() -> dict:
    return {"id": TID, "bounds": BOUNDS,
            "outcomes": [{"n": i, "claim": f"outcome {i} holds", "writes_to": w, "reads": r,
                          "after": [] if i == 1 else [1]}
                         for i, (w, r) in enumerate(STEPS, 1)]}


def _misses(doc: dict) -> list[tuple[str, str]]:
    from skills.sail import toolcalls
    obs = toolcalls.observe(doc, _calls(), roots={ROOT: ""})
    return [(f["path"], f["field"]) for f in obs["findings"] if f["kind"] == "miss"], obs


def test_clause_1_an_outcomes_ticket_foresees_what_its_outcomes_name() -> None:
    bad = []
    got, obs = _misses(_outcomes())
    want = [(p, "outcomes.reads") for p in MISSES]
    if got != want:
        bad.append(f"misses {got}, want {want}")
    twin, _ = _misses(_decisions())
    if [p for p, _ in got] != [p for p, _ in twin]:
        bad.append(f"miss paths differ from the decisions twin: {got} vs {twin}")
    if obs["calls"] != len(READS) or obs["by_tool"] != {"Read": len(READS)}:
        bad.append(f"counted {obs['calls']} {obs['by_tool']}")
    check("test_clause_1_an_outcomes_ticket_foresees_what_its_outcomes_name", not bad, "; ".join(bad))


def test_clause_2_a_decisions_ticket_scores_as_on_main() -> None:
    bad = []
    got, obs = _misses(_decisions())
    want = [(p, "decisions.reads") for p in MISSES]
    if got != want:
        bad.append(f"misses {got}, main gives {want}")
    if [f for f in obs["findings"] if f["kind"] != "miss"]:
        bad.append(f"a read drew a write finding: {obs['findings']}")
    check("test_clause_2_a_decisions_ticket_scores_as_on_main", not bad, "; ".join(bad))


def main() -> int:
    for fn in (test_clause_1_an_outcomes_ticket_foresees_what_its_outcomes_name,
               test_clause_2_a_decisions_ticket_scores_as_on_main):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print("RED" if FAILURES else "GREEN")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
