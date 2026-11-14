#!/usr/bin/env python3
"""Proof that the ticket inspector checks an outcomes plan's claims as it checks falsifier
clauses (ticket 71ad4e06c9b5, parent 5c1e0a7d93b2, Q#100).

Measured 2026-11-14 at 2f64a7b02: inspect_ticket reads ``t.get("falsifier")`` alone, so an
outcomes ticket (no falsifier) draws "falsifier is empty or missing" under required_fields, its
outcomes are never judged, and an outcome awaiting its claim is not named at all.

  (1) an outcomes ticket draws exactly the findings its clauses twin draws (same content, the
      claims on outcomes instead of falsifier.clauses); outcomes misnumbered or empty are named
      under falsifier_structure as clauses are; and a no-claim outcome is named under
      outcome_awaiting_judgement with its n — never as malformed, never as a missing falsifier;
  (2) a falsifier-clauses ticket and a prose-falsifier ticket get the findings they get on main
      (measured 2026-11-14 at 2f64a7b02): well-formed clauses and prose draw no
      falsifier_structure, clauses numbered [1, 3] draw one, no falsifier at all draws
      required_fields, and no old-shape ticket is named awaiting judgement.

inspect_ticket is a pure read of the ticket dict; the only disk it touches is node_classes/
under the commons root, the same for every twin, so the comparisons hold whatever it finds.

    PYTHONPATH=. python3 cairn/tools/ticket_inspector/proofs/test_the_ticket_inspector_reads_outcomes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"71ad4e06c9b5": {
    "1": "test_clause_1_an_outcomes_ticket_is_judged_over_its_claims",
    "2": "test_clause_2_the_old_shapes_get_mains_findings",
}}

FAILURES: list[str] = []

_BASE = {
    "id": "71ad5c7a7c40",
    "title": "fixture: a plan in either shape",
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
_CLAIMS = ["the reader sees every claim", "the old shape reads as before"]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _find(**plan) -> list[dict]:
    from cairn.tools.ticket_inspector.inspector import inspect_ticket
    return inspect_ticket(dict(_BASE, **plan))


def _checks(ff) -> list[str]:
    return sorted(f["check"] for f in ff)


def _o(n, claim=None, text=None):
    o = {"n": n, "writes_to": [], "reads": [], "after": []}
    if claim is not None:
        o["claim"] = claim
    if text is not None:
        o["text"] = text
    return o


def _clauses(ns, claims=_CLAIMS):
    return {"clauses": [{"n": n, "claim": c} for n, c in zip(ns, claims)]}


def test_clause_1_an_outcomes_ticket_is_judged_over_its_claims() -> None:
    bad = []
    # the twins: same claims, two shapes
    twin = _find(falsifier=_clauses([1, 2]))
    new = _find(outcomes=[_o(1, _CLAIMS[0]), _o(2, _CLAIMS[1])])
    if new != twin:
        bad.append(f"well-formed: outcomes {_checks(new)} vs clauses {_checks(twin)}")
    # misnumbered, as clauses [1, 3] are
    mis = _find(outcomes=[_o(1, _CLAIMS[0]), _o(3, _CLAIMS[1])])
    mis_fs = [f for f in mis if f["check"] == "falsifier_structure"]
    if len(mis_fs) != 1 or "n=3" not in mis_fs[0]["finding"]:
        bad.append(f"outcomes [1, 3] -> {[f['finding'] for f in mis_fs]}")
    # empty
    empty = _find(outcomes=[])
    if [f["check"] for f in empty if f["check"] == "falsifier_structure"] != ["falsifier_structure"]:
        bad.append(f"empty outcomes -> {_checks(empty)}")
    # one awaiting its claim: named awaiting, with its n, and nothing else beyond the twin's
    wait = _find(outcomes=[_o(1, text="D1: migrated, awaiting its claim"), _o(2, _CLAIMS[1])])
    aw = [f for f in wait if f["check"] == "outcome_awaiting_judgement"]
    if len(aw) != 1 or aw[0]["evidence"].get("awaiting") != [1]:
        bad.append(f"awaiting -> {aw}")
    rest = [f for f in wait if f["check"] != "outcome_awaiting_judgement"]
    if rest != twin:
        bad.append(f"an awaiting outcome drew more than the name: {_checks(rest)} vs {_checks(twin)}")
    check("test_clause_1_an_outcomes_ticket_is_judged_over_its_claims", not bad, "; ".join(bad))


def test_clause_2_the_old_shapes_get_mains_findings() -> None:
    bad = []
    cases = [
        ("clauses", {"falsifier": _clauses([1, 2])}, 0, 0),
        ("clauses [1, 3]", {"falsifier": _clauses([1, 3])}, 1, 0),
        ("prose", {"falsifier": "(1) " + _CLAIMS[0] + " (2) " + _CLAIMS[1]}, 0, 0),
        ("no falsifier", {}, 0, 1),
    ]
    for label, plan, want_fs, want_req in cases:
        ff = _find(**plan)
        fs = sum(1 for f in ff if f["check"] == "falsifier_structure")
        req = sum(1 for f in ff if f["check"] == "required_fields"
                  and f["evidence"].get("field") == "falsifier")
        aw = sum(1 for f in ff if f["check"] == "outcome_awaiting_judgement")
        if (fs, req, aw) != (want_fs, want_req, 0):
            bad.append(f"{label}: structure {fs}, missing-falsifier {req}, awaiting {aw}; "
                       f"main gives {want_fs}, {want_req}, 0")
    check("test_clause_2_the_old_shapes_get_mains_findings", not bad, "; ".join(bad))


def main() -> int:
    for fn in (test_clause_1_an_outcomes_ticket_is_judged_over_its_claims,
               test_clause_2_the_old_shapes_get_mains_findings):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print("RED" if FAILURES else "GREEN")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
