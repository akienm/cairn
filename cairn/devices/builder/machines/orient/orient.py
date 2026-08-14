"""orient — stage 1 of the chart chain, and a MACHINE of its own since 2026-08-13:
ground the request before anything else runs.

WHY A MACHINE. Akien's ruling: "orient is a machine. the other pre-build steps are each
their own machine." And the shape earns the word — a machine is tools plus the glue that
holds them together, and this file is exactly that: the ORIENT INSTRUMENT
(``cairn/tools/orient``, deterministic scans) plus the CHAIN GRAMMAR
(``cairn/tools/chain``) plus the glue that turns a request into stage 1's packet. The
machine and the tool it composes share the name ``orient`` on purpose; that is what the
rung says about them.

WHAT LEFT THIS FILE, and why it was never orient's. Until 2026-08-13 this module also
carried the chain's shared grammar — the roster, ref resolution, ticket claims, the
common shape lacks. Eight of the nine other legs imported orient, and NOT ONE of them
touched ``floor_facts`` or ``validate_orient``: they took only the grammar. Stage 1
looked load-bearing for the whole chain and was not; the coupling was authorship order
(orient was written first, so the shared parts landed in it). The grammar now berths in
``cairn/tools/chain/grammar.py`` and orient imports it like every other leg.

The first question nexus of the pre-build preamble (charter: ./intention+why.json;
ticket: CairnCommons/tickets/chart-orient.json). It answers ONE narrow question:
"what is actually being asked, and where does it live?" — and emits the smallest
typed artifact that fully determines what downstream nexi need.

THE FLOOR DOES NOT SCAN THE TERRITORY ITSELF. The settled owner of prebuild
measurement is the ORIENT INSTRUMENT (cairn/tools/orient — deterministic scans, born
2026-07-27), and this nexus's floor COMPOSES it: the component roster is derived
from ``device_census`` rows, never from a parallel scan. That line is written in
blood: this file's first cast carried its own charter-glob roster, and the nexus's
FIRST LIVE FIRE caught it — the floor reported ``orient`` as a component, its
builder had never surveyed for one, and cairn/tools/orient/ was sitting there proven,
one day old (Law 1 re-derivation; premature convergence n=3, this time caught by
the machinery built to stop it).

Three strata, tried cheapest-first (v0 ships two; the tree stratum is a filed stone):

  FLOOR   (this file + the orient instrument) — deterministic: parse the request,
          verify that every referenced path/component/skill EXISTS. The floor
          reports WHAT EXISTS; it never decides WHAT APPLIES — that judgment
          belongs to the loop above.
  TREE    (filed) — the nexus's graph tree via the librarian's tools.
  CEILING (the /chart skill) — the mini agentic loop that actively assembles the
          packet from floor facts; never a bare lookup.

The exit artifact is the orient packet: intent / domain / scope / refs / unknowns /
confidence / provenance. PROVENANCE IS PER-FIELD (floor|tree|claude). The schema
gate (validate_orient) is the append-door pattern: a packet that cannot fill its
shape refuses loudly, and an INVENTED ref (one the floor cannot verify exists)
refuses — downstream must never receive a pointer to nothing.

THE FLOOR AUTHORS, AND PROVENANCE IS MEASURED (2026-08-14, ticket
orient-floor-authors-and-provenance-is-measured). Until this build the floor emitted
FACTS and the ceiling wrote every packet field by hand — including the field that says
which stratum wrote it. Measured over all 45 berthed orient packets: ``domain`` was
labelled ``floor`` in 18 of them and 14 of those floor-labelled values were over 200
characters of prose; ``refs`` was labelled ``floor`` in 44 while the SELECTION was
always the ceiling's. So the dial read orient at 0.40 floor and that 0.40 was a
SELF-REPORT — the one number Akien steers the staircase by, computed by the party being
measured. Two things change here and the second is what makes the first honest:

  1. ``floor_packet`` AUTHORS the three fields that are lookup rather than language —
     ``refs`` (paths it verified, plus the directories of components and skills it
     matched), ``domain`` (the addresses and their rung, derived from where those refs
     actually sit), ``unknowns`` (what it could NOT ground). It authors nothing it
     cannot ground: an ambiguous component name is an unknown, never a guessed ref.
  2. THE SENDER MAY NOT WRITE PROVENANCE FOR THOSE THREE. The door derives it by
     re-running the floor over the packet's own ``request`` and comparing, and a field
     may claim ``floor`` only if the door can REPRODUCE the floor's answer. A sender
     that declares one and gets it wrong is REFUSED, not corrected — the label is not
     the sender's to write, and correcting it quietly would leave a sender that still
     believes it labels its own work. It lives in ``validate_orient``, which is the
     only route to both the berth and the deposit, so there is no door left open.

The evidence the door needs is the request, so a packet that carries ``request`` can
earn ``floor`` and one that does not cannot: with nothing to reproduce, the honest
reading is ``claude``. That is deliberately an incentive rather than a new required
field — 45 berthed packets predate this and none of them is retroactively malformed.

Not a token-cost argument, and the charter says so at length: Claude is cached (ruling
2026-08-14-the-preamble-compiles-to-learn-not-to-be-cheap). A floor that authors makes
the answer REUSABLE and makes the next rung's evidence real — the preamble's ceiling is
becoming Hex, whose failovers DEPOSIT, and "what did the floor already answer" has to
be a fact before "what did the ceiling have to add" can be one.

Packets are runtime state and berth in instance-space (~/.cairn/devices/chart/0/);
the durable memory is the tree (filed stone). No clocks, no daemons: orient runs
only when /chart is invoked.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

from cairn.tools.gate import gate
from cairn.tools.tree.tree import deposit_learning
from cairn.tools.chain.grammar import (CAIRN_ROOT, INSTANCE_DIR, AmbiguousComponent,
                                       _ref_exists, common_shape_record, component_home,
                                       component_roster, inspected, lacks_of,
                                       render_lacks, skill_roster)

AUTHORED_FIELDS = ("intent", "domain", "scope", "refs", "unknowns")
REQUIRED_FIELDS = AUTHORED_FIELDS + ("confidence", "provenance")

# '+' rides the class because the house's own charter filenames carry it (intention+why.json)
_PATHISH = re.compile(r"[\w~./+-]*/[\w./+-]*[\w/]")
# The trailing lookahead is what keeps ``/home/akien/...`` from reading as the slash-verb
# ``/home``. It cost nothing while the only consumer filtered against the installed skill
# roster (no skill is called "home"); it became load-bearing on 2026-08-14, when the floor
# started reporting the roster's COMPLEMENT — an unmatched verb is now an unknown, so a
# false verb match is a fabricated unknown rather than a silently dropped one.
_SLASH_VERB = re.compile(r"(?<!\S)/([a-z][\w-]*)(?![\w/-])")
_WORD = re.compile(r"[a-z0-9_]+")


class OrientRefused(RuntimeError):
    """The loud refusal — a packet or request that cannot be grounded says so."""


def floor_facts(request: str, root: str = CAIRN_ROOT) -> dict:
    """The deterministic stratum: everything about the request that is lookup,
    parsing, and existence-checking wearing the costume of reasoning.

    Reports only WHAT EXISTS (found vs missing kept separate, never merged);
    the ceiling decides what applies. A census refusal (ScanRefused on a
    nonexistent world) propagates loudly — a floor over nowhere must not
    report a clean empty roster."""
    text = str(request)
    if not text.strip():
        raise OrientRefused("orient refuses an empty request — there is nothing to ground")

    words = set(_WORD.findall(text.lower()))
    roster = component_roster(root)
    components = [c for c in roster if c.lower() in words]

    skills = skill_roster(root)
    slashes = set(_SLASH_VERB.findall(text))
    verbs = sorted(slashes & set(skills))
    # EVERY slash-verb, not only the installed ones — a token the request wrote as a verb
    # is a verb claim whether or not the skill exists, and letting the uninstalled ones
    # fall through to the path scan reported ``/nosuchskill`` twice: once as a missing
    # skill and once as a missing path. Two unknowns, one fact.
    verb_tokens = {"/" + v for v in slashes}

    paths_found, paths_missing = [], []
    for tok in _PATHISH.findall(text):
        if tok in verb_tokens:
            continue  # a known slash-verb is a skill mention, not a path claim
        # THE SAME EXISTENCE RULE THE GATE USES, deliberately, and it was not before:
        # this scan checked absolute-or-root-relative while ``inspect_orient`` refuses an
        # unverifiable ref through ``_ref_exists``, which ALSO resolves against
        # CairnCommons. Two rules meant a commons path (``tickets/foo.json``) read as a
        # missing path here and as a perfectly good ref one door later — the floor
        # manufacturing an unknown about a file the gate could see. One mouth.
        if _ref_exists(tok, root, roster):
            paths_found.append(tok)
        else:
            paths_missing.append(tok)

    # THE COMPLEMENT IS A FACT TOO, and it was missing until 2026-08-14. ``verbs`` above
    # keeps only the slash-verbs that ARE installed skills; the ones that are not are
    # exactly what the floor could not ground, and dropping them silently meant the floor
    # measured a thing and then threw the negative half away (Law 7: found and missing
    # stay separate, never merged — the same rule ``paths_found``/``paths_missing``
    # already followed one line down).
    return {
        "stratum": "floor",
        "request": text,
        "components_mentioned": components,
        "skills_mentioned": verbs,
        "skills_missing": sorted(slashes - set(skills)),
        "paths_found": sorted(set(paths_found)),
        "paths_missing": sorted(set(paths_missing)),
        "roster_size": len(roster),
    }


# The packet fields the floor can author, because each is lookup rather than language.
# ``intent`` and ``scope`` are NOT here and are not candidates: restating an ask in
# grounded terms and drawing an in/out line are the two things that need a reader.
FLOOR_AUTHORED = ("refs", "domain", "unknowns")


def _repo_relative(path, root: str) -> str | None:
    """A ref INSIDE the repo is written repo-relative, because an absolute one stops
    resolving the moment anything is checked out anywhere else. Returns ``None`` for a
    path outside the root — and outside is a real answer rather than a failure: Akien's
    design papers live in ``~/.akien/``, so a ref there is legitimately absolute and
    rewriting it relative would produce ``../../..``, a pointer that is worse than the
    one it replaced."""
    try:
        rel = os.path.relpath(os.path.realpath(str(path)), os.path.realpath(root))
    except ValueError:  # different drive/root; not a ref this repo can carry
        return None
    return None if rel == ".." or rel.startswith(".." + os.sep) else rel


def _rung(ref: str) -> tuple[str, str] | None:
    """WHERE A REF SITS ON THE COMPLEXITY AXIS, read off its address and nothing else.

    This is the whole of ``domain``'s derivation, and the reason it can be derived at all
    is that CLAUDE.md made the axis an ADDRESS: tools -> machines -> devices -> device
    instances, each rung a directory segment. A held part is named as held ("machine
    orient, held by device builder") rather than flattened, because the holder is the
    thing that owns and gates it (Law 6) and a domain that hides the holder hides the
    owner. Returns (address, rung) or None for an address off the axis."""
    parts = [p for p in ref.split("/") if p]
    if not parts:
        return None
    if parts[0] == "CairnCommons":
        return ("CairnCommons", "commons")
    if parts[0] == "skills" and len(parts) > 1:
        return ("skills/" + parts[1], "skill")
    if parts[:2] == ["cairn", "tools"] and len(parts) > 2:
        return ("/".join(parts[:3]), "tool")
    if parts[:2] == ["cairn", "machines"] and len(parts) > 2:
        return ("/".join(parts[:3]), "machine")
    if parts[:2] == ["cairn", "devices"] and len(parts) > 2:
        if len(parts) > 4 and parts[3] in ("machines", "tools"):
            held = "machine" if parts[3] == "machines" else "tool"
            return ("/".join(parts[:5]), "%s held by device %s" % (held, parts[2]))
        return ("/".join(parts[:3]), "device")
    return None


def floor_packet(request: str, root: str = CAIRN_ROOT) -> dict:
    """THE DETERMINISTIC HALF OF THE PACKET — the three fields orient can author without
    a reader, returned beside the facts they were derived from.

    Each value is ``None`` when the floor has nothing, and that is the honest answer
    rather than a hollow one: an empty ``domain`` string would satisfy the schema and
    tell a downstream stage that orient looked and found the request placeless, which is
    a different claim from "the floor could not tell". A ``None`` here means the ceiling
    authors that field and provenance will say so.

    IT AUTHORS NOTHING IT CANNOT GROUND. The sharp case is the homonym, and it is the
    one this nexus's first live fire was born from: ``orient`` answers to two rungs (the
    tool and this machine). ``component_dir`` refuses that ambiguity loudly instead of
    picking, so an ambiguous name becomes an UNKNOWN — the floor says "I found this name
    twice and cannot tell which you meant", which is a measurement, where a guessed ref
    would be a fabrication wearing the floor's provenance."""
    facts = floor_facts(request, root)

    # A path the request wrote absolutely but that sits inside the repo is rewritten
    # relative; one that sits outside is kept exactly as written (see _repo_relative).
    refs, unknowns = [], []
    for tok in facts["paths_found"]:
        expanded = os.path.expanduser(tok)
        rel = _repo_relative(expanded, root) if os.path.isabs(expanded) else None
        refs.append(rel or tok)
    for name in facts["components_mentioned"]:
        try:
            home = component_home(name, root)
        except AmbiguousComponent as exc:
            # The homes, not the exception's sentence: that sentence is written for a
            # CALLER who can go say which, and this unknown is read by a ceiling that
            # cannot. It needs the two addresses and nothing else.
            homes = [_repo_relative(h, root) or str(h) for h in exc.homes]
            unknowns.append(
                "the request names %r, which answers to more than one rung (%s) — the "
                "floor will not guess which" % (name, ", ".join(sorted(homes))))
            continue
        if home:
            refs.append(home)
    refs += ["skills/" + s for s in facts["skills_mentioned"]]

    for tok in facts["paths_missing"]:
        unknowns.append("the request names a path that does not exist on disk: %s" % tok)
    for verb in facts["skills_missing"]:
        unknowns.append("the request names /%s, which is not an installed skill" % verb)

    refs = sorted(set(refs))
    homes = sorted({_rung(r) for r in refs} - {None})
    domain = "; ".join("%s (%s)" % (addr, rung) for addr, rung in homes) or None

    return {
        "stratum": "floor",
        "refs": refs or None,
        "domain": domain,
        "unknowns": sorted(set(unknowns)) or None,
        "facts": facts,
    }


def _survived(authored, proposed) -> bool:
    """Did the floor's answer come through the ceiling unchanged? Lists are compared as
    SETS because ``refs`` and ``unknowns`` are collections and not sequences — a reorder
    is not the ceiling adding knowledge, and calling it one would understate the floor by
    exactly the amount a cosmetic difference costs."""
    if isinstance(authored, list) and isinstance(proposed, list):
        return set(map(str, authored)) == set(map(str, proposed))
    return authored == proposed


def measured_provenance(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """PROVENANCE FOR THE FLOOR-AUTHORED FIELDS, DERIVED — never accepted.

    Re-runs the floor over the packet's own ``request`` and compares. A field claims
    ``floor`` only if the door can REPRODUCE the floor's answer; otherwise it is
    ``claude``, because "the ceiling wrote this" is what an unreproducible field means.
    A ``tree`` declaration is left standing — that stratum is not what this measures and
    clobbering it would trade one wrong label for another.

    THE REQUEST IS THE EVIDENCE, AND CARRYING IT IS OPTIONAL ON PURPOSE. With no
    ``request`` in the packet there is nothing to reproduce, so nothing can earn
    ``floor`` — an incentive to carry it rather than a new required field, which matters
    because 45 packets berthed before this build and none of them should become
    retroactively malformed (Law 7: a record of truth is not rewritten by a later rule).
    """
    prov = dict(packet.get("provenance") or {})
    request = packet.get("request")
    proposal = (floor_packet(request, root)
                if isinstance(request, str) and request.strip() else {})
    for field in FLOOR_AUTHORED:
        if field not in packet:
            continue
        proposed = proposal.get(field)
        if proposed is not None and _survived(packet[field], proposed):
            prov[field] = "floor"
        elif prov.get(field) != "tree":
            prov[field] = "claude"
    return prov


def refuse_misdeclared_floor_provenance(packet: dict, measured: dict) -> None:
    """THE LOUD HALF. A sender that labels its own floor-authored provenance and gets it
    WRONG is refused, not corrected — and refused BEFORE the gate, because this is not a
    judgement about the packet's content but about the sender's authority over a field
    that is measured. Same category as "a packet must be a dict".

    A silent overwrite was the alternative and it is worse. The defect this build exists
    to end is a number computed by the party being measured; correcting the label without
    saying so would leave a sender believing it still labels its own work, and the next
    stage would be written from that belief — the propagation vector that put "a tool
    holds no state" into eight charters.

    AGREEING WITH THE MEASUREMENT IS NOT DECLARING, which is why this refuses on
    DISAGREEMENT rather than on presence. Two reasons, and the second is the load-bearing
    one: a label that matches what re-running the floor produced is not a claim the
    sender made, it is a claim the sender RE-DERIVED, and there is nothing to refuse in
    being right. And ``validate_orient`` runs at both doors over the same object, so a
    refuse-on-presence rule would make the berth's own output illegal at the deposit one
    line later — the door refusing the packet it just wrote."""
    prov = packet.get("provenance") or {}
    wrong = {f: (prov[f], measured.get(f)) for f in FLOOR_AUTHORED
             if f in prov and prov[f] != measured.get(f)}
    if wrong:
        raise OrientRefused(
            "orient refuses a packet that declares its own provenance for %s — those are "
            "DERIVED at the door by re-running the floor over the packet's own 'request' "
            "and comparing, and a field earns 'floor' only when the floor's answer can be "
            "REPRODUCED. Declared vs measured: %s. Drop those keys (the door writes them) "
            "and carry 'request' so there is something to reproduce."
            % (", ".join(sorted(wrong)),
               "; ".join("%s declared %r, measured %r" % (f, d, m)
                         for f, (d, m) in sorted(wrong.items()))))


def inspect_orient(packet: dict, root: str = CAIRN_ROOT) -> list:
    """ORIENT'S OWN INSPECTOR — the proof record for the packet it is about to hand on.

    Every question this stage asks, EXPECTED beside ACTUAL, passes included. Akien,
    2026-08-13, ruling every-machine-carries-its-own-inspector-and-gate: "passing such a
    thing without inspecting it means passing a mystery if something downstream fails …
    we can backtrack and see exactly where something went awry even if it's not something
    we're specifically looking for yet." That last clause is what a record buys and a
    complaint list cannot: the entries that PASSED are the ones nobody was looking for.

    Stage-specific entries first, then the shared half from the chain grammar. Returns
    the record and takes no verdict — the verdict is ``validate_orient``'s, at this same
    address, because the refusal belongs to the stage that would have handed the packet
    on. "We might have to add more or better inspection questions, but that's fine. we
    learn as we go" — so this list grows, and every addition is one more entry a reader
    sees whether it passed or failed.
    """
    record = []
    strings = [f for f in ("intent", "domain", "scope") if f in packet]
    if strings:
        record.append(inspected(
            "authored_fields_are_non_empty_strings", stage="orient",
            expected={f: "non-empty str" for f in strings},
            actual={f: (type(packet[f]).__name__ if not isinstance(packet[f], str)
                        else ("non-empty str" if packet[f].strip() else "empty str"))
                    for f in strings},
            lack="; ".join("field %r must be a non-empty string" % f for f in strings
                           if not isinstance(packet[f], str) or not packet[f].strip())))

    lists = [f for f in ("refs", "unknowns") if f in packet]
    if lists:
        def _shape(value):
            if not isinstance(value, list):
                return type(value).__name__
            return "list of str" if all(isinstance(x, str) for x in value) else "list, mixed"
        record.append(inspected(
            "ref_fields_are_lists_of_strings", stage="orient",
            expected={f: "list of str" for f in lists},
            actual={f: _shape(packet[f]) for f in lists},
            lack="; ".join("field %r must be a list of strings" % f for f in lists
                           if _shape(packet[f]) != "list of str")))

    # THE ONE CHECK THAT READS THE WORLD, and the reason it is guarded: an invented ref is
    # only answerable once the field is known to hold strings. Guarded, so its absence
    # makes the record SHORTER — the shape above has already closed the gate.
    if isinstance(packet.get("refs"), list) and all(
            isinstance(r, str) for r in packet["refs"]):
        roster = set(component_roster(root))
        invented = [r for r in packet["refs"] if not _ref_exists(r, root, roster)]
        record.append(inspected(
            "every_ref_exists_on_disk", stage="orient",
            expected=[], actual=invented, refs_checked=len(packet["refs"]),
            lack="refs the floor cannot verify exist: %s" % ", ".join(invented)))

    record += common_shape_record(packet, required_fields=REQUIRED_FIELDS,
                                  authored_fields=AUTHORED_FIELDS, root=root,
                                  stage="orient")
    return record


def validate_orient(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """ORIENT'S OWN GATE at the handoff — an == compare over its inspector's record.

    Opens only when every entry's expected equals its actual, per entry, no oracle
    anywhere near it (ruling a-gate-opens-on-an-equality-compare-and-never-on-an-oracle).
    Refuses on: missing fields, empty authored strings, malformed confidence, provenance
    that does not cover every authored field or names an unknown stratum, and any ref the
    floor cannot verify EXISTS (an invented pointer must never reach downstream). EVERY
    lack is named in ONE refusal (ticket chart-doors-refuse-in-one-pass) — a dribbled
    refusal costs the sender a round-trip per field — and the lacks are DERIVED from the
    record's mismatches, so the gate and the sentence cannot disagree about what failed.
    """
    if not isinstance(packet, dict):
        # Before the record exists, because there is nothing to inspect: a non-dict cannot
        # be asked a single one of the questions above, so this is the one refusal that
        # is not a gate verdict. It is loud and it is terminal.
        raise OrientRefused("orient packet must be a dict, got %s" % type(packet).__name__)

    # PROVENANCE IS MEASURED HERE, AT THE GATE, AND IN PLACE — the physics for the whole
    # build (Law 4: a rule that matters is enforced by the schema or the kernel, and
    # until it is it is an IOU). Putting it here rather than in ``write_packet`` is what
    # makes it unavoidable: BOTH doors a packet can pass through — the berth and the
    # deposit — go through this function, so there is no route by which a packet reaches
    # instance-space or the tree carrying a label it wrote about itself.
    #
    # IN PLACE, and the alternative is a trap rather than a style preference: /chart
    # calls ``write_packet(p)`` and then ``deposit_orient(p, ...)`` with the same object.
    # A copy would berth the measured provenance and hand the caller back a packet whose
    # provenance this very door would then refuse — the berth and the packet disagreeing
    # about what the packet is.
    measured = measured_provenance(packet, root=root)
    refuse_misdeclared_floor_provenance(packet, measured)
    if measured:
        packet["provenance"] = measured

    record = inspect_orient(packet, root=root)
    if not gate.verdict(record)["opens"]:
        raise OrientRefused(render_lacks("orient", lacks_of(record)))

    return packet


def write_packet(packet: dict, *, instance_dir: str = INSTANCE_DIR,
                 root: str = CAIRN_ROOT) -> str:
    """The berth: validate at the door, then land the packet in instance-space
    (runtime state, never in git). Returns the path."""
    validate_orient(packet, root=root)
    os.makedirs(instance_dir, exist_ok=True)
    digest = hashlib.sha256(
        json.dumps(packet, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = os.path.join(instance_dir, "orient-%s-%s.json" % (stamp, digest))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(packet, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def deposit_orient(packet: dict, vector, *, berth_path: str, nexus: str = "orient",
                   conn=None) -> dict:
    """The deposit-back: a berthed packet's intent becomes the tree's memory of this
    orientation. Gate before seed — the packet re-validates at this door, and the berth
    must exist on disk."""
    validate_orient(packet)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise OrientRefused(
            f"deposit_orient: berth {berth_path!r} does not exist on disk — a node whose "
            "provenance points at nothing is fabricated attribution one layer up; "
            "nothing landed")
    provenance = {
        "source": berth_path,
        "confidence": packet["confidence"],
        "intent_stratum": packet["provenance"]["intent"],
    }
    return deposit_learning(nexus, packet["intent"], vector, provenance, conn=conn)
