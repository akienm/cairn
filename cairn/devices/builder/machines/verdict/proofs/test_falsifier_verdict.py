#!/usr/bin/env python3
"""THE SECOND PROVENANCE FORM — teeth for ticket watchme-emits-a-probe piece (d).

A verdict's obligations used to come from exactly one place: a berthed chart
validate packet. A WATCHME probe fires long after the voyage that built the node
has closed, and the artifact that states "did the intention WORK?" in falsifiable
form is the ticket's own ``falsifier``. So ``validate_ref`` admits
``falsifier@<ticket-id>``.

WHAT THESE TEETH ARE FOR, precisely. The ticket's falsifier clause (6) is the
design's own RED: *"A verdict written by a probe cannot pass validate_verdict, or
needs a second schema to do so — one contract or the design failed."* So the
load-bearing rows are not the happy path; they are the ones that show the SHAPE
GATE NEVER LEARNED THIS FORM EXISTS (``test_one_contract_not_two``), that the new
form's obligation is real rather than vacuous
(``test_the_obligation_is_real_one_line_per_unanswered_clause``), and that the
half which genuinely IS vacuous is named out loud rather than counted as coverage
(``test_the_dispositions_half_is_vacuous_and_that_is_named``).

A hollow build of piece (d) — one that admitted the prefix and then read no
obligations at all — passes any happy-path row and reds on those three.

Tree-free like the module it proves: no db, no embed host, no network. The deposit
face's own nexus tooth lives beside the rest of the deposit teeth, in
``test_chart_verdict.py``, because that is where the tree is allowed.
"""
from __future__ import annotations

import ast
import json
import os
import pytest
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.builder.machines.verdict import verdict as verdict_mod
from cairn.devices.builder.machines.verdict.verdict import (DEFAULT_NEXUS, FALSIFIER_REF, VerdictRefused,
                                 falsifier_criteria, unanswered, validate_verdict,
                                 verdict_error, verdict_nexus, write_verdict)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

_FALSIFIER = ("RED on any of: (1) the door admits a claim its instrument never "
              "ran. (2) A clause is dropped in segmentation and nobody is loud "
              "about it. (3) The shape gate grows a second schema for this form.")


def make_root():
    """A synthetic world: two filed tickets — one carrying a three-clause
    falsifier, one carrying none at all (the empty-obligation case)."""
    tmp = str(scratch_dir("falsifier_verdict_proof_"))
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    tickets = os.path.join(tmp, "CairnCommons", "tickets")
    os.makedirs(tickets)
    with open(os.path.join(tickets, "watched.json"), "w") as fh:
        json.dump({"id": "watched", "falsifier": _FALSIFIER}, fh)
    with open(os.path.join(tickets, "unfalsifiable.json"), "w") as fh:
        json.dump({"id": "unfalsifiable"}, fh)
    return root, tickets


@pytest.fixture
def _world():
    return make_root()


@pytest.fixture
def root(_world):
    return _world[0]


@pytest.fixture
def tickets(_world):
    return _world[1]


def artifact_for(ticket, root, *, drop=(), fail=(), **extra):
    """Build a falsifier-sourced verdict THE WAY A PROBE WOULD — by asking the
    door itself what is owed. That is the point of ``falsifier_criteria`` being
    public: if the writer derived its claim strings any other way they would drift
    and every verdict would refuse while looking word-for-word right."""
    criteria, err = falsifier_criteria(ticket, root)
    assert err is None, err
    verdicts = []
    for i, c in enumerate(criteria):
        if i in drop:
            continue
        verdicts.append({"claim": c["claim"],
                         "instrument": "the probe's survey of the ticket corpus",
                         "outcome": "fail" if i in fail else "pass",
                         "evidence": "measured %d of 57 tickets; clause held" % (i + 1),
                         "discriminating_observation": "re-ran against a corpus with "
                         "clause %d violated; the probe reported it" % (i + 1)})
    return dict({"ticket": ticket, "validate_ref": FALSIFIER_REF + ticket,
                 "verdicts": verdicts, "dispositions": []}, **extra)


def expect_refusal(fn, needle):
    try:
        fn()
    except VerdictRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return str(err)
    raise AssertionError("expected VerdictRefused mentioning %r, got none" % needle)


# ---------------------------------------------------------------- the form works

def test_a_falsifier_verdict_answers_every_clause_and_passes(root, tickets):
    a = artifact_for("watched", root)
    assert verdict_error(a) is None
    assert unanswered(a, root) == []
    assert validate_verdict(a, root=root) is a


def test_the_writer_and_the_door_derive_the_same_claims(root, tickets):
    criteria, err = falsifier_criteria("watched", root)
    assert err is None and len(criteria) == 3, criteria
    assert criteria[0]["claim"].startswith("the door admits a claim")
    assert criteria[0]["claim"].endswith("never ran."), criteria[0]["claim"]
    assert criteria[1]["source"] == "%swatched clause (2)" % FALSIFIER_REF
    # The clause text is VERBATIM from the ticket — not paraphrased, not
    # re-numbered, not stripped of its punctuation. A claim the door reworded is a
    # claim no writer can match.
    for c in criteria:
        assert c["claim"] in _FALSIFIER, c["claim"]


def test_the_berth_round_trips(root, tickets):
    berths = str(scratch_dir("falsifier_berths_"))
    path = write_verdict(artifact_for("watched", root), instance_dir=berths, root=root)
    assert os.path.basename(path).startswith("verdict-")
    with open(path) as fh:
        assert json.load(fh)["validate_ref"] == FALSIFIER_REF + "watched"


# ------------------------------------------------------- the obligation is real

def test_the_obligation_is_real_one_line_per_unanswered_clause(root, tickets):
    """THE NON-VACUITY BIT. A hollow piece (d) — one that admitted the prefix and
    read no obligations — would pass every happy-path row above and this one goes
    red on it: an artifact answering NOTHING must be refused once per clause."""
    empty = dict(artifact_for("watched", root), verdicts=[])
    items = unanswered(empty, root)
    assert len(items) == 3, items
    assert all("criterion unanswered" in i for i in items), items


def test_an_unanswered_clause_refuses(root, tickets):
    items = unanswered(artifact_for("watched", root, drop=(1,)), root)
    assert len(items) == 1 and "criterion unanswered" in items[0], items
    assert "A clause is dropped in segmentation" in items[0], items[0]


def test_a_failed_clause_is_a_kick_back_not_a_crossing(root, tickets):
    err = expect_refusal(
        lambda: validate_verdict(artifact_for("watched", root, fail=(2,)), root=root),
        "kick-back")
    assert "answered and FAILED" in err, err


def test_the_dispositions_half_is_vacuous_and_that_is_named(root, tickets):
    """HONEST ABOUT THE HOLE. This form has no hypothesize berth, so the
    dispositions obligation is trivially satisfied — an artifact with an empty
    ``dispositions`` list passes. That is not hidden behind a happy-path row: it
    is asserted here, next to the row above that shows the criteria half is what
    carries the whole bite. If that ever stops being true, this row is where the
    reader was told to look."""
    a = artifact_for("watched", root)
    assert a["dispositions"] == []
    assert validate_verdict(a, root=root) is a
    criteria, hypotheses, err = verdict_mod._read_chain(a, root)
    assert err is None and hypotheses == [] and len(criteria) == 3


# ---------------------------------------------------- what the form refuses

def test_the_verdict_must_answer_its_own_tickets_falsifier(root, tickets):
    crossed = dict(artifact_for("watched", root), ticket="unfalsifiable")
    err = expect_refusal(lambda: validate_verdict(crossed, root=root),
                         "answering somebody else's question")
    assert "'watched'" in err and "'unfalsifiable'" in err, err


def test_a_ticket_carrying_no_falsifier_refuses(root, tickets):
    """An empty obligation would pass everything (Law 8) — so nothing is what it
    refuses on, loudly, rather than what it silently accepts."""
    a = {"ticket": "unfalsifiable", "validate_ref": FALSIFIER_REF + "unfalsifiable",
         "verdicts": [], "dispositions": []}
    assert verdict_error(a) is None, "the SHAPE is fine — it is the chain that is not"
    expect_refusal(lambda: validate_verdict(a, root=root), "carries no falsifier")


def test_an_unfiled_ticket_refuses(root, tickets):
    a = {"ticket": "watched", "validate_ref": FALSIFIER_REF + "ghost",
         "verdicts": [], "dispositions": []}
    expect_refusal(lambda: validate_verdict(a, root=root),
                   "answering somebody else's question")
    filed = dict(a, ticket="ghost")
    # ...and with the claim made consistent, it is the FILING that refuses — the
    # two refusals are different findings, so neither can mask the other.
    expect_refusal(lambda: validate_verdict(filed, root=root),
                   "names no ticket on file")


def test_an_unsegmentable_falsifier_refuses_rather_than_mis_segmenting(root, tickets):
    """Mis-segmentation is an obligation quietly DROPPED, which is exactly the
    failure this form would be blamed for later. So both shapes refuse."""
    for name, text, needle in (
            ("prose", "RED if the thing simply does not work.", "states no numbered clauses"),
            ("skipped", "RED on any of: (1) one. (3) three.", "not 1..2"),
            ("hollow", "RED on any of: (1) (2) two.", "clause (1) is empty")):
        with open(os.path.join(tickets, name + ".json"), "w") as fh:
            json.dump({"id": name, "falsifier": text}, fh)
        criteria, err = falsifier_criteria(name, root)
        assert criteria == [] and err and needle in err, (name, err)


# ------------------------------------------------------------- ONE CONTRACT

def test_one_contract_not_two(root, tickets):
    """THE TICKET'S OWN CLAUSE (6): "a verdict written by a probe cannot pass
    validate_verdict, or needs a second schema to do so — one contract or the
    design failed."

    Measured two ways. First: the shape gate never learned this form exists — the
    same ``verdict_error`` passes both provenances, and its refusals are identical
    strings for identical malformations. Second: the fork lives in exactly one
    function. If a second ``falsifier@`` branch ever appears elsewhere in the
    module, this row names it."""
    fal = artifact_for("watched", root)
    berth_form = dict(fal, validate_ref="/nonexistent/validate-berth.json")
    assert verdict_error(fal) is None and verdict_error(berth_form) is None
    for bad in ("verdicts", "dispositions"):
        assert (verdict_error(dict(fal, **{bad: "not a list"}))
                == verdict_error(dict(berth_form, **{bad: "not a list"})))
    tree = ast.parse(Path(verdict_mod.__file__).read_text(encoding="utf-8"))
    # OVER THE AST, not over the text: prose mentioning the constant is not a
    # branch on it, and a grep that cannot tell those apart would red on a comment
    # (measured — it did, the moment the module docstring named the form).
    forks = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "startswith"
             and any(isinstance(a, ast.Name) and a.id == "FALSIFIER_REF" for a in n.args)]
    assert len(forks) == 1, "the fork on the prefix must live in exactly one place"
    holders = [n.name for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef)
               and any(f in ast.walk(n) for f in forks)]
    assert holders == ["_read_chain"], holders


def test_the_berth_form_is_untouched(root, tickets):
    """Non-regression from inside the new form's own file: a ``validate_ref`` that
    is not the prefix still reads a BERTH, and an unreadable one still refuses
    with the berth-form's words, not the ticket-form's."""
    a = {"ticket": "watched", "validate_ref": "/nonexistent/validate-berth.json",
         "verdicts": [], "dispositions": []}
    items = unanswered(a, root)
    assert len(items) == 1 and "the claiming chain cannot be read" in items[0], items
    assert "falsifier" not in items[0], items[0]


# ------------------------------------------------------------------ the nexus

def test_verdict_nexus_defaults_to_where_it_always_landed(root, tickets):
    assert DEFAULT_NEXUS == "hypothesize"
    assert verdict_nexus(artifact_for("watched", root)) == DEFAULT_NEXUS
    assert verdict_nexus({}) == DEFAULT_NEXUS


def test_the_nexus_may_name_a_target_outside_this_toolchain(root, tickets):
    """The ticket's falsifier clause (8): a nexus that could only name one of our
    own devices would mean the design works for the toolchain watching itself and
    nowhere else. So this door does NOT adjudicate the name against any roster."""
    for name in ("efficacy", "acme-crm/quality-signals", "someone-elses-tree"):
        a = artifact_for("watched", root, nexus=name)
        assert verdict_error(a) is None, verdict_error(a)
        assert validate_verdict(a, root=root) is a
        assert verdict_nexus(a) == name


def test_naming_nothing_is_refused_where_omitting_is_not(root, tickets):
    for empty in ("", "   ", 7, None):
        err = verdict_error(artifact_for("watched", root, nexus=empty))
        assert err and "nexus, when named" in err, (empty, err)
    assert verdict_error(artifact_for("watched", root)) is None


# ------------------------------------------------------- over the real corpus

def test_the_real_ticket_that_built_this_form_yields_its_clauses(root, tickets):
    """Over the LIVE ticket, asserting INVARIANTS and never a snapshot count: this
    ticket's falsifier will grow if the design does, and a pinned 8 would turn
    normal motion into a spurious red."""
    criteria, err = falsifier_criteria("watchme-emits-a-probe")
    assert err is None, err
    assert len(criteria) >= 3, criteria  # a non-vacuity bit, not the count
    for i, c in enumerate(criteria):
        assert c["claim"].strip() == c["claim"] and len(c["claim"]) > 20, c
        assert c["source"].endswith("clause (%d)" % (i + 1)), c["source"]



def test_the_resolver_returns_the_standing_chain(root, tickets):
    """Ticket berths-carry-request-identity: chain_for_ticket returns the LATEST
    claiming berth per stage, absence as None, and never errors on a claimless
    ticket."""
    import tempfile as _tf
    from cairn.devices.builder.machines.verdict.verdict import chain_for_ticket
    with _tf.TemporaryDirectory() as td:
        pk = os.path.join(td, "0", "packets")
        os.makedirs(pk)
        for name, doc in [
            ("orient-20260101T000000-aaaaaaaaaaaa.json", {"ticket": "tkt-r", "intent": "x"}),
            ("validate-20260101T000000-bbbbbbbbbbbb.json", {"ticket": "tkt-r"}),
            ("validate-20260202T000000-cccccccccccc.json", {"ticket": "tkt-r"}),
            ("validate-20260303T000000-dddddddddddd.json", {"ticket": "other"}),
        ]:
            with open(os.path.join(pk, name), "w") as fh:
                json.dump(doc, fh)
        chain = chain_for_ticket("tkt-r", berths_root=td)
        assert chain["validate"].endswith("cccccccccccc.json"), chain["validate"]
        assert chain["orient"].endswith("aaaaaaaaaaaa.json")
        assert chain["constrain"] is None and chain["verdict"] is None
        empty = chain_for_ticket("nobody-claims-me", berths_root=td)
        assert all(v is None for v in empty.values()), empty


def _main():
    root, tickets = make_root()
    checks = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    checks.sort(key=lambda f: f.__code__.co_firstlineno)
    failures = 0
    for check in checks:
        try:
            check(root, tickets)
            print("  PASS  %s" % check.__name__)
        except Exception as e:  # noqa: BLE001
            failures += 1
            print("  RED   %s: %s: %s" % (check.__name__, type(e).__name__, e))
    if failures:
        print("RED — %d of %d" % (failures, len(checks)))
        return 1
    print("green — chart/verdict's SECOND PROVENANCE FORM (ticket "
          "watchme-emits-a-probe piece (d)): a verdict whose criteria come from "
          "its own ticket's falsifier is legal and round-trips; the writer and the "
          "door derive the claim strings by ONE implementation; the obligation is "
          "real (one refusal line per unanswered clause) and its vacuous half is "
          "named out loud rather than counted as coverage; a verdict may not read "
          "one ticket's falsifier while claiming another's voyage; no falsifier, "
          "no filing, and no segmentable numbering each refuse loudly rather than "
          "passing an empty obligation; ONE CONTRACT NOT TWO — the shape gate "
          "never learned this form exists and the fork lives in exactly one "
          "function; and the nexus is the artifact's to name, defaulting to where "
          "it always landed and free to name a target outside this toolchain")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
