"""hypothesize — stage 6 of the /chart chain: what do we EXPECT, and how would
we know we're wrong?

The fifth stackable learning brick built UNDER pre-installed judges (ticket
hypothesize-filters PROVED before this module existed). The berth door COMPOSES
judge_hypothesize (imports it from the inspector; the inspector never imports
back), so the module structurally cannot shape its own acceptance.

One narrow question: what will each ranked piece DO, stated so the build can
kill the claim? Not what the pieces are (decompose), not their order (triage),
not what done means for the whole (validate). Law 3 verbatim: nothing is known
until measured — an unmeasured claim is a hypothesis and is LABELED as one.
This stage makes the label the packet's shape:

  - every HYPOTHESIS attaches to a ranked piece, verbatim by what (an
    expectation about underived work is invention at the claim stage)
  - every ranked piece carries at least one hypothesis (a COVERING, not a
    permutation — several claims per piece are welcome; a piece with none is
    the piece whose wrong landing reds nothing)
  - every hypothesis carries its expect, its FALSIFIER (the observation that
    would kill it — /sorted's 'no falsifier, not ready' gate moved one stage
    earlier and one rung down), and its INSTRUMENT (the measure that would be
    run, named so the claim can be challenged — '0 of 13' was a claim whose
    instrument was a word-grep and nobody could tell).

Three strata, cheapest first:

  FLOOR   (this file) — deterministic: from the BERTHED triage packet (the
          chain deepens to depth 6 — hypothesize -> triage -> decompose ->
          survey -> constrain -> orient — re-checked whole by COMPOSING
          triage's own chain reader, one implementation rather than a parallel
          walk), hand the ceiling the intent, the bounds, the order verbatim,
          the underlying split pieces (kind and evidence), and the COVERING
          VOCABULARY the judges will enforce (ranked_whats — the exact set the
          hypotheses must cover).
  TREE    — the hypothesize brick's own corpus (nexus 'hypothesize', owner
          'chart') through the generalized verbs; free since chart-tree.
  CEILING (the /chart skill, stage 6) — the expectations themselves, assembled
          with per-field provenance.

The exit artifact berths beside the others (hypothesize-<stamp>-<digest>.json
in instance-space) and the deposit-back lands the claims as the tree's memory
of what this class of request expects — and, one day, of what killed which.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

from cairn.machines.build_inspector.inspector import judge_hypothesize, HYPOTHESIZE_ROSTER
from cairn.tools.gate import gate
from cairn.tools.chain.grammar import (CAIRN_ROOT, INSTANCE_DIR, STRATA, ticket_claim_error, common_shape_record, inspected, lacks_of, render_lacks, CHAIN_REMEDY, identity_lack)
from cairn.tools.tree.tree import deposit_learning
from cairn.devices.codemother.machines.triage.triage import _read_decompose_berth

AUTHORED_FIELDS = ("triage_ref", "hypotheses", "unknowns")
REQUIRED_FIELDS = AUTHORED_FIELDS + ("confidence", "provenance")


class HypothesizeRefused(RuntimeError):
    """The loud refusal — a packet or ask this brick cannot honestly serve."""


def _read_triage_berth(path: str) -> dict:
    """The template-fill linkage at depth 6: hypothesize's input IS a berthed,
    validated triage packet — and the whole chain below it must still read.
    The deeper links are checked by COMPOSING triage's own reader (one
    implementation of 'the chain holds', not a parallel walk); a broken link
    anywhere refuses loudly, never a shallow fill."""
    if not isinstance(path, str) or not os.path.isfile(os.path.expanduser(path)):
        raise HypothesizeRefused(
            "hypothesize refuses — triage_ref %r is not a berthed packet on "
            "disk; stage 6 template-fills from stage 5's validated file, never "
            "from the conversation" % (path,) + CHAIN_REMEDY)
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            packet = json.load(fh)
    except (OSError, ValueError) as e:
        raise HypothesizeRefused(
            "hypothesize refuses — triage_ref %r cannot be read as a packet (%s: %s)"
            % (path, type(e).__name__, e)) from e
    if not isinstance(packet, dict) or "decompose_ref" not in packet \
            or "order" not in packet or "unknowns" not in packet:
        raise HypothesizeRefused(
            "hypothesize refuses — triage_ref %r is not a triage berth (no "
            "decompose_ref/order/unknowns); the chain fills from validated "
            "stages only" % (path,) + CHAIN_REMEDY)
    try:
        decompose_packet = _read_decompose_berth(packet["decompose_ref"])
    except Exception as e:
        raise HypothesizeRefused(
            "hypothesize refuses — the chain broke below the triage berth: %s" % e
        ) from e
    packet["_decompose"] = decompose_packet
    packet["_constrain"] = decompose_packet["_constrain"]
    packet["_orient"] = decompose_packet["_orient"]
    return packet


def hypothesize_floor(triage_ref: str, root: str = CAIRN_ROOT) -> dict:
    """The deterministic stratum: the chain re-read whole, and the JUDGES'
    COVERING VOCABULARY handed to the ceiling verbatim from the triage berth —
    the exact set of ranked whats the hypotheses must cover, with the order
    itself (whats and why_nows), the underlying split pieces (kind and
    evidence), and the ranking's unknowns. The floor hands over exactly the
    words the gate will check (template-fill as physics); it never decides the
    expectations."""
    berth = _read_triage_berth(triage_ref)
    return {
        "stratum": "floor",
        "triage_ref": triage_ref,
        "intent": berth["_orient"]["intent"],
        "bounds": berth["_constrain"]["bounds"],
        "order": berth["order"],
        "sub_problems": berth["_decompose"]["sub_problems"],
        "ranking_unknowns": berth["unknowns"],
        "ranked_whats": sorted(
            {e["what"] for e in berth["order"]
             if isinstance(e, dict) and isinstance(e.get("what"), str)}),
    }


JUDGE_REFUSAL_HYPOTHESIZE = (
    "hypothesize packet refused by the installed judges (the door and the promotion gate are one implementation): ")


def inspect_hypothesize(packet: dict, root: str = CAIRN_ROOT) -> list:
    """HYPOTHESIZE'S OWN INSPECTOR — the proof record for the packet it hands the next stage.

    Every question this stage asks, EXPECTED beside ACTUAL, passes included. Akien,
    2026-08-13, ruling every-machine-carries-its-own-inspector-and-gate: "passing such a
    thing without inspecting it means passing a mystery if something downstream fails …
    we can backtrack and see exactly where something went awry even if it's not something
    we're specifically looking for yet." The entries that PASSED are exactly the ones
    nobody was looking for, which is what a record buys and a complaint list cannot.

    Takes no verdict — that is ``validate_hypothesize``'s, at this same address, because the
    refusal belongs to the stage that would have handed the packet on.

    A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED. The upstream-link entries appear only
    when the packet carries a triage_ref, and the judges only once shape holds (a judge
    reads fields whose shape is not yet established). Either way the record is SHORTER
    and the gate is already closed by the entry that did run — visible as a shorter
    list, never a cleaner one.
    """
    record = []
    if "triage_ref" in packet:
        try:
            _ref_doc = _read_triage_berth(packet["triage_ref"])
        except RuntimeError as e:
            record.append(inspected(
                "upstream_berth_is_readable", stage="hypothesize",
                expected="readable", actual="unreadable", lack=str(e)))
        else:
            record.append(inspected(
                "upstream_berth_is_readable", stage="hypothesize",
                expected="readable", actual="readable", lack=""))
            _mismatch = identity_lack(packet, _ref_doc, "triage_ref")
            record.append(inspected(
                "request_identity_rides_the_chain", stage="hypothesize",
                expected="consistent",
                actual="consistent" if not _mismatch else "broken",
                lack=_mismatch or ""))

    record += common_shape_record(packet, required_fields=REQUIRED_FIELDS,
                                  authored_fields=AUTHORED_FIELDS,
                                  list_fields=('hypotheses', 'unknowns'),
                                  root=root, stage="hypothesize")

    # THE COMPOSED JUDGES, and they run only once every entry above passes — the same
    # order the two-tier door has always used, now visible in the record rather than
    # implied by control flow. judge_hypothesize is the build inspector's, so a packet this
    # door passes is a packet the promotion gate passes: one implementation, two mouths.
    if all(gate.passed(e) for e in record):
        attendance = judge_hypothesize(packet)
        all_findings = [f for a in attendance for f in a["findings"]]
        record.append(inspected(
            "judges_all_passed", stage="hypothesize",
            expected=sorted(HYPOTHESIZE_ROSTER),
            actual=sorted(a["judge"] for a in attendance if not a["findings"]),
            lack=JUDGE_REFUSAL_HYPOTHESIZE + "; ".join(
                "[%s] %s" % (f["judge"], f["finding"]) for f in all_findings),
            attendance=attendance))
    return record


def validate_hypothesize(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """HYPOTHESIZE'S OWN GATE at the handoff — an == compare over ``inspect_hypothesize``'s record.

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
        raise HypothesizeRefused("hypothesize packet must be a dict, got %s"
                    % type(packet).__name__)

    record = inspect_hypothesize(packet, root=root)
    if gate.verdict(record)["opens"]:
        return packet

    shape = [e for e in record if e["identity"] != "judges_all_passed"]
    if not gate.verdict(shape)["opens"]:
        raise HypothesizeRefused(render_lacks("hypothesize", lacks_of(shape)))
    raise HypothesizeRefused(lacks_of(record)[0])


def write_hypothesize(packet: dict, *, instance_dir: str = INSTANCE_DIR,
                      root: str = CAIRN_ROOT) -> str:
    """The berth: gate at the door (shape + the composed judges), then land in
    instance-space beside the other stages' packets. Returns the path."""
    validate_hypothesize(packet, root=root)
    os.makedirs(instance_dir, exist_ok=True)
    digest = hashlib.sha256(
        json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = os.path.join(instance_dir, "hypothesize-%s-%s.json" % (stamp, digest))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(packet, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def hypothesize_node_content(packet: dict) -> str:
    """The ONE rendering of a hypothesize packet as a tree node's content (the
    upstream intent plus the claims, instruments visible) — used by the deposit
    and by the live edge to embed the same text it deposits."""
    intent = _read_triage_berth(packet["triage_ref"])["_orient"]["intent"]
    claims = "; ".join("%s -> %s [by %s]" % (h["piece"], h["expect"], h["instrument"])
                       for h in packet["hypotheses"]) or "nothing"
    return "%s — EXPECT: %s" % (intent, claims)


def deposit_hypothesize(packet: dict, vector, *, berth_path: str,
                        root: str = CAIRN_ROOT, conn=None) -> dict:
    """The deposit-back: the claims become the hypothesize tree's memory of
    what this class of request expects — the next similar request walks to the
    prior claims (and, one day, to what killed which) instead of re-deriving
    them (Law 1 as the brick's runtime). Gate before seed; the berth must exist
    on disk."""
    validate_hypothesize(packet, root=root)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise HypothesizeRefused(
            "deposit_hypothesize: berth %r does not exist on disk — a node "
            "whose provenance points at nothing is fabricated attribution one "
            "layer up" % (berth_path,))
    content = hypothesize_node_content(packet)
    provenance = {
        "source": berth_path,
        "triage_ref": packet["triage_ref"],
        "confidence": packet["confidence"],
    }
    return deposit_learning("hypothesize", content, vector, provenance, conn=conn)
