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
must already be in proven-space. The gate resolves the fulfilling method against the
re-instated method-registry (registry.py) and refuses an unproven one. It only RESOLVES the
method (confirms it is proven) — it never CALLS it: the harbor clears the move, the crew
sails it. A harbor that executed would be the ground_loop-executor goof the ticket warns of.

So the gate binds three refusals before a cursor moves — unauthorized (Law 6), unproven
(Law 8), illegal (Law 4, via the wrapped chokepoint) — and only then does the truth get
written (Law 7). Cooperative, not policed: there is no enforcer here, only a gate the one
owner holds (the db_domain pattern — no other door). Forgery is not the threat model on a
single-owner cooperative box; AMBIENT authority is — an actor moving a boat with no grant,
or reusing one grant across operations. That is exactly what a per-operation grant refuses.

    python3 cairn/harbor_master/proofs/test_clearance.py     # exit 0 = green
"""

from __future__ import annotations

from dataclasses import dataclass

from cairn.base.transitions import emit
from cairn.harbor_master.registry import MethodRegistry


class Unauthorized(Exception):
    """The actor may not move this boat: not its owner, and holds no matching grant (Law 6).

    Loud, never silent (Law 7) — an ambient advance that slips through unrecorded is the
    failure this gate exists to make impossible."""


@dataclass(frozen=True)
class Grant:
    """A per-operation delegation: the owner authorizes ONE actor to make ONE transition on
    ONE boat. Frozen and specific by construction — it cannot be widened after minting, and
    it authorizes nothing but the exact (boat, target, actor) it names. Non-ambient physics:
    authority is a thing you hold FOR an operation, not a standing capability you keep."""

    boat_id: str
    target: str
    to_actor: str
    by_owner: str

    def authorizes(self, *, boat_id: str, target: str, actor: str, owner: str) -> bool:
        """True only for the exact operation this grant names, issued by this boat's owner."""
        return (
            self.by_owner == owner
            and self.boat_id == boat_id
            and self.target == target
            and self.to_actor == actor
        )


def mint_grant(*, owner: str, boat_id: str, to_actor: str, target: str) -> Grant:
    """The owner delegates ONE operation — the only door delegation passes through (Law 6).

    Minting IS the owner's act: on a cooperative single-owner box the authority is that the
    boat's rightful owner is the one constructing the capability. The gate later checks the
    grant was minted BY this boat's owner (``by_owner == boat_owner``), so a grant carrying
    someone else's name authorizes nothing.
    """
    return Grant(boat_id=boat_id, target=target, to_actor=to_actor, by_owner=owner)


def clear(
    workflow_str: str,
    target: str,
    *,
    actor: str,
    boat_id: str,
    boat_owner: str,
    method: str,
    registry: MethodRegistry,
    grant: Grant | None = None,
    history_path: str | None = None,
    state_path: str | None = None,
    node_class_root=None,
) -> str:
    """Clear a transition, or refuse it — the authority rung wrapping the rules+truth chokepoint.

    Binds three refusals before the cursor may move, then records the crossing:
      1. AUTHORITY (Law 6): ``actor`` must be the boat's owner, or hold a ``grant`` that
         authorizes exactly this (boat_id, target, actor) and was minted by ``boat_owner``.
         Otherwise → ``Unauthorized``. Checked first: an actor with no standing here is
         turned away before anything else is inspected.
      2. PROVEN-SPACE (Law 8): ``method`` must resolve in ``registry`` (its proof passed
         under the tester). Otherwise → ``UnprovenMethod``. The method is resolved, never
         called — the harbor clears the move, it does not sail it.
      3. RULES + TRUTH (Law 4/7): ``emit`` validates legality against the class's versioned
         table and, only if legal, journals the crossing through the projector's write-door
         (append-only, carrying ``cleared_by`` and whether it was delegated). An illegal
         move → ``IllegalTransition`` and NOTHING is written — authority never buys an
         illegal transition.

    Returns the new workflow string (cursor moved to ``target``). Every refusal raises before
    ``emit`` is reached, so a refused move leaves no partial record (unauthorised OR unproven
    OR illegal ⇒ un-recorded).
    """
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

    # 2. PROVEN-SPACE (Law 8) — the method the move summons must already be proven.
    registry.resolve(method)  # raises UnprovenMethod if it never cleared the tester's gate

    # 3. RULES + TRUTH (Law 4/7) — wrap the chokepoint: it refuses the illegal, journals the legal.
    emit_kwargs = {}
    if node_class_root is not None:
        emit_kwargs["node_class_root"] = node_class_root
    return emit(
        workflow_str,
        target,
        history_path=history_path,
        state_path=state_path,
        cleared_by=actor,
        method=method,
        delegated=(actor != boat_owner),
        **emit_kwargs,
    )
