#!/usr/bin/env python3
"""Proof that the chart's validate door refuses a claimed chart whose proofs leave a falsifier clause undeclared (4661ca005242).

WHAT IT PROVES, and the reason is a rule held as memory that failed three times
(50ad391f4e95, 693e9f45e6f2, 5f217a2d4bd6): a proof's PROVES keys disagreed with the
falsifier's clause markers, and the disagreement surfaced only at hollow or clearance.
The rule mirrors clearance's (proof_coverage.lacks: the union over the proofs, extra keys
allowed), as Akien agreed in open-514724f8ec30: every clause of the claimed ticket's
falsifier has a PROVES tooth in some proof the chart's criteria instruments run.

Teeth, one per falsifier clause (PROVES below), over a scratch world (tmp/repo beside
tmp/CairnCommons/tickets, so grammar.ticket_path resolves the fixture ticket):
  (1) a falsifier with no (N) markers (clause 'all') against a proof declaring '1','2' is
      refused, the refusal naming the entry, the declared keys and the clauses;
  (2) a proof declaring exactly the clauses passes the entry;
  (3) a proof declaring nothing for the ticket is refused;
  (4) two proofs, clause 1 in one and clause 2 in the other, pass the entry (the union);
  (5) a ticket whose node_class folds to concept-piece gets no entry at all (absent,
      mirroring proof_coverage.lacks, which proves a concept-piece by its review record):
      the fixture is 3fef5a02da2d's shape, numbered clauses and a criterion proof that
      declares nothing for the ticket, with the class typed in mixed case.

    bin/cairn test cairn/devices/codemother/machines/validate/proofs/test_the_chart_refuses_a_clause_no_proof_it_runs_declares.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

# Bound at CALL time, never at import, so a reverted subject reds the teeth instead of
# crashing the reader.
V = None  # type: ignore[assignment]

PROVES = {"4661ca005242": {
    "1": "test_an_all_clause_against_numbered_keys_is_refused",
    "2": "test_keys_equal_to_the_clauses_pass",
    "3": "test_a_proof_declaring_nothing_for_the_ticket_is_refused",
    "4": "test_clauses_covered_by_the_union_of_two_proofs_pass",
    "5": "test_a_concept_piece_chart_gets_no_entry",
}}

ENTRY = "proves_keys_match_the_falsifier_clauses"
TID = "abcdef012345"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _world(tmp: Path, falsifier: str, proofs: dict[str, dict],
           node_class: str | None = None) -> tuple[str, dict]:
    """A repo root with the named proofs, a commons beside it holding the claimed ticket,
    and a packet whose criteria run every proof. ``proofs`` maps rel path -> PROVES."""
    root = tmp / "repo"
    tickets = tmp / "CairnCommons" / "tickets"
    tickets.mkdir(parents=True)
    doc = {"id": TID, "title": "a-proof-world", "falsifier": falsifier}
    if node_class is not None:
        doc["node_class"] = node_class
    (tickets / f"{TID}-a-proof-world.json").write_text(json.dumps(doc, indent=2) + "\n")
    criteria = []
    for rel, proves in proofs.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"PROVES = {proves!r}\n")
        criteria.append({"claim": f"{rel} is green", "instrument": f"bin/cairn test {rel}",
                         "covers": ["build the piece"]})
    packet = {"ticket": TID, "criteria": criteria, "unknowns": ["none"], "confidence": 0.9,
              "provenance": {"criteria": "cc", "unknowns": "cc"}}
    return str(root), packet


def _entry(root: str, packet: dict):
    found = [e for e in V.inspect_validate(packet, root=root) if e.get("identity") == ENTRY]
    return found[0] if found else None


def _passed(e) -> bool:
    return bool(e) and e["expected"] == e["actual"]


def _refusal(root: str, packet: dict) -> str:
    try:
        V.validate_validate(packet, root=root)
    except V.ValidateRefused as exc:
        return str(exc)
    return ""


def test_an_all_clause_against_numbered_keys_is_refused(tmp: Path) -> None:
    root, packet = _world(tmp, "Done when the door refuses it.",
                          {"x/proofs/test_a.py": {TID: {"1": "t1", "2": "t2"}}})
    e, why = _entry(root, packet), _refusal(root, packet)
    ok = e is not None and not _passed(e) and ENTRY in why and "['1', '2']" in why and "['all']" in why
    check("test_an_all_clause_against_numbered_keys_is_refused", ok,
          "no entry" if e is None else why[:200])


def test_keys_equal_to_the_clauses_pass(tmp: Path) -> None:
    root, packet = _world(tmp, "Done when (1) it refuses; (2) it passes.",
                          {"x/proofs/test_a.py": {TID: {"1": "t1", "2": "t2"}}})
    e = _entry(root, packet)
    check("test_keys_equal_to_the_clauses_pass", _passed(e), "no entry" if e is None else str(e)[:200])


def test_a_proof_declaring_nothing_for_the_ticket_is_refused(tmp: Path) -> None:
    root, packet = _world(tmp, "Done when (1) it refuses; (2) it passes.",
                          {"x/proofs/test_a.py": {"000000000000": {"1": "t1"}}})
    e, why = _entry(root, packet), _refusal(root, packet)
    check("test_a_proof_declaring_nothing_for_the_ticket_is_refused",
          e is not None and not _passed(e) and ENTRY in why, "no entry" if e is None else why[:200])


def test_clauses_covered_by_the_union_of_two_proofs_pass(tmp: Path) -> None:
    root, packet = _world(tmp, "Done when (1) it refuses; (2) it passes.",
                          {"x/proofs/test_a.py": {TID: {"1": "t1"}},
                           "y/proofs/test_b.py": {TID: {"2": "t2", "extra": "t3"}}})
    e = _entry(root, packet)
    check("test_clauses_covered_by_the_union_of_two_proofs_pass", _passed(e),
          "no entry" if e is None else str(e)[:200])


def test_a_concept_piece_chart_gets_no_entry(tmp: Path) -> None:
    # The control twin is what lets this tooth fail: the same world typed code-seam MUST get
    # the entry, refused, so a validate with no clause-coverage check at all reds here instead
    # of reading "absent" for free (F9).
    falsifier = "Done when (1) it reads; (2) it holds; (3) it names; (4) it signs."
    proofs = {"x/proofs/test_a.py": {"000000000000": {"1": "t1"}}}
    root, packet = _world(tmp / "concept", falsifier, proofs, node_class=" Concept-Piece")
    e, why = _entry(root, packet), _refusal(root, packet)
    croot, cpacket = _world(tmp / "control", falsifier, proofs, node_class="code-seam")
    ce, cwhy = _entry(croot, cpacket), _refusal(croot, cpacket)
    ok = e is None and ENTRY not in why and ce is not None and not _passed(ce) and ENTRY in cwhy
    check("test_a_concept_piece_chart_gets_no_entry", ok,
          ("concept-piece: " + ("absent" if e is None else str(e)[:120])
           + "; code-seam twin: " + ("NO ENTRY" if ce is None else ("refused" if ENTRY in cwhy else "passed"))))


def main() -> int:
    global V
    try:
        from cairn.devices.codemother.machines.validate import validate as subject
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject validate does not load: {exc!r}")
        for n in PROVES["4661ca005242"].values():
            check(n, False, "subject absent")
        return 1
    V = subject
    teeth = (test_an_all_clause_against_numbered_keys_is_refused, test_keys_equal_to_the_clauses_pass,
             test_a_proof_declaring_nothing_for_the_ticket_is_refused,
             test_clauses_covered_by_the_union_of_two_proofs_pass,
             test_a_concept_piece_chart_gets_no_entry)
    for tooth in teeth:
        try:
            with tempfile.TemporaryDirectory(prefix="cairn-chart-clause-proof-") as d:
                tooth(Path(d))
        except Exception as exc:  # noqa: BLE001
            check(tooth.__name__, False, f"aborted: {exc!r}"[:200])
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
