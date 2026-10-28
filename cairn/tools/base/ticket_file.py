"""base/ticket_file.py — find a ticket file, measure its shape, write it through the door.

Moved verbatim out of transitions.py (ticket 632edb992aa3, child 3 of e41a94da3fd0) so the
readers of ticket files (crossings, chain, ticket_log) stop importing the crossing machinery.
``_TICKETS`` here is the one patch point: transitions reads it as ``ticket_file._TICKETS``.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.workflow_grammar import IllegalTransition

_TICKETS = Path(__file__).resolve().parents[3].parent / "CairnCommons" / "tickets"


def find_ticket(name: str) -> Path | None:
    """Resolve a ticket by slug or hex id to its file path, handling hex-slug filenames."""
    exact = _TICKETS / f"{name}.json"
    if exact.is_file():
        return exact
    hits = list(_TICKETS.glob(f"*-{name}.json"))
    if len(hits) == 1:
        return hits[0]
    hits = list(_TICKETS.glob(f"{name}-*.json"))
    if len(hits) == 1:
        return hits[0]
    return None


# WHY THE SHAPE IS DETECTED RATHER THAN IMPOSED, AND IT IS A MEASUREMENT. The chart's
# constrain packet asserted the corpus was written ``indent=2, ensure_ascii=False`` with a
# trailing newline; a full-corpus round-trip falsified that on the first run. Over all 260
# files: 208 are ``indent=2`` ASCII-escaped with a trailing newline, 44 are ``indent=2``
# non-escaped with one, and 8 are ``indent=2`` non-escaped WITHOUT one. Zero fit nothing.
# A writer that picked any single shape would silently reformat between 52 and 252 files —
# turning a three-line phase write into a whole-file diff on a corpus whose entire value at
# the working surface is that a human can read the change. So the door reproduces the file's
# OWN bytes first and reuses whatever settings did it.
_TICKET_SHAPES: tuple[tuple[bool, bool], ...] = (
    (True, True), (False, True), (True, False), (False, False),
)


def ticket_shape(raw: bytes, doc: object) -> tuple[bool, bool]:
    """The ``(ensure_ascii, trailing_newline)`` pair that reproduces ``raw`` from ``doc``.

    RAISES when no pair does. That is deliberate and it is Law 7 at a record of truth: the
    alternative is writing the file in a shape it was not in, which is a whole-file diff
    nobody asked for and a working surface a reader can no longer skim. All 260 live tickets
    fit one of the four pairs as measured on 2026-09-08, so this raise fires only on a file
    genuinely outside the corpus's shape — and a lack is reported as a lack."""
    for ensure_ascii, newline in _TICKET_SHAPES:
        body = json.dumps(doc, indent=2, ensure_ascii=ensure_ascii)
        if (body + "\n" if newline else body).encode("utf-8") == raw:
            return ensure_ascii, newline
    raise IllegalTransition(
        "the ticket's serialisation cannot be reproduced: no combination of ensure_ascii and "
        "trailing-newline round-trips its current bytes at indent=2, so writing it would "
        "REFORMAT the whole file to add one record. Refusing — a phase write must show in a "
        "git diff as the lines it changed. Nothing was written.")


def write_ticket(path: Path, doc: object, ensure_ascii: bool, newline: bool, *,
                  why: str = "phase") -> None:
    """Write ``doc`` back to ``path`` in the shape ``ticket_shape`` measured, atomically,
    THROUGH THE ARTIFACT DOOR (ticket 30531f6e1c5d).

    Atomic because the file is git-tracked: a partial write here is not a lost convenience
    (as it would be for the instance-space sail record) but a corrupted record of truth
    sitting in ``git status``. The door does temp-then-replace in the same directory, and
    journals the crossing with WHO made it from the caller's cgroup — which is exactly the
    fact ticket 481221f45884's hand-moved cursor (commit 42e3db0) had no record of."""
    from cairn.tools.artifact import artifact as door
    body = json.dumps(doc, indent=2, ensure_ascii=ensure_ascii)
    door.write(path, body + "\n" if newline else body, verb="phase", why=why)
