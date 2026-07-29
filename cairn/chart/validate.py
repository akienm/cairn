"""validate — stage 7 of the /chart chain, the stone plan's LAST stage: what
does DONE mean for this request, measured?

The sixth stackable learning brick built UNDER pre-installed judges (ticket
validate-filters PROVED before this module existed). The berth door COMPOSES
judge_validate (imports it from the inspector; the inspector never imports
back), so the module structurally cannot shape its own acceptance.

One narrow question: what must the WHOLE demonstrate at acceptance? Not what
the pieces are (decompose), their order (triage), or what each will do
(hypothesize) — the request's done, as instruments. The founding failure is
the sharpest correction on record: 2026-07-24 done-while-unmoved — DONE was
reported from a proxy while the real files stood unmoved; the instrument was
never run. So every CRITERION:

  - carries its claim and its NAMED INSTRUMENT (done is verified in the world
    by the instrument, never the narration)
  - carries COVERS — the pieces it closes, verbatim from the hypothesize
    berth's claimed pieces; the union of covers exhausts that set (the
    unvalidated piece is the 2026-07-24 piece)
  - may COMPOSE a hypothesis's instrument rather than invent a parallel one
    (Law 1 at the claim level).

The coverage vocabulary composes the PREVIOUS gate's invariant: a berthed
hypothesize covering equals the ranked set (hypothesize-filters enforced it),
so the claimed pieces ARE the build's pieces — each gate stands on the gate
below, the same move as the chain readers composing by identity.

Three strata, cheapest first:

  FLOOR   (this file) — deterministic: from the BERTHED hypothesize packet
          (the chain deepens to depth 7 — validate -> hypothesize -> triage ->
          decompose -> survey -> constrain -> orient — re-checked whole by
          COMPOSING hypothesize's own chain reader), hand the ceiling the
          intent, the bounds, the hypotheses verbatim (whose instruments the
          criteria may compose), the order, and the ACCEPTANCE VOCABULARY the
          judges will enforce (claimed_pieces — the exact set covers must
          exhaust).
  TREE    — the validate brick's own corpus (nexus 'validate', owner 'chart')
          through the generalized verbs; free since chart-tree.
  CEILING (the /chart skill, stage 7) — the acceptance judgment itself,
          assembled with per-field provenance.

The exit artifact berths beside the others (validate-<stamp>-<digest>.json in
instance-space) and the deposit-back lands the criteria as the tree's memory
of what done means for this class of request.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

from cairn.build_inspector.inspector import judge_validate
from cairn.chart.hypothesize import _read_triage_berth
from cairn.chart.orient import (CAIRN_ROOT, INSTANCE_DIR, STRATA,
                                ticket_claim_error)
from cairn.chart.tree import deposit_learning

AUTHORED_FIELDS = ("hypothesize_ref", "criteria", "unknowns")
REQUIRED_FIELDS = AUTHORED_FIELDS + ("confidence", "provenance")


class ValidateRefused(RuntimeError):
    """The loud refusal — a packet or ask this brick cannot honestly serve."""


def _read_hypothesize_berth(path: str) -> dict:
    """The template-fill linkage at depth 7: validate's input IS a berthed,
    validated hypothesize packet — and the whole chain below it must still
    read. The deeper links are checked by COMPOSING hypothesize's own reader
    (one implementation of 'the chain holds', not a parallel walk); a broken
    link anywhere refuses loudly, never a shallow fill."""
    if not isinstance(path, str) or not os.path.isfile(os.path.expanduser(path)):
        raise ValidateRefused(
            "validate refuses — hypothesize_ref %r is not a berthed packet on "
            "disk; stage 7 template-fills from stage 6's validated file, never "
            "from the conversation" % (path,))
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            packet = json.load(fh)
    except (OSError, ValueError) as e:
        raise ValidateRefused(
            "validate refuses — hypothesize_ref %r cannot be read as a packet (%s: %s)"
            % (path, type(e).__name__, e)) from e
    if not isinstance(packet, dict) or "triage_ref" not in packet \
            or "hypotheses" not in packet or "unknowns" not in packet:
        raise ValidateRefused(
            "validate refuses — hypothesize_ref %r is not a hypothesize berth "
            "(no triage_ref/hypotheses/unknowns); the chain fills from "
            "validated stages only" % (path,))
    try:
        triage_packet = _read_triage_berth(packet["triage_ref"])
    except Exception as e:
        raise ValidateRefused(
            "validate refuses — the chain broke below the hypothesize berth: %s" % e
        ) from e
    packet["_triage"] = triage_packet
    packet["_constrain"] = triage_packet["_constrain"]
    packet["_orient"] = triage_packet["_orient"]
    return packet


def validate_floor(hypothesize_ref: str, root: str = CAIRN_ROOT) -> dict:
    """The deterministic stratum: the chain re-read whole, and the JUDGES'
    ACCEPTANCE VOCABULARY handed to the ceiling verbatim from the hypothesize
    berth — the exact set of claimed pieces the criteria's covers must
    exhaust, with the hypotheses themselves (whose instruments the criteria
    may compose), the order, and the expectations' unknowns. The floor hands
    over exactly the words the gate will check (template-fill as physics); it
    never decides what done means."""
    berth = _read_hypothesize_berth(hypothesize_ref)
    return {
        "stratum": "floor",
        "hypothesize_ref": hypothesize_ref,
        "intent": berth["_orient"]["intent"],
        "bounds": berth["_constrain"]["bounds"],
        "hypotheses": berth["hypotheses"],
        "order": berth["_triage"]["order"],
        "expectation_unknowns": berth["unknowns"],
        "claimed_pieces": sorted(
            {h["piece"] for h in berth["hypotheses"]
             if isinstance(h, dict) and isinstance(h.get("piece"), str)}),
    }


def validate_validate(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """The exit gate: shape first, then THE COMPOSED JUDGES — judge_validate is
    the inspector's, so a packet this door passes is a packet the promotion
    gate passes (one implementation, two mouths). The doubled name is the
    honest mirror of every stage's validate_<stage> door — consistency over
    euphony. Refusals are loud and complete on first pass."""
    if not isinstance(packet, dict):
        raise ValidateRefused("validate packet must be a dict, got %s"
                              % type(packet).__name__)
    missing = [f for f in REQUIRED_FIELDS if f not in packet]
    if missing:
        raise ValidateRefused("validate packet refused — missing fields: %s"
                              % ", ".join(missing))

    _read_hypothesize_berth(packet["hypothesize_ref"])

    for field in ("criteria", "unknowns"):
        if not isinstance(packet[field], list):
            raise ValidateRefused("validate packet refused — %s must be a list"
                                  % field)
    if any(not isinstance(x, str) for x in packet["unknowns"]):
        raise ValidateRefused(
            "validate packet refused — unknowns must be a list of strings")

    confidence = packet["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) \
            or not 0.0 <= float(confidence) <= 1.0:
        raise ValidateRefused(
            "validate packet refused — confidence must be a number in [0, 1]")

    provenance = packet["provenance"]
    if not isinstance(provenance, dict):
        raise ValidateRefused(
            "validate packet refused — provenance must be a dict of field -> stratum")
    uncovered = [f for f in AUTHORED_FIELDS if f not in provenance]
    if uncovered:
        raise ValidateRefused("validate packet refused — provenance does not cover: %s"
                              % ", ".join(uncovered))
    bad = sorted(str(s) for s in set(provenance.values()) if s not in STRATA)
    if bad:
        raise ValidateRefused("validate packet refused — unknown stratum in provenance: %s"
                              % ", ".join(bad))

    claim_error = ticket_claim_error(packet, root)
    if claim_error:
        raise ValidateRefused("validate packet refused — " + claim_error)

    verdicts = judge_validate(packet)
    if verdicts:
        raise ValidateRefused(
            "validate packet refused by the installed judges (the door and the "
            "promotion gate are one implementation): "
            + "; ".join("[%s] %s" % (v["judge"], v["finding"]) for v in verdicts))

    return packet


def write_validate(packet: dict, *, instance_dir: str = INSTANCE_DIR,
                   root: str = CAIRN_ROOT) -> str:
    """The berth: gate at the door (shape + the composed judges), then land in
    instance-space beside the other stages' packets. Returns the path."""
    validate_validate(packet, root=root)
    os.makedirs(instance_dir, exist_ok=True)
    digest = hashlib.sha256(
        json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = os.path.join(instance_dir, "validate-%s-%s.json" % (stamp, digest))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(packet, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def validate_node_content(packet: dict) -> str:
    """The ONE rendering of a validate packet as a tree node's content (the
    upstream intent plus the criteria, instruments visible) — used by the
    deposit and by the live edge to embed the same text it deposits."""
    intent = _read_hypothesize_berth(packet["hypothesize_ref"])["_orient"]["intent"]
    done = "; ".join("%s [by %s]" % (c["claim"], c["instrument"])
                     for c in packet["criteria"]) or "nothing"
    return "%s — DONE MEANS: %s" % (intent, done)


def deposit_validate(packet: dict, vector, *, berth_path: str,
                     root: str = CAIRN_ROOT, conn=None) -> dict:
    """The deposit-back: the criteria become the validate tree's memory of what
    done means for this class of request — the next similar request walks to
    the acceptance shape instead of re-arguing it (Law 1 as the brick's
    runtime). Gate before seed; the berth must exist on disk."""
    validate_validate(packet, root=root)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise ValidateRefused(
            "deposit_validate: berth %r does not exist on disk — a node whose "
            "provenance points at nothing is fabricated attribution one layer up"
            % (berth_path,))
    content = validate_node_content(packet)
    provenance = {
        "source": berth_path,
        "hypothesize_ref": packet["hypothesize_ref"],
        "confidence": packet["confidence"],
    }
    return deposit_learning("validate", content, vector, provenance, conn=conn)
