"""The primitive's shell door — how a BASH component rides it.

    python3 -m cairn.machines.learning_block trace --holder <device>/<n> <block> <door_pass|send_back> <op> [lack ...]
    python3 -m cairn.machines.learning_block dial  --holder <device>/<n> <block>
    python3 -m cairn.machines.learning_block migrate [--from <flat root>]

A trace berths under the device holding the block (ticket 17d4d1899545, outline 16.4.3), so
trace and dial name their holder; without --holder they exit 2. ``migrate`` moves the traces
that sat at the old flat root (``instance_path('learning_block', 0)/traces``) to their holders
per ``BLOCK_HOLDERS``: each file's lines are appended to the holder's file, no line twice, the
flat file removed; a block nobody is known to hold stays put and is named. A second run moves
nothing.

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
from pathlib import Path

from cairn.machines.learning_block import learning_block as lb
from cairn.tools.base.address import instance_path
from cairn.tools.system_word import canon, is_word


_USAGE = ("usage: python3 -m cairn.machines.learning_block trace --holder <device>/<n> <block> "
          "<door_pass|send_back> <op> [lack ...]   |   dial --holder <device>/<n> <block>   |   "
          "migrate [--from <flat root>]")


def _take_holder(argv: list[str]) -> tuple[str | None, list[str]]:
    if "--holder" not in argv:
        return None, argv
    i = argv.index("--holder")
    if i + 1 >= len(argv):
        return None, argv[:i]
    return argv[i + 1], argv[:i] + argv[i + 2:]


def migrate(flat: Path | None = None) -> dict:
    """Move every mapped trace file at the old flat root to its holder. Pure append: a line
    already in the holder's file is not written twice, so the move can be re-run."""
    flat = Path(flat) if flat is not None else instance_path("learning_block", 0) / "traces"
    moved, unmapped = {}, []
    if not flat.is_dir():
        return {"moved": moved, "unmapped": unmapped}
    for src in sorted(flat.glob("*.jsonl")):
        lines = [l for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
        block = src.stem.replace("__", ":", 1) if "__" in src.stem else src.stem
        if lines:
            try:
                block = json.loads(lines[0]).get("block") or block
            except ValueError:
                pass
        holder = lb.holder_of(block)
        if holder is None:
            unmapped.append(src.name)
            continue
        dst = lb.trace_path(block, holder=holder)
        dst.parent.mkdir(parents=True, exist_ok=True)
        have = set(dst.read_text(encoding="utf-8").splitlines()) if dst.exists() else set()
        new = [l for l in lines if l not in have]
        if new:
            with dst.open("a", encoding="utf-8") as f:
                f.write("".join(l + "\n" for l in new))
        src.unlink()
        moved[src.name] = {"to": str(dst), "holder": holder, "lines": len(new)}
    return {"moved": moved, "unmapped": unmapped}


def main(argv: list[str]) -> int:
    if argv and is_word(argv[0], "migrate"):
        rest = argv[1:]
        flat = None
        if rest[:1] == ["--from"] and len(rest) == 2:
            flat = Path(rest[1])
        elif rest:
            print(_USAGE, file=sys.stderr)
            return 2
        out = migrate(flat)
        for name, m in out["moved"].items():
            print(f"moved {name} -> {m['holder']} ({m['lines']} new line(s)): {m['to']}")
        for name in out["unmapped"]:
            print(f"unmapped {name}: nobody is known to hold it; left at the flat root")
        print(f"moved {len(out['moved'])}, unmapped {len(out['unmapped'])}")
        return 0
    holder, argv = _take_holder(argv)
    if argv and (is_word(argv[0], "dial") or is_word(argv[0], "trace")) and holder is None:
        print(f"{argv[0]} refused — no --holder <device>/<n>: a learning block's traces berth "
              "under the device that holds it (outline 16.4.3)", file=sys.stderr)
        return 2
    try:
        if len(argv) == 2 and is_word(argv[0], "dial"):
            print(json.dumps(lb.dial(argv[1], holder=holder)))
            return 0
        if len(argv) < 3 or not is_word(argv[0], "trace"):
            print(_USAGE, file=sys.stderr)
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
        lb.write_trace(block, event, "training", data, holder=holder)
    except lb.TraceRefused as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
