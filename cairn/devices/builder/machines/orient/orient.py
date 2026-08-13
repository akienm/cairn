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

Packets are runtime state and berth in instance-space (~/.cairn/devices/chart/);
the durable memory is the tree (filed stone). No clocks, no daemons: orient runs
only when /chart is invoked.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

from cairn.tools.tree.tree import deposit_learning
from cairn.tools.chain.grammar import (CAIRN_ROOT, INSTANCE_DIR, _ref_exists,
                                       common_shape_lacks, component_roster,
                                       render_lacks, skill_roster)

AUTHORED_FIELDS = ("intent", "domain", "scope", "refs", "unknowns")
REQUIRED_FIELDS = AUTHORED_FIELDS + ("confidence", "provenance")

# '+' rides the class because the house's own charter filenames carry it (intention+why.json)
_PATHISH = re.compile(r"[\w~./+-]*/[\w./+-]*[\w/]")
_SLASH_VERB = re.compile(r"(?<!\S)/([a-z][\w-]*)")
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
    verbs = sorted({v for v in _SLASH_VERB.findall(text) if v in skills})
    verb_tokens = {"/" + v for v in verbs}

    paths_found, paths_missing = [], []
    for tok in _PATHISH.findall(text):
        if tok in verb_tokens:
            continue  # a known slash-verb is a skill mention, not a path claim
        candidate = os.path.expanduser(tok)
        if os.path.exists(candidate) or os.path.exists(os.path.join(root, tok)):
            paths_found.append(tok)
        else:
            paths_missing.append(tok)

    return {
        "stratum": "floor",
        "request": text,
        "components_mentioned": components,
        "skills_mentioned": verbs,
        "paths_found": sorted(set(paths_found)),
        "paths_missing": sorted(set(paths_missing)),
        "roster_size": len(roster),
    }


def validate_orient(packet: dict, root: str = CAIRN_ROOT) -> dict:
    """The schema gate at the handoff — the append-door pattern (Law 4).

    Refuses on: missing fields, empty authored strings, malformed confidence,
    provenance that does not cover every authored field or names an unknown
    stratum, and any ref the floor cannot verify EXISTS (an invented pointer must
    never reach downstream). EVERY lack is accumulated and raised in ONE refusal
    (ticket chart-doors-refuse-in-one-pass) — a dribbled refusal costs the sender
    a round-trip per field."""
    if not isinstance(packet, dict):
        raise OrientRefused("orient packet must be a dict, got %s" % type(packet).__name__)

    lacks = []
    for field in ("intent", "domain", "scope"):
        if field in packet:
            value = packet[field]
            if not isinstance(value, str) or not value.strip():
                lacks.append("field %r must be a non-empty string" % field)

    for field in ("refs", "unknowns"):
        if field in packet:
            value = packet[field]
            if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
                lacks.append("field %r must be a list of strings" % field)

    if isinstance(packet.get("refs"), list) and all(
            isinstance(r, str) for r in packet["refs"]):
        roster = set(component_roster(root))
        invented = [r for r in packet["refs"] if not _ref_exists(r, root, roster)]
        if invented:
            lacks.append("refs the floor cannot verify exist: %s" % ", ".join(invented))

    lacks += common_shape_lacks(packet, required_fields=REQUIRED_FIELDS,
                                authored_fields=AUTHORED_FIELDS, root=root)
    if lacks:
        raise OrientRefused(render_lacks("orient", lacks))

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
