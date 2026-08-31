"""codemonkey/unify.py — type-check a proposed change against the pattern library.

Unification takes a proposed change (described by signals) and a library of
typed patterns, and returns matches with evidence. A match with a negative type
is a constraint violation warning. A match with a positive type that the change
conflicts with is a boundary warning.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cairn.devices.codemonkey.types import PatternType, TypePolarity


@dataclass(frozen=True)
class UnificationResult:
    """The result of unifying a proposed change against one library entry."""
    pattern: PatternType
    matched: bool
    score: float
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_name": self.pattern.name,
            "polarity": self.pattern.polarity.value,
            "matched": self.matched,
            "score": self.score,
            "evidence": list(self.evidence),
        }


_STOP_WORDS = frozenset({"a", "an", "the", "is", "are", "was", "were", "be",
    "to", "of", "in", "for", "on", "at", "by", "it", "do", "no", "not",
    "and", "or", "but", "with", "from", "that", "this", "its", "all"})


def _terms(text: str) -> set[str]:
    """Extract meaningful terms from text — lowercase, de-punctuated, stop-filtered.

    Splits on underscores and hyphens too, so `ground_loop` yields both
    `ground_loop` and `ground` + `loop`.
    """
    import re
    raw = set(re.findall(r"[a-z][a-z0-9_-]+", text.lower()))
    expanded = set()
    for w in raw:
        expanded.add(w.replace("-", "_"))
        for part in re.split(r"[_-]", w):
            if len(part) >= 2:
                expanded.add(part)
    return expanded - _STOP_WORDS


def unify_one(change_signals: list[str], pattern: PatternType, threshold: float = 0.3) -> UnificationResult:
    """Check one pattern against the change's signal descriptions.

    Two-layer matching:
    1. Substring containment (either direction)
    2. Term overlap — what fraction of the pattern's key terms appear in the
       change signals. This catches real-data matches where the descriptions
       are long and neither is a substring of the other.

    The score is the fraction of the pattern's signals that match at least one
    change signal. A match is declared when score >= threshold.
    """
    if not pattern.signals:
        name_match = _match_name(change_signals, pattern)
        if name_match:
            return UnificationResult(pattern=pattern, matched=True, score=0.5,
                                     evidence=(name_match,))
        return UnificationResult(pattern=pattern, matched=False, score=0.0, evidence=())

    change_terms = set()
    for cs in change_signals:
        change_terms |= _terms(cs)

    evidence = []
    hits = 0.0
    for ps in pattern.signals:
        desc_lower = ps.description.lower()
        matched_signal = False

        for cs in change_signals:
            cs_lower = cs.lower()
            if desc_lower in cs_lower or cs_lower in desc_lower:
                hits += ps.weight
                evidence.append(f"signal '{ps.description[:80]}' matched change '{cs}'")
                matched_signal = True
                break

        if not matched_signal:
            sig_terms = _terms(ps.description)
            if sig_terms and change_terms:
                overlap = sig_terms & change_terms
                overlap_ratio = len(overlap) / min(len(sig_terms), len(change_terms))
                if overlap_ratio >= 0.3 and len(overlap) >= 2:
                    hits += ps.weight * overlap_ratio
                    evidence.append(
                        f"term overlap ({', '.join(sorted(overlap)[:5])}) "
                        f"between signal and change"
                    )

    name_match = _match_name(change_signals, pattern)
    if name_match and not evidence:
        hits += 0.5
        evidence.append(name_match)

    total_weight = sum(s.weight for s in pattern.signals)
    score = hits / total_weight if total_weight > 0 else 0.0
    matched = score >= threshold

    return UnificationResult(
        pattern=pattern,
        matched=matched,
        score=min(score, 1.0),
        evidence=tuple(evidence),
    )


def _match_name(change_signals: list[str], pattern: PatternType) -> str:
    """Check if the pattern's name or why appear in the change signals."""
    name_terms = _terms(pattern.name) | _terms(pattern.why[:100])
    for cs in change_signals:
        cs_terms = _terms(cs)
        overlap = name_terms & cs_terms
        if len(overlap) >= 2:
            return f"name/why terms ({', '.join(sorted(overlap)[:5])}) match change '{cs}'"
    return ""


def unify(change_signals: list[str], library: list[PatternType], threshold: float = 0.3) -> list[UnificationResult]:
    """Type-check a proposed change against the full library.

    Returns all matches (score >= threshold), sorted by score descending.
    The caller distinguishes positive from negative matches by polarity.
    """
    results = []
    for pattern in library:
        result = unify_one(change_signals, pattern, threshold=threshold)
        if result.matched:
            results.append(result)
    results.sort(key=lambda r: r.score, reverse=True)
    return results
