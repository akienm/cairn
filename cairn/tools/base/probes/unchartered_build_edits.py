"""PROBE — build-time-discoveries-that-never-re-entered

Berth for the WATCHME that ticket
``a-build-discovery-re-enters-the-chain`` carries.
Berthed beside ``cairn/tools/base`` because that is WHERE THE CROSSING LIVES
— the emit chokepoint that this detector would gate.

THE QUESTION: across closed voyages, does the detector find files the build
modified that the chain never mentioned? A non-empty finding is a discovery
that never re-entered as a new node. A vacuous scan (zero voyages examined)
is reported separately — it is indistinguishable from a clean history at
exactly the moment the probe has stopped working.

THE RESOLUTION GAP, named not hidden: a voyage's git footprint is found by
searching git log for the ticket ID. Commits that don't mention the ticket
ID are invisible to this probe. The carry names how many voyages could not
be resolved this way, so a reader can tell a clean run from a blind one.
"""

from __future__ import annotations

import json
import os
import subprocess

from cairn.tools.base.probe import Probe, owning_ticket, once
from cairn.tools.chain.chain import charted_paths, uncharted_modifications

_OWNING_TICKET = "a-build-discovery-re-enters-the-chain"
_TICKETS_DIR = os.path.expanduser("~/dev/src/CairnCommons/tickets")
_CAIRN_DIR = os.path.expanduser("~/dev/src/cairn")
_ENOUGH_VOYAGES = 5
_ENOUGH_FILES = 1
_MAX_COMMITS_PER_VOYAGE = 10


def _proved_tickets_with_chains() -> list[dict]:
    """PROVED tickets whose chart chain actually stands in the berth store.

    THE CHAIN IS THE MEASUREMENT; ``chart_claim`` IS THE TICKET'S CLAIM ABOUT ITSELF, and
    this function used to gate on the claim with ``os.path.isfile(chart_claim)``. Measured
    2026-09-07 over the 196 PROVED tickets, that field has three shapes and the gate handled
    none of them: 183 hold PROSE naming a bare filename (``"chart chain complete:
    verdict-20260828T062348-43017cace664.json"``) — never a path, so ``isfile`` was False
    and the ticket was skipped; 12 hold a DICT of berth paths, and ``os.path.isfile(dict)``
    RAISES TypeError; 1 holds null. The raise landed in the shim's per-probe isolation, so
    this watch has read as healthy while being dead since 2026-08-28 — which is the shape
    "armed by hand is not the same as wired" keeps taking.

    So the claim is no longer consulted at all. ``chain_for_ticket`` reads the berth store
    directly and answers the question the filter was reaching for, authoritatively (Law 3:
    the measurement outranks the assertion about it). A ticket that claims a chart it does
    not have is a real defect and it belongs to
    ``no_component_reaches_proved_with_an_uncharted_build``, which measures exactly that;
    checking it a second time HERE, badly, bought nothing and cost the watch."""
    from cairn.devices.codemother.machines.verdict.verdict import chain_for_ticket

    results = []
    for name in sorted(os.listdir(_TICKETS_DIR)):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        path = os.path.join(_TICKETS_DIR, name)
        try:
            t = json.load(open(path))
        except (OSError, ValueError):
            continue
        state = t.get("workflow_and_state", "")
        if "[PROVED]" not in state:
            continue
        tid = t.get("id", name.removesuffix(".json"))
        chain = chain_for_ticket(tid)
        if not chain or not any(chain.values()):
            continue
        results.append({"id": tid, "chain": chain})
    return results


def _voyage_modified_files(ticket_id: str) -> list[str] | None:
    """Modified files for a voyage, found via git log --grep on the ticket ID.

    Returns None if no commits mention this ticket — the voyage is unresolvable.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--format=%H", f"--grep={ticket_id}"],
            capture_output=True, text=True, cwd=_CAIRN_DIR, timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    commits = [h for h in result.stdout.strip().split("\n") if h]
    if not commits:
        return None
    if len(commits) > _MAX_COMMITS_PER_VOYAGE:
        return None
    modified = set()
    for commit in commits:
        try:
            dt = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "-r", "--name-only",
                 "--diff-filter=M", commit],
                capture_output=True, text=True, cwd=_CAIRN_DIR, timeout=10,
            )
        except (subprocess.TimeoutExpired, OSError):
            continue
        for line in dt.stdout.strip().split("\n"):
            if line:
                modified.add(line)
    return sorted(modified) if modified else []


def _voyage_added_files(ticket_id: str) -> list[str]:
    """Added files for a voyage, same resolution method."""
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--format=%H", f"--grep={ticket_id}"],
            capture_output=True, text=True, cwd=_CAIRN_DIR, timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []
    commits = [h for h in result.stdout.strip().split("\n") if h]
    if len(commits) > _MAX_COMMITS_PER_VOYAGE:
        return []
    added = set()
    for commit in commits:
        try:
            dt = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "-r", "--name-only",
                 "--diff-filter=A", commit],
                capture_output=True, text=True, cwd=_CAIRN_DIR, timeout=10,
            )
        except (subprocess.TimeoutExpired, OSError):
            continue
        for line in dt.stdout.strip().split("\n"):
            if line:
                added.add(line)
    return sorted(added)


def survey() -> dict:
    """Full survey across all closed voyages."""
    tickets = _proved_tickets_with_chains()
    examined = []
    unresolvable = []
    total_uncharted = []

    for t in tickets:
        tid = t["id"]
        modified = _voyage_modified_files(tid)
        if modified is None:
            unresolvable.append(tid)
            continue
        added = _voyage_added_files(tid)
        charted = charted_paths(t["chain"])
        findings = uncharted_modifications(charted, modified, added)
        examined.append({
            "ticket": tid,
            "modified_count": len(modified),
            "added_count": len(added),
            "charted_count": len(charted),
            "uncharted": findings,
        })
        total_uncharted.extend(findings)

    return {
        "voyages_examined": len(examined),
        "voyages_unresolvable": len(unresolvable),
        "unresolvable_ids": unresolvable,
        "total_uncharted_files": len(total_uncharted),
        "per_voyage": examined,
    }


def _trigger(now, context: dict) -> bool:
    s = once(context, "survey", survey)
    if s["total_uncharted_files"] > 0:
        return True
    if s["voyages_examined"] == 0:
        return True
    return False


def _enough(context: dict) -> bool:
    s = once(context, "survey", survey)
    if s["voyages_examined"] < _ENOUGH_VOYAGES:
        return False
    if s["total_uncharted_files"] < _ENOUGH_FILES:
        return False
    return True


def _carry(context: dict) -> dict:
    s = once(context, "survey", survey)
    if s["voyages_examined"] == 0:
        finding = (
            "VACUITY — zero voyages resolved. The probe examined "
            f"{len(s.get('unresolvable_ids', []))} proved tickets but none had "
            "commits mentioning the ticket ID. At this count the probe is not "
            "working, and a clean-history report would be false"
        )
    elif s["total_uncharted_files"] > 0:
        uncharted_per = [
            f"{v['ticket']}: {v['uncharted']}" for v in s["per_voyage"]
            if v["uncharted"]
        ]
        finding = (
            f"{s['total_uncharted_files']} uncharted files across "
            f"{s['voyages_examined']} examined voyages. "
            f"Named: {'; '.join(uncharted_per)}"
        )
    else:
        finding = (
            f"ACCUMULATING — {s['voyages_examined']}/{_ENOUGH_VOYAGES} voyages "
            f"examined, {s['total_uncharted_files']} uncharted files so far"
        )
    return {
        "finding": finding,
        "survey": s,
        "ticket": owning_ticket(_OWNING_TICKET),
    }


_HORIZON = 1000

PROBE = Probe(
    why="a file the build modified that is named nowhere in the chain's own "
        "berths is a discovery that never re-entered as a new node. This probe "
        "watches closed voyages for that pattern — the detector's efficacy "
        "measured over real builds, not over seeded chains",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "build-time-discoveries-that-never-re-entered"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey()
    print(json.dumps({
        "survey": s,
        "would_trigger": _trigger(None, {"survey": s}),
        "enough": _enough({"survey": s}),
        "carry": _carry({"survey": s}),
    }, indent=2, default=str))
