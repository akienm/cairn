"""/sail's first act after loading the ticket: sweep both trees clean before the voyage.

Any uncommitted change standing in cairn or CairnCommons when a voyage starts is stashed
(``git stash push -u``, one stash per dirty repo, named by its commit sha — which does not
shift the way ``stash@{n}`` does) and raised as ONE trouble, ``orphaned-changes-at-sail``,
naming every path, every stash sha and the timing suspects: the ticket the newest commons
journal line under ``tickets/`` names, then Akien. A clean tree stashes and raises nothing.

Provenance: ticket 92e0d158b1bc (ruling 8w layer 2, narrowed by F11, cleared by 8x "yes to
all."), replacing 7bb99eed0629. The dirt list is orient's repo_truth ``dirty`` (5ea592dc82ca).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

IDENTITY = "orphaned-changes-at-sail"
_TICKET_PATH = re.compile(r"^tickets/([0-9a-f]{12})-")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def suspects(journal: Path) -> list[str]:
    """The ticket the newest journal line under tickets/ names, then Akien."""
    try:
        lines = journal.read_text().splitlines()
    except OSError:
        return ["Akien"]
    for line in reversed(lines):
        try:
            m = _TICKET_PATH.match(json.loads(line).get("path", ""))
        except (ValueError, AttributeError):
            continue
        if m:
            return [m.group(1), "Akien"]
    return ["Akien"]


def sweep(repos: list[Path] | None = None, *, ticket: str = "", raiser=None,
          journal: Path | None = None, now=None) -> dict | None:
    from cairn.tools.orient.orient import repo_truth
    if repos is None or journal is None:
        from cairn.tools.base.address import ROOTS
        repos = repos if repos is not None else [ROOTS["repo"], ROOTS["commons"]]
        if journal is None:
            from cairn.tools.artifact.artifact import journal_path
            journal = journal_path(ROOTS["commons"])
    repos = [Path(r) for r in repos]
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    rows = repo_truth(repos=repos)["measured"]["repos"]
    swept = []
    for repo, row in zip(repos, rows):
        dirty = row.get("dirty") or []
        if not dirty:
            continue
        _git(repo, "stash", "push", "-u", "-m", f"sail-sweep {ticket} {stamp}")
        swept.append({"repo": str(repo), "paths": dirty, "stash": _git(repo, "rev-parse", "stash@{0}")})
    if not swept:
        return None
    if raiser is None:
        from cairn.tools.base.diagnostic import ModuleRaiser
        raiser = ModuleRaiser("sail")
    return raiser.raise_trouble(
        IDENTITY,
        why="uncommitted changes stood in the tree when a voyage started; stashed so the voyage "
            "starts clean — probably leftover work from the last ticket, or Akien",
        detail={"ticket": ticket, "repos": swept, "suspects": suspects(journal),
                "restore": "git -C <repo> stash apply <sha>"})


def main(argv: list[str]) -> int:
    record = sweep(ticket=argv[0] if argv else "")
    print("clean" if record is None else json.dumps(record, indent=1, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
