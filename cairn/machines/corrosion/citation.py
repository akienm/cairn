"""Ruling-citation detector for the corrosion predicate.

Given a constraint-bearing artifact's path, determines whether a confirmed
ruling in CairnCommons/decisions/ covers the change. The ticket defines
'a ruling in the same act' as: a ruling packet whose id is cited in the
commit that weakened the constraint, or which lands in the same commit.

This implementation checks two things:
  1. Does a confirmed ruling's what_conforms include this path?
  2. Was a ruling file co-committed with the change to this path?
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

_CAIRN_ROOT = Path(__file__).resolve().parents[3]
_COMMONS_ROOT = _CAIRN_ROOT.parent / "CairnCommons"


def _rulings_store() -> Path:
    return _COMMONS_ROOT / "decisions"


def ruling_covers_path(rel_path: str) -> str | None:
    """Return the id of a confirmed ruling whose what_conforms includes rel_path, or None.

    A ruling covers a path when:
      - It is kind: "ruling" (not a legacy decision)
      - It is confirmed (has a confirmed field)
      - Its what_conforms list includes the path (exact match or prefix match)
    """
    store = _rulings_store()
    if not store.is_dir():
        return None
    for name in sorted(store.iterdir()):
        if not name.suffix == ".json":
            continue
        try:
            record = json.loads(name.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(record, dict):
            continue
        if record.get("kind") != "ruling":
            continue
        if not record.get("confirmed"):
            continue
        for p in record.get("what_conforms") or []:
            if p == rel_path or rel_path.startswith(p + "/"):
                return record.get("id")
    return None


def ruling_cited_in_commit(rel_path: str, commit: str | None = None,
                           repo: Path | None = None) -> str | None:
    """Check if a ruling was cited in the commit that last changed rel_path.

    Returns the ruling id if found, None otherwise.

    'Cited' means:
      - The commit message contains a ruling id (a YYYY-MM-DD-slug pattern
        matching a file in CairnCommons/decisions/), OR
      - A file in CairnCommons/decisions/ was also changed in the same commit
    """
    repo = repo or _CAIRN_ROOT
    if commit is None:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), "log", "-1", "--format=%H", "--", rel_path],
                capture_output=True, text=True, timeout=10)
            commit = result.stdout.strip()
        except Exception:
            return None
    if not commit:
        return None

    try:
        msg_result = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%B", commit],
            capture_output=True, text=True, timeout=10)
        message = msg_result.stdout
    except Exception:
        message = ""

    store = _rulings_store()
    if not store.is_dir():
        return None
    ruling_ids = set()
    for name in store.iterdir():
        if name.suffix == ".json":
            stem = name.stem
            ruling_ids.add(stem)

    for rid in ruling_ids:
        if rid in message:
            return rid

    try:
        files_result = subprocess.run(
            ["git", "-C", str(repo), "diff-tree", "--no-commit-id", "-r",
             "--name-only", commit],
            capture_output=True, text=True, timeout=10)
        changed_files = files_result.stdout.strip().splitlines()
    except Exception:
        changed_files = []

    commons_rel = os.path.relpath(str(store), str(repo))
    for f in changed_files:
        if f.startswith(commons_rel) or f.startswith("CairnCommons/decisions/"):
            stem = Path(f).stem
            if stem in ruling_ids:
                return stem

    return None
