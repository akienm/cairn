"""decompose — stage 4 of the /chart chain: how does this request SPLIT?

The third stackable learning brick built UNDER pre-installed judges — the
ordering is routine now (ticket decompose-filters PROVED before this module
existed; the pattern was proven at n=2 by survey-filters). The berth door
COMPOSES judge_decompose (imports it from the inspector; the inspector never
imports back), so the module structurally cannot shape its own acceptance.

One narrow question: how does the work split into pieces? Not what is asked
(orient), not what bounds it (constrain), not what exists (survey). The founding
failures are split-shaped: the 2026-07-24 done-while-unmoved substitution (the
expensive piece the chosen path implied dropped for a cheaper invented one) and
stone 1's parallel roster (a piece built where a holding sat unreferenced). So
every SUB_PROBLEM carries its what, its why, and its KIND — the checkable claim:

  compose — uses addresses the survey berth HOLDS (what exists is composed,
            never re-derived; if a piece needs something the survey does not
            hold, the survey must hold it first — the chain pushes back up)
  build   — fills an absence the survey MEASURED, verbatim (build-minimal as
            physics: only what was measured absent may be built)

Three strata, cheapest first:

  FLOOR   (this file) — deterministic: from the BERTHED survey packet (the
          chain deepens to depth 4 — decompose -> survey -> constrain ->
          orient — re-checked whole by COMPOSING survey's own chain reader,
          one implementation rather than a parallel walk), hand the ceiling
          the intent, the bounds, and the exact COMPOSE/BUILD VOCABULARIES
          the judges will enforce (holding addresses, absence whats).
          Template-fill as physics: the ceiling receives the words the gate
          will check.
  TREE    — the decompose brick's own corpus (nexus 'decompose', owner
          'chart') through the generalized verbs; free since chart-tree.
  CEILING (the /chart skill, stage 4) — the split itself: judgment about
          seams and order of attack, assembled with per-field provenance.

The exit artifact berths beside the others (decompose-<stamp>-<digest>.json in
instance-space) and the deposit-back lands the split as the tree's memory of
how this class of request divides.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

from cairn.machines.build_inspector.inspector import judge_decompose
from cairn.machines.chart.orient import (CAIRN_ROOT, INSTANCE_DIR, STRATA,
                                ticket_claim_error,
                                common_shape_lacks, render_lacks,
                                CHAIN_REMEDY, identity_lack)
from cairn.machines.chart.survey import _read_constrain_berth
from cairn.machines.chart.tree import deposit_learning

AUTHORED_FIELDS = ("survey_ref", "sub_problems", "unknowns")
REQUIRED_FIELDS = AUTHORED_FIELDS + ("confidence", "provenance")


class DecomposeRefused(RuntimeError):
    """The loud refusal — a packet or ask this brick cannot honestly serve."""


def _read_survey_berth(path: str) -> dict:
    """The template-fill linkage at depth 4: decompose's input IS a berthed,
    validated survey packet — and the whole chain below it must still read.
    The deeper links are checked by COMPOSING survey's own reader (one
    implementation of 'the chain holds', not a parallel walk); a broken link
    anywhere refuses loudly, never a shallow fill."""
    if not isinstance(path, str) or not os.path.isfile(os.path.expanduser(path)):
        raise DecomposeRefused(
            "decompose refuses — survey_ref %r is not a berthed packet on disk; "
            "stage 4 template-fills from stage 3's validated file, never from "
            "the conversation" % (path,) + CHAIN_REMEDY)
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            packet = json.load(fh)
    except (OSError, ValueError) as e:
        raise DecomposeRefused(
            "decompose refuses — survey_ref %r cannot be read as a packet (%s: %s)"
            % (path, type(e).__name__, e)) from e
    if not isinstance(packet, dict) or "constrain_ref" not in packet \
            or "holdings" not in packet or "absences" not in packet:
        raise DecomposeRefused(
            "decompose refuses — survey_ref %r is not a survey berth (no "
            "constrain_ref/holdings/absences); the chain fills from validated "
            "stages only" % (path,) + CHAIN_REMEDY)
    try:
        constrain_packet = _read_constrain_berth(packet["constrain_ref"])
    except Exception as e:
        raise DecomposeRefused(
            "decompose refuses — the chain broke below the survey berth: %s" % e
        ) from e
    packet["_constrain"] = constrain_packet
    packet["_orient"] = constrain_packet["_orient"]
    return packet


def decompose_floor(survey_ref: str, root: str = CAIRN_ROOT) -> dict:
    """The deterministic stratum: the chain re-read whole, and the JUDGES'
    VOCABULARIES handed to the ceiling verbatim from the survey berth — the
    holding addresses a compose piece may use, the absence whats a build piece
    may fill. The floor hands over exactly the words the gate will check
    (template-fill as physics); it never decides the split."""
    survey_packet = _read_survey_berth(survey_ref)
    return {
        "stratum": "floor",
        "survey_ref": survey_ref,
        "intent": survey_packet["_orient"]["intent"],
        "bounds": survey_packet["_constrain"]["bounds"],
        "holdings": survey_packet["holdings"],
        "absences": survey_packet["absences"],
        "holding_addresses": sorted(
            {h["address"] for h in survey_packet["holdings"]
             if isinstance(h, dict) and isinstance(h.get("address"), str)}),
        "absence_whats": sorted(
            {a["what"] for a in survey_packet["absences"]
             if isinstance(a, dict) and isinstance(a.get("what"), str)}),
    }


def validate_decompose(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """The exit gate, two tiers, each complete in one pass (ticket
    chart-doors-refuse-in-one-pass): every SHAPE lack is accumulated and raised in
    ONE refusal — a dribbled refusal costs the sender a round-trip per field — and
    THE COMPOSED JUDGES (judge_decompose is the inspector's, so a packet this door
    passes is a packet the promotion gate passes — one implementation, two mouths)
    already report every finding together once shape holds."""
    if not isinstance(packet, dict):
        raise DecomposeRefused("decompose packet must be a dict, got %s"
                    % type(packet).__name__)

    lacks = []
    if "survey_ref" in packet:
        try:
            _ref_doc = _read_survey_berth(packet["survey_ref"])
        except RuntimeError as e:
            lacks.append(str(e))
        else:
            _mismatch = identity_lack(packet, _ref_doc, "survey_ref")
            if _mismatch:
                lacks.append(_mismatch)

    lacks += common_shape_lacks(packet, required_fields=REQUIRED_FIELDS,
                                authored_fields=AUTHORED_FIELDS,
                                list_fields=('sub_problems', 'unknowns'), root=root)
    if lacks:
        raise DecomposeRefused(render_lacks("decompose", lacks))

    verdicts = judge_decompose(packet)
    if verdicts:
        raise DecomposeRefused(
            "decompose packet refused by the installed judges (the door and the "
            "promotion gate are one implementation): "
            + "; ".join("[%s] %s" % (v["judge"], v["finding"]) for v in verdicts))

    return packet


def write_decompose(packet: dict, *, instance_dir: str = INSTANCE_DIR,
                    root: str = CAIRN_ROOT) -> str:
    """The berth: gate at the door (shape + the composed judges), then land in
    instance-space beside the other stages' packets. Returns the path."""
    validate_decompose(packet, root=root)
    os.makedirs(instance_dir, exist_ok=True)
    digest = hashlib.sha256(
        json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = os.path.join(instance_dir, "decompose-%s-%s.json" % (stamp, digest))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(packet, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def decompose_node_content(packet: dict) -> str:
    """The ONE rendering of a decompose packet as a tree node's content (the
    upstream intent plus the split, kinds visible) — used by the deposit and by
    the live edge to embed the same text it deposits."""
    intent = _read_survey_berth(packet["survey_ref"])["_orient"]["intent"]
    pieces = "; ".join("%s: %s" % (sp["kind"], sp["what"])
                       for sp in packet["sub_problems"]) or "nothing"
    return "%s — SPLIT: %s" % (intent, pieces)


def deposit_decompose(packet: dict, vector, *, berth_path: str,
                      root: str = CAIRN_ROOT, conn=None) -> dict:
    """The deposit-back: the split becomes the decompose tree's memory of how
    this class of request divides — the next similar request walks to the seams
    instead of re-deriving them (Law 1 as the brick's runtime). Gate before
    seed; the berth must exist on disk."""
    validate_decompose(packet, root=root)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise DecomposeRefused(
            "deposit_decompose: berth %r does not exist on disk — a node whose "
            "provenance points at nothing is fabricated attribution one layer up"
            % (berth_path,))
    content = decompose_node_content(packet)
    provenance = {
        "source": berth_path,
        "survey_ref": packet["survey_ref"],
        "confidence": packet["confidence"],
    }
    return deposit_learning("decompose", content, vector, provenance, conn=conn)
