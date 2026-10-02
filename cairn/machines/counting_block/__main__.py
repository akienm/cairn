"""``python3 -m cairn.machines.counting_block`` — the counting block's one live entry point.

Ticket 5a4ec289bf15, D26: the commit is the event, and the post-commit hook (``hook.py``,
``hooks/post-commit``) is the caller. ``pulse`` folds the journals once and prints what the
fold did as one JSON line; ``install-hook`` and ``verify-hook`` install and verify the post-commit FAN-OUT
(cairn/tools/post_commit, which runs this block's subscriber) — the host-seam's apply and
its re-runnable verify, at the same address as the block they fire (Law 5).
"""
import json
import sys
from datetime import datetime

from cairn.machines.counting_block import block, hook


def summary(now=None) -> dict:
    """One fold, reduced to what a reader of the commit's output needs."""
    out = block.pulse(now=now)
    return {"block": block.COMPONENT, "raised": len(out["raised"]),
            "post_appends": out["post_appends"], "compression": out["compression"]}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["pulse"]:
        print(json.dumps(summary(datetime.now().astimezone()), sort_keys=True))
        return 0
    if argv == ["install-hook"]:
        got = hook.install_hook()
        print(("installed " if got["installed"] else "not installed ") + got["path"])
        print(f"  {got['why']}")
        return 0 if got["installed"] or "already installed" in got["why"] else 1
    if argv == ["verify-hook"]:
        got = hook.verify_hook()
        print(("green  " if got["green"] else "RED    ") + got.get("path", ""))
        print(f"  {got['why']}")
        return 0 if got["green"] else 1
    print("usage: python3 -m cairn.machines.counting_block pulse|install-hook|verify-hook",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
