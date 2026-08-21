"""plan_inspector — reads the plan against itself.

The build_inspector checks code against code; this checks the PLAN's claims
against the PLAN's own admissions. It reads charters, not code.

First tooth: a component whose filed_edges contain open items — the component's
own record of what it does not yet do. Cross-referenced with ticket state to
detect "done on the build order, not done by its own admission."

Provenance: 2026-07-26 — Akien asked for a step-back sanity check and CC found
three components reading as done while their own filed_edges said otherwise.
The hand-run became the instrument (Law 1).

CLI (inference-free):
  python3 -m cairn.machines.plan_inspector.inspector            # whole repo
  python3 -m cairn.machines.plan_inspector.inspector <component>  # one component
Exit 0 = clean, 1 = findings.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _finding(sieve_name: str, component: str, finding: str, evidence: dict,
             why: str, score: float = 0.0) -> dict:
    return {
        "sieve": sieve_name,
        "component": component,
        "finding": finding,
        "evidence": evidence,
        "score": score,
        "why_it_matters": why,
    }


def _strip_letter_prefix(s: str) -> str:
    """Remove a leading '(x) ' or '(xx) ' prefix from a filed edge."""
    stripped = re.sub(r'^\([a-z]+\)\s*', '', s)
    return stripped


def _is_closed(edge) -> bool:
    """An edge is closed if it starts with CLOSED (after any letter prefix)."""
    s = _strip_letter_prefix(str(edge).strip())
    return s.startswith("[CLOSED") or s.startswith("CLOSED")


def _is_landed(edge) -> bool:
    """An edge that says LANDED or BUILT + PROVEN is effectively closed work."""
    s = _strip_letter_prefix(str(edge).strip())
    return (s.startswith("[LANDED") or s.startswith("LANDED")
            or "BUILT + PROVEN" in s[:120] or "BUILT + PROVED" in s[:120])


def _edge_summary(edge: str, max_len: int = 150) -> str:
    s = str(edge).strip()
    return s[:max_len] + "..." if len(s) > max_len else s


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _find_charters(root: Path = _REPO_ROOT) -> list[tuple[str, Path, dict]]:
    """Find all intention+why.json files and return (component_name, path, data)."""
    charters = []
    for p in sorted(root.rglob("intention+why.json")):
        if "__pycache__" in str(p) or ".cairn" in str(p):
            continue
        try:
            data = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        comp_name = data.get("component", data.get("role", _rel(p.parent, root)))
        charters.append((comp_name, p, data))
    return charters


# ── sieve: open filed edges ─────────────────────────────────────────────────

def open_filed_edges(component: str, charter: dict, charter_path: Path,
                     root: Path = _REPO_ROOT) -> list[dict]:
    """A component with open filed_edges — unbuilt work the component admits to.

    Provenance: the founding measurement, 2026-07-26 — inference_domain, db_domain
    and web_server each had open edges while the build order read them as done.
    """
    edges = charter.get("filed_edges", [])
    if not edges:
        return []

    open_edges = []
    closed_count = 0
    for edge in edges:
        if _is_closed(edge) or _is_landed(edge):
            closed_count += 1
        else:
            open_edges.append(edge)

    if not open_edges:
        return []

    return [_finding(
        "open_filed_edges", component,
        f"{len(open_edges)} open filed edge(s) ({closed_count} closed)",
        {
            "charter": _rel(charter_path, root),
            "open_count": len(open_edges),
            "closed_count": closed_count,
            "open_edges": [_edge_summary(e) for e in open_edges],
        },
        "Law 5 / Law 7: a component's own filed_edges are its record of what it "
        "does not yet do. Open edges are not defects — they are honest admissions. "
        "The finding is when a planning surface reads the component as complete "
        "while the component says otherwise.",
    )]


# ── sieve: charter asserts things the code cannot deliver ────────────────────

def charter_asserts_unbuilt(component: str, charter: dict, charter_path: Path,
                           root: Path = _REPO_ROOT) -> list[dict]:
    """A charter whose filed_edges explicitly name unbuilt dependencies.

    Looks for edges containing patterns like 'not yet wired', 'not yet built',
    'deferred', 'not built', 'wants', 'waits on'.
    """
    edges = charter.get("filed_edges", [])
    if not edges:
        return []

    unbuilt_patterns = [
        r'\bnot yet (?:wired|built|implemented|connected|applied)\b',
        r'\bdeferred\b',
        r'\bwaits? on\b',
        r'\bwanting\b',
        r'\bnot (?:built|wired|implemented|connected)\b',
    ]

    unbuilt_edges = []
    for edge in edges:
        if _is_closed(edge) or _is_landed(edge):
            continue
        s = str(edge)
        for pat in unbuilt_patterns:
            if re.search(pat, s, re.IGNORECASE):
                unbuilt_edges.append(edge)
                break

    if not unbuilt_edges:
        return []

    return [_finding(
        "charter_asserts_unbuilt", component,
        f"{len(unbuilt_edges)} filed edge(s) explicitly name unbuilt work",
        {
            "charter": _rel(charter_path, root),
            "unbuilt_edges": [_edge_summary(e) for e in unbuilt_edges],
        },
        "The component's own charter names work it knows is not done. If "
        "downstream work is planned against this component as complete, "
        "that plan is wrong by the component's own admission.",
    )]


# ── the run ──────────────────────────────────────────────────────────────────

_SIEVES = [open_filed_edges, charter_asserts_unbuilt]


def inspect(component_filter: str | None = None,
            root: Path = _REPO_ROOT) -> list[dict]:
    """Run all sieves over all charters (or one component)."""
    charters = _find_charters(root)
    findings = []

    for comp_name, charter_path, charter_data in charters:
        if component_filter and component_filter not in comp_name:
            continue
        for sieve in _SIEVES:
            findings.extend(sieve(comp_name, charter_data, charter_path, root=root))

    return findings


def _format_findings(findings: list[dict]) -> str:
    if not findings:
        return "plan_inspector: clean — no findings.\n"

    lines = [f"plan_inspector: {len(findings)} finding(s)\n"]
    for f in findings:
        lines.append(f"  [{f['sieve']}] {f['component']}")
        lines.append(f"    {f['finding']}")
        ev = f.get("evidence", {})
        if "open_edges" in ev:
            for e in ev["open_edges"]:
                lines.append(f"      - {e}")
        elif "unbuilt_edges" in ev:
            for e in ev["unbuilt_edges"]:
                lines.append(f"      - {e}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    comp = sys.argv[1] if len(sys.argv) > 1 else None
    findings = inspect(comp)
    print(_format_findings(findings))
    sys.exit(1 if findings else 0)
