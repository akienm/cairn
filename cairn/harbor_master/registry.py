"""harbor_master/registry.py — the METHOD-REGISTRY: 'proven-space', made resolvable.

RE-INSTATED, NOT RE-DERIVED (Law 1). This is the method-registry that was born with the
ground_loop driver-executor (cairn 584aa74) and retired when the ground_loop was stripped
to the heartbeat (cairn a535de0) — its executor role was a goof, but the registry itself
was a settled, proven design: a place a method-pointer resolves from, gated into
proven-space by the tester. The clearance gate is the consumer that finally pulls it, so it
returns here (tickets/harbor-master.json child b) with its design carried forward, not
re-argued from scratch.

WHY THE CLEARANCE GATE NEEDS IT. A cleared transition summons a peer who ACTS — and the
code that acts must already be in proven-space (Law 8: nothing enters proven-space without
a proof a hollow build couldn't pass). Authority (Law 6 — who may) and proven-space (Law 8
— what code runs) are the two things the harbor checks before it lets a boat's cursor move;
this registry is the second. Clearing a move whose fulfilling method is unproven would be a
green light that means nothing — the exact defect the whole system exists to kill.

THE GATE IS THE TESTER (Law 8 as physics). A method is admitted only if its proof passes
UNDER THE TESTER — the same notary that attests every other stone. Admission is not 'the
caller asserted it's proven'; it is 'the tester ran the proof and it went green'. ``resolve``
returns the method only for names that cleared that gate; anything else raises — so the
harbor cannot clear a move onto an unproven method.

v0 scope (unchanged from the retired original — no consumer has pulled more): the registry
is IN-MEMORY, populated by ``register`` calls at wiring time. A DURABLE registry (methods
surviving a restart, resolved by a stored proof-pointer) is a filed edge — build-minimal.
"""

from __future__ import annotations

from cairn.tester.device import GREEN, TesterDevice


class UnprovenMethod(Exception):
    """A method-pointer that does not resolve to proven-space. Loud, never swallowed (Law 8)."""


class MethodRegistry:
    """The names the harbor may clear a move onto, each gated into proven-space by the tester."""

    def __init__(self, tester: TesterDevice | None = None) -> None:
        # The gate is injectable so a proof can hand in a specific tester; default is the real one.
        self._tester = tester or TesterDevice()
        self._methods: dict[str, dict] = {}  # name -> {"method", "proof", "validation"}

    def register(self, name: str, method, proof_path) -> dict:
        """Admit ``method`` under ``name`` — only if ``proof_path`` passes under the tester.

        Returns the admitting VALIDATION (the evidence of proven-space). Raises
        ``UnprovenMethod`` if the proof does not go green — the harbor clears only onto
        proven code (Law 8).
        """
        validation = self._tester.run_proof(proof_path)
        if validation["verdict"] != GREEN:
            raise UnprovenMethod(
                f"refusing to admit {name!r}: its proof {proof_path} did not pass under the "
                f"tester (verdict={validation['verdict']}) — proven-space is the tester's, "
                f"not a label anyone can claim (Law 8)"
            )
        self._methods[name] = {"method": method, "proof": str(proof_path), "validation": validation}
        return validation

    def resolve(self, name: str):
        """Return the proven method for ``name``, or refuse — the guard the clearance gate leans on.

        Refusal is the physics: an unregistered name never resolved to proven-space, so a
        move onto it cannot be cleared. This is where Law 8 stops the harbor from clearing
        a transition onto unproven code.
        """
        entry = self._methods.get(name)
        if entry is None:
            raise UnprovenMethod(
                f"{name!r} does not resolve to proven-space — no proven method is registered "
                f"under it (Law 8: the harbor clears only onto proven methods)"
            )
        return entry["method"]

    def validation_for(self, name: str) -> dict | None:
        """The VALIDATION that admitted ``name`` (its proof-of-proven), or None if unknown."""
        entry = self._methods.get(name)
        return entry["validation"] if entry else None

    def names(self) -> list[str]:
        return list(self._methods)
