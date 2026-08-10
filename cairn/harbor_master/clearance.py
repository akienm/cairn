"""harbor_master/clearance.py — the CLEARANCE gate: the AUTHORITY rung of a transition.

harbor_master owns the harbor through which workflows voyage. Child a (register.py) is the
TRUTH rung as an aggregate — the fleet register. This is child b: the AUTHORITY rung — the
gate that decides WHO may move a boat's cursor, and refuses every move that is not cleared.

A workflow-transition factors into THREE rungs (the emit-chokepoint trichotomy, resolved
2026-07-21):

  - RULES (Law 4) — IS this move legal for the class? Base-class physics, inherited,
    un-delegable. Lives in cairn/base/transitions.py; this gate does NOT re-implement it —
    it WRAPS it. Authority never overrides the rules: even a boat's owner cannot clear an
    illegal move, because ``emit`` validates legality before it writes.
  - AUTHORITY (Law 6) — WHO may invoke it? THIS FILE. Exactly one owner gates writes to a
    boat; delegated access happens only through the owner's gate, per-operation, never
    ambiently. An actor who is neither the owner nor the holder of a matching per-operation
    grant is refused — this is what stops devices from advancing workflows AROUND the harbor.
  - TRUTH (Law 7) — record it. Delegated to ``emit``'s journal door: the crossing appends to
    the boat's own history (carrying WHO cleared it), and the fleet register (child a) reads
    that history on demand — so the movement is recorded in both vantages with no rival copy.

And Law 8 binds here too: a cleared move summons a peer who ACTS, and the code that acts
must already be in proven-space. The caller names that code by its PROOF's address, and the
gate reads the seal beside it. It only READS the seal (confirms the code is proven) — it
never CALLS anything: the harbor clears the move, the crew sails it. A harbor that executed
would be the ground_loop-executor goof the ticket warns of.

NO REGISTRY (Akien, 2026-08-05: "methodregistry is a registry. generally we frown on
registries. why do we need one here?" — and we did not). Until today this rung asked an
in-memory ``MethodRegistry``, re-instated from the ground_loop driver-executor, which had
DISPATCHED and so genuinely needed a name -> callable map. That executor role was stripped as
a goof; the registry came back with its map intact and its consumer changed, and this gate
threw the callable away on the line it received it — it only ever wanted a yes or no. Law 1
forbids re-deriving a settled answer; it does not license carrying one forward when the
question moved. Three things the removal buys, none of them tidiness:

  - NO SECOND COPY. "This passed under the tester" already lives beside the proof, at an
    address DERIVED from the proof's own path (73 trails on disk). There was nothing to look
    up; the registry held a rival record of a fact that attaches at its own endpoint (Law 6).
  - THE HORIZON IS ENFORCED. A registry entry cached a bool with no expiry and kept answering
    green after the code moved. The seal carries a source fingerprint, so a stale green is a
    REFUSAL now (Law 3 — a VALIDATION expires).
  - NOTHING TO POPULATE. The registry admitted a method by RE-RUNNING its proof at wiring
    time; a restart lost the lot. Reading a seal costs a file read and survives everything.

So the gate binds FOUR refusals before a cursor moves — unauthorized (Law 6), unproven
(Law 8), illegal (Law 4, via the wrapped chokepoint), and unresourced — and only then does
the truth get written (Law 7). Cooperative, not policed: there is no enforcer here, only a
gate the one owner holds (the db_domain pattern — no other door). Forgery is not the threat
model on a single-owner cooperative box; AMBIENT authority is — an actor moving a boat with
no grant, or reusing one grant across operations. That is exactly what a per-operation grant
refuses.

THE FOURTH REFUSAL — UNRESOURCED (ratified by Akien 2026-08-04). A move that summons a
builder onto a host with no room for it fails as surely as an illegal one, just louder and
later. Measured from experience: past ~6 concurrent builders this box crawls, past 8 it heads
for a hard crash. The gate that already holds up the license to advance is where that is
answered — "it's not asking the system anymore, it's asking the harbormaster, because that's
the entity that would hold up the license to advance."

Three things this is NOT, each load-bearing:
  - NOT A COUNT. Nothing here or anywhere counts live builders — that would be a manager, and
    a manager is what this system does not have. Admission is decided from PRESSURE, which is
    directly observable, not from POPULATION, which would need a census someone owns. The
    fleet register (child a) is never consulted to gate a build; it reports, it does not
    manage.
  - NOT A READING. system_rackmount answers a VERDICT — "your line is crossed" — never a
    number. The harbor owns the LINE; the system device owns the METRIC. Either can change
    without the other knowing (Law 6).
  - NOT A SCHEDULER. The gate answers when asked. It never dispatches, never assigns, never
    starts anything. Initiative stays with the boat: each device owns its own task of checking
    whether it can start, and this is the door it checks at.

    python3 cairn/harbor_master/proofs/test_clearance.py     # exit 0 = green
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from cairn.base.transitions import emit
from cairn.tester.validation_store import standing

# How long a minted grant stays spendable. RULED BY AKIEN AT 10 SECONDS, 2026-08-04: "the thing
# asks for it, and has 10 seconds to take it to the build gate."
#
# The floor on this number is how long a launch takes to become VISIBLE to the resource owner:
# a grant that lapses before the thing it cleared shows up in the reading leaves the next asker
# blind for the gap. MEASURED: system_rackmount's runnable-count reading reflects a new load in
# under a second, so 10s clears that floor with room to spare. It would NOT have cleared it
# against the decaying load average that device served until today (~60s to reflect the same
# event) — the TTL and the metric swap are one decision, not two.
GRANT_TTL_SECONDS = 10.0

# The harbor's OWN lines — the values it holds up against system_rackmount's verdicts. The
# harbor owns these; the system device owns how they are measured, and neither needs the other's
# half. cpu: 6 of 8 cores runnable is 75%, the top of the range Akien measured as still workable.
# memory: a HYPOTHESIS, not a measurement (Law 3) — no one has yet measured what a builder needs
# to not thrash, so this is a placeholder holding the seam open, labelled as one.
HARBOR_LINES: dict[str, float] = {"cpu_threshold": 75.0, "memory_floor": 1024.0}

# THE WITNESS FIELDS — what this gate stamps on a crossing's record, and therefore what a
# caller may never hand in through ``journal_extra``. These are the evidence the chokepoint's
# clearance check reads back (ticket emit-refuses-an-uncleared-crossing, 2026-08-10): if a
# caller could supply them, an uncleared crossing could dress itself as a cleared one and the
# gate downstream would have no way to tell. The set is the exact spread ``clear`` writes at
# its ``emit`` call — kept beside the writing so the two cannot drift apart.
_GATE_WITNESS_FIELDS = frozenset({"cleared_by", "proven_by", "proven_seal_date", "delegated"})


class Unauthorized(Exception):
    """The actor may not move this boat: not its owner, and holds no matching grant (Law 6).

    Loud, never silent (Law 7) — an ambient advance that slips through unrecorded is the
    failure this gate exists to make impossible."""


class GrantExpired(Unauthorized):
    """The grant was real and named exactly this operation — and it lapsed before it was spent.

    A subclass of ``Unauthorized`` on purpose: an expired grant authorizes nothing, so every
    guarantee that holds for "no grant" must hold identically here, including that the refused
    move leaves NO record. The distinct name exists so a caller can tell "you were never
    allowed" from "you waited too long" — those want different responses from the asker."""


class Unproven(Exception):
    """The code this move would summon is not in proven-space RIGHT NOW (Law 8).

    Replaces ``registry.UnprovenMethod``, and the rename is the design change: there is no
    METHOD name any more, only the address of a proof and the seal beside it. Four ways to
    earn this refusal, and the reader (``validation_store.standing``) says which in one pass —
    never sealed, newest seal red, sealed green but carrying no fingerprint, or sealed green
    with the horizon closed because the code moved underneath it."""


class Unresourced(Exception):
    """The host has no room for what this move would summon — the fourth refusal.

    Not an authority failure and not a rules failure: the actor was entitled, the move was
    legal, and the answer is still no. It carries no reading, because the gate never received
    one — only which line was crossed (Law 6)."""


@dataclass(frozen=True)
class Grant:
    """A per-operation delegation: the owner authorizes ONE actor to make ONE transition on
    ONE boat, WITHIN A WINDOW. Frozen and specific by construction — it cannot be widened after
    minting, and it authorizes nothing but the exact (boat, target, actor) it names, for as long
    as it names. Non-ambient physics: authority is a thing you hold FOR an operation, not a
    standing capability you keep — and the expiry is what stops "for an operation" from quietly
    becoming "forever" whenever an operation is slow to happen.

    The window is also what makes a lagging instrument safe. A resource verdict is true when it
    is given and decays from there; a grant that never expired would let a builder bank a yes
    from a quiet moment and spend it into a loaded box. Ten seconds is the leash on that."""

    boat_id: str
    target: str
    to_actor: str
    by_owner: str
    issued_at: float = field(default_factory=time.monotonic)
    ttl_seconds: float = GRANT_TTL_SECONDS

    def authorizes(self, *, boat_id: str, target: str, actor: str, owner: str) -> bool:
        """True only for the exact operation this grant names, issued by this boat's owner.

        IDENTITY ONLY — it deliberately does not consider the clock. "This grant was never for
        you" and "this grant lapsed" are different answers to the asker, so the gate asks them
        separately and refuses with different names."""
        return (
            self.by_owner == owner
            and self.boat_id == boat_id
            and self.target == target
            and self.to_actor == actor
        )

    def expired(self, now: float | None = None) -> bool:
        """Has the window closed? ``now`` is injectable so the expiry is provable without a
        sleep — a proof that waits on a wall clock is a flake with a schedule."""
        if now is None:
            now = time.monotonic()
        return (now - self.issued_at) >= self.ttl_seconds


def mint_grant(*, owner: str, boat_id: str, to_actor: str, target: str,
               now: float | None = None, ttl_seconds: float = GRANT_TTL_SECONDS) -> Grant:
    """The owner delegates ONE operation — the only door delegation passes through (Law 6).

    Minting IS the owner's act: on a cooperative single-owner box the authority is that the
    boat's rightful owner is the one constructing the capability. The gate later checks the
    grant was minted BY this boat's owner (``by_owner == boat_owner``), so a grant carrying
    someone else's name authorizes nothing.

    The mint stamps the clock. There is no way to mint an unexpiring grant — the window is a
    property of the capability, not an option a caller can decline.
    """
    return Grant(
        boat_id=boat_id, target=target, to_actor=to_actor, by_owner=owner,
        issued_at=time.monotonic() if now is None else now,
        ttl_seconds=ttl_seconds,
    )


def clear(
    workflow_str: str,
    target: str,
    *,
    actor: str,
    boat_id: str,
    boat_owner: str,
    proven_by: str,
    grant: Grant | None = None,
    history_path: str | None = None,
    state_path: str | None = None,
    node_class_root=None,
    resources=None,
    lines: dict | None = None,
    now: float | None = None,
    **journal_extra,
) -> str:
    """Clear a transition, or refuse it — the authority rung wrapping the rules+truth chokepoint.

    WHAT A CC-MADE CROSSING NAMES (settled 2026-08-10, ticket
    emit-refuses-an-uncleared-crossing). The four arguments below are not free text, and
    until this settlement they had never been supplied by anything but a proof. The door
    may not mint them — a door-minted value can never disagree with the door, which is the
    same two-witness argument that killed auto-inherit for chart claims — so they are
    stated here, at the owner's address, and the caller supplies them:

      - ``actor`` — WHO MOVED THE BOAT. For a crossing CC makes, the string is ``"CC"``.
        Measured before settling: 16 records already carried an ``actor`` and already
        carried TWO spellings for one mover — ``"CC"`` x12 and ``"claude"`` x4 — because
        nothing had ever gated the field. The majority spelling wins on the ordinary
        ground that it is what Akien calls this hand. The 4 dissenting records are NOT
        repaired: they are a record of truth and they were never improper (Law 7).
      - ``boat_owner`` — WHO OWNS THE VOYAGE, in the same namespace as ``actor``. For a
        voyage CC sails on Akien's box that is ``"CC"``, so ``actor == boat_owner`` and the
        move is the owner acting directly (``delegated`` False). CORRECTED 2026-08-10 by
        the first live fire, and the wrong answer is kept here because it is the instructive
        one: this paragraph first said "THE COMPONENT WHOSE HISTORY IS BEING APPENDED TO —
        for a crossing journaled at cairn/base/history.json that is 'base'". The gate
        compares ``actor`` against ``boat_owner`` for IDENTITY, so a component name puts the
        two in different namespaces and every CC crossing refuses as ``Unauthorized``, which
        is exactly what the first real call did. The component owns its history FILE; the
        boat's owner is a mover, and the two are different ownerships that happened to share
        a word.

        AND THE HOLE THIS LEAVES IS NAMED, not papered over (ticket
        ``boat_owner-is-read-not-stated``). The caller states BOTH sides of the identity
        the gate checks, so a caller can always make them equal — the Law 6 refusal binds an
        honest caller and nothing else. It is not vacuous by accident: the failure the rung
        exists for is *a device advancing a boat it does not own*, and that needs
        ``boat_owner`` read from the BOAT rather than supplied alongside the actor. Nothing
        on disk carries it today (the ticket's ``owner`` field is prose about components,
        which is the very confusion corrected above). Until that lands, this argument is a
        declaration and the gate's other three refusals — proven-space, resources, rules —
        are the ones doing load-bearing work.
      - ``boat_id`` — THE TICKET. It is already on every gated crossing, so this adds no
        new vocabulary; it names WHICH voyage is moving, where ``boat_owner`` names whose
        water it moves in.
      - ``proven_by`` — THE PROOF THIS MOVE IS CLEARED ONTO, sealed and still describing
        the code as it stands. For a voyage this is the proof its own PROVEME step just
        sealed, which is what makes clearance affordable at all: proven-space is a FRESH
        state that decays (measured 2026-08-10: only 4 of 78 proofs in the corpus were
        standing, and they were the four most recently sealed), so the honest moment to
        lean on a seal is the moment after it is cut.

    ``**journal_extra`` rides through to ``emit`` untouched, and it is not a convenience:
    WITHOUT IT THIS FUNCTION WAS UNCALLABLE FOR EVERY CROSSING THAT MATTERS. Three gates
    at the chokepoint read ``journal_extra["ticket"]`` — the entry gate at BUILDME, the
    exit gate at PROVED, the emission gate at a carried WATCHME — and each refuses a
    crossing that names no cast ticket. Before 2026-08-10 ``clear`` accepted no such
    argument, so a caller who did everything right was still refused at the door with
    ``TicketRequiredRed``. That is the measured reason the authority rung went a year with
    no production caller: not discipline, but physics pointing the wrong way — the ticket
    gate that landed 2026-07-29 made the clearance gate structurally unreachable, and
    nothing said so because nobody was calling it to find out.

    Binds four refusals before the cursor may move, then records the crossing:
      1. AUTHORITY (Law 6): ``actor`` must be the boat's owner, or hold a ``grant`` that
         authorizes exactly this (boat_id, target, actor), was minted by ``boat_owner``, and
         has not lapsed. Otherwise → ``Unauthorized`` (or ``GrantExpired``, its subclass, when
         the grant named the right operation but its window closed). Checked first: an actor
         with no standing here is turned away before anything else is inspected.
      2. PROVEN-SPACE (Law 8): ``proven_by`` is the ADDRESS OF A PROOF — the code this move
         summons is the component that proof lives in. The seal beside it must be green AND
         still describe the code as it stands (the source fingerprint the tester recorded).
         Otherwise → ``Unproven``. The seal is read, nothing is called — the harbor clears the
         move, it does not sail it. There is no registry to populate: the proof's address IS
         the key, and a stale green refuses (Law 3).
      3. RESOURCES: if this harbor was wired to a resource owner, every line in ``lines`` is
         put to it and a crossed line refuses the move → ``Unresourced``. ``resources`` is
         anything with ``ask(name, value) -> bool`` (system_rackmount's may-I door). The
         harbor holds the LINES; the resource owner holds the METRICS and answers only a
         verdict, so neither half can drift into the other (Law 6). Left un-wired
         (``resources=None``) this gate does not run, and the harbor is honestly a harbor with
         no view of the host — not a harbor that decided there was room.
      4. RULES + TRUTH (Law 4/7): ``emit`` validates legality against the class's versioned
         table and, only if legal, journals the crossing through the projector's write-door
         (append-only, carrying ``cleared_by`` and whether it was delegated). An illegal
         move → ``IllegalTransition`` and NOTHING is written — authority never buys an
         illegal transition.

    Returns the new workflow string (cursor moved to ``target``). Every refusal raises before
    ``emit`` is reached, so a refused move leaves no partial record (unauthorised OR unproven
    OR unresourced OR illegal ⇒ un-recorded).
    """
    # 0. THE WITNESS IS THE GATE'S TO WRITE. A caller may enrich the record through
    #    ``journal_extra``, but it may not hand in the very fields this gate exists to
    #    stamp — a self-declared ``cleared_by`` is exactly the door-minted value the
    #    ticket's falsifier clause (3) names, and letting one through silently would make
    #    the authority check vacuous at the one door that reads it. Refused LOUDLY rather
    #    than dropped: a quietly discarded field is a record of truth collapsing an error
    #    into a coherent shape, which Law 7 forbids at exactly this surface.
    _witness = _GATE_WITNESS_FIELDS & journal_extra.keys()
    if _witness:
        raise Unauthorized(
            f"a caller may not hand this gate its own witness: {sorted(_witness)} "
            f"{'is' if len(_witness) == 1 else 'are'} written BY the clearance gate, never "
            "to it. A self-declared clearance can never disagree with the door, which is "
            "the whole reason the door is worth passing through (Law 6). Drop the field "
            "and let the gate stamp it."
        )

    # 1. AUTHORITY (Law 6) — owner acts directly, or a matching per-operation grant delegates.
    if actor != boat_owner:
        if grant is None or not grant.authorizes(
            boat_id=boat_id, target=target, actor=actor, owner=boat_owner
        ):
            raise Unauthorized(
                f"{actor!r} may not move boat {boat_id!r} to {target!r}: not its owner "
                f"({boat_owner!r}), and holds no grant for THIS operation — authority is "
                f"per-operation and non-ambient (Law 6)"
            )
        if grant.expired(now):
            raise GrantExpired(
                f"{actor!r} holds a grant for boat {boat_id!r} -> {target!r} that LAPSED: "
                f"minted with a {grant.ttl_seconds}s window and spent after it closed. Ask "
                f"again — a stale yes is not a yes, because what it was true about has moved"
            )

    # 2. PROVEN-SPACE (Law 8) — the code the move summons must be proven, and still be the code
    #    that was proven. One file read at a derived address; no registry, nothing to populate.
    proven = standing(proven_by)
    if not proven["proven"]:
        raise Unproven(
            f"{actor!r} may not move boat {boat_id!r} to {target!r} onto code that is not in "
            f"proven-space: {proven['why']}. The harbor clears only onto proven code (Law 8)"
        )

    # 3. RESOURCES — the fourth refusal. The harbor asks the resource owner about ITS OWN lines
    #    and receives a verdict, never a reading. Nothing here counts anything: a line is about
    #    PRESSURE on the host, and pressure is observable without a census of who is causing it.
    if resources is not None:
        for name, value in (HARBOR_LINES if lines is None else lines).items():
            if resources.ask(name, value):
                raise Unresourced(
                    f"the host has no room to move boat {boat_id!r} to {target!r}: the harbor's "
                    f"{name} line ({value}) is crossed. The move is authorized, proven and legal "
                    f"— and still refused. Ask again when the box is quieter"
                )

    # 4. RULES + TRUTH (Law 4/7) — wrap the chokepoint: it refuses the illegal, journals the legal.
    emit_kwargs = {}
    if node_class_root is not None:
        emit_kwargs["node_class_root"] = node_class_root
    return emit(
        workflow_str,
        target,
        history_path=history_path,
        state_path=state_path,
        cleared_by=actor,
        # AND THE ORDINARY FIELD TOO, not only the gate's witness. ``actor`` is the record
        # vocabulary every existing reader uses for "who moved the boat" — the corpus census
        # in troubles/every-crossing-goes-around-the-clearance-gate, the probes at
        # cairn/*/probes/, the state window. ``cleared_by`` is a different claim: that the
        # authority rung RAN, and who it cleared. On a cleared crossing the two carry the
        # same string by construction, and that is not redundancy to trim — dropping
        # ``actor`` would make the first cleared crossings in the system's life invisible to
        # every census already written, which is the failure of keeping a word and replacing
        # what fills it. Stamped here rather than accepted from ``journal_extra`` because
        # ``actor`` is a named parameter of this function: a caller cannot supply it twice.
        actor=actor,
        # The record of truth names the PROOF the clearance leaned on and the seal's date, so a
        # reader a year out can go and look at the same evidence the gate looked at rather than
        # taking "it was proven" on the record's word (Law 5 — the proof shares the address).
        proven_by=proven_by,
        proven_seal_date=proven["seal"]["date"],
        delegated=(actor != boat_owner),
        # The caller's own fields ride through untouched — ``ticket`` above all, which the
        # entry/exit/emission gates each demand and which this rung had no way to carry
        # until 2026-08-10. Spread LAST so a caller can enrich ``standing`` the same way a
        # bare ``emit`` caller can. It may NOT carry a witness field — see the refusal above.
        **journal_extra,
        **emit_kwargs,
    )
