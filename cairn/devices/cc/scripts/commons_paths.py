"""commons_paths.py <id> — the dirty commons paths that belong to ticket <id>, one per line.

Run with cwd = the commons. close.sh and prove.sh stage exactly these, so a crossing never commits
another ticket's records under its own subject (ticket d3b8cdf81a41; measured 2026-11-19: 17 close/prove
commits carried a foreign ticket's records when they staged 'git add -A tickets/ ...').

A path belongs to <id> when it is tickets/<id>-*, certificates/<id>-* or outline_checks/<id>-*, or a
questions/ or berths/ JSON whose top-level "ticket" is <id> (their names do not carry it). The shared
journal is always selected when dirty: it is one append-only chain, and the artifact check verifies it
whole. A bound JSON that cannot be read is not selected, and is named on stderr.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # the repo root, so the helper imports
try:
    from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs
except ImportError:   # a transient script copy has no tree beside it: no flags, same behaviour as before
    def windowless_kwargs(*_a, **_k):
        return {}

PREFIXED = ("tickets/", "certificates/", "outline_checks/")
BOUND = ("questions/", "berths/")
JOURNAL = ".artifact-journal.jsonl"


def _dirty() -> list[str]:
    out = subprocess.run(["git", "status", "--porcelain", "-uall", "-z"],
                         capture_output=True, text=True, check=True,
                         **windowless_kwargs()).stdout
    tokens = out.split("\0")
    paths, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        i += 1
        if len(t) < 4:
            continue
        paths.append(t[3:])
        if t[0] in "RC":  # a rename carries its source path next; the source is staged as deleted too
            paths.append(tokens[i])
            i += 1
    return paths


def _bound_ticket(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:  # deleted: its last committed bytes say whose it was
        r = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, **windowless_kwargs())
        if r.returncode != 0:
            return None
        text = r.stdout
    try:
        doc = json.loads(text)
    except ValueError as exc:
        print(f"commons_paths: {path} is not readable JSON ({exc}); not selected", file=sys.stderr)
        return None
    return doc.get("ticket") if isinstance(doc, dict) else None


def own_paths(tid: str) -> list[str]:
    own = []
    for p in _dirty():
        if p == JOURNAL:
            own.append(p)
        elif p.startswith(PREFIXED):
            if p.split("/", 1)[1].startswith(f"{tid}-"):
                own.append(p)
        elif p.startswith(BOUND) and p.endswith(".json"):
            if _bound_ticket(p) == tid:
                own.append(p)
    return own


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not argv[0]:
        print("usage: commons_paths.py <ticket id>   (cwd = the commons)", file=sys.stderr)
        return 2
    for p in own_paths(argv[0]):
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
