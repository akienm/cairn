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
from cairn.tools.gate import gate  # noqa: E402
#   THE GATE IS AN == COMPARE AND IT LIVES IN ONE PLACE (Akien, 2026-08-13: "A GATE ONLY
#   OPENS WHEN A FINDINGS REPORT MATCHES WHAT IT ALLOWS. ITS AN == compare. Must be
#   identical. NO ORACLE."). This inspector used to decide its own exit with
#   ``not findings``, which is the same compare against an empty allowlist — written out
#   longhand, where nothing could see it was a gate. Importing the primitive is what makes
#   gate-ness a MEASURABLE fact: `cairn determinism` derives "this is a gate" from this
#   import and reds any gate whose closure reaches the LLM.
from cairn.tools.chain.grammar import (CAIRN_ROOT, ref_exists,  # noqa: E402  (tree-free
                                ticket_path, is_skeleton)  #   module — the verdict
#   path stays structurally unable to reach tree machinery; the packet jurisdiction
#   composes the berth gate's OWN ref semantics so the two mouths cannot disagree.
#   ticket_path joined 2026-07-30 (watchme-emits-a-probe's own live fire): the
#   forwarding order lives on the ticket, and WHERE a ticket lives already had one
#   implementation — re-deriving it here would be the Law 1 defect the gate judges.)
from cairn.devices.builder.machines.verdict.verdict import claiming_packets, unanswered, verdict_error  # noqa: E402
#   (joined 2026-07-29, ticket proved-answers-the-chart: the exit gate composes the ONE
#   verdict-artifact validator the deposit face also composes — tree-free like
#   chart.orient, pinned transitively by the inspector-nexus allowlist tooth.
#   claiming_packets joined 2026-07-29 (the-deposit-rides-the-read): the
#   latest-claimer rule this gate used to own privately now lives beside the
#   validator, so the gate and the crossing's deposit-enqueue cannot disagree
#   about WHICH artifact answered.
from cairn.tools.orient.orient import ScanRefused, device_census  # noqa: E402
# cairn.tools.import_sieve joined 2026-08-06 (the-questions-are-the-sieve): a sieve's
# PHASE is derived from what it reads, never authored — phase_of reads this module's
# source and classifies each sieve as preprocess/record/postprocess.
# Tree-free (ast + pathlib + os only) and pinned transitively by the allowlist
# tooth, exactly like chart.orient and chart.verdict.
from cairn.tools.import_sieve import sieve as import_sieve  # noqa: E402
# The ASSEMBLY and the SHAKE ride the general berth since 2026-08-07 (ruling
# the-nest-is-block-general, ticket banding-berths-at-the-general-level): derivation
# is import_sieve's domain, banding is block-general, and this inspector is the
# nest's first TENANT, not its owner.
from cairn.tools.base import nest as base_nest  # noqa: E402
# cairn.tools.base.address joined 2026-08-17 (the-instance-address-is-resolved-never-spelled):
# _CHART_BERTHS below used to spell ~/.cairn by hand, and was held back at the parent ticket
# for two stated reasons that have both expired — the import allowlist (retired 2026-08-12
# by reachability-replaces-the-allowlist) and "no rung fits a device across instances", when
# resolve("instance/devices") is exactly that shape and predates the exclusion. The module
# imports pathlib and nothing else, so it costs this gate nothing it measures.
from cairn.tools.base.address import resolve as resolve_address  # noqa: E402
# cairn.tools.base.address_rule joined 2026-08-17 (same ticket): the ONE spelling of what
# counts as a hand-spelled instance address, shaken here at inspection time and by
# tools/base/probes/hand_spelled_instance_paths.py on a pulse — two seats, one rule, the
# same shape as sole_path_holds. It reaches ast, pathlib and import_sieve's walk, all of
# which this gate already reaches, so the fire path is unchanged (measured, not assumed).
from cairn.tools.base import address, address_rule  # noqa: E402
from cairn.tools.import_sieve import HollowScan  # noqa: E402


def _finding(method: str, component: str, about: str, expected, actual,
             compare: str = "exact", **values) -> dict:
    """A FINDING IS A STAMPED CONDITION (Akien, 2026-08-12, distinction 53 on ticket
    the-questions-are-the-sieve): '{about: checks for x, expected: true, actual: false}'
    — you can put EVERYTHING you need into that.

    SUPERSEDES datum+score (distinction 47, same ticket). Scoring is not a third
    operation: the compare field absorbs it. Gate-mode vs select-mode is the PRESENCE
    OF expected, which is data too.

    A finding is emitted only when a sieve CATCHES. Passes carry no finding — they
    appear in the report's gradation, which is where the vector Akien drew
    ([1.0, 1.0, 0.0, 1.0, 1.0] = 0.0) actually lives.

    Extra keyword arguments land in ``values`` — the same pattern as gate.proved().
    """
    entry = {
        "about": about,
        "expected": expected,
        "actual": actual,
        "compare": compare,
        "method": method,
        "component": component,
    }
    if values:
        entry["values"] = values
    return entry


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
        "charter on disk", expected=True, actual=False,
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
        "proofs exist", expected=True, actual=False,
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
        "device calls emit()", expected=True, actual=False,
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
            f"state/history pair complete ({absent.name} missing)",
            expected=True, actual=False,
        )]
    try:
        on_disk = json.loads(s.read_text())
    except json.JSONDecodeError as e:
        return [_finding(
            "state_is_projection", row["component"],
            f"state.json readable ({e})",
            expected=True, actual=False,
        )]
    projected = projector.project(projector.read_history(str(h)))
    if on_disk == projected:
        return []
    diverging = sorted(
        k for k in set(on_disk) | set(projected) if on_disk.get(k) != projected.get(k)
    )
    return [_finding(
        "state_is_projection", row["component"],
        f"state.json matches projection (diverging: {diverging})",
        expected=True, actual=False,
    )]


def crossing_fingerprints_verified(row: dict, comp_dir: Path) -> list[dict]:
    """Every crossing record carrying a fingerprint field must verify under re-hash.

    Provenance: ticket crossing-fingerprints-are-verified — a crossing record is the
    record of truth for gate passage (Law 7); a fingerprint makes it self-verifying.
    Records without a fingerprint field (pre-existing, before the change) are skipped.
    """
    from cairn.tools.base.transitions import verify_crossing_fingerprint

    h = comp_dir / "history.json"
    if not h.exists():
        return []
    entries = projector.read_history(str(h))
    findings = []
    for i, entry in enumerate(entries):
        if "fingerprint" not in entry:
            continue
        if not verify_crossing_fingerprint(entry):
            findings.append(_finding(
                "crossing_fingerprints_verified", row["component"],
                f"crossing record {i} fingerprint verifies",
                expected=True, actual=False,
                entry_from=entry.get("from", "?"),
                entry_to=entry.get("to", "?"),
            ))
    return findings


# ── PACKET JURISDICTION (ticket packet-inspector-wire, 2026-07-28) ───────────
# A build is judged against the packet that charted it. The walk is the wire's whole
# claim: the packet claims its ticket (gated at the berth door), the component's own
# history names its tickets (crossings carry them) — so the gate finds a build's
# charted packets by reading two records that already exist. No new side channel.

# STILL A MODULE-LEVEL CONSTANT, and that is a bound rather than a style: the comment
# below says a proof swaps it, so the conversion had to keep something swappable. An
# inlined resolve() call at the read sites would pass every value check and silently
# break the swap.
_CHART_BERTHS = resolve_address("instance/devices") / "chart"

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
        f"packet readable: {path.name}",
        expected=True, actual=False,
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


# ── THE SECOND SUCCESSOR DOOR: DERIVED, NOT AUTHORED ─────────────────────────
# (ticket a-bulk-move-forwards-itself-from-gits-own-rename-record, 2026-08-17)
#
# The hand-authored order above works and does not SCALE. Measured on the day it
# was written: a single reorg left 465 findings of this class across 14 of 29
# components — the door to proven-space closed on half the system — and clearing
# base's share took 40 hand-written entries across 4 tickets, every one of them
# transcribed from `git log --diff-filter=R`. A hand copying a machine-readable
# record one line at a time is a settled answer being re-derived (Law 1), and the
# copy can drift from the record it came from.
#
# So git's rename record is the SECOND door, and the precedence is not an
# implementation detail: THE HAND WINS. A rename record can only say where a file
# went; it cannot say what a DISSOLUTION meant, and a dissolution is precisely
# where the hand is the only competent witness (this ticket's gate 3).
#
# A DIRECTORY IS A CONSENSUS OVER ITS FILES, NOT A SOURCE. Git tracks files, so it
# never records a directory rename at all. The successor of a directory is read off
# where its files went — and by PLURALITY, not unanimity, because a bulk move is
# never unanimous: stragglers move separately, in their own commits, days later.
# Measured before this was built, over base's 71 unresolved addresses: plurality
# answered 67, unanimity 64, and the three it lost were real bulk moves voting
# 6-1-1, 9-1 and 9-1. The vote is bounded from the other side too — only kids whose
# path SUFFIX survived may vote (a file that was renamed AND moved says nothing
# about its directory), and the winner must hold a STRICT majority.
#
# BOTH ENDS ARE CHECKED, exactly as they are for the hand: the successor must
# resolve and the source must not. A derived forward into a hole is the same hollow
# claim as the missing address it disposed, one indirection later — and a derived
# forward to a target that exists and is WRONG is worse, because a hole reds at the
# next sieve and wrong-but-live goes green and gets leaned on (Law 8: a false green
# is worse here than a red, because a peer leans on it).
#
# NOTHING IS PERSISTED. The record is read from git at inspection time and memoized
# in memory for the life of the process. A checked-in table of derived forwards is
# this ticket's wrong-intent clause (2) — it recreates the hand-maintained second
# copy under a machine's name — and it would be runtime state in class-space
# besides. One git snapshot per inspection is also the correct semantics: an
# inspection is a measurement of one moment.

_default_exists = ref_exists  # the production predicate, named so a proof can
                              # assert the injectable seam has not become a second
                              # spelling of what 'resolves' means


class GitUnreadable(RuntimeError):
    """Git could not be read for the rename record.

    RAISED, NEVER RETURNED AS AN EMPTY RECORD. The two are the same number and the
    opposite fact: an empty record makes every address unresolvable and the residue
    maximal, so the report reads 'the corpus owes a hundred hand entries' when the
    truth is 'git did not answer'. Both are zero forwards; only one is true, and
    they want opposite dispositions."""


def _git_lines(repo_root, *args: str) -> list[str]:
    import subprocess  # local: keeps the module's import surface honest about
                       # what is a hard dependency of merely IMPORTING the gate
    root = str(repo_root if repo_root is not None else CAIRN_ROOT)
    try:
        out = subprocess.run(["git", "-C", root, *args], capture_output=True,
                             text=True, check=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise GitUnreadable("git %s at %s: %s: %s"
                            % (" ".join(args), root, type(e).__name__, e)) from e
    return out.stdout.splitlines()


def rename_records(repo_root=None) -> tuple:
    """Git's own record of every rename in this repository, oldest first, as
    ``((from, to), ...)``.

    ``-M`` and no ``-C``: the ticket's gate (1) named ``-C`` and the measurement
    disposed it — git emits no copy records without ``--find-copies-harder``, so the
    two flag sets produce an identical record (re-taken, not cited, at
    ``proofs/test_forwarding_derivation.py``). Where copy detection DOES surface, it
    feeds the directory vote a wrong-but-existing target, which is this ticket's
    wrong-intent clause (5) arriving through a flag nobody questioned."""
    pairs = []
    for line in _git_lines(repo_root, "log", "--diff-filter=R", "-M",
                           "--name-status", "--reverse", "--pretty=format:"):
        if not line.startswith("R"):
            continue
        parts = line.split("\t")
        if len(parts) != 3 or not parts[1] or not parts[2]:
            continue
        pairs.append((parts[1], parts[2]))
    return tuple(pairs)


def tracked_files(repo_root=None) -> frozenset:
    """Every path git tracks right now. The directory vote counts only kids whose
    successor the repository still holds."""
    return frozenset(p for p in _git_lines(repo_root, "ls-files") if p)


def _follow_renames(address: str, succ: dict, limit: int = 64):
    """Walk a rename chain to its end. ``None`` on a cycle or a walk that will not
    settle — a gate that can hang is a gate that stops being run."""
    seen, cur = set(), address
    for _ in range(limit):
        if cur in seen:
            return None
        seen.add(cur)
        nxt = succ.get(cur)
        if nxt is None:
            return cur
        cur = nxt
    return None


def _directory_successor(directory: str, finals: dict, tracked, exists):
    """Where a DIRECTORY went, read off its files by strict-majority plurality.

    Only a kid whose path suffix survived the move may vote, and only if its
    successor is still tracked. A leader without a strict majority is not a
    consensus about where a directory went — it is a directory that came apart, and
    the honest answer for one of those is silence (this ticket's wrong-intent
    clause 5: a target that exists and is wrong disposes a real finding and reds
    nothing)."""
    prefix = directory.rstrip("/") + "/"
    votes: dict = {}
    for kid, final in finals.items():
        if not kid.startswith(prefix) or final is None or final not in tracked:
            continue
        rel = kid[len(prefix):]
        if final.endswith("/" + rel):
            home = final[: -(len(rel) + 1)]
            votes[home] = votes.get(home, 0) + 1
    if not votes:
        return None
    total = sum(votes.values())
    best, count = max(sorted(votes.items()), key=lambda kv: kv[1])
    if count * 2 <= total:
        return None
    return best if exists(best) else None


def _successor_index_uncached(root_key: str):
    succ = {}
    for old, new in rename_records(repo_root=root_key or None):
        succ[old] = new  # oldest-first, so a later rename overwrites an earlier one
    finals = {old: _follow_renames(old, succ) for old in succ}
    return succ, finals, tracked_files(repo_root=root_key or None)


_SUCCESSOR_CACHE: dict = {}


def _successor_index(root_key: str):
    """One git snapshot per (process, repository) — in memory, never on disk."""
    if root_key not in _SUCCESSOR_CACHE:
        _SUCCESSOR_CACHE[root_key] = _successor_index_uncached(root_key)
    return _SUCCESSOR_CACHE[root_key]


_successor_index.cache_clear = _SUCCESSOR_CACHE.clear  # type: ignore[attr-defined]


def _repo_relative(address: str, root) -> str:
    """Git's rename record is repo-RELATIVE, and charted addresses are not.

    MEASURED on first live fire, and it is the reason this function exists rather
    than a tidiness: 29 of the corpus's 38 residual addresses were spelled
    absolutely, and 28 of them had a perfectly good rename record sitting in git
    under their relative name. The derivation was answering 'no successor' for the
    wrong reason — a false negative, which is the safe direction (it reds loudly)
    and still wrong. An address outside the repo comes back untouched: git has
    nothing to say about it, and saying nothing IS the answer there."""
    if not os.path.isabs(address):
        return address
    root = os.path.normpath(str(root))
    norm = os.path.normpath(address)
    if norm.startswith(root + os.sep):
        return norm[len(root) + 1:]
    return address


def derived_successor(address, repo_root=None, exists=None):
    """Where git says this address went, or ``None`` — and ``None`` is a real
    answer, not a failure.

    ``exists`` is injectable so a proof can ask about a synthetic repository; the
    default is ``ref_exists``, the same predicate the berth gate used to admit the
    address in the first place, so the judge and the gate cannot disagree about
    what resolving means."""
    if not isinstance(address, str) or not address.strip():
        return None
    exists = exists or _default_exists
    if exists(address):
        return None  # a live address is never forwarded out from under itself
    root = str(repo_root) if repo_root else CAIRN_ROOT
    succ, finals, tracked = _successor_index(str(repo_root) if repo_root else "")
    key = _repo_relative(address, root)
    # THE ANSWER COMES BACK IN THE FORM IT WAS ASKED IN. An absolute question
    # answered relatively hands a reader an address it has to re-root itself, and
    # the whole point of a successor is that it can be USED.
    dress = (lambda p: os.path.join(root, p)) if key != address else (lambda p: p)
    if key in succ:
        final = finals.get(key)
        if final and final != key and final in tracked and exists(dress(final)):
            return dress(final)
        return None
    got = _directory_successor(key, finals, tracked,
                               lambda p: exists(dress(p)))
    return dress(got) if got else None


def resolves_to(address, ticket_id, repo_root=None, exists=None):
    """THE SUCCESSOR ORDER, SPELLED FOR CALLERS OUTSIDE THIS MODULE — and it is
    the same order, not a second one: this delegates, and ``_resolves_to`` below
    remains the only body holding the precedence.

    Added 2026-08-17 (ticket a-deposit-stands-downstream-of-a-move), because the
    successor family had grown a hole in its own naming: ``derived_successor`` and
    ``forwarding_residue`` are public, ``_forwarding_map`` and ``_resolves_to``
    are private — and the private one is the ONLY of the four that carries the
    precedence rule. So a second component needing 'where did this address go'
    could reach a public name for either HALF of the answer, and had to go through
    an underscore for the whole of it. That is the shape in which a rule gets
    copied instead of composed, and the copy is exactly what
    one-owner-for-the-instance-address was born of.

    The delegation rather than a rename is deliberate and was priced: renaming
    would edit the three sieves and this module's own proof, killing
    build_inspector's seal for a component outside that voyage's bounds. One body,
    two spellings, and the spelling a stranger reaches for is the public one."""
    return _resolves_to(address, ticket_id, repo_root=repo_root, exists=exists)


def _resolves_to(address, ticket_id, repo_root=None, exists=None):
    """THE ONE SUCCESSOR RESOLVER the three address sieves compose.

    Precedence: the ticket's hand-authored order first, git's rename record second.
    One rule with one spelling — the neighbouring voyage
    (one-owner-for-the-instance-address) was born of the same rule spelled twice in
    two seats that then drifted apart, and two answers to 'where did this address
    go' would be that defect again."""
    hand = _forwarding_map(ticket_id).get(address)
    if hand:
        return hand
    try:
        return derived_successor(address, repo_root=repo_root, exists=exists)
    except GitUnreadable:
        return None  # the residue report owns the reader's failure and says so
                     # by name; a sieve's job is not to turn it into a finding
                     # about the component that happened to be crossing


def forwarding_residue(comp_dir=None) -> dict:
    """WHAT A HAND STILL OWES — the charted addresses no successor door can reach.

    Gate (4) of this ticket: the derivation is MEASURED, not asserted. A residue
    nobody can enumerate is a residue nobody owes, so this reports the count AND
    the named list, per address, with the tickets that charted it.

    ``reader_failed`` is the field that keeps the report honest at its worst
    moment: zero-because-everything-resolved and zero-because-git-said-nothing are
    the same number, and this is where they are made different.

    THE UNIT IS THE (ADDRESS, TICKET) PAIR, NOT THE ADDRESS — and that is a defect
    this report had until its second live fire. A forwarding order is one TICKET's
    record of what ITS build moved, so the sieve asks only the order of the ticket
    whose packet drew the finding. A residue keyed on the address alone accepts an
    answer from any ticket that ever charted it, which is strictly more generous
    than the gate it reports for: one instance-space address read CLEAN here while
    the sieve still redded it, because a neighbouring voyage's ticket carried the
    entry and the charting one did not. A residue that reports less work than a
    hand actually owes is the report failing at its one job.

    SO ``asked`` AND ``answered`` ARE PAIR COUNTS AND ``answers`` IS AN
    ADDRESS-KEYED INDEX — different units on purpose, and the difference is a
    measurement rather than a caveat. One address asked under two tickets is two
    pairs and one entry, and it can appear in ``answers`` AND ``unanswered`` at
    once: measured on this corpus, ``cairn/chart/intention+why.json`` is answered
    for the ticket that carries a hand order and unanswered for the claimless
    packet that has no ticket to carry one. The accounting closes over pairs;
    reading completeness off ``len(answers)`` is reading the index for the ledger.
    """
    tickets = _component_tickets(Path(comp_dir)) if comp_dir is not None else None
    asked: dict = {}          # (address, ticket) -> None, in first-seen order
    reader_failed = None
    if _CHART_BERTHS.is_dir():
        for stage in ("orient", "constrain", "survey"):
            for path in sorted(_CHART_BERTHS.glob("*/packets/%s-*.json" % stage)):
                try:
                    packet = json.loads(path.read_text())
                except (OSError, json.JSONDecodeError):
                    continue  # the unreadable berth is its owner's finding, above
                if not isinstance(packet, dict):
                    continue
                tid = packet.get("ticket")
                if tickets is not None and tid not in tickets:
                    continue
                for addr in _charted_addresses(packet, stage):
                    if not ref_exists(addr):
                        asked[(addr, tid if isinstance(tid, str) else None)] = None
    answers, answered_by, unanswered_pairs, answered_pairs = {}, {}, [], 0
    for addr, tid in sorted(asked, key=lambda p: (p[0], p[1] or "")):
        got, by = None, None
        try:
            # The hand door needs a ticket; git does not — so a CLAIMLESS packet
            # still gets the derived door. Measured on first live fire: three
            # addresses sat in the residue with a perfectly good rename record
            # behind them, purely because there was no ticket to look an order up
            # under.
            got = _resolves_to(addr, tid)
            by = (tid if tid and _forwarding_map(tid).get(addr) == got else "git")
        except GitUnreadable as e:                           # pragma: no cover
            got, by, reader_failed = None, None, str(e)
        if got is None and reader_failed is None:
            try:
                derived_successor(addr)     # the reader's health, asked separately
            except GitUnreadable as e:
                reader_failed = str(e)
        if got:
            answered_pairs += 1
            answers[addr] = got
            answered_by[addr] = by   # WHICH door answered — the hand order and the
                                     # derivation are different authorities, and an
                                     # answer that cannot say which one it came from
                                     # cannot be audited (Law 3)
        else:
            unanswered_pairs.append({"address": addr, "charted_by": tid})
    return {"asked": len(asked), "answered": answered_pairs, "answers": answers,
            "answered_by": answered_by, "unanswered": unanswered_pairs,
            "reader_failed": reader_failed}


def _charted_addresses(packet: dict, stage: str) -> list:
    """The addresses a berthed packet claims the world holds — read through the same
    fields the three sieves read, so the residue cannot report on a different
    population than the one the gate judges."""
    out = []
    if stage == "orient":
        refs = packet.get("refs")
        if isinstance(refs, list):
            out += [r for r in refs if isinstance(r, str) and r.strip()]
    elif stage == "constrain":
        for c in packet.get("constraints") or []:
            if isinstance(c, dict) and isinstance(c.get("source"), str):
                out.append(c["source"])
    elif stage == "survey":
        for h in packet.get("holdings") or []:
            if isinstance(h, dict) and isinstance(h.get("address"), str):
                out.append(h["address"])
    return out


def forwarding_order_resolves(row: dict, comp_dir: Path) -> list[dict]:
    """A ticket's forwarding order is checked in the world at both ends: every
    entry says where an address WENT (``to``, which must resolve) and WHY, and
    forwards an address that genuinely no longer resolves.

    Provenance: 2026-07-30 — ticket watchme-emits-a-probe's own WATCHME crossing
    was refused with five findings (one orient ref, four survey holdings) naming
    base's callback module, its crossing proof, and the homeless intention — the
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
                f"ticket readable: {tid} ({type(e).__name__})",
                expected=True, actual=False,
            ))
            continue
        order = ticket.get("forwarding")
        if order is None:
            continue  # most tickets move nothing; absence is the normal case
        if not isinstance(order, dict):
            findings.append(_finding(
                "forwarding_order_resolves", row["component"],
                f"forwarding order shaped: {tid}",
                expected=True, actual=False,
            ))
            continue
        for old, entry in order.items():
            ev = {"ticket": tid, "from": old, "entry": entry}
            if not isinstance(old, str) or not old.strip() or not isinstance(entry, dict):
                findings.append(_finding(
                    "forwarding_order_resolves", row["component"],
                    f"forwarding entry shaped: {old!r}",
                    expected=True, actual=False,
                ))
                continue
            to, why = entry.get("to"), entry.get("why")
            if not all(isinstance(v, str) and v.strip() for v in (to, why)):
                findings.append(_finding(
                    "forwarding_order_resolves", row["component"],
                    f"forwarding entry complete: {old!r}",
                    expected=True, actual=False,
                ))
                continue
            if not ref_exists(to):
                findings.append(_finding(
                    "forwarding_order_resolves", row["component"],
                    f"forwarding successor resolves: {old!r} -> {to!r}",
                    expected=True, actual=False,
                ))
                continue
            if ref_exists(old):
                findings.append(_finding(
                    "forwarding_order_resolves", row["component"],
                    f"forwarding source retired: {old!r} -> {to!r}",
                    expected=True, actual=False,
                ))
    return findings


def charted_refs_resolve(row: dict, comp_dir: Path) -> list[dict]:
    """A promoted build must still match what its packet charted: every ref the
    orient packet carried must resolve at promotion time — or the ticket must say
    where it went (see the forwarding order above).

    Provenance: 2026-07-24 — 'done' reported while the files stood unmoved (the
    sharpest claim-vs-world drift on record). The packet is the claim, the
    promotion is the moment, this sieve is the comparison — through the berth
    gate's own ref semantics (cairn.devices.builder.machines.orient.orient.ref_exists), so the judge and
    the gate that admitted the refs cannot disagree.
    """
    packets, unreadable = _charted_packets(comp_dir, "orient")
    findings = _unreadable_findings("charted_refs_resolve", row, unreadable)
    for path, packet in packets:
        refs = packet.get("refs")
        if not isinstance(refs, list):
            continue  # shaped at the berth door; unreachable through it
        tid = packet.get("ticket")
        missing = [r for r in refs if not isinstance(r, str) or not ref_exists(r)]
        missing = [r for r in missing
                   if not (isinstance(r, str) and _resolves_to(r, tid))]
        if missing:
            findings.append(_finding(
                "charted_refs_resolve", row["component"],
                f"charted refs resolve: {', '.join(map(str, missing))}",
                expected=True, actual=False,
            ))
    return findings


# ── THE JUDGES BEFORE THE JUDGED (ticket constrain-filters, 2026-07-28) ──────
# Akien's higher-order build-the-test-first: the acceptance gate for the constrain
# brick's output, installed and proved BEFORE the constrain module exists. The judge
# is the inspector's — behind the inspector's write-gate — and the future constrain
# berth door COMPOSES it (imports judge_constrain; never the reverse), so the module
# structurally cannot shape its own acceptance criteria. One implementation, two
# mouths: the door refuses at berth time, these sieves re-judge at promotion.

CONSTRAIN_ROSTER = ("constraint_traces", "constraint_bounds_complete")


def _attendance(frags, roster):
    """Group judge fragments into attendance records — one per roster member.

    The attendance record is emitted by the judge, not asserted by the caller
    (ticket a-judge-declares-its-attendance, falsifier clause 4). A judge that
    ran produces {judge, ran, findings}; a judge absent from the return never ran.
    """
    by_judge = {name: [] for name in roster}
    for f in frags:
        by_judge[f["judge"]].append(f)
    return [{"judge": name, "ran": True, "findings": findings}
            for name, findings in sorted(by_judge.items())]


def judge_constrain(packet: dict) -> list[dict]:
    """The pure judge over ONE constrain packet — attendance records per judge,
    each carrying its findings (possibly empty). Composed by the berth door and
    wrapped by the gate sieves below; if the two mouths ever disagree, this
    function's singleness is the broken claim."""
    frags = []
    if is_skeleton(packet.get("constraints")) and is_skeleton(packet.get("bounds")):
        return _attendance(frags, CONSTRAIN_ROSTER)
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
    return _attendance(frags, CONSTRAIN_ROSTER)


def _judge_charted(row: dict, comp_dir: Path, stage: str, judge,
                   judge_name: str, report_unreadable: bool = False) -> list[dict]:
    """One wrapper for every stage's pure judge — the promotion-side mouth. Each
    stage's sieves pass their own judge fn; growing a parallel wrapper per stage
    would be the drift the import_map correction just retired from the proofs."""
    packets, unreadable = _charted_packets(comp_dir, stage)
    findings = _unreadable_findings(judge_name, row, unreadable) if report_unreadable else []
    for path, packet in packets:
        for att in judge(packet):
            if att["judge"] == judge_name:
                for frag in att["findings"]:
                    ev = dict(frag.get("evidence") or {}, berth=str(path),
                              ticket=packet.get("ticket"))
                    findings.append(_finding(
                        judge_name, row["component"], frag["finding"],
                        expected=True, actual=False, **ev))
    return findings


def constraint_traces(row: dict, comp_dir: Path) -> list[dict]:
    """Every constraint in a charted constrain packet names a source that resolves.

    Provenance: 2026-07-26 — the fabricated-attribution class (an echo label
    attesting an unhappened push; a misattributed ruling the same week). Installed
    2026-07-28 BEFORE the constrain module exists, on Akien's ordering ruling
    ('we set up it's inspector sieves first') — the failure predates the module,
    so tooth 10 holds: this sieve was taught by a real, dated failure.

    THE FORWARDING ORDER IS CONSULTED HERE TOO, and until 2026-08-14 it was not.
    That was not a decision — it was the shape of the day the tolerance was built.
    On 2026-07-30 the moving ticket's own refusal named one orient ref and four
    survey holdings, so the successor door was fitted to exactly those two sieves
    and this third one, whose findings were not in that day's set, kept the flat
    rule. A constraint's ``source`` is an address in the same sense a holding's
    ``address`` is, and a move breaks it identically; MEASURED at the crossing
    that found this — ground_loop reds 52, of which 40 are disposed by a
    forwarding order and the remaining 12 are constraint sources ALREADY
    FORWARDED on the same tickets, with the successor resolving, by an order this
    sieve did not read. A tolerance that covers two of three sieves is not a
    narrower tolerance, it is an unmeasurable one.

    The asymmetry that IS deliberate is preserved exactly as ``survey_holdings_
    resolve`` states it: ``judge_constrain`` is also the BERTH DOOR's mouth, where
    every source resolves by definition, so the pure judge keeps the flat rule and
    only the promotion side — the one that alone stands downstream of a move —
    disposes. Both ends of every entry are still checked in the world.
    """
    findings = _judge_charted(row, comp_dir, "constrain", judge_constrain,
                              "constraint_traces", report_unreadable=True)
    return [f for f in findings
            if not _resolves_to((f.get("values") or {}).get("source"),
                                (f.get("values") or {}).get("ticket"))]


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

SURVEY_ROSTER = ("survey_holdings_resolve", "survey_coverage_complete")


def judge_survey(packet: dict) -> list[dict]:
    """The pure judge over ONE survey packet — fragments tagged by owning sieve.
    A survey asserts an inventory: HOLDINGS must be held by the world (address
    resolves), and the sweep's COVERAGE must be on record (sought non-empty; every
    absence carrying the measure that established it — an absence is a claim)."""
    frags = []
    if is_skeleton(packet.get("holdings")) and is_skeleton(packet.get("sought")) \
            and is_skeleton(packet.get("absences")):
        return _attendance(frags, SURVEY_ROSTER)
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
    return _attendance(frags, SURVEY_ROSTER)


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
            if not _resolves_to((f.get("values") or {}).get("address"),
                                (f.get("values") or {}).get("ticket"))]


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

DECOMPOSE_ROSTER = ("decompose_builds_absences", "decompose_composes_holdings")


def judge_decompose(packet: dict) -> list[dict]:
    """The pure judge over ONE decompose packet — fragments tagged by owning
    sieve. A decomposition derives from the chain or it is invented: a
    'compose' piece may only use addresses the survey berth HOLDS, a 'build'
    piece may only fill an absence the survey MEASURED — known-vs-novel as
    physics, a stage early."""
    frags = []
    if is_skeleton(packet.get("sub_problems")):
        return _attendance(frags, DECOMPOSE_ROSTER)
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
        return _attendance(frags, DECOMPOSE_ROSTER)
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
        # WHERE THE PIECE'S OUTPUT LANDS — and this mouth judges only a `writes_to`
        # that IS PRESENT. The decompose DOOR requires the field; this judge is also
        # the PROMOTION mouth (_judge_charted sweeps every standing berth claiming a
        # ticket the component owns), and the 51 berths charted before the field
        # existed never had it asked of them. Reading their silence as a finding
        # would red 51 healthy components against a spec that did not exist when
        # they were written — tooth 1 ("a healthy component draws a finding — a gate
        # that always fires gets unwired") and Law 9's bound read the other way. The
        # two-mouth asymmetry is deliberate, and it has precedent at
        # survey_holdings_resolve. Tagged under composes_holdings because that judge
        # already carries "every piece has its shape", which is what a malformed
        # output address is; the split is by claim, not by a third sieve nobody was
        # taught by.
        if "writes_to" in sp:
            frags += _writes_to_frags(i, sp)
    return _attendance(frags, DECOMPOSE_ROSTER)


def _writes_to_frags(i: int, sp: dict) -> list[dict]:
    """The findings a PRESENT ``writes_to`` can draw — never the finding of its absence.

    An address is judged on three things, and existence is NOT one of them: a build
    piece names the file it is about to create, so demanding existence would red
    exactly the case the field was added to carry. What is judged is that the address
    is a non-empty string, that it is INSIDE the cairn repo, and that it is not an
    existing DIRECTORY — the downstream reader hands it to an apprentice as an editable
    file, and a directory handed over as a file is a brief that cannot be honoured.
    """
    frags, addrs = [], sp.get("writes_to")
    if not isinstance(addrs, list) or not addrs:
        return [{
            "judge": "decompose_composes_holdings",
            "finding": "sub-problem %d declares a `writes_to` that is not a "
                       "non-empty list" % i,
            "evidence": {"index": i, "what": sp.get("what"), "writes_to": addrs},
            "why_it_matters": "a piece that names where its output lands and then "
                              "names nothing has an address field that reads as "
                              "answered while answering nothing — worse than the "
                              "absence, which at least measures as absent.",
        }]
    root = str(_REPO_ROOT)
    for addr in addrs:
        if not isinstance(addr, str) or not addr.strip():
            frags.append({
                "judge": "decompose_composes_holdings",
                "finding": "sub-problem %d declares `writes_to` entry %r, which is "
                           "not a non-empty string" % (i, addr),
                "evidence": {"index": i, "what": sp.get("what"), "entry": addr},
                "why_it_matters": "the address is handed downstream as a path; a "
                                  "non-string is a brief that cannot be assembled.",
            })
            continue
        resolved = os.path.normpath(os.path.join(root, addr))
        if not (resolved == root or resolved.startswith(root + os.sep)):
            frags.append({
                "judge": "decompose_composes_holdings",
                "finding": "sub-problem %d writes_to %r — outside the cairn repo" % (i, addr),
                "evidence": {"index": i, "what": sp.get("what"), "entry": addr,
                             "repo_root": root},
                "why_it_matters": "a declared output outside the repo is a write this "
                                  "system does not gate and git cannot see (Law 6, and "
                                  "the class-space rule that runtime state never lands "
                                  "here).",
            })
        elif os.path.isdir(resolved):
            frags.append({
                "judge": "decompose_composes_holdings",
                "finding": "sub-problem %d writes_to %r — an existing directory, "
                           "not a file" % (i, addr),
                "evidence": {"index": i, "what": sp.get("what"), "entry": addr},
                "why_it_matters": "the downstream reader hands this to the apprentice "
                                  "as an editable FILE; a directory is an address that "
                                  "cannot be edited, and the drive would silently do "
                                  "nothing there.",
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

TRIAGE_ROSTER = ("triage_covers_the_split", "triage_reasons_the_order")


def judge_triage(packet: dict) -> list[dict]:
    """The pure judge over ONE triage packet — fragments tagged by owning
    sieve. A triage either ranks the derived work or quietly reshapes it: the
    ORDER must be a complete permutation of the split's pieces (nothing dropped,
    invented, or double-ordered — coverage as a multiset), and every entry must
    carry its why_now (the ranking standard stated, so the order can be
    adjudicated)."""
    frags = []
    if is_skeleton(packet.get("order")):
        return _attendance(frags, TRIAGE_ROSTER)
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
        return _attendance(frags, TRIAGE_ROSTER)
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
    return _attendance(frags, TRIAGE_ROSTER)


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

HYPOTHESIZE_ROSTER = ("hypothesize_covers_the_ranked", "hypothesize_falsifiable_measured")


def judge_hypothesize(packet: dict) -> list[dict]:
    """The pure judge over ONE hypothesize packet — fragments tagged by owning
    sieve. Law 3 as schema: every hypothesis attaches to a RANKED piece
    (verbatim) and every ranked piece carries at least one hypothesis (a
    covering — the piece with none is the piece whose wrong landing reds
    nothing); and every hypothesis carries its expect, its falsifier, and its
    instrument, so the claim can be challenged."""
    frags = []
    if is_skeleton(packet.get("hypotheses")):
        return _attendance(frags, HYPOTHESIZE_ROSTER)
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
        return _attendance(frags, HYPOTHESIZE_ROSTER)
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
    return _attendance(frags, HYPOTHESIZE_ROSTER)


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

VALIDATE_ROSTER = ("validate_covers_the_build", "validate_measures_done",
                   "validate_criterion_is_runnable_before_the_crossing")


def judge_validate(packet: dict) -> list[dict]:
    """The pure judge over ONE validate packet — fragments tagged by owning
    sieve. Done gets an instrument or it is narration: every criterion carries
    its claim and its named instrument; every criterion's covers entries name
    pieces the hypothesize berth claims; and the union of covers equals that
    piece set — every piece's done is measured by at least one criterion."""
    frags = []
    if is_skeleton(packet.get("criteria")):
        return _attendance(frags, VALIDATE_ROSTER)
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
        return _attendance(frags, VALIDATE_ROSTER)
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
        inst = c.get("instrument", "")
        if isinstance(inst, str) and inst.strip():
            markers = []
            if re.search(r"cursor\s*\[PROVED\]", inst):
                markers.append("cursor [PROVED]")
            if re.search(r"after the (?:PROVED )?crossing", inst, re.IGNORECASE):
                markers.append("after the crossing")
            if re.search(r"after the cursor write", inst, re.IGNORECASE):
                markers.append("after the cursor write")
            if markers:
                frags.append({
                    "judge": "validate_criterion_is_runnable_before_the_crossing",
                    "finding": "criterion %d instrument reads post-crossing "
                               "state: %s" % (i, ", ".join(markers)),
                    "evidence": {"index": i, "instrument": inst,
                                 "post_crossing_markers": markers},
                    "why_it_matters":
                        "the verdict gates the PROVED crossing — a criterion "
                        "whose instrument reads state that only exists after "
                        "the crossing is a verdict deferred past the gate "
                        "that reads it, measured 2026-08-15 on "
                        "verdict-20260815T150437-70306f8bfca3.",
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
    return _attendance(frags, VALIDATE_ROSTER)


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
        "chart chain claims this ticket",
        expected=True, actual=False,
        searched=str(root),
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

    if berth is None:
        return [_finding(
            "buildme_rides_the_intent", ticket,
            "ticket names /intent firing",
            expected=True, actual=False,
            ticket_file=str(filed),
        )]

    if not isinstance(berth, str) or not berth.strip():
        return [_finding(
            "buildme_rides_the_intent", ticket,
            "intent_berth well-formed",
            expected=True, actual=False,
            ticket_file=str(filed), found=berth,
        )]

    exempt = _EXEMPT_RE.match(berth)
    if exempt:
        reason = berth[exempt.end():].strip()
        if not reason:
            return [_finding(
                "buildme_rides_the_intent", ticket,
                "exemption reason present",
                expected=True, actual=False,
                ticket_file=str(filed), found=berth,
            )]
        return []

    doc_berth = read_berth(berth)
    if doc_berth is None:
        return [_finding(
            "buildme_rides_the_intent", ticket,
            "intent berth readable",
            expected=True, actual=False,
            ticket_file=str(filed), intent_berth=berth,
        )]

    if doc_berth.get("skill") != "intent":
        return [_finding(
            "buildme_rides_the_intent", ticket,
            "intent berth skill",
            expected="intent", actual=doc_berth.get("skill"),
            ticket_file=str(filed), intent_berth=berth,
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

    if berth is None:
        return [_finding(
            "buildme_rides_the_sorted", ticket,
            "ticket names /sorted firing",
            expected=True, actual=False,
            ticket_file=str(filed),
        )]

    if not isinstance(berth, str) or not berth.strip():
        return [_finding(
            "buildme_rides_the_sorted", ticket,
            "sorted_berth well-formed",
            expected=True, actual=False,
            ticket_file=str(filed), found=berth,
        )]

    exempt = _EXEMPT_RE.match(berth)
    if exempt:
        reason = berth[exempt.end():].strip()
        if not reason:
            return [_finding(
                "buildme_rides_the_sorted", ticket,
                "exemption reason present",
                expected=True, actual=False,
                ticket_file=str(filed), found=berth,
            )]
        if not reason_has_referent(reason):
            return [_finding(
                "buildme_rides_the_sorted", ticket,
                "exemption reason resolvable",
                expected=True, actual=False,
                ticket_file=str(filed), found=berth,
            )]
        return []

    doc_berth = read_berth(berth)
    if doc_berth is None:
        return [_finding(
            "buildme_rides_the_sorted", ticket,
            "sorted berth readable",
            expected=True, actual=False,
            ticket_file=str(filed), sorted_berth=berth,
        )]

    if doc_berth.get("skill") != "sorted":
        return [_finding(
            "buildme_rides_the_sorted", ticket,
            "sorted berth skill",
            expected="sorted", actual=doc_berth.get("skill"),
            ticket_file=str(filed), sorted_berth=berth,
        )]

    return []


# ── THE EXIT GATE (ticket proved-answers-the-chart, 2026-07-29) ──────────────
# The loop's other hand: the entry gate above demands a chart EXISTS before a
# build begins; this demands the chart is ANSWERED before the voyage may close.
# A claimed cast ticket crossing forward into PROVED must show a verdict
# artifact (cairn/devices/builder/machines/verdict/verdict.py — the ONE validator, shared with the deposit
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
    # this gate's private glob loop retired into cairn.devices.builder.machines.verdict.verdict, where the
    # crossing's deposit-enqueue reads it too — one implementation, two mouths.
    claiming = claiming_packets(ticket, "validate", berths_root=root)
    artifacts = claiming_packets(ticket, "verdict", berths_root=root)
    if not claiming:
        return []  # unclaimed — ungated (v0 jurisdiction, inherited from the entry gate)
    if not artifacts:
        return [_finding(
            "proved_answers_the_chart", ticket,
            "verdict artifact exists",
            expected=True, actual=False,
            searched=str(root),
            claiming=[str(p) for p, _ in claiming],
        )]
    path, artifact = artifacts[-1]  # the latest answer is the one that stands
    err = verdict_error(artifact)
    if err:
        return [_finding(
            "proved_answers_the_chart", ticket,
            "verdict artifact well-formed",
            expected=True, actual=False,
            artifact=str(path), error=err,
        )]
    if artifact.get("validate_ref") not in {str(p) for p, _ in claiming}:
        return [_finding(
            "proved_answers_the_chart", ticket,
            "verdict answers claiming chart",
            expected=True, actual=False,
            artifact=str(path),
            claiming=[str(p) for p, _ in claiming],
        )]
    return [_finding(
        "proved_answers_the_chart", ticket,
        item,
        expected=True, actual=False,
        artifact=str(path),
        validate_ref=artifact["validate_ref"])
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
            expected=True, actual=False,
            rule=dict(_SOLE_PATH), file=str(comp_dir.parent / path),
        ))
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
        "cairn.tools.tree.tree",        # the graph tree — a verdict may not consult one
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
            expected=True, actual=False,
            rule=dict(_FIRE_PATH),
            file=str(_REPO_ROOT / caught.split(" imports ", 1)[0]),
        ))
    return findings


def address_is_resolved_never_spelled(row: dict, comp_dir: Path) -> list[dict]:
    """A component builds an instance-space path by hand instead of asking the resolver.

    Provenance: ticket ``one-owner-for-the-instance-address``, whose WATCHME predicted the
    way the design fails — "the resolver becomes an ELEVENTH place a path is built rather
    than the only one" — and whose charter said in as many words that nothing REFUSED a
    further hand-spelled path. Between the resolver landing (2026-08-12) and this seat
    (2026-08-17) the corpus grew from a predicted floor of 1 to a measured 7. The watch was
    armed and correct the whole time; nobody read it, which is the difference this seat
    makes: a probe REPORTS, a sieve REDS THE BUILD.

    THE RULE IS NOT HERE — ``cairn/tools/base/address_rule.py`` owns it, and this seat is
    the same rule at the OTHER moment, the same shape as ``sole_path_holds``: the probe
    shakes it over the whole corpus on a pulse, this shakes it over ONE component at its
    inspection. Two seats, one spelling. Re-implementing the pattern here would be the
    defect the ticket is about, committed inside the gate that judges it.

    ATTRIBUTION IS BY DEEPEST OWNER, not by containment. Components nest — a device's
    ``machines/<name>/`` is its own component — so a scan rooted at the device would
    otherwise red the device for its machine's line, and the same site would be caught
    twice under two names. ``address.component_of`` is the existing answer to exactly that
    question and is composed rather than re-derived.

    A COMPONENT THIS CANNOT JUDGE READS RED, NOT GREEN (Law 9). ``scan`` raises
    ``HollowScan`` when it read zero files, and a sieve that swallowed that would report
    clean for a component it never looked at. Measured 2026-08-17: 0 of 39 components hold
    no readable Python, so this branch fires on nothing today and is here for the day the
    census admits a component that does.
    """
    try:
        found = address_rule.scan(root=comp_dir)
    except HollowScan as e:
        return [_finding(
            "address_is_resolved_never_spelled", row["component"],
            "address rule shakeable",
            expected=True, actual=False,
            root=str(comp_dir), refusal=str(e),
        )]
    # The inspection root, recovered from the row rather than re-spelled: ``row["dir"]`` is
    # comp_dir's path relative to it, and a fixture root is not the repo. ``component_of``
    # needs the PACKAGE root to know what the components are, and handing it comp_dir's
    # grandparent would be right only for an unnested component — the exact assumption the
    # rung move already broke once.
    pkg_root = comp_dir
    for _ in Path(row["dir"]).parts:
        pkg_root = pkg_root.parent

    findings = []
    for entry in found["sites"]:
        rel = Path(entry["site"].rsplit(":", 1)[0])
        # ``scan`` writes repo-relative inside the repo and absolute outside it (a fixture
        # tree), so both shapes are read rather than one assumed.
        site_path = rel if rel.is_absolute() else _REPO_ROOT / rel
        owner = address.component_of(site_path, pkg_root=pkg_root)
        if owner is not None and owner.resolve() != comp_dir.resolve():
            continue          # a nested component's line is that component's row, not ours
        findings.append(_finding(
            "address_is_resolved_never_spelled", row["component"],
            f"address resolved not spelled: {entry['site']}",
            expected=True, actual=False,
            site=entry["site"], shape=entry["shape"],
            rule="cairn/tools/base/address_rule.py",
            exemptions=found["exempted"],
        ))
    return findings


_HONEST_ABSENCE = re.compile(
    r"FIRST CROSSING|once its ticket|once the seam crosses|once a ticket|"
    r"until a ticket crosses|NONE,? and",
    re.IGNORECASE,
)


def charter_asserts_file_present(row: dict, comp_dir: Path) -> list[dict]:
    """A charter's PRESENT-TENSE claim about a file beside it is checked against the address.

    Provenance: 2026-08-14, ticket a-charter-may-not-assert-a-file-that-is-not-there —
    seven chart-machine charters asserted 'state.json + history.json beside this charter.
    Both were born at the carve-out', and neither file existed at seven of eight addresses.
    The mechanism named was also wrong: no journal has ever been born at a carve-out.
    The check is NOT limited to state.json and history.json — the defect is a charter
    asserting ANY file beside it that is not there (falsifier point 4).

    A charter that HONESTLY QUALIFIES the absence — "born at this address's first crossing",
    "once its ticket exists", "once the seam crosses" — is describing a not-yet state,
    not asserting present existence. Those pass. A charter that asserts files without
    qualification, or names a past event that never happened ("born at the carve-out"),
    is the finding.
    """
    charter_path = comp_dir / "intention+why.json"
    if not charter_path.is_file():
        return []
    try:
        charter = json.loads(charter_path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    text = charter.get("state_and_history", "")
    if not text:
        return []
    if _HONEST_ABSENCE.search(text):
        return []
    asserted = set(re.findall(r'\b(\w+\.(?:json|py|md))\b', text))
    findings = []
    for name in sorted(asserted):
        if not (comp_dir / name).is_file():
            findings.append(_finding(
                "charter_asserts_file_present", row["component"],
                f"asserted file present: {name}",
                expected=True, actual=False,
                asserted_file=name,
                field="state_and_history",
                charter=str(charter_path),
            ))
    return findings


def constraint_enforcement_holds(row: dict, comp_dir: Path) -> list[dict]:
    """A declared constraint stopped constraining with no ruling in the same act.

    Provenance: ruling 2026-08-14-corrosion-is-drift-with-no-ruling-behind-it.
    Akien: 'presenting a deterministic result of an error will prompt you to fix
    it, not to plaster over it.' ONE PREDICATE: drift with a ruling behind it is
    the system learning; drift with none is corrosion.

    Checks the declared constraint set (cairn/machines/corrosion/constraint_set.json)
    when the corrosion component is inspected. The set includes itself as a member
    (self-reference: narrowing the set fires the check on itself).
    """
    if row["component"] != "corrosion":
        return []
    set_path = comp_dir / "constraint_set.json"
    if not set_path.exists():
        return [_finding(
            "constraint_enforcement_holds", row["component"],
            "constraint set exists", expected=True, actual=False,
        )]
    try:
        cset = json.loads(set_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return [_finding(
            "constraint_enforcement_holds", row["component"],
            "constraint set readable", expected=True, actual=False,
        )]
    constraints = cset.get("constraints", [])
    if not constraints:
        return [_finding(
            "constraint_enforcement_holds", row["component"],
            "constraint set non-empty", expected=True, actual=False,
        )]
    from cairn.machines.corrosion.citation import ruling_covers_path
    findings = []
    repo_root = comp_dir
    while repo_root.name and not (repo_root / ".git").exists():
        repo_root = repo_root.parent
    for entry in constraints:
        cpath = entry.get("path", "")
        cid = entry.get("id", cpath)
        abs_path = repo_root / cpath
        if not abs_path.exists():
            covering = ruling_covers_path(cpath)
            if not covering:
                findings.append(_finding(
                    "constraint_enforcement_holds", row["component"],
                    f"constraint present: {cid}",
                    expected=True, actual=False,
                    constraint_id=cid,
                    constraint_path=cpath,
                    constraint_kind=entry.get("kind", "unknown"),
                ))
    if not any("corrosion" in str(e.get("path", "")) for e in constraints):
        findings.append(_finding(
            "constraint_enforcement_holds", row["component"],
            "constraint set includes itself",
            expected=True, actual=False,
        ))
    return findings


def history_integrity(row: dict, comp_dir: Path) -> list[dict]:
    """Working-copy history.json and state.json match their last committed version.

    Provenance: ticket state-and-history-door-catches-in-place-edits.
    The append door (transitions.emit) writes and commits atomically — the
    committed version IS the ground truth. An in-place edit changes a past entry
    silently; an uncommitted append bypasses the door. state_is_projection catches
    state-vs-history drift but not working-vs-committed drift, because an in-place
    edit changes both consistently.
    """
    import subprocess
    repo_root = comp_dir
    while repo_root.name and not (repo_root / ".git").exists():
        repo_root = repo_root.parent
    if not (repo_root / ".git").exists():
        return []
    findings = []
    for fname in ("history.json", "state.json"):
        fpath = comp_dir / fname
        if not fpath.exists():
            continue
        rel = fpath.relative_to(repo_root)
        try:
            proc = subprocess.run(
                ["git", "-C", str(repo_root), "show", f"HEAD:{rel}"],
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if proc.returncode != 0:
            continue
        try:
            working = json.loads(fpath.read_text(encoding="utf-8"))
            committed = json.loads(proc.stdout)
        except (json.JSONDecodeError, OSError):
            continue
        if fname == "history.json" and isinstance(working, list) and isinstance(committed, list):
            for i, entry in enumerate(committed):
                if i >= len(working):
                    findings.append(_finding(
                        "history_integrity", row["component"],
                        f"committed entry {i} present in working copy ({fname})",
                        expected=True, actual=False,
                        entry_index=i,
                    ))
                elif entry != working[i]:
                    findings.append(_finding(
                        "history_integrity", row["component"],
                        f"entry {i} unchanged from committed ({fname})",
                        expected=True, actual=False,
                        entry_index=i,
                    ))
            uncommitted_count = len(working) - len(committed)
            if uncommitted_count > 0:
                findings.append(_finding(
                    "history_integrity", row["component"],
                    f"all entries committed ({fname}, {uncommitted_count} uncommitted)",
                    expected=True, actual=False,
                    uncommitted_count=uncommitted_count,
                ))
        elif working != committed:
            findings.append(_finding(
                "history_integrity", row["component"],
                f"{fname} matches committed version",
                expected=True, actual=False,
            ))
    return findings


def _source_fingerprint(comp_dir: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(comp_dir):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, comp_dir)
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            with open(full, "rb") as f:
                digest.update(f.read())
            digest.update(b"\0")
    return digest.hexdigest()


def component_color(row: dict, comp_dir: Path) -> list[dict]:
    """A component whose validation seals are expired, absent, or red.

    Provenance: 2026-08-04 — Law 9 ruled as default-red by Akien: 'everything
    not working is red should have been one of the very first rules.' A component
    whose validation seals are expired or absent reads as though nothing was
    proved; the existing proofs_exist catches zero proofs, but a component with
    proofs that stopped matching its code looks green to everything except this
    sieve. Ticket green-is-earned-not-assumed.
    """
    proofs_dir = comp_dir / "proofs"
    vals_dir = comp_dir / "validations"
    proof_files = sorted(proofs_dir.glob("test_*.py")) if proofs_dir.is_dir() else []
    if not proof_files:
        return []
    current_fp = _source_fingerprint(comp_dir)
    findings = []
    for proof in proof_files:
        val_file = vals_dir / (proof.stem + ".json")
        if not val_file.exists():
            findings.append(_finding(
                "component_color", row["component"],
                f"proof {proof.name} has a validation seal",
                expected=True, actual=False,
                proof=proof.name,
                reason="no seal — never proved (Law 9)",
            ))
            continue
        try:
            records = json.loads(val_file.read_text(encoding="utf-8"))
            seal = records[-1] if isinstance(records, list) and records else records
        except (json.JSONDecodeError, OSError):
            findings.append(_finding(
                "component_color", row["component"],
                f"validation seal for {proof.name} is readable",
                expected=True, actual=False,
                proof=proof.name,
            ))
            continue
        if not isinstance(seal, dict):
            continue
        verdict = seal.get("verdict")
        if verdict != "green":
            findings.append(_finding(
                "component_color", row["component"],
                f"proof {proof.name} sealed green",
                expected=True, actual=False,
                proof=proof.name,
                verdict=verdict,
            ))
            continue
        recorded_fp = (seal.get("evidence") or {}).get("source_fingerprint")
        if recorded_fp is None or recorded_fp != current_fp:
            findings.append(_finding(
                "component_color", row["component"],
                f"proof {proof.name} fingerprint matches working tree",
                expected=True, actual=False,
                proof=proof.name,
                reason="code changed since seal — horizon closed (Law 3)",
                recorded=recorded_fp[:12] + "…" if recorded_fp else None,
                current=current_fp[:12] + "…",
            ))
    return findings


def unbuilt_intentions(census_rows: list, root: Path) -> list[dict]:
    """Intentions with no corresponding proved component — the unbuilt lots.

    Provenance: 2026-08-04 — Law 9's site-plan ruling: 'a newly minted IDEA is
    red until it's in code and running.' A site plan that only knows about
    buildings already started is not a site plan; the reddest lots are the ones
    nobody has broken ground on. Ticket green-is-earned-not-assumed.

    Not a row-level sieve: unbuilt intentions have no census row by definition.
    Called by inspect() after the sieve shake.
    """
    commons = root.parent.parent / "CairnCommons"
    intentions_dir = commons / "intentions-not-beside-code"
    if not intentions_dir.is_dir():
        return []
    census_dirs = {r["dir"] for r in census_rows}
    census_names = {r["component"] for r in census_rows}
    all_census_text = " ".join(census_dirs) + " " + " ".join(census_names)
    findings = []
    for ifile in sorted(intentions_dir.glob("I-*.md")):
        stem = ifile.stem[2:]
        slug = stem.replace("-", "_")
        words = set(stem.split("-")) - {"a", "an", "the", "is", "and", "or", "not"}
        has_component = (
            slug in all_census_text
            or stem in all_census_text
            or any(w in all_census_text for w in words if len(w) > 3)
        )
        if not has_component:
            findings.append(_finding(
                "unbuilt_intention", stem,
                "intention has a corresponding proved component",
                expected=True, actual=False,
                intention_file=ifile.name,
                reason="unbuilt lot — red by default (Law 9)",
            ))
    return findings


def durable_state_declared(row: dict, comp_dir: Path) -> list[dict]:
    """A charter declares durable_state outside db_domain.

    Provenance: ticket relational-state-goes-through-the-one-door — the data-path
    face of the sole-path rule. import_sieve catches the DRIVER (psycopg2, sqlite3);
    this catches the DATA: a charter that says where its durable state lives, and that
    answer is not db_domain. A charter with no durable_state field passes silently —
    making the field required is a separate ticket (learning-as-a-pattern).
    """
    charter_path = comp_dir / "intention+why.json"
    if not charter_path.is_file():
        return []
    try:
        charter = json.loads(charter_path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    decl = charter.get("durable_state")
    if not isinstance(decl, str) or not decl.strip():
        return []
    if decl.strip().lower() == "db_domain":
        return []
    return [_finding(
        "durable_state_declared", row["component"],
        "durable state outside db_domain",
        expected="db_domain", actual=decl,
        charter=str(charter_path),
    )]


def learning_declared(row: dict, comp_dir: Path) -> list[dict]:
    """A charter does not answer 'how does this component learn?'

    Provenance: ticket learning-as-a-pattern — every component's charter answers
    the question; 'it does not, because X' is valid; blank or missing is not.
    Checks presence and non-emptiness of the 'learns' field only — content
    quality is not this sieve's jurisdiction.
    """
    charter_path = comp_dir / "intention+why.json"
    if not charter_path.is_file():
        return []
    try:
        charter = json.loads(charter_path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    learns = charter.get("learns")
    if isinstance(learns, str) and learns.strip():
        return []
    return [_finding(
        "learning_declared", row["component"],
        "charter answers 'how does this component learn?'",
        expected=True, actual=False,
        charter=str(charter_path),
    )]


def claim_provenance(row: dict, comp_dir: Path) -> list[dict]:
    """A charter does not carry per-claim attribution (akien vs cc-read).

    Provenance: ticket a-claim-carries-its-provenance — twice in two days a CC
    definition propagated at full confidence with no mark that Akien never gave
    it.  Checks presence and non-emptiness of the 'claim_provenance' dict only —
    content quality is not this sieve's jurisdiction.
    """
    charter_path = comp_dir / "intention+why.json"
    if not charter_path.is_file():
        return []
    try:
        charter = json.loads(charter_path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    cp = charter.get("claim_provenance")
    if isinstance(cp, dict) and cp:
        return []
    return [_finding(
        "claim_provenance", row["component"],
        "charter carries per-claim attribution (claim_provenance)",
        expected=True, actual=False,
        charter=str(charter_path),
    )]


def working_tree_clean(row: dict, comp_dir: Path) -> list[dict]:
    """A component's subtree carries uncommitted changes at a crossing.

    Provenance: ticket nothing-rides-loose — the crossing half of durability
    physics. A stone cannot be promoted out of PROVEME while the code it claims
    exists only in a working tree. Uses git status --porcelain on the component's
    relative path; any output means dirt.
    """
    import subprocess
    repo_root = comp_dir
    while repo_root.name and not (repo_root / ".git").exists():
        repo_root = repo_root.parent
    if not (repo_root / ".git").exists():
        return []
    try:
        rel = comp_dir.relative_to(repo_root)
    except ValueError:
        return []
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain", str(rel)],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    dirty_lines = [l for l in proc.stdout.splitlines() if l.strip()]
    if not dirty_lines:
        return []
    return [_finding(
        "working_tree_clean", row["component"],
        "component subtree is clean (no uncommitted changes)",
        expected=True, actual=False,
        dirty_count=len(dirty_lines),
        dirty_sample=dirty_lines[:5],
    )]


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
    "address_is_resolved_never_spelled": address_is_resolved_never_spelled,
    "charter_asserts_file_present": charter_asserts_file_present,
    "crossing_fingerprints_verified": crossing_fingerprints_verified,
    "constraint_enforcement_holds": constraint_enforcement_holds,
    "history_integrity": history_integrity,
    "component_color": component_color,
    "durable_state_declared": durable_state_declared,
    "learning_declared": learning_declared,
    "claim_provenance": claim_provenance,
    "working_tree_clean": working_tree_clean,
}


_NEST_CACHE: list | None = None


def the_nest() -> list:
    """The sieves assembled coarsest-first, as [(phase, [sieve names]), ...].

    BANDS ARE PHASES (Akien, 2026-08-12, ruled; confirmed 2026-08-21). Three phases:
    preprocess (produces subjects), record (scores subjects — every current sieve),
    postprocess (picks from results — "the which is smallest is simply a post
    processing sieve"). DERIVED from what the sieve reads, never authored.
    """
    global _NEST_CACHE
    if _NEST_CACHE is None:
        phases = import_sieve.phase_of(Path(__file__).read_text())
        _NEST_CACHE = base_nest.nest(
            {name: phases.get(fn.__name__, 1) for name, fn in SIEVES.items()})
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
    # THE SUBJECT KEY IS THE ADDRESS, NOT THE NAME, and comp_dir is the measured dir
    # rather than a re-spelled ``root / name``. Both halves were the same 2026-08-13 defect,
    # found by moving the seven pre-build stages under the builder device: keyed by name,
    # the two components called ``orient`` (the tool and the builder's machine) collapsed
    # into one dict entry, so one of them was shaken twice and the other never — a component
    # silently exempt from every sieve, which is precisely "a gate that inspects nothing
    # passes everything". And ``root / row["component"]`` had been the FLAT-era spelling
    # since the rung move: it pointed at cairn/<name>/, which no longer exists for any
    # component, so every sieve reading comp_dir (state_is_projection, the charted-packet
    # judges, _component_tickets) was reading an absent directory and returning clean.
    # Vacuously green is the worst colour a gate can be.
    def fire(name, row):
        """Stamp every finding with the address it was caught at. ``component`` stays the
        bare NAME because the sieves compare on it (``!= "chart"``, the sole_path prefix),
        and because a reader wants the name first. ``at`` is what correlates a finding back
        to its row in the gradation, which is keyed by address — one place, so a finding
        cannot disagree with the subject that produced it."""
        caught = SIEVES[name](row, root / row["dir"])
        for f in caught:
            f["at"] = row["dir"]
        return caught

    shaken = base_nest.shake(nest, {row["dir"]: row for row in rows}, fire)
    # Unbuilt intentions — the site-plan scan for lots nobody has broken ground on.
    # Not a sieve (no census row), so it runs after the shake and reports separately —
    # it cannot be in gradation (no census row to grade) or in SIEVES (it is a scan,
    # not a per-row sieve), so mixing it into findings would break the invariants
    # the proof record relies on.
    unbuilt = []
    if component is None:
        unbuilt = unbuilt_intentions(rows, root)
    # ONE record, read twice. Building it twice would let the report and the verdict be
    # about different things — the exact drift a proof record exists to make impossible.
    record = proof_record(shaken["gradation"], shaken["findings"])
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
        "unbuilt_intentions": unbuilt,
        "clean": not shaken["findings"] and not unbuilt,
        # THE PROOF RECORD — every sieve that ran against every component, expected beside
        # actual, PASSES INCLUDED. Akien, 2026-08-13: "The build inspector must list EVERY
        # TEST THAT HAS PASSED ... EVERYTHING ALWAYS PROVED AND LISTING WHAT IT PROVED."
        "proof_record": record,
        # THE GATE, and the exit code comes from it rather than from a longhand `not`.
        "gate": gate.verdict(record),
    }


def proof_record(gradation: dict, findings: list) -> list[dict]:
    """Every sieve × every component as one proof entry: expected 1.0, actual the score.

    THE LIST OF WHAT PASSED IS THE POINT, and it is what a findings report throws away. A
    findings list is only the failures, so an empty one means "everything passed" and "no
    sieve ran" and "the census found no components" all at once, and nothing downstream can
    tell them apart — which is a gate whose green is a green about SILENCE. Here a sieve
    that stops running vanishes from the record, so the list gets SHORTER rather than
    CLEANER, and the difference is readable.

    The scores are already measured; this does not re-judge anything. It states the
    expectation (1.0 — a sieve passes) beside what the shake actually came to rest on, in
    the seed shape every gate in the system emits (gate.proved).
    """
    by_site = {}
    for f in findings:
        by_site.setdefault((f.get("method"), f.get("at")), []).append(f)
    out = []
    for at in sorted(gradation):
        for sieve_name in sorted(gradation[at]):
            score = gradation[at][sieve_name]
            out.append(gate.proved(
                identity=sieve_name,
                location=at,
                code=f"cairn/machines/build_inspector/inspector.py:{sieve_name}",
                expected=1.0,
                actual=score,
                source="build_inspector",
                findings=by_site.get((sieve_name, at), []),
            ))
    return out


def _main(argv: list[str]) -> int:
    report = inspect(component=argv[0] if argv else None)
    print(json.dumps(report, indent=2))
    return 0 if report["gate"]["opens"] else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
