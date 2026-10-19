"""WATCHME(a-commit-that-reseals-leaves-a-clean-tree) for ticket 357c402172ca — does a commit
whose pre-commit reseal rewrites a seal still leave that seal behind it, unstaged?

THE QUESTION THE PROOF CANNOT ANSWER. The build made ``cairn test --reseal --stage`` git-add each
seal it rewrote, so the commit carries the seal of the code it certifies. The proof settles that
in a fixture repo. Whether real commits live it — whether the tree after a reseal-changing commit
is clean, every time, under every future edit of the hook — is a fact about live traffic.

THIS PROBE WAS OWED, AND IT SAYS SO. The ticket crossed PROVED on 2026-10-13 naming this file, and
the file was never written (no commit in either repo ever held it). The corpus check
``cairn/tools/base/proofs/test_every_built_probe_spec_names_a_file.py`` red it on 2026-10-18; it
was built that day, which is the date ``_ARMED`` carries.

HOW A HOOK-LEFT SEAL IS TOLD FROM AN ORDINARY ONE. A validation dirty in the working tree is the
normal state between ``cairn test --seal`` and the commit that carries it, so dirt alone would
fire on every build. What the defect leaves is narrower and every validation record says which it
is: its last record's ``caller`` is ``cairn test --reseal`` (the hook's own writer) and its
``date`` is no later than HEAD's commit time — the seal was written for the commit that just
landed, and the commit did not take it.

Two readings:

  1. THE DEFECT. Every ``validations/*.json`` git reports modified in class-space whose last record
     the reseal wrote at or before HEAD's commit — the trigger.
  2. THE TRAFFIC. Commits since arming that touched a validation — the evidence that reseals are
     still happening, so a quiet tree is not mistaken for a proven hook.

AUTHORITY: none, by construction. This probe deposits and pokes; reopening the ticket is the
owner's act (Law 6).

ONE SUBPROCESS, AND IT IS GIT. The siblings read files only; the reading this ticket names is
``git status --porcelain``, and only git can say what git considers dirty. Read-only commands,
bounded by a timeout, no network.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date, datetime
from pathlib import Path

from cairn.tools.base.probe import Probe, once, owning_ticket

_OWNING_TICKET = "357c402172ca"

# Class-space root: this file is cairn/devices/tester/probes/<name>.py.
_CLASS_SPACE = Path(__file__).resolve().parents[4]

# The reseal ladder's own caller string, as it writes it into each record (cli.py --reseal).
_RESEAL_CALLER = "cairn test --reseal"

# MEASURED 2026-10-18 AT ARMING: 0 validations dirty from the reseal, 125 commits since
# 2026-10-13 touching a validation. Carried as CONTEXT, never asserted. (The since is pinned
# to midnight: git reads a bare date as that day at the CURRENT time of day.)
_AT_ARMING = {"hook_left_seals": 0}
_ARMED = "2026-10-18"

# The ticket's `enough`: 20 reseal-changing commits, none followed by a dirty validation file.
_ENOUGH_COMMITS = 20

_GIT_TIMEOUT_S = 10


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(_CLASS_SPACE), *args], capture_output=True,
                          text=True, check=True, timeout=_GIT_TIMEOUT_S).stdout


def _parse(stamp: str) -> datetime:
    """Both stamps compared as naive local time — the records write naive local, git's %ci
    is converted to naive local here."""
    dt = datetime.fromisoformat(stamp.strip())
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt


def hook_left_seals() -> dict:
    """The validations dirty now whose last record the reseal wrote for the commit at HEAD."""
    head_at = _parse(_git("log", "-1", "--format=%cI"))
    left: list[str] = []
    unreadable: list[str] = []
    for line in _git("status", "--porcelain", "--", "*/validations/*.json").splitlines():
        rel = line[3:].strip()
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        try:
            trail = json.loads((_CLASS_SPACE / rel).read_text(encoding="utf-8"))
            last = trail[-1] if isinstance(trail, list) and trail else {}
            if last.get("caller") == _RESEAL_CALLER and _parse(str(last.get("date"))) <= head_at:
                left.append(rel)
        except Exception as exc:
            unreadable.append(f"{rel}: {exc}")
    return {"left": left, "unreadable": unreadable, "head_at": head_at.isoformat(),
            "fires": bool(left)}


def reseal_commits_since_arming() -> int:
    """Commits since arming that carried a validation — the traffic the hook rides."""
    out = _git("log", f"--since={_ARMED}T00:00:00", "--format=%H", "--", "*/validations/*.json")
    return len(out.split())


def _days_since_arming() -> int:
    y, m, d = (int(p) for p in _ARMED.split("-"))
    return (date.today() - date(y, m, d)).days


def _trigger(now, context: dict) -> bool:
    """TRUE when a seal the reseal wrote for HEAD's commit stands unstaged behind it."""
    return once(context, "hook_left_seals", hook_left_seals)["fires"]


def _enough(context: dict) -> bool:
    """CLEARED once twenty validation-carrying commits have landed since arming and the tree
    holds no hook-left seal. The commit count is what keeps a quiet tree from clearing it."""
    return (once(context, "commits", reseal_commits_since_arming) >= _ENOUGH_COMMITS
            and not once(context, "hook_left_seals", hook_left_seals)["fires"])


def _carry(context: dict) -> dict:
    c = once(context, "hook_left_seals", hook_left_seals)
    return {
        "hook_left_seals": c["left"],
        "unreadable_files": c["unreadable"],
        "head_committed_at": c["head_at"],
        "reseal_commits_since_arming": once(context, "commits", reseal_commits_since_arming),
        "at_arming": _AT_ARMING,
        "days_since_arming": _days_since_arming(),
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "a commit that causes a reseal leaves `git status --porcelain` empty, and the crossing "
            "immediately after it passes working_tree_clean and history_integrity with no "
            "hand-staging in between"),
        "suggests": (
            "a validation whose last record says caller 'cairn test --reseal', dated at or before "
            "HEAD, is dirty: the pre-commit hook rewrote it and the commit did not take it — read "
            "cairn/devices/tester/hooks/pre-commit (is --stage still passed?) and reseal.py's "
            "git-add site. A commit made with --no-verify skips the hook and cannot leave this."),
    }


# THE HORIZON. Same unit and same honest placeholder as the sibling probes: PULSES.
_HORIZON = 1000

PROBE = Probe(
    why="the proof settles in a fixture repo that the reseal stages what it rewrites; whether a "
        "real commit ever again leaves a hook-written seal unstaged behind it is a fact about live "
        "commits, and the falsifier asks for a clean tree after every one",
    trigger=_trigger,
    to="tester",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
