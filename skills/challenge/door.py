"""THE CHALLENGE DOOR — the adversarial pass's vocabulary enforced at entry.

/challenge's input_contract declares eight fields. The flat contract (the seam's
``check_input``) handles presence; this module handles the one semantic judgment:
``back_up`` must be one of the three dispositions (proceed, revise, abandon). A fourth
value is a free-text disposition, which defeats the count: how many challenges ended in
'revise' is a question the trace should answer from data, not from reading prose.

ONE PASS: semantic lacks are collected and returned to the seam, which merges them with
the flat lacks and raises a SINGLE ``DoorRefused``.

Fire from bash:

    PYTHONPATH=$HOME/dev/src/cairn python3 skills/challenge/door.py <packet.json>

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

BACK_UP_VALUES = ("proceed", "revise", "abandon")


def judge_packet(payload: dict) -> list[dict]:
    """Every SEMANTIC lack, one pass. Judges only fields that are PRESENT."""
    lacks: list[dict] = []

    back_up = payload.get("back_up")
    if isinstance(back_up, str) and back_up.strip():
        if back_up.strip().lower() not in BACK_UP_VALUES:
            lacks.append({"field": "back_up",
                          "why": f"{back_up!r} is not one of {BACK_UP_VALUES}. The "
                                 "disposition has three values, no fourth — the count "
                                 "'how many challenges ended in revise' is a question "
                                 "the trace should answer from data, not from reading "
                                 "free-text prose"})

    return lacks


def fire(payload: dict, *, now=None, skills_root=None, berths=None,
         trace_root=None) -> dict:
    """Ride the seam."""
    return sb.fire("challenge", payload, now=now, skills_root=skills_root,
                   berths=berths, trace_root=trace_root)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: python3 skills/challenge/door.py <packet.json>\n"
              "The packet carries /challenge's input_contract fields — see\n"
              "  python3 -m cairn.machines.skill_block contract challenge",
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
        print("/challenge refused — every lack named on this one pass:\n"
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
