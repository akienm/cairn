"""base/transitions.py — the EMIT-CHOKEPOINT: the one door a workflow transition passes through.

A node's ``state`` is a versioned, mutable, greppable workflow string with the cursor in
brackets — ``code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED``
(MAP.md 'The node state-machine — states as summons'). Moving that cursor is not a free
string edit anyone may make: it is a TRANSITION, and a transition is physics, not policy
(Law 4). This module is the chokepoint that makes it so.

The emit-chokepoint factors into three rungs (resolved in the harbor_master /sorted,
2026-07-21; tickets/state-machine-physics.json + tickets/harbor-master.json):

  - RULES  — is this transition legal for this class@version? THIS MODULE. Base-class
             physics, inherited, inescapable. Validated against the versioned table the
             node-class DEFINITION carries (node_classes/<class>.json), and against the
             ``-ME`` grammar (a summons ends in -ME; a rest does not).
  - AUTHORITY — who may invoke it? The harbor_master's CLEARANCE gate (child b), which
             WRAPS this: it calls ``validate_transition`` for legality, then adds the
             owner-gated, delegable-per-operation authority (Law 6). Not here.
  - TRUTH  — record it. ``emit`` journals the crossing append-only through the projector
             door (charter-state-history-split), the same door a charter's state rides.
             Two-vantage: the boat's own history (here) + the harbor register (harbor_master).

The grammar carries the semantics, so most of the table is DERIVED, not stored:
  - ``-ME`` = a SUMMONS (a demand for the peer who acts next). ``THINKME TICKETME BUILDME
    PROVEME WATCHME REVIEWME`` …
  - no ``-ME`` = the node's own CONDITION/REST: ``PROVED`` (passed its gate, grazed by the
    background loop). NOT terminal — a back-edge re-opens it.
    ONE REST, NOT TWO, since 2026-07-30 (ticket watchme-emits-a-probe). There used to be a
    second: ``LEARNING``, "a standing driver, actively collecting". It is DISSOLVED, not
    renamed — a node does not BECOME a watcher, it EMITS one and rests. A proved
    intention's efficacy data can only accumulate AFTER it rests, so a node that turned
    into its own watcher would never rest and would never be the thing measured. The
    standing worker is a PROBE (``cairn/base/probe.py``), which is a different species from
    a node: immutable, carrying no authority, and outliving the crossing that emitted it.
    That deletes a state rather than adding one. ``LEARNME``/``LEARNING`` survive only in
    v1 strings, in history, and in the migration's own record — a record of truth is never
    edited to hide the shape it used to have (Law 7).
What the grammar cannot derive, the class definition declares — and there are exactly TWO
such facts, orthogonal on purpose:
  - ``skippable_summons`` — which summons is an optional FORK at runtime (``TICKETME``: a
    leaf goes THINKME->BUILDME; a parent goes THINKME->TICKETME).
  - ``free_summons`` — which summons may appear ZERO OR MORE TIMES AT ANY POSITION in the
    authored string (``WATCHME``, from v2). Skippable is about the fork a node TAKES; free
    is about the shape the ticket AUTHORED. A free summons is lifted out of the string
    before the backbone is compared to the registered path, so "a drifted string is refused"
    stays true while it roams — and it must NAME ITS OBJECT (``WATCHME(what-it-watches)``),
    because learning without an object is inert. Being free does NOT make it skippable:
    optional to CARRY, mandatory to SATISFY once carried.
Everything else falls out:

  - forward: advance to the next state, or skip forward over ONLY skippable summonses (the
    leaf fork). Skipping a NON-skippable summons (a gate like PROVEME) is refused.
  - back-edge: re-enter any EARLIER summons — a kick-back (severity = how far back;
    routing the very-wrong ones to the ask-Akien escalation is a filed edge below).
  - illegal: a target outside the class's vocabulary, a forward skip past a gate, a no-op
    self-loop, or a back-edge to a non-summons (you cannot un-rest by fiat).

Version-validated: the node's string names ``class@vN``; the transition is checked against
that class definition's registered ``workflow_versions[vN]``, and a string whose path does
not CONFORM to the registered path for the version it claims is refused as drifted. So a
workflow string cannot quietly diverge from the class it claims to be an instance of.

THE BUILD GATE (2026-07-27, build_inspector's filed edge (a) landing): a journaled FORWARD
crossing out of ``PROVEME`` — the crossing OF the gate summons — first runs the
build_inspector on the component at the crossing's own address (the directory holding
``history_path``), and is refused while any filter reds. The gate lives HERE because this is
the one door: the clearance gate wraps ``emit``, so wiring anywhere else (the tester's
discipline, a hook CC remembers to run) would be the run-it-by-discipline gap the inspector
exists to close. Jurisdiction is the addressed crossing: no ``history_path`` means no journal,
so the record of truth does not move and there is nothing to gate. Kick-backs OUT of PROVEME
are never gated — retreating on a red is the correct move. An address the census cannot see
is REFUSED, not skipped: a gate that silently inspects nothing passes everything (Law 8), and
the refusal names the growth path (grow the census/filters, the learning device's move).

Dependency-light AT IMPORT: pure parsing + the projector's pure core. No device, no bus, no
DB. The build gate summons the build_inspector LAZILY, only at a journaled PROVEME exit —
both are modules (inference-free by their own proofs), so the boot-order law holds.

    python3 cairn/base/proofs/test_transitions.py     # exit 0 = green
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from cairn.charter import projector

_REPO_ROOT = Path(__file__).resolve().parents[2]
_NODE_CLASSES = _REPO_ROOT.parent / "CairnCommons" / "node_classes"

_HEADER_RE = re.compile(r"^\s*([a-z][a-z-]*)@(v\d+)\s*$")     # "code-seam@v1"
# A state token, maybe bracketed, maybe carrying its OBJECT in parens — "WATCHME(what-it-watches)".
# Prose after the token is ignored (see the walk in parse_workflow).
_STATE_RE = re.compile(r"^\[?([A-Z][A-Z_]*)(?:\(([^)]*)\))?\]?")


class MalformedWorkflow(ValueError):
    """The workflow string does not parse, or does not conform to its claimed class@version."""


class IllegalTransition(ValueError):
    """The requested transition is refused by the rules — loud, never silent (Law 7)."""


class EntryGateRed(IllegalTransition):
    """The forward crossing into BUILDME is refused: the crossing names a cast ticket
    that no berthed chart chain claims — the build has no charted course. Carries
    ``findings`` complete on the first pass; run /chart for the request, never bypass.
    Sibling of ``BuildGateRed``, not a subclass: the two gates refuse different
    crossings (entry vs promotion) and a handler for one must not silently catch
    the other."""

    def __init__(self, message: str, findings: list[dict] | None = None):
        super().__init__(message)
        self.findings = findings or []


class BuildGateRed(IllegalTransition):
    """The forward crossing out of PROVEME is refused: the component at the crossing's own
    address reds the build_inspector (or cannot be inspected at all — same refusal, no side
    door). Carries ``findings`` complete on the first pass; fix or kick back, never bypass."""

    def __init__(self, message: str, findings: list[dict] | None = None):
        super().__init__(message)
        self.findings = findings or []


class ExitGateRed(IllegalTransition):
    """The forward crossing into PROVED is refused: the crossing names a cast ticket
    whose claiming chart is not yet ANSWERED — a criterion without a passing run
    verdict, or a hypothesis nobody dispositioned. Carries ``findings`` complete on
    the first pass; run the criteria and write the verdict artifact, never bypass.
    Sibling of ``EntryGateRed`` and ``BuildGateRed``, not a subclass: the three
    gates refuse different crossings (entry vs promotion vs close) and a handler
    for one must not silently catch another."""

    def __init__(self, message: str, findings: list[dict] | None = None):
        super().__init__(message)
        self.findings = findings or []


class WatchmeEmissionRed(IllegalTransition):
    """The forward crossing OUT of WATCHME is refused: the watch the node carried did not
    EMIT — no ticket to read the spec from, no spec for the object the boat stands at, or a
    spec whose promised probe is not berthed and armed. Carries ``findings`` complete on the
    first pass; berth and arm the probe, never bypass.

    Sibling of ``EntryGateRed`` / ``BuildGateRed`` / ``ExitGateRed`` — sharing the
    ``IllegalTransition`` parent, not each other, so a handler written for one gate cannot
    silently swallow a different gate's refusal. This is the FIFTH seat at the chokepoint,
    and the first that guards a FREE summons: the other four sit at fixed backbone crossings,
    which is why 'mandatory to satisfy ONCE CARRIED' needed a gate of its own rather than a
    clause bolted onto an existing one.

    Provenance: 2026-07-30, ticket watchme-emits-a-probe piece (c-i). Its falsifier (1): *a
    WATCHME crossing is accepted that emitted no armed probe* — the clause that makes 'not
    optional once present' physics rather than prose."""

    def __init__(self, message: str, findings: list[dict] | None = None):
        super().__init__(message)
        self.findings = findings or []


def _emission_gate(obj: str | None, ticket: object) -> str:
    """A node crossing FORWARD out of a WATCHME it carried must have EMITTED its probe.
    Returns the one-line gate note the journal carries; raises ``WatchmeEmissionRed`` before
    anything is written.

    EMISSION, NOT ACCUMULATION — the ticket's own phrase. The failure this refuses is a node
    that walks past its own watch having gathered nothing: the LEARNME shape that v1 measured
    and that this whole node dissolves. LEARNME sat in the backbone, forced on every node, and
    carried NO GATE at all — so it was crossed by every voyage and satisfied by none.

    WHY A CROSSING WITH NO TICKET IS REFUSED RATHER THAN WAVED THROUGH. The spec lives on the
    ticket, so without one the gate cannot know whether a probe was emitted — and 'cannot
    know' must never render as 'clean' (Law 3). There is no exempt roster here on purpose: the
    other gates' roster exists for call sites that legitimately cross ticketless, and a
    ticketless node cannot have carried a WATCHME in the first place (the spec is what put it
    in the string).

    Back-edges INTO a WATCHME retreat ungated — that is the owner's act of re-arming a watch
    whose verdict came back failed, and gating a retreat would trap the boat at the one state
    it is supposed to be able to return to."""
    from cairn.base import watchme_spec

    if not isinstance(ticket, str) or not (_TICKETS / (ticket + ".json")).exists():
        raise WatchmeEmissionRed(
            f"WATCHME({obj}) crossing refused: the crossing names no cast ticket, so the "
            "watch's spec cannot be read and emission cannot be measured — a watch that "
            "cannot be checked is not a watch (Law 3). Nothing was journaled. Name the "
            "ticket on the crossing (ticket=<id>).")

    data = json.loads((_TICKETS / (ticket + ".json")).read_text(encoding="utf-8"))
    spec = watchme_spec.spec_for(data, obj)
    if spec is None:
        raise WatchmeEmissionRed(
            f"WATCHME({obj}) crossing refused: ticket {ticket!r} carries no watchme spec for "
            f"object {obj!r}. Optional to carry, MANDATORY TO SATISFY once carried — the "
            "string says this node has this watch. Nothing was journaled. Add the spec "
            "(trigger, enough, carrier, nexus, consumer, probe) to the ticket.",
            [{"judge": "watchme_spec", "detail": watchme_spec.watchme_spec_error(data)}])

    err = watchme_spec.armed_error(spec)
    if err:
        raise WatchmeEmissionRed(
            f"WATCHME({obj}) crossing refused: {err}. Nothing was journaled. The watch is "
            "carried, so it is owed a probe that can be fired — berth and arm it, or "
            "back-edge and drop the watch from the string through the owner's gate.",
            [{"judge": "armed", "detail": err, "berth": spec.get("probe")}])
    return "clean — WATCHME(%s) emitted the probe berthed at %s (ticket %r)" % (
        obj, spec.get("probe"), ticket)


def migrate_to_v2(workflow_str: str, *, watch: str | None = None) -> str:
    """A v1 node's string, expressed in v2. Pure — returns the new string, writes nothing.

    Ticket ``watchme-emits-a-probe`` piece (b), 2026-07-30. v1's ``LEARNME`` sat in the
    backbone, mandatory and ungated; v2 dissolves it and offers ``WATCHME(<object>)`` as a
    free summons instead. Every node at sea today rides v1, so the vocabulary change needs a
    way across that does not rewrite anybody's past.

    MIGRATION RIDES THE NEXT CROSSING — it is not a sweep. There is no script that walks the
    repo rewriting state files: a node's version changes at the one moment it was going to
    write a record anyway (``emit_migrated`` below), so past entries stay byte-identical and
    nothing is edited in place (Law 7). A node resting on v1 and never crossing again simply
    stays v1, correctly: v1 is frozen, not broken, and a version is immutable.

    WHERE A BOAT STANDING AT LEARNME LANDS — the one real decision here, and it is PROVEME.
    Standing at LEARNME meant the node had passed the PROVEME summons and not yet been
    promoted; LEARNME itself was ungated, so standing there is not evidence that anything was
    learned. Under v2's vocabulary that position IS PROVEME: one forward crossing from PROVED,
    with the build gate still owed. Re-running that gate is a cost, not a defect — it is
    exactly the check that asks "may this be promoted", asked of a boat that never was.

    THE DROP IS NOT SILENT, which is the part Law 7 cares about: ``emit_migrated`` journals
    ``migrated_from`` carrying the old string verbatim, so the record of truth shows the
    version change at the crossing where it happened.

    ``watch`` CARRIES A WATCHME INSTEAD OF DROPPING — for a node that genuinely wants to keep
    learning. It is opt-in on purpose. Making it the default would retro-impose an armed-probe
    obligation on every boat mid-voyage and refuse its next crossing out of the watch: the
    same retro-red that the spec check (piece c-ii) already paid for once. "Every intention
    gets a keep-learning step by default" is a rule AT TICKETING, where an author is present
    to answer it — not a rule applied to the past."""
    wf = parse_workflow(workflow_str)
    if wf.version != "v1":
        raise IllegalTransition(
            f"migrate_to_v2 refused: {workflow_str!r} claims {wf.version}, not v1 — a version "
            "is immutable, so there is nothing to migrate and nothing to guess at")

    path, objects, cursor = [], [], wf.cursor
    for i, state in enumerate(wf.path):
        if state == "LEARNME":
            if watch:
                path.append("WATCHME")
                objects.append(watch)
                continue
            if i < wf.cursor:
                cursor -= 1            # a state dropped from behind the boat moves it up one
            elif i == wf.cursor:
                cursor = len(path) - 1  # AT LEARNME -> land on the state before it (PROVEME)
            continue
        path.append(state)
        objects.append(wf.objects[i] if i < len(wf.objects) else None)

    rendered = " -> ".join(
        ("[%s]" if j == cursor else "%s") % (f"{s}({o})" if o else s)
        for j, (s, o) in enumerate(zip(path, objects)))
    return f"{wf.node_class}@v2: {rendered}"


def emit_migrated(workflow_str: str, target: str, *, watch: str | None = None, **kw) -> str:
    """Cross, migrating v1 -> v2 in the same act. THE ONE DOOR for a migration crossing.

    Two things must happen together or the record lies: the string moves to v2, and the
    journal says it did. Leaving that to caller discipline would make "the migration is on the
    record" a policy someone remembers rather than physics (Law 4) — so it is one call, and
    ``migrated_from`` cannot be forgotten. An already-v2 string passes straight through, so
    this is safe to call on a node whose version you have not checked."""
    try:
        migrated = migrate_to_v2(workflow_str, watch=watch)
    except IllegalTransition:
        return emit(workflow_str, target, **kw)          # already v2 — nothing to record
    return emit(migrated, target, migrated_from=workflow_str, **kw)


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
    # A FREE SUMMONS (see ``_conform``) is refused without one: "learning without an object is
    # inert" (Akien 2026-07-30) — a bare token cannot state what is being learned, so nothing
    # can check it. Parallel rather than a dict because a free summons may repeat, and two
    # occurrences of WATCHME watching different things are two different obligations.
    objects: tuple[str | None, ...] = ()

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
    return Workflow(node_class, version, tuple(path), cursor, tuple(objects))


def load_class_def(node_class: str, *, root: Path | str = _NODE_CLASSES) -> dict:
    """Load a node-class definition, or refuse an unknown class (Law 8: a workflow string is
    validated against a KNOWN versioned definition — an unknown class has no physics to run)."""
    p = Path(root) / f"{node_class}.json"
    if not p.exists():
        raise IllegalTransition(f"unknown node-class {node_class!r} — no definition at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


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

    AND A FREE SUMMONS MUST NAME ITS OBJECT. "Learning without an object is inert" — a bare
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
                    f"free summons must NAME ITS OBJECT ({state}(what-it-watches)); learning "
                    f"without an object is inert, and a blank object cannot be checked")
    backbone = [s for s in wf.path if s not in free]
    if backbone != list(reg["path"]):
        raise MalformedWorkflow(
            f"{wf.node_class}@{wf.version} string path {list(wf.path)} does not conform to the "
            f"registered path {reg['path']} — a drifted workflow is not a valid instance"
            + (f" (free summonses {sorted(free)} lifted out first; backbone read as {backbone})"
               if free else ""))
    return reg


def resolve_target(wf: Workflow, target: str) -> int:
    """Which POSITION does naming ``target`` mean? For a state occurring once — every state
    before free summonses existed — this is just ``path.index``. A free summons may repeat,
    so a name can be ambiguous, and a silently-wrong index would move the cursor to the wrong
    obligation (the failure class the parse-walk fix of 2026-07-26 already paid for once).

    THE RULE: the NEAREST occurrence, FORWARD FIRST. A transition names progress by default,
    so an occurrence after the cursor wins over one before it; among several on the same side,
    the closest wins. Deliberately not "refuse the ambiguous": a node carrying two watches
    would then be un-crossable, which is worse than a stated, provable rule."""
    after = [i for i, s in enumerate(wf.path) if s == target and i > wf.cursor]
    if after:
        return after[0]
    before = [i for i, s in enumerate(wf.path) if s == target and i < wf.cursor]
    if before:
        return before[-1]
    return wf.path.index(target)


def legal_targets(wf: Workflow, *, class_def: dict) -> set[str]:
    """The set of states the cursor may legally move to from where it rests now.

    Forward: the next state, plus any reachable by skipping ONLY declared-skippable summonses
    (the leaf fork). Back: any earlier summons (a kick-back). Derived from the grammar + the
    class's ``skippable_summons``; nothing here is stored that the grammar can compute.
    """
    reg = _conform(wf, class_def)
    skippable = set(reg.get("skippable_summons", []))
    path, i = wf.path, wf.cursor
    targets: set[str] = set()
    # forward — advance, skipping only skippable summonses on the way
    j = i + 1
    while j < len(path):
        targets.add(path[j])
        if path[j] in skippable and is_summons(path[j]):
            j += 1
            continue
        break
    # back-edges — re-enter any earlier summons (kick-back)
    for k in range(i):
        if is_summons(path[k]):
            targets.add(path[k])
    return targets


def validate_transition(wf: Workflow, target: str, *, class_def: dict) -> None:
    """Refuse an illegal transition, loudly (Law 4/7). Silence would be a silent bad default."""
    if target not in wf.path:
        raise IllegalTransition(
            f"{target!r} is not in the {wf.node_class}@{wf.version} vocabulary {list(wf.path)}")
    # A NO-OP IS A POSITION, NOT A NAME. Once a free summons may repeat, a node standing at
    # one WATCHME and moving to the NEXT one is a real crossing that happens to share a name;
    # refusing it on the name would make a two-watch node un-crossable at its first watch.
    if resolve_target(wf, target) == wf.cursor:
        raise IllegalTransition(f"{target!r} -> {target!r} is a no-op, not a transition")
    legal = legal_targets(wf, class_def=class_def)
    if target not in legal:
        raise IllegalTransition(
            f"{wf.here} -> {target} is illegal for {wf.node_class}@{wf.version} "
            f"(legal from here: {sorted(legal)}) — e.g. a forward skip past a gate summons is refused")


_TICKETS = _REPO_ROOT.parent / "CairnCommons" / "tickets"

# THE EXEMPT ROSTER (ticket a-voyage-names-its-ticket, 2026-07-29): call-site
# component names allowed to cross forward into BUILDME/PROVED with NO ticket
# named at all. Structure ahead of any real entry — a future exemption is a
# roster ENTRY (explicit, journaled), never an ambient pass. EMPTY IN V0 BY
# MEASURE: `grep -rn 'BUILDME|PROVED' --include=*.py cairn/` (excluding
# proofs/ and this module's own gate branches), 2026-07-29 — zero in-repo
# call sites cross forward ticketless today; every real crossing already
# names its ticket. Consulted ONLY inside ``_require_named_ticket`` below,
# and only when the crossing names NO ticket at all — a NAMED-but-uncast
# ticket is never exempt (naming one is a claim to be judged, not waived by
# coincidence of address).
_EXEMPT_ROSTER: frozenset[str] = frozenset()


class TicketRequiredRed(IllegalTransition):
    """The forward crossing into BUILDME or PROVED is refused: no cast ticket is
    named on the crossing, and the crossing's component is not on the explicit
    exempt roster (``_EXEMPT_ROSTER``, EMPTY in v0) — or a ticket IS named but
    is not cast. Both failure classes raise this ONE exception (the fourth
    sibling of ``EntryGateRed``/``BuildGateRed``/``ExitGateRed`` — sharing the
    ``IllegalTransition`` parent, not each other, so a handler for one gate
    cannot silently catch another) with DISTINCT wording: unnamed routes to
    casting the work (/sorted); named-but-uncast names what is missing,
    never exempted by coincidence of address. Nothing is written before this
    raises (Law 8: a voyage that cannot show its ticket is the side door this
    closes).

    Provenance: 2026-07-29, ticket a-voyage-names-its-ticket — build_inspector
    charter edge (k)'s 'the stricter every-journaled-BUILDME-names-a-ticket
    rule waits for a dated need'; the need is the budget stage-split plan,
    delegating builds to agents most likely to omit the name innocently.
    """

    def __init__(self, message: str, findings: list[dict] | None = None):
        super().__init__(message)
        self.findings = findings or []


def _require_named_ticket(target: str, ticket: object, *, history_path: str) -> str | None:
    """The one precondition BOTH doors share (replacing the two former opt-in
    ``isinstance`` checks): a forward crossing into BUILDME or PROVED must
    name a CAST ticket, or refuse before anything is written.

    Returns an exemption note — journaled through the same ``entry_gate``/
    ``exit_gate`` key the real gate below uses, so an exempt pass is
    gated-and-clean on the record, never silent — when the crossing's own
    component name is on the explicit ``_EXEMPT_ROSTER`` and NO ticket was
    named at all. Returns ``None`` when a named, cast ticket is present — the
    caller proceeds into the standing entry/exit gate exactly as before this
    stone. Raises ``TicketRequiredRed`` otherwise: no ticket and no roster
    match (routes to /sorted), or a named ticket that is not cast (never
    exempt — naming one is a claim to be judged, not a claim to be waived).
    """
    if ticket is None:
        comp = Path(history_path).resolve().parent.name
        if comp in _EXEMPT_ROSTER:
            return f"exempt — {comp!r} is on the explicit ticketless roster (_EXEMPT_ROSTER)"
        raise TicketRequiredRed(
            f"{target} crossing refused: no ticket is named on the crossing — a forward "
            "crossing into BUILDME or PROVED must name a cast ticket (Law 8: nothing enters "
            "proven-space without showing its ticket; the side door for a delegated build "
            "that omits the name closes here). Nothing was journaled. Cast the work as a "
            f"ticket (/sorted), name it on the crossing (ticket=<id>), then cross again — or, "
            f"if this component's crossings are a legitimate exception, add {comp!r} to "
            "_EXEMPT_ROSTER explicitly, never silently."
        )
    if not isinstance(ticket, str) or not (_TICKETS / (ticket + ".json")).exists():
        raise TicketRequiredRed(
            f"{target} crossing refused: named ticket {ticket!r} is not cast — no file at "
            f"{_TICKETS / (str(ticket) + '.json')}. A named-but-uncast ticket is an error to "
            "fix, never an exemption (naming one is a claim to be judged, not waived by "
            "coincidence of address). Cast it via /sorted, or correct the name, then cross "
            "again. Nothing was journaled."
        )
    return None


def _entry_gate(ticket: str) -> str:
    """A cast ticket crossing forward into BUILDME must be claimed by a berthed chart
    chain — the entry half of packet jurisdiction (the PROVEME exit below is the
    promotion half). Returns the one-line gate note the journal carries; raises
    ``EntryGateRed`` — findings complete on the first pass — before anything is
    written.

    Provenance: 2026-07-29, ticket buildme-rides-the-chart — the sail step-0 prose
    refusal ('no berths → run /chart first') retired into physics (Law 4), on
    Akien's word with the stake in numbers (Fable at 64% of usage). Wired at the
    emit-chokepoint because this is the one door; jurisdiction is the crossing's
    own named, cast ticket — an un-cast or unnamed ticket is not gated (v0; the
    stricter require-a-ticket edge is filed on the ticket).
    """
    # Lazy on purpose, same boot-order law as the build gate below: the check's cost
    # lands only at the rare journaled BUILDME entry — an event, never a poll.
    from cairn.build_inspector.inspector import buildme_rides_the_chart as _check

    findings = _check(ticket)
    if not findings:
        return "clean — a berthed chart chain claims ticket %r" % ticket
    lines = [
        f"  [{f['filter']}] {f['finding']} — {f['why_it_matters']} (evidence: "
        f"{json.dumps(f['evidence'], default=str)})"
        for f in findings
    ]
    raise EntryGateRed(
        f"BUILDME crossing refused: cast ticket {ticket!r} has no berthed chart chain "
        "claiming it — skipping /chart is a build error, the same physics that refuses "
        "skipping a stage inside the chain. Nothing was journaled. Run /chart for this "
        "request (its validate berth carries the claim), then cross again:\n"
        + "\n".join(lines),
        findings=findings,
    )


def _exit_gate(ticket: str) -> str:
    """A cast ticket crossing forward into PROVED must have ANSWERED the chart that
    claims it — every criterion of the claiming validate berth a passing run verdict,
    every hypothesis dispositioned confirmed-or-killed, all in a durable verdict
    artifact (cairn/chart/verdict.py). Returns the one-line gate note the journal
    carries; raises ``ExitGateRed`` — findings complete on the first pass — before
    anything is written.

    Provenance: 2026-07-29, ticket proved-answers-the-chart — the exit half of the
    loop whose entry half is ``_entry_gate`` above ('agreed and go!', the 64% stake's
    other hand): a voyage is charted at BUILDME and measured at PROVED, both by
    physics. The gate shape-checks the artifact on disk only — it runs no
    instruments and reaches no tree or host, so a netns-sealed crossing gates
    identically to a live one.
    """
    # Lazy on purpose, same boot-order law as the gates below: the check's cost
    # lands only at the rare journaled PROVED entry — an event, never a poll.
    from cairn.build_inspector.inspector import proved_answers_the_chart as _check

    findings = _check(ticket)
    if not findings:
        return "clean — no unanswered chart claim stands against ticket %r" % ticket
    lines = [
        f"  [{f['filter']}] {f['finding']} — {f['why_it_matters']} (evidence: "
        f"{json.dumps(f['evidence'], default=str)})"
        for f in findings
    ]
    raise ExitGateRed(
        f"PROVED crossing refused: cast ticket {ticket!r} has not answered its chart — "
        "PROVED asserts done, and done is verified in the world by the instrument, "
        "never the narration. Nothing was journaled. Run the claiming validate berth's "
        "criteria, write the verdict artifact (cairn.chart.verdict.write_verdict), "
        "deposit it, then cross again:\n" + "\n".join(lines),
        findings=findings,
    )


def _enqueue_verdict(ticket: str) -> str | None:
    """THE DEPOSIT ENQUEUE (ticket the-deposit-rides-the-read, 2026-07-29): an
    exit-gate-clean forward crossing into PROVED files its answering verdict berth
    on chart's append-only pending ledger, so the deposit into the hypothesize tree
    stops being a sail step someone remembers and becomes a CONSEQUENCE of the
    crossing. The tree side is paid at chart.live's next door entry (the read is
    the event — no clock, no daemon); an undeposited verdict is a measurable
    pending entry, never a silent lapse.

    A FILE WRITE ONLY. Coupling this door to the db/embed hosts is exactly what
    build_inspector edge (l) says would break netns sealing, so the crossing writes
    the cheap durable half and never reaches a host: a sealed crossing enqueues
    identically to a live one.

    Keys on the ARTIFACT, never on the gate's clean note: the exit gate is clean
    both when a chart was answered AND when no chart claims the ticket at all, so
    the unclaimed gated-and-clean crossing has no artifact and enqueues nothing
    (returns None). Refusals never reach here, and back-edges are never gated.

    A ledger write that fails propagates LOUDLY (nothing is journaled): a deposit
    obligation that could not be recorded must not be swallowed into a green
    crossing (Law 7).
    """
    # Lazy on purpose, same boot-order law as the gates: the cost lands only at a
    # journaled PROVED entry — an event, never a poll.
    from cairn.chart.verdict import enqueue_verdict as _enqueue

    return _enqueue(ticket)


def _build_gate(history_path: str) -> str:
    """Run the build_inspector on the component at the crossing's own address; refuse on red.

    The component IS its address: ``history_path`` lives beside the code it voyages for
    (Law 5), so the directory holding it is the component and that directory's parent is the
    tree the census measures it within. Returns the one-line gate note the journal carries
    (the crossing's record of truth says the gate ran and what it saw); raises
    ``BuildGateRed`` — findings complete on the first pass — before anything is written.

    Provenance: 2026-07-27, build_inspector's filed edge (a) — 'today CC runs it; the lever
    lands when a PROVEME crossing is refused while the inspector reds.' Wired at the
    emit-chokepoint because the clearance gate wraps emit: this is the one door.
    """
    # Lazy on purpose: the rules layer stays import-light for every non-gated transition,
    # and the gate's cost (an AST census) lands only at the rare promotion event — an event,
    # never a poll.
    from cairn.build_inspector.inspector import inspect as _inspect
    from cairn.orient.orient import ScanRefused

    comp_dir = Path(history_path).resolve().parent
    try:
        report = _inspect(root=comp_dir.parent, component=comp_dir.name)
    except ScanRefused as e:
        raise BuildGateRed(
            f"PROVEME crossing refused: the census cannot measure component "
            f"{comp_dir.name!r} at {comp_dir} — {e} A gate that silently inspects nothing "
            "passes everything (Law 8), so an uninspectable address is refused, not waved "
            "through. Disposition: make the component census-visible (grow the census — the "
            "learning device's move: new blindness, new scan), or re-home its history beside "
            "measurable code."
        ) from e
    if report["clean"]:
        return (f"clean — build_inspector ran {len(report['filters_run'])} filters over "
                f"{comp_dir.name}")
    lines = [
        f"  [{f['filter']}] {f['finding']} — {f['why_it_matters']} (evidence: "
        f"{json.dumps(f['evidence'], default=str)})"
        for f in report["findings"]
    ]
    raise BuildGateRed(
        f"PROVEME crossing refused: component {comp_dir.name!r} reds the build_inspector "
        f"({len(report['findings'])} finding(s)) — nothing enters proven-space past a red "
        "gate (Law 8). Nothing was journaled. Fix the findings or kick back to BUILDME; "
        "every finding is complete here, no re-run needed:\n" + "\n".join(lines),
        findings=report["findings"],
    )


def render(wf: Workflow, target: str) -> str:
    """Render the workflow string with the cursor moved to ``target`` (the new instance state).
    Objects ride back out verbatim — the string is the record, so a round-trip that dropped
    ``WATCHME(x)`` down to ``WATCHME`` would erase the obligation while looking like a move."""
    idx = resolve_target(wf, target)
    states = []
    for k, s in enumerate(wf.path):
        obj = wf.objects[k] if k < len(wf.objects) else None
        tok = f"{s}({obj})" if obj else s
        states.append(f"[{tok}]" if k == idx else tok)
    return f"{wf.node_class}@{wf.version}: " + " -> ".join(states)


def emit(
    workflow_str: str,
    target: str,
    *,
    history_path: str | None = None,
    state_path: str | None = None,
    node_class_root: Path | str = _NODE_CLASSES,
    **journal_extra,
) -> str:
    """The chokepoint: validate the transition (RULES), then journal the crossing (TRUTH),
    then return the new workflow string. Refuses the illegal before any record is written.

    If ``history_path``/``state_path`` are given, the crossing appends through the projector's
    single write-door — append-only, cursor bounded, no in-place edit (Law 7). A back-edge
    carries its ``severity`` (how far back); routing very-wrong kick-backs to the ask-Akien
    escalation is a filed edge, not this rung. AUTHORITY (who may) is the harbor's clearance
    gate wrapping this call — not checked here.
    """
    wf = parse_workflow(workflow_str)
    class_def = load_class_def(wf.node_class, root=node_class_root)
    validate_transition(wf, target, class_def=class_def)
    new_str = render(wf, target)
    if history_path and state_path:
        target_idx = resolve_target(wf, target)
        # THE BUILD GATE: crossing the PROVEME summons forward runs the build_inspector on
        # the component at this crossing's address; a red refuses BEFORE anything is written
        # (a refused move leaves no partial record). Back-edges retreat ungated.
        gate_note = None
        if wf.here == "PROVEME" and target_idx > wf.cursor:
            gate_note = _build_gate(history_path)
        # THE ENTRY GATE: crossing forward INTO the BUILDME summons requires a named,
        # CAST ticket — or the crossing's own component on the explicit exempt
        # roster — else it refuses BEFORE anything is written (ticket
        # a-voyage-names-its-ticket, 2026-07-29; retires charter edge (k)'s v0
        # opt-in jurisdiction). A named, cast ticket then requires a berthed chart
        # chain claiming it, same as before this stone. Back-edges into BUILDME
        # retreat ungated (never subject to either check).
        entry_note = None
        if target == "BUILDME" and target_idx > wf.cursor:
            _ticket = journal_extra.get("ticket")
            _exempt = _require_named_ticket(target, _ticket, history_path=history_path)
            entry_note = _exempt if _exempt is not None else _entry_gate(_ticket)
        # THE EXIT GATE: crossing forward INTO PROVED requires a named, CAST ticket
        # — or the crossing's own component on the explicit exempt roster — else it
        # refuses BEFORE anything is written (ticket a-voyage-names-its-ticket,
        # 2026-07-29; retires charter edge (k)'s v0 opt-in jurisdiction). A named,
        # cast ticket then requires the claiming chart ANSWERED (verdict artifact
        # complete and passing), same as before this stone. Back-edges retreat
        # ungated (never subject to either check).
        exit_note = None
        # THE EMISSION GATE (ticket watchme-emits-a-probe, 2026-07-30): crossing
        # FORWARD out of a WATCHME the node carried requires that the watch actually
        # EMITTED — its ticket carries a spec for this object, and the probe that spec
        # promised is berthed and armed. Refuses before anything is written. THE FIFTH
        # SEAT, and the first at a FREE summons: the other four sit at fixed backbone
        # crossings, so 'mandatory to satisfy ONCE CARRIED' needed its own seat rather
        # than a clause on someone else's. Back-edges INTO a WATCHME retreat ungated —
        # re-arming a failed watch is the owner's act (Law 6), and gating the retreat
        # would trap the boat at the one state it must be able to return to.
        emission_note = None
        if wf.here == "WATCHME" and target_idx > wf.cursor:
            emission_note = _emission_gate(wf.here_object, journal_extra.get("ticket"))
        # THE DEPOSIT ENQUEUE: an exit-gate-CLEAN crossing files its answering
        # verdict berth on chart's pending ledger before the record is written, so
        # the crossing's own journal names the deposit it owes (ticket
        # the-deposit-rides-the-read). Nothing is enqueued for an exempt crossing
        # (it names no ticket), for an unclaimed one (no artifact exists), or for
        # a refusal (the gate raises above this line).
        enqueued = None
        if target == "PROVED" and target_idx > wf.cursor:
            _ticket = journal_extra.get("ticket")
            _exempt = _require_named_ticket(target, _ticket, history_path=history_path)
            exit_note = _exempt if _exempt is not None else _exit_gate(_ticket)
            if _exempt is None:
                enqueued = _enqueue_verdict(_ticket)
        record = {
            "from": wf.here,
            "to": target,
            # WHERE THE BOAT NOW STANDS. Derived here, not asked of every caller: this
            # function is the one place that knows the crossing landed, and ``standing``
            # is the field a component's readers (harbor_master's register reads
            # ``project(history).cursor["standing"]``) turn into a berth. A caller may
            # override it with a richer line through ``journal_extra`` — the spread below
            # sits after this key deliberately — but it can no longer be forgotten.
            #
            # Found by the append door's shape gate, 2026-07-25, BEFORE this emitter had
            # ever written to a live history: every emit-shaped record on disk was zero.
            # That is the whole argument for the gate — the same fault as the trouble it
            # closes, caught while it was still cheap instead of permanent (Law 7).
            "standing": target,
            "workflow": new_str,
            "direction": "back" if target_idx < wf.cursor else "forward",
            **({"severity": wf.cursor - target_idx} if target_idx < wf.cursor else {}),
            # The record of truth says the gate ran: a PROVEME exit journals what the
            # build_inspector saw, so a promotion's evidence travels with the crossing.
            **({"build_gate": gate_note} if gate_note else {}),
            # The record of truth says the entry gate ran: a gated BUILDME entry
            # journals that its chart claim was checked and found standing.
            **({"entry_gate": entry_note} if entry_note else {}),
            # The record of truth says the exit gate ran: a gated PROVED entry
            # journals that the chart's claims were answered before the close.
            **({"exit_gate": exit_note} if exit_note else {}),
            # The record of truth says the emission gate ran: a gated WATCHME exit
            # journals WHICH probe answered for the watch, so a year later the record
            # names the berth rather than asserting that something was learned.
            **({"emission_gate": emission_note} if emission_note else {}),
            # The record of truth says the deposit was filed: a gated PROVED entry
            # that answered a chart names the berth now standing on chart's pending
            # ledger, so the obligation and the crossing share an address (Law 5).
            **({"deposit_enqueued": enqueued} if enqueued else {}),
            **journal_extra,
        }
        projector.append_entry(history_path, state_path, record)
    return new_str
