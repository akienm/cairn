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
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# Deliberate reuse, on the record: orient's scans are the measuring layer under these
# filters (device_census feeds every row-judging filter). This is the first evidence on
# orient's filed edge (e) — scans-vs-filters as one shared library — earned by use, not
# merged on symmetry. The registries stay separate: a scan MEASURES, a filter JUDGES.
from cairn.charter import projector  # noqa: E402
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
    went-red-silently gap, systemic.
    """
    if not row["device_subclasses"] or row["emit_call_sites_outside_proofs"] > 0:
        return []
    return [_finding(
        "silent_device", row["component"],
        "subclasses BaseDevice (inherits emit()) but never calls it outside proofs",
        {"device_subclasses": row["device_subclasses"], "emit_call_sites_outside_proofs": 0},
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


FILTERS = {
    "charter_on_disk": charter_on_disk,
    "proofs_exist": proofs_exist,
    "silent_device": silent_device,
    "state_is_projection": state_is_projection,
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
