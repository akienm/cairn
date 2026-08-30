"""PROBE — at-rest history/state integrity

Fires when any component's history.json or state.json differs from its last
committed version. The build_inspector's history_integrity sieve catches this
at crossing time; this probe catches it between crossings, on the beat.

Berths beside the cairn device because it watches the whole tree's state/history
files — the cairn device owns the build_inspector as a machine.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cairn.tools.base.probe import Probe

_CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_HORIZON = 1000


def _scan() -> list[dict]:
    """Walk the tree, compare each history.json/state.json against committed."""
    repo_root = _CAIRN_ROOT
    if not (repo_root / ".git").exists():
        return []
    findings = []
    for fname in ("history.json", "state.json"):
        for fpath in sorted(repo_root.rglob(fname)):
            rel = fpath.relative_to(repo_root)
            parts = rel.parts
            if any(p.startswith(".") or p in {"__pycache__", "node_modules", "venv"}
                   for p in parts):
                continue
            try:
                proc = subprocess.run(
                    ["git", "-C", str(repo_root), "show", f"HEAD:{rel}"],
                    capture_output=True, text=True, timeout=10,
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
            if working != committed:
                comp = str(rel.parent)
                findings.append({
                    "component": comp,
                    "file": fname,
                    "detail": f"{comp}/{fname} differs from committed version",
                })
    return findings


def _trigger(now, context: dict) -> bool:
    findings = context.get("findings")
    if findings is None:
        findings = _scan()
        context["findings"] = findings
    return len(findings) > 0


def _carry(context: dict) -> dict:
    findings = context.get("findings")
    if findings is None:
        findings = _scan()
    return {
        "finding": f"{len(findings)} component(s) with uncommitted state/history changes",
        "components": [f["component"] for f in findings],
        "details": findings,
    }


PROBE = Probe(
    why="a component at rest between voyages is never crossed, so the "
        "build_inspector's history_integrity sieve never fires on it. This "
        "probe fires the same comparison on the beat, closing the temporal gap.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "triage", "kind": "efficacy"},
    carry=_carry,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    findings = _scan()
    print(json.dumps({
        "findings": findings,
        "would_trigger": len(findings) > 0,
    }, indent=2))
