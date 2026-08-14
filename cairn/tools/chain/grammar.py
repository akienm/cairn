"""chain/grammar.py — the grammar every leg of the chart chain speaks.

EXTRACTED FROM ``chart/orient.py`` 2026-08-13, under Akien's ruling "chart is a skill,
it calls a collection of machines." The extraction was not a tidying: orient.py was
TWO FILES UNDER ONE NAME, and the measurement that proved it is that eight of the nine
other legs imported orient and **none of them touched ``floor_facts`` or
``validate_orient``** — every one took only the names below. The chain's apparent
dependence on its own first stage was an artifact of authorship order (orient was
written first, so the shared parts landed there), not of design. Left alone, it made
stage 1 un-removable and every other stage look like it needed orienting before it
could check a field name.

WHY A TOOL AND NOT A MACHINE. A tool is a complete primitive with USERS, not an owner
(Akien, 2026-08-13) — and that is NOT because a tool cannot remember. It can: ongoing
state berths under the holder that assembled it (ruling
2026-08-14-tools-and-machines-remember-under-their-holder), which is why there is nothing
OF ITS OWN to gate. What settles it HERE is the narrower fact that nothing
here owns a durable record: the roster memo below is a per-process memo of a
measurement, dropped by ``forget_roster`` at the write that invalidates it, and the
berths these functions name are owned by the stages that write them.

WHAT LIVES HERE — the shared vocabulary, and nothing stage-specific:
  - WHERE things are: ``CAIRN_ROOT``, ``INSTANCE_DIR`` (every leg berths in one place).
  - WHAT EXISTS: ``component_roster`` / ``skill_roster`` / ``ref_exists`` — the ONE
    semantics for "this ref resolves", so a judge and the gate that admitted a packet
    can never disagree.
  - WHOSE VOYAGE: ``ticket_path`` / ``ticket_claim_error`` / ``identity_lack`` — the
    claim rides every link.
  - WHAT A PACKET MUST BE: ``STRATA`` / ``common_shape_record`` / ``inspected`` /
    ``lacks_of`` / ``common_shape_lacks`` / ``render_lacks`` / ``CHAIN_REMEDY`` — one
    implementation of the checks all seven stage doors run, so the doors cannot drift
    apart again (ticket chart-doors-refuse-in-one-pass).

THE SHARED HALF OF EVERY MACHINE'S INSPECTOR lives here, and it emits a PROOF RECORD
(2026-08-13, ruling every-machine-carries-its-own-inspector-and-gate). Akien: "passing
such a thing without inspecting it means passing a mystery if something downstream fails
… if every machine and even some more complex tools have their own inspector and gate,
then each has documented and controllable quality validation." The stage-specific half
lives at each machine's own address, and each machine's gate is the == compare over the
two halves joined — so a failure backtracks to the stage that let it through.

`cairn determinism` MARKS THIS TOOL A GATE, and it is right to. Gate-ness there is a
DIRECT-import fact, deliberately coarser than "takes the verdict" — a component cannot
hide its gate behind a helper — and this module does import the gate tool and does run
its per-entry == compare (``lacks_of``). What it does NOT do is take the artifact-level
verdict: that is each machine's, at its own address, because that is where the refusal
belongs and where a failure must backtrack to. The two readings are not in conflict; the
instrument measures the vocabulary, and this sentence says what is done with it.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from cairn.tools.base.address import AmbiguousComponent, component_dir, instance_path
from cairn.tools.gate import gate
from cairn.tools.orient.orient import device_census

# .../repo/cairn/tools/chain/grammar.py -> repo root: four dirnames, counted off THIS
# file's own address. It used to be justified as "same depth as the file this was carved
# out of", which stopped being true on 2026-08-13 when that file moved under the builder
# device — a magic number defended by reference to a movable neighbour is a number that
# goes wrong silently. The depth is the tool's own.
CAIRN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
INSTANCE_DIR = str(instance_path("chart", 0) / "packets")

STRATA = ("floor", "tree", "claude")

_TICKET_RE = re.compile(r"^[a-z][a-z0-9-]*$")

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

    The lived symptom, which is how this was found: ``cairn/machines/build_inspector`` was the one
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
    # A ROSTER IS MEMBERSHIP, NOT MULTIPLICITY — hence the set. Since the rungs landed,
    # one NAME can have two homes (``orient`` is a tool and a machine, and the layering is
    # deliberate), so the census returns two rows for it. Without the set, ``roster_size``
    # reported 33 for 32 components and the floor's own arithmetic was wrong. What this
    # deliberately does NOT do is answer WHERE — ``address.component_dir`` owns that
    # question and refuses loudly on the same ambiguity this line collapses, which is the
    # only reason collapsing it here is safe.
    roster = sorted({row["component"] for row in census["measured"]["components"]
                     if row["charter_on_disk"]})
    _ROSTER_MEMO[root] = roster
    return list(roster)


def component_home(name: str, root: str = CAIRN_ROOT) -> str | None:
    """WHERE a component lives, written repo-relative — the WHERE that
    ``component_roster`` deliberately does not answer, composed here rather than reached
    for directly so a chain leg keeps speaking only the grammar.

    Returns ``None`` for a name no component answers to, and RAISES
    ``AmbiguousComponent`` (re-exported from this module for the same reason) when two
    rungs do. That refusal is the whole value of routing through here: a leg that
    concatenated ``cairn/<name>/`` would silently pick a rung, and the first name to
    break it is ``orient`` itself — a tool and a machine, three rungs apart."""
    home = component_dir(name, os.path.join(root, "cairn"))
    return os.path.relpath(str(home), root) if home is not None else None


def skill_roster(root: str = CAIRN_ROOT) -> list[str]:
    """The slash-verbs that exist, derived from the one thing that makes a directory a
    skill: a SKILL.md for the host to read.

    THE TEST IS THE ARTIFACT, NOT THE DIRECTORY. Until 2026-08-13 this listed every
    subdirectory of ``skills/``, which was true only because nothing else had ever been
    put there. Then ``skills/__init__.py`` landed (the packages the chart decomposition
    needed) — Python compiled the folder, ``skills/__pycache__/`` appeared, and the floor
    reported a thirteenth skill named ``__pycache__``. A rule that holds because nobody
    has stepped on it yet is not a rule; this one names what it is looking for."""
    base = os.path.join(root, "skills")
    if not os.path.isdir(base):
        return []
    return sorted(name for name in os.listdir(base)
                  if os.path.isfile(os.path.join(base, name, "SKILL.md")))


def ref_exists(ref: str, root: str = CAIRN_ROOT) -> bool:
    """The ONE semantics for 'this ref resolves' — the public face of the berth
    gate's own resolution, composed by the build_inspector's packet jurisdiction
    (ticket packet-inspector-wire). A judge resolving refs by different rules than
    the gate that admitted them would make the two mouths disagree — so there is
    exactly one implementation, and this is its door."""
    return _ref_exists(ref, root, set(component_roster(root)))


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
                "python3 -m skills.chart.live chain %s" % (mine, ref_name, theirs, mine))
    if has_theirs and not has_mine:
        return ("request-identity vanished: this chain is claimed by ticket %r (its %s "
                "berth carries the claim) but this packet is claimless — on a claimed "
                "chain the claim rides every link; add \"ticket\": %r to this packet, "
                "or recover the chain with: python3 -m skills.chart.live chain %s"
                % (theirs, ref_name, theirs, theirs))
    return None


CHAIN_REMEDY = (
    " REMEDIATION: re-fire the broken link's own stage for THIS request and hand "
    "the NEW berth path forward (the chain re-berths from the repaired link down) "
    "- stage 1 orient: write_packet / 2 constrain: write_constrain / 3 survey: "
    "write_survey / 4 decompose: write_decompose / 5 triage: write_triage / "
    "6 hypothesize: write_hypothesize, each fired as PYTHONPATH=$HOME/dev/src/cairn "
    "python3 -c 'from cairn.machines.<stage>.<stage> import <writer>; ...' <packet.json> - "
    "see the /chart skill for the full step."
)


def inspected(identity, *, expected, actual, lack, stage="", **values) -> dict:
    """One inspection question, in the gate's own vocabulary, carrying its own lack.

    A stage door needs the entry for its GATE and the sentence for its REFUSAL, and the
    two must never be able to disagree about which check failed — so the sentence rides
    inside the entry rather than being assembled from a parallel list. ``gate.proved``
    puts extras under ``values``; the lack is one of them, and it is written for the
    mismatch case because that is the only case a reader ever meets it in.
    """
    return gate.proved(identity=identity, expected=expected, actual=actual,
                       location=("cairn/devices/builder/machines/%s" % stage) if stage else
                                "cairn/tools/chain",
                       code="grammar.py:%s" % identity,
                       source=stage or "chain.grammar", lack=lack, **values)


def common_shape_record(packet: dict, *, required_fields, authored_fields,
                        list_fields=(), root: str = CAIRN_ROOT, stage: str = "") -> list:
    """THE SHARED PROOF RECORD every stage door holds — one entry per check that ran,
    EXPECTED beside ACTUAL, passes included (Akien, 2026-08-13: "EVERYTHING ALWAYS
    PROVED AND LISTING WHAT IT PROVED. SAME PATTERN EVERYWHERE.").

    This is the one implementation of the checks all seven stage doors run, so the doors
    cannot drift apart again (ticket chart-doors-refuse-in-one-pass) — and since the
    every-machine-carries-its-own-inspector-and-gate ruling it emits a RECORD rather than
    a list of complaints. The difference is the whole point: a complaint list is empty
    both when every check passed and when no check ran, so the door downstream is handed
    a mystery in exactly the case Akien named ("passing such a thing without inspecting
    it means passing a mystery if something downstream fails").

    A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED. The guarded checks below only append
    when their input is present, so an absent field makes this record SHORTER — visible
    as a shorter list, never as a cleaner one — and the ``required_fields_present`` entry
    that always runs has already closed the gate. That is also why an absent field still
    produces exactly one lack rather than two, which is the property the complaint-list
    version had and this must not lose.
    """
    record = []
    present = [f for f in required_fields if f in packet]
    missing = [f for f in required_fields if f not in packet]
    record.append(inspected(
        "required_fields_present", stage=stage,
        expected=sorted(required_fields), actual=sorted(present),
        lack="missing fields: %s" % ", ".join(missing)))

    checkable = [f for f in list_fields if f in packet]
    if checkable:
        record.append(inspected(
            "list_fields_are_lists", stage=stage,
            expected={f: "list" for f in checkable},
            actual={f: type(packet[f]).__name__ for f in checkable},
            lack="; ".join("%s must be a list" % f for f in checkable
                           if not isinstance(packet[f], list))))

    if isinstance(packet.get("unknowns"), list):
        bad_unknowns = [x for x in packet["unknowns"] if not isinstance(x, str)]
        record.append(inspected(
            "unknowns_are_strings", stage=stage,
            expected=0, actual=len(bad_unknowns),
            lack="unknowns must be a list of strings"))

    if "confidence" in packet:
        confidence = packet["confidence"]
        ok = (not isinstance(confidence, bool)
              and isinstance(confidence, (int, float))
              and 0.0 <= float(confidence) <= 1.0)
        record.append(inspected(
            "confidence_in_unit_interval", stage=stage,
            expected="a number in [0, 1]",
            actual=("a number in [0, 1]" if ok else repr(confidence)),
            lack="confidence must be a number in [0, 1]"))

    if "provenance" in packet:
        provenance = packet["provenance"]
        record.append(inspected(
            "provenance_is_a_mapping", stage=stage,
            expected="dict", actual=type(provenance).__name__,
            lack="provenance must be a dict of field -> stratum"))
        if isinstance(provenance, dict):
            uncovered = [f for f in authored_fields if f not in provenance]
            record.append(inspected(
                "provenance_covers_authored_fields", stage=stage,
                expected=sorted(authored_fields),
                actual=sorted(f for f in authored_fields if f in provenance),
                lack="provenance does not cover: %s" % ", ".join(uncovered)))
            bad = sorted(str(s) for s in set(provenance.values()) if s not in STRATA)
            record.append(inspected(
                "provenance_strata_are_known", stage=stage,
                expected=[], actual=bad,
                lack="unknown stratum in provenance: %s (must be one of %s)"
                     % (", ".join(bad), "|".join(STRATA))))

    claim_error = ticket_claim_error(packet, root)
    record.append(inspected(
        "ticket_claim_is_consistent", stage=stage,
        expected="consistent", actual=("consistent" if not claim_error else "inconsistent"),
        lack=claim_error or ""))
    return record


def lacks_of(record) -> list:
    """The complaints a proof record implies — its mismatched entries' own sentences.

    DERIVED, NEVER PARALLEL. The record is the measurement and this is a view of it, so a
    check cannot fail while its sentence goes missing, or produce a sentence while the
    gate reads it as passing. Order follows the record, which is the order the checks ran.
    """
    return [e["values"]["lack"] for e in record
            if not gate.passed(e) and e.get("values", {}).get("lack")]


def common_shape_lacks(packet: dict, *, required_fields, authored_fields,
                       list_fields=(), root: str = CAIRN_ROOT) -> list:
    """The shared lacks — now a VIEW of ``common_shape_record``, unchanged for callers.

    Kept because seven stage doors and their proofs speak it, and because a door that
    wants only the sentences should not have to know the record shape. It is one line
    over the record rather than a second implementation: the drift this whole module
    exists to prevent would otherwise reappear between a stage's gate and its refusal.
    """
    return lacks_of(common_shape_record(
        packet, required_fields=required_fields, authored_fields=authored_fields,
        list_fields=list_fields, root=root))


def render_lacks(stage: str, lacks: list) -> str:
    """One refusal carrying every lack — the header a fixer reads first, then one
    line per lack. The count is in the header so 'did I get them all' is answerable
    without re-firing."""
    return ("%s packet refused — %d lack(s), all named on this one pass "
            "(fix them together, then fire again):\n  - %s"
            % (stage, len(lacks), "\n  - ".join(lacks)))
