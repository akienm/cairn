"""triage — stage 5 of the /chart chain: what matters FIRST, by what standard?

The fourth stackable learning brick built UNDER pre-installed judges (ticket
triage-filters PROVED before this module existed). The berth door COMPOSES
judge_triage (imports it from the inspector; the inspector never imports back),
so the module structurally cannot shape its own acceptance.

One narrow question: in what order is the split attacked? Not what the pieces
are (decompose), not what outcome each will have (hypothesize). The founding
failures are ranking-shaped: the 2026-07-24 done-while-unmoved substitution
began as a triage defect (the expensive implied piece silently deprioritized
out of existence), and the standing get-it-right-not-cheap CC-- names the
reflex — ordering by cost-to-me, hidden in an unstated standard. So the ORDER:

  - is a complete permutation of the berthed split's pieces, verbatim by what
    (nothing dropped, invented, or double-ordered — coverage as a multiset;
    descoping is a bounds question for Akien, never a silent drop here)
  - carries its standard per entry: the why_now is forced (the 2026-07-23
    solidify-the-layer-below inversion was adjudicable only because its why
    was stated)
  - IS the rank: position is the only copy of the truth — no numeric priority
    field exists to drift against the list (Law 1).

Three strata, cheapest first:

  FLOOR   (this file) — deterministic: from the BERTHED decompose packet (the
          chain deepens to depth 5 — triage -> decompose -> survey ->
          constrain -> orient — re-checked whole by COMPOSING decompose's own
          chain reader, one implementation rather than a parallel walk), hand
          the ceiling the intent, the bounds, the sub_problems verbatim, the
          split's unknowns, and the COVERAGE VOCABULARY the judges will
          enforce (piece_whats — the exact multiset the order must cover).
  TREE    — the triage brick's own corpus (nexus 'triage', owner 'chart')
          through the generalized verbs; free since chart-tree.
  CEILING (the /chart skill, stage 5) — the ranking judgment itself,
          assembled with per-field provenance.

The exit artifact berths beside the others (triage-<stamp>-<digest>.json in
instance-space) and the deposit-back lands the order as the tree's memory of
how this class of request ranks.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

from cairn.build_inspector.inspector import judge_triage
from cairn.chart.decompose import _read_survey_berth
from cairn.chart.orient import (CAIRN_ROOT, INSTANCE_DIR, STRATA,
                                ticket_claim_error,
                                common_shape_lacks, render_lacks,
                                CHAIN_REMEDY, identity_lack)
from cairn.chart.tree import deposit_learning

AUTHORED_FIELDS = ("decompose_ref", "order", "unknowns")
REQUIRED_FIELDS = AUTHORED_FIELDS + ("confidence", "provenance")


class TriageRefused(RuntimeError):
    """The loud refusal — a packet or ask this brick cannot honestly serve."""


def _read_decompose_berth(path: str) -> dict:
    """The template-fill linkage at depth 5: triage's input IS a berthed,
    validated decompose packet — and the whole chain below it must still read.
    The deeper links are checked by COMPOSING decompose's own reader (one
    implementation of 'the chain holds', not a parallel walk); a broken link
    anywhere refuses loudly, never a shallow fill."""
    if not isinstance(path, str) or not os.path.isfile(os.path.expanduser(path)):
        raise TriageRefused(
            "triage refuses — decompose_ref %r is not a berthed packet on disk; "
            "stage 5 template-fills from stage 4's validated file, never from "
            "the conversation" % (path,) + CHAIN_REMEDY)
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            packet = json.load(fh)
    except (OSError, ValueError) as e:
        raise TriageRefused(
            "triage refuses — decompose_ref %r cannot be read as a packet (%s: %s)"
            % (path, type(e).__name__, e)) from e
    if not isinstance(packet, dict) or "survey_ref" not in packet \
            or "sub_problems" not in packet or "unknowns" not in packet:
        raise TriageRefused(
            "triage refuses — decompose_ref %r is not a decompose berth (no "
            "survey_ref/sub_problems/unknowns); the chain fills from validated "
            "stages only" % (path,) + CHAIN_REMEDY)
    try:
        survey_packet = _read_survey_berth(packet["survey_ref"])
    except Exception as e:
        raise TriageRefused(
            "triage refuses — the chain broke below the decompose berth: %s" % e
        ) from e
    packet["_survey"] = survey_packet
    packet["_constrain"] = survey_packet["_constrain"]
    packet["_orient"] = survey_packet["_orient"]
    return packet


def triage_floor(decompose_ref: str, root: str = CAIRN_ROOT) -> dict:
    """The deterministic stratum: the chain re-read whole, and the JUDGES'
    COVERAGE VOCABULARY handed to the ceiling verbatim from the decompose berth
    — the exact multiset of piece whats the order must cover, with the pieces
    themselves (what/why/kind and their evidence) and the split's unknowns.
    The floor hands over exactly the words the gate will check (template-fill
    as physics); it never decides the order."""
    berth = _read_decompose_berth(decompose_ref)
    return {
        "stratum": "floor",
        "decompose_ref": decompose_ref,
        "intent": berth["_orient"]["intent"],
        "bounds": berth["_constrain"]["bounds"],
        "sub_problems": berth["sub_problems"],
        "split_unknowns": berth["unknowns"],
        "piece_whats": sorted(
            sp["what"] for sp in berth["sub_problems"]
            if isinstance(sp, dict) and isinstance(sp.get("what"), str)),
    }


def validate_triage(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """The exit gate, two tiers, each complete in one pass (ticket
    chart-doors-refuse-in-one-pass): every SHAPE lack is accumulated and raised in
    ONE refusal — a dribbled refusal costs the sender a round-trip per field — and
    THE COMPOSED JUDGES (judge_triage is the inspector's, so a packet this door
    passes is a packet the promotion gate passes — one implementation, two mouths)
    already report every finding together once shape holds."""
    if not isinstance(packet, dict):
        raise TriageRefused("triage packet must be a dict, got %s"
                    % type(packet).__name__)

    lacks = []
    if "decompose_ref" in packet:
        try:
            _ref_doc = _read_decompose_berth(packet["decompose_ref"])
        except RuntimeError as e:
            lacks.append(str(e))
        else:
            _mismatch = identity_lack(packet, _ref_doc, "decompose_ref")
            if _mismatch:
                lacks.append(_mismatch)

    lacks += common_shape_lacks(packet, required_fields=REQUIRED_FIELDS,
                                authored_fields=AUTHORED_FIELDS,
                                list_fields=('order', 'unknowns'), root=root)
    if lacks:
        raise TriageRefused(render_lacks("triage", lacks))

    verdicts = judge_triage(packet)
    if verdicts:
        raise TriageRefused(
            "triage packet refused by the installed judges (the door and the "
            "promotion gate are one implementation): "
            + "; ".join("[%s] %s" % (v["judge"], v["finding"]) for v in verdicts))

    return packet


def write_triage(packet: dict, *, instance_dir: str = INSTANCE_DIR,
                 root: str = CAIRN_ROOT) -> str:
    """The berth: gate at the door (shape + the composed judges), then land in
    instance-space beside the other stages' packets. Returns the path."""
    validate_triage(packet, root=root)
    os.makedirs(instance_dir, exist_ok=True)
    digest = hashlib.sha256(
        json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = os.path.join(instance_dir, "triage-%s-%s.json" % (stamp, digest))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(packet, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def triage_node_content(packet: dict) -> str:
    """The ONE rendering of a triage packet as a tree node's content (the
    upstream intent plus the order, positions visible) — used by the deposit
    and by the live edge to embed the same text it deposits."""
    intent = _read_decompose_berth(packet["decompose_ref"])["_orient"]["intent"]
    ranked = "; ".join("%d. %s" % (i + 1, e["what"])
                       for i, e in enumerate(packet["order"])) or "nothing"
    return "%s — ORDER: %s" % (intent, ranked)


def deposit_triage(packet: dict, vector, *, berth_path: str,
                   root: str = CAIRN_ROOT, conn=None) -> dict:
    """The deposit-back: the order becomes the triage tree's memory of how this
    class of request ranks — the next similar request walks to the standard
    instead of re-deriving it (Law 1 as the brick's runtime). Gate before seed;
    the berth must exist on disk."""
    validate_triage(packet, root=root)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise TriageRefused(
            "deposit_triage: berth %r does not exist on disk — a node whose "
            "provenance points at nothing is fabricated attribution one layer up"
            % (berth_path,))
    content = triage_node_content(packet)
    provenance = {
        "source": berth_path,
        "decompose_ref": packet["decompose_ref"],
        "confidence": packet["confidence"],
    }
    return deposit_learning("triage", content, vector, provenance, conn=conn)
