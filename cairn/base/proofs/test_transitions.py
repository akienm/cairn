"""Proof: the EMIT-CHOKEPOINT (cairn/base/transitions.py) makes the state vocabulary PHYSICS.

The gate a hollow build could not pass (tickets/state-machine-physics.json): a node whose
workflow attempts an ILLEGAL transition is REFUSED (a skip past a gate summons, a target
outside the vocabulary, an unknown class/version, a no-op, a drifted path); a LEGAL transition
moves the cursor AND journals the crossing append-only; the string is version-validated against
a KNOWN node-class definition; a back-edge (kick-back) is legal and carries its severity.

Non-hollow: validated against the REAL registered table (node_classes/code-seam.json) and the
REAL projector door — not a stand-in — and it parses an actual ticket's live workflow string
(trailing prose and all). A green over a toy table or a swallowed refusal would be hollow.

Dependency-light: pure parsing + the projector's pure core. Runs bare.

    python3 cairn/base/proofs/test_transitions.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base import transitions
from cairn.charter import projector

_CODE_SEAM = "code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"


def _expect_refused(fn, exc=transitions.IllegalTransition):
    try:
        fn()
    except exc:
        return
    raise AssertionError("expected a refusal (a silent pass would be policy, not physics — Law 4/7)")


def test_a_legal_forward_advance_journals_the_crossing():
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        new = transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        assert "[PROVEME]" in new and "[BUILDME]" not in new, f"cursor did not move to PROVEME: {new}"
        log = projector.read_history(hist)
        assert len(log) == 1, "the crossing was not journaled exactly once (Law 7 append-only)"
        rec = log[0]
        assert rec["from"] == "BUILDME" and rec["to"] == "PROVEME" and rec["direction"] == "forward"
        assert rec["workflow"] == new, "the journal did not record the resulting workflow string"


def test_the_crossing_carries_where_the_boat_now_stands():
    """The emitter derives ``standing``; no caller has to remember it.

    FOUND BY THE APPEND DOOR'S SHAPE GATE, 2026-07-25, before this emitter had ever written
    to a live history: it journaled from/to/workflow/direction and NO ``standing``, which is
    the one field harbor_master's register reads to place a boat. Every such record would
    have been permanently unreadable (Law 7 — append-only, no edit afterwards). The gate
    refused it at the door instead, which is the whole reason the gate exists.
    """
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        rec = projector.read_history(hist)[0]
    assert rec["standing"] == "PROVEME", \
        f"a crossing that does not say where the boat stands cannot be read — got {rec.get('standing')!r}"
    assert all(rec.get(k) for k in projector.UNIVERSAL_REQUIRED), \
        "the emitter's record must clear the door's floor by construction, not by luck"


def test_a_caller_may_say_it_richer_but_may_not_drop_it():
    """``journal_extra`` overrides the derived standing (a berth line says more than a gate
    name) — the default is a FLOOR, not a ceiling. What it cannot do is omit it."""
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state,
                         standing="PROVEME — green under the tester, VALIDATION sealed beside it")
        rec = projector.read_history(hist)[0]
    assert rec["standing"].startswith("PROVEME — green"), "the caller's richer line must win"
    assert rec["to"] == "PROVEME", "and the machine-readable target is untouched beside it"


def test_the_leaf_fork_thinkme_may_go_to_ticketme_or_buildme():
    at_think = "code-seam@v1: [THINKME] -> TICKETME -> BUILDME -> PROVEME -> LEARNME -> PROVED"
    # decompose (parent) and build (leaf, skipping the skippable TICKETME) are BOTH legal
    assert "[TICKETME]" in transitions.emit(at_think, "TICKETME")
    assert "[BUILDME]" in transitions.emit(at_think, "BUILDME")


def test_a_forward_skip_past_a_gate_summons_is_refused():
    # BUILDME -> PROVED would skip PROVEME (a non-skippable gate summons) — physics refuses it
    _expect_refused(lambda: transitions.emit(_CODE_SEAM, "PROVED"))
    _expect_refused(lambda: transitions.emit(_CODE_SEAM, "LEARNME"))   # skips PROVEME too


def test_a_target_outside_the_vocabulary_is_refused():
    _expect_refused(lambda: transitions.emit(_CODE_SEAM, "FROBME"))


def test_a_no_op_self_transition_is_refused():
    _expect_refused(lambda: transitions.emit(_CODE_SEAM, "BUILDME"))


def test_an_unknown_class_or_version_is_refused():
    _expect_refused(lambda: transitions.emit("no-such-class@v1: [THINKME] -> PROVED", "PROVED"))
    _expect_refused(lambda: transitions.emit(
        "code-seam@v9: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED", "PROVEME"))


def test_a_drifted_path_that_claims_v1_is_refused():
    # claims code-seam@v1 but the path is mangled (TICKETME dropped) — not a valid v1 instance
    drifted = "code-seam@v1: THINKME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"
    _expect_refused(lambda: transitions.emit(drifted, "PROVEME"), exc=transitions.MalformedWorkflow)


def test_a_back_edge_kickback_is_legal_and_carries_severity():
    at_prove = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> LEARNME -> PROVED"
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        new = transitions.emit(at_prove, "BUILDME", history_path=hist, state_path=state)
        assert "[BUILDME]" in new, f"kick-back did not move the cursor: {new}"
        rec = projector.read_history(hist)[0]
        assert rec["direction"] == "back" and rec["severity"] == 1, f"severity not carried: {rec}"
        # a deeper kick-back to THINKME is legal with greater severity (2)
        assert transitions.parse_workflow(transitions.emit(at_prove, "THINKME")).here == "THINKME"
    # the last forward advance into the rest is legal — LEARNME -> PROVED reaches the rest
    at_learn = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> [LEARNME] -> PROVED"
    assert "[PROVED]" in transitions.emit(at_learn, "PROVED"), "the PROVED rest is unreachable"


def test_it_parses_a_real_live_ticket_workflow_string():
    # A real on-disk ticket with trailing prose after the cursor — proves the parser survives the
    # wild format and that the ticket is a CONFORMANT v1 instance. Picks ANY live code-seam@v1 ticket
    # from CairnCommons/tickets/ rather than a pinned filename: a ticket legitimately berths beside its
    # code and leaves the open lane (harbor-master did, 2026-07-24), so pinning one file re-derives a
    # moving target (Law 1). Asserts INVARIANTS on whichever ticket it finds — never a live cursor value.
    tickets_dir = _REPO_ROOT.parent / "CairnCommons" / "tickets"
    canonical = tuple(transitions.load_class_def("code-seam")["workflow_versions"]["v1"]["path"])
    found = None
    for t in sorted(tickets_dir.glob("*.json")):
        try:
            state = json.loads(t.read_text()).get("state")
            wf = transitions.parse_workflow(state) if isinstance(state, str) else None
        except (ValueError, OSError):
            continue                      # prose state / garbled ticket — not a code-seam workflow string
        if wf and wf.node_class == "code-seam" and wf.version == "v1" and wf.path == canonical:
            found = (t.name, wf)
            break
    assert found, ("no live code-seam@v1 ticket in CairnCommons/tickets/ to parse — the real-ticket tooth "
                   "needs at least one on-disk code-seam ticket (a green over zero would be hollow, Law 8)")
    name, wf = found
    assert wf.here in canonical, f"cursor mis-parsed from the real string ({name}, not a real stage): {wf.here}"


def _main() -> int:
    checks = [
        test_a_legal_forward_advance_journals_the_crossing,
        test_the_crossing_carries_where_the_boat_now_stands,
        test_a_caller_may_say_it_richer_but_may_not_drop_it,
        test_the_leaf_fork_thinkme_may_go_to_ticketme_or_buildme,
        test_a_forward_skip_past_a_gate_summons_is_refused,
        test_a_target_outside_the_vocabulary_is_refused,
        test_a_no_op_self_transition_is_refused,
        test_an_unknown_class_or_version_is_refused,
        test_a_drifted_path_that_claims_v1_is_refused,
        test_a_back_edge_kickback_is_legal_and_carries_severity,
        test_it_parses_a_real_live_ticket_workflow_string,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the emit-chokepoint refuses illegal transitions (skip-past-gate, off-vocabulary, "
          "unknown class/version, no-op, drifted path), journals legal crossings append-only, "
          "version-validates against the real node-class table, and carries kick-back severity — "
          "the state vocabulary is physics (Law 4), not /sorted's prose")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
