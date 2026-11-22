"""hidden — run a command line with no console window (ticket 364704f371dd).

    pythonw -m cairn.tools.windowless_spawn.hidden <log> <command> [args...]

Runs the argv list (never a shell) with ``windowless_kwargs``: on Windows the child gets
the helper's no-window flag, a console with no window, which every console grandchild it starts inherits,
so none of them pops one up. The child's stdout goes to ``<log>`` (appended) with its stderr
folded in, its stdin is empty, and this process exits with the child's exit code. Started
through ``background_pythonw()`` the launcher itself owns no console either. Off Windows the
flags are empty and it is a plain logged run.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs

USAGE = "usage: python -m cairn.tools.windowless_spawn.hidden <log> <command> [args...]"


def run(log: str | Path, argv: list[str]) -> int:
    """Run ``argv`` windowless with its output in ``log``; return its exit code."""
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "ab") as fh:
        return subprocess.run(list(argv), stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                              **windowless_kwargs()).returncode


def main(args: list[str]) -> int:
    if len(args) < 2:
        print(USAGE, file=sys.stderr) if sys.stderr else None
        return 2
    return run(args[0], args[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
