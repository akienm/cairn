"""method-registry — 'proven-space', made a place a driver's method-pointer resolves from.

A driver introduces NO new code (operational-driver's founding rule, Law 8): it only WIRES
a method that is already proven. That makes 'proven-space' something a resolver needs to
consult — so here it is a real registry with a real gate, not a label anyone can claim.

THE GATE IS THE TESTER (Law 8, made physics). A method is admitted only if its proof passes
UNDER THE TESTER — the same notary that attests every other stone. Admission is not 'the
caller asserted it's proven'; it is 'the tester ran the proof and it went green'. A method
registered with a failing (or missing) proof is refused, loudly. ``resolve`` returns the
method only for names that cleared that gate; anything else raises — so the ground_loop
cannot run a method that is not in proven-space.

v0 scope (round-three: simplest provable version): the registry is IN-MEMORY, populated by
``register`` calls at wiring time. A DURABLE registry (methods surviving a restart, resolved
by a stored proof-pointer) is a filed edge — no consumer has pulled it yet; the ground_loop
and its drivers live in one process today.
"""

from __future__ import annotations

from cairn.tester.device import GREEN, TesterDevice


class UnprovenMethod(Exception):
    """A method-pointer that does not resolve to proven-space. Loud, never swallowed (Law 8)."""


class MethodRegistry:
    """The names a driver may wire, each gated into proven-space by the tester."""

    def __init__(self, tester: TesterDevice | None = None) -> None:
        # The gate is injectable so a proof can hand in a specific tester; default is the real one.
        self._tester = tester or TesterDevice()
        self._methods: dict[str, dict] = {}  # name -> {"method", "proof", "validation"}

    def register(self, name: str, method, proof_path) -> dict:
        """Admit ``method`` under ``name`` — only if ``proof_path`` passes under the tester.

        Returns the admitting VALIDATION (the evidence of proven-space). Raises
        ``UnprovenMethod`` if the proof does not go green — a driver wires only proven code.
        """
        validation = self._tester.run_proof(proof_path)
        if validation["verdict"] != GREEN:
            raise UnprovenMethod(
                f"refusing to admit {name!r}: its proof {proof_path} did not pass under the "
                f"tester (verdict={validation['verdict']}) — a driver wires only proven methods (Law 8)"
            )
        self._methods[name] = {"method": method, "proof": str(proof_path), "validation": validation}
        return validation

    def resolve(self, name: str):
        """Return the proven method for ``name``, or refuse — the guard the ground_loop leans on.

        Refusal is the physics: an unregistered name never resolved to proven-space, so it
        cannot be run. This is where Law 8 stops a driver from introducing unproven code.
        """
        entry = self._methods.get(name)
        if entry is None:
            raise UnprovenMethod(
                f"{name!r} does not resolve to proven-space — no proven method is registered "
                f"under it (Law 8: a driver wires only proven methods)"
            )
        return entry["method"]

    def validation_for(self, name: str) -> dict | None:
        """The VALIDATION that admitted ``name`` (its proof-of-proven), or None if unknown."""
        entry = self._methods.get(name)
        return entry["validation"] if entry else None

    def names(self) -> list[str]:
        return list(self._methods)
