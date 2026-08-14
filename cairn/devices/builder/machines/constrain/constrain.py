"""constrain — stage 2 of the /chart chain: what BOUNDS this request?

The first stackable learning brick (Akien's ratified name, 2026-07-28 — formerly
question nexus) built UNDER pre-installed judges: constraint_traces and
constraint_bounds_complete were installed and PROVED in the build_inspector BEFORE
this module existed (ticket constrain-filters — 'a higher order build the test
first'), and this module's berth door COMPOSES them (imports judge_constrain; the
inspector never imports back). The module structurally cannot shape its own
acceptance criteria — the judge lives behind another component's write-gate.

One narrow question: what bounds this request? Not what to build, not how — later
stages. The founding failure is constrain-shaped: the web-server carrier miss
(CC-- 2026-07-28) was bounds-checking that never ran to completion.

Three strata, cheapest first:

  FLOOR   (this file) — deterministic: from the BERTHED orient packet (the
          template-fill linkage — stage 2's input is stage 1's validated file,
          never the conversation), surface each ref'd component's charter
          falsifier / gates / owner VERBATIM with its address. The constraints
          most often violated are exactly falsifiers, gates, and ownership. The
          floor surfaces text; it never decides what applies — a paraphrased
          constraint is a constraint with laundered provenance.
  TREE    — the constrain brick's own corpus (nexus 'constrain', owner 'chart')
          through the generalized verbs; free since chart-tree.
  CEILING (the /chart skill, stage 2) — assembles constraints[] (text + a source
          that resolves + kind), bounds {in, out} both non-empty, unknowns,
          confidence, per-field provenance.

The exit artifact berths beside orient's (constrain-<stamp>-<digest>.json in
instance-space) and the deposit-back lands the bounds as the tree's memory of
this class of request. `kind` stays an open string at the gate (law | charter |
ticket | memory | ruling observed, not frozen — the reify-vs-flow caution).
"""
from __future__ import annotations

import hashlib
import json
import os
import time

from cairn.machines.build_inspector.inspector import judge_constrain
# Admitted 2026-08-13 by the rung reorganisation: a component's rung is looked up, not
# spelled. The leaf imports pathlib and nothing else (measured), so this buys the one
# owner of class-space addressing without widening what actually enters.
from cairn.tools.base import address
from cairn.tools.gate import gate
from cairn.tools.chain.grammar import (CAIRN_ROOT, INSTANCE_DIR, STRATA, component_roster, ticket_claim_error, common_shape_record, inspected, lacks_of, render_lacks, CHAIN_REMEDY, identity_lack)
from cairn.tools.tree.tree import deposit_learning

AUTHORED_FIELDS = ("intent_ref", "constraints", "bounds", "unknowns")
REQUIRED_FIELDS = AUTHORED_FIELDS + ("confidence", "provenance")


class ConstrainRefused(RuntimeError):
    """The loud refusal — a packet or ask this brick cannot honestly serve."""


def _read_orient_berth(path: str) -> dict:
    """The template-fill linkage: constrain's input IS a berthed, validated orient
    packet. A missing or unreadable berth refuses — stage 2 without stage 1 is the
    step-skipping this chain exists to make a build error."""
    if not isinstance(path, str) or not os.path.isfile(os.path.expanduser(path)):
        raise ConstrainRefused(
            "constrain refuses — intent_ref %r is not a berthed packet on disk; "
            "stage 2 template-fills from stage 1's validated file, never from "
            "the conversation" % (path,) + CHAIN_REMEDY)
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            packet = json.load(fh)
    except (OSError, ValueError) as e:
        raise ConstrainRefused(
            "constrain refuses — intent_ref %r cannot be read as a packet (%s: %s)"
            % (path, type(e).__name__, e)) from e
    if not isinstance(packet, dict) or "intent" not in packet:
        raise ConstrainRefused(
            "constrain refuses — intent_ref %r is not an orient berth (no intent "
            "field); the chain fills from validated stages only" % (path,) + CHAIN_REMEDY)
    return packet


def constrain_floor(intent_ref: str, root: str = CAIRN_ROOT) -> dict:
    """The deterministic stratum: the charter text that already bounds the ref'd
    components — falsifier, gates, owner — VERBATIM, each with its address.
    Reports WHAT EXISTS; the ceiling decides what applies."""
    orient_packet = _read_orient_berth(intent_ref)
    roster = set(component_roster(root))
    charter_constraints, refs_not_components = [], []
    for ref in orient_packet.get("refs", []):
        if ref not in roster:
            refs_not_components.append(ref)
            continue
        # The ref is a component NAME; its rung is looked up, never concatenated in
        # (address.component_dir, 2026-08-13). The roster above already said this ref is a
        # component, so a None here would be the two readers disagreeing — reported as an
        # unreadable charter with its address, which is what this loop does with every
        # other way the read can fail.
        # AMBIGUITY IS REPORTED, NEVER RESOLVED HERE. A name two rungs answer to
        # (orient, since the chart decomposition) has no single charter, and picking
        # one would put a charter under a component name that only half means it. It
        # rides out in the same shape as every other way the read can fail.
        try:
            comp_dir = address.component_dir(ref, os.path.join(root, "cairn"))
        except address.AmbiguousComponent as e:
            charter_constraints.append({
                "component": ref, "charter": None, "unreadable": str(e)})
            continue
        charter_path = str(comp_dir / "intention+why.json") if comp_dir else \
            os.path.join(root, "cairn", "<no rung holds %s>" % ref, "intention+why.json")
        try:
            with open(charter_path, encoding="utf-8") as fh:
                charter = json.load(fh)
        except (OSError, ValueError) as e:
            charter_constraints.append({
                "component": ref, "charter": charter_path,
                "unreadable": "%s: %s" % (type(e).__name__, e)})
            continue
        charter_constraints.append({
            "component": ref,
            "charter": charter_path,
            "falsifier": charter.get("falsifier"),
            "gates": charter.get("gates"),
            "owner": charter.get("owner"),
        })
    return {
        "stratum": "floor",
        "intent_ref": intent_ref,
        "intent": orient_packet["intent"],
        "charter_constraints": charter_constraints,
        "refs_not_components": refs_not_components,
        "laws_note": "CLAUDE.md's Laws bound every request; surfacing them as "
                     "parsed constraints waits for a checkable shape (ticket "
                     "chart-constrain, filed edge (a))",
    }


JUDGE_REFUSAL_CONSTRAIN = (
    "constrain packet refused by the installed judges (the door and the promotion gate "
    "are one implementation): ")


def inspect_constrain(packet: dict, root: str = CAIRN_ROOT) -> list:
    """CONSTRAIN'S OWN INSPECTOR — the proof record for the packet it hands the next stage.

    Every question this stage asks, EXPECTED beside ACTUAL, passes included. Akien,
    2026-08-13, ruling every-machine-carries-its-own-inspector-and-gate: "passing such a
    thing without inspecting it means passing a mystery if something downstream fails …
    we can backtrack and see exactly where something went awry even if it's not something
    we're specifically looking for yet." The entries that PASSED are exactly the ones
    nobody was looking for, which is what a record buys and a complaint list cannot.

    Takes no verdict — that is ``validate_constrain``'s, at this same address, because
    the refusal belongs to the stage that would have handed the packet on.

    A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED. The upstream-link entries appear only
    when the packet carries an intent_ref, the per-constraint entry only when there are
    constraints to walk, and the judges only once shape holds (a judge reads fields whose
    shape is not yet established). Either way the record is SHORTER and the gate is
    already closed by the entry that did run — visible as a shorter list, never a cleaner
    one.
    """
    record = []
    if "intent_ref" in packet:
        try:
            _ref_doc = _read_orient_berth(packet["intent_ref"])
        except RuntimeError as e:
            record.append(inspected(
                "upstream_berth_is_readable", stage="constrain",
                expected="readable", actual="unreadable", lack=str(e)))
        else:
            record.append(inspected(
                "upstream_berth_is_readable", stage="constrain",
                expected="readable", actual="readable", lack=""))
            _mismatch = identity_lack(packet, _ref_doc, "intent_ref")
            record.append(inspected(
                "request_identity_rides_the_chain", stage="constrain",
                expected="consistent",
                actual="consistent" if not _mismatch else "broken",
                lack=_mismatch or ""))

    if "constraints" in packet:
        constraints = packet["constraints"]
        bounded = isinstance(constraints, list) and bool(constraints)
        record.append(inspected(
            "bounds_question_ran", stage="constrain",
            expected="a non-empty list of constraints",
            actual=("a non-empty list of constraints" if bounded
                    else "%s of %d" % (type(constraints).__name__, len(constraints)
                                       if isinstance(constraints, list) else 0)),
            lack="constraints must be a non-empty list: every Cairn request is bounded "
                 "by at least one charter or Law; an empty list means the bounds "
                 "question never ran"))
        if bounded:
            def _whole(c):
                return isinstance(c, dict) and all(
                    isinstance(c.get(k), str) and c.get(k).strip()
                    for k in ("text", "source", "kind"))
            partial = [i for i, c in enumerate(constraints) if not _whole(c)]
            record.append(inspected(
                "every_constraint_carries_text_source_kind", stage="constrain",
                expected=[], actual=partial, constraints_checked=len(constraints),
                lack="; ".join("constraint %d must carry non-empty text, source, "
                               "and kind" % i for i in partial)))

    record += common_shape_record(packet, required_fields=REQUIRED_FIELDS,
                                  authored_fields=AUTHORED_FIELDS,
                                  list_fields=(), root=root, stage="constrain")

    # THE COMPOSED JUDGES, and they run only once every entry above passes — the same
    # order the two-tier door has always used, now visible in the record rather than
    # implied by control flow. judge_constrain is the build inspector's, so a packet this
    # door passes is a packet the promotion gate passes: one implementation, two mouths.
    if all(gate.passed(e) for e in record):
        verdicts = judge_constrain(packet)
        record.append(inspected(
            "installed_judges_find_nothing", stage="constrain",
            expected=[], actual=sorted({v["judge"] for v in verdicts}),
            lack=JUDGE_REFUSAL_CONSTRAIN + "; ".join(
                "[%s] %s" % (v["judge"], v["finding"]) for v in verdicts),
            findings=verdicts))
    return record


def validate_constrain(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """CONSTRAIN'S OWN GATE at the handoff — an == compare over ``inspect_constrain``.

    Opens only when every entry's expected equals its actual, per entry, no oracle
    anywhere near it (ruling a-gate-opens-on-an-equality-compare-and-never-on-an-oracle).

    TWO REFUSAL SENTENCES, ONE RECORD AND ONE VERDICT. Shape lacks are rendered together
    (ticket chart-doors-refuse-in-one-pass — a dribbled refusal costs the sender a
    round-trip per field); a judge finding is rendered in the judges' own voice, because
    it tells the sender something different from a malformed field. Both are DERIVED from
    the record's mismatches, so the gate and the sentence cannot disagree about what
    failed.
    """
    if not isinstance(packet, dict):
        # Before the record exists, because there is nothing to inspect: a non-dict cannot
        # be asked a single one of the questions above. Loud, and terminal.
        raise ConstrainRefused("constrain packet must be a dict, got %s"
                    % type(packet).__name__)

    record = inspect_constrain(packet, root=root)
    if gate.verdict(record)["opens"]:
        return packet

    shape = [e for e in record if e["identity"] != "installed_judges_find_nothing"]
    if not gate.verdict(shape)["opens"]:
        raise ConstrainRefused(render_lacks("constrain", lacks_of(shape)))
    raise ConstrainRefused(lacks_of(record)[0])


def write_constrain(packet: dict, *, instance_dir: str = INSTANCE_DIR,
                    root: str = CAIRN_ROOT) -> str:
    """The berth: gate at the door (shape + the composed judges), then land in
    instance-space beside orient's packets. Returns the path."""
    validate_constrain(packet, root=root)
    os.makedirs(instance_dir, exist_ok=True)
    digest = hashlib.sha256(
        json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = os.path.join(instance_dir, "constrain-%s-%s.json" % (stamp, digest))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(packet, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def constrain_node_content(packet: dict) -> str:
    """The ONE rendering of a constrain packet as a tree node's content (the
    upstream intent plus the bounds) — used by the deposit and by the live edge
    to embed the same text it deposits; two renderings would make the vector and
    the content drift."""
    intent = _read_orient_berth(packet["intent_ref"])["intent"]
    bounds = packet["bounds"]
    return "%s — IN: %s | OUT: %s" % (
        intent, "; ".join(bounds["in"]), "; ".join(bounds["out"]))


def deposit_constrain(packet: dict, vector, *, berth_path: str, root: str = CAIRN_ROOT,
                      conn=None) -> dict:
    """The deposit-back: the bounds become the constrain tree's memory of this
    class of request — the next similar request walks to its settled bounds
    instead of re-deriving them (Law 1 as the brick's runtime). Gate before seed;
    the berth must exist on disk."""
    validate_constrain(packet, root=root)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise ConstrainRefused(
            "deposit_constrain: berth %r does not exist on disk — a node whose "
            "provenance points at nothing is fabricated attribution one layer up" % (berth_path,))
    content = constrain_node_content(packet)
    provenance = {
        "source": berth_path,
        "intent_ref": packet["intent_ref"],
        "confidence": packet["confidence"],
    }
    return deposit_learning("constrain", content, vector, provenance, conn=conn)
