#!/usr/bin/env python3
"""Proof that the operator inbox shows falsifier clauses one per line (ticket 4b05529f5f49).

Measured 2026-11-05: _format_ticket prints each dict falsifier value with f'{k}: {v}', so a
falsifier {clauses: [{n, claim}]} (parent e4f02a1ceef5, Akien: "should be json") prints as
'clauses: [{...}]', a Python list repr.

  (1) a doc with falsifier {clauses: [{n:1, claim:'a'}, {n:2, claim:'b'}], horizon:'h'} renders
      lines '  (1) a', '  (2) b' and a horizon line, and no '[{' anywhere in the FALSIFIER block;
  (2) a {proves_green, proves_red} doc and a string doc render byte-identical to HEAD (the HEAD
      renderings below were measured 2026-11-05 at commit cc77054f).

    PYTHONPATH=. python3 cairn/tools/operator_inbox/proofs/test_falsifier_clauses_render_one_per_line.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

PROVES = {"4b05529f5f49": {
    "1": "test_clause_1_clauses_render_one_per_line",
    "2": "test_clause_2_standing_shapes_render_as_at_head",
}}

FAILURES: list[str] = []

_PATH = Path("/tmp/4b05-scratch.json")  # never read: measurements_since_cast rides the doc


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _render(falsifier) -> str:
    from cairn.tools.operator_inbox.inbox import _format_ticket
    return _format_ticket({"id": "x", "measurements_since_cast": [], "falsifier": falsifier}, _PATH)


def _block(out: str) -> list[str]:
    """The FALSIFIER block: from its heading to the first blank line after it."""
    lines = out.split("\n")
    i = lines.index("FALSIFIER:")
    j = lines.index("", i)
    return lines[i + 1:j]


_HEADER = ("============================================================================\n"
           "  TICKET: x\n  ?\n  class: ?   state: \n  path: /tmp/4b05-scratch.json\n"
           "============================================================================\n\n")


def test_clause_1_clauses_render_one_per_line() -> None:
    long = "the third claim " * 8
    block = _block(_render({"clauses": [{"n": 1, "claim": "a"}, {"n": 2, "claim": "b"},
                                        {"n": 3, "claim": long}],
                            "wrong_intent": "w", "horizon": "h"}))
    bad = []
    if block[:2] != ["  (1) a", "  (2) b"]:
        bad.append(f"first lines {block[:2]}")
    if not any(l.startswith("  (3) the third claim") for l in block) or any(len(l) > 76 for l in block):
        bad.append("clause 3 not wrapped at 76")
    if "  wrong_intent: w" not in block or "  horizon: h" not in block:
        bad.append("wrong_intent/horizon lines missing")
    if any("[{" in l or "clauses:" in l for l in block):
        bad.append("a list repr in the block")
    check("test_clause_1_clauses_render_one_per_line", not bad,
          f"block {block}" + (f"; failing {bad}" if bad else ""))


def test_clause_2_standing_shapes_render_as_at_head() -> None:
    want_dict = _HEADER + "FALSIFIER:\n  proves_green: g\n  proves_red: (1) a (2) b\n\n"
    want_str = _HEADER + "FALSIFIER:\n  (1) a (2) b\n\n"
    got_dict = _render({"proves_green": "g", "proves_red": "(1) a (2) b"})
    got_str = _render("(1) a (2) b")
    check("test_clause_2_standing_shapes_render_as_at_head",
          got_dict == want_dict and got_str == want_str,
          f"dict {got_dict == want_dict}, string {got_str == want_str}")


def main() -> int:
    for fn in (test_clause_1_clauses_render_one_per_line,
               test_clause_2_standing_shapes_render_as_at_head):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print(f"{'FAIL' if FAILURES else 'PASS'}: {len(FAILURES)} failing")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
