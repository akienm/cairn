"""The primitive's shell door — how a BASH component rides the trace wire.

    python3 -m cairn.learning_block trace <block> <door_pass|send_back> <op> [lack ...]
    python3 -m cairn.learning_block dial  <block>

Built for the deploy pass's approved move (one wire per existing door): superclaude
and logger_for_bash are bash, and a wire only python can fire is a wire two of the
four ordered components cannot wear. The door accepts exactly the two firing events
the dial counts; everything richer (contracts, findings, verdicts) stays in python,
where the callers can be refused properly.

Exit codes are honest: 0 recorded, 2 refused (bad event / missing args — the lack
named on stderr). Callers whose prime directive forbids dying on this (superclaude's
launch, a sourced logger) guard the CALL SITE with `|| true`; this door itself never
lies with a green exit.
"""

from __future__ import annotations

import json
import sys

from cairn.learning_block import learning_block as lb


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "dial":
        print(json.dumps(lb.dial(argv[1])))
        return 0
    if len(argv) < 3 or argv[0] != "trace":
        print("usage: python3 -m cairn.learning_block trace <block> "
              "<door_pass|send_back> <op> [lack ...]   |   dial <block>", file=sys.stderr)
        return 2
    _, block, event, *rest = argv
    if event not in ("door_pass", "send_back"):
        print(f"trace refused — event {event!r} is not a firing "
              "(door_pass|send_back); findings and verdicts go through python",
              file=sys.stderr)
        return 2
    if not rest:
        print("trace refused — the op is missing (what fired?)", file=sys.stderr)
        return 2
    op, *lacks = rest
    if event == "send_back" and not lacks:
        print("trace refused — a send_back names its lack(s); an unnamed refusal "
              "teaches nothing", file=sys.stderr)
        return 2
    data: dict = {"op": op}
    if lacks:
        data["lacks"] = lacks
    lb.write_trace(block, event, "training", data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
