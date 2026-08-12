"""orient — nexus #1 of the chart device: ground the request before anything else runs.

The first question nexus of the pre-build preamble (charter: ../intention+why.json;
ticket: CairnCommons/tickets/chart-orient.json). It answers ONE narrow question:
"what is actually being asked, and where does it live?" — and emits the smallest
typed artifact that fully determines what downstream nexi need.

THE FLOOR DOES NOT SCAN THE TERRITORY ITSELF. The settled owner of prebuild
measurement is the ORIENT INSTRUMENT (cairn/orient — deterministic scans, born
2026-07-27), and this nexus's floor COMPOSES it: the component roster is derived
from ``device_census`` rows, never from a parallel scan. That line is written in
blood: this file's first cast carried its own charter-glob roster, and the nexus's
FIRST LIVE FIRE caught it — the floor reported ``orient`` as a component, its
builder had never surveyed for one, and cairn/orient/ was sitting there proven,
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
from pathlib import Path

from cairn.base.address import instance_path
from cairn.orient.orient import device_census

# .../repo/cairn/chart/orient.py -> repo root
CAIRN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INSTANCE_DIR = str(instance_path("chart", 0) / "packets")

STRATA = ("floor", "tree", "claude")
AUTHORED_FIELDS = ("intent", "domain", "scope", "refs", "unknowns")
REQUIRED_FIELDS = AUTHORED_FIELDS + ("confidence", "provenance")

# '+' rides the class because the house's own charter filenames carry it (intention+why.json)
_PATHISH = re.compile(r"[\w~./+-]*/[\w./+-]*[\w/]")
_SLASH_VERB = re.compile(r"(?<!\S)/([a-z][\w-]*)")
_WORD = re.compile(r"[a-z0-9_]+")


class OrientRefused(RuntimeError):
    """The loud refusal — a packet or request that cannot be grounded says so."""


_ROSTER_MEMO: dict[str, list[str]] = {}


def forget_roster(root: str | None = None) -> None:
    """Drop the memo below — the whole one, or one root's. The door for a caller that
    KNOWS the tree changed under it (a proof that just wrote a component; a process that
    installed one). Not a timer, not a poll: the write is the event."""
    if root is None:
        _ROSTER_MEMO.clear()
    else:
        _ROSTER_MEMO.pop(root, None)


def component_roster(root: str = CAIRN_ROOT) -> list[str]:
    """The components that carry a charter beside their code, derived from the
    orient instrument's census — the floor asks the settled measurer, it does not
    scan in parallel. (A component without an intention doesn't run, so only
    charter-on-disk rows ride the roster.)

    MEASURED ONCE PER PROCESS, PER ROOT (2026-08-05). Law 1 is not a performance note
    here, it is the correctness argument: ``ref_exists`` called this on EVERY ref, so a
    single ``inspect(component='base')`` ran ``device_census`` **168 times** — 15,960
    ``ast.parse`` calls, 30.3s of wall clock for ONE component, and 99.3% of the profile
    under this one line. That is not one measurement taken slowly; it is 168 different
    measurements of 168 different instants, stitched together and reported as one census.
    A judge that re-derives its world between two of its own findings can contradict
    itself and be right both times.

    The lived symptom, which is how this was found: ``cairn/build_inspector`` was the one
    proof in the corpus the tester could not finish — RED at its 120s wall, every tooth
    green when run alone at 2m47s. The gate that stands at every forward PROVEME crossing
    was, itself, the slowest thing in the system.

    THE RESIDUE, named rather than glossed: this memo has no invalidation event. Every
    caller today is a short-lived CLI or gate invocation, where "the tree at the moment
    this process started" is exactly the right world to judge against — but a long-lived
    holder (a shim, the ground loop) would keep a roster past a real install. ``forget_roster``
    is the door for a caller that knows; a FileChanged-hook-fired clear is the physics that
    would retire the residue, and it is an IOU, not a resting state (Law 4).
    """
    hit = _ROSTER_MEMO.get(root)
    if hit is not None:
        return list(hit)
    # A REFUSAL IS NEVER MEMOIZED. device_census raises ScanRefused on a root that is not
    # a world; caching that would turn one bad call into a permanently broken process, and
    # the second caller would be told about a scan it never ran (Law 7).
    census = device_census(root=Path(root) / "cairn")
    roster = sorted(row["component"] for row in census["measured"]["components"]
                    if row["charter_on_disk"])
    _ROSTER_MEMO[root] = roster
    return list(roster)


def skill_roster(root: str = CAIRN_ROOT) -> list[str]:
    base = os.path.join(root, "skills")
    if not os.path.isdir(base):
        return []
    return sorted(name for name in os.listdir(base)
                  if os.path.isdir(os.path.join(base, name)))


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


def ref_exists(ref: str, root: str = CAIRN_ROOT) -> bool:
    """The ONE semantics for 'this ref resolves' — the public face of the berth
    gate's own resolution, composed by the build_inspector's packet jurisdiction
    (ticket packet-inspector-wire). A judge resolving refs by different rules than
    the gate that admitted them would make the two mouths disagree — so there is
    exactly one implementation, and this is its door."""
    return _ref_exists(ref, root, set(component_roster(root)))


def ticket_path(claim, root: str = CAIRN_ROOT) -> str | None:
    """WHERE A TICKET LIVES — the one implementation, so a reader that OPENS a
    ticket and the gate that merely checks it is on file can never disagree about
    which file that is (ticket watchme-emits-a-probe piece (d), which taught the
    verdict door to read a ticket's falsifier). Returns the path for a
    well-formed claim naming a filed ticket, else None — the None carries both
    'malformed' and 'not on file', because the caller's refusal is the same."""
    if not isinstance(claim, str) or not _TICKET_RE.match(claim):
        return None
    filed = os.path.join(os.path.dirname(root), "CairnCommons", "tickets",
                         claim + ".json")
    return filed if os.path.isfile(filed) else None


def ticket_claim_error(packet: dict, root: str = CAIRN_ROOT) -> str | None:
    """The ticket-claim rule, shared by every packet gate: an optional 'ticket'
    field must name a ticket ON FILE in CairnCommons/tickets/ — a packet claiming
    an unfiled ticket is fabricated attribution (the 2026-07-26 class). Returns
    the refusal text, or None when the claim is absent or holds."""
    if "ticket" not in packet:
        return None
    claim = packet["ticket"]
    if ticket_path(claim, root):
        return None
    return ("ticket claim %r names no ticket on file in CairnCommons/tickets/ — "
            "a packet may not attribute itself to an unfiled voyage" % (claim,))


_TICKET_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def _ref_exists(ref: str, root: str, roster: set) -> bool:
    if not isinstance(ref, str) or not ref.strip():
        return False
    if ref in roster:
        return True
    candidate = os.path.expanduser(ref)
    if os.path.isabs(candidate):
        return os.path.exists(candidate)
    if os.path.exists(os.path.join(root, ref)):
        return True
    commons = os.path.join(os.path.dirname(root), "CairnCommons")
    return os.path.exists(os.path.join(commons, ref))


def identity_lack(packet: dict, berth_doc, ref_name: str):
    """Request identity on a chain link (tickets berths-carry-request-identity +
    the-claim-rides-every-link): two clauses, one home, six mouths (every
    follower door) — the same rule buildme_rides_the_chart already applies at
    the chain's end, extended inward.

    MISMATCH — both sides claim and disagree: the chain would sail green under
    another request (the one silent-corruption path the opus pass ranked first).

    VANISH — the upstream berth claims and this packet is silent: on a claimed
    chain the claim rides every link (Akien's verdict on cbbadb13530f,
    2026-08-03: 'no warns, refuse and send back to sender'). A claim may ENTER
    mid-chain (packet claims, upstream silent — legal), it may never silently
    vanish. The author's claim stays AUTHORED, never door-copied: it is the one
    witness the berth cannot contaminate, which is what gives the mismatch
    clause something to check.

    Returns the lack message, or None when the upstream is claimless
    (jurisdiction: nothing already sailing unclaimed is retro-redded)."""
    mine = packet.get("ticket")
    theirs = berth_doc.get("ticket") if isinstance(berth_doc, dict) else None
    has_mine = isinstance(mine, str) and mine.strip()
    has_theirs = isinstance(theirs, str) and theirs.strip()
    if has_mine and has_theirs and mine != theirs:
        return ("request-identity mismatch: this packet claims ticket %r but its %s "
                "berth claims %r — every door would pass and the voyage would sail "
                "under another request's chain; recover the RIGHT chain with: "
                "python3 -m cairn.chart.live chain %s" % (mine, ref_name, theirs, mine))
    if has_theirs and not has_mine:
        return ("request-identity vanished: this chain is claimed by ticket %r (its %s "
                "berth carries the claim) but this packet is claimless — on a claimed "
                "chain the claim rides every link; add \"ticket\": %r to this packet, "
                "or recover the chain with: python3 -m cairn.chart.live chain %s"
                % (theirs, ref_name, theirs, theirs))
    return None


CHAIN_REMEDY = (
    " REMEDIATION: re-fire the broken link's own stage for THIS request and hand "
    "the NEW berth path forward (the chain re-berths from the repaired link down) "
    "- stage 1 orient: write_packet / 2 constrain: write_constrain / 3 survey: "
    "write_survey / 4 decompose: write_decompose / 5 triage: write_triage / "
    "6 hypothesize: write_hypothesize, each fired as PYTHONPATH=$HOME/dev/src/cairn "
    "python3 -c 'from cairn.chart.<stage> import <writer>; ...' <packet.json> - "
    "see the /chart skill for the full step."
)


def common_shape_lacks(packet: dict, *, required_fields, authored_fields,
                       list_fields=(), root: str = CAIRN_ROOT) -> list:
    """Every SHARED shape lack, accumulated — the one implementation of the checks
    all seven stage doors run (missing fields, list shapes, unknowns, confidence,
    provenance coverage and strata, the ticket claim), so the doors cannot drift
    apart again: the copied-cascade defect this replaces began as one hand-written
    tier copied six times (ticket chart-doors-refuse-in-one-pass).

    Returns messages, never raises — each caller appends its stage-specific lacks
    and raises ONCE with everything named. Checks guard on field presence: an
    absent field is reported by the missing-fields lack alone, not twice.
    """
    lacks = []
    missing = [f for f in required_fields if f not in packet]
    if missing:
        lacks.append("missing fields: %s" % ", ".join(missing))

    for field in list_fields:
        if field in packet and not isinstance(packet[field], list):
            lacks.append("%s must be a list" % field)

    if isinstance(packet.get("unknowns"), list) and any(
            not isinstance(x, str) for x in packet["unknowns"]):
        lacks.append("unknowns must be a list of strings")

    if "confidence" in packet:
        confidence = packet["confidence"]
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) \
                or not 0.0 <= float(confidence) <= 1.0:
            lacks.append("confidence must be a number in [0, 1]")

    if "provenance" in packet:
        provenance = packet["provenance"]
        if not isinstance(provenance, dict):
            lacks.append("provenance must be a dict of field -> stratum")
        else:
            uncovered = [f for f in authored_fields if f not in provenance]
            if uncovered:
                lacks.append("provenance does not cover: %s" % ", ".join(uncovered))
            bad = sorted(str(s) for s in set(provenance.values()) if s not in STRATA)
            if bad:
                lacks.append("unknown stratum in provenance: %s (must be one of %s)"
                             % (", ".join(bad), "|".join(STRATA)))

    claim_error = ticket_claim_error(packet, root)
    if claim_error:
        lacks.append(claim_error)
    return lacks


def render_lacks(stage: str, lacks: list) -> str:
    """One refusal carrying every lack — the header a fixer reads first, then one
    line per lack. The count is in the header so 'did I get them all' is answerable
    without re-firing."""
    return ("%s packet refused — %d lack(s), all named on this one pass "
            "(fix them together, then fire again):\n  - %s"
            % (stage, len(lacks), "\n  - ".join(lacks)))


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
