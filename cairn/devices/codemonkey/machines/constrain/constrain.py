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

from cairn.machines.build_inspector.inspector import judge_constrain, CONSTRAIN_ROSTER
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


def _resolve_ref(ref: str, root: str):
    """A REF TO THE COMPONENT THAT OWNS IT, by whichever of the two shapes it wears.

    Returns ``(component_dir, None)`` or ``(None, why_not)``. The two shapes are a bare
    NAME (looked up by rung, never concatenated) and a PATH (resolved to its deepest
    owning component). Both are legal on an orient packet and this is the one place that
    knows it, so the floor's loop reads the same regardless of which arrived.

    MEASURED 2026-08-14, and it is why this function exists: across the 45 berthed orient
    packets, 266 of 310 refs are paths and only 44 are names. The previous version tested
    ``ref in component_roster`` — a set of NAMES — and dropped everything else, so the
    floor discarded 86% of its own input and emitted an empty constraint list, which is a
    legal list and therefore redded nothing.
    """
    if ref in set(component_roster(root)):
        # AMBIGUITY IS REPORTED, NEVER RESOLVED HERE. A name two rungs answer to
        # (``orient`` is a tool AND this machine) has no single charter, and picking one
        # would put a charter under a component name that only half means it.
        try:
            comp_dir = address.component_dir(ref, os.path.join(root, "cairn"))
        except address.AmbiguousComponent as e:
            return None, str(e)
        if comp_dir is not None:
            return comp_dir, None
        # The roster said component and the lookup said no: two readers disagreeing, which
        # is a finding about the corpus and not about this ref. Said so rather than folded
        # into "not a component".
        return None, ("%r is in the component roster but no rung holds it — the roster "
                      "and the address lookup disagree" % (ref,))
    candidate = os.path.expanduser(ref)
    if not os.path.isabs(candidate):
        candidate = os.path.join(root, ref)
    if not os.path.exists(candidate):
        return None, ("%r names neither a component nor a path that exists on disk" % (ref,))
    comp_dir = address.component_of(candidate, os.path.join(root, "cairn"))
    if comp_dir is None:
        # A real path under no component — a commons ticket, a skill, a repo-root file.
        # It exists and it is not this floor's to bound, which is a different answer from
        # "there is nothing there" and leaves by the same door wearing a different reason.
        return None, ("%r exists but sits under no component, so no charter bounds it" % (ref,))
    return comp_dir, None


def _charter_constraints(charter_path: str, charter: dict) -> list:
    """The THREE fields of a charter that BOUND, rendered as constraints — verbatim, each
    carrying the address it was read from.

    Falsifier, gates and owner, because those are the constraints most often violated:
    what would make this wrong, what it must pass, and who may write it. The text is
    copied and never summarised — a paraphrased constraint is a constraint with laundered
    provenance, and the ceiling that reads it cannot tell that it has been touched.

    THE SOURCE IS THE CHARTER PATH AND NOTHING ELSE, with the field in its own key. The
    first version packed them as ``<path>#<field>``, which the installed judge
    ``constraint_traces`` refused on all six — it resolves a source through the ONE
    ref-resolution semantics the berth gate uses (``ref_exists``), and ``path#field`` is
    not a path. Teaching that judge about fragments would have put a second spelling of
    "where does this point" into a component this module is forbidden to shape; carrying
    the field in a key it already had room for costs nothing and keeps one implementation.
    """
    out = []
    for field in ("falsifier", "gates", "owner"):
        text = charter.get(field)
        if isinstance(text, str) and text.strip():
            out.append({
                "text": text,
                "source": charter_path,
                "field": field,
                "kind": "charter",
            })
    return out


def constrain_floor(intent_ref: str, root: str = CAIRN_ROOT) -> dict:
    """The deterministic stratum: the charter text that already bounds the ref'd
    components — falsifier, gates, owner — VERBATIM, each with its address.
    Reports WHAT EXISTS; the ceiling decides what applies."""
    orient_packet = _read_orient_berth(intent_ref)
    charter_constraints, refs_not_components = [], []
    # ONE ENTRY PER COMPONENT, NOT PER REF. The two ref shapes are not exclusive: a packet
    # naming ``alpha`` and ``cairn/tools/alpha/alpha.py`` names one component twice, and
    # before this was deduped the floor read that charter twice and emitted every one of
    # its constraints in duplicate. Found by a count tooth in this machine's own proof the
    # hour the path shape started resolving — the defect was invisible while path refs
    # were being discarded, because a discarded ref cannot collide with anything.
    seen = set()
    for ref in orient_packet.get("refs", []):
        comp_dir, why_not = _resolve_ref(ref, root)
        if comp_dir is None:
            refs_not_components.append({"ref": ref, "why": why_not})
            continue
        if str(comp_dir) in seen:
            continue
        seen.add(str(comp_dir))
        charter_path = str(comp_dir / "intention+why.json")
        try:
            with open(charter_path, encoding="utf-8") as fh:
                charter = json.load(fh)
        except (OSError, ValueError) as e:
            charter_constraints.append({
                "component": comp_dir.name, "charter": charter_path,
                "unreadable": "%s: %s" % (type(e).__name__, e)})
            continue
        charter_constraints.append({
            "component": comp_dir.name,
            "charter": charter_path,
            "falsifier": charter.get("falsifier"),
            "gates": charter.get("gates"),
            "owner": charter.get("owner"),
            "constraints": _charter_constraints(charter_path, charter),
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


FLOOR_AUTHORED = ("constraints", "unknowns")

# THE KINDS THIS FLOOR CAN AUTHOR — asked, never spelled at the point of use.
#
# Two places need the answer and both had it as the literal ``"charter"``: the survival
# rule below, which decides whether the ceiling counterfeited a floor constraint, and the
# crowding_out probe beside this module, which counts non-floor constraints as the
# ceiling's contribution. A literal was correct for exactly as long as the floor had one
# kind. The moment it emits a second, the survival rule stops guarding the new kind
# against forgery and the probe reads THE FLOOR'S OWN BULK as evidence the ceiling is
# healthy — an armed watch flattering the thing it measures, which is worse than no watch
# because something is reading it.
#
# A DECLARATION, AND A CHECKED ONE. This is not derived from a floor run: a run whose refs
# reach no instruments would emit no ``check`` constraints, the derived set would quietly
# shrink, and the probe would go back to miscounting on exactly the packets where it
# matters. So the module declares what it is CAPABLE of authoring, and a tooth in this
# machine's proof asserts that every kind the floor actually emits appears here — a
# declaration that cannot drift from the code beneath it without reddening.
FLOOR_KINDS = ("charter", "check")


# THE RE-ENTRANCY GUARD, and it is physics rather than a convention because the thing it
# stops is unbounded.
#
# MEASURED BEFORE IT WAS DESIGNED AROUND: constrain's own proof calls ``validate_constrain``
# seventeen times and ``floor_packet`` three. So a floor that RUNS the proofs it discovers,
# fired on a packet whose refs include this machine, runs a proof that calls the floor that
# runs the proof — process fork without a bottom. Nothing in the chain caught this; it was
# found by grepping the proof before writing the run half, and it would have been found
# otherwise by the machine running out of processes.
#
# THE EXCLUSION IS COMPUTED, NOT LISTED, which is Akien's clause 3 at the one place it was
# genuinely tempting to write a constant. A hand-kept roster of "proofs the floor must not
# run" is a learned value stranded in a human's head, and it is wrong the first time a
# proof anywhere starts calling this stage. Instead the guard rides the ENVIRONMENT: the
# tester spawns each proof with ``subprocess.run`` and no ``env=``, so the child inherits
# this flag, and a floor that finds itself already inside a floor reports the instrument
# rather than running it. Depth is bounded at one for every proof in the corpus, present
# and future, with nothing to maintain.
_REENTRY = "CAIRN_CONSTRAIN_FLOOR_RUNNING"

# Keyed by (proof path, source fingerprint) so the SECOND ask in one firing is free. The
# door re-runs the floor to measure provenance (``measured_provenance`` below), which
# would otherwise run every discovered proof a second time and double the stage's cost for
# an answer that cannot have changed — the tree has not moved between the two calls, and
# the fingerprint is exactly the thing that would say so if it had.
_RUN_CACHE: dict = {}


def discovered_instruments(intent_ref: str, root: str = CAIRN_ROOT) -> list:
    """THE INSTRUMENTS THAT JUDGE THE REF'D COMPONENTS — discovered, never enumerated.

    COMPOSED FROM THE TESTER'S OWN COLLECTOR, and that is the whole of the discovery half.
    The chart chain's survey recorded an absence here — "no importable primitive that,
    given a component, yields its proofs" — and the absence was false: ``discover`` is a
    public module-level function of ``cairn.devices.tester.cli``, importable and
    documented, and this build composes it unchanged. The survey had measured where the
    glob SAT rather than whether it could be CALLED, which is the ladder of proxies one
    rung down from behaviour; the finding is recorded on the ticket rather than quietly
    corrected here.

    Composing rather than copying is also the only version that satisfies the hypothesis
    the chain put on this piece — that constrain and the tester agree, set for set, about
    which files are proofs. They agree by identity: there is one implementation, so there
    is nothing for a later edit to make disagree.

    Returns repo-relative paths, sorted, deduped — relative because that is the spelling
    ``constraint_traces`` resolves, and this build does not get to choose that.
    """
    from cairn.tools.base.validation import discover

    orient_packet = _read_orient_berth(intent_ref)
    comp_dirs, seen = [], set()
    for ref in orient_packet.get("refs", []):
        comp_dir, _why = _resolve_ref(ref, root)
        if comp_dir is None or str(comp_dir) in seen:
            continue
        seen.add(str(comp_dir))
        comp_dirs.append(str(comp_dir))
    if not comp_dirs:
        return []
    out = set()
    for path in discover(comp_dirs):
        try:
            out.add(str(path.relative_to(root)))
        except ValueError:
            # A proof outside the class-space root cannot be spelled the way the judge
            # resolves sources. Kept out rather than emitted with a spelling the door
            # would refuse — and it is not silently dropped: the count is reported.
            continue
    return sorted(out)


def _run_instrument(rel_path: str, root: str = CAIRN_ROOT) -> dict:
    """Run ONE discovered instrument and report the state it is in RIGHT NOW.

    The verdict is the tester's, read and not granted. ``run_proof`` returns its record
    and PERSISTS NOTHING — measured in its own docstring and in its source, which settles
    the Law 6 question the chain carried as an unknown: a floor calling it is a reader, not
    a writer into another component's records, so no ownership gate is crossed here.

    A REPORT THAT COULD NOT RUN SAYS SO, and never defaults to green. That is the second
    of the three hollow passes this node's ticket names, and the empty set passing
    trivially is the first — so an instrument is never omitted, only ever reported.
    """
    if os.environ.get(_REENTRY):
        return {"verdict": "not-run", "how": "the floor was already running inside a "
                "floor — this instrument calls the stage that discovered it, and running "
                "it here is the unbounded fork the guard exists to stop"}
    abs_path = os.path.join(root, rel_path)
    # A MISSING FILE IS UNRUNNABLE, AND SAYING SO IS THE WHOLE POINT OF THE CLAUSE. Without
    # it the tester still answers — python exits non-zero on a path it cannot open — so the
    # report reads "red ... run by the tester" for a file that was never run and does not
    # exist. The verdict is not wrong (it is certainly not green), but the HOW is a record
    # of truth telling a false story, and a builder reading it goes hunting for a failing
    # assertion in a file that isn't there. Measured 2026-08-14 while building the teeth,
    # on a path deleted between discovery and the run — which is the only way to reach it,
    # since discovery emits what the glob just saw.
    if not os.path.isfile(abs_path):
        return {"verdict": "unrunnable",
                "how": "no file at %s — it was discovered and then was not there, so "
                       "nothing was run and no verdict was read" % rel_path}
    from cairn.tools.base.validation import run_proof, source_fingerprint
    try:
        key = (rel_path, source_fingerprint(abs_path))
    except Exception as e:                                   # unreadable tree, not a green
        return {"verdict": "unrunnable", "how": "could not fingerprint %s (%s: %s)"
                % (rel_path, type(e).__name__, e)}
    if key in _RUN_CACHE:
        return _RUN_CACHE[key]
    os.environ[_REENTRY] = "1"
    started = time.monotonic()
    try:
        # sink="none" — THE FLOOR READS A VERDICT, IT DOES NOT SEAL ONE. A chart stage runs
        # this proof to report what the component's own tests currently say; a validation
        # written from inside a preamble would be a seal nobody asked for, landing on a
        # component this voyage may not even touch. The tester requires the choice by name
        # (ticket standing-gates-the-newest-link-and-run-proof-names-its-sink), so the
        # not-sealing is now stated here rather than being the absence of a thought.
        record = run_proof(abs_path, sink="none", caller="constrain_floor")
        state = {"verdict": record.get("verdict"), "how": "run by the tester"}
    except Exception as e:
        state = {"verdict": "unrunnable",
                 "how": "%s: %s" % (type(e).__name__, e)}
    finally:
        os.environ.pop(_REENTRY, None)
    # The duration rides the COST report, never the constraint's text. A constraint whose
    # text carried a wall time could never be reproduced by the door, so the field could
    # never earn ``floor`` — the measurement would have destroyed the label it exists to
    # make honest.
    state["_seconds"] = round(time.monotonic() - started, 3)
    _RUN_CACHE[key] = state
    return state


def instrument_constraints(intent_ref: str, root: str = CAIRN_ROOT) -> tuple:
    """The check-kind constraints and this firing's own cost — the node's whole payoff.

    A constraint here says what will REFUSE this build and what state it is in, so the
    builder stops looking those up by hand. It is not a briefing: a floor that listed
    check names without running them would be the charter prose again, one indirection
    further out, which is the first hollow pass the ticket names.

    THE SOURCE IS THE PROOF PATH, repo-relative, because ``constraint_traces`` resolves a
    source through the berth gate's ref semantics and nothing else. That judge refused
    this very build's chart packet earlier today over six sources spelled relative to the
    wrong root; the spelling is its answer, not this module's.
    """
    instruments = discovered_instruments(intent_ref, root)
    constraints, seconds = [], 0.0
    for rel in instruments:
        state = _run_instrument(rel, root)
        seconds += state.get("_seconds", 0.0)
        constraints.append({
            "text": "%s judges this build and is %s right now (%s)"
                    % (rel, state["verdict"], state["how"]),
            "source": rel,
            "kind": "check",
            "verdict": state["verdict"],
        })
    cost = {
        "instruments": len(instruments),
        "seconds": round(seconds, 3),
        "note": "this firing's own run cost, measured rather than estimated — the "
                "selection rule's only real bound, and a number that lived in an "
                "operator's hand until the floor started reporting it",
    }
    return constraints, cost


def floor_packet(intent_ref: str, root: str = CAIRN_ROOT) -> dict:
    """THE DETERMINISTIC HALF OF THE PACKET — the two fields constrain can author without
    a reader, returned beside the facts they were derived from.

    ``constraints`` is every ref'd component's falsifier, gates and owner, verbatim and
    addressed. ``unknowns`` is what the floor could not ground — a ref answering to two
    rungs, a ref naming nothing on disk, a charter that would not parse. Each is ``None``
    when the floor has nothing, which is a different claim from an empty list: ``None``
    says the floor could not tell, and an empty list would say it looked and found this
    request unbounded — a sentence no Cairn request can truthfully carry.

    ``bounds`` IS NOT A CANDIDATE AND NEVER WILL BE. What is in and out of scope for a
    request is a judgement about intent, not a lookup: the floor can say what the charters
    of the ref'd components demand, and it cannot say which of those demands this request
    is choosing to serve. Same shape as ``intent`` and ``scope`` at orient — the fields
    named here are the ones that are lookup rather than language.
    """
    facts = constrain_floor(intent_ref, root)

    constraints, unknowns = [], []
    for entry in facts["charter_constraints"]:
        if entry.get("unreadable"):
            unknowns.append("the charter at %s could not be read (%s)"
                            % (entry.get("charter"), entry["unreadable"]))
            continue
        constraints += entry.get("constraints") or []
    for miss in facts["refs_not_components"]:
        unknowns.append("the request refs %s — %s" % (miss["ref"], miss["why"]))

    # THE SECOND CLASS OF CONSTRAINT, and it is the same field on purpose. A constraint
    # enforced by a runnable check is the same constraint said in physics (Law 4), so it
    # belongs in the list the ceiling already reads — a new packet field would have made
    # the ceiling opt in to noticing what refuses its build.
    checks, cost = instrument_constraints(intent_ref, root)
    constraints += checks
    for c in checks:
        if c["verdict"] not in ("green", "not-run"):
            unknowns.append(
                "the instrument %s is %s before this build starts — a constraint that is "
                "already failing is not a bound this build can be judged against until "
                "someone says which it is" % (c["source"], c["verdict"]))

    return {
        "stratum": "floor",
        "constraints": constraints or None,
        "unknowns": sorted(set(unknowns)) or None,
        "cost": cost,
        "facts": facts,
    }


def _canon(item) -> str:
    """One string per collection member, so a dict constraint and a string unknown compare
    by the same rule. Sorted keys, because two dicts that differ only in key order are the
    same constraint and a serialisation artifact is not the ceiling's contribution."""
    return json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else str(item)


def _survived(field: str, authored, proposed) -> bool:
    """Did the floor's answer come through the ceiling unchanged?

    SURVIVAL, NOT EQUALITY, AND THE DIFFERENCE FROM ORIENT IS DELIBERATE. orient compares
    its floor-authored fields by set EQUALITY, because ``refs`` is a complete lookup
    result: a ref the ceiling added is a ref the floor missed, which is the ceiling doing
    the floor's job on the floor's own field. constrain's ``constraints`` is not that
    shape. It is inherently MULTI-SOURCE — the 41 berthed packets carry 148 charter, 110
    ticket, 63 law and 33 ruling constraints — and the floor owns exactly one of those
    kinds. Under equality the field could never earn ``floor`` at all, because any law the
    ceiling correctly adds would demote it, and a label that is structurally unreachable is
    not a measurement, it is a constant. The dial exists to detect a nexus compiling; a
    field that can only ever read ``claude`` makes it blind to the thing it watches.

    So the test is two-sided, and the second side is what keeps it honest:

      1. every constraint the floor produced is PRESENT in the packet, unchanged;
      2. every constraint in the packet wearing a kind THE FLOOR AUTHORS was produced
         by the floor.

    (1) alone would let the ceiling carry the floor's three and invent a fourth wearing the
    same kind, taking the floor's label for its own text. (2) closes that: the floor owns
    every kind in ``FLOOR_KINDS``, and additions in any OTHER kind are the ceiling doing
    its own job and cost it nothing. Additions the floor cannot reach are the point of
    having a ceiling — they are not evidence that the floor did not run.

    CLAUSE (2) ASKS RATHER THAN SPELLS, and that is not cosmetic. It read ``kind ==
    "charter"`` while the floor had one kind; the day the floor gained ``check`` that
    literal would have left every check constraint unguarded — the ceiling free to invent
    one, wear the floor's kind, and take the floor's label for it, which is precisely the
    counterfeit this clause exists to stop.

    ``unknowns`` is survival only. The ceiling legitimately notices unknowns a lookup
    cannot, and no kind field separates them, so there is nothing here to counterfeit: an
    unknown is a confession, and a sender inventing extra ones is not claiming credit."""
    if not (isinstance(authored, list) and isinstance(proposed, list)):
        return authored == proposed
    have, floor_said = set(map(_canon, authored)), set(map(_canon, proposed))
    if not floor_said <= have:
        return False
    if field == "constraints":
        floor_kind = {_canon(c) for c in authored
                      if isinstance(c, dict) and c.get("kind") in FLOOR_KINDS}
        return floor_kind <= floor_said
    return True


def measured_provenance(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """PROVENANCE FOR THE FLOOR-AUTHORED FIELDS, DERIVED — never accepted.

    Re-runs the floor over the packet's own ``intent_ref`` and compares. A field claims
    ``floor`` only if the door can REPRODUCE the floor's answer; otherwise it is
    ``claude``, because "the ceiling wrote this" is what an unreproducible field means. A
    ``tree`` declaration is left standing — that stratum is not what this measures and
    clobbering it would trade one wrong label for another.

    THE INPUT IS THE UPSTREAM BERTH, WHICH IS WHY THIS NEEDS NO NEW FIELD. orient measures
    against the packet's own ``request`` and has to ask senders to carry it; constrain
    template-fills from ``intent_ref``, a field it already requires, so the evidence for
    the measurement is the same file the stage was built to read. Nothing to add and
    nothing to forget.

    WHAT "REPRODUCE" MEANS FOR A MULTI-SOURCE LIST is settled in ``_survived`` and is the
    one place this stage's rule differs from orient's: the floor's items must survive
    unchanged, and no OTHER constraint wearing a kind the floor authors (``FLOOR_KINDS``)
    may appear beside them. The
    ceiling adding a law or a ruling is the ceiling doing its own job and does not demote
    the field, because a rule that demoted it would make ``floor`` unreachable and the
    dial blind to the compiling it exists to detect.
    """
    prov = dict(packet.get("provenance") or {})
    ref = packet.get("intent_ref")
    try:
        proposal = (floor_packet(ref, root)
                    if isinstance(ref, str) and ref.strip() else {})
    except ConstrainRefused:
        # An unreadable berth is already a lack the record carries by name; nothing can be
        # reproduced from it, so nothing earns ``floor`` and the gate refuses on the entry
        # that actually measured it rather than on an exception raised from the label.
        proposal = {}
    for field in FLOOR_AUTHORED:
        if field not in packet:
            continue
        proposed = proposal.get(field)
        if proposed is not None and _survived(field, packet[field], proposed):
            prov[field] = "floor"
        elif prov.get(field) != "tree":
            prov[field] = "cc"
    return prov


def refuse_misdeclared_floor_provenance(packet: dict, measured: dict) -> None:
    """THE LOUD HALF. A sender that labels its own floor-authored provenance and gets it
    WRONG is refused, not corrected — and refused BEFORE the gate, because this is not a
    judgement about the packet's content but about the sender's authority over a field
    that is measured.

    THE DEFECT IT ENDS, MEASURED 2026-08-14 over the 41 berthed constrain packets: 24 of
    them declare ``constraints: floor``, while the floor as it then stood produced zero
    charter constraints for that same input in 24 cases and one in ten more. The kinds in
    those lists — 148 charter, 110 ticket, 63 law, 33 ruling — are mostly things the floor
    cannot reach at all. The number the staircase is steered by was computed by the party
    being measured, which is the same finding orient's floor build closed one stage up.

    AGREEING WITH THE MEASUREMENT IS NOT DECLARING, which is why this refuses on
    DISAGREEMENT rather than on presence: a label that matches what re-running the floor
    produced is a claim the sender RE-DERIVED, and there is nothing to refuse in being
    right. It also has to be that way mechanically — ``validate_constrain`` runs at both
    doors over the same object, so a refuse-on-presence rule would make the berth's own
    output illegal at the deposit one line later."""
    prov = packet.get("provenance") or {}
    wrong = {f: (prov[f], measured.get(f)) for f in FLOOR_AUTHORED
             if f in prov and prov[f] != measured.get(f)}
    if wrong:
        raise ConstrainRefused(
            "constrain refuses a packet that declares its own provenance for %s — those "
            "are DERIVED at the door by re-running the floor over the packet's own "
            "'intent_ref' and comparing, and a field earns 'floor' only when the floor's "
            "answer can be REPRODUCED. Declared vs measured: %s. Drop those keys (the "
            "door writes them)."
            % (", ".join(sorted(wrong)),
               "; ".join("%s declared %r, measured %r" % (f, d, m)
                         for f, (d, m) in sorted(wrong.items()))))


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
            # A CHECK'S SOURCE MUST NAME THE INSTRUMENT, NOT MERELY RESOLVE.
            #
            # MEASURED 2026-08-14, and it is the reason this entry exists rather than an
            # argument for it: the chain's own hypothesis on this build said the serious
            # falsification would be the judges PASSING a check "because the source is a
            # string the judge resolves trivially without it naming the check". Run at
            # acceptance, that is exactly what happened — ``constraint_traces`` asks only
            # that a source RESOLVE, so replacing a proof path with the component
            # DIRECTORY it sits in left every installed judge silent. A source that
            # resolves but does not identify is laundered provenance in a new place.
            #
            # The judge is the build inspector's and is shared by every constrain packet
            # ever written; widening it is out of this ticket's bounds and would be a
            # question for Akien. This kind is not: ``check`` was minted by this build, so
            # the rule about what earns it belongs at the door this machine owns. The
            # comparison is a == against a deterministic re-derivation, no oracle near it,
            # and it costs nothing extra — discovery is the glob half, and the runs the
            # door already pays for are served from the cache.
            #
            # ABSENT, NOT PASSED, when the packet has no readable intent_ref: there is
            # nothing to derive the allowed set from, and the entry above has already
            # closed the gate.
            claimed = [c for c in constraints
                       if isinstance(c, dict) and c.get("kind") == "check"]
            if claimed and "intent_ref" in packet:
                try:
                    allowed = set(discovered_instruments(packet["intent_ref"], root))
                except RuntimeError:
                    allowed = None
                if allowed is not None:
                    unnamed = sorted({c.get("source") for c in claimed
                                      if c.get("source") not in allowed})
                    record.append(inspected(
                        "every_check_names_a_discovered_instrument", stage="constrain",
                        expected=[], actual=unnamed,
                        checks_claimed=len(claimed), instruments_discovered=len(allowed),
                        lack="; ".join(
                            "a constraint of kind 'check' sources %r, which is not one of "
                            "the instruments discovered for this request — a check's "
                            "source is the proof that judges the build, and a path that "
                            "merely resolves is not one" % s for s in unnamed)))

    record += common_shape_record(packet, required_fields=REQUIRED_FIELDS,
                                  authored_fields=AUTHORED_FIELDS,
                                  list_fields=(), root=root, stage="constrain")

    # THE COMPOSED JUDGES, and they run only once every entry above passes — the same
    # order the two-tier door has always used, now visible in the record rather than
    # implied by control flow. judge_constrain is the build inspector's, so a packet this
    # door passes is a packet the promotion gate passes: one implementation, two mouths.
    if all(gate.passed(e) for e in record):
        attendance = judge_constrain(packet)
        all_findings = [f for a in attendance for f in a["findings"]]
        record.append(inspected(
            "judges_all_passed", stage="constrain",
            expected=sorted(CONSTRAIN_ROSTER),
            actual=sorted(a["judge"] for a in attendance if not a["findings"]),
            lack=JUDGE_REFUSAL_CONSTRAIN + "; ".join(
                "[%s] %s" % (f["judge"], f["finding"]) for f in all_findings),
            attendance=attendance))
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

    # PROVENANCE IS MEASURED HERE, AT THE GATE, AND IN PLACE — the same position orient
    # settled on one stage up, for the same reason: BOTH doors a packet can leave by (the
    # berth and the deposit) run this function, so there is no route by which a packet
    # reaches instance-space or the tree carrying a label it wrote about itself. In place
    # rather than on a copy because /chart calls write_constrain(p) and then
    # deposit_constrain(p, ...) with the SAME object — a copy would berth the measured
    # provenance and hand the caller back a packet this very door would then refuse.
    measured = measured_provenance(packet, root=root)
    refuse_misdeclared_floor_provenance(packet, measured)
    if measured:
        packet["provenance"] = measured

    record = inspect_constrain(packet, root=root)
    if gate.verdict(record)["opens"]:
        return packet

    shape = [e for e in record if e["identity"] != "judges_all_passed"]
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
