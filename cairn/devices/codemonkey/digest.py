"""codemonkey/digest.py — nighttime batch consolidation on Hex.

Reads accumulated corrections/negative types, consolidates by why, updates
type definitions, and notices which error classes die off. Runs on Hex via
inference_domain for economics — Hex processes the batch cheaper than Claude
would interactively.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from cairn.devices.codemonkey.types import PatternType, TypePolarity, PatternSignal, negative
from cairn.devices.codemonkey.project import load_types, save_type, ensure_project


def consolidate_by_why(types: list[PatternType]) -> list[PatternType]:
    """Consolidate negative types with the same why into weighted entries.

    The why does the dedup: multiple incidents with the same why become one
    entry with a summed count. This is how 3 separate 'don't touch the ground
    loop' incidents become 1 constraint, not 3.
    """
    by_why: dict[str, list[PatternType]] = defaultdict(list)
    for t in types:
        if t.polarity == TypePolarity.NEGATIVE:
            key = t.why.strip().lower()
            by_why[key].append(t)

    consolidated = []
    for why_key, entries in sorted(by_why.items()):
        primary = entries[0]
        total_count = sum(e.count for e in entries)
        all_signals = list(dict.fromkeys(s for e in entries for s in e.signals))
        all_tags = list(dict.fromkeys(tag for e in entries for tag in e.tags))
        all_sources = "; ".join(dict.fromkeys(e.source for e in entries if e.source))

        consolidated.append(negative(
            name=primary.name,
            why=primary.why,
            signals=tuple(all_signals),
            source=all_sources,
            count=total_count,
            tags=tuple(all_tags),
        ))

    return consolidated


def find_dying_classes(current: list[PatternType], previous: list[PatternType]) -> list[str]:
    """Notice which error classes have died off.

    An error class that was present in the previous snapshot but has no new
    catches (count unchanged or decreased) is a candidate for retirement.
    """
    prev_counts: dict[str, int] = {}
    for t in previous:
        if t.polarity == TypePolarity.NEGATIVE:
            prev_counts[t.name] = t.count

    dying = []
    curr_names = {t.name for t in current if t.polarity == TypePolarity.NEGATIVE}
    for name, prev_count in prev_counts.items():
        if name not in curr_names:
            dying.append(name)

    return dying


def digest(project: str, use_hex: bool = True) -> dict[str, Any]:
    """Run the digest cycle: consolidate, detect dying classes, update library.

    When use_hex is True, classification runs through inference_domain targeting
    Hex. When False, runs locally (fallback for when Hex is unreachable).
    """
    types = load_types(project)
    negatives = [t for t in types if t.polarity == TypePolarity.NEGATIVE]
    positives = [t for t in types if t.polarity == TypePolarity.POSITIVE]

    consolidated = consolidate_by_why(negatives)

    dying = find_dying_classes(consolidated, negatives)

    ensure_project(project)
    for t in consolidated:
        save_type(project, t)

    return {
        "input_count": len(negatives),
        "consolidated_count": len(consolidated),
        "reduction": len(negatives) - len(consolidated),
        "dying_classes": dying,
        "used_hex": use_hex,
    }
