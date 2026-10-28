"""base/workflow_grammar.py — the workflow string's grammar, and nothing that can post.

Moved verbatim out of transitions.py (ticket 632edb992aa3, child 3 of e41a94da3fd0): the
inspector read workflow strings by importing transitions, and transitions.emit fires
gate_probes, which reaches the bus — so the verdict path could reach a host. The grammar
lives here, importing only the standard library; transitions imports it back under the old
names, so the objects are the same objects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_HEADER_RE = re.compile(r"^\s*([a-z][a-z-]*)@(v\d+)\s*$")     # "code-seam@v1"
# A state token, maybe bracketed, maybe carrying its OBJECT in parens — "WATCHME(what-it-watches)"
# — and, on the cursor only, its PICKUP PHASE after a colon — "[BUILDME:waiting]" (ruled
# 2026-08-07, the-ticket-is-the-source-period). The capture is deliberately wider than the
# legal vocabulary so "[BUILDME:Waiting]" is refused loudly instead of silently truncating
# the walk. Prose after the token is ignored (see the walk in parse_workflow).
_STATE_RE = re.compile(r"^\[?([A-Z][A-Z_]*)(?:\(([^)]*)\))?(?::([A-Za-z-]+))?\]?")
# The pickup lifecycle every summons inherits, stated once. Terminals and rests take no
# phase — a state that summons nobody has no pickup to show. A bare cursor (no colon) is the
# whole legacy corpus and parses as phase=None forever; there is no v3.
#
# NARROWED 2026-09-08 (ruling 2026-09-08-a-fleet-of-one-reshapes-the-pickup-phase). The axis
# was WHO HOLDS IT, which assumed a fleet of many; the fleet is one, so "nobody has picked it
# up" and "CC has not got to it yet" were the same sentence and the slot said nothing. The
# axis is now WHY IT IS NOT MOVING — and with it, who acts next.
_PHASES = ("waiting", "in-process", "queued", "hold", "blocked")
# Which of the five a hand may WRITE onto a cursor. in-process is the one exclusion and it is
# the point of the narrowing: it is runtime state, true only while a process runs, and the
# ticket is git-tracked and SHARED — a committed ":in-process" claims a hand that is gone the
# moment the session ends and is false on every machine that pulls it. It is DERIVED instead
# (see cairn/tools/base/sail_record.py). Parsing it stays legal so a derived read can render
# it and so no legacy string breaks; writing it is refused.
_WRITABLE_PHASES = ("waiting", "queued", "hold", "blocked")
# Which written phases must name what would RELEASE them. Akien, 2026-09-08: "nothing passes
# a gate with prose. an inspector will not allow it. not only has to have a field, but valid
# data to the limits of detection of deterministic code." waiting is the default and needs no
# release; in-process is derived and has nothing to release.
_RELEASE_PHASES = ("queued", "hold", "blocked")


class MalformedWorkflow(ValueError):
    """The workflow string does not parse, or does not conform to its claimed class@version."""


class IllegalTransition(ValueError):
    """The requested transition is refused by the rules — loud, never silent (Law 7)."""


TERMINAL_STATES: frozenset[str] = frozenset({
    "PROVED", "SUPERSEDED", "RETIRED", "DROPPED", "KILLED", "ABSORBED",
})


def is_terminal(state: str) -> bool:
    """A terminal state is one where no further work is expected — PROVED (the successful
    rest) plus every disposition exit the corpus has used."""
    return state in TERMINAL_STATES


def is_summons(state: str) -> bool:
    """The grammar: a state that ends in ``-ME`` is a SUMMONS (demands a peer); else a rest."""
    return state.endswith("ME")


@dataclass(frozen=True)
class Workflow:
    node_class: str
    version: str
    path: tuple[str, ...]
    cursor: int          # index into ``path`` of the bracketed state
    # THE OBJECT EACH POSITION CARRIES, parallel to ``path`` — None where a state names none.
    # A FREE SUMMONS (see ``_conform``) is refused without one: a watch without an object is
    # inert (Akien 2026-07-30) — a bare token cannot state what is being watched, so nothing
    # can check it. Parallel rather than a dict because a free summons may repeat, and two
    # occurrences of WATCHME watching different things are two different obligations.
    objects: tuple[str | None, ...] = ()
    # THE CURSOR'S PICKUP PHASE (ruled 2026-08-07: "the ticket is THE SOURCE PERIOD").
    # Only the cursor carries one — a state the boat is not standing at has no pickup in
    # flight — so this is a scalar, not a tuple parallel to ``path``. None is the legacy
    # grammar (every pre-ruling history) AND a rest/terminal cursor; "waiting" is a summons
    # arrived with no pickup yet; "in-process" is a summons somebody journaled a pickup on.
    phase: str | None = None

    @property
    def here(self) -> str:
        return self.path[self.cursor]

    @property
    def here_object(self) -> str | None:
        return self.objects[self.cursor] if self.cursor < len(self.objects) else None


def parse_workflow(s: str) -> Workflow:
    """Parse ``class@version: S -> S -> [CURSOR] -> S ...`` — trailing prose after the last
    state is tolerated (real tickets carry a parenthetical note after the workflow)."""
    header, sep, rest = s.partition(":")
    m = _HEADER_RE.match(header)
    if not sep or not m:
        raise MalformedWorkflow(f"no 'class@version:' header in {s!r}")
    node_class, version = m.group(1), m.group(2)
    path: list[str] = []
    objects: list[str | None] = []
    cursor: int | None = None
    phase: str | None = None
    for seg in rest.split("->"):
        seg = seg.strip()
        sm = _STATE_RE.match(seg)
        if not sm:
            break                      # trailing prose (e.g. "(cursor at ...)") — the path is done
        if seg.startswith("["):
            cursor = len(path)
        path.append(sm.group(1))
        obj = sm.group(2)
        objects.append(obj.strip() if obj and obj.strip() else None)
        # THE PICKUP PHASE (ruled 2026-08-07). Three refusals make the rule physics at parse:
        # a phase anywhere but the cursor is fiction (only the standing state has a pickup in
        # flight); a phase on a rest or terminal is fiction (a state that summons nobody has
        # no pickup); a word outside the vocabulary is not a phase. A bare token is the whole
        # legacy corpus and stays legal forever — phase simply stays None.
        ph = sm.group(3)
        if ph is not None:
            if not seg.startswith("["):
                raise MalformedWorkflow(
                    f"phase {ph!r} on non-cursor state {sm.group(1)!r} in {s!r} — only the "
                    "cursor segment carries a pickup phase (the boat stands at one state)")
            if ph not in _PHASES:
                raise MalformedWorkflow(
                    f"unknown phase {ph!r} on {sm.group(1)!r} in {s!r} — the pickup "
                    f"vocabulary is {_PHASES}")
            if not is_summons(sm.group(1)):
                raise MalformedWorkflow(
                    f"phase {ph!r} on {sm.group(1)!r} in {s!r} — a rest or terminal summons "
                    "nobody, so it has no pickup to phase")
            phase = ph
        # STOP AT THE FIRST STATE THAT CARRIES PROSE. A real ticket's note follows the LAST state
        # in the same segment ("PROVED   (cursor at BUILDME: ...)"), so the token is taken and the
        # walk ends here. Without this the split kept marching through the note, and any ARROW
        # inside the prose fed phantom states onto the path — a SILENT WRONG ANSWER, not a refusal:
        # state-machine-physics.json's note names the concept-piece path, and its 6-state workflow
        # parsed as 9 (THINKME TICKETME BUILDME PROVEME LEARNME PROVED + BUILDME REVIEWME PROVED).
        # It surfaced only by luck, because _conform compared paths; `here`, `legal_targets` and
        # every reader of `path` were being handed fiction. Measured 2026-07-26 while binding
        # stage-needs to the stage vocabulary (tickets/stage-needs.json child a).
        if sm.end() < len(seg):
            break
    if not path:
        raise MalformedWorkflow(f"no states in {s!r}")
    if cursor is None:
        raise MalformedWorkflow(f"no bracketed cursor in {s!r}")
    return Workflow(node_class, version, tuple(path), cursor, tuple(objects), phase)


_FINGERPRINT_EXCLUDE = frozenset({"fingerprint", "at", "seq"})


def _crossing_fingerprint(record: dict) -> str:
    body = {k: v for k, v in record.items() if k not in _FINGERPRINT_EXCLUDE}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ": "), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_crossing_fingerprint(record: dict) -> bool:
    fp = record.get("fingerprint")
    if fp is None:
        return False
    return _crossing_fingerprint(record) == fp
