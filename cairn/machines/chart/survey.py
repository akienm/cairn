"""survey — stage 3 of the /chart chain: what already EXISTS that bears on this?

The second stackable learning brick built UNDER pre-installed judges — the
judges-before-the-judged move's second instance, the one that turns it from
pattern-candidate into proven pattern (constrain-filters filed edge (b); ticket
survey-filters PROVED before this module existed). The berth door COMPOSES
judge_survey (imports it from the inspector; the inspector never imports back),
so the module structurally cannot shape its own acceptance criteria.

One narrow question: what does the territory already hold? Not what is asked
(orient), not what bounds it (constrain), not how to split it (decompose). The
founding failures are survey-shaped: stone 1's parallel roster (2026-07-28 — the
sweep that never ran, so a settled component got rebuilt) and 'logging: 0 of 13'
(2026-07-27 — an absence claimed from a word-grep). So the packet records the
sweep itself: SOUGHT (where the light was pointed), HOLDINGS (found, each with an
address the gate re-checks), ABSENCES (not found, each with the measure that
established it — an absence is a claim).

Three strata, cheapest first:

  FLOOR   (this file) — deterministic: from the BERTHED constrain packet (the
          chain deepens — survey's input is stage 2's validated file, whose own
          intent_ref must still resolve; a broken link anywhere refuses), surface
          each ref'd component's device_census ROW VERBATIM. Survey's question is
          MEASURED state (proofs, validations, devices, emit sites) — constrain
          already surfaced the authored charter text; re-reading charters here
          would be the parallel-scan drift. Non-component refs are existence-
          measured. The floor reports what exists; it never decides relevance.
  TREE    — the survey brick's own corpus (nexus 'survey', owner 'chart')
          through the generalized verbs; free since chart-tree.
  CEILING (the /chart skill, stage 3) — the wide sweep that earns its keep
          (charter falsifier 7: parsimony must not squeeze it), assembling
          sought / holdings / absences / unknowns, confidence, per-field
          provenance. Loose process, tight output.

The exit artifact berths beside the others (survey-<stamp>-<digest>.json in
instance-space) and the deposit-back lands the inventory as the tree's memory of
this class of request.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from cairn.machines.build_inspector.inspector import judge_survey
from cairn.machines.chart.orient import (CAIRN_ROOT, INSTANCE_DIR, STRATA,
                                component_roster, ref_exists, ticket_claim_error,
                                common_shape_lacks, render_lacks,
                                CHAIN_REMEDY, identity_lack)
from cairn.machines.chart.tree import deposit_learning
from cairn.tools.orient.orient import device_census

AUTHORED_FIELDS = ("constrain_ref", "sought", "holdings", "absences", "unknowns")
REQUIRED_FIELDS = AUTHORED_FIELDS + ("confidence", "provenance")


class SurveyRefused(RuntimeError):
    """The loud refusal — a packet or ask this brick cannot honestly serve."""


def _read_constrain_berth(path: str) -> dict:
    """The template-fill linkage, one link deeper: survey's input IS a berthed,
    validated constrain packet — and that packet's own intent_ref must still be a
    readable orient berth. A broken link anywhere in the chain refuses; a shallow
    fill over a broken chain would be the step-skipping this chain exists to
    make a build error."""
    if not isinstance(path, str) or not os.path.isfile(os.path.expanduser(path)):
        raise SurveyRefused(
            "survey refuses — constrain_ref %r is not a berthed packet on disk; "
            "stage 3 template-fills from stage 2's validated file, never from "
            "the conversation" % (path,) + CHAIN_REMEDY)
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            packet = json.load(fh)
    except (OSError, ValueError) as e:
        raise SurveyRefused(
            "survey refuses — constrain_ref %r cannot be read as a packet (%s: %s)"
            % (path, type(e).__name__, e)) from e
    if not isinstance(packet, dict) or "bounds" not in packet \
            or "intent_ref" not in packet:
        raise SurveyRefused(
            "survey refuses — constrain_ref %r is not a constrain berth (no "
            "bounds/intent_ref); the chain fills from validated stages only" % (path,) + CHAIN_REMEDY)
    intent_ref = packet["intent_ref"]
    if not isinstance(intent_ref, str) \
            or not os.path.isfile(os.path.expanduser(intent_ref)):
        raise SurveyRefused(
            "survey refuses — the chain broke: constrain berth %r points at "
            "intent_ref %r which is no longer on disk" % (path, intent_ref) + CHAIN_REMEDY)
    try:
        with open(os.path.expanduser(intent_ref), encoding="utf-8") as fh:
            orient_packet = json.load(fh)
    except (OSError, ValueError) as e:
        raise SurveyRefused(
            "survey refuses — the chain broke: orient berth %r unreadable (%s: %s)"
            % (intent_ref, type(e).__name__, e)) from e
    if not isinstance(orient_packet, dict) or "intent" not in orient_packet:
        raise SurveyRefused(
            "survey refuses — the chain broke: %r is not an orient berth" % (intent_ref,) + CHAIN_REMEDY)
    packet["_orient"] = orient_packet
    return packet


def survey_floor(constrain_ref: str, root: str = CAIRN_ROOT) -> dict:
    """The deterministic stratum: the MEASURED state of the ref'd territory —
    each component ref's device_census row VERBATIM (the orient instrument is the
    settled measurer; a parallel scan here is the drift stone 1 bled for), each
    non-component ref existence-measured. Reports WHAT EXISTS; the ceiling
    decides what bears on the request."""
    constrain_packet = _read_constrain_berth(constrain_ref)
    orient_packet = constrain_packet["_orient"]
    census = device_census(root=Path(root) / "cairn")
    rows = {r["component"]: r for r in census["measured"]["components"]}
    roster = set(component_roster(root))
    census_rows, refs_found, refs_missing = [], [], []
    for ref in orient_packet.get("refs", []):
        if ref in roster and ref in rows:
            census_rows.append(rows[ref])
            continue
        # ref_exists is the gate's own resolution semantics (commons fallback
        # included) — the floor's FIRST live fire reported two filed tickets as
        # missing because its first cast checked a narrower world than the gate
        # that admitted the refs: a false absence, this brick's own failure class.
        if ref_exists(ref, root):
            refs_found.append(ref)
        else:
            refs_missing.append(ref)
    return {
        "stratum": "floor",
        "constrain_ref": constrain_ref,
        "intent": orient_packet["intent"],
        "bounds": constrain_packet["bounds"],
        "census_rows": census_rows,
        "refs_found": sorted(set(refs_found)),
        "refs_missing": sorted(set(refs_missing)),
        "roster_size": len(roster),
    }


def validate_survey(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """The exit gate, two tiers, each complete in one pass (ticket
    chart-doors-refuse-in-one-pass): every SHAPE lack is accumulated and raised in
    ONE refusal — a dribbled refusal costs the sender a round-trip per field — and
    THE COMPOSED JUDGES (judge_survey is the inspector's, so a packet this door
    passes is a packet the promotion gate passes — one implementation, two mouths)
    already report every finding together once shape holds."""
    if not isinstance(packet, dict):
        raise SurveyRefused("survey packet must be a dict, got %s"
                    % type(packet).__name__)

    lacks = []
    if "constrain_ref" in packet:
        try:
            _ref_doc = _read_constrain_berth(packet["constrain_ref"])
        except RuntimeError as e:
            lacks.append(str(e))
        else:
            _mismatch = identity_lack(packet, _ref_doc, "constrain_ref")
            if _mismatch:
                lacks.append(_mismatch)

    lacks += common_shape_lacks(packet, required_fields=REQUIRED_FIELDS,
                                authored_fields=AUTHORED_FIELDS,
                                list_fields=('holdings', 'absences', 'unknowns'), root=root)
    if lacks:
        raise SurveyRefused(render_lacks("survey", lacks))

    verdicts = judge_survey(packet)
    if verdicts:
        raise SurveyRefused(
            "survey packet refused by the installed judges (the door and the "
            "promotion gate are one implementation): "
            + "; ".join("[%s] %s" % (v["judge"], v["finding"]) for v in verdicts))

    return packet


def write_survey(packet: dict, *, instance_dir: str = INSTANCE_DIR,
                 root: str = CAIRN_ROOT) -> str:
    """The berth: gate at the door (shape + the composed judges), then land in
    instance-space beside the other stages' packets. Returns the path."""
    validate_survey(packet, root=root)
    os.makedirs(instance_dir, exist_ok=True)
    digest = hashlib.sha256(
        json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = os.path.join(instance_dir, "survey-%s-%s.json" % (stamp, digest))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(packet, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def survey_node_content(packet: dict) -> str:
    """The ONE rendering of a survey packet as a tree node's content (the
    upstream intent plus the inventory) — used by the deposit and by the live
    edge to embed the same text it deposits; two renderings would make the
    vector and the content drift."""
    intent = _read_constrain_berth(packet["constrain_ref"])["_orient"]["intent"]
    have = "; ".join(h["what"] for h in packet["holdings"]) or "nothing"
    absent = "; ".join(a["what"] for a in packet["absences"]) or "nothing"
    return "%s — HOLDS: %s | ABSENT: %s" % (intent, have, absent)


def deposit_survey(packet: dict, vector, *, berth_path: str, root: str = CAIRN_ROOT,
                   conn=None) -> dict:
    """The deposit-back: the inventory becomes the survey tree's memory of this
    class of request — the next similar request walks to what the territory held
    instead of re-sweeping blind (Law 1 as the brick's runtime). Gate before
    seed; the berth must exist on disk."""
    validate_survey(packet, root=root)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise SurveyRefused(
            "deposit_survey: berth %r does not exist on disk — a node whose "
            "provenance points at nothing is fabricated attribution one layer up" % (berth_path,))
    content = survey_node_content(packet)
    provenance = {
        "source": berth_path,
        "constrain_ref": packet["constrain_ref"],
        "confidence": packet["confidence"],
    }
    return deposit_learning("survey", content, vector, provenance, conn=conn)
