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

def _roots(tmp: Path) -> dict:
    """The world a fixture ticket's CROSSINGS are derived from.

    Since the crossings stopped being an array on the ticket, a fixture ticket dict carries
    no evidence of its own — the derivation reads journals off disk. Handing ``lacks`` only
    ``repo_root`` would point the proof-reads at the fixture and the crossing-reads at the
    live corpus, where ``fixture01`` has never crossed anything.
    """
    return {"repo": tmp, "commons": tmp / "CairnCommons", "instance": tmp / ".cairn"}


def _journal(tmp: Path, entries: list[dict], *, at: str = "cairn/fixture/history.json") -> Path:
    """A history.json in the fixture world — the shape ``emit`` writes and the ONLY shape
    the crossings derivation reads. Writing the crossing here rather than onto the ticket
    is the point of the migration: a gate reads what physics wrote."""
    path = tmp / at
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"entries": entries}, indent=2), encoding="utf-8")
    return path


def _ticket(tmp: Path, clauses_text: str, *, proven_by: str | None,
            node_class: str = "code-seam", cursor: str = "PROVEME",
            crossings: list | None = None) -> dict:
    """A fixture ticket, plus the JOURNAL its crossing lives in.

    ``crossings`` is still the parameter a tooth varies — an empty list means "this ticket
    has journalled nothing", which is how the ``crossing_record_absent`` split is exercised
    — but the entries land in a history.json under ``tmp`` rather than on the returned dict.
    The ticket itself carries no crossings key at all, because no ticket in the corpus does.
    """
    wf = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> "
          f"[{cursor}:waiting] -> PROVED")
    if crossings is None:
        crossings = [{"to": "BUILDME", "direction": "forward", "actor": "CC",
                      **({"proven_by": proven_by} if proven_by else {})}]
    entries = []
    for i, one in enumerate(crossings):
        entry = {"ticket": "fixture01", "at": f"2026-09-07T10:0{i}:00",
                 "direction": "forward", "actor": "CC"}
        entry.update(one)
        entries.append(entry)
    _journal(tmp, entries)
    return {"id": "fixture01", "node_class": node_class, "workflow_and_state": wf,
            "falsifier": {"proves_green": "the fixture is green",
                          "proves_red": clauses_text}}


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
        ticket = _ticket(tmp, "DONE when (1) the first half holds and (2) the second half holds.",
                         proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

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
        ticket = _ticket(tmp, "DONE when the widget holds.", proven_by=str(proof))
        # a falsifier with no (N) markers is one clause, keyed WHOLE
        ticket["falsifier"]["proves_red"] = "DONE when (1) the widget holds."

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

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
        ticket = _ticket(tmp, "DONE when (1) the widget holds.", proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

    assert "proof_declares_the_ticket" in {f["kind"] for f in found}, found


def test_a_flat_falsifier_is_one_clause_and_still_needs_a_tooth():
    """A falsifier with no (N) markers is not exempt — it is ONE clause named 'all'. An
    exemption here would make 'write the falsifier as a paragraph' the way past the gate."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof = _component(tmp, proof_body='print("  ok   test_something")\n')
        _seal(proof, teeth_green=["test_something"])
        ticket = _ticket(tmp, "DONE when the widget holds under load.", proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

    assert pc.clauses(ticket) == [pc.WHOLE]
    assert "clause_declared" in {f["kind"] for f in found}, found


def test_wrong_intent_clauses_are_not_demanded_as_teeth():
    """Everything after WRONG INTENT describes what would make the ticket the wrong thing
    to have built — a disposition, not a condition a tooth can go green on. Demanding a
    tooth for 'this was a bad idea' would make every well-written falsifier redder than a
    lazy one, which is the incentive exactly backwards."""
    with tempfile.TemporaryDirectory() as tmp:
        ticket = _ticket(
            Path(tmp),
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
        ticket = _ticket(tmp, "DONE when (1) the first holds and (2) the second holds.",
                         proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

    assert found == [], found


def test_a_seam_ticket_is_covered_by_teeth_in_more_than_one_proof():
    """A SEAM HAS ENDS IN MORE THAN ONE COMPONENT. Measured on 9579a6f9cec6 (a device
    reaches trouble over the bus, never by import): its six clauses are served by teeth in
    three proofs — trouble's own, tools/base's fixture-device raise, and the panel probe —
    because that is where the seam's ends are. If a crossing could name only one proof, the
    honest options would be a crossing that lies about two thirds of the evidence, or
    inlining other components' teeth into trouble's proof, which is the tighter coupling
    that ticket exists to remove. So `proven_by` reads as one-or-many, and a clause is
    covered if ANY named proof declares a green tooth for it."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        near = _component(tmp, name="near", proof_body=(
            'PROVES = {"fixture01": {"1": "test_this_end"}}\nprint("  ok   test_this_end")\n'))
        far = _component(tmp, name="far", proof_body=(
            'PROVES = {"fixture01": {"2": "test_that_end"}}\nprint("  ok   test_that_end")\n'))
        _seal(near, teeth_green=["test_this_end"])
        _seal(far, teeth_green=["test_that_end"])
        ticket = _ticket(tmp, "DONE when (1) this end holds and (2) that end holds.",
                         proven_by=None, crossings=[{"date": "2026-09-07", "to": "PROVEME",
                                                     "by": "CC",
                                                     "proven_by": [str(near), str(far)]}])

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

    assert found == [], found


def test_each_proof_in_a_list_is_still_checked_on_its_own_terms():
    """One-or-many relaxes WHERE a tooth may live, nothing else. A second named proof that
    declares this ticket nothing is still named — otherwise 'name more proofs' would be the
    way to dilute the check, and a list would be a loophole rather than a shape."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        near = _component(tmp, name="near", proof_body=(
            'PROVES = {"fixture01": {"1": "test_this_end", "2": "test_that_end"}}\n'
            'print("  ok   test_this_end")\nprint("  ok   test_that_end")\n'))
        bystander = _component(tmp, name="bystander", proof_body='print("  ok   test_x")\n')
        _seal(near, teeth_green=["test_this_end", "test_that_end"])
        _seal(bystander, teeth_green=["test_x"])
        ticket = _ticket(tmp, "DONE when (1) this end holds and (2) that end holds.",
                         proven_by=None,
                         crossings=[{"date": "2026-09-07", "to": "PROVEME", "by": "CC",
                                     "proven_by": [str(near), str(bystander)]}])

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

    assert [f["kind"] for f in found] == ["proof_declares_the_ticket"], found
    assert found[0]["values"]["proof"].endswith("bystander/proofs/test_widget.py"), found[0]


def test_a_stale_fingerprint_reds_a_ticket_that_is_otherwise_covered():
    """Coverage expires with the seal. The declaration and the teeth can both be perfect
    and still describe code that no longer exists (Law 3 — a VALIDATION has a horizon)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof = _component(tmp, proof_body=(
            'PROVES = {"fixture01": {"1": "test_first"}}\nprint("  ok   test_first")\n'))
        _seal(proof, teeth_green=["test_first"], fingerprint="0" * 64)
        ticket = _ticket(tmp, "DONE when (1) the first holds.", proven_by=str(proof))

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

    assert [f["kind"] for f in found] == ["seal_fingerprint_current"], found


def test_a_ticket_below_proveme_is_not_asked_for_coverage():
    """Scope. A ticket at BUILDME has not claimed to be proved, so demanding coverage of it
    would red the whole backlog for not having finished — Law 9 reds what claims green, not
    what is honestly under way."""
    from cairn.machines.build_inspector.inspector import _workflow_cursor, _PROVEN_SPACE
    with tempfile.TemporaryDirectory() as tmp:
        below = _ticket(Path(tmp), "x", proven_by=None, cursor="BUILDME")
    assert _workflow_cursor(below["workflow_and_state"]) == "BUILDME"
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

    # A PROVEME TICKET IS EITHER NAMED WITH A LACK, OR DEMONSTRABLY COVERED — and the second
    # half is the correction. This assertion used to be "every PROVEME ticket is named by a
    # finding", full stop, and it read as an invariant because on 2026-09-07 all 19 tickets at
    # PROVEME happened to be uncovered. It is not an invariant. A ticket that is fully covered
    # is exactly what a ticket looks like in the moment BEFORE it crosses to PROVED — the state
    # this whole ticket was built to make reachable — so the old form redded the corpus for
    # doing the thing the build succeeded at. Measured 2026-09-09: one ticket at PROVEME
    # (feeb4c786b14, this one), unnamed because the sieve checked it and found every clause
    # declared, every declared tooth green in the standing seal, fingerprint matching.
    #
    # WHAT ACTUALLY MUST HOLD is that no PROVEME ticket is SKIPPED: silence about a ticket must
    # mean "checked and clean", never "never looked at". So an unnamed one is re-asked
    # DIRECTLY, through the per-ticket evaluator the sieve itself composes — if lacks() returns
    # empty the sieve did evaluate it, and if the ticket were vacuous (no proven_by, nothing
    # declared for it) lacks() would name that as its own lack rather than come back empty.
    proveme = [t for t in in_space
               if _workflow_cursor(t["workflow_and_state"]) == "PROVEME"]
    for t in proveme:
        if t["id"] in named:
            continue
        residual = pc.lacks(t, repo_root=REPO_ROOT)
        assert residual == [], (
            f"PROVEME ticket {t['id']} was not named by the sweep, but asking the evaluator "
            f"directly returns lacks — the sweep skipped it: {residual}")


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
        ticket = _ticket(tmp, "DONE when (1) three readers say it lands.",
                         proven_by=str(piece), node_class="concept-piece")

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

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
        ticket = _ticket(tmp, "DONE when (1) three readers say it lands.",
                         proven_by=str(piece), node_class="concept-piece")

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

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
        ticket = _ticket(tmp, "DONE when (1) three readers say it lands.",
                         proven_by=str(piece), node_class="concept-piece")

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

    assert [f["kind"] for f in found] == ["review_record"], found


# ── the two shapes of "no proof named" ───────────────────────────────────────────────

def test_a_ticket_with_no_crossings_is_named_differently_from_one_that_forgot():
    """Measured 2026-09-07: of 230 tickets in proven-space, 215 name no proof — but 196 of
    those carry no crossings array at all, because they were resolved before the crossing
    record existed. Both are red; collapsing them into one line would bury nineteen
    actionable tickets under two hundred archaeological ones."""
    # TWO WORLDS, NOT TWO TICKETS IN ONE. Both fixtures are ``fixture01``, and the crossings
    # derivation indexes journals BY TICKET ID across the whole world — so a single tmp would
    # merge "journalled nothing" into "journalled without a proof" and the split under test
    # would silently stop being a split.
    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
        t1, t2 = Path(t1), Path(t2)
        absent = _ticket(t1, "DONE when (1) x.", proven_by=None, crossings=[])
        forgot = _ticket(t2, "DONE when (1) x.", proven_by=None,
                         crossings=[{"to": "PROVEME"}])

        a = pc.lacks(absent, repo_root=t1, roots=_roots(t1))
        f = pc.lacks(forgot, repo_root=t2, roots=_roots(t2))

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
        ticket = _ticket(tmp, "DONE when (1) the first holds.", proven_by=None, crossings=[
            {"date": "2026-09-01", "to": "PROVEME", "by": "CC",
             "proven_by": str(tmp / "gone" / "proofs" / "test_old.py")},
            {"date": "2026-09-07", "to": "PROVEME", "by": "CC", "proven_by": str(proof)},
        ])

        found = pc.lacks(ticket, repo_root=tmp, roots=_roots(tmp))

    assert found == [], found


# ── the printer and the reader are one component ─────────────────────────────────────

def test_the_printer_writes_names_THIS_MODULE_can_read_back():
    """``print_teeth_main`` exists because a pytest-shaped proof prints dots, and a seal
    over dots records ``teeth_green: []`` — every clause declared against it reds, for a
    proof that actually ran everything. So the printer and the reader ship in one
    component, and this is the tooth that makes that mean something: run the printer for
    real, feed its stdout to ``teeth_printed``, and check the three verdicts land where
    they belong.

    THE FAILURE THIS CAUGHT ON THE DAY IT WAS WRITTEN, and the reason the printer emits a
    leading newline: pytest writes its progress dot to the same line with no newline, so
    the first draft produced ``.  ok   test_x``. Both marker patterns are anchored, so
    every tooth was invisible to the reader while looking perfectly correct to a human —
    a hollow green wearing the output of a real run.

    Run as a SUBPROCESS, not by calling ``print_teeth_main`` in this process: pytest
    inside pytest shares a terminal reporter, and the point of the tooth is the bytes a
    proof actually writes when the tester runs it as ``python3 <proof>``."""
    import subprocess

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "test_fixture_teeth.py"
        target.write_text(
            "import pytest\n"
            "def test_one_that_passes(): assert True\n"
            "def test_one_that_fails(): assert False, 'on purpose'\n"
            "@pytest.mark.skip(reason='on purpose')\n"
            "def test_one_that_skips(): pass\n"
            "if __name__ == '__main__':\n"
            "    import sys; sys.path.insert(0, %r)\n" % str(REPO_ROOT) +
            "    from cairn.tools.proof_coverage import print_teeth_main\n"
            "    raise SystemExit(print_teeth_main(__file__))\n",
            encoding="utf-8")
        out = subprocess.run([sys.executable, str(target)], capture_output=True,
                             text=True, timeout=120)

    printed = pc.teeth_printed(out.stdout)
    assert printed["green"] == ["test_one_that_passes"], (printed, out.stdout)
    assert printed["red"] == ["test_one_that_fails"], (printed, out.stdout)
    assert "test_one_that_skips" not in printed["green"], (
        "a SKIPPED tooth was counted green — it did not prove and it did not fail, and "
        "counting it either way is the direction a hollow build wants")
    assert "test_one_that_skips" not in printed["red"], printed
    assert out.returncode != 0, "a proof with a failing tooth exited 0"


def test_a_proof_with_NO_main_block_is_a_GREEN_over_ZERO_teeth():
    """THE DEFECT ``print_teeth_main`` WAS BUILT FOR, stated as a tooth so it cannot come
    back quietly. The tester runs a proof as ``python3 <proof>`` and reads the exit code,
    so a proof file with no ``__main__`` block defines its functions, runs none of them,
    and exits 0 — a green seal over nothing at all, inside the machinery Law 8 exists to
    be. Measured 2026-09-07: ten of the corpus's 158 proofs were in exactly this state.

    Asserted against a fixture rather than against the live corpus, because the live
    count is a number that will change and this is a claim about the SHAPE: a run that
    named no teeth is not evidence, whatever its exit code says."""
    import subprocess

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "test_no_main.py"
        target.write_text("def test_that_would_have_failed(): assert False\n",
                          encoding="utf-8")
        out = subprocess.run([sys.executable, str(target)], capture_output=True,
                             text=True, timeout=120)

    assert out.returncode == 0, "the fixture no longer demonstrates the defect"
    assert pc.teeth_printed(out.stdout) == {"green": [], "red": []}, out.stdout


def test_an_ok_style_PROSE_LABEL_is_recorded_as_a_tooth_not_only_a_test_identifier():
    """HALF THE CORPUS'S TEETH WERE INVISIBLE, AND THE TICKET HAD ALREADY SAID SO.

    feeb4c786b14's HOW: "a tooth name is the ok() label for ok-style proofs (18 in the
    corpus) or the test_ function name for pytest-style proofs (152)". The test_ half was
    built; the ok() half was not, because both marker patterns anchored on a ``test_``
    name. The anchor's REASON was sound — a marker word in prose must not mint a tooth —
    it was simply spent on one of the two shapes that occur.

    MEASURED 2026-09-09: 31 of 131 green seals recorded ZERO teeth, and SEVENTEEN of those
    print their teeth in plain sight (``  ok the backdate refusal wrote no slate``,
    ``PASS: status returns 0 and reads liveness``). This matters beyond tidiness because
    the sieve reds when a DECLARED tooth is absent from teeth_green, and every declared
    tooth is absent from an empty list — so those seventeen proofs were structurally
    unable to serve as coverage evidence for any ticket, while reading green.
    """
    printed = pc.teeth_printed(
        "  ok the backdate refusal wrote no slate\n"
        "PASS: status returns 0 and reads liveness\n"
        "  PASS  a unified line is the answer\n"
        "  FAIL the door committed the real repo\n")
    assert printed["green"] == ["the backdate refusal wrote no slate",
                                "status returns 0 and reads liveness",
                                "a unified line is the answer"], printed
    assert printed["red"] == ["the door committed the real repo"], printed


def test_a_marker_word_at_the_LEFT_MARGIN_mints_no_tooth():
    """THE ANCHOR THAT REPLACES ``test_`` FOR THE PROSE CASE, and the tooth that keeps it.

    Widening the parser to prose labels gives up the ``test_`` anchor, so it needs another
    one or a proof narrating "ok so the next thing" would mint a tooth named after its own
    aside — and a fabricated GREEN tooth is the one direction a hollow build wants (Law 8).
    The replacement anchor is punctuation, not vocabulary: the marker must OPEN the line
    AND the line must be INDENTED or the marker followed by a COLON, which is what every
    per-tooth report line in the corpus does and what a sentence does not.

    Measured against every stored proof output in the corpus (192 seals): zero green seals
    parse to a red tooth under the widened rule. The summary lines proofs actually print at
    the left margin — ``GREEN - 35 teeth``, ``green - validation_store: one record`` — mint
    nothing, and they are in the fixture below because they are the real near-misses.
    """
    printed = pc.teeth_printed(
        "ok so the next thing we do is check the door\n"
        "GREEN - 35 teeth\n"
        "green - validation_store: one current record beside its proof\n"
        "error occurred while reading the tree\n")
    assert printed["green"] == [], printed
    assert printed["red"] == [], printed


def test_NO_GREEN_SEAL_IN_THE_CORPUS_PARSES_TO_A_RED_TOOTH():
    """The invariant that guards the widening, over the real corpus rather than a fixture.

    An INVARIANT, never a snapshot count: seal contents change every time a proof re-seals,
    so asserting "17 seals gain teeth" would red on the next reseal for the right reason and
    teach nothing. What must hold forever is the DIRECTION — a proof that ran green must not
    have its own output read back as a failing tooth, because that red would be manufactured
    by the reader rather than measured by the proof.
    """
    import json as _json
    bad = []
    for v in sorted(REPO_ROOT.rglob("validations/*.json")):
        try:
            d = _json.loads(v.read_text())
        except Exception:
            continue
        rec = d[0] if isinstance(d, list) else d
        if not isinstance(rec, dict) or rec.get("verdict") != "green":
            continue
        tail = (rec.get("evidence") or {}).get("stdout_tail") or ""
        if tail and pc.teeth_printed(tail)["red"]:
            bad.append((str(v.relative_to(REPO_ROOT)), pc.teeth_printed(tail)["red"][:3]))
    assert not bad, (
        "a GREEN seal's own output parses to a red tooth — the parser is minting a red the "
        f"proof never reported: {bad[:5]}")


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
