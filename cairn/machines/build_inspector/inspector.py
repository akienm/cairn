"""build_inspector — the post-build gate. Python sieves; new failure, new sieve.

Akien's ruling, 2026-07-27, verbatim: "the next thing is a post build inspector (also in
python with SIEVES) that can catch these kinds of things. we find a new thing, we add a
new sieve. can also be a seperate, command line only inference free operation to run it
on the whole repo once built. we should only ever have to do that once."

THE CONTRACT
  - A SIEVE judges a MEASUREMENT — it reads orient's census rows and the component's
    files, never a narration about them. Inference-free by construction: there is no
    deepen seam here at all; a gate that consults an oracle is not a gate.
  - Every sieve carries PROVENANCE: the failure that seeded it (the learning device,
    same shape as orient's scans — proofs refuse a sieve nobody was taught by).
  - A FINDING is complete on first pass (I-complete-diagnostic-on-first-pass): what
    was measured, why it matters, which law — never "run again for details".
  - "ONLY ONCE" BY CONSTRUCTION: the whole-repo sweep brings the existing tree up to
    the gate one time; after that, every build runs the inspector on its component and
    the sweep can never be needed again. Wanting a second sweep IS a finding — it
    means some build bypassed the gate.

CLI (inference-free):
  python3 -m cairn.machines.build_inspector.inspector            # the whole-repo sweep
  python3 -m cairn.machines.build_inspector.inspector <component>  # post-build, one component
Exit 0 = clean, 1 = findings — gate-able by anything that can read an exit code.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# Deliberate reuse, on the record: orient's scans are the measuring layer under these
# sieves (device_census feeds every row-judging sieve). This is the first evidence on
# orient's filed edge (e) — scans-vs-sieves as one shared library — earned by use, not
# merged on symmetry. The registries stay separate: a scan MEASURES, a sieve JUDGES.
from cairn.tools.charter import projector  # noqa: E402
from cairn.machines.chart.orient import (CAIRN_ROOT, ref_exists,  # noqa: E402  (tree-free
                                ticket_path)             #   module — the verdict
#   path stays structurally unable to reach tree machinery; the packet jurisdiction
#   composes the berth gate's OWN ref semantics so the two mouths cannot disagree.
#   ticket_path joined 2026-07-30 (watchme-emits-a-probe's own live fire): the
#   forwarding order lives on the ticket, and WHERE a ticket lives already had one
#   implementation — re-deriving it here would be the Law 1 defect the gate judges.)
from cairn.machines.chart.verdict import claiming_packets, unanswered, verdict_error  # noqa: E402
#   (joined 2026-07-29, ticket proved-answers-the-chart: the exit gate composes the ONE
#   verdict-artifact validator the deposit face also composes — tree-free like
#   chart.orient, pinned transitively by the inspector-nexus allowlist tooth.
#   claiming_packets joined 2026-07-29 (the-deposit-rides-the-read): the
#   latest-claimer rule this gate used to own privately now lives beside the
#   validator, so the gate and the crossing's deposit-enqueue cannot disagree
#   about WHICH artifact answered.
from cairn.tools.orient.orient import ScanRefused, device_census  # noqa: E402
# cairn.tools.import_sieve joined 2026-08-06 (the-questions-are-the-sieve): a sieve's BAND
# is derived from what its own body reaches, never authored — so the nest reads this
# module's source through the same AST primitive that seals the inference/db doors.
# It is tree-free (ast + pathlib + os only) and pinned transitively by the allowlist
# tooth, exactly like chart.orient and chart.verdict.
from cairn.tools.import_sieve import sieve as import_sieve  # noqa: E402
# The ASSEMBLY and the SHAKE ride the general berth since 2026-08-07 (ruling
# the-nest-is-block-general, ticket banding-berths-at-the-general-level): derivation
# is import_sieve's domain, banding is block-general, and this inspector is the
# nest's first TENANT, not its owner.
from cairn.tools.base import nest as base_nest  # noqa: E402


def _finding(sieve_name: str, component: str, finding: str, evidence, why: str,
             score: float = 0.0) -> dict:
    """A finding carries the DATUM and a SCORE — Akien, 2026-08-06: 'each finding can
    have a datum AND a score, because the score is relative to the requirement.'

    ``evidence`` IS the datum, under the name it has carried since the founding sieves;
    minting a second key for the same measured value would be terminology drift, not a
    new field. What is genuinely new is ``score``: the measurement read AGAINST the
    requirement, which the datum alone cannot say. Float, because elapsed time and
    performance values are coming; 1.0/0.0 today because every sieve here is binary
    (his call: 'binary but as a float? and for now it's 1 and 0').

    A finding is emitted only when a sieve CATCHES, so the default is 0.0. Passes carry
    no finding — they appear in the report's gradation, which is where the vector he drew
    ([1.0, 1.0, 0.0, 1.0, 1.0] = 0.0) actually lives.
    """
    return {
        "sieve": sieve_name,
        "component": component,
        "finding": finding,
        "evidence": evidence,          # the datum
        "score": score,                # the datum read against the requirement
        "why_it_matters": why,
    }


# ── the founding sieves — one per failure that seeded it ────────────────────


def charter_on_disk(row: dict, comp_dir: Path) -> list[dict]:
    """A component with code but no intention+why.json beside it.

    Provenance: 2026-07-27 — orient's census's FIRST real run flagged orient itself
    (charter_on_disk: False); the charter got written because the instrument refused
    its absence. 'A component without an intention doesn't run' (CLAUDE.md) was prose
    until this sieve; now a build that skips the charter reds the gate.
    """
    if row["charter_on_disk"]:
        return []
    return [_finding(
        "charter_on_disk", row["component"],
        "component has code but no intention+why.json beside it",
        {"expected": str(comp_dir / "intention+why.json"), "exists": False},
        "Law 5 / CLAUDE.md: intent, voyage and proofs share an address; a component "
        "without an intention doesn't run. The filename forces the why (CP3 as schema).",
    )]


def proofs_exist(row: dict, comp_dir: Path) -> list[dict]:
    """A component with code but zero proofs.

    Provenance: 2026-07-25 — the bus stood 'PROVEN' in its history while the usable
    half was unbuilt (the true-but-silently-partial record). Zero proofs is the loud
    end of that spectrum: nothing entered proven-space at all (Law 8).
    """
    if row["proofs"] > 0:
        return []
    return [_finding(
        "proofs_exist", row["component"],
        "component has code but zero proofs under proofs/",
        {"proofs_found": 0, "looked_in": str(comp_dir / "proofs")},
        "Law 8: nothing enters proven-space without a proof a hollow build couldn't "
        "pass. Code with no proof is a hypothesis parked in class-space.",
    )]


def silent_device(row: dict, comp_dir: Path) -> list[dict]:
    """A BaseDevice subclass whose non-proof code never calls emit().

    Provenance: 2026-07-27 — MAP.md:434 claims every major state transition and every
    boundary crossing is logged ('no device can opt out'); the AST measurement found
    ZERO emit() call sites in bus, the boundary named first. A device that inherits
    emit() and never fires it is silent at every crossing — the system_rackmount
    went-red-silently gap, systemic. Sharpened same day: judges the SELF-scoped count
    (``self.emit`` — receiver checked), after two components passed this sieve on
    emit-homonyms (an audit function; the transitions chokepoint). The word is not
    the capability, even inside the instrument built to say so.
    """
    if not row["device_subclasses"] or row["self_emit_call_sites_outside_proofs"] > 0:
        return []
    return [_finding(
        "silent_device", row["component"],
        "subclasses BaseDevice (inherits emit()) but never calls self.emit() outside proofs",
        {"device_subclasses": row["device_subclasses"], "self_emit_call_sites_outside_proofs": 0},
        "Law 7 + MAP.md:434 ('every crossing logged... no device can opt out'): a "
        "silent device fails invisibly — the exact gap that motivated DiagnosticBase. "
        "This sieve is the enforcement half of that 2026-07-14 claim.",
    )]


def state_is_projection(row: dict, comp_dir: Path) -> list[dict]:
    """state.json must be exactly the projection of history.json — never hand-edited.

    Provenance: CLAUDE.md 'Rules awaiting physics': 'a compiled view is never
    hand-edited... → single write-door + tester drift check'. The write-door exists
    (projector.append_entry, shape-gated 2026-07-25); THIS is the drift check — the
    IOU's other half, now physics at the build gate.
    """
    h, s = comp_dir / "history.json", comp_dir / "state.json"
    if not h.exists() and not s.exists():
        return []  # no voyage yet — nothing to drift
    if h.exists() != s.exists():
        present, absent = (h, s) if h.exists() else (s, h)
        return [_finding(
            "state_is_projection", row["component"],
            f"{present.name} exists without {absent.name} — the pair is the contract",
            {"present": present.name, "absent": absent.name},
            "Law 7 / charter-state-history split: state is a projection of history; "
            "one without the other means a write bypassed the append door.",
        )]
    try:
        on_disk = json.loads(s.read_text())
    except json.JSONDecodeError as e:
        return [_finding(
            "state_is_projection", row["component"],
            "state.json is unreadable JSON",
            {"error": str(e)},
            "Law 7: a record of truth's projection must at minimum parse.",
        )]
    projected = projector.project(projector.read_history(str(h)))
    if on_disk == projected:
        return []
    diverging = sorted(
        k for k in set(on_disk) | set(projected) if on_disk.get(k) != projected.get(k)
    )
    return [_finding(
        "state_is_projection", row["component"],
        "state.json is NOT the projection of history.json — hand-edited, or written "
        "by a stale projector",
        {"diverging_keys": diverging,
         "cursor_on_disk": (on_disk.get("cursor") or {}).get("gate"),
         "cursor_projected": (projected.get("cursor") or {}).get("gate")},
        "Law 7 + the awaiting-physics rule: a compiled view is written only by the "
        "projector's append door. Fix by APPENDING through the door (which rewrites "
        "state from truth), never by editing either file.",
    )]


# ── PACKET JURISDICTION (ticket packet-inspector-wire, 2026-07-28) ───────────
# A build is judged against the packet that charted it. The walk is the wire's whole
# claim: the packet claims its ticket (gated at the berth door), the component's own
# history names its tickets (crossings carry them) — so the gate finds a build's
# charted packets by reading two records that already exist. No new side channel.

_CHART_BERTHS = Path.home() / ".cairn" / "devices" / "chart"

# Where this gate looks up a ticket. A constant so a proof can swap it (the
# _CHART_BERTHS pattern), and composed through chart.orient's ticket_path so the
# reader that OPENS a ticket and this gate cannot disagree about which file that is.
_TICKETS_ROOT = CAIRN_ROOT


def _component_tickets(comp_dir: Path) -> set:
    h = comp_dir / "history.json"
    if not h.exists():
        return set()
    try:
        entries = json.loads(h.read_text())
    except json.JSONDecodeError:
        return set()  # state_is_projection owns the unreadable-history finding
    if not isinstance(entries, list):
        return set()
    return {e["ticket"] for e in entries
            if isinstance(e, dict) and isinstance(e.get("ticket"), str)}


def _charted_packets(comp_dir: Path, stage: str):
    """The berthed <stage>-*.json packets claiming this component's tickets, plus
    the berths that could not be read at all (owned by chart's own inspection —
    an unreadable berth names no ticket, so its finding lands with the berth
    owner, not on every component's crossing)."""
    tickets = _component_tickets(comp_dir)
    packets, unreadable = [], []
    if not _CHART_BERTHS.is_dir():
        return packets, unreadable
    for path in sorted(_CHART_BERTHS.glob("*/packets/%s-*.json" % stage)):
        try:
            packet = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            unreadable.append((path, "%s: %s" % (type(e).__name__, e)))
            continue
        if isinstance(packet, dict) and tickets and packet.get("ticket") in tickets:
            packets.append((path, packet))
    return packets, unreadable


def _unreadable_findings(sieve_name: str, row: dict, unreadable) -> list[dict]:
    if row["component"] != "chart":
        return []  # the berth owner carries the finding, exactly once per sweep
    return [_finding(
        sieve_name, row["component"],
        "berthed packet %s is unreadable" % path.name,
        {"berth": str(path), "why": why},
        "Law 7: a record the gate cannot read is a named finding, never a silent "
        "skip — an unreadable chart could be hiding any claim.",
    ) for path, why in unreadable]


# ── THE FORWARDING ORDER (ticket watchme-emits-a-probe, 2026-07-30) ──────────
# A charted address can stop resolving two ways, and until this voyage the gate
# could only see one of them.
#
#   DRIFT — the world moved and the chart did not know. This is the 2026-07-24
#   failure the ref sieves were built for: 'done' reported while the files stood
#   unmoved. The address names nothing and nothing else names it either.
#
#   A MOVE — the build's own charted plan renamed the thing. Measured here, in
#   anger: this ticket's decompose piece (f) was 'the CALLBACK -> PROBE rename,
#   run FIRST so nothing else is built on the retired word', and running it first
#   is exactly what falsified the chart's own orient refs and survey holdings.
#   Five findings, all correct, none of them drift. The berths are records of
#   truth and may not be edited to look consistent, so the disposition cannot be
#   a quieter chart — it has to be a named successor.
#
# So: a missing address is a finding UNLESS the ticket that charted it records
# where it WENT. The tolerance is not a softening — the gate still measures the
# world, it just measures the far end of a declared move instead of the near end,
# and both ends are checked. An order that forwards to nothing, or forwards an
# address that still resolves, disposes nothing and reds by its own name.


def _forwarding_map(ticket_id) -> dict:
    """The VALID entries of a ticket's forwarding order, ``{from: to}``.

    Only well-shaped entries whose ``to`` resolves and whose ``from`` does not are
    returned, so a broken order grants no tolerance at all — the charted-ref
    finding stands AND ``forwarding_order_resolves`` fires. Two loud records
    beat one silent pass."""
    filed = ticket_path(ticket_id, root=_TICKETS_ROOT)
    if filed is None:
        return {}
    try:
        with open(filed, encoding="utf-8") as fh:
            ticket = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}  # forwarding_order_resolves owns the unreadable-ticket finding
    order = ticket.get("forwarding")
    if not isinstance(order, dict):
        return {}
    good = {}
    for old, entry in order.items():
        if not isinstance(old, str) or not old.strip() or not isinstance(entry, dict):
            continue
        to, why = entry.get("to"), entry.get("why")
        if not all(isinstance(v, str) and v.strip() for v in (to, why)):
            continue
        if ref_exists(old) or not ref_exists(to):
            continue
        good[old] = to
    return good


def forwarding_order_resolves(row: dict, comp_dir: Path) -> list[dict]:
    """A ticket's forwarding order is checked in the world at both ends: every
    entry says where an address WENT (``to``, which must resolve) and WHY, and
    forwards an address that genuinely no longer resolves.

    Provenance: 2026-07-30 — ticket watchme-emits-a-probe's own WATCHME crossing
    was refused with five findings (one orient ref, four survey holdings) naming
    cairn/tools/base/callback.py, its crossing proof, and the homeless intention — the
    three addresses the ticket's OWN decompose piece (f) had renamed hours
    earlier. A chart that plans a rename falsifies its own refs by succeeding,
    and the ref sieves could not tell that from the drift they were taught by.
    This sieve is the other half: the tolerance exists only where a ticket has
    named the successor, permanently, on the record of truth. Forwarding to
    something that is not there, or forwarding a live address out from under
    itself, is exactly the laundering the tolerance must not enable — so both
    red here rather than passing quietly through the sieves that consult it.
    """
    findings = []
    for tid in sorted(_component_tickets(comp_dir)):
        filed = ticket_path(tid, root=_TICKETS_ROOT)
        if filed is None:
            continue  # a ticket not on file is another gate's finding, not this one's
        try:
            with open(filed, encoding="utf-8") as fh:
                ticket = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            findings.append(_finding(
                "forwarding_order_resolves", row["component"],
                "ticket %r cannot be read (%s: %s)" % (tid, type(e).__name__, e),
                {"ticket": tid, "path": filed},
                "Law 7: a record of truth the gate cannot read is a named finding, "
                "never a silent skip — an unreadable ticket could be forwarding "
                "anything anywhere.",
            ))
            continue
        order = ticket.get("forwarding")
        if order is None:
            continue  # most tickets move nothing; absence is the normal case
        if not isinstance(order, dict):
            findings.append(_finding(
                "forwarding_order_resolves", row["component"],
                "ticket %r's forwarding order is not a map of from -> {to, why}" % tid,
                {"ticket": tid, "got": order},
                "a forwarding order the gate cannot read entry-by-entry cannot be "
                "checked at both ends — and an unreadable order that silently "
                "granted tolerance would be the laundering this sieve exists to stop.",
            ))
            continue
        for old, entry in order.items():
            ev = {"ticket": tid, "from": old, "entry": entry}
            if not isinstance(old, str) or not old.strip() or not isinstance(entry, dict):
                findings.append(_finding(
                    "forwarding_order_resolves", row["component"],
                    "forwarding entry %r has no shape (needs a non-empty address "
                    "mapping to {to, why})" % (old,), ev,
                    "an entry that names no address forwards nothing and can be "
                    "checked against nothing.",
                ))
                continue
            to, why = entry.get("to"), entry.get("why")
            if not all(isinstance(v, str) and v.strip() for v in (to, why)):
                findings.append(_finding(
                    "forwarding_order_resolves", row["component"],
                    "forwarding entry %r lacks 'to' and/or 'why'" % old, ev,
                    "the why is forced structurally: a move nobody can justify at "
                    "the gate is a move nobody can adjudicate in a year (CP3).",
                ))
                continue
            if not ref_exists(to):
                findings.append(_finding(
                    "forwarding_order_resolves", row["component"],
                    "forwarding %r -> %r: the successor does not resolve" % (old, to), ev,
                    "Law 8 + the 2026-07-24 failure: forwarding to an address the "
                    "world does not hold is the same hollow claim as the missing "
                    "ref it was offered to dispose, one indirection later.",
                ))
                continue
            if ref_exists(old):
                findings.append(_finding(
                    "forwarding_order_resolves", row["component"],
                    "forwarding %r -> %r: the FROM address still resolves" % (old, to), ev,
                    "a forwarding order is for what MOVED. Pointing a live address "
                    "somewhere else would let a chart's claim be re-aimed at a "
                    "different thing while the original sits there untouched.",
                ))
    return findings


def charted_refs_resolve(row: dict, comp_dir: Path) -> list[dict]:
    """A promoted build must still match what its packet charted: every ref the
    orient packet carried must resolve at promotion time — or the ticket must say
    where it went (see the forwarding order above).

    Provenance: 2026-07-24 — 'done' reported while the files stood unmoved (the
    sharpest claim-vs-world drift on record). The packet is the claim, the
    promotion is the moment, this sieve is the comparison — through the berth
    gate's own ref semantics (cairn.machines.chart.orient.ref_exists), so the judge and
    the gate that admitted the refs cannot disagree.
    """
    packets, unreadable = _charted_packets(comp_dir, "orient")
    findings = _unreadable_findings("charted_refs_resolve", row, unreadable)
    for path, packet in packets:
        refs = packet.get("refs")
        if not isinstance(refs, list):
            continue  # shaped at the berth door; unreachable through it
        forwarded = _forwarding_map(packet.get("ticket"))
        missing = [r for r in refs if not isinstance(r, str) or not ref_exists(r)]
        missing = [r for r in missing if not (isinstance(r, str) and r in forwarded)]
        if missing:
            findings.append(_finding(
                "charted_refs_resolve", row["component"],
                "charted refs no longer resolve at promotion: %s" % ", ".join(map(str, missing)),
                {"berth": str(path), "ticket": packet.get("ticket"), "missing": missing},
                "Law 8 + the 2026-07-24 failure: the world drifted from the chart "
                "between berth and promotion — a build promoted over refs that no "
                "longer exist is a hollow claim.",
            ))
    return findings


# ── THE JUDGES BEFORE THE JUDGED (ticket constrain-filters, 2026-07-28) ──────
# Akien's higher-order build-the-test-first: the acceptance gate for the constrain
# brick's output, installed and proved BEFORE the constrain module exists. The judge
# is the inspector's — behind the inspector's write-gate — and the future constrain
# berth door COMPOSES it (imports judge_constrain; never the reverse), so the module
# structurally cannot shape its own acceptance criteria. One implementation, two
# mouths: the door refuses at berth time, these sieves re-judge at promotion.


def judge_constrain(packet: dict) -> list[dict]:
    """The pure judge over ONE constrain packet — fragments tagged by which sieve
    owns them ({judge, finding, evidence, why_it_matters}). Composed by the berth
    door and wrapped by the gate sieves below; if the two mouths ever disagree,
    this function's singleness is the broken claim."""
    frags = []
    for i, c in enumerate(packet.get("constraints") or []):
        if not isinstance(c, dict):
            frags.append({
                "judge": "constraint_traces",
                "finding": "constraint %d is not a dict" % i,
                "evidence": {"index": i, "got": type(c).__name__},
                "why_it_matters": "a constraint that has no shape can name no source "
                                  "— untraceable by construction.",
            })
            continue
        source = c.get("source")
        if not isinstance(source, str) or not source.strip() or not ref_exists(source):
            frags.append({
                "judge": "constraint_traces",
                "finding": "constraint %d names a source that does not resolve" % i,
                "evidence": {"index": i, "source": source, "text": c.get("text")},
                "why_it_matters": "an invented constraint is fabricated attribution "
                                  "wearing a bound's costume (the 2026-07-26 class): "
                                  "a bound nobody set binds nobody, and a bound that "
                                  "cites nothing cannot be challenged.",
            })
    bounds = packet.get("bounds")
    for side in ("in", "out"):
        vals = bounds.get(side) if isinstance(bounds, dict) else None
        if (not isinstance(vals, list) or not vals
                or any(not isinstance(x, str) or not x.strip() for x in vals)):
            frags.append({
                "judge": "constraint_bounds_complete",
                "finding": "bounds.%s is missing, empty, or malformed" % side,
                "evidence": {"side": side, "got": vals},
                "why_it_matters": "the founding failure (the 2026-07-28 carrier miss) "
                                  "was bounds-checking that never ran to completion — "
                                  "an empty side is exactly that failure as data; a "
                                  "packet must say what is OUT, not just what is in.",
            })
    return frags


def _judge_charted(row: dict, comp_dir: Path, stage: str, judge,
                   judge_name: str, report_unreadable: bool = False) -> list[dict]:
    """One wrapper for every stage's pure judge — the promotion-side mouth. Each
    stage's sieves pass their own judge fn; growing a parallel wrapper per stage
    would be the drift the import_map correction just retired from the proofs."""
    packets, unreadable = _charted_packets(comp_dir, stage)
    findings = _unreadable_findings(judge_name, row, unreadable) if report_unreadable else []
    for path, packet in packets:
        for frag in judge(packet):
            if frag["judge"] == judge_name:
                findings.append(_finding(
                    judge_name, row["component"], frag["finding"],
                    dict(frag["evidence"], berth=str(path), ticket=packet.get("ticket")),
                    frag["why_it_matters"]))
    return findings


def constraint_traces(row: dict, comp_dir: Path) -> list[dict]:
    """Every constraint in a charted constrain packet names a source that resolves.

    Provenance: 2026-07-26 — the fabricated-attribution class (an echo label
    attesting an unhappened push; a misattributed ruling the same week). Installed
    2026-07-28 BEFORE the constrain module exists, on Akien's ordering ruling
    ('we set up it's inspector sieves first') — the failure predates the module,
    so tooth 10 holds: this sieve was taught by a real, dated failure.
    """
    return _judge_charted(row, comp_dir, "constrain", judge_constrain,
                          "constraint_traces", report_unreadable=True)


def constraint_bounds_complete(row: dict, comp_dir: Path) -> list[dict]:
    """A charted constrain packet declares BOTH in-bounds and out-of-bounds,
    non-empty — an empty 'out' is bounds-checking that never ran to completion.

    Provenance: 2026-07-28 — the web-server carrier miss (CC--): premature
    convergence collapsed the bounds question into pattern-match and the carrier
    was missed. Installed the same day, before the constrain module exists (the
    judges-before-the-judged ordering, Akien's higher-order build-the-test-first).
    """
    return _judge_charted(row, comp_dir, "constrain", judge_constrain,
                          "constraint_bounds_complete")


# ── THE JUDGES BEFORE THE JUDGED, SECOND INSTANCE (ticket survey-filters) ────
# The acceptance gate for the SURVEY brick's output, installed before the survey
# module exists — the move constrain-filters filed as 'pattern, not rule, until a
# second instance proves it' (edge (b)); this is that instance. Same physics: the
# judge is the inspector's, the future berth door composes it, never the reverse.


def judge_survey(packet: dict) -> list[dict]:
    """The pure judge over ONE survey packet — fragments tagged by owning sieve.
    A survey asserts an inventory: HOLDINGS must be held by the world (address
    resolves), and the sweep's COVERAGE must be on record (sought non-empty; every
    absence carrying the measure that established it — an absence is a claim)."""
    frags = []
    for i, h in enumerate(packet.get("holdings") or []):
        if not isinstance(h, dict) or not isinstance(h.get("what"), str) \
                or not h.get("what").strip():
            frags.append({
                "judge": "survey_holdings_resolve",
                "finding": "holding %d has no shape (needs non-empty 'what' + 'address')" % i,
                "evidence": {"index": i, "got": h},
                "why_it_matters": "a holding that names no thing can be checked "
                                  "against nothing — uninspectable by construction.",
            })
            continue
        address = h.get("address")
        if not isinstance(address, str) or not address.strip() or not ref_exists(address):
            frags.append({
                "judge": "survey_holdings_resolve",
                "finding": "holding %d names an address that does not resolve" % i,
                "evidence": {"index": i, "what": h.get("what"), "address": address},
                "why_it_matters": "a holding the world does not hold is state "
                                  "reported from records (the 2026-07-26/27 class: "
                                  "wrong about the world three times in one morning) "
                                  "— downstream builds on an inventory of nothing.",
            })
    sought = packet.get("sought")
    if (not isinstance(sought, list) or not sought
            or any(not isinstance(s, str) or not s.strip() for s in sought)):
        frags.append({
            "judge": "survey_coverage_complete",
            "finding": "sought is missing, empty, or malformed",
            "evidence": {"got": sought},
            "why_it_matters": "an empty sought means the sweep never ran wide — "
                              "the stone-1 failure (2026-07-28: a parallel roster "
                              "built because the survey that would have found the "
                              "settled component never happened); a survey must "
                              "say where the light was pointed.",
        })
    for i, a in enumerate(packet.get("absences") or []):
        if not isinstance(a, dict) or not all(
                isinstance(a.get(k), str) and a.get(k).strip()
                for k in ("what", "measure")):
            frags.append({
                "judge": "survey_coverage_complete",
                "finding": "absence %d lacks its measure (needs non-empty 'what' + 'measure')" % i,
                "evidence": {"index": i, "got": a},
                "why_it_matters": "an absence is a claim, and an unmeasured absence "
                                  "is the most dangerous claim in the preamble — "
                                  "'logging: 0 of 13' (2026-07-27) was an absence "
                                  "established by word-grep; the measure must "
                                  "travel with the claim so it can be challenged.",
            })
    return frags


def survey_holdings_resolve(row: dict, comp_dir: Path) -> list[dict]:
    """Every holding in a charted survey packet names an address that resolves —
    through the berth gate's own ref semantics, so the two mouths agree.

    Provenance: 2026-07-26/27 — system state reported from records, wrong about
    the world three times in one morning (device_census's seeding failures); and
    2026-07-28, stone 1's parallel charter-glob roster — a build begun without
    surveying the settled territory. Installed 2026-07-28 BEFORE the survey
    module exists (judges-before-the-judged, second instance — the pattern
    constrain-filters filed at edge (b), proven by this use).

    THE FORWARDING ORDER IS CONSULTED HERE, NOT IN THE JUDGE, and the asymmetry
    is the point (2026-07-30). ``judge_survey`` is also the BERTH DOOR's mouth,
    and at berth time every holding resolves by definition — that is what makes
    it a holding. Teaching the pure judge about successors would hand the door a
    tolerance it has no moment to need, and would let a packet be berthed naming
    an address that was already gone. So the door keeps the flat rule and only
    the promotion side, which alone stands downstream of a move, disposes.
    """
    findings = _judge_charted(row, comp_dir, "survey", judge_survey,
                              "survey_holdings_resolve", report_unreadable=True)
    return [f for f in findings
            if f["evidence"].get("address") not in
            _forwarding_map(f["evidence"].get("ticket"))]


def survey_coverage_complete(row: dict, comp_dir: Path) -> list[dict]:
    """A charted survey packet declares what it SOUGHT (non-empty), and every
    absence claim carries the measure that established it.

    Provenance: 2026-07-27 — 'logging: 0 of 13': an absence claimed from a
    word-grep (a mention-measure that missed the capability), collapsing three
    times in one morning. Installed 2026-07-28, before the survey module exists —
    an absence without its measure is that failure as data.
    """
    return _judge_charted(row, comp_dir, "survey", judge_survey,
                          "survey_coverage_complete")


# ── THE JUDGES BEFORE THE JUDGED, THIRD APPLICATION (ticket decompose-filters) ──
# The acceptance gate for the DECOMPOSE brick's output, installed before the
# decompose module exists — the ordering is routine now (proven at n=2 by
# survey-filters). Same physics: the judge is the inspector's, the future berth
# door composes it, never the reverse. The judge reads the packet's survey_ref
# berth with its OWN minimal read — importing chart's chain reader would be the
# inspector importing from the module family it judges.


def judge_decompose(packet: dict) -> list[dict]:
    """The pure judge over ONE decompose packet — fragments tagged by owning
    sieve. A decomposition derives from the chain or it is invented: a
    'compose' piece may only use addresses the survey berth HOLDS, a 'build'
    piece may only fill an absence the survey MEASURED — known-vs-novel as
    physics, a stage early."""
    frags = []
    holding_addrs, absence_whats, chain_ok = set(), set(), False
    ref = packet.get("survey_ref")
    try:
        with open(os.path.expanduser(ref), encoding="utf-8") as fh:
            berth = json.load(fh)
        holdings, absences = berth.get("holdings"), berth.get("absences")
        if isinstance(holdings, list) and isinstance(absences, list):
            holding_addrs = {h.get("address") for h in holdings
                             if isinstance(h, dict)}
            absence_whats = {a.get("what") for a in absences
                             if isinstance(a, dict)}
            chain_ok = True
    except (TypeError, OSError, ValueError):
        pass
    if not chain_ok:
        frags.append({
            "judge": "decompose_composes_holdings",
            "finding": "survey_ref does not read as a survey berth",
            "evidence": {"survey_ref": ref},
            "why_it_matters": "the chain broke — a split that cannot be checked "
                              "against the inventory that grounds it is a split "
                              "filled from the conversation, the step-skipping "
                              "the chain exists to make a build error.",
        })
    sub_problems = packet.get("sub_problems")
    if not isinstance(sub_problems, list) or not sub_problems:
        frags.append({
            "judge": "decompose_builds_absences",
            "finding": "sub_problems is missing, empty, or malformed",
            "evidence": {"got": sub_problems},
            "why_it_matters": "an empty decomposition hands downstream the whole "
                              "request ungrounded — every piece it then builds is "
                              "unmeasured against the inventory (the stone-1 "
                              "parallel-roster failure, wholesale).",
        })
        return frags
    for i, sp in enumerate(sub_problems):
        if not isinstance(sp, dict) or not all(
                isinstance(sp.get(k), str) and sp.get(k).strip()
                for k in ("what", "why")) or sp.get("kind") not in ("compose", "build"):
            frags.append({
                "judge": "decompose_composes_holdings",
                "finding": "sub-problem %d has no shape (needs non-empty 'what' + "
                           "'why' + kind compose|build)" % i,
                "evidence": {"index": i, "got": sp},
                "why_it_matters": "a piece without its why cannot be adjudicated "
                                  "(the why is forced structurally, never a blank "
                                  "field), and a piece without a kind makes no "
                                  "checkable claim against the inventory.",
            })
            continue
        uses = sp.get("uses")
        if sp["kind"] == "compose":
            if (not isinstance(uses, list) or not uses
                    or any(not isinstance(u, str) or not u.strip() for u in uses)):
                frags.append({
                    "judge": "decompose_composes_holdings",
                    "finding": "compose sub-problem %d lists nothing it composes" % i,
                    "evidence": {"index": i, "what": sp["what"], "uses": uses},
                    "why_it_matters": "a compose claim with no addresses is a "
                                      "build wearing compose's costume — "
                                      "unchallengeable by construction.",
                })
                uses = []
        else:
            fills = sp.get("fills")
            if not isinstance(fills, str) or not fills.strip():
                frags.append({
                    "judge": "decompose_builds_absences",
                    "finding": "build sub-problem %d names no absence it fills" % i,
                    "evidence": {"index": i, "what": sp["what"], "fills": fills},
                    "why_it_matters": "build-minimal means building against a "
                                      "MEASURED absence — a build that cites none "
                                      "is work invented, not derived (the "
                                      "2026-07-24 substitution class).",
                })
            elif chain_ok and fills not in absence_whats:
                frags.append({
                    "judge": "decompose_builds_absences",
                    "finding": "build sub-problem %d fills %r — not a measured "
                               "absence in the survey berth" % (i, fills),
                    "evidence": {"index": i, "what": sp["what"], "fills": fills,
                                 "measured_absences": sorted(
                                     a for a in absence_whats if a)},
                    "why_it_matters": "what was never measured absent is either "
                                      "already held (stone 1's parallel roster, "
                                      "2026-07-28) or invented (2026-07-24 "
                                      "done-while-unmoved) — either way the piece "
                                      "bypassed the sweep.",
                })
            uses = uses if isinstance(uses, list) else []
        if chain_ok:
            for u in uses:
                if u not in holding_addrs:
                    frags.append({
                        "judge": "decompose_composes_holdings",
                        "finding": "sub-problem %d uses %r — not a holding the "
                                   "survey berth carries" % (i, u),
                        "evidence": {"index": i, "what": sp["what"], "uses": u},
                        "why_it_matters": "composition outside the measured "
                                          "inventory bypasses the sweep — the "
                                          "one-web-server drift (2026-07-28: the "
                                          "exception paralleled instead of the "
                                          "rule composed); if the piece needs it, "
                                          "the survey must hold it first.",
                    })
    return frags


def decompose_composes_holdings(row: dict, comp_dir: Path) -> list[dict]:
    """Every 'compose' piece in a charted decompose packet uses only addresses
    the survey berth actually holds, every piece has its shape, and the chain
    to the survey berth reads.

    Provenance: 2026-07-28 — stone 1's parallel charter-glob roster (a settled
    component rebuilt because the sweep went unreferenced) and the one-web-server
    drift (CC--: the /harbor exception paralleled instead of the pane rule
    composed). Installed 2026-07-28 BEFORE the decompose module exists — the
    judges-before-the-judged ordering, routine since survey-filters proved it.
    """
    return _judge_charted(row, comp_dir, "decompose", judge_decompose,
                          "decompose_composes_holdings", report_unreadable=True)


def decompose_builds_absences(row: dict, comp_dir: Path) -> list[dict]:
    """Every 'build' piece in a charted decompose packet fills an absence the
    survey berth MEASURED, verbatim — build-minimal as physics.

    Provenance: 2026-07-24 — done-while-unmoved (a substituted mechanism: work
    invented rather than derived from what the chain established; the cascade
    the chosen path implies IS the task). Installed 2026-07-28, before the
    decompose module exists.
    """
    return _judge_charted(row, comp_dir, "decompose", judge_decompose,
                          "decompose_builds_absences")


# ── THE JUDGES BEFORE THE JUDGED, FOURTH APPLICATION (ticket triage-filters) ──
# The acceptance gate for the TRIAGE brick's output, installed before the triage
# module exists. Same physics: the judge is the inspector's, the future berth
# door composes it, never the reverse. The judge reads the packet's decompose_ref
# berth with its OWN minimal read — same reason as judge_decompose above.


def judge_triage(packet: dict) -> list[dict]:
    """The pure judge over ONE triage packet — fragments tagged by owning
    sieve. A triage either ranks the derived work or quietly reshapes it: the
    ORDER must be a complete permutation of the split's pieces (nothing dropped,
    invented, or double-ordered — coverage as a multiset), and every entry must
    carry its why_now (the ranking standard stated, so the order can be
    adjudicated)."""
    frags = []
    piece_counts, chain_ok = {}, False
    ref = packet.get("decompose_ref")
    try:
        with open(os.path.expanduser(ref), encoding="utf-8") as fh:
            berth = json.load(fh)
        sub_problems = berth.get("sub_problems")
        if isinstance(sub_problems, list):
            for sp in sub_problems:
                if isinstance(sp, dict) and isinstance(sp.get("what"), str):
                    piece_counts[sp["what"]] = piece_counts.get(sp["what"], 0) + 1
            chain_ok = True
    except (TypeError, OSError, ValueError):
        pass
    if not chain_ok:
        frags.append({
            "judge": "triage_covers_the_split",
            "finding": "decompose_ref does not read as a decompose berth",
            "evidence": {"decompose_ref": ref},
            "why_it_matters": "the chain broke — a ranking that cannot be "
                              "checked against the split that grounds it is a "
                              "ranking filled from the conversation, the "
                              "step-skipping the chain exists to make a build "
                              "error.",
        })
    order = packet.get("order")
    if not isinstance(order, list) or not order:
        frags.append({
            "judge": "triage_covers_the_split",
            "finding": "order is missing, empty, or malformed",
            "evidence": {"got": order},
            "why_it_matters": "an empty triage ranks nothing — downstream "
                              "starts wherever is cheapest, which is the "
                              "unstated-standard reflex this gate exists to "
                              "stop.",
        })
        return frags
    ordered_counts = {}
    for i, entry in enumerate(order):
        if not isinstance(entry, dict) or not isinstance(entry.get("what"), str) \
                or not entry.get("what").strip():
            frags.append({
                "judge": "triage_covers_the_split",
                "finding": "order entry %d has no shape (needs non-empty 'what' "
                           "+ 'why_now')" % i,
                "evidence": {"index": i, "got": entry},
                "why_it_matters": "an entry that names no piece covers nothing "
                                  "— uncheckable against the split by "
                                  "construction.",
            })
            continue
        what = entry["what"]
        ordered_counts[what] = ordered_counts.get(what, 0) + 1
        why_now = entry.get("why_now")
        if not isinstance(why_now, str) or not why_now.strip():
            frags.append({
                "judge": "triage_reasons_the_order",
                "finding": "order entry %d (%r) carries no why_now" % (i, what),
                "evidence": {"index": i, "what": what, "why_now": why_now},
                "why_it_matters": "an unreasoned rank cannot be adjudicated — "
                                  "the cheap-first reflex (the standing "
                                  "get-it-right-not-cheap CC--) hides exactly "
                                  "in unstated ranking standards; the 2026-07-23 "
                                  "solidify-the-layer-below inversion was "
                                  "adjudicable only because its why was stated.",
            })
    if chain_ok:
        for what, n in ordered_counts.items():
            have = piece_counts.get(what, 0)
            if have == 0:
                frags.append({
                    "judge": "triage_covers_the_split",
                    "finding": "the order ranks %r — not a piece the split "
                               "carries" % what,
                    "evidence": {"what": what,
                                 "split_pieces": sorted(piece_counts)},
                    "why_it_matters": "a ranked piece the split never derived "
                                      "is work invented at the ranking stage — "
                                      "the 2026-07-24 substitution class, one "
                                      "stage later.",
                })
            elif n > have:
                frags.append({
                    "judge": "triage_covers_the_split",
                    "finding": "the order ranks %r %d times; the split carries "
                               "it %d" % (what, n, have),
                    "evidence": {"what": what, "ordered": n, "split": have},
                    "why_it_matters": "a double-ordered piece is two copies of "
                                      "one truth — the bookkeeping drift "
                                      "position-is-rank exists to prevent.",
                })
        dropped = sorted(w for w, n in piece_counts.items()
                         if ordered_counts.get(w, 0) < n)
        if dropped:
            frags.append({
                "judge": "triage_covers_the_split",
                "finding": "the order drops pieces the split carries: %s"
                           % ", ".join(repr(w) for w in dropped),
                "evidence": {"dropped": dropped,
                             "split_pieces": sorted(piece_counts)},
                "why_it_matters": "a silent drop at triage is descoping without "
                                  "the word — the 2026-07-24 done-while-unmoved "
                                  "class (the expensive implied piece quietly "
                                  "deprioritized out of existence); descoping "
                                  "is a bounds question for Akien, never a "
                                  "ranking.",
            })
    return frags


def triage_covers_the_split(row: dict, comp_dir: Path) -> list[dict]:
    """The order in a charted triage packet is a complete permutation of the
    decompose berth's pieces — nothing dropped, invented, or double-ordered —
    and the chain to the decompose berth reads.

    Provenance: 2026-07-24 — done-while-unmoved (the expensive piece the chosen
    path implied was silently dropped for a cheaper substitute; the drop began
    as a triage defect). Installed 2026-07-28 BEFORE the triage module exists —
    the judges-before-the-judged ordering, fourth application.
    """
    return _judge_charted(row, comp_dir, "triage", judge_triage,
                          "triage_covers_the_split", report_unreadable=True)


def triage_reasons_the_order(row: dict, comp_dir: Path) -> list[dict]:
    """Every entry in a charted triage packet's order carries its non-empty
    why_now — the ranking standard travels with the rank.

    Provenance: the standing get-it-right-not-cheap CC-- (the reflex ordering
    is by cost-to-me, hidden in unstated standards) and 2026-07-23 —
    solidify-the-layer-below (the rackmount flake ranked ahead of the librarian
    spine: the honest order inverted the appealing one, and only its STATED why
    made the inversion adjudicable). Installed 2026-07-28, before the triage
    module exists.
    """
    return _judge_charted(row, comp_dir, "triage", judge_triage,
                          "triage_reasons_the_order")


# ── THE JUDGES BEFORE THE JUDGED, FIFTH APPLICATION (ticket hypothesize-filters) ──
# The acceptance gate for the HYPOTHESIZE brick's output, installed before the
# hypothesize module exists. Same physics: the judge is the inspector's, the
# future berth door composes it, never the reverse. The judge reads the packet's
# triage_ref berth with its OWN minimal read — same reason as the judges above.


def judge_hypothesize(packet: dict) -> list[dict]:
    """The pure judge over ONE hypothesize packet — fragments tagged by owning
    sieve. Law 3 as schema: every hypothesis attaches to a RANKED piece
    (verbatim) and every ranked piece carries at least one hypothesis (a
    covering — the piece with none is the piece whose wrong landing reds
    nothing); and every hypothesis carries its expect, its falsifier, and its
    instrument, so the claim can be challenged."""
    frags = []
    ranked, chain_ok = set(), False
    ref = packet.get("triage_ref")
    try:
        with open(os.path.expanduser(ref), encoding="utf-8") as fh:
            berth = json.load(fh)
        order = berth.get("order")
        if isinstance(order, list):
            ranked = {e.get("what") for e in order
                      if isinstance(e, dict) and isinstance(e.get("what"), str)}
            chain_ok = True
    except (TypeError, OSError, ValueError):
        pass
    if not chain_ok:
        frags.append({
            "judge": "hypothesize_covers_the_ranked",
            "finding": "triage_ref does not read as a triage berth",
            "evidence": {"triage_ref": ref},
            "why_it_matters": "the chain broke — expectations that cannot be "
                              "checked against the ranked work they claim to "
                              "cover are expectations filled from the "
                              "conversation, the step-skipping the chain "
                              "exists to make a build error.",
        })
    hypotheses = packet.get("hypotheses")
    if not isinstance(hypotheses, list) or not hypotheses:
        frags.append({
            "judge": "hypothesize_covers_the_ranked",
            "finding": "hypotheses is missing, empty, or malformed",
            "evidence": {"got": hypotheses},
            "why_it_matters": "a build with no stated expectations is a build "
                              "whose wrong landing reds nothing — the "
                              "2026-07-26/27 wrong-about-the-world class, "
                              "wholesale.",
        })
        return frags
    covered = set()
    for i, h in enumerate(hypotheses):
        if not isinstance(h, dict) or not isinstance(h.get("piece"), str) \
                or not h.get("piece").strip():
            frags.append({
                "judge": "hypothesize_covers_the_ranked",
                "finding": "hypothesis %d has no shape (needs a non-empty "
                           "'piece')" % i,
                "evidence": {"index": i, "got": h},
                "why_it_matters": "a hypothesis that names no piece covers "
                                  "nothing — uncheckable against the ranking "
                                  "by construction.",
            })
            continue
        piece = h["piece"]
        covered.add(piece)
        if chain_ok and piece not in ranked:
            frags.append({
                "judge": "hypothesize_covers_the_ranked",
                "finding": "hypothesis %d attaches to %r — not a piece the "
                           "ranking carries" % (i, piece),
                "evidence": {"index": i, "piece": piece,
                             "ranked_pieces": sorted(ranked)},
                "why_it_matters": "an expectation about work the chain never "
                                  "derived is invention at the claim stage — "
                                  "the substitution class, one stage later "
                                  "again.",
            })
        lacking = [k for k in ("expect", "falsifier", "instrument")
                   if not isinstance(h.get(k), str) or not h.get(k).strip()]
        if lacking:
            frags.append({
                "judge": "hypothesize_falsifiable_measured",
                "finding": "hypothesis %d (%r) lacks: %s"
                           % (i, piece, ", ".join(lacking)),
                "evidence": {"index": i, "piece": piece, "lacking": lacking},
                "why_it_matters": "an unmeasured claim is a hypothesis only "
                                  "when LABELED as one (Law 3) — without its "
                                  "falsifier and named instrument it cannot "
                                  "be challenged ('0 of 13', 2026-07-27: the "
                                  "instrument was a word-grep and nobody "
                                  "could tell).",
            })
    if chain_ok:
        uncovered = sorted(ranked - covered)
        if uncovered:
            frags.append({
                "judge": "hypothesize_covers_the_ranked",
                "finding": "ranked pieces carry no hypothesis: %s"
                           % ", ".join(repr(w) for w in uncovered),
                "evidence": {"uncovered": uncovered,
                             "ranked_pieces": sorted(ranked)},
                "why_it_matters": "the piece nobody predicted is the piece "
                                  "that lands wrong silently — the covering "
                                  "is what makes a kill a FINDING instead of "
                                  "a surprise.",
            })
    return frags


def hypothesize_covers_the_ranked(row: dict, comp_dir: Path) -> list[dict]:
    """Every hypothesis in a charted hypothesize packet attaches to a piece the
    triage berth's order carries, every ranked piece carries at least one
    hypothesis, and the chain to the triage berth reads.

    Provenance: 2026-07-26/27 — the wrong-about-the-world mornings (expectations
    never instrumented; three false state claims before noon), and the
    2026-07-24 substitution class (work invented rather than derived — here, an
    expectation about underived work). Installed 2026-07-28 BEFORE the
    hypothesize module exists — judges-before-the-judged, fifth application.
    """
    return _judge_charted(row, comp_dir, "hypothesize", judge_hypothesize,
                          "hypothesize_covers_the_ranked", report_unreadable=True)


def hypothesize_falsifiable_measured(row: dict, comp_dir: Path) -> list[dict]:
    """Every hypothesis in a charted hypothesize packet carries its expect, its
    falsifier, and its named instrument — missing fields reported completely in
    one finding.

    Provenance: 2026-07-27 — 'logging: 0 of 13' (a claim whose instrument was a
    word-grep; unchallengeable because unnamed), plus the falsifier-defect proof
    lessons (the pinned-cursor spurious red; the coin-toss leak-scan) — the
    falsifier is part of the claim, not an afterthought. /sorted's 'no
    falsifier, not ready to cast' gate, moved one stage earlier and one rung
    down. Installed 2026-07-28, before the hypothesize module exists.
    """
    return _judge_charted(row, comp_dir, "hypothesize", judge_hypothesize,
                          "hypothesize_falsifiable_measured")


# ── THE JUDGES BEFORE THE JUDGED, SIXTH APPLICATION (ticket validate-filters) ──
# The acceptance gate for the VALIDATE brick's output, installed before the
# validate module exists. Same physics: the judge is the inspector's, the future
# berth door composes it, never the reverse. The coverage vocabulary COMPOSES
# THE PREVIOUS GATE'S INVARIANT — a berthed hypothesize covering equals the
# ranked set (hypothesize-filters enforced it), so this judge reads ONE link
# with one minimal open; each judge stays small by standing on the gate below.


def judge_validate(packet: dict) -> list[dict]:
    """The pure judge over ONE validate packet — fragments tagged by owning
    sieve. Done gets an instrument or it is narration: every criterion carries
    its claim and its named instrument; every criterion's covers entries name
    pieces the hypothesize berth claims; and the union of covers equals that
    piece set — every piece's done is measured by at least one criterion."""
    frags = []
    claimed, chain_ok = set(), False
    ref = packet.get("hypothesize_ref")
    try:
        with open(os.path.expanduser(ref), encoding="utf-8") as fh:
            berth = json.load(fh)
        hypotheses = berth.get("hypotheses")
        if isinstance(hypotheses, list):
            claimed = {h.get("piece") for h in hypotheses
                       if isinstance(h, dict) and isinstance(h.get("piece"), str)}
            chain_ok = True
    except (TypeError, OSError, ValueError):
        pass
    if not chain_ok:
        frags.append({
            "judge": "validate_covers_the_build",
            "finding": "hypothesize_ref does not read as a hypothesize berth",
            "evidence": {"hypothesize_ref": ref},
            "why_it_matters": "the chain broke — acceptance criteria that "
                              "cannot be checked against the claimed work are "
                              "criteria filled from the conversation, the "
                              "step-skipping the chain exists to make a build "
                              "error.",
        })
    criteria = packet.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        frags.append({
            "judge": "validate_covers_the_build",
            "finding": "criteria is missing, empty, or malformed",
            "evidence": {"got": criteria},
            "why_it_matters": "a build with no acceptance criteria is a build "
                              "whose done is narration — the 2026-07-24 class, "
                              "wholesale.",
        })
        return frags
    covered = set()
    for i, c in enumerate(criteria):
        if not isinstance(c, dict):
            frags.append({
                "judge": "validate_measures_done",
                "finding": "criterion %d is not a dict" % i,
                "evidence": {"index": i, "got": type(c).__name__},
                "why_it_matters": "a criterion with no shape can name no "
                                  "instrument — unmeasurable by construction.",
            })
            continue
        lacking = [k for k in ("claim", "instrument")
                   if not isinstance(c.get(k), str) or not c.get(k).strip()]
        if lacking:
            frags.append({
                "judge": "validate_measures_done",
                "finding": "criterion %d lacks: %s" % (i, ", ".join(lacking)),
                "evidence": {"index": i, "claim": c.get("claim"),
                             "lacking": lacking},
                "why_it_matters": "done is verified in the world by the "
                                  "instrument, never the narration — the "
                                  "2026-07-24 done-while-unmoved class: DONE "
                                  "was reported from a proxy while the real "
                                  "files stood unmoved; the instrument was "
                                  "never run.",
            })
        covers = c.get("covers")
        if (not isinstance(covers, list) or not covers
                or any(not isinstance(w, str) or not w.strip() for w in covers)):
            frags.append({
                "judge": "validate_covers_the_build",
                "finding": "criterion %d covers nothing" % i,
                "evidence": {"index": i, "claim": c.get("claim"),
                             "covers": covers},
                "why_it_matters": "a criterion tied to no piece closes "
                                  "nothing — the acceptance run cannot say "
                                  "what it validated.",
            })
            continue
        for w in covers:
            covered.add(w)
            if chain_ok and w not in claimed:
                frags.append({
                    "judge": "validate_covers_the_build",
                    "finding": "criterion %d covers %r — not a piece the "
                               "hypothesize berth claims" % (i, w),
                    "evidence": {"index": i, "covers": w,
                                 "claimed_pieces": sorted(claimed)},
                    "why_it_matters": "acceptance for work the chain never "
                                      "claimed is invention at the acceptance "
                                      "stage — the substitution class at its "
                                      "last door.",
                })
    if chain_ok:
        uncovered = sorted(claimed - covered)
        if uncovered:
            frags.append({
                "judge": "validate_covers_the_build",
                "finding": "claimed pieces no criterion covers: %s"
                           % ", ".join(repr(w) for w in uncovered),
                "evidence": {"uncovered": uncovered,
                             "claimed_pieces": sorted(claimed)},
                "why_it_matters": "the unvalidated piece is the 2026-07-24 "
                                  "piece — the one whose done was narrated; "
                                  "coverage is what makes acceptance a "
                                  "measurement of the whole build.",
            })
    return frags


def validate_measures_done(row: dict, comp_dir: Path) -> list[dict]:
    """Every criterion in a charted validate packet carries its claim and its
    named instrument — missing fields reported completely in one finding.

    Provenance: 2026-07-24 — done-while-unmoved (the sharpest correction on
    record: DONE reported from a proxy while the real files stood unmoved; the
    instrument — ls of the actual files — was never run). Installed 2026-07-28
    BEFORE the validate module exists — judges-before-the-judged, sixth
    application.
    """
    return _judge_charted(row, comp_dir, "validate", judge_validate,
                          "validate_measures_done", report_unreadable=True)


def validate_covers_the_build(row: dict, comp_dir: Path) -> list[dict]:
    """Every criterion's covers entries name pieces the hypothesize berth
    claims, the union of covers equals that piece set, and the chain to the
    hypothesize berth reads.

    Provenance: 2026-07-24 — the dropped piece was also the unvalidated piece
    (the substitution survived because no acceptance measured the whole); and
    the wire's filed edge (a), 2026-07-28 — success_criteria as an IOU from the
    day packet jurisdiction landed, coming due at the stage whose question they
    answer. Installed 2026-07-28, before the validate module exists.
    """
    return _judge_charted(row, comp_dir, "validate", judge_validate,
                          "validate_covers_the_build")


# ── THE ENTRY GATE (ticket buildme-rides-the-chart, 2026-07-29) ──────────────
# The other end of packet jurisdiction: promotion judges a build AGAINST its chart;
# this judges that a chart EXISTS before the build may begin. A cast ticket crossing
# forward into BUILDME must be claimed by a berthed chart chain — the validate berth
# (stage 7) carries the claim, and a validate berth on disk means the whole preamble
# held at its doors, so one direct claim-check is the chain-check (no ref-walk).
#
# Deliberately NOT in SIEVES: that registry's jurisdiction is the promotion sweep
# over components, which has no crossing context and would retro-red every component
# whose tickets predate the chart chain (a healthy component drawing a finding — the
# always-fires failure tooth 1 exists to refuse). This check's jurisdiction is ONE
# crossing's own ticket, so it is called from the emit chokepoint's BUILDME entry,
# exactly as the census is called from its PROVEME exit.
#
# Provenance: installed 2026-07-29 on Akien's word, the stake in numbers (Fable at
# 64% of usage — what the gate enforces, the model no longer spends context
# remembering). Retires the sail step-0 prose refusal into physics (Law 4).


def buildme_rides_the_chart(ticket: str, *, berths_root: Path | None = None) -> list[dict]:
    """Green (empty findings) iff a readable berthed validate packet claims ``ticket``.

    Red returns ONE finding naming the ticket, the searched root, and the
    disposition — complete on the first pass, nothing to re-run.
    """
    root = Path(berths_root) if berths_root is not None else _CHART_BERTHS
    if root.is_dir():
        for path in sorted(root.glob("*/packets/validate-*.json")):
            try:
                packet = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue  # an unreadable berth names no claim; the berth owner's sweep carries that finding
            if isinstance(packet, dict) and packet.get("ticket") == ticket:
                return []
    return [_finding(
        "buildme_rides_the_chart", ticket,
        "no berthed chart chain claims ticket %r — the build has no charted course" % ticket,
        {"ticket": ticket, "searched": str(root), "wanted": "*/packets/validate-*.json with a 'ticket' field naming this ticket"},
        "Law 4 + Law 1: the preamble is compiled once into berths and the build runs "
        "inside them; a BUILDME with no chart is the step-skipping the chain exists to "
        "refuse. Disposition: run /chart for this request (the validate berth carries "
        "the claim), then cross again.",
    )]


# ── THE INTENT GATE (ticket intent-becomes-a-learning-block, 2026-08-01) ─────
# Akien's ruling, 2026-08-01: "no cast without /intent" — the door is PHYSICS, not
# policy. He selected it over a self-checking door, knowing the cost: /intent becomes
# mandatory before any cast, which gates CC's casting and not his direction.
#
# WHY THE CLAIM TRAVELS THE OPPOSITE WAY FROM THE CHART'S. buildme_rides_the_chart
# globs berths for a packet CLAIMING a ticket. That cannot work here: /intent fires
# BEFORE /sorted casts, so an intent berth can never know a ticket id that does not
# exist yet. So the ticket names its berth instead. Field and check are one act — a
# field nothing reads is policy wearing physics' clothes, which is the defect this
# whole ticket exists to close.
#
# THE NAMED EXEMPTION, AND THE NUMBER THAT FORCED IT. Measured before wiring, as the
# turnscan IOU taught: 25 of 70 filed tickets sit at or before BUILDME and ZERO carry
# an intent_berth. A gate that reds on absence reds a quarter of the backlog. So the
# gate accepts "none, because <X>" — the same shape /sorted already uses for watchme,
# where silence is the failure and a named exemption is legal. You must say something;
# what you may not do is say nothing. The exemption is recorded in the gate note, so
# an exempted crossing is visible in the journal rather than indistinguishable from a
# berthed one.


_EXEMPT_PREFIX = "none, because "
# Matched on the RAW value, not a stripped one: `"none, because "` — the exemption with
# nothing after it — loses its trailing space to .strip() and then fails a
# startswith(_EXEMPT_PREFIX) test, so the blank exemption fell through to the path
# branch and was refused as an unreadable berth. Same red, wrong reason, and a wrong
# reason at a diagnostic surface sends the reader to fix a path that was never a path.
_EXEMPT_RE = re.compile(r"^\s*none,\s+because\b", re.IGNORECASE)


def buildme_rides_the_intent(ticket: str, *, tickets_root: Path | None = None) -> list[dict]:
    """Green (empty findings) iff the cast ticket names an /intent firing — either a
    readable berth for skill ``intent``, or an explicit ``none, because <X>`` exemption.

    Red returns ONE finding naming the ticket, what was wanted and what was found —
    complete on the first pass, nothing to re-run.
    """
    # Lazy, the same boot-order law the entry/exit gates already follow: the cost lands
    # only at a journaled BUILDME entry, and the inspector does not grow a load-time
    # dependency on the seam it merely reads.
    from cairn.machines.skill_block.skill_block import read_berth

    root = tickets_root if tickets_root is not None else _TICKETS_ROOT
    filed = ticket_path(ticket, root=root)
    if filed is None:
        return []
    try:
        doc = json.loads(Path(filed).read_text())
    except (OSError, json.JSONDecodeError):
        # Not this gate's finding to make: an unfiled or unreadable ticket is already
        # the chokepoint's own refusal ("a named-but-uncast ticket is an error to fix"),
        # and two sieves reporting one fault is noise at the diagnostic surface.
        return []

    berth = doc.get("intent_berth") if isinstance(doc, dict) else None
    why = (
        "Akien's ruling 2026-08-01: /intent is the cheapest gate in the system and an "
        "intention that shouldn't exist dies there, before any cost is spent on it "
        "(Law 1). A ticket that cannot name its /intent firing was cast without one — "
        "or with one nobody recorded, which is the same thing to every later reader "
        "(Law 3). Disposition: fire /intent for this request and put its berth path in "
        "the ticket's 'intent_berth', or record an explicit exemption "
        f"('{_EXEMPT_PREFIX}<why>') — silence is the one answer that is not legal."
    )

    if berth is None:
        return [_finding(
            "buildme_rides_the_intent", ticket,
            "ticket %r names no /intent firing — no 'intent_berth' field at all" % ticket,
            {"ticket": ticket, "ticket_file": str(filed), "found": None,
             "wanted": "an 'intent_berth' path to a berthed /intent firing, or "
                       f"'{_EXEMPT_PREFIX}<why>'"},
            why,
        )]

    if not isinstance(berth, str) or not berth.strip():
        return [_finding(
            "buildme_rides_the_intent", ticket,
            "ticket %r carries an empty or non-string 'intent_berth'" % ticket,
            {"ticket": ticket, "ticket_file": str(filed), "found": berth,
             "wanted": "a berth path, or " + f"'{_EXEMPT_PREFIX}<why>'"},
            why,
        )]

    exempt = _EXEMPT_RE.match(berth)
    if exempt:
        reason = berth[exempt.end():].strip()
        if not reason:
            return [_finding(
                "buildme_rides_the_intent", ticket,
                "ticket %r claims an /intent exemption with no reason after "
                "'%s'" % (ticket, _EXEMPT_PREFIX),
                {"ticket": ticket, "ticket_file": str(filed), "found": berth},
                "An exemption whose reason is blank is silence with a prefix on it. The "
                "whole point of the named exemption is that a later reader can judge it.",
            )]
        return []

    doc_berth = read_berth(berth)
    if doc_berth is None:
        return [_finding(
            "buildme_rides_the_intent", ticket,
            "ticket %r names an /intent berth that does not read: %s" % (ticket, berth),
            {"ticket": ticket, "ticket_file": str(filed), "intent_berth": berth,
             "found": "missing or unparseable"},
            "A berth path that resolves to nothing is state reported from records — the "
            "gate would be passing on a promise. " + why,
        )]

    if doc_berth.get("skill") != "intent":
        return [_finding(
            "buildme_rides_the_intent", ticket,
            "ticket %r names a berth for skill %r, not 'intent'"
            % (ticket, doc_berth.get("skill")),
            {"ticket": ticket, "ticket_file": str(filed), "intent_berth": berth,
             "found_skill": doc_berth.get("skill")},
            "The gate reads which skill actually fired, not which one the field is named "
            "after — otherwise any berth at all would satisfy it. " + why,
        )]

    return []


def reason_has_referent(reason: str, *, repo: Path | None = None,
                        commons: Path | None = None) -> bool:
    """The floor-form of 'judgeable': the reason points at something CHECKABLE — a path
    on disk, a cast ticket id, or a roster command (bin/cmd/<name>).

    ONE implementation, two mouths (the read_berth rule): the sorted door
    (skills/sorted/door.py) judges a cast's watchme exemption with this, and
    ``buildme_rides_the_sorted`` below judges a ticket's sorted_berth exemption with
    the same function — so the cast-time door and the crossing-time gate cannot
    disagree about what a judgeable reason is. The system's existing rule is 'sources
    must resolve' (the constrain judges refuse invented ones); this bends that rule to
    prose. Quality of the reason stays the model's (the engine track's thesis);
    EXISTENCE of a checkable referent is a floor, and floors are physics.
    Provenance: ticket sorted-becomes-a-learning-block (opus-pass rank 3, ruled
    2026-08-03) — the measured hollow pass was 'none, because <one plausible
    sentence>'.
    """
    repo = Path(repo) if repo is not None else _REPO_ROOT
    # CAIRN_ROOT is the cairn REPO root (chart.orient's, string, os.path lineage);
    # the commons sits beside it — same derivation ticket_path uses.
    commons = (Path(commons) if commons is not None
               else Path(CAIRN_ROOT).parent / "CairnCommons")
    for raw in str(reason).split():
        token = raw.strip("'\"`.,;:()[]{}")
        if not token:
            continue
        if "/" in token or token.endswith((".py", ".json", ".md", ".sh")):
            p = Path(token).expanduser()
            if p.is_absolute() and p.exists():
                return True
            if (repo / token).exists() or (commons / token).exists():
                return True
        if (commons / "tickets" / f"{token}.json").exists():
            return True
        if (repo / "bin" / "cmd" / token).exists():
            return True
    return False


def buildme_rides_the_sorted(ticket: str, *, tickets_root: Path | None = None) -> list[dict]:
    """Green (empty findings) iff the cast ticket names its /sorted door firing — either
    a readable berth for skill ``sorted``, or the ``none, because <X>`` exemption whose
    reason carries a resolvable referent.

    The third leg of the sorted door (ticket sorted-becomes-a-learning-block): without
    this, the door is policy — a cast that skipped it files a ticket no gate ever
    questions. Red returns ONE finding naming the ticket, what was wanted and what was
    found — complete on the first pass, nothing to re-run. Census at install
    (2026-08-03): 76 tickets, 0 carrying the field, 30 at or before BUILDME — each
    rides the exemption or its own next crossing, never edited ambiently.
    """
    from cairn.machines.skill_block.skill_block import read_berth

    root = tickets_root if tickets_root is not None else _TICKETS_ROOT
    filed = ticket_path(ticket, root=root)
    if filed is None:
        return []
    try:
        doc = json.loads(Path(filed).read_text())
    except (OSError, json.JSONDecodeError):
        # The chokepoint's own refusal already covers an unreadable ticket; two sieves
        # reporting one fault is noise at the diagnostic surface.
        return []

    berth = doc.get("sorted_berth") if isinstance(doc, dict) else None
    why = (
        "Ticket sorted-becomes-a-learning-block (2026-08-03): the cast rides a door, so "
        "a partial cast survives on disk instead of dying with the context (Law 1) and "
        "the completeness answers are a record, not a memory. A ticket that cannot name "
        "its /sorted firing was cast around the door. Disposition: fire the cast packet "
        "through skills/sorted/door.py and put the printed berth path in the ticket's "
        "'sorted_berth', or record an explicit exemption "
        f"('{_EXEMPT_PREFIX}<why>' — the why must carry a resolvable referent: a path, "
        "a cast ticket id, or a roster command) — silence is the one answer that is "
        "not legal."
    )

    if berth is None:
        return [_finding(
            "buildme_rides_the_sorted", ticket,
            "ticket %r names no /sorted door firing — no 'sorted_berth' field at all" % ticket,
            {"ticket": ticket, "ticket_file": str(filed), "found": None,
             "wanted": "a 'sorted_berth' path to a berthed /sorted firing, or "
                       f"'{_EXEMPT_PREFIX}<why>'"},
            why,
        )]

    if not isinstance(berth, str) or not berth.strip():
        return [_finding(
            "buildme_rides_the_sorted", ticket,
            "ticket %r carries an empty or non-string 'sorted_berth'" % ticket,
            {"ticket": ticket, "ticket_file": str(filed), "found": berth,
             "wanted": "a berth path, or " + f"'{_EXEMPT_PREFIX}<why>'"},
            why,
        )]

    exempt = _EXEMPT_RE.match(berth)
    if exempt:
        reason = berth[exempt.end():].strip()
        if not reason:
            return [_finding(
                "buildme_rides_the_sorted", ticket,
                "ticket %r claims a /sorted exemption with no reason after "
                "'%s'" % (ticket, _EXEMPT_PREFIX),
                {"ticket": ticket, "ticket_file": str(filed), "found": berth},
                "An exemption whose reason is blank is silence with a prefix on it. " + why,
            )]
        if not reason_has_referent(reason):
            return [_finding(
                "buildme_rides_the_sorted", ticket,
                "ticket %r claims a /sorted exemption whose reason points at nothing "
                "checkable" % ticket,
                {"ticket": ticket, "ticket_file": str(filed), "found": berth,
                 "wanted": "a reason carrying a resolvable referent — a path on disk, "
                           "a cast ticket id, or a roster command (bin/cmd/<name>)"},
                "A plausible sentence a later reader cannot go verify is the hollow pass "
                "the sorted door was built against (opus-pass rank 3). " + why,
            )]
        return []

    doc_berth = read_berth(berth)
    if doc_berth is None:
        return [_finding(
            "buildme_rides_the_sorted", ticket,
            "ticket %r names a /sorted berth that does not read: %s" % (ticket, berth),
            {"ticket": ticket, "ticket_file": str(filed), "sorted_berth": berth,
             "found": "missing or unparseable"},
            "A berth path that resolves to nothing is state reported from records — the "
            "gate would be passing on a promise. " + why,
        )]

    if doc_berth.get("skill") != "sorted":
        return [_finding(
            "buildme_rides_the_sorted", ticket,
            "ticket %r names a berth for skill %r, not 'sorted'"
            % (ticket, doc_berth.get("skill")),
            {"ticket": ticket, "ticket_file": str(filed), "sorted_berth": berth,
             "found_skill": doc_berth.get("skill")},
            "The gate reads which skill actually fired, not which one the field is named "
            "after — otherwise any berth at all would satisfy it. " + why,
        )]

    return []


# ── THE EXIT GATE (ticket proved-answers-the-chart, 2026-07-29) ──────────────
# The loop's other hand: the entry gate above demands a chart EXISTS before a
# build begins; this demands the chart is ANSWERED before the voyage may close.
# A claimed cast ticket crossing forward into PROVED must show a verdict
# artifact (cairn/machines/chart/verdict.py — the ONE validator, shared with the deposit
# face) in which every criterion of the claiming validate berth carries a run
# verdict with outcome pass, and every hypothesis of the chain is dispositioned
# confirmed-or-killed with the deciding observation.
#
# Deliberately NOT in SIEVES, same measured reason as the entry gate: the
# promotion sweep has no crossing context and would retro-red every component
# whose voyages predate the chart chain. Jurisdiction is ONE crossing's own
# claimed ticket; called from the emit chokepoint's PROVED entry, exactly as the
# entry check is called from its BUILDME entry and the census from its PROVEME
# exit. An UNCLAIMED ticket passes ungated (v0 — inherits the entry gate's
# jurisdiction, charter edge (k)).
#
# Provenance: installed 2026-07-29 on Akien's word ("agreed and go!" — the exit
# half of the 64%-stake trust transfer). Retires the sail steps' narrated done
# into physics at the close (Law 4; the 2026-07-24 correction as schema).


def proved_answers_the_chart(ticket: str, *, berths_root: Path | None = None) -> list[dict]:
    """Green (empty findings) iff no chart claims ``ticket``, or a readable
    verdict artifact answers the claiming chart completely (every criterion
    passing, every hypothesis dispositioned).

    Red returns findings complete on the first pass — one naming each unanswered
    item, or one naming the missing/malformed artifact — nothing to re-run.
    """
    root = Path(berths_root) if berths_root is not None else _CHART_BERTHS
    # THE ONE LATEST-CLAIMER RULE, composed (ticket the-deposit-rides-the-read):
    # this gate's private glob loop retired into cairn.machines.chart.verdict, where the
    # crossing's deposit-enqueue reads it too — one implementation, two mouths.
    claiming = claiming_packets(ticket, "validate", berths_root=root)
    artifacts = claiming_packets(ticket, "verdict", berths_root=root)
    if not claiming:
        return []  # unclaimed — ungated (v0 jurisdiction, inherited from the entry gate)
    disposition = ("Disposition: run the claiming validate berth's criteria by their "
                   "instruments, write the verdict artifact through "
                   "cairn.machines.chart.verdict.write_verdict, deposit it, then cross again.")
    if not artifacts:
        return [_finding(
            "proved_answers_the_chart", ticket,
            "no verdict artifact answers the chart claiming ticket %r — the voyage "
            "is closing on narration" % ticket,
            {"ticket": ticket, "searched": str(root),
             "claiming": [str(p) for p, _ in claiming],
             "wanted": "*/packets/verdict-*.json with a 'ticket' field naming this ticket"},
            "Law 3 + Law 4: PROVED asserts done, and done is verified in the world by "
            "the instrument, never the narration. " + disposition)]
    path, artifact = artifacts[-1]  # the latest answer is the one that stands
    err = verdict_error(artifact)
    if err:
        return [_finding(
            "proved_answers_the_chart", ticket,
            "the verdict artifact is malformed — %s" % err,
            {"ticket": ticket, "artifact": str(path)},
            "A verdict without its instrument and evidence is narration wearing a "
            "filename (Law 7: loud at the surface, permanent in the record). " + disposition)]
    if artifact.get("validate_ref") not in {str(p) for p, _ in claiming}:
        return [_finding(
            "proved_answers_the_chart", ticket,
            "the verdict artifact answers a chart that does not claim this ticket "
            "(validate_ref %r is not a claiming berth)" % artifact.get("validate_ref"),
            {"ticket": ticket, "artifact": str(path),
             "claiming": [str(p) for p, _ in claiming]},
            "An answer to someone else's chart answers nothing here (Law 6: the claim "
            "and its answer share an owner). " + disposition)]
    return [_finding(
        "proved_answers_the_chart", ticket,
        item,
        {"ticket": ticket, "artifact": str(path),
         "validate_ref": artifact["validate_ref"]},
        "Law 3 as the close: an unanswered claim leaves the voyage a hypothesis, and "
        "a hypothesis may not rest at PROVED. " + disposition)
        for item in unanswered(artifact)]


# The mesh, verbatim from the component's own proof-time seat (inference_domain/proofs/
# test_host.py) — one rule, two moments. OUTBOUND ONLY, matched on the full dotted name:
# a module that can DIAL is a potential door; one that can only LISTEN is not.
# ``only`` is relative to the inspection root (the cairn package dir), not the repo.
_SOLE_PATH = {
    "kind": "sole_path",
    "capability": "the inference host",
    "modules": ("urllib.request", "urllib.error", "http.client", "requests", "httpx",
                "aiohttp", "socket", "ftplib", "telnetlib"),
    "only": "inference_domain/",
}


def sole_path_holds(row: dict, comp_dir: Path) -> list[dict]:
    """A component other than inference_domain imports a module that can DIAL.

    Provenance: ruling 2026-08-08-inference-proxy-is-a-rules-stack, item 1, verbatim: "ALL
    CALLS GO THRU INFERENCY PROXY ... NO OTHER REACHING FOR INFERENCE VIA ANY OTHER
    MECHANISM IS ALLOWED. THAT NEEDS TO BE IN THE BUILD INSPECTION." The mesh predates the
    ruling — inference_domain/proofs/test_host.py shakes the same rule over the whole REPO
    (floor 20) at that component's proof time; this seat is the same rule at the OTHER
    moment: every component, every inspection (the ruling's words, made a roster fact).

    Scope: this sieve judges the component tree under the inspection root; the repo-wide
    sweep (skills/, bin/) stays with the proof-time mesh. The graph is re-walked per firing
    rather than cached — a cache keyed by root would go stale between a proof's seeded
    fixtures (measured while building the seeded tooth, not guessed). Known residue
    (CLAUDE.md): a subprocess that dials and a dynamic import are invisible to both seats
    — that IOU stays named, not closed here.
    """
    graph = import_sieve.import_graph(str(comp_dir.parent))
    prefix = row["component"] + os.sep
    findings = []
    for caught in import_sieve.catches(graph, _SOLE_PATH, floor=1):
        path = caught.split(" imports ", 1)[0]
        if not path.startswith(prefix):
            continue          # another component's door reds THAT component's row
        findings.append(_finding(
            "sole_path_holds", row["component"],
            caught,
            {"rule": {k: v for k, v in _SOLE_PATH.items()}, "file": str(comp_dir.parent / path)},
            "Ruling 2026-08-08 item 1 / Law 6: the proxy alone reaches inference hosts; "
            "a second importer is a second door, and this seat makes it a build-time red."))
    return findings


# WHAT THE VERDICT MAY REACH — the second rule at this address, and a DIFFERENT question
# from the one above. _SOLE_PATH asks who may DIAL; this asks what the verdict path may
# ARRIVE AT, by any number of hops. The two do not cover each other, and that was measured
# rather than argued (2026-08-12): planting `import cairn.devices.inference_domain.route` into
# inspector.py leaves _SOLE_PATH GREEN — inference_domain is precisely the component that
# is allowed to dial — while the verdict path gains the ability to ask an LLM. A verdict
# is always hardware; a verdict that can reach a graph tree, a database or a host is a
# verdict with an opinion in it.
#
# WHY A CAPABILITY AND NOT AN ALLOWLIST. Until today this was a literal tuple of the
# modules inspector.py was ALLOWED to import, living in its own proof. Every legitimate
# new dependency had to be added to it by hand, and on 2026-08-08 one arrived that was not
# (`cairn.tools.base.nest`, in 047d633) — so the tooth read as holding while it was not. Naming
# the denied capability inverts the maintenance: the innocent never need a signature, and
# the set below only grows when a genuinely new capability is built. Its stability is what
# probes/does_the_denied_set_stay_put.py watches.
#
# `start` and the graph keys are REPO-relative; `modules` are dotted names as WRITTEN in
# source, so they keep their `cairn.` prefix regardless of where the scan is rooted.
_FIRE_PATH = {
    "kind": "unreachable",
    "capability": "a graph tree, a database, or a host that could answer",
    "modules": (
        "cairn.machines.chart.tree",        # the graph tree — a verdict may not consult one
        "cairn.devices.librarian",         # the same tree, by its other name
        "cairn.devices.db_domain",         # port 5432
        "cairn.devices.inference_domain",  # the inference/embedding host, by its permitted door
        # and the network itself, for a path that dials without going through the door
        # above — _SOLE_PATH reds those inside cairn/, but the fire path can route through
        # skills/ and bin/, where it has no seat.
        "urllib.request", "urllib.error", "http.client", "requests", "httpx",
        "aiohttp", "socket", "ftplib", "telnetlib",
    ),
    "start": "cairn/machines/build_inspector/inspector.py",
}


def fire_path_unreachable(row: dict, comp_dir: Path) -> list[dict]:
    """Something the verdict path can reach imports a door that would let it ask.

    Provenance: ticket reachability-replaces-the-allowlist, which replaced the allowlist
    tuple in this component's own proof with the rule above. This is the same "one rule,
    two moments" shape as sole_path_holds — except there is no second moment to share
    with, because the fire path is a property of THIS component and the inspection is
    where it is asked.

    Scope, stated because it is NOT the same as the sieve above, and the difference was
    measured rather than assumed. The walk is always over the REAL repo, never the
    inspection root: the rule names one fixed file at one fixed address, there is no
    per-fixture variant of it, and a walk from a start the fixture never contained would
    raise rather than answer.

    And the finding is THIS component's, on every row but its own it returns immediately.
    sole_path_holds attributes to the file's owner because its constraint binds every
    component — everyone owes it not to open a second door. This constraint binds ONE
    PATH, and the path is ours; chart never agreed that what IT imports decides what a
    verdict may reach. So build_inspector's row carries the red, and the finding names the
    offending file and the whole route so the hand that must break the chain knows where
    to stand. The cost settles the same way (measured 2026-08-12): the answer does not
    vary by row, and computing it per row rebuilt a 243-file graph 24 times — 22 seconds
    added to every inspection, which timed out this component's own proof at 120s.

    Known residue, inherited whole from import_sieve and not closed here: a subprocess
    dials and imports nothing, and a dynamic import is invisible.
    """
    if row["component"] != "build_inspector":
        return []
    graph = import_sieve.import_graph(str(_REPO_ROOT))
    findings = []
    for caught in import_sieve.catches(graph, _FIRE_PATH):
        findings.append(_finding(
            "fire_path_unreachable", row["component"],
            caught,
            {"rule": {k: v for k, v in _FIRE_PATH.items()},
             "file": str(_REPO_ROOT / caught.split(" imports ", 1)[0])},
            "A verdict is always hardware (Law 3): a fire path that can reach a tree, a "
            "database or a host can return an opinion wearing a measurement's clothes. "
            "Break the import chain the finding names, or bring the new capability "
            "through Akien's gate — never widen the denied set to make this green."))
    return findings


SIEVES = {
    "charter_on_disk": charter_on_disk,
    "proofs_exist": proofs_exist,
    "silent_device": silent_device,
    "state_is_projection": state_is_projection,
    "forwarding_order_resolves": forwarding_order_resolves,
    "charted_refs_resolve": charted_refs_resolve,
    "constraint_traces": constraint_traces,
    "constraint_bounds_complete": constraint_bounds_complete,
    "survey_holdings_resolve": survey_holdings_resolve,
    "survey_coverage_complete": survey_coverage_complete,
    "decompose_composes_holdings": decompose_composes_holdings,
    "decompose_builds_absences": decompose_builds_absences,
    "triage_covers_the_split": triage_covers_the_split,
    "triage_reasons_the_order": triage_reasons_the_order,
    "hypothesize_covers_the_ranked": hypothesize_covers_the_ranked,
    "hypothesize_falsifiable_measured": hypothesize_falsifiable_measured,
    "validate_measures_done": validate_measures_done,
    "validate_covers_the_build": validate_covers_the_build,
    "sole_path_holds": sole_path_holds,
    "fire_path_unreachable": fire_path_unreachable,
}


_NEST_CACHE: list | None = None


def the_nest() -> list:
    """The sieves assembled coarsest-first, as [(band, [sieve names]), ...].

    BANDS ARE SCAFFOLDING, NOT THE SPEC (Akien, 2026-08-11, ruling
    2026-08-11-a-sieve-is-one-true-false-rule): "a seive is something that evaluates to
    true based on whatever it's inspecting. it's specific to the device being inspected
    and provides a true false ruling." No bands, no ladder, no ordering are part of what
    a sieve IS — SIEVES below is the real structure, and each entry is one boolean about
    one component. Bands were CC's ("we added bands and ordering because you thought you
    needed it. I DONT") and remain only by leave to remain ("i do not think the existing
    stuff needs to go"), which does not extend to growing them. Do not read the
    2026-08-06/08-07 citations below as him asking for this; he ruled on an object CC
    put in front of him. See cairn/tools/base/nest.py's header for the full note.

    DERIVED, NEVER AUTHORED (ticket the-questions-are-the-sieve, and its first
    falsifier): each sieve's band comes from what its own body REACHES — is the answer
    in hand, on local disk, spread across local sources, or off this box — read out of
    this module's source by import_sieve. A hand-set band would be exactly the learned
    value stranded in a human's head that the derivation exists to end, and it would go
    stale silently the first time a sieve started reaching further.

    A BAND SEQUENCES, IT NEVER FORBIDS (Akien, 2026-08-06). The off-box band is empty
    today; that is a MEASUREMENT over the sieves that exist, not a rule that one may not
    be built. There are already two hosts, and four laptops once ran this system
    overnight against local models — 'will we do that? I don't know. but we CAN.'
    """
    global _NEST_CACHE
    if _NEST_CACHE is None:
        reaches = import_sieve.reach_of(Path(__file__).read_text())
        _NEST_CACHE = base_nest.nest(
            {name: reaches.get(fn.__name__, 0) for name, fn in SIEVES.items()})
    return _NEST_CACHE


def inspect(*, root: Path | None = None, component: str | None = None) -> dict:
    """Shake the nest over the measured census. One component (post-build) or the whole
    tree (the one-time sweep). Findings are judgments over measurements only.

    ONE SHAKE (ruling 2026-08-06-a-stack-of-sieves-is-a-nest): every sieve in the nest
    runs once, coarse band first, and nothing is fired-read-and-refired. What comes out
    is a GRADATION — a score per sieve per component — rather than a pass/fail, and the
    findings are the detail behind the zeroes.
    """
    root = root or (_REPO_ROOT / "cairn")
    census = device_census(root=root)  # refuses bad roots loudly — inherited, not re-built
    rows = census["measured"]["components"]
    if component is not None:
        rows = [r for r in rows if r["component"] == component]
        if not rows:
            raise ScanRefused(
                f"inspect: no component {component!r} under {root} — the census sees "
                f"{[r['component'] for r in census['measured']['components']]}. A gate "
                "that silently inspects nothing passes everything (Law 8)."
            )
    nest = the_nest()
    # The shake is the general half (cairn.tools.base.nest, since 2026-08-07); what stays
    # here is the tenant's convention — which sieve meets which subject, and how:
    # SIEVES[name](row, comp_dir). Binary scores, absence-not-a-third-value, and the
    # min() roll-up are the general side's contract now, stated at its berth.
    shaken = base_nest.shake(
        nest,
        {row["component"]: row for row in rows},
        lambda name, row: SIEVES[name](row, root / row["component"]),
    )
    return {
        "inspector": "build_inspector",
        "scope": component or "whole-repo sweep",
        "components_inspected": len(rows),
        "sieves_run": sorted(SIEVES),
        "nest": [{"band": b, "band_name": base_nest.BAND_NAMES[b], "sieves": names}
                 for b, names in nest],
        # The vector Akien drew, one per component: [1.0, 1.0, 0.0, 1.0, 1.0] = 0.0.
        "gradation": shaken["gradation"],
        "component_scores": shaken["roll_up"],
        "findings": shaken["findings"],
        "clean": not shaken["findings"],
    }


def _main(argv: list[str]) -> int:
    report = inspect(component=argv[0] if argv else None)
    print(json.dumps(report, indent=2))
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
