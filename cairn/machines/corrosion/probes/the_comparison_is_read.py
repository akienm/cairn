"""WATCHME probe: the-comparison-is-read-not-just-written.

Fires when 20+ run records have accumulated and no comparison finding has
been acted on. Clears when at least one comparison finding has been
dispositioned — a silently-stopped check investigated, or a never-redded
check confirmed sound.

Ticket: the-proof-record-persists-so-runs-can-be-compared.
"""
from __future__ import annotations

from pathlib import Path

from cairn.tools.base.probe import Probe

_INSTANCE_ROOT = Path.home() / ".cairn" / "devices" / "build_inspector" / "0"
_RECORDS_DIR = _INSTANCE_ROOT / "run_records"
_ACTED_MARKER = _INSTANCE_ROOT / "comparison_acted.json"


def _trigger(now, context: dict) -> bool:
    from cairn.machines.build_inspector.run_record import list_runs
    runs = list_runs(_RECORDS_DIR)
    context["run_count"] = len(runs)
    context["acted"] = _ACTED_MARKER.is_file()
    return len(runs) >= 20 and not _ACTED_MARKER.is_file()


def _carry(context: dict) -> dict:
    return {
        "run_count": context.get("run_count", 0),
        "acted": context.get("acted", False),
        "finding": "20+ run records accumulated with no comparison finding acted on"
        if not context.get("acted", False)
        else "at least one comparison finding has been acted on",
    }


def _enough(context: dict) -> bool:
    return _ACTED_MARKER.is_file()


PROBE = Probe(
    why="the founding defect restated as accumulation: records are written "
        "and nothing compares two runs. This probe fires when records have "
        "piled up and nobody has acted on a comparison finding — the exact "
        "shape the ticket's falsifier clause (1) describes.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)
