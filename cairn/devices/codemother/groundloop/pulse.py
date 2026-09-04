"""codemother/groundloop/pulse.py — commit watcher on the heartbeat.

On each beat, checks git for new commits since the last beat. When found,
calls codemother's on_commit() directly — the pulse IS the bridge between
git and the watcher face, not the probe (which remains a liveness check
on the watcher's output).

State (last-seen HEAD) persists to instance-space so a restart doesn't
replay history. On first run or after a state loss, seeds from current HEAD
without firing — the watcher watches forward, not backward.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from cairn.tools.base.address import instance_path

_STATE_DIR = instance_path("codemother", 0) / "watch"
_STATE_FILE = _STATE_DIR / "last_seen_head.json"

_last_head: str | None = None


def _read_state() -> str | None:
    global _last_head
    if _last_head is not None:
        return _last_head
    try:
        data = json.loads(_STATE_FILE.read_text())
        _last_head = data.get("head")
        return _last_head
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def _write_state(head: str) -> None:
    global _last_head
    _last_head = head
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"head": head}) + "\n")
    os.replace(tmp, _STATE_FILE)


def _git(*args: str) -> str:
    repo_root = Path(__file__).resolve().parents[4]
    result = subprocess.run(
        ["git", "-C", str(repo_root)] + list(args),
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip()


def on_pulse(now, context: dict) -> dict:
    """Called each heartbeat beat. Detect new commits and fire the watcher."""
    try:
        current_head = _git("rev-parse", "HEAD")
    except Exception as e:
        return {"outcome": "git_unavailable", "error": str(e)}

    if not current_head:
        return {"outcome": "no_head"}

    last_head = _read_state()

    if last_head is None:
        _write_state(current_head)
        return {"outcome": "seeded", "head": current_head[:8]}

    if current_head == last_head:
        return {"outcome": "no_new_commits"}

    log_output = _git("log", "--oneline", f"{last_head}..{current_head}")
    if not log_output:
        _write_state(current_head)
        return {"outcome": "head_moved_no_log", "head": current_head[:8]}

    commits = []
    for line in log_output.strip().split("\n"):
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append({"hash": parts[0], "message": parts[1]})

    _write_state(current_head)

    results = []
    for commit in commits:
        diff_output = _git("diff-tree", "--no-commit-id", "-r", "--name-only", commit["hash"])
        changed_files = [f for f in diff_output.split("\n") if f] if diff_output else []

        try:
            from cairn.devices.codemother.watch import on_commit
            result = on_commit(commit["hash"], changed_files, commit["message"])
            results.append({"commit": commit["hash"][:8], "areas": result.get("areas_checked", 0),
                            "findings": len(result.get("results", []))})
        except Exception as e:
            results.append({"commit": commit["hash"][:8], "error": str(e)})

    context["new_commits"] = [c["hash"] for c in commits]

    return {
        "outcome": "commits_processed",
        "count": len(commits),
        "results": results,
    }
