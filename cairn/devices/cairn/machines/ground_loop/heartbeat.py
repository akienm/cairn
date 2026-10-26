"""heartbeat — what one beat of the ground loop does, with no clock in it (ticket bae622881f03).

Akien, 2026-09-30: on start the loop records its own files' timestamps; on each beat it
compares them and restarts if they changed; then it calls every device's ground loop
trigger file and records which it called; then it writes that to one JSON. "Not
everything we MIGHT need, everything we KNOW WE NEED."

THE TRIGGER CALLS ARE RETIRED (ticket 164da559823d, Akien open-291189a9766a, 2026-10-01):
nothing fires on the heartbeat but its listeners, so a beat calls nothing and every listener
fires on its own event.

THE BEAT LAUNCHES EACH DEVICE'S groundloop/pulse.py (ticket 81eb3e46aed9, Akien's outline
5.5.3.4-5): a detached child per device, never imported and never waited on. pulse.py is
part of that device's shim; what it does with the pulse is the device's business. The record
lists every device folder: its pulse.py's path, mtime and pid, or NOT FOUND.

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

import os
import subprocess
import sys
from pathlib import Path

from cairn.tools.rack.rack import rack

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



def spawn_pulses(class_root=None, held=None) -> tuple[list[dict], list]:
    """Launch every device's ``groundloop/pulse.py`` as a detached child; return
    ``(entries, still_running)``. ``held`` is the previous beat's handles: finished ones are
    reaped (``poll``, never ``wait``), so no zombies pile up and no beat blocks. A device with
    no pulse.py is listed as NOT FOUND; a launch that fails is listed with its error and the
    next device is still launched."""
    still = [h for h in (held or []) if h.poll() is None]
    root = Path(class_root) if class_root is not None else None
    entries: list[dict] = []
    for device, folder, _shim in rack(root):
        path = folder / "groundloop" / "pulse.py"
        entry: dict = {"device": device}
        entries.append(entry)
        if not path.is_file():
            entry["pulse"] = "NOT FOUND"
            continue
        entry["path"] = str(path)
        cwd = Path(class_root) if class_root is not None else folder.parents[2]
        try:
            entry["mtime"] = path.stat().st_mtime
            child = subprocess.Popen(
                [sys.executable, str(path)], cwd=str(cwd),
                env={**os.environ, "PYTHONPATH": str(cwd)},
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True)
        except OSError as err:
            entry["error"] = f"{type(err).__name__}: {err}"
            continue
        entry["pid"] = child.pid
        still.append(child)
    return entries, still
