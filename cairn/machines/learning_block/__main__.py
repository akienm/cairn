"""The primitive's shell door — how a BASH component rides it.

    python3 -m cairn.machines.learning_block trace <block> <door_pass|send_back> <op> [lack ...]
    python3 -m cairn.machines.learning_block dial  <block>

trace/dial were built for the deploy pass's approved move (one wire per existing
door): superclaude and logger_for_bash are bash, and a wire only python can fire is
a wire two of the four ordered components cannot wear.

The approve/disprove verb that stood here retired with ticket e5a8e8059296 (outline 5.10.8:
review is the one gate act, `cairn review <id> "<words>"`); the records it wrote stay
read-only under CairnCommons/learning/records, and dial still reads them.
"""

from __future__ import annotations

import json
import sys

from cairn.machines.learning_block import learning_block as lb
from cairn.tools.system_word import canon, is_word


def main(argv: list[str]) -> int:
    if len(argv) == 2 and is_word(argv[0], "dial"):
        print(json.dumps(lb.dial(argv[1])))
        return 0
    if len(argv) < 3 or not is_word(argv[0], "trace"):
        print("usage: python3 -m cairn.machines.learning_block trace <block> "
              "<door_pass|send_back> <op> [lack ...]   |   dial <block>", file=sys.stderr)
        return 2
    _, block, event, *rest = argv
    event = canon(event, ("door_pass", "send_back")) or event
    if event not in ("door_pass", "send_back"):
        print(f"trace refused — event {event!r} is not a firing "
              "(door_pass|send_back); nothing else rides the shell",
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
