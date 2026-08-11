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
    OwnerUnresolvable,
    Unauthorized,
    Unproven,
    Unresourced,
    boat_owner_of,
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

# THE BOATS ARE REAL NOW, and they have to be. Since 2026-08-10 (ticket
# boat-owner-is-read-not-stated) the gate READS a boat's owner off disk rather than taking
# it as an argument, and it accepts no root injection — a ``tickets_dir=`` parameter would
# hand the caller back the choice of what the gate reads, which is the ticket's own
# falsifier clause (1) wearing a coat. So a proof that wants a cleared crossing must name a
# boat that exists.
#
# WHAT IS ASSERTED ABOUT THEM IS AN INVARIANT, NEVER A SNAPSHOT. ``_OWNER`` is not the
# string 'CC' written down here; it is whatever hand these boats' owning intention admits,
# read the same way the gate reads it. If that list changes tomorrow these teeth still
# mean what they say — where a hard-coded 'CC' would go green for the wrong reason on the
# day somebody edits the charter.
_BOAT = "boat-owner-is-read-not-stated"
_OTHER_BOAT = "an-intention-declares-its-gated-hands"
_OWNER = boat_owner_of(_BOAT).hands[0]
_IGOR = "igor_7"
assert _IGOR not in boat_owner_of(_BOAT).hands, \
    "the unauthorized actor these teeth use must actually be unauthorized"

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
            actor=_OWNER, boat_id=_BOAT,
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
                actor=_IGOR, boat_id=_BOAT, # igor, no grant
                proven_by=_PROVEN, history_path=hp, state_path=sp,
            )
        except Unauthorized:
            assert not Path(hp).exists(), "a refused move must leave NO record (no ambient advance)"
            return
        raise AssertionError("an ungranted non-owner must be refused — ambient advance is the failure")


def test_clearance_is_delegable_per_operation():
    grant = mint_grant(minted_by=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_IGOR, boat_id=_BOAT,
            proven_by=_PROVEN, grant=grant, history_path=hp, state_path=sp,
        )
        assert "[PROVEME:waiting]" in new
        rec = projector.read_history(hp)[0]
        assert rec["cleared_by"] == _IGOR and rec["delegated"] is True, "a delegated crossing is recorded as such"


def test_a_grant_is_non_ambient_it_does_not_authorize_other_operations():
    # THE HOLLOW-KILLER. A grant for (this boat, PROVEME, this igor) must NOT authorize a
    # different target, a different boat, or a different actor. An ambient authority model
    # (a grant that lets the igor do anything) passes every happy path and dies right here.
    grant = mint_grant(minted_by=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    other_actor = "igor_9"

    def _refused(**overrides):
        kw = dict(actor=_IGOR, boat_id=_BOAT, proven_by=_PROVEN, grant=grant)
        kw.update(overrides)
        try:
            clear(_WF, kw.pop("target_state", "PROVEME"), **kw)
        except Unauthorized:
            return True
        return False

    # wrong target: the grant names PROVEME, try to clear a back-edge to TICKETME under it
    assert _refused(target_state="TICKETME"), "a grant for PROVEME must not authorize a different target"
    # wrong boat: same grant, a different boat_id
    # A REAL other boat, because the gate now reads one: an id with no ticket behind it
    # would raise OwnerUnresolvable and this tooth would be passing on the wrong refusal.
    assert _refused(boat_id=_OTHER_BOAT), "a grant for one boat must not authorize another"
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
                actor=_OWNER, boat_id=_BOAT,
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
                actor=_OWNER, boat_id=_BOAT,
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
            actor=_OWNER, boat_id=_BOAT,
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
            actor=_OWNER, boat_id=_BOAT,
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
    grant = mint_grant(minted_by=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME", now=1000.0)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_IGOR, boat_id=_BOAT,
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
    grant = mint_grant(minted_by=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME", now=1000.0)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_IGOR, boat_id=_BOAT,
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
                actor=_OWNER, boat_id=_BOAT,
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
            actor=_OWNER, boat_id=_BOAT,
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


# ---- THE GATE BECOMES CALLABLE, AND STAYS THE ONLY HAND THAT STAMPS ----------------
# Ticket ``emit-refuses-an-uncleared-crossing`` (2026-08-10). The build's decisive finding
# was not a discipline failure: ``clear`` had been STRUCTURALLY UNCALLABLE for every gated
# crossing since 2026-07-29, when ``a-voyage-names-its-ticket`` landed the ticket demand.
# Three gates inside ``emit`` read ``journal_extra["ticket"]``; ``clear`` accepted no
# ``**journal_extra``, so a caller doing everything right was still refused with
# ``TicketRequiredRed``. A year of ambient crossings had physics pointing the wrong way,
# and nothing said so because nobody was calling it to find out.
#
# The pass-through is what makes the gate reachable. The refusal below is what keeps it
# worth passing through: the four witness fields are written BY this gate, never TO it.


def test_a_gated_crossing_can_actually_be_cleared_and_the_ticket_rides():
    """THE REACHABILITY TOOTH — this is the row that was impossible before this stone.
    A crossing whose downstream gate demands a ticket now clears, because ``clear``
    forwards ``**journal_extra`` to ``emit``. Revert the pass-through and this refuses
    with ``TicketRequiredRed``, which is exactly the state the corpus was in: every
    gated crossing routed around the harbor because going through it could not work."""
    # THE FIXTURE TICKETS DIR IS GONE, and its removal is part of the same settlement:
    # this test used to fabricate a ``widget.json`` and monkeypatch ``_t._TICKETS`` at it,
    # which was safe only while nothing read the ticket's CONTENTS. The gate does now, so
    # the boat is real and the two halves of the crossing name the same voyage — which is
    # what the binding tooth below refuses to let drift apart.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        at_learn = ("code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
                    "[LEARNME] -> PROVED")
        # ``_OTHER_BOAT`` RATHER THAN ``_BOAT``, and the reason is worth a line because it
        # bit on the first run: this crossing goes into PROVED, so it meets the exit gate,
        # which refuses a ticket whose chart claim has no verdict yet. Pointing it at the
        # voyage that is running this very proof makes a circle — the proof cannot pass
        # until the verdict is written, and the verdict cannot be written until the proof
        # passes. The gate was right and the fixture was wrong.
        new = clear(
            at_learn, "PROVED",
            actor=_OWNER, boat_id=_OTHER_BOAT,
            proven_by=_PROVEN, history_path=hp, state_path=sp,
            ticket=_OTHER_BOAT,
        )
        assert "[PROVED]" in new, new
        rec = projector.read_history(hp)[0]
        assert rec["ticket"] == _OTHER_BOAT, \
            f"the ticket must ride through to the record the gates read: {rec}"
        assert rec["cleared_by"] == _OWNER and rec["proven_by"] == _PROVEN, rec
        assert "re-read at the door" in rec.get("clearance_gate", ""), (
            "and the chokepoint's own sixth seat must have re-read the seal — a crossing "
            f"through this gate satisfies that gate rather than being waived past it: {rec}")


def test_a_caller_may_not_hand_this_gate_its_own_witness():
    """THE VACUITY KILL. ``cleared_by``, ``proven_by``, ``proven_seal_date`` and
    ``delegated`` are stamped BY this gate. If a caller could pass them in, a
    self-declared clearance could never disagree with the door — which is the whole
    reason the door is worth passing through (Law 6). Each of the four is refused by
    name, before anything is written, and the refusal says which."""
    import inspect as _inspect
    named = _inspect.signature(clear).parameters
    # ``proven_by`` is on the roster too, but it can never REACH journal_extra: it is a
    # named parameter, so a caller who passes it passes it to the gate's own argument and
    # a second one is a TypeError at the call. Structure, not a check — and asserted here
    # rather than assumed, because the day it stops being named is the day the roster
    # entry stops being decorative and starts being the only thing standing there.
    assert named["proven_by"].kind is _inspect.Parameter.KEYWORD_ONLY, \
        "proven_by must stay a named parameter — that is what makes it unsmugglable"
    reachable = [f for f in ("cleared_by", "proven_seal_date", "delegated") if f not in named]
    assert len(reachable) == 3, f"all three must be reachable through journal_extra: {reachable}"
    for field in reachable:
        with tempfile.TemporaryDirectory() as tmp:
            hp, sp = _paths(tmp)
            try:
                clear(
                    _WF, "PROVEME",
                    actor=_OWNER, boat_id=_BOAT,
                    proven_by=_PROVEN, history_path=hp, state_path=sp,
                    **{field: "forged"},
                )
            except Unauthorized as e:
                assert field in str(e), f"the refusal must name the field it refused: {e}"
                assert "written BY the clearance gate" in str(e), e
            else:
                raise AssertionError(f"a caller-supplied {field!r} was accepted")
            assert not Path(hp).exists(), \
                "a refused clearance writes no record of truth — not even an empty one"


# ── THE OWNER IS READ, NOT STATED (ticket boat-owner-is-read-not-stated, 2026-08-10) ──
#
# THE NON-HOLLOW METHOD FOR THIS SET IS TWO-SIDED, AND THE SIGN IS WRITTEN DOWN HERE
# because the ticket's own wording about it is ambiguous and would let a later reader
# check the wrong one. Unambiguously: the exploit call — an actor naming ITSELF the owner
# of a boat it does not own — SUCCEEDS on the reverted code and is REFUSED on the built
# code. On the reverted code the tooth below cannot even be written the same way, because
# ``boat_owner`` was a parameter; that is the point. Revert cycle run by hand at build
# time, both directions recorded in the verdict artifact.


def test_the_owner_cannot_be_stated_by_any_route():
    """THE CENTRAL TOOTH. Four routes, because one closed door is not a closed room.

    (1) the parameter is gone; (2) the keyword does not ride ``**journal_extra`` into the
    record — this is the non-obvious one, since removing a parameter alone leaves the
    caller able to journal an unchecked ownership claim; (3) a grant cannot be minted from
    an owner the minter invented; (4) the two ids naming the voyage must agree."""
    import inspect as _inspect
    assert "boat_owner" not in _inspect.signature(clear).parameters, \
        "the owner must not be statable as an argument — that IS the ticket"

    # (2) the keyword must RAISE, not be swallowed. A signature check alone would pass
    #     while the value rode through into a record of truth.
    for smuggled in ("boat_owner", "owning_intention", "gated_by"):
        with tempfile.TemporaryDirectory() as tmp:
            hp, sp = _paths(tmp)
            try:
                clear(
                    _WF, "PROVEME",
                    actor=_OWNER, boat_id=_BOAT,
                    proven_by=_PROVEN, history_path=hp, state_path=sp,
                    **{smuggled: "fiction"},
                )
            except Unauthorized as e:
                assert smuggled in str(e) and "READ off the boat" in str(e), e
            else:
                raise AssertionError(f"a caller-supplied {smuggled!r} was accepted")
            assert not Path(hp).exists(), "a refused clearance writes no record"


def test_a_grant_minted_from_an_owner_the_minter_invented_authorizes_nothing():
    """THE HOLE THE PARENT TICKET NAMED AS EXAMINED: fixing the direct branch alone moves
    the hole one door along, because a caller who could state the owner could mint itself
    a grant from that same fictional owner and ``authorizes`` would compare the fiction to
    itself. Minting now reads the boat and refuses a minter with no standing on it."""
    try:
        mint_grant(minted_by=_IGOR, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    except Unauthorized as e:
        assert "may not mint" in str(e) and _BOAT in str(e), e
    else:
        raise AssertionError("an unadmitted hand minted itself standing on a boat")


def test_an_actor_merely_similar_to_an_admitted_one_is_refused():
    """THE GREEN-FOR-THE-WRONG-REASON KILL. The comparison replaced a substring scan over
    charter prose, and a substring scan is exactly what it must not become: an actor that
    is a prefix of an admitted one, or an admitted one with something appended, must be
    refused. Derived from the read rather than hard-coded, so the tooth still means this
    if the charter's list changes."""
    admitted = boat_owner_of(_BOAT).hands[0]
    for near in (admitted[:1], admitted + "_extra", admitted.lower(), " " + admitted):
        if near in boat_owner_of(_BOAT).hands:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            hp, sp = _paths(tmp)
            try:
                clear(
                    _WF, "PROVEME",
                    actor=near, boat_id=_BOAT,
                    proven_by=_PROVEN, history_path=hp, state_path=sp,
                )
            except Unauthorized:
                assert not Path(hp).exists(), "a refused clearance writes no record"
            else:
                raise AssertionError(
                    f"{near!r} cleared a boat whose gate admits only "
                    f"{list(boat_owner_of(_BOAT).hands)!r} — the check is scanning, not matching"
                )


def test_a_crossing_that_names_two_voyages_is_refused_before_anything_is_written():
    """``boat_id`` and ``ticket`` arrive by different routes and the docstring has called
    them the same thing since this function was written. Until this check they could
    disagree, so the owner would be read off one boat while the record was written about
    another."""
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT,
                proven_by=_PROVEN, history_path=hp, state_path=sp,
                ticket=_OTHER_BOAT,
            )
        except Unauthorized as e:
            assert "two different voyages" in str(e), e
            assert not Path(hp).exists(), "a mismatched crossing leaves the record untouched"
        else:
            raise AssertionError("a crossing named two voyages and was cleared")


def test_an_unresolvable_hop_refuses_by_name_and_never_defaults():
    """A default here IS the ticket's falsifier clause (1): the owner would once again be
    something other than what the boat says. Each hop is broken in a fixture and the
    refusal must name the address it opened. ``OwnerUnresolvable`` is deliberately not an
    ``Unauthorized`` — 'nobody says who owns this' and 'you have no standing' want
    different responses, and a reader that conflated them would go looking for a grant
    when what is missing is one line in a file."""
    with tempfile.TemporaryDirectory() as tmp:
        tickets = Path(tmp) / "tickets"
        tickets.mkdir()
        charters = Path(tmp) / "charters"
        (charters / "thing").mkdir(parents=True)

        (tickets / "no-field.json").write_text("{}", encoding="utf-8")
        (tickets / "bad-address.json").write_text(
            '{"owning_intention": "nowhere/at/all/intention+why.json"}', encoding="utf-8")
        (tickets / "no-hands.json").write_text(
            '{"owning_intention": "thing/intention+why.json"}', encoding="utf-8")
        (charters / "thing" / "intention+why.json").write_text(
            '{"owner": "a paragraph of prose that no gate can stand on"}', encoding="utf-8")

        def _why(boat):
            try:
                boat_owner_of(boat, tickets_dir=str(tickets),
                              cairn_root=str(charters), commons_root=str(charters))
            except OwnerUnresolvable as e:
                return str(e)
            raise AssertionError(f"{boat!r} resolved an owner it has no business resolving")

        assert str(tickets / "missing.json") in _why("missing"), "name the file you opened"
        assert "owning_intention" in _why("no-field")
        assert "nowhere/at/all" in _why("bad-address")
        assert "gated_by" in _why("no-hands") and "substring scan" in _why("no-hands")

    # And through the gate itself, against the REAL corpus — no injection, because ``clear``
    # accepts none. An id with no ticket behind it is the honest live case.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id="no-such-boat-has-ever-been-cast",
                proven_by=_PROVEN, history_path=hp, state_path=sp,
            )
        except OwnerUnresolvable as e:
            assert "has no ticket at" in str(e), e
            assert not Path(hp).exists(), "an unresolvable owner writes no record"
        else:
            raise AssertionError("the gate cleared a boat it could not find an owner for")


def test_the_read_reaches_nothing_outward():
    """GATE (iii) OF THE TICKET'S OWN PROVEME SET, and falsifier clause (2): the read must
    not make the gate reach outward at a crossing. Asserted structurally over the module's
    transitive imports rather than by trusting the source to look innocent — and the whole
    proof also runs under the tester with ``isolation='netns'``, where a network reach
    fails by construction rather than by an assertion somebody remembered to write."""
    import ast

    # THE SCOPE OF THIS TOOTH IS THE READ, and getting the scope right took two wrong
    # versions worth recording, because both were the same mistake in opposite directions.
    #
    # TOO NARROW: walk ``vars(module)`` for things whose ``__module__`` starts with
    # 'cairn.'. That set contains only cairn names by construction, so 'socket',
    # 'subprocess', 'urllib' and 'http' in the forbidden list below could never match and
    # sat there as decoration reading as coverage. Measured: 5 names, all 'cairn.*'.
    #
    # TOO WIDE: parse the whole transitive static import graph from this module. That
    # reaches ``cairn.base.transitions``, and through it the tester, the build inspector and
    # the chart verdict — 17 modules, three of which import ``subprocess`` because running a
    # proof under netns isolation is *supposed* to shell out. It went red on its first run
    # and the red was about somebody else's correct behaviour. A tooth that fires on normal
    # motion is the pinned-cursor defect; it would have been silenced, and silencing is how
    # a real signal gets trained away.
    #
    # THE CLAIM IS ABOUT THIS FUNCTION: ``boat_owner_of`` must not make a crossing depend on
    # anything being up. So the check is this module's own imports, plus every call the
    # resolution makes, against a whitelist. Anything not on it is a finding — which is the
    # sign that matters, since a NEW reach is exactly what this would have to catch.
    src = _REPO_ROOT / "cairn" / "harbor_master" / "clearance.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            imported.add(node.module.split(".")[0])
    assert imported, "the import scan found nothing — it is measuring itself"
    forbidden = ("socket", "requests", "urllib", "subprocess", "http", "psycopg",
                 "asyncio", "db_domain", "inference_domain")
    assert not (imported & set(forbidden)), \
        f"clearance imports {sorted(imported & set(forbidden))} — falsifier clause (2)"

    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "boat_owner_of")
    # The whitelist is FILE READS AND PURE BUILTINS — nothing that can wait on a socket, a
    # port, a process or a clock. It is enumerated rather than grown by adding whatever the
    # assertion last complained about, which would turn it into a rubber stamp that ratifies
    # the code instead of judging it.
    allowed = {"open", "isinstance", "json.loads", "os.path.join", "os.path.isfile",
               "OwnerUnresolvable", "BoatOwner", "tuple", "str", "read", "strip",
               "get", "encode", "list", "sorted", "len", "repr", "any", "all"}
    called = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            parts = []
            while isinstance(f, ast.Attribute):
                parts.append(f.attr)
                f = f.value
            if isinstance(f, ast.Name):
                parts.append(f.id)
            called.add(".".join(reversed(parts)) if parts else "<computed>")
    stray = {c for c in called if c not in allowed and c.split(".")[-1] not in allowed}
    assert not stray, (
        f"the owner resolution calls {sorted(stray)}, which is outside the files-only "
        f"whitelist — a crossing must not depend on anything being up (falsifier clause 2)"
    )
    assert "open" in called, "the resolution opens no file — it is not reading the boat at all"


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
        test_a_gated_crossing_can_actually_be_cleared_and_the_ticket_rides,
        test_a_caller_may_not_hand_this_gate_its_own_witness,
        test_the_owner_cannot_be_stated_by_any_route,
        test_a_grant_minted_from_an_owner_the_minter_invented_authorizes_nothing,
        test_an_actor_merely_similar_to_an_admitted_one_is_refused,
        test_a_crossing_that_names_two_voyages_is_refused_before_anything_is_written,
        test_an_unresolvable_hop_refuses_by_name_and_never_defaults,
        test_the_read_reaches_nothing_outward,
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
