#!/usr/bin/env python3
"""Proof that the verdict contract derives criteria from a clause-shaped falsifier (ticket e6cac10b0297).

Measured 2026-11-05: verdict_contract.falsifier_criteria reads proves_red from a dict falsifier and
segments it by regex, so a falsifier {clauses: [{n, claim}]} (parent e4f02a1ceef5, Akien: "should
be json") has no proves_red and is refused as 'carries no falsifier'.

  (1) a scratch ticket with two clauses yields two criteria, claims verbatim, sources
      'falsifier@<id> clause (1)' and '(2)';
  (2) clauses [] and numbering [2] are each refused with an error naming the ticket;
  (3) a scratch ticket with a string falsifier '(1) a (2) b' yields what it yields at HEAD.

Every ticket here lives under a scratch root (<tmp>/cairn beside <tmp>/CairnCommons/tickets);
nothing reads the live commons.

    PYTHONPATH=. python3 cairn/tools/chain/proofs/test_criteria_come_from_falsifier_clauses.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

PROVES = {"e6cac10b0297": {
    "1": "test_clause_1_two_clauses_yield_two_criteria",
    "2": "test_clause_2_a_malformed_clause_list_is_refused_naming_the_ticket",
    "3": "test_clause_3_a_string_falsifier_yields_what_it_did_at_head",
}}

FAILURES: list[str] = []

_ID = "c1a05e5ca1e0"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _criteria(falsifier):
    """Write one scratch ticket carrying ``falsifier`` and read its criteria through the contract."""
    from cairn.tools.chain.verdict_contract import falsifier_criteria
    with tempfile.TemporaryDirectory(prefix="e6ca-") as tmp:
        root = Path(tmp) / "cairn"
        tickets = Path(tmp) / "CairnCommons" / "tickets"
        root.mkdir()
        tickets.mkdir(parents=True)
        (tickets / f"{_ID}-scratch-clause-ticket.json").write_text(
            json.dumps({"id": _ID, "title": "scratch clause ticket", "falsifier": falsifier}))
        return falsifier_criteria(_ID, str(root))


def test_clause_1_two_clauses_yield_two_criteria() -> None:
    crit, err = _criteria({"clauses": [{"n": 1, "claim": "the first (9) holds"},
                                       {"n": 2, "claim": "the second holds"}]})
    want = [{"claim": "the first (9) holds", "source": f"falsifier@{_ID} clause (1)"},
            {"claim": "the second holds", "source": f"falsifier@{_ID} clause (2)"}]
    check("test_clause_1_two_clauses_yield_two_criteria", err is None and crit == want,
          f"criteria {crit}, error {err!r}")


def test_clause_2_a_malformed_clause_list_is_refused_naming_the_ticket() -> None:
    bad = []
    # Each refusal must name the ticket AND the lack it actually has: a list that carries
    # clauses is not refused as 'carries no falsifier', which is what HEAD says of all three.
    for label, fal, says in (("clauses []", {"clauses": []}, "no"),
                             ("numbering [2]", {"clauses": [{"n": 2, "claim": "only two"}]}, "1..1"),
                             ("a blank claim", {"clauses": [{"n": 1, "claim": "  "}]}, "clause (1)")):
        crit, err = _criteria(fal)
        if crit or not err or _ID not in err or says not in err:
            bad.append(f"{label}: criteria {crit}, error {err!r}")
    check("test_clause_2_a_malformed_clause_list_is_refused_naming_the_ticket", not bad,
          "each malformed list refuses naming the ticket" + (f"; failing {bad}" if bad else ""))


def test_clause_3_a_string_falsifier_yields_what_it_did_at_head() -> None:
    crit, err = _criteria("(1) a (2) b")
    want = [{"claim": "a", "source": f"falsifier@{_ID} clause (1)"},
            {"claim": "b", "source": f"falsifier@{_ID} clause (2)"}]
    crit2, err2 = _criteria({"proves_green": "g", "proves_red": "(1) a (2) b"})
    check("test_clause_3_a_string_falsifier_yields_what_it_did_at_head",
          err is None and crit == want and err2 is None and crit2 == want,
          f"string -> {crit} {err!r}; proves_red dict -> {crit2} {err2!r}")


def main() -> int:
    for fn in (test_clause_1_two_clauses_yield_two_criteria,
               test_clause_2_a_malformed_clause_list_is_refused_naming_the_ticket,
               test_clause_3_a_string_falsifier_yields_what_it_did_at_head):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print(f"{'FAIL' if FAILURES else 'PASS'}: {len(FAILURES)} failing")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
