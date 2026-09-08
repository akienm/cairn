"""Teeth for proof_coverage — the join that stops a ticket naming any green proof.

Charter: cairn/tools/proof_coverage/intention+why.json
Ticket:  CairnCommons/tickets/feeb4c786b14-proof-coverage-is-declared-and-a-proveme-ticket-without-it-reads-red.json

Run: python3 cairn/tools/proof_coverage/proofs/test_proof_coverage.py

THIS FILE DECLARES ITS OWN COVERAGE, which is the smallest honest test of the feature:
if the mechanism could not be pointed at the ticket that built it, it would be a mechanism
for other people's tickets. The PROVES block below is read by the same AST reader the
sieve uses over every other proof in the corpus.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from cairn.tools import proof_coverage as pc  # noqa: E402

PROVES = {
    "feeb4c786b14": {
        "1": "test_a_sealed_run_records_every_tooth_it_printed_not_just_the_tail",
        "2": "test_an_undeclared_clause_is_named_by_its_number",
        "3": "test_a_fully_covered_ticket_produces_no_finding",
        "4": "test_the_live_corpus_reds_every_ticket_at_proveme",
        "5": "test_a_concept_piece_with_no_review_record_reds",
    }
}

TICKET = "feeb4c786b14"


# ── fixtures ─────────────────────────────────────────────────────────────────────────

def _ticket(clauses_text: str, *, proven_by: str | None, node_class: str = "code-seam",
            cursor: str = "PROVEME", crossings: list | None = None) -> dict:
    wf = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> "
          f"[{cursor}:waiting] -> PROVED")
    if crossings is None:
        crossings = [{"date": "2026-09-07", "to": "BUILDME", "by": "CC",
                      **({"proven_by": proven_by} if proven_by else {})}]
    return {"id": "fixture01", "node_class": node_class, "workflow_and_state": wf,
            "falsifier": {"proves_green": "the fixture is green",
                          "proves_red": clauses_text},
            "crossings": crossings}


def _component(tmp: Path, *, proof_body: str, name: str = "widget") -> Path:
    """A component dir with proofs/ and validations/ — the shape a seal is derived from."""
    comp = tmp / name
    (comp / "proofs").mkdir(parents=True)
    (comp / "validations").mkdir(parents=True)
    proof = comp / "proofs" / "test_widget.py"
    proof.write_text(proof_body, encoding="utf-8")
    return proof


def _seal(proof: Path, *, teeth_green: list[str], fingerprint: str | None = None) -> None:
    from cairn.tools.base.validation import source_fingerprint
    fp = fingerprint if fingerprint is not None else source_fingerprint(str(proof))
    record = {"claim": f"proof {proof.name} passes", "date": "2026-09-07T00:00:00Z",
              "method": "ran the proof as a subprocess", "verdict": "green",
              "evidence": {"returncode": 0, "source_fingerprint": fp,
                           "teeth_green": teeth_green, "teeth_red": []},
              "falsifier": "re-run reds", "horizon": "until the code changes"}
    (proof.parent.parent / "validations" / (proof.stem + ".json")).write_text(
        json.dumps([record], indent=2), encoding="utf-8")


# ── clause (1) ───────────────────────────────────────────────────────────────────────

def test_a_sealed_run_records_every_tooth_it_printed_not_just_the_tail():
    """FORTY TEETH, AND ALL FORTY IN THE SEAL — the tail must not bound the reading.

    ``evidence.stdout_tail`` is twenty lines by design. If teeth_green were read from the
    tail, a forty-tooth proof would seal twenty and the other twenty would read as
    unproved — a red for the wrong reason, which is worse than no reading at all because
    the fix it suggests (write a tooth that already exists) never converges. Forty is
    chosen to be exactly twice the tail so the failure would be unmistakable rather than
    marginal.

    This runs the REAL tester through the REAL door, not a parser over a canned string:
    the claim is about what run_proof records, and a canned string would prove only that
    the parser works on strings I wrote.
    """
    from cairn.devices.tester.device import TesterDevice

    with tempfile.TemporaryDirectory() as tmp:
        proof = Path(tmp) / "test_forty.py"
        proof.write_text(
            "\n".join([f'print("  ok   test_tooth_{i:02d}")' for i in range(40)])
            + "\nraise SystemExit(0)\n", encoding="utf-8")
        record = TesterDevice().run_proof(proof, sink="none", caller="test_proof_coverage")

    assert record["verdict"] == "green", record
    green = record["evidence"]["teeth_green"]
    assert len(green) == 40, f"the seal recorded {len(green)} of 40 teeth — the tail bounded it"
    assert green[0] == "test_tooth_00" and green[-1] == "test_tooth_39", green[:3] + green[-3:]
    # And the tail really is shorter, so the tooth above is not vacuously true.
    assert len(record["evidence"]["stdout_tail"].splitlines()) <= 20


def test_a_red_tooth_is_never_recorded_green():
    """The safe direction. A name printed on a red-marked line is red even if the same
    name also appears green — a proof that reports one tooth twice with two verdicts has
    not proved it, and resolving that toward green is the only direction a hollow build
    ever needs."""
    printed = pc.teeth_printed(
        "  ok   test_flappy\n  FAIL test_flappy: boom\n  ok   test_solid\n")
    assert printed["green"] == ["test_solid"], printed
    assert printed["red"] == ["test_flappy"], printed


def test_every_printing_style_in_the_corpus_is_read():
    """Five markers, measured 2026-09-07 across 189 proof files: ok, PASS, GREEN, green,
    and pytest's trailing PASSED. The extractor keys on a marker word beside a test_-shaped
    name rather than on the five styles, because a hand roster of styles beside the corpus
    it lists is the same shape that let two teeth go unrun while test_trouble.py printed
    '16/16 green'."""
    printed = pc.teeth_printed(
        "  ok   test_a\n  PASS  test_b\n  GREEN  test_c\n  green  test_d\n"
        "x/y.py::test_e PASSED\nx/y.py::test_f FAILED\n")
    assert printed["green"] == ["test_a", "test_b", "test_c", "test_d", "test_e"], printed
    assert printed["red"] == ["test_f"], printed


def test_a_marker_word_in_prose_does_not_mint_a_tooth():
    """WRONG-INTENT TOOTH. If any line containing 'ok' or 'green' produced a tooth, the
    summary lines every proof prints ('all teeth green', '13 passed in 0.18s') would seal
    teeth nobody wrote — and coverage would go green on names that do not exist."""
    printed = pc.teeth_printed(
        "green - the widget holds under load\n"
        "\n6/6 green\n13 passed in 0.18s\nok, moving on\n")
    assert printed["green"] == [], printed
    assert printed["red"] == [], printed


# ── clause (2) ───────────────────────────────────────────────────────────────────────

def test_an_undeclared_clause_is_named_by_its_number():
    """THE LACK IS A CLAUSE, NOT A TICKET. A two-clause falsifier whose proof declares only
    clause (1) reds naming clause (2) — because 'this ticket is not covered' tells a builder
    nothing he can act on, and a report he cannot act on is one he learns to skip."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof = _component(tmp, proof_body=(
            'PROVES = {"fixture01": {"1": "test_first_half"}}\n'
            'print("  ok   test_first_half")\n'))
        _seal(proof, teeth_green=["test_first_half"])
        ticket = _ticket("DONE when (1) the first half holds and (2) the second half holds.",
                         proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp)

    kinds = {f["kind"] for f in found}
    assert kinds == {"clause_declared"}, found
    assert len(found) == 1, found
    assert found[0]["values"]["clause"] == "2", found[0]
    assert "(2)" in found[0]["why"], found[0]["why"]


def test_a_declared_tooth_that_never_ran_green_is_named():
    """Declaring is not proving. A clause may name a tooth that the seal never recorded
    green — the tooth was renamed, or deleted, or never written — and a check that stopped
    at 'a tooth is declared' would pass exactly that."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof = _component(tmp, proof_body=(
            'PROVES = {"fixture01": {"1": "test_renamed_yesterday"}}\n'
            'print("  ok   test_the_new_name")\n'))
        _seal(proof, teeth_green=["test_the_new_name"])
        ticket = _ticket("DONE when the widget holds.", proven_by=str(proof))
        # a falsifier with no (N) markers is one clause, keyed WHOLE
        ticket["falsifier"]["proves_red"] = "DONE when (1) the widget holds."

        found = pc.lacks(ticket, repo_root=tmp)

    assert [f["kind"] for f in found] == ["declared_tooth_green"], found
    assert found[0]["values"]["tooth"] == "test_renamed_yesterday", found[0]


def test_a_proof_that_declares_nothing_for_this_ticket_is_named():
    """The measured defect, in miniature: three PROVEME tickets named test_trouble_panel.py,
    a green-sealed proof containing no tooth about any of them."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof = _component(tmp, proof_body=(
            'PROVES = {"someone_elses_ticket": {"1": "test_unrelated"}}\n'
            'print("  ok   test_unrelated")\n'))
        _seal(proof, teeth_green=["test_unrelated"])
        ticket = _ticket("DONE when (1) the widget holds.", proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp)

    assert "proof_declares_the_ticket" in {f["kind"] for f in found}, found


def test_a_flat_falsifier_is_one_clause_and_still_needs_a_tooth():
    """A falsifier with no (N) markers is not exempt — it is ONE clause named 'all'. An
    exemption here would make 'write the falsifier as a paragraph' the way past the gate."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof = _component(tmp, proof_body='print("  ok   test_something")\n')
        _seal(proof, teeth_green=["test_something"])
        ticket = _ticket("DONE when the widget holds under load.", proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp)

    assert pc.clauses(ticket) == [pc.WHOLE]
    assert "clause_declared" in {f["kind"] for f in found}, found


def test_wrong_intent_clauses_are_not_demanded_as_teeth():
    """Everything after WRONG INTENT describes what would make the ticket the wrong thing
    to have built — a disposition, not a condition a tooth can go green on. Demanding a
    tooth for 'this was a bad idea' would make every well-written falsifier redder than a
    lazy one, which is the incentive exactly backwards."""
    ticket = _ticket(
        "DONE when (1) the widget holds. WRONG INTENT if (2) nobody ever uses the widget.",
        proven_by=None)
    assert pc.clauses(ticket) == ["1"], pc.clauses(ticket)


# ── clause (3) ───────────────────────────────────────────────────────────────────────

def test_a_fully_covered_ticket_produces_no_finding():
    """THE GREEN HALF, and it is the half that makes the rest falsifiable. A check that only
    ever reds is not a measurement of anything — it is a constant. Every clause declared,
    every declared tooth green in the seal, fingerprint matching the tree: no finding."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof = _component(tmp, proof_body=(
            'PROVES = {"fixture01": {"1": "test_first", "2": "test_second"}}\n'
            'print("  ok   test_first")\nprint("  ok   test_second")\n'))
        _seal(proof, teeth_green=["test_first", "test_second"])
        ticket = _ticket("DONE when (1) the first holds and (2) the second holds.",
                         proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp)

    assert found == [], found


def test_a_stale_fingerprint_reds_a_ticket_that_is_otherwise_covered():
    """Coverage expires with the seal. The declaration and the teeth can both be perfect
    and still describe code that no longer exists (Law 3 — a VALIDATION has a horizon)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof = _component(tmp, proof_body=(
            'PROVES = {"fixture01": {"1": "test_first"}}\nprint("  ok   test_first")\n'))
        _seal(proof, teeth_green=["test_first"], fingerprint="0" * 64)
        ticket = _ticket("DONE when (1) the first holds.", proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp)

    assert [f["kind"] for f in found] == ["seal_fingerprint_current"], found


def test_a_ticket_below_proveme_is_not_asked_for_coverage():
    """Scope. A ticket at BUILDME has not claimed to be proved, so demanding coverage of it
    would red the whole backlog for not having finished — Law 9 reds what claims green, not
    what is honestly under way."""
    from cairn.machines.build_inspector.inspector import _workflow_cursor, _PROVEN_SPACE
    assert _workflow_cursor(_ticket("x", proven_by=None, cursor="BUILDME")[
        "workflow_and_state"]) == "BUILDME"
    assert "BUILDME" not in _PROVEN_SPACE
    assert {"PROVEME", "WATCHME", "PROVED"} == set(_PROVEN_SPACE)


# ── clause (4) ───────────────────────────────────────────────────────────────────────

def test_the_live_corpus_reds_every_ticket_at_proveme():
    """THE INSTRUMENT'S OWN CORPUS, not a fixture — measured 2026-09-07: all 19 tickets at
    PROVEME:waiting red, with the lack named per ticket.

    Asserted as an INVARIANT rather than as the number 19 (memory:
    proof-over-live-data-assert-invariants): the count moves as tickets cross, and a proof
    pinned to a snapshot value would go red for the corpus doing exactly what it should.
    What must hold forever is that no ticket in proven-space escapes the check unnamed and
    that every finding carries an actionable lack.
    """
    from cairn.machines.build_inspector.inspector import (
        proof_covers_the_ticket, _workflow_cursor, _PROVEN_SPACE)

    findings = proof_covers_the_ticket(REPO_ROOT / "cairn")
    tickets = pc.load_tickets(REPO_ROOT.parent / "CairnCommons")
    in_space = [t for t in tickets
                if _workflow_cursor(t.get("workflow_and_state")) in _PROVEN_SPACE]
    assert len(in_space) > 40, f"only {len(in_space)} tickets in proven-space — not the real corpus"

    named = {f["component"] for f in findings}
    covered = {t["id"] for t in in_space} - named
    # Every ticket is either covered or named with a reason. Nothing may be silently absent.
    assert named | covered == {t["id"] for t in in_space}
    for f in findings:
        assert f["values"]["lack"], f
        assert f["values"]["reason"], f
        assert f["expected"] is True and f["actual"] is False, f

    proveme = {t["id"] for t in in_space
               if _workflow_cursor(t["workflow_and_state"]) == "PROVEME"}
    uncovered_proveme = proveme - named
    assert not uncovered_proveme, (
        "these PROVEME tickets claim coverage the sieve did not check: "
        f"{sorted(uncovered_proveme)}")


def test_this_very_proof_declares_the_ticket_that_built_it():
    """Dogfood, and it is not decoration: it is the one tooth that fails if the AST reader
    stops finding PROVES blocks at all — which every other tooth here would survive,
    because they all hand the reader a string they wrote."""
    mine = pc.declared(Path(__file__))
    assert TICKET in mine, mine
    assert set(mine[TICKET]) == {"1", "2", "3", "4", "5"}, mine[TICKET]
    for clause, tooth in mine[TICKET].items():
        assert tooth in globals(), f"clause ({clause}) declares {tooth}, which does not exist"


def test_a_proof_is_never_imported_to_read_its_declaration():
    """The reader must not execute what it reads. A proof imported to fetch one dict would
    run its teeth — the instrument seeding the tree it measures, which is the same defect
    the tester's instance seal exists to remove."""
    with tempfile.TemporaryDirectory() as tmp:
        bomb = Path(tmp) / "test_bomb.py"
        bomb.write_text(
            'import pathlib\n'
            f'pathlib.Path({str(Path(tmp) / "DETONATED")!r}).write_text("x")\n'
            'PROVES = {"t1": {"1": "test_x"}}\n', encoding="utf-8")

        got = pc.declared(bomb)

        assert got == {"t1": {"1": "test_x"}}, got
        assert not (Path(tmp) / "DETONATED").exists(), "reading the declaration ran the proof"


# ── clause (5) ───────────────────────────────────────────────────────────────────────

def test_a_concept_piece_with_no_review_record_reds():
    """A concept-piece is proved by people reading it, so its coverage question is whether
    a review VALIDATION sits beside the artifact. No clause-by-clause join applies — a
    reader does not go green per numbered clause — and demanding a PROVES block inside a
    markdown file would be the mechanism outrunning its own subject."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        piece = tmp / "press_office" / "the-method.md"
        piece.parent.mkdir(parents=True)
        piece.write_text("# The method\n", encoding="utf-8")
        ticket = _ticket("DONE when (1) three readers say it lands.",
                         proven_by=str(piece), node_class="concept-piece")

        found = pc.lacks(ticket, repo_root=tmp)

    assert [f["kind"] for f in found] == ["review_record"], found
    assert "no review record" in found[0]["why"], found[0]["why"]


def test_a_concept_piece_with_a_review_record_is_covered():
    """The green half of clause (5) — without it the concept-piece branch is a constant."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        piece = tmp / "press_office" / "the-method.md"
        (piece.parent / "validations").mkdir(parents=True)
        piece.write_text("# The method\n", encoding="utf-8")
        (piece.parent / "validations" / "the-method.json").write_text(json.dumps([{
            "claim": "the method transfers", "date": "2026-09-07T00:00:00Z",
            "method": "review by 3 readers", "verdict": "green", "evidence": {},
            "falsifier": "a reader says it does not land", "horizon": "until it is rewritten",
        }]), encoding="utf-8")
        ticket = _ticket("DONE when (1) three readers say it lands.",
                         proven_by=str(piece), node_class="concept-piece")

        found = pc.lacks(ticket, repo_root=tmp)

    assert found == [], found


def test_a_seal_that_is_not_a_reading_does_not_prove_a_concept_piece():
    """A subprocess run beside a markdown file is a seal about something, but not about
    anyone having read it — and 'a seal exists' is exactly the check the whole ticket was
    written against."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        piece = tmp / "press_office" / "the-method.md"
        (piece.parent / "validations").mkdir(parents=True)
        piece.write_text("# The method\n", encoding="utf-8")
        (piece.parent / "validations" / "the-method.json").write_text(json.dumps([{
            "claim": "x", "date": "2026-09-07T00:00:00Z",
            "method": "ran the proof as a subprocess", "verdict": "green", "evidence": {},
            "falsifier": "x", "horizon": "x",
        }]), encoding="utf-8")
        ticket = _ticket("DONE when (1) three readers say it lands.",
                         proven_by=str(piece), node_class="concept-piece")

        found = pc.lacks(ticket, repo_root=tmp)

    assert [f["kind"] for f in found] == ["review_record"], found


# ── the two shapes of "no proof named" ───────────────────────────────────────────────

def test_a_ticket_with_no_crossings_is_named_differently_from_one_that_forgot():
    """Measured 2026-09-07: of 230 tickets in proven-space, 215 name no proof — but 196 of
    those carry no crossings array at all, because they were resolved before the crossing
    record existed. Both are red; collapsing them into one line would bury nineteen
    actionable tickets under two hundred archaeological ones."""
    absent = _ticket("DONE when (1) x.", proven_by=None, crossings=[])
    forgot = _ticket("DONE when (1) x.", proven_by=None,
                     crossings=[{"date": "2026-09-07", "to": "PROVEME", "by": "CC"}])

    a = pc.lacks(absent, repo_root=REPO_ROOT)
    f = pc.lacks(forgot, repo_root=REPO_ROOT)

    assert [x["kind"] for x in a] == ["crossing_record_absent"], a
    assert [x["kind"] for x in f] == ["proof_named"], f
    assert a[0]["why"] != f[0]["why"]


def test_the_latest_crossing_wins_when_a_ticket_was_kicked_back():
    """A ticket kicked back to BUILDME and re-crossed names a NEW proof. Reading the first
    crossing would check the abandoned one forever — and the abandoned one is exactly the
    proof least likely to still cover anything."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof = _component(tmp, proof_body=(
            'PROVES = {"fixture01": {"1": "test_first"}}\nprint("  ok   test_first")\n'))
        _seal(proof, teeth_green=["test_first"])
        ticket = _ticket("DONE when (1) the first holds.", proven_by=None, crossings=[
            {"date": "2026-09-01", "to": "PROVEME", "by": "CC",
             "proven_by": str(tmp / "gone" / "proofs" / "test_old.py")},
            {"date": "2026-09-07", "to": "PROVEME", "by": "CC", "proven_by": str(proof)},
        ])

        found = pc.lacks(ticket, repo_root=tmp)

    assert found == [], found


TESTS = [fn for name, fn in sorted(globals().items())
         if name.startswith("test_") and callable(fn)]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
