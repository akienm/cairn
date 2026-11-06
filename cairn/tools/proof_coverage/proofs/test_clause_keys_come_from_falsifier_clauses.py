#!/usr/bin/env python3
"""Proof that proof_coverage reads clause keys from a clause-shaped falsifier (ticket ab32ccdc4504).

Measured 2026-11-05: proof_coverage.py's _falsifier_clauses reads proves_red text and segments it
by (N) and lettered-run regex, so a falsifier {clauses: [{n, claim}]} (parent e4f02a1ceef5,
Akien: "should be json") has no proves_red and keys as [] — every tooth a proof declares for it
would read as covering nothing.

  (1) a falsifier {clauses: [{n:1}, {n:2}, {n:3}]} keys ['1', '2', '3'], read as data;
  (2) a decide line 'falsifier clause (4) is added by this line' still adds '4' on such a ticket;
  (3) over every ticket in CairnCommons/tickets/ whose falsifier carries no clauses, the keys
      equal those at HEAD of the red-first commit (fixtures/clause_keys_at_head.json);
  (4) the clause key the ticket's own prose cites as "(4)": an added key lands after the
      falsifier's own keys exactly once, even when the decide line repeats it.

    PYTHONPATH=. python3 cairn/tools/proof_coverage/proofs/test_clause_keys_come_from_falsifier_clauses.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

PROVES = {"ab32ccdc4504": {
    "1": "test_clause_1_clause_keys_are_read_as_data",
    "2": "test_clause_2_a_decide_line_still_adds_a_key",
    "3": "test_clause_3_standing_shapes_key_as_at_head",
    "4": "test_clause_4_an_added_key_lands_once_after_the_falsifiers",
}}

SNAPSHOT = Path(__file__).resolve().parent / "fixtures" / "clause_keys_at_head.json"

FAILURES: list[str] = []

_CLAUSES = {"clauses": [{"n": 1, "claim": "a holds"}, {"n": 2, "claim": "b (7) holds"},
                        {"n": 3, "claim": "c holds"}]}
_ADDS = "A falsifier clause (4) is added by this line: d holds."


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _ticket(falsifier, decisions=()) -> dict:
    return {"id": "a1b2c3d4e5f6", "falsifier": falsifier,
            "decisions": [{"n": i, "text": t, "by": "cc"} for i, t in enumerate(decisions, 1)]}


def _fhash(falsifier) -> str:
    return hashlib.sha256(json.dumps(falsifier, sort_keys=True).encode()).hexdigest()[:16]


def _tickets_dir() -> Path:
    """The live commons beside this checkout, else the home one — hollow's /tmp worktree has
    no CairnCommons sibling, and a repo-relative read would red at HEAD there."""
    beside = _REPO.parent / "CairnCommons" / "tickets"
    return beside if beside.is_dir() else Path.home() / "dev" / "src" / "CairnCommons" / "tickets"


def _standing_tickets():
    from cairn.tools.base import ticket_file
    for f in ticket_file.plans(_tickets_dir()):
        try:
            t = ticket_file.read_ticket(f)
        except (json.JSONDecodeError, OSError):
            continue
        fal = t.get("falsifier")
        if isinstance(fal, dict) and "clauses" in fal:
            continue
        yield t


def take_snapshot() -> None:
    """Run once, in the red-first commit: the keys every no-clauses ticket reads at HEAD."""
    from cairn.tools.proof_coverage import proof_coverage as pc
    snap = {t["id"]: {"falsifier_sha": _fhash(t.get("falsifier")), "keys": pc.clauses(t)}
            for t in _standing_tickets() if isinstance(t.get("id"), str)}
    SNAPSHOT.write_text(json.dumps(snap, indent=1, sort_keys=True) + "\n")
    print(f"snapshot: {len(snap)} tickets -> {SNAPSHOT}")


def test_clause_1_clause_keys_are_read_as_data() -> None:
    from cairn.tools.proof_coverage import proof_coverage as pc
    keys = pc.clauses(_ticket(_CLAUSES))
    check("test_clause_1_clause_keys_are_read_as_data", keys == ["1", "2", "3"],
          f"clauses {{n:1,2,3}} key {keys} (the '(7)' inside a claim is not a key)")


def test_clause_2_a_decide_line_still_adds_a_key() -> None:
    from cairn.tools.proof_coverage import proof_coverage as pc
    keys = pc.clauses(_ticket(_CLAUSES, [_ADDS]))
    check("test_clause_2_a_decide_line_still_adds_a_key", "4" in keys and keys[:3] == ["1", "2", "3"],
          f"with the decide line the keys are {keys}")


def test_clause_3_standing_shapes_key_as_at_head() -> None:
    from cairn.tools.proof_coverage import proof_coverage as pc
    snap = json.loads(SNAPSHOT.read_text())
    compared, moved = 0, []
    for t in _standing_tickets():
        s = snap.get(t.get("id"))
        if not s or s["falsifier_sha"] != _fhash(t.get("falsifier")):
            continue  # cast or amended since the snapshot: nothing at HEAD to compare against
        compared += 1
        now = pc.clauses(t)
        if now != s["keys"]:
            moved.append(f"{t['id']}: {s['keys']} -> {now}")
    ok = not moved and compared >= 0.9 * len(snap) and compared > 100
    check("test_clause_3_standing_shapes_key_as_at_head", ok,
          f"{compared} of {len(snap)} snapshot tickets compared, {len(moved)} moved {moved[:5]}")


def test_clause_4_an_added_key_lands_once_after_the_falsifiers() -> None:
    from cairn.tools.proof_coverage import proof_coverage as pc
    keys = pc.clauses(_ticket(_CLAUSES, [_ADDS, _ADDS]))
    check("test_clause_4_an_added_key_lands_once_after_the_falsifiers", keys == ["1", "2", "3", "4"],
          f"two decide lines adding (4) key {keys}")


def main() -> int:
    if "--snapshot" in sys.argv:
        take_snapshot()
        return 0
    for fn in (test_clause_1_clause_keys_are_read_as_data,
               test_clause_2_a_decide_line_still_adds_a_key,
               test_clause_3_standing_shapes_key_as_at_head,
               test_clause_4_an_added_key_lands_once_after_the_falsifiers):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print(f"{'FAIL' if FAILURES else 'PASS'}: {len(FAILURES)} failing")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
