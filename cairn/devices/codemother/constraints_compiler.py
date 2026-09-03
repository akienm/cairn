"""codemother/constraints_compiler.py — compile the negative body into the constraints lab.

Mirror of the intentions model compiler. Same compilation structure, different
sourcing: where intentions come from code, constraints come from CC memory files,
learning records, corrections, and Akien's own mistakes.

The why does the dedup: multiple incidents with the same why are consolidated
into one weighted constraint, not N copies of a rule.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from cairn.devices.codemother.types import PatternType, TypePolarity
from cairn.devices.codemother.project import load_types, save_constraint, ensure_project


def compile_constraints(project: str) -> list[dict[str, Any]]:
    """Compile all negative types in the project's library into the constraints lab.

    Consolidation rule: entries with the same why are merged. The count is summed,
    sources are collected, and the name comes from the first-seen entry. This is
    how 3 separate 'don't touch the ground loop' incidents become 1 weighted
    constraint rather than 3 copies.

    Returns the compiled constraints.
    """
    negative_types = [t for t in load_types(project) if t.polarity == TypePolarity.NEGATIVE]

    by_why: dict[str, list[PatternType]] = defaultdict(list)
    for t in negative_types:
        key = t.why.strip().lower()
        by_why[key].append(t)

    compiled = []
    for why_key, entries in sorted(by_why.items()):
        primary = entries[0]
        total_count = sum(e.count for e in entries)
        all_sources = list(dict.fromkeys(e.source for e in entries if e.source))
        all_tags = list(dict.fromkeys(tag for e in entries for tag in e.tags))
        all_signals = list(dict.fromkeys(
            (s.description, s.weight) for e in entries for s in e.signals
        ))

        constraint = {
            "name": primary.name,
            "why": primary.why,
            "incident_count": total_count,
            "sources": all_sources,
            "signals": [{"description": d, "weight": w} for d, w in all_signals],
            "tags": all_tags,
            "consolidated_from": len(entries),
        }
        compiled.append(constraint)
        save_constraint(project, primary.name, constraint)

    return compiled
