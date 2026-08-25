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

from cairn.machines.build_inspector.inspector import judge_decompose, DECOMPOSE_ROSTER
from cairn.tools.gate import gate
from cairn.tools.chain.grammar import (CAIRN_ROOT, INSTANCE_DIR, STRATA, ticket_claim_error, common_shape_record, inspected, lacks_of, render_lacks, CHAIN_REMEDY, identity_lack)
from cairn.devices.builder.machines.survey.survey import _read_constrain_berth
from cairn.tools.tree.tree import deposit_learning

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


JUDGE_REFUSAL_DECOMPOSE = (
    "decompose packet refused by the installed judges (the door and the promotion gate are one implementation): ")


def writes_to_lacks(sub_problems, root: str = CAIRN_ROOT) -> list:
    """The lacks in the pieces' ``writes_to`` — where each piece's output LANDS.

    ``uses`` cannot carry this, by construction: it names survey HOLDINGS, things the
    sweep FOUND, and a build piece's whole job is to create what a measured absence says
    is missing — so its target is excluded from ``uses`` by definition. Measured at the
    first live drive of aider-builds-a-piece (ticket
    a-piece-names-where-its-output-lands): the brief handed the apprentice the file the
    piece READS, and nothing berthed said where the new code went.

    THE HARD REQUIREMENT LIVES AT THIS DOOR AND NOWHERE ELSE. A decompose packet has two
    mouths: this one judges only the packet being written, while ``judge_decompose`` is
    also the PROMOTION mouth and reads the standing corpus through ``_charted_packets``.
    A hard requirement there would red 51 healthy berths whose ``writes_to`` was never
    asked for — Law 9's bound read the other way, and the build_inspector's own tooth 1
    ("a healthy component draws a finding — a gate that always fires gets unwired"). The
    asymmetry is deliberate and has precedent at ``survey_holdings_resolve``.

    EXISTENCE IS NOT CHECKED, and that is the point rather than an omission: a build
    piece names a file that does not exist YET. What is checked is that the address is a
    string, non-empty, and IN-REPO — because the only reader downstream hands it to an
    apprentice as an editable path, and an address outside the repo is a write this
    system does not gate (Law 6).

    Returns one sentence per offending piece, in packet order; empty when every piece
    names where it writes.
    """
    lacks = []
    for i, sp in enumerate(sub_problems):
        if not isinstance(sp, dict):
            continue  # shape of the piece itself is the judges' question, not this one
        where = "sub_problem %d (%s)" % (i, str(sp.get("what", "?"))[:60])
        addrs = sp.get("writes_to")
        if not isinstance(addrs, list) or not addrs:
            lacks.append("%s has no non-empty `writes_to` — name the address(es) this "
                         "piece's output lands at, existing or not" % where)
            continue
        for addr in addrs:
            if not isinstance(addr, str) or not addr.strip():
                lacks.append("%s: `writes_to` entry %r is not a non-empty string"
                             % (where, addr))
                continue
            resolved = os.path.normpath(os.path.join(root, addr))
            if not (resolved == root or resolved.startswith(root + os.sep)):
                lacks.append("%s: `writes_to` %s is outside the cairn repo — a piece may "
                             "only declare output this system gates writes to" % (where, addr))
    return lacks


def inspect_decompose(packet: dict, root: str = CAIRN_ROOT) -> list:
    """DECOMPOSE'S OWN INSPECTOR — the proof record for the packet it hands the next stage.

    Every question this stage asks, EXPECTED beside ACTUAL, passes included. Akien,
    2026-08-13, ruling every-machine-carries-its-own-inspector-and-gate: "passing such a
    thing without inspecting it means passing a mystery if something downstream fails …
    we can backtrack and see exactly where something went awry even if it's not something
    we're specifically looking for yet." The entries that PASSED are exactly the ones
    nobody was looking for, which is what a record buys and a complaint list cannot.

    Takes no verdict — that is ``validate_decompose``'s, at this same address, because the
    refusal belongs to the stage that would have handed the packet on.

    A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED. The upstream-link entries appear only
    when the packet carries a survey_ref, and the judges only once shape holds (a judge
    reads fields whose shape is not yet established). Either way the record is SHORTER
    and the gate is already closed by the entry that did run — visible as a shorter
    list, never a cleaner one.
    """
    record = []
    if "survey_ref" in packet:
        try:
            _ref_doc = _read_survey_berth(packet["survey_ref"])
        except RuntimeError as e:
            record.append(inspected(
                "upstream_berth_is_readable", stage="decompose",
                expected="readable", actual="unreadable", lack=str(e)))
        else:
            record.append(inspected(
                "upstream_berth_is_readable", stage="decompose",
                expected="readable", actual="readable", lack=""))
            _mismatch = identity_lack(packet, _ref_doc, "survey_ref")
            record.append(inspected(
                "request_identity_rides_the_chain", stage="decompose",
                expected="consistent",
                actual="consistent" if not _mismatch else "broken",
                lack=_mismatch or ""))

    record += common_shape_record(packet, required_fields=REQUIRED_FIELDS,
                                  authored_fields=AUTHORED_FIELDS,
                                  list_fields=('sub_problems', 'unknowns'),
                                  root=root, stage="decompose")

    # THE OUTPUT ADDRESS, and it is THIS mouth's alone. See ``writes_to_lacks`` for why the
    # hard requirement lives at the door and never in the promotion judge.
    if isinstance(packet.get("sub_problems"), list) and packet["sub_problems"]:
        _lacks = writes_to_lacks(packet["sub_problems"], root=root)
        record.append(inspected(
            "every_piece_names_where_it_writes", stage="decompose",
            expected=[], actual=_lacks,
            lack="; ".join(_lacks)))

    # THE COMPOSED JUDGES, and they run only once every entry above passes — the same
    # order the two-tier door has always used, now visible in the record rather than
    # implied by control flow. judge_decompose is the build inspector's, so a packet this
    # door passes is a packet the promotion gate passes: one implementation, two mouths.
    if all(gate.passed(e) for e in record):
        attendance = judge_decompose(packet)
        all_findings = [f for a in attendance for f in a["findings"]]
        record.append(inspected(
            "judges_all_passed", stage="decompose",
            expected=sorted(DECOMPOSE_ROSTER),
            actual=sorted(a["judge"] for a in attendance if not a["findings"]),
            lack=JUDGE_REFUSAL_DECOMPOSE + "; ".join(
                "[%s] %s" % (f["judge"], f["finding"]) for f in all_findings),
            attendance=attendance))
    return record


def validate_decompose(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """DECOMPOSE'S OWN GATE at the handoff — an == compare over ``inspect_decompose``'s record.

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
        raise DecomposeRefused("decompose packet must be a dict, got %s"
                    % type(packet).__name__)

    record = inspect_decompose(packet, root=root)
    if gate.verdict(record)["opens"]:
        return packet

    shape = [e for e in record if e["identity"] != "judges_all_passed"]
    if not gate.verdict(shape)["opens"]:
        raise DecomposeRefused(render_lacks("decompose", lacks_of(shape)))
    raise DecomposeRefused(lacks_of(record)[0])


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
