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
  - AUTHORITY — who may invoke it? The harbor_master's CLEARANCE gate (child b), which is
             RULED MANDATORY (2026-08-10) and DOES NOT YET WRAP THIS. It calls
             ``validate_transition`` for legality, then adds the owner-gated,
             delegable-per-operation authority (Law 6). Not here — and, as of the
             measurement below, not anywhere: MEASURED 2026-08-10, 186 emit-shaped records
             across the component histories and ZERO carrying ``cleared_by``; ``clear()``
             has no production caller. Until ``emit`` refuses an uncleared crossing, this
             file's claim to be the *authority* door is an IOU, not a fact
             (ticket emit-refuses-an-uncleared-crossing).
  - TRUTH  — record it. ``emit`` journals the crossing append-only through the projector
             door (charter-state-history-split), the same door a charter's state rides.
             Two-vantage: the boat's own history (here) + the harbor register (harbor_master).

The grammar carries the semantics, so most of the table is DERIVED, not stored:
  - ``-ME`` = a SUMMONS (a demand for the peer who acts next). ``THINKME TICKETME BUILDME
    PROVEME WATCHME REVIEWME`` …
  - no ``-ME`` = the node's own CONDITION/REST: ``PROVED`` (passed its gate, grazed by the
    background loop). NOT terminal — a back-edge re-opens it.
    ONE REST, NOT TWO, since 2026-07-30 (ticket watchme-emits-a-probe). There used to be a
    second: a standing-driver rest, "actively collecting". It is DISSOLVED, not renamed —
    a ticket does not BECOME a watcher, it CREATES one and rests. A proved intention's
    efficacy data can only accumulate AFTER it rests, so a ticket that turned into its own
    watcher would never rest and would never be the thing measured. The standing worker is
    a PROBE (``cairn/tools/base/probe.py``), a different species from a ticket: immutable,
    carrying no authority, and outliving the crossing that created it.
    That deletes a state rather than adding one. WORDING, ruled by Akien 2026-08-03: the
    state CAUSES THE CREATION of a probe (*emission* was the wrong word), and once the
    probe is created THE STATE IS COMPLETE. The dead tokens survive only in v1 strings, in
    history, and in the migration code below that has to match them literally in order to
    strip them — a record of truth is never edited to hide the shape it used to have
    (Law 7), and a sweep cannot remove a token it may not name.
What the grammar cannot derive, the class definition declares — and there are exactly TWO
such facts, orthogonal on purpose:
  - ``skippable_summons`` — which summons is an optional FORK at runtime (``TICKETME``: a
    leaf goes THINKME->BUILDME; a parent goes THINKME->TICKETME).
  - ``free_summons`` — which summons may appear ZERO OR MORE TIMES AT ANY POSITION in the
    authored string (``WATCHME``, from v2). Skippable is about the fork a node TAKES; free
    is about the shape the ticket AUTHORED. A free summons is lifted out of the string
    before the backbone is compared to the registered path, so "a drifted string is refused"
    stays true while it roams — and it must NAME ITS OBJECT (``WATCHME(what-it-watches)``),
    because a watch without an object is inert. Being free does NOT make it skippable:
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
``history_path``), and is refused while any sieve reds. The gate lives HERE because this is
the one door THE JOURNAL passes through — every record of truth is written here — so wiring
anywhere else (the tester's discipline, a hook CC remembers to run) would be the
run-it-by-discipline gap the inspector exists to close. (This sentence used to read 'the
clearance gate wraps emit', which was false for a year and is still not what happens: the
clearance gate is a SEAT AT this door, below, not a wrapper around it. The build gate's
argument never depended on either — it depends on emit owning the journal.) Jurisdiction is the addressed crossing: no ``history_path`` means no journal,
so the record of truth does not move and there is nothing to gate. Kick-backs OUT of PROVEME
are never gated — retreating on a red is the correct move. An address the census cannot see
is REFUSED, not skipped: a gate that silently inspects nothing passes everything (Law 8), and
the refusal names the growth path (grow the census/sieves, the learning device's move).

THE CLEARANCE GATE (2026-08-10, ticket emit-refuses-an-uncleared-crossing, draining the live
trouble ``every-crossing-goes-around-the-clearance-gate``): a journaled FORWARD crossing into
a REST — ``not is_summons(target)``, i.e. the move that ENTERS proven-space — must carry the
witness ``harbor_master.clearance.clear`` stamps, and this door re-reads the Law 8 half of it
against the world (the named proof must be in proven-space right now, at the seal date the
record claims). The demanded set is derived from the grammar, never from a component list, so
a future class inherits the rule for free.

  WHAT IT IS NOT. It is not a wrapper — the harbor's gate calls emit, not the other way
  round — and it does not decide WHO MAY. That is Law 6 and it stays at harbor_master's
  door; this seat asks only whether the authority rung RAN, which is a Law 7 question about
  a record's completeness. A forged actor over a genuinely proven proof passes here and is
  recorded permanently for the owner to find.

  WHY IT IS SCOPED TO THE REST rather than to every crossing: that is exactly the crossing
  ``clear`` already knows how to judge (it reads ``standing`` on the proof), and a voyage
  seals that proof one step earlier at PROVEME — so the demand is affordable and
  ``_CLEARANCE_EXEMPT_ROSTER`` stays EMPTY. Its own build's PROVED crossing CLEARS rather
  than being waived, which is the difference between a gate and a wall with a guest list.

Dependency-light AT IMPORT: pure parsing + the projector's pure core. No device, no bus, no
DB. The build gate summons the build_inspector LAZILY, only at a journaled PROVEME exit, and
the clearance gate summons ``validation_store.standing`` the same way — all modules
(inference-free by their own proofs), so the boot-order law holds.

    python3 cairn/tools/base/proofs/test_transitions.py     # exit 0 = green
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from cairn.tools.charter import projector
from cairn.tools.gate import gate

_REPO_ROOT = Path(__file__).resolve().parents[3]
_NODE_CLASSES = _REPO_ROOT.parent / "CairnCommons" / "node_classes"

_HEADER_RE = re.compile(r"^\s*([a-z][a-z-]*)@(v\d+)\s*$")     # "code-seam@v1"
# A state token, maybe bracketed, maybe carrying its OBJECT in parens — "WATCHME(what-it-watches)"
# — and, on the cursor only, its PICKUP PHASE after a colon — "[BUILDME:waiting]" (ruled
# 2026-08-07, the-ticket-is-the-source-period). The capture is deliberately wider than the
# legal vocabulary so "[BUILDME:Waiting]" is refused loudly instead of silently truncating
# the walk. Prose after the token is ignored (see the walk in parse_workflow).
_STATE_RE = re.compile(r"^\[?([A-Z][A-Z_]*)(?:\(([^)]*)\))?(?::([A-Za-z-]+))?\]?")
# The pickup lifecycle every summons inherits, stated once: a summons ARRIVES waiting (no
# pickup yet) and a journaled pickup advances it to in-process. Terminals and rests take no
# phase — a state that summons nobody has no pickup to show. A bare cursor (no colon) is the
# whole legacy corpus and parses as phase=None forever; there is no v3.
_PHASES = ("waiting", "in-process")


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


# ---------------------------------------------------------------------------
# THE PROOF RECORD — every check that ran, expected beside actual, PASSES INCLUDED.
#
# Akien, 2026-08-13: "EVERYTHING ALWAYS PROVED AND LISTING WHAT IT PROVED. SAME PATTERN
# EVERYWHERE." The six seats at this chokepoint each used to return one PROSE sentence on
# success — "clean — a berthed chart chain claims ticket X" — which says that A gate ran
# and never WHICH CHECKS it ran. The entry gate is the clearest case: it composes THREE
# sieves and collapses them into one word, so a sieve that stopped firing and a crossing
# that genuinely satisfied all three wrote the identical line into a record of truth,
# forever (Law 7). The record ends that: a check that stops running makes the list SHORTER,
# not cleaner.
#
# DERIVED, NEVER PARALLEL. Each ``inspect_*`` below is the ONE implementation; the gate
# function is a view over it — the clean note is rendered FROM the record, and the refusal's
# ``findings`` are read back out of the record's mismatches. Two mouths for one question is
# how a gate and the sentence it prints come to disagree.
#
# ELIGIBILITY IS NESTED, NOT PASSED. A lane whose input the lane above it already refused is
# ABSENT from the record, never a green entry: one fault yields exactly one failing entry.
# That is why the inspectors below append conditionally and return early rather than
# evaluating every lane defensively.
#
# BOTH SIDES READ THE SAME SENTENCE WHEN A LANE PASSES. A lane whose ``expected`` and
# ``actual`` cannot be ``==`` on a healthy subject reds every healthy subject — measured n=4
# on 2026-08-13 (gate.py's module docstring carries the hazard). The offending value rides in
# ``values``. Sieve lanes therefore compare ``[]`` against the sieve's own finding sentences.


def _lane(identity: str, *, expected, actual, code: str, **values) -> dict:
    """One entry in this module's proof record, in the shape every gate in the corpus emits.

    ``location`` is this door for every lane — the emit-chokepoint is one address, and a
    reader who wants the subject reads ``values``. ``source`` names the function that
    OWNS the rule, so a lane can be traced to the code that decides it rather than to the
    renderer that printed it.
    """
    return gate.proved(identity=identity, expected=expected, actual=actual,
                       location="cairn/tools/base/transitions.py",
                       code=code, source="transitions." + code.split("::")[-1],
                       **values)


def _mismatches(record: list[dict]) -> list[dict]:
    """The record's failing entries. THE VIEW every refusal below renders from."""
    return [e for e in record if not gate.passed(e)]


def _findings_of(record: list[dict]) -> list[dict]:
    """The old ``findings`` payload, read back OUT of the record rather than built beside it.

    A lane that refused while naming no finding still speaks here — a refusal with no
    sentence is exactly the silence the record exists to end, and flattening the lists
    alone would have dropped it.
    """
    out: list[dict] = []
    for entry in _mismatches(record):
        found = (entry.get("values") or {}).get("findings")
        out.extend(found or [{
            "about": "lane %s refused and named no finding" % entry["identity"],
            "expected": entry["expected"],
            "actual": entry["actual"],
            "compare": "exact",
            "method": entry["identity"],
            "component": entry["identity"],
        }])
    return out


def _proved_note(what: str, record: list[dict]) -> str:
    """The journal's clean line, RENDERED FROM THE RECORD — so it can no longer say 'clean'
    about checks that did not run. It names the count and every lane by name, which is the
    half the old sentence threw away."""
    return "clean — %s proved %d check(s): %s" % (
        what, len(record), ", ".join(e["identity"] for e in record))


def _sieve_lane(identity: str, findings: list[dict], *, code: str, **values) -> dict:
    """One composed sieve as one lane: expected NO finding, actual the sentences it wrote.

    Both sides read ``[]`` when the sieve is clean — the authoring hazard's rule — and a
    refusal carries the whole finding dicts in ``values['findings']`` so the refusal message
    and the record cannot describe different things.
    """
    return _lane(identity,
                 expected=[],
                 actual=[f.get("about", str(f)) for f in findings],
                 code=code, findings=findings, **values)


def inspect_emission(obj: str | None, ticket: object) -> list[dict]:
    """THE EMISSION GATE'S PROOF RECORD — three lanes, eligibility-nested.

    A ticketless crossing cannot be asked whether its spec is present, and an absent spec
    cannot be asked whether its probe is armed: each lane's input is the lane above it, so a
    refusal upstream leaves the ones below ABSENT rather than green. One fault, one failing
    entry — which is why this returns early instead of evaluating all three defensively.
    """
    from cairn.tools.base import watchme_spec

    code = "transitions.py::inspect_emission"
    cast = isinstance(ticket, str) and (_TICKETS / (ticket + ".json")).exists()
    named = f"a cast ticket for the WATCHME({obj}) crossing"
    record = [_lane("the_crossing_names_a_cast_ticket",
                    expected=named,
                    actual=named if cast else (
                        "no ticket named on the crossing" if not isinstance(ticket, str)
                        else "named %r, and no ticket is cast at that address" % ticket),
                    code=code, ticket=ticket, watch_object=obj,
                    looked_at=str(_TICKETS / (str(ticket) + ".json")))]
    if not cast:
        return record

    data = json.loads((_TICKETS / (ticket + ".json")).read_text(encoding="utf-8"))
    spec = watchme_spec.spec_for(data, obj)
    carried = f"ticket {ticket!r} carries a watchme spec for {obj!r}"
    record.append(_lane("the_ticket_carries_a_spec_for_this_watch",
                        expected=carried,
                        actual=carried if spec is not None else
                        f"ticket {ticket!r} carries no watchme spec for {obj!r}",
                        code=code, ticket=ticket, watch_object=obj,
                        findings=[] if spec is not None else [{
                            "sieve": "watchme_spec",
                            "finding": watchme_spec.watchme_spec_error(data),
                            "why_it_matters": "optional to carry, MANDATORY to satisfy once "
                                              "carried — the string says this node has this watch",
                            "evidence": {"ticket": ticket, "object": obj}}]))
    if spec is None:
        return record

    err = watchme_spec.armed_error(spec)
    armed = "the probe the spec promised is berthed and armed"
    record.append(_lane("the_promised_probe_is_berthed_and_armed",
                        expected=armed,
                        actual=armed if not err else err,
                        code=code, ticket=ticket, watch_object=obj,
                        berth=spec.get("probe"),
                        findings=[] if not err else [{
                            "sieve": "armed",
                            "finding": err,
                            "why_it_matters": "a watch that cannot be fired gathered nothing; "
                                              "EMISSION, not accumulation",
                            "evidence": {"berth": spec.get("probe"), "ticket": ticket}}]))
    return record


def _emission_gate(obj: str | None, ticket: object) -> tuple[str, list[dict]]:
    """A node crossing FORWARD out of a WATCHME it carried must have EMITTED its probe.
    Returns ``(note, record)`` — the one-line gate note the journal carries beside the proof
    record it is RENDERED FROM; raises ``WatchmeEmissionRed`` before anything is written.

    EMISSION, NOT ACCUMULATION — the ticket's own phrase. The failure this refuses is a node
    that walks past its own watch having gathered nothing: the forced-and-ungated shape that v1
    measured and that this whole node dissolves. That summons sat in the backbone, forced, and
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
    record = inspect_emission(obj, ticket)
    bad = _mismatches(record)
    if bad:
        raise WatchmeEmissionRed(
            f"WATCHME({obj}) crossing refused — {bad[0]['actual']}. Nothing was journaled. "
            f"{len(record)} check(s) ran and are named on this first pass; berth and arm the "
            "probe, name the ticket on the crossing (ticket=<id>), or back-edge and drop the "
            "watch from the string through the owner's gate. A watch that cannot be checked "
            "is not a watch (Law 3).\n" + "\n".join(
                f"  [{e['identity']}] expected {e['expected']!r}, actual {e['actual']!r}"
                for e in bad),
            _findings_of(record))
    berth = (record[-1].get("values") or {}).get("berth")
    return ("%s — WATCHME(%s) emitted the probe berthed at %s (ticket %r)" % (
        _proved_note("the emission gate", record), obj, berth, ticket), record)


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


def inspect_rules(wf: Workflow, target: str, *, class_def: dict) -> list[dict]:
    """THE RULES RUNG'S PROOF RECORD — three lanes, eligibility-nested, ALWAYS RUN.

    This is the one inspector at this door that fires on EVERY crossing, gated or not, so
    every journaled record carries at least these three lanes: NO EMPTY ANYWHERE. It is also
    the reason the five guarded gates below may return early — the always-running rung above
    them has already closed the gate on a crossing that is not even a legal edge.

    The nesting is not defensive style, it is the rule: ``resolve_target`` is meaningless for
    a target outside the vocabulary, and every out-of-path target is also outside
    ``legal_targets``, so evaluating all three flat would multiply ONE fault into three
    failing entries in three vocabularies — the shape a proof record exists to prevent.
    """
    code = "transitions.py::inspect_rules"
    known = target in wf.path
    vocab = f"{target!r} in the {wf.node_class}@{wf.version} vocabulary"
    record = [_lane("the_target_is_in_the_vocabulary",
                    expected=vocab,
                    actual=vocab if known else
                    f"{target!r} is not in the {wf.node_class}@{wf.version} vocabulary",
                    code=code, target=target, vocabulary=list(wf.path))]
    if not known:
        return record

    # A NO-OP IS A POSITION, NOT A NAME. Once a free summons may repeat, a node standing at
    # one WATCHME and moving to the NEXT one is a real crossing that happens to share a name;
    # refusing it on the name would make a two-watch node un-crossable at its first watch.
    idx = resolve_target(wf, target)
    moves = idx != wf.cursor
    crossing = f"{wf.here} -> {target} moves the cursor off position {wf.cursor}"
    record.append(_lane("the_crossing_moves_the_cursor",
                        expected=crossing,
                        actual=crossing if moves else
                        f"{target!r} -> {target!r} is a no-op at position {wf.cursor}, "
                        "not a transition",
                        code=code, target=target, cursor=wf.cursor, resolved=idx))
    if not moves:
        return record

    legal = legal_targets(wf, class_def=class_def)
    edge = f"{wf.here} -> {target}"
    record.append(_lane("the_crossing_is_a_legal_edge",
                        expected=edge,
                        actual=edge if target in legal else
                        f"{edge} is illegal for {wf.node_class}@{wf.version}",
                        code=code, target=target, legal_from_here=sorted(legal),
                        direction="back" if idx < wf.cursor else "forward"))
    return record


def validate_transition(wf: Workflow, target: str, *, class_def: dict) -> list[dict]:
    """Refuse an illegal transition, loudly (Law 4/7). Silence would be a silent bad default.

    Returns the RULES rung's proof record so the crossing's journal can carry what the rules
    proved — every lane that ran, expected beside actual, passes included. The return value
    is additive: this raised on refusal and returned ``None`` before, and callers that ignore
    it are unchanged.
    """
    record = inspect_rules(wf, target, class_def=class_def)
    bad = _mismatches(record)
    if bad:
        e = bad[0]
        detail = ""
        if e["identity"] == "the_target_is_in_the_vocabulary":
            detail = " %s" % list(wf.path)
        elif e["identity"] == "the_crossing_is_a_legal_edge":
            detail = (" (legal from here: %s) — e.g. a forward skip past a gate summons is "
                      "refused" % sorted((e.get("values") or {})["legal_from_here"]))
        raise IllegalTransition(str(e["actual"]) + detail)
    return record


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


def inspect_named_ticket(target: str, ticket: object, *, history_path: str) -> list[dict]:
    """THE TICKET PRECONDITION'S PROOF RECORD — two lanes, eligibility-nested.

    A crossing that named no ticket has nothing for the second lane to weigh, so the
    cast-check is ABSENT there rather than green. The roster is read INSIDE the first lane's
    actual rather than as a lane of its own: exempt and named are two ways of SATISFYING one
    rule, not two rules, and splitting them would make an exempt crossing carry a failing
    lane it can never satisfy.
    """
    code = "transitions.py::inspect_named_ticket"
    comp = Path(history_path).resolve().parent.name
    exempt = ticket is None and comp in _EXEMPT_ROSTER
    shown = f"a ticket named on the {target} crossing, or {comp!r} on _EXEMPT_ROSTER"
    record = [_lane("the_crossing_shows_its_ticket_or_its_exemption",
                    expected=shown,
                    actual=shown if (ticket is not None or exempt) else
                    f"no ticket is named on the {target} crossing and {comp!r} is not on "
                    "_EXEMPT_ROSTER",
                    code=code, target=target, ticket=ticket, component=comp,
                    exempt=exempt, roster=sorted(_EXEMPT_ROSTER))]
    if ticket is None:
        return record

    cast = isinstance(ticket, str) and (_TICKETS / (ticket + ".json")).exists()
    named = f"named ticket {ticket!r} is cast"
    record.append(_lane("the_named_ticket_is_cast",
                        expected=named,
                        actual=named if cast else f"named ticket {ticket!r} is not cast",
                        code=code, target=target, ticket=ticket,
                        looked_at=str(_TICKETS / (str(ticket) + ".json"))))
    return record


def _require_named_ticket(target: str, ticket: object, *,
                          history_path: str) -> tuple[str | None, list[dict]]:
    """The one precondition BOTH doors share (replacing the two former opt-in
    ``isinstance`` checks): a forward crossing into BUILDME or PROVED must
    name a CAST ticket, or refuse before anything is written.

    Returns ``(note, record)``. The note is an exemption line — journaled through the same
    ``entry_gate``/``exit_gate`` key the real gate below uses, so an exempt pass is
    gated-and-clean on the record, never silent — when the crossing's own
    component name is on the explicit ``_EXEMPT_ROSTER`` and NO ticket was
    named at all. The note is ``None`` when a named, cast ticket is present — the
    caller proceeds into the standing entry/exit gate exactly as before this
    stone — and the record rides along either way, so an exempt crossing journals
    WHAT WAS PROVED about it rather than only that it was let through. Raises
    ``TicketRequiredRed`` otherwise: no ticket and no roster
    match (routes to /sorted), or a named ticket that is not cast (never
    exempt — naming one is a claim to be judged, not a claim to be waived).
    """
    record = inspect_named_ticket(target, ticket, history_path=history_path)
    bad = _mismatches(record)
    if bad:
        # The component is read off lane 1, which always ran — lane 2 is about the ticket,
        # not the address, and asking it for the address would be reaching into the wrong lane.
        comp = (record[0].get("values") or {})["component"]
        if bad[0]["identity"] == "the_crossing_shows_its_ticket_or_its_exemption":
            raise TicketRequiredRed(
                f"{target} crossing refused: no ticket is named on the crossing — a forward "
                "crossing into BUILDME or PROVED must name a cast ticket (Law 8: nothing enters "
                "proven-space without showing its ticket; the side door for a delegated build "
                "that omits the name closes here). Nothing was journaled. Cast the work as a "
                f"ticket (/sorted), name it on the crossing (ticket=<id>), then cross again — or, "
                f"if this component's crossings are a legitimate exception, add {comp!r} to "
                "_EXEMPT_ROSTER explicitly, never silently.",
                _findings_of(record))
        raise TicketRequiredRed(
            f"{target} crossing refused: named ticket {ticket!r} is not cast — no file at "
            f"{_TICKETS / (str(ticket) + '.json')}. A named-but-uncast ticket is an error to "
            "fix, never an exemption (naming one is a claim to be judged, not waived by "
            "coincidence of address). Cast it via /sorted, or correct the name, then cross "
            "again. Nothing was journaled.",
            _findings_of(record))
    if ticket is None:
        comp = (record[0].get("values") or {})["component"]
        return (f"exempt — {comp!r} is on the explicit ticketless roster (_EXEMPT_ROSTER); "
                + _proved_note("the ticket precondition", record), record)
    return None, record


# THE CLEARANCE-EXEMPT ROSTER (ticket emit-refuses-an-uncleared-crossing, 2026-08-10):
# call-site component names allowed to cross forward into a REST with NO clearance at
# all. A SECOND roster beside ``_EXEMPT_ROSTER``, deliberately, and the two are not one
# artifact wearing two hats. They answer different questions — that one asks "may this
# cross without NAMING A TICKET", this one asks "may this cross WITHOUT CLEARANCE" — and
# their empty states make opposite claims, which is what settles it: an empty
# ``_EXEMPT_ROSTER`` claims that NOTHING may skip naming a ticket, so lending it a second
# meaning would silently invert that claim into "nothing may skip clearance either",
# a rule nobody wrote and nobody could point at. Two rosters is the honest cost; one
# roster with two meanings is a laundered one.
#
# EMPTY IN V0, BY MEASURE AND NOT BY OPTIMISM. The rule below demands clearance only of
# the crossing INTO proven-space, which is the crossing that has a freshly sealed proof
# to name (a voyage seals at PROVEME, one step earlier). So the bootstrap needs no entry:
# THIS TICKET'S OWN PROVED CROSSING CLEARS RATHER THAN BEING WAIVED, which is the whole
# difference between a gate and a wall with a guest list. An entry here is a real
# exemption for a real reason stated beside it — never a component that is merely behind
# on its seals, which would be the ticket's falsifier clause (1): an exemption roster
# that grows to cover the fleet is the gate not landing, wearing a roster's clothes.
_CLEARANCE_EXEMPT_ROSTER: frozenset[str] = frozenset()


class ClearanceRequiredRed(IllegalTransition):
    """The forward crossing into a REST is refused: the crossing carries no evidence that
    the AUTHORITY rung ran, and the crossing's component is not on the explicit
    ``_CLEARANCE_EXEMPT_ROSTER`` (EMPTY in v0). Nothing is written before this raises.

    The SIXTH seat at the chokepoint, and the narrowest. Sibling of ``EntryGateRed`` /
    ``BuildGateRed`` / ``ExitGateRed`` / ``WatchmeEmissionRed`` / ``TicketRequiredRed`` —
    sharing the ``IllegalTransition`` parent, not each other.

    WHAT THIS GATE DOES NOT DO, and the distinction the whole build turns on: it does not
    decide WHO MAY. That is Law 6 and it belongs to ``harbor_master``, whose charter says
    so in its own words — 'AUTHORITY (Law 6) — WHO may invoke it? THIS FILE'. Teaching
    ``base`` to judge authority would break Law 6 in the very act of enforcing it. So this
    gate reads a RECORD, not a right: it asks whether the crossing carries the witness the
    clearance gate stamps, which is a Law 7 completeness check on a record of truth. The
    difference is not a technicality — it is why this refusal can live at base's door at
    all.

    WHY ONLY A REST (the demanded set, settled 2026-08-10). Clearance's second refusal is
    Law 8: ``proven_by`` must name a proof that is sealed and still describes the code as
    it stands. A crossing that summons no code has no such proof to name — a TICKETME or a
    BUILDME entry runs nothing, so any address it named would be about the COMPONENT
    ('this was once green') rather than about the MOVE ('this move is authorized'), and
    clearance would come to mean the weaker thing everywhere. The grammar already draws
    the line for us: a state ending in ``-ME`` is a summons, and a state that does not is
    the node's own rest — the one crossing that ENTERS proven-space. Demanding clearance
    exactly there puts the check where its own semantics live, and nowhere else. This is a
    rule about the CROSSING, derived from the grammar; it is not a list of components, and
    it must never become one.

    Provenance: 2026-08-10, ticket emit-refuses-an-uncleared-crossing, under Akien's ruling
    the same day ('Law 4: the chokepoint refuses a crossing carrying no cleared_by' —
    confirmed in his words, 'indeed and honestly, why else have them?'). It closes the
    trouble every-crossing-goes-around-the-clearance-gate, whose measured condition was
    that ZERO of 189 emit-shaped records carried ``cleared_by`` — not one crossing in the
    system's recorded life had passed the authority rung."""

    def __init__(self, message: str, findings: list[dict] | None = None):
        super().__init__(message)
        self.findings = findings or []


class DemoGateRed(IllegalTransition):
    """The forward crossing into PROVED is refused: the ticket carries ``"demo": true``
    and no DEMO validation (quorum seal with Akien's watched-and-approved signature) exists.

    The SEVENTH seat at the chokepoint. Sibling of ``ClearanceRequiredRed`` et al. —
    sharing the ``IllegalTransition`` parent, not each other.

    A DEMO gate is PER-NODE, not per-class — the ticket author binds it at /sorted by
    setting ``"demo": true`` on the tickets Akien wants to watch work. The gate fires only
    on tickets that carry it, so a ticket with no ``demo`` field crosses PROVED ungated by
    this seat (the other seats still fire). Akien watching and approving is the clearing
    act; CC recording it through the quorum door is the notarial act. The quorum door
    already refuses a self-seal (notary == reviewer), so the two-hands requirement is free.

    Provenance: 2026-07-26, ticket demo-gate — Akien's founding reason for Cairn restated
    as a structural gate: 'the prior system didn't have the proving structure there. and we
    didn't have me trying to be insistent on showing me each thing working.' The binding
    question (who picks which tickets carry DEMO) was resolved 2026-08-20: Akien, at
    /sorted. The clearing question: Akien watched and approved."""

    def __init__(self, message: str, findings: list[dict] | None = None):
        super().__init__(message)
        self.findings = findings or []


def _require_demo(ticket: str, journal_extra: dict) -> tuple[str | None, list[dict]]:
    """The seventh gate: a ticket flagged ``"demo": true`` crossing forward into PROVED
    must carry a DEMO validation — a quorum seal with Akien's watched-and-approved
    signature. Returns ``(note, record)`` or ``(None, record)`` when the ticket has no
    demo flag. Raises ``DemoGateRed`` before anything is written.
    """
    import json as _json

    code = "transitions.py::_require_demo"
    ticket_path = _TICKETS / f"{ticket}.json"
    if not ticket_path.exists():
        return (None, [_lane("demo_gate_ticket_readable",
                             expected=f"ticket {ticket!r} exists on disk",
                             actual=f"ticket file not found at {ticket_path}",
                             code=code, ticket=ticket)])

    ticket_data = _json.loads(ticket_path.read_text())
    if not ticket_data.get("demo"):
        return (None, [_lane("demo_gate_binding_check",
                             expected="ticket carries demo flag, or does not",
                             actual=f"ticket {ticket!r} has no demo flag — gate does not fire",
                             code=code, ticket=ticket)])

    from cairn.devices.tester.validation_store import (
        read_validations, validations_path_for_artifact)

    val_path = validations_path_for_artifact(str(ticket_path))
    vals = read_validations(path=val_path)
    demo_vals = [v for v in vals if "demo" in v.get("method", "").lower()
                 or "demo" in v.get("claim", "").lower()]
    green_demos = [v for v in demo_vals if v.get("verdict") == "green"]

    record = [_lane("demo_gate_flag_bound",
                     expected=f"ticket {ticket!r} carries demo: true",
                     actual=f"ticket {ticket!r} carries demo: true — gate fires",
                     code=code, ticket=ticket),
              _lane("demo_validation_exists",
                     expected="a green DEMO validation (quorum seal) exists for this ticket",
                     actual=(f"{len(green_demos)} green DEMO validation(s) found"
                             if green_demos else
                             "no green DEMO validation found — Akien has not watched and approved"),
                     code=code, ticket=ticket, val_path=val_path,
                     demo_validations_found=len(demo_vals),
                     green_demo_validations=len(green_demos))]

    if not green_demos:
        raise DemoGateRed(
            f"PROVED crossing refused: ticket {ticket!r} carries demo: true, but no "
            "DEMO validation exists — Akien has not watched and approved. The gate "
            "demands a quorum seal (quorum.seal with Akien as signer, CC as notary) "
            "before this ticket enters proven-space. Nothing was journaled.",
            findings=_findings_of(record),
        )

    v = green_demos[-1]
    return (f"DEMO gate clean — Akien watched and approved (sealed {v.get('date', '?')}, "
            f"method: {v.get('method', '?')})", record)


def _require_clearance(target: str, journal_extra: dict, *,
                       history_path: str) -> tuple[str, list[dict]]:
    """The sixth gate: a forward journaled crossing into a REST must carry the witness the
    harbor's clearance gate stamps, or refuse before anything is written.

    Returns ``(note, record)``. The note is an exemption line — journaled through its own
    ``clearance_gate`` key, the same
    way the ticket roster's exempt pass is journaled, so an exempt crossing is
    gated-and-clean ON THE RECORD rather than silent — when the crossing's own component
    is on ``_CLEARANCE_EXEMPT_ROSTER``; otherwise it names the proof and seal the
    clearance leaned on. Either way the note is RENDERED FROM the record beside it, so it
    can no longer say the gate ran without saying which checks it ran. Raises
    ``ClearanceRequiredRed`` otherwise.

    IT VERIFIES AGAINST THE WORLD, NOT AGAINST THE FIELD IT WAS HANDED — which is the
    settled pattern of every sibling gate at this chokepoint, and the first version of
    this gate got it wrong. The entry gate reads the chart berths off disk; the exit gate
    reads the verdict artifact off disk; the emission gate resolves the probe off disk.
    A gate that trusted a caller-supplied field would be one keyword away from being
    walked around, which is the trouble this ticket closes, restated one layer out. So a
    complete witness is required (all four fields ``clear`` stamps), and the Law 8 half of
    it is RE-READ: the named proof must be in proven-space right now, and the seal date on
    the record must be the date that seal actually carries. A hand that types
    ``cleared_by=`` into a bare ``emit`` call cannot manufacture either.

    WHAT IT STILL DOES NOT CHECK, and the line is deliberate: whether ``cleared_by`` names
    someone who may. That is Law 6, it is harbor_master's, and base may not compute it.
    A forged actor over a genuinely proven proof would pass here — and it would still be a
    crossing onto proven code, with the forgery recorded permanently in a record of truth
    for the owner to find. Law 8 is base's to re-read at the truth door; Law 6 is not
    base's to decide anywhere.

    ``standing`` is summoned LAZILY, the same way the build gate summons the
    build_inspector, so this module stays dependency-light at import (no device, no bus,
    no DB) and the boot-order law holds.
    """
    record = inspect_clearance(target, journal_extra, history_path=history_path)
    bad = _mismatches(record)
    if bad:
        raise ClearanceRequiredRed(_clearance_refusal(target, record, bad[0]),
                                   _findings_of(record))
    note = _proved_note("the clearance gate", record)
    v = record[0].get("values") or {}
    if not journal_extra.get("cleared_by"):
        return (f"exempt — {v['component']!r} is on the explicit clearance roster "
                f"(_CLEARANCE_EXEMPT_ROSTER); " + note, record)
    via = " (delegated)" if journal_extra.get("delegated") else ""
    sealed = (record[-1].get("values") or {}).get("seal")
    return (f"cleared by {journal_extra['cleared_by']!r}{via} onto "
            f"{journal_extra.get('proven_by')} (seal {sealed}, re-read at the door); "
            + note, record)


def inspect_clearance(target: str, journal_extra: dict, *, history_path: str) -> list[dict]:
    """THE CLEARANCE GATE'S PROOF RECORD — four lanes, eligibility-nested.

    Lane 1 is the fork AND the guard: a crossing carries a clearance witness or it stands on
    the roster, and the three witness lanes below apply only to the first branch. An exempt
    crossing has no witness to weigh, so its record is one lane long and SAYS SO — which is
    the difference between an exemption that is on the record and one that is silent.

    THE WITNESS IS RE-READ AGAINST THE WORLD, never trusted as a field: completeness, then
    the proof's standing in proven-space, then the seal DATE it actually carries. Each is the
    input to the next, so a missing ``proven_by`` leaves the standing lane ABSENT rather than
    failing it in a second vocabulary about the same one fault.
    """
    code = "transitions.py::inspect_clearance"
    comp = Path(history_path).resolve().parent.name
    who = journal_extra.get("cleared_by")
    exempt = not who and comp in _CLEARANCE_EXEMPT_ROSTER
    shown = (f"the {target} crossing into a rest carries the harbor's clearance witness, "
             f"or {comp!r} is on _CLEARANCE_EXEMPT_ROSTER")
    record = [_lane("the_crossing_shows_clearance_or_its_exemption",
                    expected=shown,
                    actual=shown if (who or exempt) else
                    f"the {target} crossing into a rest carries no evidence that the "
                    f"authority rung ran, and {comp!r} is not on _CLEARANCE_EXEMPT_ROSTER",
                    code=code, target=target, component=comp, cleared_by=who,
                    exempt=exempt, roster=sorted(_CLEARANCE_EXEMPT_ROSTER))]
    if not who:
        return record

    missing = [k for k in ("proven_by", "proven_seal_date") if not journal_extra.get(k)]
    whole = "the witness carries every field the harbor's gate stamps"
    record.append(_lane("the_witness_is_whole",
                        expected=whole,
                        actual=whole if not missing else
                        f"the witness is INCOMPLETE — missing {missing}",
                        code=code, target=target, cleared_by=who, missing=missing,
                        demanded=["proven_by", "proven_seal_date"]))
    if missing:
        return record

    from cairn.devices.tester.validation_store import standing  # lazy: keep import dependency-light
    proof = journal_extra["proven_by"]
    proven = standing(proof)
    stands = f"{proof} stands in proven-space"
    record.append(_lane("the_named_proof_stands_in_proven_space",
                        expected=stands,
                        actual=stands if proven["proven"] else
                        f"{proof} is NOT in proven-space: {proven['why']}",
                        code=code, target=target, proof=proof, why=proven["why"]))
    if not proven["proven"]:
        return record

    actual_seal = proven["seal"]["date"]
    dated = f"the witness dates {proof}'s seal at {actual_seal!r}"
    record.append(_lane("the_witness_agrees_with_the_seal_it_names",
                        expected=dated,
                        actual=dated if journal_extra["proven_seal_date"] == actual_seal else
                        f"the witness dates {proof}'s seal at "
                        f"{journal_extra['proven_seal_date']!r}",
                        code=code, target=target, proof=proof, seal=actual_seal,
                        claimed=journal_extra["proven_seal_date"]))
    return record


def _clearance_refusal(target: str, record: list[dict], first: dict) -> str:
    """The refusal message, keyed off WHICH LANE closed the gate — one sentence per lane,
    rendered from the record rather than raised beside it."""
    v = first.get("values") or {}
    ident = first["identity"]
    if ident == "the_witness_is_whole":
        return (f"{target} crossing refused: the record claims cleared_by={v['cleared_by']!r} "
                f"but its witness is INCOMPLETE — missing {v['missing']}. A partial witness "
                "is not a clearance; the harbor's gate stamps all four fields together and a "
                "record carrying only some of them did not come through it. Nothing was "
                "journaled.")
    if ident == "the_named_proof_stands_in_proven_space":
        return (f"{target} crossing refused: the record claims clearance onto {v['proof']}, "
                f"but that proof is NOT in proven-space: {v['why']} A witness naming a proof "
                "the world does not hold proven is not evidence that the authority rung ran "
                "— it is the shape of one. Nothing was journaled. Re-seal the proof, then "
                "clear the crossing through harbor_master's gate.")
    if ident == "the_witness_agrees_with_the_seal_it_names":
        return (f"{target} crossing refused: the record dates the seal on {v['proof']} at "
                f"{v['claimed']!r}, but the standing seal is dated {v['seal']!r}. A witness "
                "that disagrees with the seal it names did not come from the gate that reads "
                "it (Law 7 — a record of truth may not carry an error quietly). Nothing was "
                "journaled.")
    comp = v["component"]
    return (
        f"{target} crossing refused: this is a forward crossing into a REST — the move that "
        f"ENTERS proven-space — and it carries no evidence that the authority rung ran. "
        "Nothing was journaled. Cross through the harbor's gate instead of the bare door: "
        "cairn.devices.cairn.machines.harbor_master.clearance.clear(workflow_str, target, actor=..., boat_id=..., "
        "boat_owner=..., proven_by=<the proof your PROVEME step just sealed>, "
        "history_path=..., state_path=..., ticket=...). That call stamps cleared_by itself "
        "— you cannot supply it here, and a crossing that could would make the check "
        f"vacuous. If {comp!r}'s crossings are a legitimate structural exception, add it to "
        "_CLEARANCE_EXEMPT_ROSTER with the reason beside it, explicitly, never silently."
    )


def inspect_entry(ticket: str) -> list[dict]:
    """THE ENTRY GATE'S PROOF RECORD — one lane per composed sieve, ALL THREE ALWAYS RUN.

    THIS IS THE GATE THE RECORD WAS MOST OWED. It composes three sieves and used to collapse
    them into one sentence, so a sieve that stopped firing and a crossing that genuinely
    satisfied all three wrote the identical line into a record of truth. Three lanes make the
    difference visible: the record gets SHORTER, not cleaner.

    Nothing is nested here, deliberately — the three sieves are independent, a caller missing
    all three must learn all three on the first pass (complete-diagnostic-on-first-pass), and
    fixing one must not merely earn the right to be refused for the next.
    """
    # Lazy on purpose, same boot-order law as the build gate below: the check's cost
    # lands only at the rare journaled BUILDME entry — an event, never a poll.
    from cairn.machines.build_inspector.inspector import buildme_rides_the_chart as _chart
    from cairn.machines.build_inspector.inspector import buildme_rides_the_intent as _intent
    from cairn.machines.build_inspector.inspector import buildme_rides_the_sorted as _sorted

    code = "transitions.py::inspect_entry"
    return [
        _sieve_lane("a_berthed_chart_chain_claims_the_ticket", _chart(ticket),
                    code=code, ticket=ticket),
        _sieve_lane("the_ticket_names_its_intent_firing", _intent(ticket),
                    code=code, ticket=ticket),
        _sieve_lane("the_ticket_names_its_sorted_door_firing", _sorted(ticket),
                    code=code, ticket=ticket),
    ]


def _entry_gate(ticket: str) -> tuple[str, list[dict]]:
    """A cast ticket crossing forward into BUILDME must be claimed by a berthed chart
    chain — the entry half of packet jurisdiction (the PROVEME exit below is the
    promotion half). Returns ``(note, record)`` — the journal's line beside the proof record
    it is RENDERED FROM; raises
    ``EntryGateRed`` — findings complete on the first pass — before anything is
    written.

    Provenance: 2026-07-29, ticket buildme-rides-the-chart — the sail step-0 prose
    refusal ('no berths → run /chart first') retired into physics (Law 4), on
    Akien's word with the stake in numbers (Fable at 64% of usage). Wired at the
    emit-chokepoint because this is the one door; jurisdiction is the crossing's
    own named, cast ticket — an un-cast or unnamed ticket is not gated (v0; the
    stricter require-a-ticket edge is filed on the ticket).
    """
    # ALL checks run, and their findings are reported TOGETHER. Not three gates in
    # sequence: a caller missing a chart, an /intent berth AND a /sorted berth must
    # learn all three on the first pass, or fixing one only earns the right to be
    # refused for the next (the complete-diagnostic-on-first-pass method, and Law 7
    # at a diagnostic surface). The third addend joined 2026-08-03 (ticket
    # sorted-becomes-a-learning-block).
    record = inspect_entry(ticket)
    findings = _findings_of(record)
    if not findings:
        return (
            "clean — a berthed chart chain claims ticket %r, and the ticket names its "
            "/intent firing and its /sorted door firing; %s"
            % (ticket, _proved_note("the entry gate", record)), record
        )
    lines = [
        f"  [{f['method']}] {f['about']} (expected: {f['expected']!r}, actual: "
        f"{f['actual']!r}{', ' + json.dumps(f['values'], default=str) if f.get('values') else ''})"
        for f in findings
    ]
    raise EntryGateRed(
        f"BUILDME crossing refused for cast ticket {ticket!r} — {len(findings)} "
        f"finding(s) across {len(record)} check(s), all named on this first pass. Skipping "
        "/chart, /intent or the "
        "/sorted door is a build error, the same physics that refuses skipping a stage "
        "inside the chain. Nothing was journaled. Fix what is named below, then cross "
        "again:\n"
        + "\n".join(lines),
        findings=findings,
    )


def inspect_exit(ticket: str) -> list[dict]:
    """THE EXIT GATE'S PROOF RECORD — one lane, and one lane is not a formality.

    The sieve it composes answers a compound question (every criterion of the claiming
    validate berth has a passing run verdict, every hypothesis is dispositioned), and the
    record deliberately does NOT split that into lanes here: the decomposition belongs to the
    sieve that owns the rule, and inventing lanes at this door would be a second mouth for
    build_inspector's question. What the lane adds is the one thing the old sentence could
    not say — that this check RAN, by name, on this crossing.
    """
    # Lazy on purpose, same boot-order law as the gates below: the check's cost
    # lands only at the rare journaled PROVED entry — an event, never a poll.
    from cairn.machines.build_inspector.inspector import proved_answers_the_chart as _check

    return [_sieve_lane("the_claiming_chart_is_answered", _check(ticket),
                        code="transitions.py::inspect_exit", ticket=ticket)]


def _exit_gate(ticket: str) -> tuple[str, list[dict]]:
    """A cast ticket crossing forward into PROVED must have ANSWERED the chart that
    claims it — every criterion of the claiming validate berth a passing run verdict,
    every hypothesis dispositioned confirmed-or-killed, all in a durable verdict
    artifact (cairn/devices/builder/machines/verdict/verdict.py). Returns ``(note, record)``
    — the journal's line beside the proof record it is RENDERED FROM;
    raises ``ExitGateRed`` — findings complete on the first pass — before
    anything is written.

    Provenance: 2026-07-29, ticket proved-answers-the-chart — the exit half of the
    loop whose entry half is ``_entry_gate`` above ('agreed and go!', the 64% stake's
    other hand): a voyage is charted at BUILDME and measured at PROVED, both by
    physics. The gate shape-checks the artifact on disk only — it runs no
    instruments and reaches no tree or host, so a netns-sealed crossing gates
    identically to a live one.
    """
    record = inspect_exit(ticket)
    findings = _findings_of(record)
    if not findings:
        return ("clean — no unanswered chart claim stands against ticket %r; %s"
                % (ticket, _proved_note("the exit gate", record)), record)
    lines = [
        f"  [{f['method']}] {f['about']} (expected: {f['expected']!r}, actual: "
        f"{f['actual']!r}{', ' + json.dumps(f['values'], default=str) if f.get('values') else ''})"
        for f in findings
    ]
    raise ExitGateRed(
        f"PROVED crossing refused: cast ticket {ticket!r} has not answered its chart — "
        "PROVED asserts done, and done is verified in the world by the instrument, "
        "never the narration. Nothing was journaled. Run the claiming validate berth's "
        "criteria, write the verdict artifact (cairn.devices.builder.machines.verdict.verdict.write_verdict), "
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
    from cairn.devices.builder.machines.verdict.verdict import enqueue_verdict as _enqueue

    return _enqueue(ticket)


def inspect_build(history_path: str) -> list[dict]:
    """THE BUILD GATE'S PROOF RECORD — the guard lane, then the INSPECTOR'S OWN RECORD.

    THIS ONE DOES NOT BUILD LANES, IT CARRIES THEM. build_inspector already emits a proof
    record — one entry per sieve per component, expected 1.0 beside the actual score — and
    re-deriving lanes here would be a second mouth for its question, which is exactly how a
    gate and the sentence it prints come to disagree. So this door adds the ONE check that is
    its own and that the inspector cannot make: that the census could see the address at all.

    The guard lane is the whole reason a ScanRefused is not just re-raised. 'The census
    cannot measure this component' and 'the census measured it and found nothing wrong' are
    the two states a gate must never confuse (Law 8), and before this the second half of that
    distinction lived only in an exception type. Now it is a lane, and when it fails the
    inspector's own lanes are ABSENT rather than green — because they did not run.
    """
    # Lazy on purpose: the rules layer stays import-light for every non-gated transition,
    # and the gate's cost (an AST census) lands only at the rare promotion event — an event,
    # never a poll.
    from cairn.machines.build_inspector.inspector import inspect as _inspect
    from cairn.tools.orient.orient import ScanRefused

    code = "transitions.py::inspect_build"
    comp_dir = Path(history_path).resolve().parent
    seen = f"the census can measure component {comp_dir.name!r} at {comp_dir}"
    try:
        report = _inspect(root=comp_dir.parent, component=comp_dir.name)
    except ScanRefused as e:
        return [_lane("the_census_can_measure_the_component",
                      expected=seen, actual=f"the census cannot measure it — {e}",
                      code=code, component=comp_dir.name, address=str(comp_dir),
                      findings=[{"sieve": "census",
                                 "finding": str(e),
                                 "why_it_matters": "a gate that silently inspects nothing "
                                                   "passes everything (Law 8)",
                                 "evidence": {"component": comp_dir.name,
                                              "address": str(comp_dir)}}])]
    return [_lane("the_census_can_measure_the_component", expected=seen, actual=seen,
                  code=code, component=comp_dir.name, address=str(comp_dir),
                  sieves_run=report["sieves_run"])] + list(report["proof_record"])


def _build_gate(history_path: str) -> tuple[str, list[dict]]:
    """Run the build_inspector on the component at the crossing's own address; refuse on red.

    The component IS its address: ``history_path`` lives beside the code it voyages for
    (Law 5), so the directory holding it is the component and that directory's parent is the
    tree the census measures it within. Returns ``(note, record)`` — the journal's line
    beside the proof record it is RENDERED FROM, so the crossing's record of truth says the
    gate ran, which sieves it ran, and what each one saw; raises
    ``BuildGateRed`` — findings complete on the first pass — before anything is written.

    Provenance: 2026-07-27, build_inspector's filed edge (a) — 'today CC runs it; the lever
    lands when a PROVEME crossing is refused while the inspector reds.' Wired at the
    emit-chokepoint because emit owns the journal: this is the one door a record of truth
    passes through. (Not because the clearance gate wraps emit — it never has and does not
    now: since 2026-08-10 clearance is a SIBLING SEAT at this same door, scoped to the
    crossing into a rest — ticket emit-refuses-an-uncleared-crossing.)
    """
    comp_dir = Path(history_path).resolve().parent
    record = inspect_build(history_path)
    if not gate.passed(record[0]):
        raise BuildGateRed(
            f"PROVEME crossing refused: the census cannot measure component "
            f"{comp_dir.name!r} at {comp_dir} — {record[0]['actual']} A gate that silently "
            "inspects nothing passes everything (Law 8), so an uninspectable address is "
            "refused, not waved through. Disposition: make the component census-visible "
            "(grow the census — the learning device's move: new blindness, new scan), or "
            "re-home its history beside measurable code.",
            _findings_of(record))
    findings = _findings_of(record)
    if not findings:
        sieves = (record[0].get("values") or {})["sieves_run"]
        return (f"clean — build_inspector ran {len(sieves)} sieves over {comp_dir.name}, and "
                f"{len(record)} check(s) are proved on this crossing", record)
    lines = [
        f"  [{f['method']}] {f['about']} (expected: {f['expected']!r}, actual: "
        f"{f['actual']!r}{', ' + json.dumps(f['values'], default=str) if f.get('values') else ''})"
        for f in findings
    ]
    raise BuildGateRed(
        f"PROVEME crossing refused: component {comp_dir.name!r} reds the build_inspector "
        f"({len(findings)} finding(s) across {len(record)} check(s)) — nothing enters "
        "proven-space past a red gate (Law 8). Nothing was journaled. Fix the findings or "
        "kick back to BUILDME; every finding is complete here, no re-run needed:\n"
        + "\n".join(lines),
        findings=findings,
    )


def _render_at(wf: Workflow, idx: int, phase: str | None) -> str:
    """Render with the cursor at ``idx`` carrying ``phase`` (None = bare). The one string
    assembler — ``render`` (a crossing) and ``pickup`` (a phase advance in place) both come
    through here, so the two doors cannot drift apart on what a cursor looks like."""
    states = []
    for k, s in enumerate(wf.path):
        obj = wf.objects[k] if k < len(wf.objects) else None
        tok = f"{s}({obj})" if obj else s
        if k == idx:
            states.append(f"[{tok}:{phase}]" if phase else f"[{tok}]")
        else:
            states.append(tok)
    return f"{wf.node_class}@{wf.version}: " + " -> ".join(states)


def render(wf: Workflow, target: str) -> str:
    """Render the workflow string with the cursor moved to ``target`` (the new instance state).
    Objects ride back out verbatim — the string is the record, so a round-trip that dropped
    ``WATCHME(x)`` down to ``WATCHME`` would erase the obligation while looking like a move.

    ARRIVAL STAMPS THE PHASE (ruled 2026-08-07): landing on a summons renders it
    ``[X:waiting]`` — the summons is out and nobody has picked it up, and the ticket shows
    that without anyone remembering to write it. Landing on a rest or terminal renders bare.
    The departed state loses any phase it carried: only the cursor has a pickup in flight."""
    idx = resolve_target(wf, target)
    return _render_at(wf, idx, "waiting" if is_summons(wf.path[idx]) else None)


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
    escalation is a filed edge, not this rung.

    AUTHORITY (WHO MAY) IS STILL NOT DECIDED HERE, and that line did not move on 2026-08-10.
    What landed then (ticket emit-refuses-an-uncleared-crossing) is the CLEARANCE GATE — the
    sixth seat below — which reads a RECORD rather than a right: a forward crossing into a
    REST must carry the witness ``harbor_master.clearance.clear`` stamps, and this door
    re-reads the Law 8 half of that witness against the world. Whether the named actor MAY
    is Law 6, it is harbor_master's, and base computes it nowhere. So the honest shape is
    two rungs at one door, not one rung doing two jobs.

    For a year this docstring said 'the harbor's clearance gate wrapping this call', present
    tense, while nothing wrapped anything: measured 2026-08-05, of 229 records across 21
    component histories, 146 were emit-shaped and ZERO carried ``cleared_by``. It still does
    not wrap this call — it is a seat AT it, and only for the crossing into a rest.
    """
    wf = parse_workflow(workflow_str)
    class_def = load_class_def(wf.node_class, root=node_class_root)
    # THE RULES RUNG ALWAYS RUNS, so every journaled crossing carries at least its three
    # lanes: NO EMPTY ANYWHERE (Akien, 2026-08-13). `proved` accumulates every lane every
    # seat below ran, and `checks_proved` is its length — so a gate that stops running makes
    # a crossing's record SHORTER, which is readable, rather than cleaner, which is not.
    proved: list[dict] = list(validate_transition(wf, target, class_def=class_def))
    new_str = render(wf, target)
    if history_path and state_path:
        target_idx = resolve_target(wf, target)
        # THE BUILD GATE: crossing the PROVEME summons forward runs the build_inspector on
        # the component at this crossing's address; a red refuses BEFORE anything is written
        # (a refused move leaves no partial record). Back-edges retreat ungated.
        gate_note = None
        if wf.here == "PROVEME" and target_idx > wf.cursor:
            gate_note, _rec = _build_gate(history_path)
            proved += _rec
        # THE ENTRY GATE: crossing forward INTO the BUILDME summons requires a named,
        # CAST ticket — or the crossing's own component on the explicit exempt
        # roster — else it refuses BEFORE anything is written (ticket
        # a-voyage-names-its-ticket, 2026-07-29; retires charter edge (k)'s v0
        # opt-in jurisdiction). A named, cast ticket then requires a berthed chart
        # chain claiming it, same as before this stone. Back-edges into BUILDME
        # retreat ungated (never subject to either check).
        # THE CLEARANCE GATE (ticket emit-refuses-an-uncleared-crossing, 2026-08-10): a
        # forward crossing into a REST — a state the grammar says summons nobody, i.e. the
        # move that ENTERS proven-space — must carry the witness the harbor's clearance
        # gate stamps, or the crossing's component must be on the explicit clearance
        # roster. Refuses BEFORE anything is written. Keyed off ``is_summons`` rather than
        # off the token "PROVED" deliberately: the demanded set is a rule about the shape
        # of the crossing, derived from the same grammar the rest of this module derives
        # from, so a class whose rest is named something else inherits it for free and no
        # component list is ever consulted. Back-edges retreat ungated, like every sibling
        # gate here — trapping a boat at the state it must be able to return to would make
        # a kick-back impossible, which is the motion a red is supposed to produce.
        # This gate reads a RECORD, never a right: who-may is Law 6 and stays at
        # harbor_master's door (see ``ClearanceRequiredRed``).
        #
        # IT SITS LAST AMONG THE GATES — below the emission gate, above the deposit
        # enqueue — and the position is load-bearing twice over. Below, because the four
        # gates above it ask whether THE WORK IS DONE and this one asks whether the
        # finished work came through the harbor's door; in the voyage that order is the
        # real sequence of events (build it, prove it, emit the watch, then get the
        # crossing cleared), so a caller who is wrong about both hears about the work
        # first, which is the half they can act on. Above the enqueue, because the
        # enqueue is the one thing in this function that touches the world before the
        # record is written: every gate must refuse upstream of it or a refused crossing
        # would leave a deposit owed for a voyage that never closed.
        entry_note = None
        if target == "BUILDME" and target_idx > wf.cursor:
            _ticket = journal_extra.get("ticket")
            _exempt, _rec = _require_named_ticket("BUILDME", _ticket, history_path=history_path)
            proved += _rec
            if _exempt is not None:
                entry_note = _exempt
            else:
                entry_note, _rec = _entry_gate(_ticket)
                proved += _rec
        elif wf.here == "BUILDME" and target_idx > wf.cursor:
            _ticket = journal_extra.get("ticket")
            if _ticket is not None:
                entry_note, _rec = _entry_gate(_ticket)
                proved += _rec
            else:
                entry_note = "not_checked"
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
            emission_note, _rec = _emission_gate(wf.here_object, journal_extra.get("ticket"))
            proved += _rec
        # THE DEPOSIT ENQUEUE: an exit-gate-CLEAN crossing files its answering
        # verdict berth on chart's pending ledger before the record is written, so
        # the crossing's own journal names the deposit it owes (ticket
        # the-deposit-rides-the-read). Nothing is enqueued for an exempt crossing
        # (it names no ticket), for an unclaimed one (no artifact exists), or for
        # a refusal (the gate raises above this line).
        enqueued = None
        _exempt = None
        if target == "PROVED" and target_idx > wf.cursor:
            _ticket = journal_extra.get("ticket")
            _exempt, _rec = _require_named_ticket(target, _ticket, history_path=history_path)
            proved += _rec
            if _exempt is not None:
                exit_note = _exempt
            else:
                exit_note, _rec = _exit_gate(_ticket)
                proved += _rec
        clearance_note = None
        if not is_summons(target) and target_idx > wf.cursor:
            clearance_note, _rec = _require_clearance(target, journal_extra,
                                                      history_path=history_path)
            proved += _rec
        # THE DEMO GATE (ticket demo-gate, 2026-07-26; resolved 2026-08-20): a
        # forward crossing into PROVED on a ticket carrying ``"demo": true`` must
        # carry a DEMO validation — a quorum seal where Akien watched and approved.
        # The SEVENTH SEAT, and the first per-node gate: it fires only when the
        # ticket asks for it, which is Akien choosing at /sorted what he wants to
        # watch work. Sits after clearance (authority check) and before the deposit
        # enqueue (the last world-touching act before the record is written).
        demo_note = None
        if target == "PROVED" and target_idx > wf.cursor and _exempt is None:
            _ticket = journal_extra.get("ticket")
            if _ticket:
                demo_note, _rec = _require_demo(_ticket, journal_extra)
                proved += _rec
        if target == "PROVED" and target_idx > wf.cursor and _exempt is None:
            enqueued = _enqueue_verdict(journal_extra.get("ticket"))
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
            # ALWAYS PRESENT (ticket the-buildme-gates-guard-a-crossing-not-a-state):
            # "not_applicable" when no build-relevant crossing, else the gate's note.
            "entry_gate": entry_note if entry_note is not None else "not_applicable",
            # The record of truth says the exit gate ran: a gated PROVED entry
            # journals that the chart's claims were answered before the close.
            **({"exit_gate": exit_note} if exit_note else {}),
            # The record of truth says the clearance gate ran: a crossing into a rest
            # journals WHICH proof the authority rung leaned on and when it was sealed —
            # or, for an exempt crossing, that it was exempt and by which roster. An
            # exemption that passed silently would be strictly weaker than the ticket
            # roster standing beside it, and it is how this trouble stayed invisible for
            # the whole recorded life of the system.
            **({"clearance_gate": clearance_note} if clearance_note else {}),
            # The record of truth says the demo gate ran: a DEMO-flagged ticket's
            # PROVED crossing journals that Akien watched and approved, with the
            # seal date. A ticket with no demo flag journals nothing — the gate
            # did not fire, and a record that says it did would be fabricated.
            **({"demo_gate": demo_note} if demo_note else {}),
            # The record of truth says the emission gate ran: a gated WATCHME exit
            # journals WHICH probe answered for the watch, so a year later the record
            # names the berth rather than asserting that something was learned.
            **({"emission_gate": emission_note} if emission_note else {}),
            # The record of truth says the deposit was filed: a gated PROVED entry
            # that answered a chart names the berth now standing on chart's pending
            # ledger, so the obligation and the crossing share an address (Law 5).
            **({"deposit_enqueued": enqueued} if enqueued else {}),
            # EVERYTHING ALWAYS PROVED AND LISTING WHAT IT PROVED (Akien, 2026-08-13).
            # Every lane every seat ran on this crossing, expected beside actual, PASSES
            # INCLUDED — the half the ``*_gate`` notes above throw away, and the half that
            # lets a reader backtrack a crossing a year later without re-running anything.
            # Never empty: the rules rung always contributes. ``checks_proved`` is derived
            # from the list rather than counted beside it, so the two cannot disagree.
            "proved": proved,
            "checks_proved": len(proved),
            **journal_extra,
        }
        record["fingerprint"] = _crossing_fingerprint(record)
        projector.append_entry(history_path, state_path, record)
    return new_str


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


def pickup(
    workflow_str: str,
    *,
    actor: str,
    history_path: str | None = None,
    state_path: str | None = None,
    **journal_extra,
) -> str:
    """The pickup door — ``emit``'s sibling for the act that is NOT a crossing (ruled
    2026-08-07, the-ticket-is-the-source-period). A summons goes out ``[X:waiting]``; the
    peer who takes it up comes through HERE, and the ticket advances to ``[X:in-process]``
    with the pickup journaled (who, when — the append door stamps ``at``). The ticket is the
    source, period: nobody derives "is anyone on this?" from a side channel.

    Refusals, before anything is written: a rest or terminal (nothing summoned, nothing to
    pick up) and a doubled pickup (already in-process — the second hand sees the first on
    the ticket, which is the encapsulation the ruling bought). A bare summons cursor (the
    legacy corpus, arrived before phases existed) IS picked up — the act records what
    arrival never stamped.

    ``actor`` is a recorded claim, not an authenticated identity — authenticating it is the
    clearance gate's rung (a named open edge in the definition), not this door's.

    A forward crossing straight from ``:waiting`` stays legal at ``emit`` — today one hand
    summons, picks up, and crosses (single-actor collapse); making pickup a crossing
    precondition is a named future dial, not this door."""
    wf = parse_workflow(workflow_str)
    if not is_summons(wf.here):
        raise IllegalTransition(
            f"pickup refused: {wf.here!r} is a rest or terminal — it summons nobody, so "
            "there is no pickup. Nothing was journaled.")
    if wf.phase == "in-process":
        raise IllegalTransition(
            f"pickup refused: {wf.here!r} is already in-process — a doubled pickup would "
            "overwrite the hand already on the ticket. Nothing was journaled.")
    new_str = _render_at(wf, wf.cursor, "in-process")
    if history_path and state_path:
        record = {
            "act": "pickup",
            "actor": actor,
            # Not a crossing — the boat stands where it stood; ``standing`` is required by
            # the append door's shape gate and stays the same state.
            "standing": wf.here,
            "workflow": new_str,
            **journal_extra,
        }
        projector.append_entry(history_path, state_path, record)
    return new_str
