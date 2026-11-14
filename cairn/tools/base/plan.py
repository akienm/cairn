"""THE ONE PLAN VIEW (ticket 5c1e0a7d93b2, Q#100, outline 9.3.5.1.2.1).

A plan is CONSTRAINTS, then OUTCOMES ``{n, claim, writes_to, reads, after, via?}``, then
RESOURCES. Until every reader moves, a ticket carries one of two shapes: the outcomes plan, or
the older ``falsifier.clauses`` beside ``decisions``. Every reader composes this module instead
of reading either shape itself, so the two read the same during the change (the dual-read
Q#100 asks for), and when the old shape is gone only this module changes.

- ``clauses(doc)``  -> ``[{n, claim}]``: what the proof's ``PROVES`` keys on — an outcome
  still awaiting its claim is no clause yet.
- ``steps(doc)``    -> ``[{n, text, writes_to, reads, after}]``: what the build does, where,
  and after what. An outcome's text is its claim, else the text the migration carried over;
  a decision has no ``after``, so it reads ``[]``.
- ``awaiting(doc)`` -> the ``n`` of every outcome with no claim yet. A cast never carries one
  (the door refuses it); a plan the migration moved carries one until its claim is judged,
  and the BUILDME lane ``every_outcome_has_its_claim`` holds the crossing until then.

A non-dict ``doc``, or a shape that is not a list of dicts, reads as no lines: a reader asks
what the plan says, and the cast door is where an unreadable plan is named.
"""
from __future__ import annotations


def _lines(value) -> list[dict]:
    return [x for x in value if isinstance(x, dict)] if isinstance(value, list) else []


def _paths(value) -> list:
    return list(value) if isinstance(value, list) else []


def _claimed(o: dict) -> bool:
    return isinstance(o.get("claim"), str) and bool(o["claim"].strip())


def has_outcomes(doc) -> bool:
    """True when ``doc`` carries the outcomes shape (a key ``outcomes``, whatever it holds)."""
    return isinstance(doc, dict) and "outcomes" in doc


def clauses(doc) -> list[dict]:
    """The plan's falsifiable claims as ``{n, claim}``, in the order written."""
    if not isinstance(doc, dict):
        return []
    if has_outcomes(doc):
        return [{"n": o.get("n"), "claim": o.get("claim")} for o in _lines(doc.get("outcomes"))
                if _claimed(o)]
    f = doc.get("falsifier")
    return [{"n": c.get("n"), "claim": c.get("claim")}
            for c in _lines(f.get("clauses") if isinstance(f, dict) else None)]


def steps(doc) -> list[dict]:
    """The plan's build steps as ``{n, text, writes_to, reads, after}``: an outcome's text is
    its claim (else the migrated ``text``); a decision's is its text, its ``after`` []."""
    if not isinstance(doc, dict):
        return []
    if has_outcomes(doc):
        return [{"n": o.get("n"), "text": o.get("claim") if _claimed(o) else o.get("text"),
                 "writes_to": _paths(o.get("writes_to")), "reads": _paths(o.get("reads")),
                 "after": _paths(o.get("after"))} for o in _lines(doc.get("outcomes"))]
    return [{"n": d.get("n"), "text": d.get("text"), "writes_to": _paths(d.get("writes_to")),
             "reads": _paths(d.get("reads")), "after": []} for d in _lines(doc.get("decisions"))]


def awaiting(doc) -> list:
    """The ``n`` of each outcome whose claim is absent or blank; [] for a decisions plan."""
    if not has_outcomes(doc):
        return []
    return [o.get("n") for o in _lines(doc.get("outcomes")) if not _claimed(o)]
