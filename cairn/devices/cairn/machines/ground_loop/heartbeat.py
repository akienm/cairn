"""heartbeat — what one beat of the ground loop does, with no clock in it (ticket bae622881f03).

Akien, 2026-09-30: on start the loop records its own files' timestamps; on each beat it
compares them and restarts if they changed; then it calls every device's ground loop
trigger file and records which it called; then it writes that to one JSON. "Not
everything we MIGHT need, everything we KNOW WE NEED."

THE TRIGGER CALLS ARE RETIRED (ticket 164da559823d, Akien open-291189a9766a, 2026-10-01):
nothing fires on the heartbeat but its listeners, so a beat calls nothing and every listener
fires on its own event.

WHY MTIMES AND NOT BYTECODE. Until this ticket the loop asked whether the code objects it
held still matched a fresh compile of each file (staleness.py). On Python 3.14 a nested
``__annotate__`` const collided by ``co_name`` with the function's own, so an untouched tree
read as stale after beat 1 and the loop restarted itself 61 times. An mtime compare over
the loop's own folder answers the only question the restart needs: did someone change
this code since I started?

The runner (__main__.py) owns the clock, the claim, the flags and the exec. Everything here
is callable from a proof with temp trees.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent


def own_files(folder: Path | None = None) -> list[Path]:
    """The loop's own files: the top-level ``*.py`` in its folder (proofs/ and the rest are not
    the running code)."""
    folder = Path(folder) if folder is not None else HERE
    return sorted(p for p in folder.glob("*.py") if p.is_file())


def mtimes(paths) -> dict[str, float]:
    """``{path: st_mtime}``; a file that vanished between the glob and the stat is omitted,
    which ``changed`` reports as removed."""
    out: dict[str, float] = {}
    for p in paths:
        try:
            out[str(p)] = Path(p).stat().st_mtime
        except OSError:
            continue
    return out


def changed(recorded: dict, current: dict) -> list[str]:
    """Every path added, removed, or with a different mtime. Empty means unchanged."""
    return sorted(p for p in set(recorded) | set(current) if recorded.get(p) != current.get(p))

