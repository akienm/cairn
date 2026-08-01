"""THE SHELL REACH — how a skill whose executor is an LLM reading markdown fires the
Learning Block anatomy.

THE STANCE REVISION, WRITTEN DOWN (the decompose piece required it, so here it is,
narrower than expected). ``cairn.learning_block.__main__`` refuses any trace event
outside ``door_pass|send_back`` with the message "findings go through python", and
that refusal STILL STANDS — nothing here removes it. The reason it existed is that a
bare shell caller could mint a finding with no gated input behind it, which is a
finding with laundered provenance. That reason does not apply to this door: the
finding is emitted only as the far side of a firing whose packet the door already
gated, whose lacks were traced, and whose berth is written in the same act. So the
stance is not reversed — it is met. A finding still cannot be conjured from bash; it
can only be the exit of a firing that passed a contract.

Exit codes follow the primitive's convention: 0 recorded, 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cairn.learning_block.learning_block import DoorRefused, FindingRefused
from cairn.skill_block.skill_block import SkillBlockRefused, fire, load_contract

USAGE = """usage:
  python3 -m cairn.skill_block fire <skill> <packet.json>
  python3 -m cairn.skill_block contract <skill>

The packet is a JSON object carrying the skill's declared input_contract fields
(see `contract`), plus `bullets` — a list of {text, stratum} with stratum in
code|tree (hex is minted only through the injected seam, never by hand) — and
`exit`, one of routed_forward|routed_out."""


def _refuse(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        return 0 if args else 2

    verb, rest = args[0], args[1:]

    if verb == "contract":
        if len(rest) != 1:
            return _refuse(USAGE)
        try:
            contract = load_contract(rest[0])
        except SkillBlockRefused as exc:
            return _refuse(str(exc))
        print(json.dumps(contract, indent=2, sort_keys=True))
        return 0

    if verb == "fire":
        if len(rest) != 2:
            return _refuse(USAGE)
        skill, packet_path = rest
        try:
            payload = json.loads(Path(packet_path).read_text())
        except (OSError, json.JSONDecodeError) as exc:
            return _refuse(f"packet {packet_path!r} unreadable — {exc}")
        if not isinstance(payload, dict):
            return _refuse(f"packet {packet_path!r} must be a JSON object, not "
                           f"{type(payload).__name__}")
        try:
            result = fire(skill, payload)
        except OSError as exc:
            # THE WIRE IS NOT FATAL — measured 2026-08-01 at this build's live fire, where
            # an unwritable berth root wedged /intent with a raw PermissionError traceback.
            # The first four wired components set the precedent (backgrounded, never fatal),
            # and it is the right one: the RECORDING must never stop the WORK. /intent is
            # the cheapest gate in the system precisely because it costs nothing to fire; a
            # skill that cannot run when its trace root is read-only is not cheap, it is
            # brittle.
            #
            # THE HONESTY THIS BUYS AND WHAT IT COSTS, both stated. It exits 0, so the
            # firing is not counted — the denominator loses a line, which is the primitive's
            # falsifier (2) in miniature and is NOT hidden here. What keeps it from being a
            # silent loss is that no berth path is printed, and the downstream gate
            # (buildme_rides_the_intent) refuses the eventual BUILDME for a ticket that
            # cannot name one. So the loss surfaces later, at a door, with a disposition —
            # rather than never, or by wedging the work now.
            #
            # A DoorRefused is a different animal and stays fatal below: that is the packet
            # being wrong, which is the whole point of the door.
            print(f"/{skill}: the firing could not be RECORDED — {exc}\n"
                  "  the skill's own work is unaffected and this exits 0 on purpose (the\n"
                  "  recording never wedges the work), but NO BERTH EXISTS for this firing:\n"
                  "  nothing to put in a ticket's intent_berth, and the BUILDME gate will\n"
                  "  refuse that ticket until this is fixed or an exemption is recorded.",
                  file=sys.stderr)
            print(json.dumps({"berth": None, "recorded": False, "reason": str(exc)},
                             indent=2, sort_keys=True))
            return 0
        except DoorRefused as exc:
            # EVERY lack, on the first pass — the send_back is already traced by the
            # door itself, so this refusal is loud AND counted.
            lacks = getattr(exc, "lacks", None) or []
            lines = [f"  - {l['field']}: {l['why']}" for l in lacks] or [f"  - {exc}"]
            return _refuse(
                f"/{skill} refused — the firing does not meet the contract:\n"
                + "\n".join(lines)
                + "\n(the refusal is recorded; fix the packet and fire again)"
            )
        except (SkillBlockRefused, FindingRefused) as exc:
            return _refuse(str(exc))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    return _refuse(f"no such verb: {verb!r}\n\n{USAGE}")


if __name__ == "__main__":
    raise SystemExit(main())
