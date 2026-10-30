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


def find_ticket(name: str, tickets_dir: Path | None = None) -> Path | None:
    """Resolve a ticket by slug or hex id to its PLAN file path, handling hex-slug filenames.

    ``tickets_dir`` defaults to the live store (``_TICKETS``, read at call time so a proof's
    patch holds). A ``.state.json`` beside a plan is never returned (ticket 284798998ab0)."""
    d = _TICKETS if tickets_dir is None else Path(tickets_dir)
    exact = d / f"{name}.json"
    if exact.is_file() and not _is_state(exact):
        return exact
    hits = [h for h in d.glob(f"*-{name}.json") if not _is_state(h)]
    if len(hits) == 1:
        return hits[0]
    hits = [h for h in d.glob(f"{name}-*.json") if not _is_state(h)]
    if len(hits) == 1:
        return hits[0]
    return None


# A TICKET IS THREE FILES (ticket 284798998ab0; Akien 2026-10-29, open-c7809a745bf7: "three
# parts. record it and reshape the ticket."): the PLAN ``<id>-<slug>.json`` a builder builds
# from, the STATE ``<id>-<slug>.state.json`` a gate or door reads or writes as the ticket
# moves, and the LOG ``<id>-<slug>.log.jsonl`` (ticket_log). Which key goes where is declared
# once, in the store charter's ``plan_fields`` / ``state_fields``; this module reads it there.
_STATE_SUFFIX = ".state.json"


def _is_state(p: Path) -> bool:
    return p.name.endswith(_STATE_SUFFIX)


def state_path(plan: str | Path) -> Path:
    """``<dir>/<id>-<slug>.state.json`` beside ``<dir>/<id>-<slug>.json``."""
    p = Path(plan)
    if not p.name.endswith(".json") or _is_state(p):
        raise ValueError(f"{p} is not a plan file (*.json, not *{_STATE_SUFFIX})")
    return p.with_name(p.name[:-5] + _STATE_SUFFIX)


def plans(tickets_dir: str | Path | None = None) -> list[Path]:
    """Every plan in the store: the sorted ``*.json`` that is neither the store's own charter
    (``_``-prefixed) nor a state file. A ``.log.jsonl`` never matches ``*.json``."""
    d = _TICKETS if tickets_dir is None else Path(tickets_dir)
    return sorted(p for p in d.glob("*.json")
                  if not p.name.startswith("_") and not _is_state(p))


def plans_of(ticket_id: str, tickets_dir: str | Path | None = None) -> list[Path]:
    """The plans filed under one id: ``<id>.json`` and every ``<id>-<slug>.json``, sorted,
    never a state file. Unlike ``find_ticket`` it returns every hit, so a caller that must
    say "resolves to N files, not one" still can."""
    d = _TICKETS if tickets_dir is None else Path(tickets_dir)
    return sorted(p for p in [d / f"{ticket_id}.json", *d.glob(f"{ticket_id}-*.json")]
                  if p.is_file() and not _is_state(p))


def read_ticket(plan: str | Path) -> dict:
    """The whole ticket a reader means: the plan's JSON updated with its state file's, when
    one stands (a key in both takes the state's value — only an unsplit plan carries one)."""
    p = Path(plan)
    doc = json.loads(p.read_text(encoding="utf-8"))
    s = state_path(p)
    if s.is_file():
        doc.update(json.loads(s.read_text(encoding="utf-8")))
    return doc


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
                  why: str = "phase", verb: str = "phase") -> None:
    """Write ``doc`` back to ``path`` in the shape ``ticket_shape`` measured, atomically,
    THROUGH THE ARTIFACT DOOR (ticket 30531f6e1c5d).

    Atomic because the file is git-tracked: a partial write here is not a lost convenience
    (as it would be for the instance-space sail record) but a corrupted record of truth
    sitting in ``git status``. The door does temp-then-replace in the same directory, and
    journals the crossing with WHO made it from the caller's cgroup — which is exactly the
    fact ticket 481221f45884's hand-moved cursor (commit 42e3db0) had no record of.

    SPLIT AT THE DOOR (ticket 284798998ab0): the keys the charter declares in ``state_fields``
    land in ``state_path(path)`` (indent=2, not ASCII-escaped, newline), the rest in the plan
    in its measured shape. The state file is written only when it carries a key, so a writer
    that hands over the plan alone leaves the standing state untouched."""
    from cairn.tools.artifact import artifact as door
    from cairn.tools.base.ticket_log import state_fields  # at call time: ticket_log imports us
    if isinstance(doc, dict):
        sk = set(state_fields(path))
        state = {k: v for k, v in doc.items() if k in sk}
        doc = {k: v for k, v in doc.items() if k not in sk}
        if state:
            write_state(path, state, why=why, verb=verb)
    body = json.dumps(doc, indent=2, ensure_ascii=ensure_ascii)
    door.write(path, body + "\n" if newline else body, verb=verb, why=why)


def rewrite_ticket(plan: str | Path, doc: dict, *, why: str, verb: str = "phase") -> None:
    """``write_ticket`` in the plan's own measured shape: the one call a writer that read the
    ticket with ``read_ticket`` makes to put it back (ticket 284798998ab0)."""
    p = Path(plan)
    raw = p.read_bytes()
    write_ticket(p, doc, *ticket_shape(raw, json.loads(raw.decode("utf-8"))), why=why, verb=verb)


def write_state(plan: str | Path, state: dict, *, why: str, verb: str = "phase") -> None:
    """Write ``state`` as the plan's whole state file through the door: indent=2, not
    ASCII-escaped, trailing newline — one shape, since every state file is born of this."""
    from cairn.tools.artifact import artifact as door
    door.write(state_path(plan), json.dumps(state, indent=2, ensure_ascii=False) + "\n",
               verb=verb, why=why)
