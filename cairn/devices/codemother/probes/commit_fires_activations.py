"""PROBE — a commit triggers spreading activations in codemother's trees.

Watches for commits (via the ground loop's heartbeat context) and fires
codemother's watcher face to check the changed areas. The probe is the
bridge between the commit event and the watcher's activation loop.

Berths with codemother (the watcher), not with git (the trigger source) —
a probe berths with what it watches, and this watches codemother's codebase
awareness, not git's commit stream.
"""

from __future__ import annotations

from cairn.tools.base.probe import Probe


def _trigger(now, context: dict) -> bool:
    return bool(context.get("new_commits"))


def _carry(context: dict) -> dict:
    commits = context.get("new_commits", [])
    return {
        "commits": commits[:5],
        "commit_count": len(commits),
    }


def _enough(context: dict) -> bool:
    activations_fired = context.get("activations_fired", 0)
    findings_surfaced = context.get("findings_surfaced", 0)
    return activations_fired >= 20 and findings_surfaced > 0


PROBE = Probe(
    why="a commit is the natural trigger for codemother's watcher face — code "
        "changed, and the trees should check what they know about the areas "
        "that moved. Enough when activations have fired 20+ times and at least "
        "one finding has surfaced (the watcher is doing its job).",
    trigger=_trigger,
    to="codemother",
    body={"kind": "commit_activation", "object": "codebase-areas-touched-by-commit"},
    carry=_carry,
    enough=_enough,
    horizon=500,
)
