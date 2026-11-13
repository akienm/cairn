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
from cairn.tools.chain.grammar import STAGE_AUTHORED_FIELDS
from cairn.tools.chain.grammar import (CAIRN_ROOT, INSTANCE_DIR, STRATA, component_roster, ticket_claim_error, common_shape_record, inspected, lacks_of, render_lacks, CHAIN_REMEDY, identity_lack)
from cairn.tools.tree.tree import deposit_learning

# codemother owns her learning (Akien 2026-11-05; ticket 2b3d842bc118): her leaves are codemother_<nexus>_nodes
OWNER = "codemother"

AUTHORED_FIELDS = STAGE_AUTHORED_FIELDS["constrain"]
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


# THE FLOOR READS SEALS; IT NEVER RUNS A PROOF (ticket 5243cf9dc630, orchestrator's ruling
# 2026-11-12). Until this ticket a proof without a standing seal was run, over the bus, by the
# tester, inside the chart stage. Measured 2026-11-12: b0e65cf8a77e's floor ran 44 proofs one
# after another (1858 s), the longest 1040.8 s, and every ask queued at the tester's one shim
# lock, so neither a longer wait (d58e7887cc99) nor parallel askers could bring a stage under
# its budget. A seal is the tester's verdict already read (Law 8: prove, then trust); where
# there is none standing, the floor says which state it is in and the build that owns the
# proof runs it. The run cache, its flock, the re-entrancy guard and the bus ask went with the
# run: each existed only because the floor ran proofs (history keeps them).


def _git_names(root: str, args: list) -> list | None:
    """Repo-relative paths one git command prints, or None when git cannot answer here."""
    import subprocess
    try:
        out = subprocess.run(["git", "-C", root] + args, capture_output=True, text=True,
                             timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def _changed_under(abs_path: str, seal: dict, root: str):
    """The files under a moved seal that git says changed since it was sealed, or ``None``
    when git cannot name them (``root`` is not the top of a repository).

    THE FILES ARE THE SEAL'S OWN, never a guess: the import closure it recorded when that
    closure names this proof (the rule ``sealed_fingerprint_now`` applies), otherwise the
    component directory the directory recipe hashed. A seal records one digest and no
    per-file hashes, so the changed set is read from git: commits since the seal's date that
    touch those files, plus what the working tree holds uncommitted or untracked there, kept
    to the files the recipe hashes."""
    top = _git_names(root, ["rev-parse", "--show-toplevel"])
    if not top or os.path.realpath(top[0]) != os.path.realpath(root):
        return None
    rel = os.path.relpath(abs_path, root)
    closure = (seal.get("evidence") or {}).get("fingerprint_closure")
    if isinstance(closure, list) and rel in closure:
        paths, hashed = sorted(set(closure)), set(closure)
    else:
        paths, hashed = [os.path.relpath(os.path.dirname(os.path.dirname(abs_path)), root)], None
    changed = set()
    since = seal.get("date")
    if isinstance(since, str) and since:
        logged = _git_names(root, ["log", "--since=%s" % since, "--name-only", "--format=",
                                   "--"] + paths)
        if logged is None:
            return None
        changed.update(logged)
    status = _git_names(root, ["status", "--porcelain", "--untracked-files=all", "--"] + paths)
    if status is None:
        return None
    for line in status:
        changed.add(line[3:].split(" -> ")[-1].strip().strip('"'))
    # the directory recipe hashes every *.py under the component and nothing else, so a
    # seal file or a note changing beside the code is not what moved the fingerprint
    return sorted(p for p in changed if (p in hashed if hashed is not None else p.endswith(".py")))


def _read_instrument(rel_path: str, root: str = CAIRN_ROOT) -> dict:
    """The state ONE discovered instrument is in RIGHT NOW, read from its seal.

    Four states and one absence, every one a sentence from ``standing`` or from git:

      - ``green``: sealed green and the fingerprint matches the working tree;
      - ``red``: the standing seal is not green — it was measured and did not pass;
      - ``moved``: sealed green and the code has moved under it; ``changed`` names the files;
      - ``never-sealed``: the tester has not spoken about this code;
      - ``missing``: discovered, then not on disk.

    Only ``green`` is a bound the build can be judged against, and each other state rides out
    of ``floor_packet`` as an unknown. A state the floor cannot read is never green.
    """
    abs_path = os.path.join(root, rel_path)
    if not os.path.isfile(abs_path):
        return {"verdict": "missing",
                "how": "no file at %s — it was discovered and then was not there, so there "
                       "is no seal to read" % rel_path}
    from cairn.tools.base.validation import standing
    try:
        st = standing(abs_path)
    except Exception as e:                                   # an unreadable seal, not a green
        return {"verdict": "unreadable", "how": "the seal on %s could not be read (%s: %s)"
                % (rel_path, type(e).__name__, e)}
    seal = st.get("seal")
    if st.get("proven"):
        return {"verdict": "green", "how": "read from the standing seal: %s" % st.get("why")}
    if not isinstance(seal, dict):
        return {"verdict": "never-sealed", "how": st.get("why")}
    if seal.get("verdict") != "green":
        return {"verdict": "red", "how": st.get("why")}
    changed = _changed_under(abs_path, seal, root)
    named = ("git names no file changed since the seal" if changed == [] else
             "git cannot name the changed files here" if changed is None else
             "changed since the seal: %s" % ", ".join(changed))
    return {"verdict": "moved", "how": "%s; %s" % (st.get("why"), named), "changed": changed}


def discovered_instruments(intent_ref: str, root: str = CAIRN_ROOT, *, tickets_dir=None) -> list:
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

    A CLAIMED CHART DISCOVERS IN ITS OWN COMPONENT ONLY (ticket b0e608f34ccb, RULE 1). Measured
    2026-10-05: b312ff041558's constrain stage, a one-file tester build, discovered 70 proofs
    across 6 components because every ref'd component contributed its proofs. A ticket's proofs
    measure only its own component, so when the orient berth claims a ticket, discovery reads
    the component whose charter is that ticket's ``owning_intention``; the other refs stay
    context (charter constraints) and contribute no instruments. An owner outside class-space
    (a commons-berthed intention) has no proofs here. A claimless chart has no owner to read
    and discovers across its refs as before. ``tickets_dir`` is the proof's seam onto a fixture
    store (``grammar.ticket_path``'s own keyword, the reader the claim door uses).
    """
    from cairn.tools.base.validation import discover

    orient_packet = _read_orient_berth(intent_ref)
    tid = orient_packet.get("ticket")
    if isinstance(tid, str) and tid:
        return _owned_instruments(tid, root, tickets_dir, discover)
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


def _owned_instruments(tid: str, root: str, tickets_dir, discover) -> list:
    """The proofs of the component that owns ticket ``tid``: the directory of its
    ``owning_intention`` charter under ``root``. An unresolved ticket or an owner with no
    charter in class-space discovers nothing (the door refuses an unfiled claim upstream)."""
    from cairn.tools.chain.grammar import ticket_path
    found = ticket_path(tid, root, None if tickets_dir is None else str(tickets_dir))
    if found is None:
        return []
    try:
        with open(found, encoding="utf-8") as fh:
            owner = json.load(fh).get("owning_intention")
    except (OSError, ValueError):
        return []
    if not isinstance(owner, str) or not owner:
        return []
    charter = os.path.join(root, owner)
    if not os.path.isfile(charter):
        return []
    out = set()
    for path in discover([os.path.dirname(charter)]):
        try:
            out.add(str(path.relative_to(root)))
        except ValueError:
            continue
    return sorted(out)


def instrument_constraints(intent_ref: str, root: str = CAIRN_ROOT) -> tuple:
    """The check-kind constraints and this firing's own cost — the node's whole payoff.

    A constraint here says what will REFUSE this build and what state it is in, so the
    builder stops looking those up by hand. It is not a briefing: a floor that listed
    check names without reading their seals would be the charter prose again, one
    indirection further out, which is the first hollow pass the ticket names.

    THE SOURCE IS THE PROOF PATH, repo-relative, because ``constraint_traces`` resolves a
    source through the berth gate's ref semantics and nothing else. That judge refused
    this very build's chart packet earlier today over six sources spelled relative to the
    wrong root; the spelling is its answer, not this module's.
    """
    instruments = discovered_instruments(intent_ref, root)
    constraints = []
    started = time.monotonic()
    for rel in instruments:
        state = _read_instrument(rel, root)
        constraints.append({
            "text": "%s judges this build and is %s right now (%s)"
                    % (rel, state["verdict"], state["how"]),
            "source": rel,
            "kind": "check",
            "verdict": state["verdict"],
        })
    cost = {
        "instruments": len(instruments),
        "seconds": round(time.monotonic() - started, 3),
        "note": "this firing's own cost, measured rather than estimated: seals read, no "
                "proof run (ticket 5243cf9dc630)",
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
        if c["verdict"] != "green":
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
    right.

    THIS RUNS AT THE WRITE DOOR ONLY (ticket 4c022c44de53, 2026-09-10). It used to run at
    the deposit door as well, and the charters the floor reads get reworded — so 293 of
    348 berthed constrain packets were refused at that door for a label this door had
    itself derived. Asking a stored label whether the floor still agrees is a question
    about the world, not about the sender."""
    prov = packet.get("provenance") or {}
    wrong = {f: (prov[f], measured.get(f)) for f in FLOOR_AUTHORED
             if f in prov and prov[f] != measured.get(f)}
    if wrong:
        raise ConstrainRefused(
            "constrain refuses a packet that declares its own provenance for %s — those "
            "are DERIVED at the door by re-running the floor over the packet's own "
            "'intent_ref' and comparing, and a field earns 'floor' only when the floor's "
            "answer can be REPRODUCED. Declared vs measured: %s. Leave those keys out — "
            "this door writes them."
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
            # and it costs nothing extra — discovery is the glob half, and the floor
            # reads seals rather than running proofs.
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


def validate_constrain(packet: dict, root: str = CAIRN_ROOT, *,
                       measure_provenance: bool = True) -> dict:
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

    # PROVENANCE IS MEASURED AT THE WRITE DOOR AND READ AT THE DEPOSIT DOOR — the same
    # position orient settled on one stage up, and for the same reason. The switch chooses
    # where the label COMES FROM; it never chooses whether the gate runs, and the gate
    # below runs on both paths.
    #
    # Measuring asks a packet arriving from outside whether it earned the label it wrote.
    # Asked again at the deposit door it becomes a different question, because the floor
    # reads TODAY's charters and TODAY's tree: a charter is reworded, a ref moves, and the
    # floor's answer changes underneath a berth that was measured honestly last week.
    # Measured before this build, 293 of 348 berthed constrain packets were refused at the
    # deposit door for a label their own write door had derived and stamped.
    #
    # In place rather than on a copy because /chart calls write_constrain(p) and then
    # deposit_constrain(p, ...) with the SAME object — a copy would berth the measured
    # provenance and hand the caller back a packet this very door would then refuse.
    if measure_provenance:
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
    instance-space beside orient's packets. Returns the path.

    MEASURES provenance: this is the door a packet arrives at from outside, so the
    floor-authored labels are re-derived here and a sender that declares them wrongly is
    refused."""
    validate_constrain(packet, root=root, measure_provenance=True)
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


def _refuse_provenance_the_berth_does_not_carry(packet: dict, berth_path: str) -> None:
    """THE READ DOOR'S ANCHOR (2026-09-10, ticket 4c022c44de53) — the same anchor orient
    holds one stage up, for the same reason. Once the deposit door reads the label instead
    of re-deriving it, only the berth can say what the write door actually stamped; without
    this, a caller could pass a real berth path beside a forged provenance."""
    try:
        with open(os.path.expanduser(berth_path), encoding="utf-8") as fh:
            berthed = json.load(fh)
    except (OSError, ValueError) as err:
        raise ConstrainRefused(
            "deposit_constrain: berth %r could not be read back (%s) — the deposit reads "
            "its provenance from the berth rather than re-measuring it, so an unreadable "
            "berth leaves the label unanchored" % (berth_path, err))
    if (berthed.get("provenance") or {}) != (packet.get("provenance") or {}):
        raise ConstrainRefused(
            "deposit_constrain: the packet's provenance is not the one the berth carries. "
            "The deposit door READS this label rather than measuring it, so it must be the "
            "label the write door stamped: berth %r carries %r, the packet carries %r."
            % (berth_path, berthed.get("provenance"), packet.get("provenance")))


def deposit_constrain(packet: dict, vector, *, berth_path: str, root: str = CAIRN_ROOT,
                      conn=None) -> dict:
    """The deposit-back: the bounds become the constrain tree's memory of this
    class of request — the next similar request walks to its settled bounds
    instead of re-deriving them (Law 1 as the brick's runtime). Gate before seed;
    the berth must exist on disk.

    READS the packet's stored provenance rather than re-measuring it: the label on a
    berthed packet was derived by ``write_constrain`` and belongs to this door, not to
    the sender. The gate still runs in full here, so a stored provenance that is missing
    a key, fails to cover the authored fields, or names an unknown stratum is refused."""
    validate_constrain(packet, root=root, measure_provenance=False)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise ConstrainRefused(
            "deposit_constrain: berth %r does not exist on disk — a node whose "
            "provenance points at nothing is fabricated attribution one layer up" % (berth_path,))
    _refuse_provenance_the_berth_does_not_carry(packet, berth_path)
    content = constrain_node_content(packet)
    provenance = {
        "source": berth_path,
        "intent_ref": packet["intent_ref"],
        "confidence": packet["confidence"],
    }
    return deposit_learning("constrain", content, vector, provenance, owner=OWNER, conn=conn)
