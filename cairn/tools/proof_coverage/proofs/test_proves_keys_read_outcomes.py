#!/usr/bin/env python3
"""Proof that proof coverage keys a proof's PROVES on outcome numbers as on clause numbers
(ticket 6e41b8d2f0a3, parent 5c1e0a7d93b2, Q#100).

Measured 2026-11-14: proof_coverage.clauses reads only ``ticket['falsifier']`` and the
decisions' text, so an outcomes ticket (no falsifier) owes no key at all and ``lacks`` refuses
it as 'the falsifier is empty or unreadable'. proof_coverage holds no writes set read from the
plan: its ``_writes_to`` reads the decompose berth's ``writes_to``, which this ticket does not
reach.

  (1) an outcomes ticket's keys are the n of its outcomes with a claim (an outcome awaiting
      its claim owes none), a migrated outcome's text still adds a clause by the decide-line
      convention, and ``lacks`` no longer refuses it for having no clauses;
  (2) a falsifier-clauses ticket, a prose falsifier, a lettered one, a flat one and a decide
      line that adds a clause give exactly the keys main gives (measured 2026-11-14 at
      2f64a7b02).

Nothing here reads the live commons: ``clauses`` is a pure read of the ticket dict, and the one
``lacks`` call is handed a scratch world for its roots.

    PYTHONPATH=. python3 cairn/tools/proof_coverage/proofs/test_proves_keys_read_outcomes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"6e41b8d2f0a3": {
    "1": "test_clause_1_an_outcomes_ticket_keys_on_its_claimed_outcomes",
    "2": "test_clause_2_the_old_shapes_key_as_on_main",
}}

FAILURES: list[str] = []
_ID = "6e415c7a7c40"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _o(n, claim=None, text=None, after=()):
    o = {"n": n, "writes_to": [], "reads": [], "after": list(after)}
    if claim is not None:
        o["claim"] = claim
    if text is not None:
        o["text"] = text
    return o


def test_clause_1_an_outcomes_ticket_keys_on_its_claimed_outcomes() -> None:
    from cairn.tools.proof_coverage import proof_coverage as pc
    from cairn.tools.scratch.scratch import scratch_dir
    bad = []
    full = {"id": _ID, "outcomes": [_o(1, "a holds"), _o(2, "b holds"), _o(3, "c holds")]}
    if pc.clauses(full) != ["1", "2", "3"]:
        bad.append(f"three claims -> {pc.clauses(full)}")
    mig = {"id": _ID, "outcomes": [_o(1, text="D1: migrated, awaiting its claim"),
                                   _o(2, "b holds", after=[1])]}
    if pc.clauses(mig) != ["2"]:
        bad.append(f"one awaiting -> {pc.clauses(mig)}")
    added = {"id": _ID, "outcomes": [
        _o(1, "a holds"),
        _o(2, text="D2: falsifier clause (4) is added by this line, and nothing else")]}
    if pc.clauses(added) != ["1", "4"]:
        bad.append(f"migrated decide line -> {pc.clauses(added)}")
    # through the gate: an outcomes ticket with claims is not refused for having no clauses
    w = scratch_dir("testing-6e41b8d2f0a3-")
    (w / "cairn").mkdir()
    (w / "CairnCommons" / "tickets").mkdir(parents=True)
    got = pc.lacks(full, repo_root=w / "cairn",
                   roots={"repo": w / "cairn", "commons": w / "CairnCommons"})
    if any(lk.get("kind") == "falsifier_has_clauses" for lk in got):
        bad.append(f"lacks refused it as clauseless: {[lk.get('kind') for lk in got]}")
    check("test_clause_1_an_outcomes_ticket_keys_on_its_claimed_outcomes", not bad, "; ".join(bad))


def test_clause_2_the_old_shapes_key_as_on_main() -> None:
    from cairn.tools.proof_coverage import proof_coverage as pc
    bad = []
    cases = [
        ("clauses", {"falsifier": {"clauses": [{"n": 1, "claim": "x"}, {"n": 2, "claim": "y"}]}},
         ["1", "2"]),
        ("prose", {"falsifier": "(1) a holds (2) b holds"}, ["1", "2"]),
        ("proves_red", {"falsifier": {"proves_green": "g", "proves_red": "(1) a (2) b (3) c"}},
         ["1", "2", "3"]),
        ("lettered", {"falsifier": "(a) one (b) two"}, ["a", "b"]),
        ("flat", {"falsifier": "it works"}, [pc.WHOLE]),
        ("decide adds", {"falsifier": "(1) a",
                         "decisions": [{"n": 1, "text": "D1: falsifier clause (2) is added by "
                                                        "this line", "writes_to": [], "reads": []}]},
         ["1", "2"]),
        ("decide cites", {"falsifier": "(1) a",
                          "decisions": [{"n": 1, "text": "D1: see (3)", "writes_to": [],
                                         "reads": []}]}, ["1"]),
        ("none", {}, []),
    ]
    for label, doc, want in cases:
        got = pc.clauses({"id": _ID, **doc})
        if got != want:
            bad.append(f"{label} -> {got}, main gives {want}")
    check("test_clause_2_the_old_shapes_key_as_on_main", not bad, "; ".join(bad))


def main() -> int:
    for fn in (test_clause_1_an_outcomes_ticket_keys_on_its_claimed_outcomes,
               test_clause_2_the_old_shapes_key_as_on_main):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print("RED" if FAILURES else "GREEN")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
