"""THE CHART DOOR — the chain's entry validated at its skill-block tenant.

/chart's input_contract declares four fields. The flat contract handles presence;
this module handles the semantic judgment on ``task_or_ticket`` — the same two-value
vocabulary /intent and /sorted already enforce.

The chart already berths every firing through its own 8 doors. The skill_block berth
is an ADDITIONAL trace surface, not a replacement — the chart's own doors remain
authoritative for per-stage detail. This berth carries the entry point: what was asked
and whether it was a ticket or a task.

ONE PASS: semantic lacks returned to the seam, merged with flat lacks, one refusal.

Fire from bash:

    PYTHONPATH=$HOME/dev/src/cairn python3 skills/chart/door.py <packet.json>

exit 0 recorded (berth printed), 2 refused (every lack named).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.machines.learning_block.learning_block import DoorRefused  # noqa: E402
from cairn.machines.skill_block import skill_block as sb              # noqa: E402


def judge_packet(payload: dict) -> list[dict]:
    """Every SEMANTIC lack, one pass. Judges only fields that are PRESENT."""
    lacks: list[dict] = []

    tot = payload.get("task_or_ticket")
    if isinstance(tot, str) and tot.strip():
        if tot.strip().lower() not in ("ticket", "task"):
            lacks.append({"field": "task_or_ticket",
                          "why": f"{tot!r} is not 'ticket' or 'task' — carried through "
                                 "from /intent; the seed test has exactly two answers"})

    return lacks


def fire(payload: dict, *, now=None, skills_root=None, berths=None,
         trace_root=None) -> dict:
    """Ride the seam."""
    return sb.fire("chart", payload, now=now, skills_root=skills_root,
                   berths=berths, trace_root=trace_root)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: python3 skills/chart/door.py <packet.json>\n"
              "The packet carries /chart's input_contract fields — see\n"
              "  python3 -m cairn.machines.skill_block contract chart",
              file=sys.stderr)
        return 2
    try:
        payload = json.loads(Path(args[0]).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"packet {args[0]!r} unreadable — {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print(f"packet {args[0]!r} must be a JSON object", file=sys.stderr)
        return 2
    try:
        result = fire(payload)
    except DoorRefused as exc:
        lacks = getattr(exc, "lacks", None) or []
        lines = [f"  - {l['field']}: {l['why']}" for l in lacks] or [f"  - {exc}"]
        print("/chart refused — every lack named on this one pass:\n"
              + "\n".join(lines)
              + "\n(the refusal is recorded; fix the packet and fire again)",
              file=sys.stderr)
        return 2
    except sb.SkillBlockRefused as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
