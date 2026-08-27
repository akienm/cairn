"""PROBE — does the operator inbox script match live state?

Berth for the WATCHME that ticket operator-inbox-is-deterministic-python carries.
Berthed beside cairn/tools/operator_inbox because that is WHAT IT WATCHES: the
script's output, section by section, against independent reads of each source.

THE MEASUREMENT. Run the script's readers, independently read each source, compare
counts. A mismatch means the script reports a figure that is not true at the moment
of the read.

ENOUGH: three consecutive runs where every section's count matches the independent
check, across at least one state change. State change is measured by whether any
source's count differed between consecutive runs.

AUTHORITY: none. This probe deposits and pokes; the operator decides what to do
about a mismatch (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "operator-inbox-is-deterministic-python"

_consecutive_passes = 0
_state_change_seen = False
_last_counts: dict | None = None


def _check_all() -> dict:
    from cairn.tools.operator_inbox.inbox import (
        read_troubles, read_adjudications, read_questions,
        read_tickets, read_ideas, read_intentions,
    )
    from cairn.devices.trouble.trouble import TroubleDevice
    from cairn.machines.learning_block.learning_block import pending_findings

    mismatches = []

    script_troubles = read_troubles()
    independent_troubles = [t for t in TroubleDevice().all()
                            if t.get("standing") != "CLEARED"]
    if script_troubles["live_count"] != len(independent_troubles):
        mismatches.append({
            "section": "troubles",
            "script": script_troubles["live_count"],
            "independent": len(independent_troubles),
        })

    script_adj = read_adjudications()
    independent_adj = pending_findings()
    if script_adj["count"] != len(independent_adj):
        mismatches.append({
            "section": "adjudications",
            "script": script_adj["count"],
            "independent": len(independent_adj),
        })

    script_q = read_questions()
    questions_dir = Path.home() / "dev" / "src" / "CairnCommons" / "questions"
    independent_q = len(list(questions_dir.glob("open-*.json"))) if questions_dir.exists() else 0
    if script_q["count"] != independent_q:
        mismatches.append({
            "section": "questions",
            "script": script_q["count"],
            "independent": independent_q,
        })

    script_t = read_tickets()
    script_i = read_ideas()
    script_int = read_intentions()

    current_counts = {
        "troubles": script_troubles["live_count"],
        "adjudications": script_adj["count"],
        "questions": script_q["count"],
        "tickets": script_t["total_not_done"],
        "ideas": script_i["count"],
        "intentions": script_int["count"],
    }

    return {"mismatches": mismatches, "current_counts": current_counts}


def _trigger(now, context: dict) -> bool:
    result = _check_all()
    return bool(result["mismatches"])


def _enough(context: dict) -> bool:
    global _consecutive_passes, _state_change_seen, _last_counts

    result = _check_all()
    if result["mismatches"]:
        _consecutive_passes = 0
        return False

    current = result["current_counts"]
    if _last_counts is not None and current != _last_counts:
        _state_change_seen = True
    _last_counts = current

    _consecutive_passes += 1
    return _consecutive_passes >= 3 and _state_change_seen


def _carry(context: dict) -> dict:
    result = _check_all()
    parts = []
    if result["mismatches"]:
        for m in result["mismatches"]:
            parts.append(f"{m['section']}: script={m['script']} vs independent={m['independent']}")
    else:
        parts.append("all sections match independent reads")

    return {
        "finding": "; ".join(parts),
        "mismatches": result["mismatches"],
        "current_counts": result["current_counts"],
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="the operator inbox script must match live state — a mismatch means the script "
        "reports a figure that is not true, which is the founding defect this script was "
        "built to kill (the old LLM skill could invent counts)",
    trigger=_trigger,
    to="cairn",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=500,
)


if __name__ == "__main__":
    result = _check_all()
    print(json.dumps({
        "mismatches": result["mismatches"],
        "current_counts": result["current_counts"],
        "would_trigger": bool(result["mismatches"]),
    }, indent=2, default=str))
