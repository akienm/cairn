"""base/transitions.py — the EMIT-CHOKEPOINT: the one door a workflow transition passes through.

A node's ``state`` is a versioned, mutable, greppable workflow string with the cursor in
brackets — ``code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED``
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
    PROVEME LEARNME REVIEWME`` …
  - no ``-ME`` = the node's own CONDITION/REST: ``PROVED`` (passed its gate, grazed by the
    background loop) and ``LEARNING`` (a standing driver). Neither terminal.
The ONE thing the grammar cannot derive — which summons is an optional FORK (``TICKETME``
is skippable: a leaf goes THINKME->BUILDME; a parent goes THINKME->TICKETME) — is the one
thing the class definition declares (``skippable_summons``). Everything else falls out:

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
_STATE_RE = re.compile(r"^\[?([A-Z][A-Z_]*)\]?")              # a state token, maybe bracketed, prose after ignored


class MalformedWorkflow(ValueError):
    """The workflow string does not parse, or does not conform to its claimed class@version."""


class IllegalTransition(ValueError):
    """The requested transition is refused by the rules — loud, never silent (Law 7)."""


class BuildGateRed(IllegalTransition):
    """The forward crossing out of PROVEME is refused: the component at the crossing's own
    address reds the build_inspector (or cannot be inspected at all — same refusal, no side
    door). Carries ``findings`` complete on the first pass; fix or kick back, never bypass."""

    def __init__(self, message: str, findings: list[dict] | None = None):
        super().__init__(message)
        self.findings = findings or []


def is_summons(state: str) -> bool:
    """The grammar: a state that ends in ``-ME`` is a SUMMONS (demands a peer); else a rest."""
    return state.endswith("ME")


@dataclass(frozen=True)
class Workflow:
    node_class: str
    version: str
    path: tuple[str, ...]
    cursor: int          # index into ``path`` of the bracketed state

    @property
    def here(self) -> str:
        return self.path[self.cursor]


def parse_workflow(s: str) -> Workflow:
    """Parse ``class@version: S -> S -> [CURSOR] -> S ...`` — trailing prose after the last
    state is tolerated (real tickets carry a parenthetical note after the workflow)."""
    header, sep, rest = s.partition(":")
    m = _HEADER_RE.match(header)
    if not sep or not m:
        raise MalformedWorkflow(f"no 'class@version:' header in {s!r}")
    node_class, version = m.group(1), m.group(2)
    path: list[str] = []
    cursor: int | None = None
    for seg in rest.split("->"):
        seg = seg.strip()
        sm = _STATE_RE.match(seg)
        if not sm:
            break                      # trailing prose (e.g. "(cursor at ...)") — the path is done
        if seg.startswith("["):
            cursor = len(path)
        path.append(sm.group(1))
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
    return Workflow(node_class, version, tuple(path), cursor)


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
    drifted string, refused (validate against a KNOWN versioned definition)."""
    reg = _registered_workflow(class_def, wf.version)
    if list(wf.path) != list(reg["path"]):
        raise MalformedWorkflow(
            f"{wf.node_class}@{wf.version} string path {list(wf.path)} does not conform to the "
            f"registered path {reg['path']} — a drifted workflow is not a valid instance")
    return reg


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
    if target == wf.here:
        raise IllegalTransition(f"{target!r} -> {target!r} is a no-op, not a transition")
    legal = legal_targets(wf, class_def=class_def)
    if target not in legal:
        raise IllegalTransition(
            f"{wf.here} -> {target} is illegal for {wf.node_class}@{wf.version} "
            f"(legal from here: {sorted(legal)}) — e.g. a forward skip past a gate summons is refused")


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
    """Render the workflow string with the cursor moved to ``target`` (the new instance state)."""
    idx = wf.path.index(target)
    states = [f"[{s}]" if k == idx else s for k, s in enumerate(wf.path)]
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
        target_idx = wf.path.index(target)
        # THE BUILD GATE: crossing the PROVEME summons forward runs the build_inspector on
        # the component at this crossing's address; a red refuses BEFORE anything is written
        # (a refused move leaves no partial record). Back-edges retreat ungated.
        gate_note = None
        if wf.here == "PROVEME" and target_idx > wf.cursor:
            gate_note = _build_gate(history_path)
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
            **journal_extra,
        }
        projector.append_entry(history_path, state_path, record)
    return new_str
