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

from cairn.tools.base.diagnostic import DiagnosticBase
from cairn.tools.system_word.system_word import canon

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


class IllegalTransition(DiagnosticBase, ValueError):
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
class Workflow(DiagnosticBase):
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


# ── THE RULES GRAMMAR (ticket 66ee1ffc1ec7) ───────────────────────────────────────────────
# Moved from transitions so the inspector measures a crossing's legality without importing
# the crossing; transitions imports these back under the same names.

def is_disposition(state: str, class_def: dict) -> bool:
    """A DISPOSITION is a terminal exit declared at the class level — DROPPED, SUPERSEDED,
    RETIRED. Not grammar-derived (no suffix rule); class-declared because the vocabulary is
    a fact about which exits a class offers, not a rule the token's shape can compute."""
    return state in class_def.get("dispositions", [])


def _registered_workflow(class_def: dict, version: str) -> dict:
    wvs = class_def.get("workflow_versions", {})
    if version not in wvs:
        raise IllegalTransition(
            f"unknown workflow version {version!r} for class {class_def.get('class')!r} "
            f"(known: {sorted(wvs)}) — a string cannot claim a version the class does not define")
    return wvs[version]


def _conform(wf: Workflow, class_def: dict) -> dict:
    """The node's path must match the registered path for the version it claims — else it is a
    drifted string, refused (validate against a KNOWN versioned definition).

    A FREE SUMMONS (``free_summons``, ticket ``watchme-emits-a-probe`` 2026-07-30) is the ONE
    exception, and it is a class-declared fact the grammar cannot derive — the same category
    as ``skippable_summons``, not a second mechanism. It may appear ZERO OR MORE TIMES AT ANY
    POSITION, so it is lifted out before the backbone is compared: what remains must still
    match the registered path exactly, which is what keeps "a drifted string is refused" true
    while ``WATCHME`` roams. Skippable is about the FORK a node takes at runtime; free is
    about the SHAPE the ticket authored. A state can be neither, either, or both.

    AND A FREE SUMMONS MUST NAME ITS OBJECT. A watch without an object is inert — a bare
    ``WATCHME`` cannot say what is being watched, so nothing downstream can check it, and a
    blank field is exactly the shape ``intention+why.json`` exists to refuse. This is caught
    HERE rather than in ``parse_workflow`` because the parser does not know the class, and
    therefore cannot know which of its states are free — the grammar stays classless on
    purpose (hardcoding ``WATCHME`` into the parser would be the reification the whole
    -ME grammar avoids)."""
    reg = _registered_workflow(class_def, wf.version)
    free = set(reg.get("free_summons", []))
    if free:
        for i, state in enumerate(wf.path):
            if state in free and not (wf.objects[i] if i < len(wf.objects) else None):
                raise MalformedWorkflow(
                    f"{wf.node_class}@{wf.version} carries a bare {state!r} at position {i} — a "
                    f"free summons must NAME ITS OBJECT ({state}(what-it-watches)); a watch "
                    f"without an object is inert, and a blank object cannot be checked")
    # A REPAIR SUMMONS (ticket 72d2f79daf0a) is lifted out beside the free ones, but it is
    # not free: it may occur at most once, and only directly before the backbone state it is
    # anchored to — FIXME sits before BUILDME because design is repaired before building.
    repair = reg.get("repair_summons", {})
    for state, anchor in repair.items():
        hits = [i for i, s in enumerate(wf.path) if s == state]
        if len(hits) > 1:
            raise MalformedWorkflow(
                f"{wf.node_class}@{wf.version} carries {state!r} {len(hits)} times — a repair "
                f"summons occurs at most once")
        if hits and (hits[0] + 1 >= len(wf.path) or wf.path[hits[0] + 1] != anchor):
            raise MalformedWorkflow(
                f"{wf.node_class}@{wf.version} carries {state!r} not directly before {anchor!r} "
                f"— a repair summons sits immediately before its anchor")
    dispositions = set(class_def.get("dispositions", []))
    backbone = [s for s in wf.path if s not in free and s not in dispositions and s not in repair]
    if backbone != list(reg["path"]):
        raise MalformedWorkflow(
            f"{wf.node_class}@{wf.version} string path {list(wf.path)} does not conform to the "
            f"registered path {reg['path']} — a drifted workflow is not a valid instance"
            + (f" (free summonses {sorted(free)} lifted out first; backbone read as {backbone})"
               if free else ""))
    return reg


def canon_target(wf: Workflow, target: str, class_def: dict | None = None) -> str:
    """The SYSTEM's spelling of a stage target he may have typed in any case (ruled
    2026-09-07: a stage token is a system word). Resolved against the workflow's own path
    first, then the class's dispositions; a token naming neither rides through unchanged so
    the refusal downstream names what he typed. This is a COMPARE, not a rewrite: the string
    on disk always carries the path's spelling, never his."""
    hit = canon(target, wf.path)
    if hit is None and class_def is not None:
        hit = canon(target, class_def.get("dispositions", []))
    return target if hit is None else hit


def resolve_target(wf: Workflow, target: str) -> int:
    """Which POSITION does naming ``target`` mean? For a state occurring once — every state
    before free summonses existed — this is just ``path.index``. A free summons may repeat,
    so a name can be ambiguous, and a silently-wrong index would move the cursor to the wrong
    obligation (the failure class the parse-walk fix of 2026-07-26 already paid for once).

    THE RULE: the NEAREST occurrence, FORWARD FIRST. A transition names progress by default,
    so an occurrence after the cursor wins over one before it; among several on the same side,
    the closest wins. Deliberately not "refuse the ambiguous": a node carrying two watches
    would then be un-crossable, which is worse than a stated, provable rule."""
    target = canon_target(wf, target)
    after = [i for i, s in enumerate(wf.path) if s == target and i > wf.cursor]
    if after:
        return after[0]
    before = [i for i, s in enumerate(wf.path) if s == target and i < wf.cursor]
    if before:
        return before[-1]
    try:
        return wf.path.index(target)
    except ValueError:
        return len(wf.path)


# The dispositions a rest (a state not ending -ME) may take: a later proved ticket replaces a
# proved one. DROPPED and RETIRED stay alternatives to completing, so a rest never takes them
# (ticket c63d2e99039e; Akien chose option a at open-bb5a0ceb8991).
_REST_DISPOSITIONS = ("SUPERSEDED",)


def legal_targets(wf: Workflow, *, class_def: dict) -> set[str]:
    """The set of states the cursor may legally move to from where it rests now.

    Forward: the next state, plus any reachable by skipping ONLY declared-skippable summonses
    (the leaf fork). Back: any earlier summons (a kick-back). Derived from the grammar + the
    class's ``skippable_summons``; nothing here is stored that the grammar can compute.
    """
    reg = _conform(wf, class_def)
    dispositions = set(class_def.get("dispositions", []))
    if wf.here in dispositions:
        return set()
    skippable = set(reg.get("skippable_summons", []))
    path, i = wf.path, wf.cursor
    targets: set[str] = set()
    # forward — advance, skipping only skippable summonses on the way
    j = i + 1
    while j < len(path):
        if path[j] in dispositions:
            j += 1
            continue
        targets.add(path[j])
        if path[j] in skippable and is_summons(path[j]):
            j += 1
            continue
        break
    # back-edges — re-enter any earlier summons (kick-back)
    for k in range(i):
        if is_summons(path[k]):
            targets.add(path[k])
    # dispositions — reachable from any summons as terminal exits; SUPERSEDED also from a rest
    if is_summons(wf.here):
        targets.update(dispositions)
    elif wf.here not in dispositions:
        targets.update(dispositions & set(_REST_DISPOSITIONS))
    return targets
