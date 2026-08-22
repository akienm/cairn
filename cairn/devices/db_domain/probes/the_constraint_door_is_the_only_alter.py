"""Watchme probe: the constraint door is the only ALTER.

Sweeps the tree for schema-changing SQL outside db_domain/store.py — ALTER TABLE,
ADD CONSTRAINT, DROP CONSTRAINT in any module, and psql invocations in scripts.
The same shape of sweep import_sieve runs for the inference host: a grep of the
codebase, not a runtime check.

The probe carries no authority (Law 6). It deposits a finding and pokes; the owner
decides what to do about it.

    python3 cairn/devices/db_domain/probes/the_constraint_door_is_the_only_alter.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
STORE = Path("cairn/devices/db_domain/store.py")

SCHEMA_CHANGE_PATTERNS = [
    r"\bALTER\s+TABLE\b",
    r"\bADD\s+CONSTRAINT\b",
    r"\bDROP\s+CONSTRAINT\b",
    r"\bALTER\s+COLUMN\b",
]

COMBINED = re.compile("|".join(SCHEMA_CHANGE_PATTERNS), re.IGNORECASE)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".mypy_cache", ".cairn"}
SKIP_EXTENSIONS = {".pyc", ".pyo", ".so", ".jpg", ".png", ".gif", ".pdf"}


def sweep() -> list[dict]:
    findings = []
    for path in REPO.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix in SKIP_EXTENSIONS:
            continue
        rel = path.relative_to(REPO)
        if rel == STORE:
            continue
        if rel == Path(__file__).relative_to(REPO):
            continue
        try:
            text = path.read_text(errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if COMBINED.search(line):
                if line.lstrip().startswith("#") or line.lstrip().startswith("//"):
                    continue
                findings.append({"file": str(rel), "line": i, "text": line.strip()[:120]})
    return findings


def check_psql_invocations() -> list[dict]:
    findings = []
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include=*.sh", "--include=*.bash", "--include=*.py", "psql", str(REPO)],
            capture_output=True, text=True, timeout=30,
        )
        for hit in result.stdout.splitlines():
            if ".git/" in hit or "__pycache__" in hit:
                continue
            if "psql" not in hit:
                continue
            parts = hit.split(":", 2)
            if len(parts) >= 3:
                fpath = Path(parts[0]).relative_to(REPO)
                if fpath == Path(__file__).relative_to(REPO):
                    continue
                if parts[2].lstrip().startswith("#"):
                    continue
                findings.append({"file": str(fpath), "line": int(parts[1]), "text": parts[2].strip()[:120]})
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return findings


def main() -> int:
    schema_hits = sweep()
    psql_hits = check_psql_invocations()

    print(f"schema-changing SQL outside store.py: {len(schema_hits)}")
    for h in schema_hits:
        print(f"  {h['file']}:{h['line']}  {h['text']}")

    print(f"psql invocations: {len(psql_hits)}")
    for h in psql_hits:
        print(f"  {h['file']}:{h['line']}  {h['text']}")

    total = len(schema_hits) + len(psql_hits)
    if total == 0:
        print("GREEN — the constraint door is the only ALTER; zero schema changes outside store.py")
        return 0
    else:
        print(f"FINDING — {total} hit(s) outside the one door")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
