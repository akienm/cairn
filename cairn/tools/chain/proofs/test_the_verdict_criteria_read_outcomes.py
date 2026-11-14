#!/usr/bin/env python3
"""Proof that the verdict contract draws its criteria from outcomes as from falsifier clauses
(ticket 2a9b7e4c1d06, parent 5c1e0a7d93b2, Q#100).

Measured 2026-11-14: verdict_contract.falsifier_criteria reads only ``ticket['falsifier']``, so
a ticket whose plan is outcomes (no falsifier) is refused as 'carries no falsifier'.

  (1) an outcomes ticket yields one criterion per outcome with a claim, each keyed by the
      outcome's n, its claim verbatim;
  (2) a falsifier-clauses ticket and a prose-falsifier ticket yield exactly the criteria they
      yield on main (the main results below were measured 2026-11-14 at 948fdaed7).

Every ticket here lives under a scratch root (<tmp>/cairn beside <tmp>/CairnCommons/tickets);
nothing reads the live commons.

    PYTHONPATH=. python3 cairn/tools/chain/proofs/test_the_verdict_criteria_read_outcomes.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

PROVES = {"2a9b7e4c1d06": {
    "1": "test_clause_1_an_outcomes_ticket_yields_one_criterion_per_claim",
    "2": "test_clause_2_the_standing_shapes_yield_what_they_did_on_main",
}}

FAILURES: list[str] = []

_ID = "2a9b5c7a7c40"

# One plan's content: two claims, and the line the migration carried over without one.
_CLAIMS = ["the first (9) holds", "the second holds"]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _criteria(plan: dict):
    """Write one scratch ticket carrying ``plan`` and read its criteria through the contract."""
    from cairn.tools.chain.verdict_contract import falsifier_criteria
    with tempfile.TemporaryDirectory(prefix="2a9b-") as tmp:
        root = Path(tmp) / "cairn"
        tickets = Path(tmp) / "CairnCommons" / "tickets"
        root.mkdir()
        tickets.mkdir(parents=True)
        (tickets / f"{_ID}-scratch-plan-ticket.json").write_text(
            json.dumps({"id": _ID, "title": "scratch plan ticket", **plan}))
        return falsifier_criteria(_ID, str(root))


def _want(pairs) -> list[dict]:
    return [{"claim": c, "source": f"falsifier@{_ID} clause ({n})"} for n, c in pairs]


def test_clause_1_an_outcomes_ticket_yields_one_criterion_per_claim() -> None:
    bad = []
    full = [{"n": i, "claim": c, "writes_to": [], "reads": [], "after": []}
            for i, c in enumerate(_CLAIMS, 1)]
    crit, err = _criteria({"outcomes": full})
    if err is not None or crit != _want(enumerate(_CLAIMS, 1)):
        bad.append(f"two claims -> {crit} {err!r}")
    # an outcome still awaiting its claim owes no criterion; the others keep their own n
    mig = [{"n": 1, "text": "D1: migrated", "writes_to": [], "reads": [], "after": []},
           {"n": 2, "claim": _CLAIMS[1], "writes_to": [], "reads": [], "after": [1]}]
    crit, err = _criteria({"outcomes": mig})
    if err is not None or crit != _want([(2, _CLAIMS[1])]):
        bad.append(f"one awaiting -> {crit} {err!r}")
    # an outcomes plan with no claim at all owes nothing a verdict could answer: refused
    crit, err = _criteria({"outcomes": mig[:1]})
    if crit or not err or _ID not in err:
        bad.append(f"none claimed -> {crit} {err!r}")
    check("test_clause_1_an_outcomes_ticket_yields_one_criterion_per_claim", not bad,
          "; ".join(bad))


def test_clause_2_the_standing_shapes_yield_what_they_did_on_main() -> None:
    bad = []
    crit, err = _criteria({"falsifier": {"clauses": [{"n": i, "claim": c}
                                                     for i, c in enumerate(_CLAIMS, 1)]}})
    if err is not None or crit != _want(enumerate(_CLAIMS, 1)):
        bad.append(f"clauses -> {crit} {err!r}")
    crit, err = _criteria({"falsifier": "(1) a (2) b"})
    if err is not None or crit != _want([(1, "a"), (2, "b")]):
        bad.append(f"prose -> {crit} {err!r}")
    crit, err = _criteria({"falsifier": {"proves_green": "g", "proves_red": "(1) a (2) b"}})
    if err is not None or crit != _want([(1, "a"), (2, "b")]):
        bad.append(f"proves_red -> {crit} {err!r}")
    # the refusals main gives stand as they were
    for label, fal, says in (("clauses []", {"clauses": []}, "carries no falsifier clauses"),
                             ("numbering [2]", {"clauses": [{"n": 2, "claim": "x"}]}, "not 1..1"),
                             ("no falsifier", None, "carries no falsifier")):
        crit, err = _criteria({} if fal is None else {"falsifier": fal})
        if crit or not err or says not in err:
            bad.append(f"{label} -> {crit} {err!r}")
    check("test_clause_2_the_standing_shapes_yield_what_they_did_on_main", not bad,
          "; ".join(bad))


def main() -> int:
    for fn in (test_clause_1_an_outcomes_ticket_yields_one_criterion_per_claim,
               test_clause_2_the_standing_shapes_yield_what_they_did_on_main):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print("RED" if FAILURES else "GREEN")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
