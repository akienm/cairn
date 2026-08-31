"""codemonkey/constraint_proof.py — three-sided constraint proof lifecycle.

Every constraint carries evidence (Law 10):
  1. Founding incident — the measurement that created the constraint
  2. Live catch — the device catching a violation is the ongoing proof
  3. Retirement — when the underlying cause is gone, the constraint retires
     (marked, not deleted)

A retired constraint is a constraint whose cause was removed. It is still in the
record (Law 7) but no longer fires in challenge.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ConstraintProof:
    """The proof lifecycle for one constraint."""
    constraint_name: str
    founding_incident: dict[str, Any]
    catches: list[dict[str, Any]] = field(default_factory=list)
    retired: bool = False
    retirement_reason: str = ""
    retirement_at: str = ""

    def record_catch(self, context: str, at: str | None = None) -> dict[str, Any]:
        """Record a live catch — the constraint fired on a real violation."""
        catch = {
            "context": context,
            "at": at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.catches.append(catch)
        return catch

    def retire(self, reason: str, at: str | None = None) -> None:
        """Retire the constraint — the underlying cause is gone."""
        self.retired = True
        self.retirement_reason = reason
        self.retirement_at = at or datetime.now(timezone.utc).isoformat(timespec="seconds")

    @property
    def is_active(self) -> bool:
        return not self.retired

    @property
    def catch_count(self) -> int:
        return len(self.catches)

    def to_dict(self) -> dict[str, Any]:
        return {
            "constraint_name": self.constraint_name,
            "founding_incident": self.founding_incident,
            "catches": self.catches,
            "catch_count": self.catch_count,
            "retired": self.retired,
            "retirement_reason": self.retirement_reason,
            "retirement_at": self.retirement_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ConstraintProof:
        proof = cls(
            constraint_name=d["constraint_name"],
            founding_incident=d["founding_incident"],
            catches=d.get("catches", []),
            retired=d.get("retired", False),
            retirement_reason=d.get("retirement_reason", ""),
            retirement_at=d.get("retirement_at", ""),
        )
        return proof


def save_proof(project_root: Path, proof: ConstraintProof) -> Path:
    """Save a constraint proof to the project's constraints directory."""
    proofs_dir = project_root / "constraints" / "proofs"
    proofs_dir.mkdir(parents=True, exist_ok=True)
    safe_name = proof.constraint_name.replace("/", "_").replace(" ", "_").lower()
    path = proofs_dir / f"{safe_name}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(proof.to_dict(), indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    return path


def load_proof(project_root: Path, constraint_name: str) -> ConstraintProof | None:
    """Load a constraint proof by name."""
    proofs_dir = project_root / "constraints" / "proofs"
    safe_name = constraint_name.replace("/", "_").replace(" ", "_").lower()
    path = proofs_dir / f"{safe_name}.json"
    if not path.exists():
        return None
    try:
        return ConstraintProof.from_dict(json.loads(path.read_text()))
    except (json.JSONDecodeError, KeyError):
        return None


def load_all_proofs(project_root: Path) -> list[ConstraintProof]:
    """Load all constraint proofs for a project."""
    proofs_dir = project_root / "constraints" / "proofs"
    if not proofs_dir.is_dir():
        return []
    proofs = []
    for p in sorted(proofs_dir.glob("*.json")):
        try:
            proofs.append(ConstraintProof.from_dict(json.loads(p.read_text())))
        except (json.JSONDecodeError, KeyError):
            continue
    return proofs
