"""PROBE — is the memory curve actually being recorded?

WATCHME probe for ticket the-memory-curve-is-recorded-not-eyeballed, object
the_memory_curve_is_recorded. This watches whether the RECORDER (memory_curve.py)
is actually producing data — the efficacy question, not the sampling itself.

Trigger: the series file exists and has at least one entry.
Enough: the series covers at least one full session (from launch to exit), so the
shape can be read against a session's LIFETIME. Until then the watch stands.

AUTHORITY: none. This probe deposits and pokes; the back-edge that re-opens the
node is the owner's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.base.probe import Probe, owning_ticket

_SERIES_PATH = address.instance_path("cc", 0) / "memory_series.jsonl"
_TICKET = "the-memory-curve-is-recorded-not-eyeballed"


def _series_count() -> int:
    try:
        if _SERIES_PATH.exists():
            return len(_SERIES_PATH.read_text().strip().splitlines())
    except OSError:
        pass
    return 0


def _trigger(now, context: dict) -> bool:
    return _series_count() > 0


def _carry(context: dict) -> dict:
    count = _series_count()
    return {
        "ticket": owning_ticket(_TICKET),
        "samples": count,
    }


def _enough(context: dict) -> bool:
    count = _series_count()
    if count < 10:
        return False
    try:
        lines = _SERIES_PATH.read_text().strip().splitlines()
        first = json.loads(lines[0])
        last = json.loads(lines[-1])
        span = last.get("ts", 0) - first.get("ts", 0)
        return span >= 3600
    except (OSError, json.JSONDecodeError, IndexError):
        return False


PROBE = Probe(
    why="the memory curve must actually be recorded, not just built — a probe that "
        "never fires gathers nothing while looking like learning. This watches the "
        "recorder's output.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=100,
)


if __name__ == "__main__":
    print(json.dumps({
        "series_count": _series_count(),
        "would_trigger": _trigger(None, {}),
        "enough": _enough({}),
    }, indent=2))
