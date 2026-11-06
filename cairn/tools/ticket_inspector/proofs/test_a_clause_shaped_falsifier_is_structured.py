#!/usr/bin/env python3
"""Proof that ticket_inspector reads a clause-shaped falsifier as structured (ticket 660352d41cb7).

Measured 2026-11-05: inspector.py's FALSIFIER STRUCTURE block reds any dict falsifier that does
not carry proves_green and proves_red, so a ticket whose falsifier is the new clause list
{clauses: [{n, claim}]} (parent e4f02a1ceef5, Akien: "should be json") would red here.

  (1) {clauses: [{n:1, claim:'x'}, {n:2, claim:'y'}]} yields no falsifier_structure finding;
  (2) clauses empty, a blank claim, or numbering [1, 3] each yields one falsifier_structure
      finding naming it;
  (3) a {proves_green, proves_red} falsifier and a string falsifier read as before.

    PYTHONPATH=. python3 cairn/tools/ticket_inspector/proofs/test_a_clause_shaped_falsifier_is_structured.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

PROVES = {"660352d41cb7": {
    "1": "test_clause_1_a_well_formed_clause_list_is_structured",
    "2": "test_clause_2_a_malformed_clause_list_is_named",
    "3": "test_clause_3_the_standing_shapes_read_as_before",
}}

FAILURES: list[str] = []

_BASE = {
    "id": "a1b2c3d4e5f6",
    "title": "fixture: a clause-shaped falsifier",
    "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED",
    "intention": "a fixture intention",
    "why": "a fixture reason",
    "node_class": "code-seam",
    "traces_to": ["Law 3"],
    "how": "build the thing",
    "children": [],
    "sorted_berth": "none, because test fixture",
    "intent_berth": "none, because test fixture",
    "chart_claim": "none, because test fixture",
}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _structure_findings(falsifier) -> list[dict]:
    from cairn.tools.ticket_inspector.inspector import inspect_ticket
    t = dict(_BASE, falsifier=falsifier)
    return [f for f in inspect_ticket(t) if f["check"] == "falsifier_structure"]


def test_clause_1_a_well_formed_clause_list_is_structured() -> None:
    ff = _structure_findings({"clauses": [{"n": 1, "claim": "x"}, {"n": 2, "claim": "y"}]})
    check("clause_1: a well-formed clause list yields no falsifier_structure finding",
          ff == [], str(ff))


def test_clause_2_a_malformed_clause_list_is_named() -> None:
    cases = {
        "empty": ({"clauses": []}, ("clauses",)),
        "blank claim": ({"clauses": [{"n": 1, "claim": "x"}, {"n": 2, "claim": "  "}]},
                        ("claim", "2")),
        "numbering [1, 3]": ({"clauses": [{"n": 1, "claim": "x"}, {"n": 3, "claim": "y"}]},
                             ("3",)),
    }
    for label, (fals, words) in cases.items():
        ff = _structure_findings(fals)
        text = " ".join(f["finding"] for f in ff)
        ok = len(ff) == 1 and all(w in text for w in words) and "proves_" not in text
        check(f"clause_2: {label} yields one falsifier_structure finding naming it",
              ok, str(ff))


def test_clause_3_the_standing_shapes_read_as_before() -> None:
    ff = _structure_findings({"proves_green": "g", "proves_red": "r"})
    check("clause_3: a {proves_green, proves_red} falsifier is clean", ff == [], str(ff))
    ff = _structure_findings({"proves_green": "g"})
    check("clause_3: a dict missing proves_red still reds on falsifier.proves_red",
          len(ff) == 1 and "proves_red" in ff[0]["finding"], str(ff))
    ff = _structure_findings("a prose falsifier")
    check("clause_3: a string falsifier yields no falsifier_structure finding", ff == [], str(ff))


def main() -> int:
    for fn in (test_clause_1_a_well_formed_clause_list_is_structured,
               test_clause_2_a_malformed_clause_list_is_named,
               test_clause_3_the_standing_shapes_read_as_before):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print(f"{'FAIL' if FAILURES else 'PASS'}: {len(FAILURES)} failing")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
