"""PROBE — the watcher's commit-triggered activations are alive.

Liveness check on codemother's commit watcher: the pulse module
(groundloop/pulse.py) detects commits and calls on_commit() directly.
This probe watches the OUTPUT — activation records in instance-space —
to verify the watcher is doing its job. Fires when new activation
records appear, clears when enough have accumulated with findings.

Berths with codemother (the watcher), not with git (the trigger source) —
a probe berths with what it watches, and this watches codemother's codebase
awareness, not git's commit stream.
"""

from __future__ import annotations

from pathlib import Path

from cairn.tools.base.address import instance_path
from cairn.tools.base.probe import Probe

_ACTIVATIONS_DIR = instance_path("codemother", 0) / "watch" / "activations"


def _trigger(now, context: dict) -> bool:
    if not _ACTIVATIONS_DIR.is_dir():
        return False
    return any(_ACTIVATIONS_DIR.iterdir())


def _carry(context: dict) -> dict:
    if not _ACTIVATIONS_DIR.is_dir():
        return {"activation_count": 0}
    files = sorted(_ACTIVATIONS_DIR.glob("activation-*.json"))
    return {
        "activation_count": len(files),
        "latest": files[-1].name if files else None,
    }


def _enough(context: dict) -> bool:
    if not _ACTIVATIONS_DIR.is_dir():
        return False
    count = sum(1 for _ in _ACTIVATIONS_DIR.glob("activation-*.json"))
    return count >= 20


PROBE = Probe(
    why="the watcher's commit-triggered activations are alive — the pulse "
        "module detects commits and calls on_commit(), this probe watches "
        "the activation records to verify the pipeline is producing output. "
        "Enough when 20+ activation records exist (the watcher has run "
        "long enough to trust).",
    trigger=_trigger,
    to="codemother",
    body={"kind": "watcher_liveness", "object": "activation-records-in-instance-space"},
    carry=_carry,
    enough=_enough,
    horizon=500,
)
