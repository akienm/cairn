"""Teeth for ticket 46ece5fd9f69 — a clause a decide line adds is a clause proof coverage sees.

Charter: cairn/tools/proof_coverage/intention+why.json
Ticket:  CairnCommons/tickets/46ece5fd9f69-a-clause-a-decide-line-adds-is-covered-by-proof-coverage.json

Run: python3 cairn/tools/proof_coverage/proofs/test_a_clause_a_decide_line_adds_is_covered.py

A decide line that says 'falsifier clause (N) is added by this line' (the convention
answered "yes" at open-4b3d45d375ca; measured once in the corpus, 11cd253f10bc D6) adds a
clause the gate must see. A decision that merely cites '(N)' in prose adds nothing — the
charter's WRONG-INTENT signal is prose minting a tooth that does not exist.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

PROVES = {
    "46ece5fd9f69": {
        "1": "test_a_decide_line_that_adds_a_clause_extends_clauses",
        "2": "test_lacks_names_the_clause_a_decide_line_added",
        "3": "test_a_decision_citing_a_marker_in_prose_adds_nothing",
    },
}

FALSIFIER = "DONE when (1) a holds (2) b holds (3) c holds."
ADDS = "A falsifier clause (4) is added by this line: d holds."
CITES = "D2 (6) stands; tooth (4) is green."


# ── fixtures ─────────────────────────────────────────────────────────────────────────

def _decision(n: int, text: str) -> dict:
    """The shape a rehearsal decide line lands on a ticket (keys measured on 11cd253f10bc)."""
    return {"n": n, "text": text, "by": "cc", "step": "unlisted",
            "source": "rehearsal", "at": "2026-10-08T12:00:00+00:00"}


def _ticket(decisions: list[dict]) -> dict:
    return {"id": "fixture01", "node_class": "code-seam",
            "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> BUILDME -> "
                                  "[PROVEME:waiting] -> PROVED",
            "falsifier": {"proves_green": "the fixture is green", "proves_red": FALSIFIER},
            "decisions": decisions}


def _world(tmp: Path) -> tuple[Path, dict]:
    """A fixture proof declaring clauses 1-3, sealed green, and the journal that names it
    proven_by — the world lacks() derives its crossings and seals from."""
    from cairn.tools.base.validation import source_fingerprint
    comp = tmp / "widget"
    (comp / "proofs").mkdir(parents=True)
    (comp / "validations").mkdir(parents=True)
    proof = comp / "proofs" / "test_widget.py"
    teeth = ["test_a", "test_b", "test_c"]
    proof.write_text(
        'PROVES = {"fixture01": {"1": "test_a", "2": "test_b", "3": "test_c"}}\n'
        + "".join(f'print("  ok   {t}")\n' for t in teeth), encoding="utf-8")
    record = {"claim": "proof test_widget.py passes", "date": "2026-10-08T00:00:00Z",
              "method": "ran the proof as a subprocess", "verdict": "green",
              "evidence": {"returncode": 0, "source_fingerprint": source_fingerprint(str(proof)),
                           "teeth_green": teeth, "teeth_red": []},
              "falsifier": "re-run reds", "horizon": "until the code changes"}
    (comp / "validations" / "test_widget.json").write_text(json.dumps([record], indent=2),
                                                           encoding="utf-8")
    journal = tmp / "cairn" / "fixture" / "history.json"
    journal.parent.mkdir(parents=True)
    journal.write_text(json.dumps({"entries": [
        {"ticket": "fixture01", "at": "2026-10-08T10:00:00", "direction": "forward",
         "actor": "CC", "to": "BUILDME", "proven_by": str(proof)}]}, indent=2),
        encoding="utf-8")
    roots = {"repo": tmp, "commons": tmp / "CairnCommons", "instance": tmp / ".cairn"}
    return proof, roots


# ── clause (1) ───────────────────────────────────────────────────────────────────────

def test_a_decide_line_that_adds_a_clause_extends_clauses():
    """The falsifier's keys stand as they are; the decide line's key follows them."""
    from cairn.tools import proof_coverage as pc
    ticket = _ticket([_decision(1, ADDS)])
    assert pc.clauses(ticket) == ["1", "2", "3", "4"], pc.clauses(ticket)


# ── clause (2) ───────────────────────────────────────────────────────────────────────

def test_lacks_names_the_clause_a_decide_line_added():
    """A proof declaring 1-3 covers the falsifier and not the decide line: the lack names
    clause 4, through the same clause_declared kind a falsifier clause gets."""
    from cairn.tools import proof_coverage as pc
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("decide-clause-")
    _, roots = _world(tmp)
    found = pc.lacks(_ticket([_decision(1, ADDS)]), repo_root=tmp, roots=roots)
    assert [(f["kind"], f["values"].get("clause")) for f in found] == \
        [("clause_declared", "4")], found


# ── clause (3) ───────────────────────────────────────────────────────────────────────

def test_a_decision_citing_a_marker_in_prose_adds_nothing():
    """'(6)' and '(4)' in an ordinary decision are citations, not clauses."""
    from cairn.tools import proof_coverage as pc
    ticket = _ticket([_decision(1, CITES)])
    assert pc.clauses(ticket) == ["1", "2", "3"], pc.clauses(ticket)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
