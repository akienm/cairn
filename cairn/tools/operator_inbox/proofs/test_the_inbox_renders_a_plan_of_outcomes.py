#!/usr/bin/env python3
"""Proof that the operator inbox renders a plan of outcomes, and no line carries a marker
(ticket 8f3d61c0ae47, parent 5c1e0a7d93b2, Q#100).

Measured 2026-11-14: _decisions_section reads only ``decisions`` and renders each line as
'<n>. <text> [<by>]', so an outcomes plan renders no plan at all, and a decision whose by is
absent renders '[?]'.

  (1) an outcomes ticket renders OUTCOMES: with each outcome's n and claim, an outcome with
      no claim as '<n>. awaiting judgement: <text>', and each non-empty after;
  (2) a decisions ticket with the same content renders every line's n and text as before, and
      no rendered line carries '[?]' or a ' [<by>]' suffix.

    PYTHONPATH=. python3 cairn/tools/operator_inbox/proofs/test_the_inbox_renders_a_plan_of_outcomes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

PROVES = {"8f3d61c0ae47": {
    "1": "test_clause_1_an_outcomes_plan_renders_its_outcomes",
    "2": "test_clause_2_a_decisions_plan_renders_without_a_marker",
}}

FAILURES: list[str] = []

_PATH = Path("/tmp/8f3d-scratch.json")  # never read: measurements_since_cast rides the doc

# One plan, written in both shapes with the same content.
_LINES = [
    {"n": 1, "text": "the inbox reads the plan through the one view",
     "writes_to": ["cairn/tools/operator_inbox/inbox.py"], "reads": []},
    {"n": 2, "text": "the proof renders one ticket in each shape",
     "writes_to": ["cairn/tools/operator_inbox/proofs/x.py"], "reads": []},
    {"n": 3, "text": "D3: a line the migration carried over",
     "writes_to": [], "reads": []},
]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _render(doc: dict) -> str:
    from cairn.tools.operator_inbox.inbox import _format_ticket
    return _format_ticket({"id": "x", "measurements_since_cast": [], **doc}, _PATH)


def _block(out: str, heading: str) -> list[str]:
    lines = out.split("\n")
    if heading not in lines:
        return []
    i = lines.index(heading)
    j = lines.index("", i)
    return lines[i + 1:j]


def test_clause_1_an_outcomes_plan_renders_its_outcomes() -> None:
    outcomes = [
        {"n": 1, "claim": _LINES[0]["text"], "writes_to": _LINES[0]["writes_to"], "reads": [],
         "after": []},
        {"n": 2, "claim": _LINES[1]["text"], "writes_to": _LINES[1]["writes_to"], "reads": [],
         "after": [1]},
        {"n": 3, "text": _LINES[2]["text"], "writes_to": [], "reads": [], "after": [1, 2]},
    ]
    bad = []
    for name, doc in (("v1", {"outcomes": outcomes}),
                      ("v2", {"schema_version": "ticket-v2", "outcomes": outcomes})):
        block = _block(_render(doc), "OUTCOMES:")
        want = ["  1. the inbox reads the plan through the one view",
                "  2. the proof renders one ticket in each shape (after 1)",
                "  3. awaiting judgement: D3: a line the migration carried over (after 1, 2)"]
        if block != want:
            bad.append(f"{name}: {block}")
    check("test_clause_1_an_outcomes_plan_renders_its_outcomes", not bad, "; ".join(bad))


def test_clause_2_a_decisions_plan_renders_without_a_marker() -> None:
    decisions = [dict(_LINES[0], by="cc"), dict(_LINES[1]), dict(_LINES[2], by="akien")]
    bad = []
    for name, doc in (("v1", {"decisions": decisions}),
                      ("v2", {"schema_version": "ticket-v2", "decisions": decisions})):
        out = _render(doc)
        block = _block(out, "DECISIONS:")
        want = [f"  {d['n']}. {d['text']}" for d in _LINES]
        if block != want:
            bad.append(f"{name}: {block}")
        if any("[?]" in l or l.rstrip().endswith(("[cc]", "[akien]")) for l in out.split("\n")):
            bad.append(f"{name}: a marker in {out!r}")
    check("test_clause_2_a_decisions_plan_renders_without_a_marker", not bad, "; ".join(bad))


def main() -> int:
    test_clause_1_an_outcomes_plan_renders_its_outcomes()
    test_clause_2_a_decisions_plan_renders_without_a_marker()
    print("RED" if FAILURES else "GREEN")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
