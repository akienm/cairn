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
  - THE CODE THE MOVE SUMMONS MUST BE PROVEN, AND STILL BE THE CODE THAT WAS PROVEN (Law 8 +
    Law 3). The caller names a PROOF's address and the gate reads the seal beside it — there
    is no registry to populate (ripped out 2026-08-05). Three refusals: never sealed, sealed
    red, and THE HOLLOW-KILLER — sealed GREEN and then the component's code changed, so the
    VALIDATION's own horizon ('valid until the proof file or the code it proves changes') has
    closed. That last tooth is exactly what the in-memory registry could not do: it cached a
    bool with no description of what it was about, so it answered yes forever. A build that
    reads the verdict and skips the fingerprint dies there.
  - A GRANT LAPSES (Law 6): a grant that names the right operation and was minted by the right
    owner is STILL refused once its window closes. A build that treated the grant as a standing
    capability passes every operation-identity tooth above and dies here.
  - THE HOST CAN REFUSE (the fourth refusal): a move that is authorized, proven and legal is
    still refused when the harbor's resource line is crossed. THE HOLLOW-KILLERS: the gate
    receives a VERDICT and never a reading (a fake that raises on any door but ``ask`` proves
    it), and NOTHING COUNTS BUILDERS anywhere in the chain — the fake also raises on every
    census-shaped door, so a build that decided admission from a population dies here.

Runs bare. The proven-space fixtures are REAL: scratch component trees whose validation
trails are written by the real tester through the real single write-door, so a build that
faked a seal or a verdict dies before the teeth even start.
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
from cairn.harbor_master.clearance import (
    GRANT_TTL_SECONDS,
    HARBOR_LINES,
    GrantExpired,
    Unauthorized,
    Unproven,
    Unresourced,
    clear,
    mint_grant,
)
from cairn.tester.device import TesterDevice
from cairn.tester.scratch import scratch_dir
from cairn.tester.validation_store import persist_validation

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

# Scratch components for the proven-space teeth. NOT hand-written seals: each is a real
# component tree whose validation trail is produced by the REAL tester and landed through the
# REAL single write-door, so a build that faked either dies here. Swept at process exit by
# cairn.tester.scratch — the corpus's own door for this, and test_scratch.py enforces its use.
_SCRATCH = scratch_dir("clearance-proven-space-")


def _component(name: str, fixture: Path) -> str:
    """Build a component tree ``<scratch>/<name>/proofs/test_<name>.py`` and return the proof."""
    proofs = Path(_SCRATCH) / name / "proofs"
    proofs.mkdir(parents=True, exist_ok=True)
    proof = proofs / f"test_{name}.py"
    proof.write_text(fixture.read_text(), encoding="utf-8")
    return str(proof)


def _seal(proof: str) -> dict:
    """Run it under the real tester and append the verdict through the real store's write-door."""
    validation = TesterDevice().run_proof(proof)
    persist_validation(validation, proof_path=proof)
    return validation


# Sealed GREEN, fingerprint current — the code a move may be cleared onto.
_PROVEN = _component("proven", _GREEN_FIXTURE)
_seal(_PROVEN)

# Never sealed at all: a component with a proof and no trail beside it.
_UNSEALED = _component("unsealed", _GREEN_FIXTURE)

# Sealed, and the tester said RED. It was measured, and it failed.
_REDDED = _component("redded", _RED_FIXTURE)
_seal(_REDDED)


def _paths(tmp: str):
    return str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")


def test_the_owner_may_clear_a_legal_move_and_it_is_recorded():
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
            proven_by=_PROVEN, history_path=hp, state_path=sp,
        )
        assert "[PROVEME:waiting]" in new, "the cursor must have moved to PROVEME"
        history = projector.read_history(hp)
        assert len(history) == 1, "exactly one crossing recorded"
        rec = history[0]
        assert rec["from"] == "BUILDME" and rec["to"] == "PROVEME"
        assert rec["cleared_by"] == _OWNER, "the record must name WHO cleared it (Law 7)"
        assert rec["delegated"] is False, "the owner acting directly is not a delegation"


def test_an_unauthorized_actor_is_refused_and_nothing_is_written():
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_IGOR, boat_id=_BOAT, boat_owner=_OWNER,  # igor, no grant
                proven_by=_PROVEN, history_path=hp, state_path=sp,
            )
        except Unauthorized:
            assert not Path(hp).exists(), "a refused move must leave NO record (no ambient advance)"
            return
        raise AssertionError("an ungranted non-owner must be refused — ambient advance is the failure")


def test_clearance_is_delegable_per_operation():
    grant = mint_grant(owner=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_IGOR, boat_id=_BOAT, boat_owner=_OWNER,
            proven_by=_PROVEN, grant=grant, history_path=hp, state_path=sp,
        )
        assert "[PROVEME:waiting]" in new
        rec = projector.read_history(hp)[0]
        assert rec["cleared_by"] == _IGOR and rec["delegated"] is True, "a delegated crossing is recorded as such"


def test_a_grant_is_non_ambient_it_does_not_authorize_other_operations():
    # THE HOLLOW-KILLER. A grant for (this boat, PROVEME, this igor) must NOT authorize a
    # different target, a different boat, or a different actor. An ambient authority model
    # (a grant that lets the igor do anything) passes every happy path and dies right here.
    grant = mint_grant(owner=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    other_actor = "igor_9"

    def _refused(**overrides):
        kw = dict(actor=_IGOR, boat_id=_BOAT, boat_owner=_OWNER, proven_by=_PROVEN, grant=grant)
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
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "LEARNME",
                actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
                proven_by=_PROVEN, history_path=hp, state_path=sp,
            )
        except IllegalTransition:
            assert not Path(hp).exists(), "an illegal move, even by the owner, writes no record"
            return
        raise AssertionError("a rules-illegal move must be refused regardless of authority (Law 4)")


def _refused_for_proven_space(proven_by: str) -> str:
    """Clear an otherwise-perfect move onto ``proven_by``; return the refusal text. Asserts the
    refusal wrote nothing — a move turned away at Law 8 leaves no more record than one turned
    away at Law 6."""
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
                proven_by=proven_by, history_path=hp, state_path=sp,
            )
        except Unproven as exc:
            assert not Path(hp).exists(), "a move refused for want of proven-space writes no record"
            return str(exc)
        raise AssertionError(
            f"clearing onto {proven_by} must be refused — the harbor clears only onto proven "
            f"code (Law 8)")


def test_clearing_onto_code_that_was_never_sealed_is_refused():
    # Law 8, the plainest way in: nobody ever ran this proof, so proven-space has not spoken
    # about this code. Silence is not a pass.
    why = _refused_for_proven_space(_UNSEALED)
    assert "no VALIDATION has ever sealed" in why, f"the refusal must say WHICH lack it is: {why}"


def test_clearing_onto_code_whose_proof_went_red_is_refused():
    # Proven-space is the TESTER's, not a label anyone can claim: this component's proof was
    # actually run and it actually failed, and the seal beside it says so.
    why = _refused_for_proven_space(_REDDED)
    assert "did not pass" in why, f"the refusal must name the red verdict it read: {why}"


def test_a_green_seal_whose_code_has_moved_underneath_it_is_refused():
    # THE HOLLOW-KILLER FOR THIS STONE, and the whole reason the registry went (2026-08-05).
    # Every VALIDATION promises a horizon — "valid until the proof file or the code it proves
    # changes" — and until today nothing checked it. An in-memory registry CANNOT: it cached a
    # bool at wiring time with no description of what it was about, so it kept answering yes
    # forever. Here the seal is real, green, and freshly written by the real tester; the only
    # thing that happens is that the component's code changes afterwards. A build that reads
    # the verdict and skips the fingerprint passes every other tooth in this file and dies here.
    drifting = _component("drifting", _GREEN_FIXTURE)
    _seal(drifting)

    # Sanity: before anything moves, this same code clears. Without this the tooth below could
    # pass because `drifting` was never clearable in the first place.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        assert "[PROVEME:waiting]" in clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
            proven_by=drifting, history_path=hp, state_path=sp,
        ), "a freshly-sealed green component must clear before its code moves"

    # Now the code moves. Not the proof — a sibling module, which is the likelier drift by far
    # and the one a proof-only hash would miss entirely.
    (Path(drifting).parent.parent / "worker.py").write_text(
        "# the code the proof proves, edited after the seal\n", encoding="utf-8")

    why = _refused_for_proven_space(drifting)
    assert "HORIZON HAS CLOSED" in why, f"the refusal must name the expiry, not a vaguer lack: {why}"
    assert "fingerprint" in why, f"and must say what moved: {why}"


def test_the_record_names_the_proof_the_clearance_leaned_on():
    # Law 5: the crossing and its evidence share an address. A record that said only "proven"
    # would make a reader take the gate's word for it a year later; this one hands over the
    # proof path and the seal's date, so the same evidence can be re-read.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
            proven_by=_PROVEN, history_path=hp, state_path=sp,
        )
        rec = projector.read_history(hp)[0]
        assert rec["proven_by"] == _PROVEN, "the record must name the proof that backed the clearance"
        assert rec["proven_seal_date"], "and the date of the seal it read, so the trail entry is findable"


class _ResourceOwner:
    """A stand-in for system_rackmount's may-I door, built to catch a gate reaching for more
    than a verdict. It answers ``ask`` with a fixed verdict and RAISES on every other shape a
    hollow build might reach for — the raw reading, and any census of who is running. Those
    raises are the teeth: they are the two designs this one is not."""

    def __init__(self, crossed: bool) -> None:
        self._crossed = crossed
        self.asked: list[tuple] = []

    def ask(self, name: str, value) -> bool:
        self.asked.append((name, value))
        return self._crossed

    def _forbidden(self, *_a, **_k):
        raise AssertionError(
            "the gate reached past the verdict — it must never pull a reading, and it must "
            "never count builders (admission is decided from pressure, not population)"
        )

    reading = _reading = state = _forbidden          # the raw number: not this gate's business
    builders = count = active_builders = _forbidden  # the census that would make this a manager


def test_a_lapsed_grant_is_refused_and_nothing_is_written():
    # The window is part of the capability. This grant names exactly the right operation and was
    # minted by the right owner — the only thing wrong with it is that it is old.
    grant = mint_grant(owner=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME", now=1000.0)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_IGOR, boat_id=_BOAT, boat_owner=_OWNER,
                proven_by=_PROVEN, grant=grant,
                now=1000.0 + GRANT_TTL_SECONDS + 0.1,   # spent just past the window
                history_path=hp, state_path=sp,
            )
        except GrantExpired:
            assert not Path(hp).exists(), "a lapsed grant writes no record — it authorizes nothing"
            return
        raise AssertionError("a grant spent after its window must be refused (Law 6)")


def test_the_same_grant_inside_its_window_still_clears():
    # The other half of the tooth above: the expiry must refuse the STALE, not the DELEGATED.
    # A build that broke delegation outright would pass the lapse test and die right here.
    grant = mint_grant(owner=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME", now=1000.0)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_IGOR, boat_id=_BOAT, boat_owner=_OWNER,
            proven_by=_PROVEN, grant=grant,
            now=1000.0 + GRANT_TTL_SECONDS - 0.1,       # spent just inside it
            history_path=hp, state_path=sp,
        )
        assert "[PROVEME:waiting]" in new, "a grant inside its window must still clear the move"


def test_a_crossed_resource_line_refuses_an_otherwise_perfect_move():
    # THE FOURTH REFUSAL. Owner acting directly, proven method, legal target — every other gate
    # is wide open, and the host still says no.
    host = _ResourceOwner(crossed=True)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
                proven_by=_PROVEN, resources=host,
                history_path=hp, state_path=sp,
            )
        except Unresourced:
            assert not Path(hp).exists(), "a move refused for want of room writes no record"
            assert host.asked, "the gate must actually ask the resource owner, not assume"
            assert host.asked[0][0] in HARBOR_LINES, "it asks by ADVERTISED MENU NAME, not method"
            return
        raise AssertionError("a crossed resource line must refuse the move — the fourth refusal")


def test_the_gate_asks_for_a_verdict_and_never_counts_anything():
    # THE HOLLOW-KILLER for this stone. _ResourceOwner raises on every door but `ask` — on the
    # raw reading (which would export the metric's semantics into the harbor, Law 6) and on
    # every census shape (which would make this a manager). A build that reached for either
    # dies here even though the happy path below is identical.
    host = _ResourceOwner(crossed=False)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT, boat_owner=_OWNER,
            proven_by=_PROVEN, resources=host,
            history_path=hp, state_path=sp,
        )
        assert "[PROVEME:waiting]" in new, "room on the host → the move clears"
        assert host.asked == [(name, value) for name, value in HARBOR_LINES.items()], (
            "every line the harbor holds must be put to the resource owner — one unasked line "
            "is a gate that does not gate"
        )
        for name, value in host.asked:
            assert isinstance(value, (int, float)), "the harbor sends its LINE, a number it owns"
        assert projector.read_history(hp)[0]["to"] == "PROVEME"


def _main() -> int:
    checks = [
        test_the_owner_may_clear_a_legal_move_and_it_is_recorded,
        test_an_unauthorized_actor_is_refused_and_nothing_is_written,
        test_clearance_is_delegable_per_operation,
        test_a_grant_is_non_ambient_it_does_not_authorize_other_operations,
        test_even_the_owner_cannot_clear_an_illegal_move,
        test_clearing_onto_code_that_was_never_sealed_is_refused,
        test_clearing_onto_code_whose_proof_went_red_is_refused,
        test_a_green_seal_whose_code_has_moved_underneath_it_is_refused,
        test_the_record_names_the_proof_the_clearance_leaned_on,
        test_a_lapsed_grant_is_refused_and_nothing_is_written,
        test_the_same_grant_inside_its_window_still_clears,
        test_a_crossed_resource_line_refuses_an_otherwise_perfect_move,
        test_the_gate_asks_for_a_verdict_and_never_counts_anything,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the clearance gate binds authority (Law 6), proven-space (Law 8), resources, "
          "and the wrapped rules (Law 4) before a cursor moves, and records the crossing "
          "(Law 7) — the harbor clears the move, it never sails it, and it never counts a fleet")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
