"""THE SAIL DOOR — the build voyage's entry contract enforced at the seam.

/sail's input_contract declares five fields. The flat contract handles presence;
this module handles two semantic judgments:

- ``task_or_ticket`` must be 'ticket' — /sail always builds a cast ticket (/sorted
  runs before /sail), so 'task' is structurally impossible for this skill.
- ``exit`` and ``disposition`` must cohere — the same pattern as /sorted's door:
  routed_forward carries 'built', routed_out carries 'not-ready' or
  'kicked-back:<reason>'. The real outcome rides the disposition so the trace carries
  more than just pass/fail.

ONE PASS: semantic lacks returned to the seam, merged with flat lacks, one refusal.

Fire from bash:

    PYTHONPATH=$HOME/dev/src/cairn python3 skills/sail/door.py <packet.json>

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
        if tot.strip().lower() != "ticket":
            lacks.append({"field": "task_or_ticket",
                          "why": f"{tot!r} is not 'ticket' — /sail always builds a cast "
                                 "ticket (/sorted runs before /sail). A 'task' cannot "
                                 "reach /sail because it was never cast"})

    exit_value = payload.get("exit")
    disposition = payload.get("disposition")
    if isinstance(exit_value, str) and exit_value in sb.EXITS:
        if isinstance(disposition, str) and disposition.strip():
            d = disposition.strip()
            if exit_value == "routed_forward" and d != "built":
                lacks.append({"field": "disposition",
                              "why": f"routed_forward carries disposition {d!r} — a "
                                     "completed voyage IS 'built'; anything else is a "
                                     "route wearing the wrong exit"})
            if exit_value == "routed_out" and not (d == "not-ready" or
                                                    d.startswith("kicked-back:")):
                lacks.append({"field": "disposition",
                              "why": f"routed_out carries disposition {d!r} — the real "
                                     "route is 'not-ready' or 'kicked-back:<reason>', "
                                     "so the two-exit vocabulary never flattens the "
                                     "voyage's real outcomes"})

    return lacks


def fire(payload: dict, *, now=None, skills_root=None, berths=None,
         trace_root=None) -> dict:
    """Ride the seam."""
    return sb.fire("sail", payload, now=now, skills_root=skills_root,
                   berths=berths, trace_root=trace_root)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: python3 skills/sail/door.py <packet.json>\n"
              "The packet carries /sail's input_contract fields — see\n"
              "  python3 -m cairn.machines.skill_block contract sail",
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
        print("/sail refused — every lack named on this one pass:\n"
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
