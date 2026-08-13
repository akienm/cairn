"""Proof: WATCHME is a FREE SUMMONS — optional to carry, mandatory to satisfy once carried.

Ticket ``watchme-emits-a-probe`` (2026-07-30), triage position 4. code-seam@v2 and skill@v2
are minted here; v1 stays frozen beside them, because versions are immutable and a path
change is a new version, not a widening.

WHAT WAS WRONG WITH v1, measured: ``LEARNME`` sat in ``path`` with only ``TICKETME`` in
``skippable_summons``, so it was MANDATORY TO CROSS for every node of both classes — and it
carried NO GATE (the build gate fires at the PROVEME crossing, the exit gate into PROVED).
The one summons in the path that was forced and unchecked. Akien's rule is the exact
inverse: OPTIONAL TO CARRY, MANDATORY TO SATISFY ONCE CARRIED.

HOW THAT INVERSION IS SPELLED, and why it needed the parser rung rather than only the class
files: WATCHME may appear ZERO OR MORE TIMES AT ANY POSITION, which the chokepoint's
exact-sequence conformance refused outright. So the class declares ``free_summons`` — the
same category of fact as ``skippable_summons``, something the -ME grammar cannot derive —
and ``_conform`` lifts free summonses out before comparing the backbone. The two
declarations are orthogonal on purpose: skippable is the FORK a node takes at runtime, free
is the SHAPE the ticket authored. Optional to carry = the author writes it or does not.
Mandatory to satisfy = it is NOT skippable, so the forward walk cannot step over it.

AND IT NAMES ITS OBJECT. ``WATCHME(what-it-watches)``; a bare token is refused. "Learning
without an object is inert" (Akien 2026-07-30) — a bare token cannot state what is being
learned, so nothing downstream can check it, which is the blank-field shape
``intention+why.json`` exists to refuse.

NON-HOLLOW: run against the REAL registered tables in CairnCommons/node_classes/ and the
REAL projector door, never a fixture table. The load-bearing row is
``test_a_drifted_v2_path_is_still_refused`` — a "free" state must not turn conformance into
anything-goes, which is the way this change could quietly delete the drift check that was
the whole point of versioned paths.

    python3 cairn/tools/base/proofs/test_watchme_vocabulary.py     # exit 0 = green
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import transitions
from cairn.tools.charter import projector

_CD = transitions.load_class_def("code-seam")
_SKILL_CD = transitions.load_class_def("skill")

_WATCHED = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> "
            "WATCHME(does-the-emission-gate-fire-in-anger) -> PROVED")
_UNWATCHED = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"


def _expect_refused(fn, exc=transitions.IllegalTransition):
    try:
        fn()
    except exc as e:
        return str(e)
    raise AssertionError(f"expected {exc.__name__}, got a pass")


def test_a_carried_watchme_parses_conforms_and_is_a_summons_by_grammar_alone():
    wf = transitions.parse_workflow(_WATCHED)
    assert wf.path[4] == "WATCHME"
    assert wf.objects[4] == "does-the-emission-gate-fire-in-anger", wf.objects
    assert transitions.is_summons("WATCHME"), \
        "the -ME grammar is classless — it must recognise a state it has never been told about"
    transitions.legal_targets(wf, class_def=_CD)          # conforms against the REAL table


def test_zero_watchmes_conforms_too_optional_to_carry():
    wf = transitions.parse_workflow(_UNWATCHED)
    assert transitions.legal_targets(wf, class_def=_CD) >= {"PROVED"}, \
        "a node that declares no watch reads exactly like v1 minus LEARNME"


def test_a_carried_watchme_cannot_be_skipped_mandatory_to_satisfy():
    wf = transitions.parse_workflow(_WATCHED)
    legal = transitions.legal_targets(wf, class_def=_CD)
    assert "WATCHME" in legal and "PROVED" not in legal, \
        f"a carried watch must be crossed, not stepped over — legal was {sorted(legal)}"
    _expect_refused(lambda: transitions.validate_transition(wf, "PROVED", class_def=_CD))


def test_a_bare_watchme_is_refused_and_says_what_is_missing():
    bare = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> WATCHME -> PROVED"
    msg = _expect_refused(
        lambda: transitions.legal_targets(transitions.parse_workflow(bare), class_def=_CD),
        transitions.MalformedWorkflow)
    assert "NAME ITS OBJECT" in msg and "inert" in msg, msg


def test_any_position_not_just_the_tail():
    mid = ("code-seam@v2: THINKME -> [TICKETME] -> WATCHME(do-the-children-actually-land) -> "
           "BUILDME -> PROVEME -> PROVED")
    wf = transitions.parse_workflow(mid)
    assert transitions.legal_targets(wf, class_def=_CD) >= {"WATCHME"}, \
        "'zero or more at ANY position' means the tail is a convention, not the rule"


def test_two_watches_are_two_obligations_not_a_no_op():
    two = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
           "[WATCHME(does-the-gate-fire)] -> WATCHME(does-anyone-read-the-verdict) -> PROVED")
    wf = transitions.parse_workflow(two)
    assert transitions.resolve_target(wf, "WATCHME") == 5, \
        "naming a repeated free summons resolves FORWARD — the next obligation, not this one"
    transitions.validate_transition(wf, "WATCHME", class_def=_CD)      # NOT a no-op
    moved = transitions.render(wf, "WATCHME")
    assert "[WATCHME(does-anyone-read-the-verdict):waiting]" in moved, moved
    assert "[WATCHME(does-the-gate-fire)" not in moved, moved


def test_the_object_survives_the_round_trip():
    wf = transitions.parse_workflow(_WATCHED)
    moved = transitions.render(wf, "WATCHME")
    assert "WATCHME(does-the-emission-gate-fire-in-anger)" in moved, moved
    back = transitions.parse_workflow(moved)
    assert back.objects == wf.objects, \
        "a move that dropped the object would erase the obligation while looking like progress"


def test_a_drifted_v2_path_is_still_refused():
    """THE LOAD-BEARING ROW. 'Free' must widen exactly one state, never the drift check."""
    drifted = "code-seam@v2: THINKME -> [BUILDME] -> PROVEME -> WATCHME(x) -> PROVED"
    msg = _expect_refused(
        lambda: transitions.legal_targets(transitions.parse_workflow(drifted), class_def=_CD),
        transitions.MalformedWorkflow)
    assert "does not conform" in msg and "backbone read as" in msg, msg


def test_v1_is_untouched_beside_it():
    v1 = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> LEARNME -> PROVED"
    wf = transitions.parse_workflow(v1)
    assert transitions.legal_targets(wf, class_def=_CD) >= {"LEARNME"}, \
        "a frozen version keeps working — migration is a crossing, never a rewrite of the past"
    # LEARNME ends in -ME, so even the frozen v1 vocabulary is a summons to the classless
    # grammar — arrival stamps :waiting there too (ruled 2026-08-07; the stamp is
    # grammar-level, not per-class, which is the whole point of the ruling).
    assert transitions.render(wf, "LEARNME").endswith("[LEARNME:waiting] -> PROVED")


def test_skill_v2_is_minted_the_same_way():
    s = ("skill@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> "
         "WATCHME(does-the-step-actually-fire-in-a-real-session) -> PROVED")
    wf = transitions.parse_workflow(s)
    legal = transitions.legal_targets(wf, class_def=_SKILL_CD)
    assert "WATCHME" in legal and "PROVED" not in legal, sorted(legal)


def test_a_real_v2_crossing_journals_the_object_through_the_real_door():
    """End-to-end at the REAL chokepoint and the REAL projector door. A back-edge, so no gate
    is in play — this row is about the vocabulary reaching the record of truth, nothing else."""
    with tempfile.TemporaryDirectory() as td:
        hist, state = f"{td}/history.json", f"{td}/state.json"
        resting = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
                   "WATCHME(does-the-emission-gate-fire-in-anger) -> [PROVED]")
        new = transitions.emit(resting, "WATCHME", history_path=hist,
                               state_path=state, why="the efficacy verdict came back failed")
        assert "[WATCHME(does-the-emission-gate-fire-in-anger):waiting]" in new, new
        last = projector.read_history(hist)[-1]
        assert last["to"] == "WATCHME" and last["direction"] == "back", last
        assert "WATCHME(does-the-emission-gate-fire-in-anger)" in last["workflow"], last
        assert last["standing"] == "WATCHME", last


TESTS = [
    test_a_carried_watchme_parses_conforms_and_is_a_summons_by_grammar_alone,
    test_zero_watchmes_conforms_too_optional_to_carry,
    test_a_carried_watchme_cannot_be_skipped_mandatory_to_satisfy,
    test_a_bare_watchme_is_refused_and_says_what_is_missing,
    test_any_position_not_just_the_tail,
    test_two_watches_are_two_obligations_not_a_no_op,
    test_the_object_survives_the_round_trip,
    test_a_drifted_v2_path_is_still_refused,
    test_v1_is_untouched_beside_it,
    test_skill_v2_is_minted_the_same_way,
    test_a_real_v2_crossing_journals_the_object_through_the_real_door,
]

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
