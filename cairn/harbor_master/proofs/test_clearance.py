"""Proof: the CLEARANCE gate (harbor_master child b) — the AUTHORITY rung of a transition.

The stone's claim: no boat's cursor moves without CLEARANCE — the owner's, or a delegate's
under a per-operation grant — and every refusal (unauthorized, unproven, illegal) leaves no
record, while every cleared move is recorded in the boat's own history. Teeth a hollow build
could not pass (mapped to the parent falsifier, tickets/harbor-master.json):

  - CLEARANCE IS REQUIRED (Law 6): the owner may move the boat; an actor who is neither the
    owner nor a grant-holder is REFUSED — and nothing is journaled. An ambient-advance build
    (anyone may move any boat) dies here.
  - CLEARANCE IS DELEGABLE, PER-OPERATION (Law 6): the owner mints a grant for ONE igor to
    make ONE move; the igor clears it. THE HOLLOW-KILLER: that same grant does NOT authorize
    a different target, a different boat, or a different actor — an ambient "the igor may
    advance anything" model passes the happy path and dies on this tooth.
  - AUTHORITY NEVER BUYS AN ILLEGAL MOVE (Law 4): even the OWNER, with a proven method,
    cannot clear a rules-illegal transition (a skip past a gate summons) — the wrapped
    chokepoint refuses it and nothing is written. Authority and rules are separate gates.
  - THE MOVE'S METHOD MUST BE PROVEN (Law 8): clearing onto a method not in proven-space is
    refused; a method is admitted to the registry only if its proof passes UNDER THE TESTER
    (a red-proof method is refused at register time). Proven-space is the tester's, not a
    claim.
  - THE MOVEMENT IS RECORDED, TWO VANTAGES (Law 7): a cleared crossing appends to the boat's
    own history carrying WHO cleared it; the fleet register (child a), computed over that
    history, then reflects the new standing — no rival record.

Runs bare (the registry's gate is the real tester; the green/red fixtures are the tester's):
    python3 cairn/harbor_master/proofs/test_clearance.py     # exit 0 = green
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.transitions import IllegalTransition
from cairn.charter import projector
from cairn.harbor_master.clearance import Unauthorized, clear, mint_grant
from cairn.harbor_master.registry import MethodRegistry, UnprovenMethod

# The real code-seam@v1 string, cursor at BUILDME. Legal forward from here: PROVEME (the next
# summons). Illegal: LEARNME (a skip PAST the PROVEME gate). Validated against the REAL
# node-class table (CairnCommons/node_classes/code-seam.json) — non-hollow, like transitions.
_WF = "code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"

_OWNER = "akiendelllinux_cc_0"
_IGOR = "igor_7"
_BOAT = "some-code-seam"

_FIXTURES = _REPO_ROOT / "cairn" / "tester" / "proofs" / "fixtures"
_GREEN_FIXTURE = _FIXTURES / "green_proof.py"
_RED_FIXTURE = _FIXTURES / "red_proof.py"


def _proven_registry():
    """A registry with one method ('build') admitted through the REAL tester gate."""
    reg = MethodRegistry()
    reg.register("build", method=lambda: "built", proof_path=_GREEN_FIXTURE)
    return reg


def _paths(tmp: str):
    return str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")


def test_the_owner_may_clear_a_legal_move_and_it_is_recorded():
    reg = _proven_registry()
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
            method="build", registry=reg, history_path=hp, state_path=sp,
        )
        assert "[PROVEME]" in new, "the cursor must have moved to PROVEME"
        history = projector.read_history(hp)
        assert len(history) == 1, "exactly one crossing recorded"
        rec = history[0]
        assert rec["from"] == "BUILDME" and rec["to"] == "PROVEME"
        assert rec["cleared_by"] == _OWNER, "the record must name WHO cleared it (Law 7)"
        assert rec["delegated"] is False, "the owner acting directly is not a delegation"


def test_an_unauthorized_actor_is_refused_and_nothing_is_written():
    reg = _proven_registry()
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_IGOR, boat_id=_BOAT, boat_owner=_OWNER,  # igor, no grant
                method="build", registry=reg, history_path=hp, state_path=sp,
            )
        except Unauthorized:
            assert not Path(hp).exists(), "a refused move must leave NO record (no ambient advance)"
            return
        raise AssertionError("an ungranted non-owner must be refused — ambient advance is the failure")


def test_clearance_is_delegable_per_operation():
    reg = _proven_registry()
    grant = mint_grant(owner=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_IGOR, boat_id=_BOAT, boat_owner=_OWNER,
            method="build", registry=reg, grant=grant, history_path=hp, state_path=sp,
        )
        assert "[PROVEME]" in new
        rec = projector.read_history(hp)[0]
        assert rec["cleared_by"] == _IGOR and rec["delegated"] is True, "a delegated crossing is recorded as such"


def test_a_grant_is_non_ambient_it_does_not_authorize_other_operations():
    # THE HOLLOW-KILLER. A grant for (this boat, PROVEME, this igor) must NOT authorize a
    # different target, a different boat, or a different actor. An ambient authority model
    # (a grant that lets the igor do anything) passes every happy path and dies right here.
    reg = _proven_registry()
    grant = mint_grant(owner=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    other_actor = "igor_9"

    def _refused(**overrides):
        kw = dict(actor=_IGOR, boat_id=_BOAT, boat_owner=_OWNER, method="build", registry=reg, grant=grant)
        kw.update(overrides)
        try:
            clear(_WF, kw.pop("target_state", "PROVEME"), **kw)
        except Unauthorized:
            return True
        return False

    # wrong target: the grant names PROVEME, try to clear a back-edge to TICKETME under it
    assert _refused(target_state="TICKETME"), "a grant for PROVEME must not authorize a different target"
    # wrong boat: same grant, a different boat_id
    assert _refused(boat_id="other-boat"), "a grant for one boat must not authorize another"
    # wrong actor: the grant names igor_7, igor_9 tries to use it
    assert _refused(actor=other_actor), "a grant to one actor must not authorize another"


def test_even_the_owner_cannot_clear_an_illegal_move():
    # Authority never overrides the base-class rules (Law 4). LEARNME is a skip PAST the
    # PROVEME gate — illegal — and the owner's authority does not buy it.
    reg = _proven_registry()
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "LEARNME",
                actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
                method="build", registry=reg, history_path=hp, state_path=sp,
            )
        except IllegalTransition:
            assert not Path(hp).exists(), "an illegal move, even by the owner, writes no record"
            return
        raise AssertionError("a rules-illegal move must be refused regardless of authority (Law 4)")


def test_clearing_onto_an_unproven_method_is_refused():
    # Law 8: the method a cleared move summons must be in proven-space. An unregistered name
    # never cleared the tester's gate, so the move cannot be cleared onto it.
    reg = _proven_registry()
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
                method="not_registered", registry=reg, history_path=hp, state_path=sp,
            )
        except UnprovenMethod:
            assert not Path(hp).exists(), "a move refused for an unproven method writes no record"
            return
        raise AssertionError("clearing onto an unproven method must be refused (Law 8)")


def test_a_method_with_a_failing_proof_is_refused_admission():
    # Proven-space is the TESTER's, not a label: a method whose proof reds under the tester
    # is refused at register time, so it can never be resolved for a clearance.
    reg = MethodRegistry()
    try:
        reg.register("bogus", method=lambda: None, proof_path=_RED_FIXTURE)
    except UnprovenMethod:
        assert "bogus" not in reg.names(), "a red-proof method must not enter proven-space"
        return
    raise AssertionError("a method whose proof fails under the tester must be refused admission (Law 8)")


def _main() -> int:
    checks = [
        test_the_owner_may_clear_a_legal_move_and_it_is_recorded,
        test_an_unauthorized_actor_is_refused_and_nothing_is_written,
        test_clearance_is_delegable_per_operation,
        test_a_grant_is_non_ambient_it_does_not_authorize_other_operations,
        test_even_the_owner_cannot_clear_an_illegal_move,
        test_clearing_onto_an_unproven_method_is_refused,
        test_a_method_with_a_failing_proof_is_refused_admission,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the clearance gate binds authority (Law 6), proven-space (Law 8), and the "
          "wrapped rules (Law 4) before a cursor moves, and records the crossing (Law 7) — "
          "the harbor clears the move, it never sails it")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
