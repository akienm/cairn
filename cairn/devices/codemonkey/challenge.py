"""codemonkey/challenge.py — adversarial type-check of proposed changes.

The first visible payoff: a proposed change is type-checked against the positive
and negative types, and a match with a negative type surfaces what CC needs to
know BEFORE the code is written.

This is not a gate — it surfaces information as a peer (Law 6). A warning is
advisory, not blocking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cairn.devices.codemonkey.types import PatternType, TypePolarity
from cairn.devices.codemonkey.unify import unify, UnificationResult
from cairn.devices.codemonkey.project import load_types, load_constraints
from cairn.devices.codemonkey.constraint_proof import (
    ConstraintProof, load_proof, save_proof, load_all_proofs,
)


@dataclass
class ChallengeResult:
    """The result of challenging a proposed change."""
    violations: list[UnificationResult]
    boundary_warnings: list[UnificationResult]
    clean: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "violations": [v.to_dict() for v in self.violations],
            "boundary_warnings": [w.to_dict() for w in self.boundary_warnings],
            "clean": self.clean,
            "violation_count": len(self.violations),
            "boundary_warning_count": len(self.boundary_warnings),
        }


def challenge(change_signals: list[str], project: str,
              project_root=None, threshold: float = 0.3) -> ChallengeResult:
    """Type-check a proposed change against the project's pattern library.

    change_signals: descriptions of what the change does (e.g. "adding learning
    to ground_loop", "modifying the heartbeat interval").

    Returns violations (negative type matches) and boundary warnings (positive
    type conflicts) with evidence.
    """
    library = load_types(project)

    matches = unify(change_signals, library, threshold=threshold)

    violations = [m for m in matches if m.pattern.polarity == TypePolarity.NEGATIVE]
    boundary_warnings = [m for m in matches if m.pattern.polarity == TypePolarity.POSITIVE]

    if violations and project_root is not None:
        for v in violations:
            _record_catch(project_root, v)

    return ChallengeResult(
        violations=violations,
        boundary_warnings=boundary_warnings,
        clean=len(violations) == 0,
    )


def _record_catch(project_root, result: UnificationResult) -> None:
    """Record a live catch on the constraint's proof lifecycle."""
    proof = load_proof(project_root, result.pattern.name)
    if proof is None:
        proof = ConstraintProof(
            constraint_name=result.pattern.name,
            founding_incident={
                "source": result.pattern.source,
                "why": result.pattern.why,
            },
        )
    evidence_str = "; ".join(result.evidence) if result.evidence else "signal match"
    proof.record_catch(context=evidence_str)
    save_proof(project_root, proof)
