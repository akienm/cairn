"""build_inspector — the post-build gate. Python filters; new failure, new filter.

Akien's ruling, 2026-07-27, verbatim: "the next thing is a post build inspector (also in
python with FILTERS) that can catch these kinds of things. we find a new thing, we add a
new filter. can also be a seperate, command line only inference free operation to run it
on the whole repo once built. we should only ever have to do that once."

THE CONTRACT
  - A FILTER judges a MEASUREMENT — it reads orient's census rows and the component's
    files, never a narration about them. Inference-free by construction: there is no
    deepen seam here at all; a gate that consults an oracle is not a gate.
  - Every filter carries PROVENANCE: the failure that seeded it (the learning device,
    same shape as orient's scans — proofs refuse a filter nobody was taught by).
  - A FINDING is complete on first pass (I-complete-diagnostic-on-first-pass): what
    was measured, why it matters, which law — never "run again for details".
  - "ONLY ONCE" BY CONSTRUCTION: the whole-repo sweep brings the existing tree up to
    the gate one time; after that, every build runs the inspector on its component and
    the sweep can never be needed again. Wanting a second sweep IS a finding — it
    means some build bypassed the gate.

CLI (inference-free):
  python3 -m cairn.build_inspector.inspector            # the whole-repo sweep
  python3 -m cairn.build_inspector.inspector <component>  # post-build, one component
Exit 0 = clean, 1 = findings — gate-able by anything that can read an exit code.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# Deliberate reuse, on the record: orient's scans are the measuring layer under these
# filters (device_census feeds every row-judging filter). This is the first evidence on
# orient's filed edge (e) — scans-vs-filters as one shared library — earned by use, not
# merged on symmetry. The registries stay separate: a scan MEASURES, a filter JUDGES.
from cairn.charter import projector  # noqa: E402
from cairn.chart.orient import ref_exists  # noqa: E402  (tree-free module — the verdict
#   path stays structurally unable to reach tree machinery; the packet jurisdiction
#   composes the berth gate's OWN ref semantics so the two mouths cannot disagree)
from cairn.orient.orient import ScanRefused, device_census  # noqa: E402


def _finding(filter_name: str, component: str, finding: str, evidence, why: str) -> dict:
    return {
        "filter": filter_name,
        "component": component,
        "finding": finding,
        "evidence": evidence,
        "why_it_matters": why,
    }


# ── the founding filters — one per failure that seeded it ────────────────────


def charter_on_disk(row: dict, comp_dir: Path) -> list[dict]:
    """A component with code but no intention+why.json beside it.

    Provenance: 2026-07-27 — orient's census's FIRST real run flagged orient itself
    (charter_on_disk: False); the charter got written because the instrument refused
    its absence. 'A component without an intention doesn't run' (CLAUDE.md) was prose
    until this filter; now a build that skips the charter reds the gate.
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
    (``self.emit`` — receiver checked), after two components passed this filter on
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
        "This filter is the enforcement half of that 2026-07-14 claim.",
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


def _unreadable_findings(filter_name: str, row: dict, unreadable) -> list[dict]:
    if row["component"] != "chart":
        return []  # the berth owner carries the finding, exactly once per sweep
    return [_finding(
        filter_name, row["component"],
        "berthed packet %s is unreadable" % path.name,
        {"berth": str(path), "why": why},
        "Law 7: a record the gate cannot read is a named finding, never a silent "
        "skip — an unreadable chart could be hiding any claim.",
    ) for path, why in unreadable]


def charted_refs_resolve(row: dict, comp_dir: Path) -> list[dict]:
    """A promoted build must still match what its packet charted: every ref the
    orient packet carried must resolve at promotion time.

    Provenance: 2026-07-24 — 'done' reported while the files stood unmoved (the
    sharpest claim-vs-world drift on record). The packet is the claim, the
    promotion is the moment, this filter is the comparison — through the berth
    gate's own ref semantics (cairn.chart.orient.ref_exists), so the judge and
    the gate that admitted the refs cannot disagree.
    """
    packets, unreadable = _charted_packets(comp_dir, "orient")
    findings = _unreadable_findings("charted_refs_resolve", row, unreadable)
    for path, packet in packets:
        refs = packet.get("refs")
        if not isinstance(refs, list):
            continue  # shaped at the berth door; unreachable through it
        missing = [r for r in refs if not isinstance(r, str) or not ref_exists(r)]
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
# mouths: the door refuses at berth time, these filters re-judge at promotion.


def judge_constrain(packet: dict) -> list[dict]:
    """The pure judge over ONE constrain packet — fragments tagged by which filter
    owns them ({judge, finding, evidence, why_it_matters}). Composed by the berth
    door and wrapped by the gate filters below; if the two mouths ever disagree,
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
    stage's filters pass their own judge fn; growing a parallel wrapper per stage
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
    ('we set up it's inspector filters first') — the failure predates the module,
    so tooth 10 holds: this filter was taught by a real, dated failure.
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
    """The pure judge over ONE survey packet — fragments tagged by owning filter.
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
    """
    return _judge_charted(row, comp_dir, "survey", judge_survey,
                          "survey_holdings_resolve", report_unreadable=True)


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
    filter. A decomposition derives from the chain or it is invented: a
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


FILTERS = {
    "charter_on_disk": charter_on_disk,
    "proofs_exist": proofs_exist,
    "silent_device": silent_device,
    "state_is_projection": state_is_projection,
    "charted_refs_resolve": charted_refs_resolve,
    "constraint_traces": constraint_traces,
    "constraint_bounds_complete": constraint_bounds_complete,
    "survey_holdings_resolve": survey_holdings_resolve,
    "survey_coverage_complete": survey_coverage_complete,
    "decompose_composes_holdings": decompose_composes_holdings,
    "decompose_builds_absences": decompose_builds_absences,
}


def inspect(*, root: Path | None = None, component: str | None = None) -> dict:
    """Run every filter over the measured census. One component (post-build) or the
    whole tree (the one-time sweep). Findings are judgments over measurements only."""
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
    findings = []
    for row in rows:
        comp_dir = root / row["component"]
        for name, judge in FILTERS.items():
            findings.extend(judge(row, comp_dir))
    return {
        "inspector": "build_inspector",
        "scope": component or "whole-repo sweep",
        "components_inspected": len(rows),
        "filters_run": sorted(FILTERS),
        "findings": findings,
        "clean": not findings,
    }


def _main(argv: list[str]) -> int:
    report = inspect(component=argv[0] if argv else None)
    print(json.dumps(report, indent=2))
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
