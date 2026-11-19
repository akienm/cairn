#!/usr/bin/env python3
"""Proof that the build inspector's fidelity read takes an outcomes plan as it takes falsifier
clauses (ticket d07c3f9a2b58, parent 5c1e0a7d93b2, Q#100).

Measured 2026-11-14: intention_fidelity keys a ticket on ``t.get("falsifier")`` alone, so an
outcomes ticket (no falsifier) yields no keywords and is silently dropped from every pairing.
The inspector holds no other plan read this ticket's shape change reaches: the FIXME-answers
ledger (every_fixme_entry_is_answered) keys on rehearsal's ``step: "FIXME n"`` answers, which
are not plan steps.

  (1) an outcomes ticket's fidelity keywords, and the findings they draw, equal those of the
      same content written as falsifier clauses; an outcome still awaiting its claim adds none;
  (2) an old-shape ticket's keywords are what main computes from its falsifier as written
      (clauses dict and prose), and a ticket with no claim at all pairs with nothing.

The keywords are read off the inspector's own call: ``_fidelity_keywords`` is wrapped for the
duration of one sieve call and the set it returns for the ticket is recorded. Every world is a
scratch cairn root with a CairnCommons/tickets beside it.

    PYTHONPATH=. python3 cairn/devices/codemother/machines/build_inspector/proofs/test_the_build_gates_read_outcomes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"d07c3f9a2b58": {
    "1": "test_clause_1_an_outcomes_ticket_reads_as_its_clauses",
    "2": "test_clause_2_the_old_shapes_read_as_on_main",
}}

FAILURES: list[str] = []

_CLAIMS = ["the sieve reads every outcome claim through the plan view",
           "a migrated decision carries forward without a claim"]
# Unrelated to the claims, so the pairing reds (coverage 0, invented 1.0): findings to compare.
_CHARTER = "Bananas ripen yellow quickly overnight"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _read(ticket_plan: dict) -> tuple[list, list]:
    """One scratch world holding one ticket carrying ``ticket_plan``; returns (the keyword sets
    the sieve computed for the ticket, the findings)."""
    from cairn.devices.codemother.machines.build_inspector import inspector
    from cairn.tools.scratch.scratch import scratch_dir
    w = scratch_dir("testing-d07c3f9a2b58-")
    comp = w / "cairn" / "cairn" / "machines" / "fixture_comp"
    comp.mkdir(parents=True)
    (comp / "intention+why.json").write_text(json.dumps(
        {"intention": "fixture", "why": "fixture", "falsifier": _CHARTER}))
    tickets = w / "CairnCommons" / "tickets"
    tickets.mkdir(parents=True)
    (tickets / "d07c5c7a7c40-fixture.json").write_text(json.dumps(
        {"id": "d07c5c7a7c40", "title": "fixture",
         "owning_intention": "cairn/machines/fixture_comp/intention+why.json", **ticket_plan}))
    row = {"component": "fixture_comp", "dir": "machines/fixture_comp", "charter_on_disk": True}
    seen, real = [], inspector._fidelity_keywords
    inspector._fidelity_keywords = lambda v: (lambda r: (seen.append(r), r)[1])(real(v))
    try:
        found = inspector.intention_fidelity(row, comp)
    finally:
        inspector._fidelity_keywords = real
    # the first call is the charter's; every later one is the ticket's
    return seen[1:], [(f.get("about"), f.get("actual")) for f in found]


def _kw(value) -> set:
    from cairn.devices.codemother.machines.build_inspector import inspector
    return inspector._fidelity_keywords(value)


def test_clause_1_an_outcomes_ticket_reads_as_its_clauses() -> None:
    bad = []
    old = {"falsifier": {"clauses": [{"n": i, "claim": c} for i, c in enumerate(_CLAIMS, 1)]}}
    new = {"outcomes": [{"n": i, "claim": c, "writes_to": [], "reads": [], "after": []}
                        for i, c in enumerate(_CLAIMS, 1)]}
    k_old, f_old = _read(old)
    k_new, f_new = _read(new)
    if not k_old or not k_old[0] or not f_old:
        bad.append(f"the clauses ticket drew nothing to compare: {k_old} {f_old}")
    if k_new != k_old:
        bad.append(f"keywords differ: outcomes {k_new} vs clauses {k_old}")
    if f_new != f_old:
        bad.append(f"findings differ: outcomes {f_new} vs clauses {f_old}")
    # an outcome awaiting its claim adds no words: the plan reads as its one claimed clause
    mig = {"outcomes": [{"n": 1, "text": "D1: zeppelin migrated text", "writes_to": [],
                         "reads": [], "after": []},
                        {"n": 2, "claim": _CLAIMS[1], "writes_to": [], "reads": [], "after": [1]}]}
    k_mig, _ = _read(mig)
    want = _kw({"clauses": [{"n": 2, "claim": _CLAIMS[1]}]})
    if k_mig != [want]:
        bad.append(f"one awaiting -> {k_mig}, want [{want}]")
    check("test_clause_1_an_outcomes_ticket_reads_as_its_clauses", not bad, "; ".join(bad))


def test_clause_2_the_old_shapes_read_as_on_main() -> None:
    bad = []
    for label, fal in (("clauses", {"clauses": [{"n": 1, "claim": _CLAIMS[0]}]}),
                       ("prose", "(1) " + _CLAIMS[0] + " (2) " + _CLAIMS[1])):
        k, f = _read({"falsifier": fal})
        if k != [_kw(fal)] or not f:
            bad.append(f"{label} -> {k} {f}, want [{_kw(fal)}] and a finding")
    # a decisions plan beside its falsifier: the decisions do not enter the keywords
    k, _ = _read({"falsifier": "(1) " + _CLAIMS[0],
                  "decisions": [{"n": 1, "text": "D1: zeppelin", "writes_to": [], "reads": []}]})
    if k != [_kw("(1) " + _CLAIMS[0])]:
        bad.append(f"decisions beside -> {k}")
    # nothing claimed, either shape: no words, so no pair and no finding
    for label, doc in (("no falsifier", {}),
                       ("outcomes, none claimed", {"outcomes": [{"n": 1, "text": "D1: x",
                                                                 "writes_to": [], "reads": [],
                                                                 "after": []}]})):
        k, f = _read(doc)
        if any(k) or f:
            bad.append(f"{label} -> {k} {f}")
    check("test_clause_2_the_old_shapes_read_as_on_main", not bad, "; ".join(bad))


def main() -> int:
    for fn in (test_clause_1_an_outcomes_ticket_reads_as_its_clauses,
               test_clause_2_the_old_shapes_read_as_on_main):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print("RED" if FAILURES else "GREEN")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
