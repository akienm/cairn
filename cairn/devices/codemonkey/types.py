"""codemonkey/types.py — the type system for positive and negative patterns.

Graph tree paths ARE the type system. A component's intention becomes its positive
type (what it IS), corrections become negative types (what it ISN'T), proposed
changes are type-checked by unification.

Project-agnostic: no cairn-specific field names or references. Any codebase that
can produce a pattern with a name, a why, and signals can use this schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TypePolarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


@dataclass(frozen=True)
class PatternSignal:
    """One observable signal that suggests a pattern is present or violated."""
    description: str
    weight: float = 1.0


@dataclass(frozen=True)
class PatternType:
    """A typed pattern entry — the unit the library stores and challenge reads.

    Positive types describe what a thing IS (its structural identity).
    Negative types describe what has gone wrong (corrections, mistakes, constraints).
    The polarity is the only distinction; the schema is the same.
    """
    name: str
    why: str
    polarity: TypePolarity
    signals: tuple[PatternSignal, ...] = ()
    scope: str = ""
    source: str = ""
    count: int = 1
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "why": self.why,
            "polarity": self.polarity.value,
            "signals": [{"description": s.description, "weight": s.weight} for s in self.signals],
            "scope": self.scope,
            "source": self.source,
            "count": self.count,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PatternType:
        return cls(
            name=d["name"],
            why=d["why"],
            polarity=TypePolarity(d["polarity"]),
            signals=tuple(
                PatternSignal(description=s["description"], weight=s.get("weight", 1.0))
                for s in d.get("signals", [])
            ),
            scope=d.get("scope", ""),
            source=d.get("source", ""),
            count=d.get("count", 1),
            tags=tuple(d.get("tags", ())),
        )


def positive(name: str, why: str, **kwargs) -> PatternType:
    """Convenience: create a positive type."""
    return PatternType(name=name, why=why, polarity=TypePolarity.POSITIVE, **kwargs)


def negative(name: str, why: str, **kwargs) -> PatternType:
    """Convenience: create a negative type."""
    return PatternType(name=name, why=why, polarity=TypePolarity.NEGATIVE, **kwargs)
