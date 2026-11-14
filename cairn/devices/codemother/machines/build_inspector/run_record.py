"""run_record — persistent check-run records for cross-run comparison.

Ticket: the-proof-record-persists-so-runs-can-be-compared (2026-08-14).
The founding defect: inspect() computes a full record per run and discards it,
so a sieve that silently stops running shortens the list with nobody told.

Three capabilities behind one door:
  persist_run(result, surface, records_dir)  — write one run record
  compare_runs(old, new)                     — diff two records
  never_redded(records_dir)                  — checks green in every recorded run

Green is recorded alongside red: a record of failures cannot distinguish a green
from an absence, which is the entire disease (Law 7).

build_inspector is the first tenant; the format is shared so other surfaces
(derivation gate, ruling intake, emit chokepoint, tester) can adopt it under
their own owners (Law 6).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def persist_run(result: dict, surface: str, records_dir: str | Path) -> Path:
    """Persist an inspect() result as a timestamped run record.

    The record captures every component×sieve score — green AND red.
    Returns the path of the written record.
    """
    records_dir = Path(records_dir)
    run_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    checks: dict[str, dict[str, dict[str, Any]]] = {}
    for comp, sieves in result.get("gradation", {}).items():
        checks[comp] = {}
        for sieve, score in sieves.items():
            checks[comp][sieve] = {"score": score}

    record = {
        "run_id": run_id,
        "timestamp": ts,
        "surface": surface,
        "scope": result.get("scope"),
        "components_inspected": result.get("components_inspected", 0),
        "sieves_run": result.get("sieves_run", []),
        "checks": checks,
    }

    records_dir.mkdir(parents=True, exist_ok=True)
    ts_slug = ts[:19].replace(":", "").replace("-", "").replace("T", "T")
    filename = f"run-{ts_slug}-{run_id[:8]}.json"
    path = records_dir / filename
    path.write_text(json.dumps(record, indent=2, sort_keys=False), encoding="utf-8")
    return path


def read_run(path: str | Path) -> dict:
    """Load a run record from disk."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _flatten_checks(checks: dict) -> dict[tuple[str, str], float]:
    """Flatten {comp: {sieve: {score: N}}} to {(comp, sieve): score}."""
    out: dict[tuple[str, str], float] = {}
    for comp, sieves in checks.items():
        for sieve, data in sieves.items():
            out[(comp, sieve)] = data.get("score", 0.0)
    return out


def compare_runs(old: dict, new: dict) -> dict:
    """Compare two run records. Returns {added, removed, changed}.

    - added: checks in new but not old (new sieve or new component)
    - removed: checks in old but not new (silent stop — the founding symptom)
    - changed: checks in both with different scores (verdict changed)
    """
    old_flat = _flatten_checks(old.get("checks", {}))
    new_flat = _flatten_checks(new.get("checks", {}))

    old_keys = set(old_flat.keys())
    new_keys = set(new_flat.keys())

    added = [
        {"component": k[0], "sieve": k[1], "score": new_flat[k]}
        for k in sorted(new_keys - old_keys)
    ]
    removed = [
        {"component": k[0], "sieve": k[1], "score": old_flat[k]}
        for k in sorted(old_keys - new_keys)
    ]
    changed = []
    for k in sorted(old_keys & new_keys):
        if old_flat[k] != new_flat[k]:
            changed.append({
                "component": k[0],
                "sieve": k[1],
                "old_score": old_flat[k],
                "new_score": new_flat[k],
            })

    return {"added": added, "removed": removed, "changed": changed}


def list_runs(records_dir: str | Path) -> list[Path]:
    """List all run records in chronological order (by filename)."""
    records_dir = Path(records_dir)
    if not records_dir.is_dir():
        return []
    return sorted(records_dir.glob("run-*.json"))


def never_redded(records_dir: str | Path) -> set[tuple[str, str]]:
    """Identify checks that have scored 1.0 in every recorded run.

    Returns a set of (component, sieve) tuples. An empty set with zero
    runs is correct — nothing has been measured, so nothing qualifies.
    """
    runs = list_runs(records_dir)
    if not runs:
        return set()

    first = read_run(runs[0])
    candidates = {
        (comp, sieve)
        for comp, sieves in first.get("checks", {}).items()
        for sieve, data in sieves.items()
        if data.get("score", 0.0) == 1.0
    }

    for run_path in runs[1:]:
        run = read_run(run_path)
        flat = _flatten_checks(run.get("checks", {}))
        candidates = {k for k in candidates if flat.get(k, 0.0) == 1.0}

    return candidates
