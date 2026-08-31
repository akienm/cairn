"""codemonkey/query.py — what matters about X while working on Y.

Area-scoped retrieval against the pattern library. Where challenge fires on
proposed changes, query fires on questions. Both read the same type library.
The response is contextualized to the task, not a dump of everything known.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cairn.devices.codemonkey.types import PatternType, TypePolarity
from cairn.devices.codemonkey.unify import unify, UnificationResult
from cairn.devices.codemonkey.project import load_types


@dataclass
class QueryResult:
    """What the library knows about area X in the context of task Y."""
    area: str
    task: str
    positive_matches: list[UnificationResult]
    negative_matches: list[UnificationResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "area": self.area,
            "task": self.task,
            "what_it_is": [m.to_dict() for m in self.positive_matches],
            "what_has_gone_wrong": [m.to_dict() for m in self.negative_matches],
            "positive_count": len(self.positive_matches),
            "negative_count": len(self.negative_matches),
        }


def query(area: str, task: str, project: str, threshold: float = 0.2) -> QueryResult:
    """What matters about area while working on task.

    Combines the area name and task description into signals and matches
    against the full library. Lower threshold than challenge — query is
    exploratory, challenge is adversarial.
    """
    signals = [area, task, f"{area} {task}"]

    library = load_types(project)
    matches = unify(signals, library, threshold=threshold)

    positive_matches = [m for m in matches if m.pattern.polarity == TypePolarity.POSITIVE]
    negative_matches = [m for m in matches if m.pattern.polarity == TypePolarity.NEGATIVE]

    return QueryResult(
        area=area,
        task=task,
        positive_matches=positive_matches,
        negative_matches=negative_matches,
    )
