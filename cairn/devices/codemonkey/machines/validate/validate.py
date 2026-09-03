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

from cairn.machines.build_inspector.inspector import judge_validate, VALIDATE_ROSTER
from cairn.devices.codemonkey.machines.hypothesize.hypothesize import _read_triage_berth
from cairn.tools.gate import gate
from cairn.tools.chain.grammar import (CAIRN_ROOT, INSTANCE_DIR, STRATA, ticket_claim_error, common_shape_record, inspected, lacks_of, render_lacks, CHAIN_REMEDY, identity_lack)
from cairn.tools.tree.tree import deposit_learning

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
            "from the conversation" % (path,) + CHAIN_REMEDY)
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
            "validated stages only" % (path,) + CHAIN_REMEDY)
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


JUDGE_REFUSAL_VALIDATE = (
    "validate packet refused by the installed judges (the door and the promotion gate are one implementation): ")


def inspect_validate(packet: dict, root: str = CAIRN_ROOT) -> list:
    """VALIDATE'S OWN INSPECTOR — the proof record for the packet it hands the next stage.

    Every question this stage asks, EXPECTED beside ACTUAL, passes included. Akien,
    2026-08-13, ruling every-machine-carries-its-own-inspector-and-gate: "passing such a
    thing without inspecting it means passing a mystery if something downstream fails …
    we can backtrack and see exactly where something went awry even if it's not something
    we're specifically looking for yet." The entries that PASSED are exactly the ones
    nobody was looking for, which is what a record buys and a complaint list cannot.

    Takes no verdict — that is ``validate_validate``'s, at this same address, because the
    refusal belongs to the stage that would have handed the packet on.

    A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED. The upstream-link entries appear only
    when the packet carries a hypothesize_ref, and the judges only once shape holds (a judge
    reads fields whose shape is not yet established). Either way the record is SHORTER
    and the gate is already closed by the entry that did run — visible as a shorter
    list, never a cleaner one.
    """
    record = []
    if "hypothesize_ref" in packet:
        try:
            _ref_doc = _read_hypothesize_berth(packet["hypothesize_ref"])
        except RuntimeError as e:
            record.append(inspected(
                "upstream_berth_is_readable", stage="validate",
                expected="readable", actual="unreadable", lack=str(e)))
        else:
            record.append(inspected(
                "upstream_berth_is_readable", stage="validate",
                expected="readable", actual="readable", lack=""))
            _mismatch = identity_lack(packet, _ref_doc, "hypothesize_ref")
            record.append(inspected(
                "request_identity_rides_the_chain", stage="validate",
                expected="consistent",
                actual="consistent" if not _mismatch else "broken",
                lack=_mismatch or ""))

    record += common_shape_record(packet, required_fields=REQUIRED_FIELDS,
                                  authored_fields=AUTHORED_FIELDS,
                                  list_fields=('criteria', 'unknowns'),
                                  root=root, stage="validate")

    # THE COMPOSED JUDGES, and they run only once every entry above passes — the same
    # order the two-tier door has always used, now visible in the record rather than
    # implied by control flow. judge_validate is the build inspector's, so a packet this
    # door passes is a packet the promotion gate passes: one implementation, two mouths.
    if all(gate.passed(e) for e in record):
        attendance = judge_validate(packet)
        all_findings = [f for a in attendance for f in a["findings"]]
        record.append(inspected(
            "judges_all_passed", stage="validate",
            expected=sorted(VALIDATE_ROSTER),
            actual=sorted(a["judge"] for a in attendance if not a["findings"]),
            lack=JUDGE_REFUSAL_VALIDATE + "; ".join(
                "[%s] %s" % (f["judge"], f["finding"]) for f in all_findings),
            attendance=attendance))
    return record


def validate_validate(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """VALIDATE'S OWN GATE at the handoff — an == compare over ``inspect_validate``'s record.

    Opens only when every entry's expected equals its actual, per entry, no oracle
    anywhere near it (ruling a-gate-opens-on-an-equality-compare-and-never-on-an-oracle).

    TWO REFUSAL SENTENCES, ONE RECORD AND ONE VERDICT. Shape lacks are rendered together
    (ticket chart-doors-refuse-in-one-pass — a dribbled refusal costs the sender a
    round-trip per field); a judge finding is rendered in the judges' own voice, because
    it tells the sender something different from a malformed field. Both are DERIVED from
    the record's mismatches, so the gate and the sentence cannot disagree about what
    failed.
    The doubled name is the honest mirror of every stage's validate_<stage> door — consistency over euphony.
    """
    if not isinstance(packet, dict):
        # Before the record exists, because there is nothing to inspect: a non-dict cannot
        # be asked a single one of the questions above. Loud, and terminal.
        raise ValidateRefused("validate packet must be a dict, got %s"
                    % type(packet).__name__)

    record = inspect_validate(packet, root=root)
    if gate.verdict(record)["opens"]:
        return packet

    shape = [e for e in record if e["identity"] != "judges_all_passed"]
    if not gate.verdict(shape)["opens"]:
        raise ValidateRefused(render_lacks("validate", lacks_of(shape)))
    raise ValidateRefused(lacks_of(record)[0])


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
