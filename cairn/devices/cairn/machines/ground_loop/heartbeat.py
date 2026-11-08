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

THE LOOP OWNS ITS RECORD AND ITS CADENCE (ticket 6208d0a27d6e, Q#53): both lived in a\nseparate tool that also judged the record by its age; that judgement is retired. Whether the\nloop is up is its held lock (guard.py), and the record only says what the last beat did.\n\nThe runner (__main__.py) owns the clock, the claim, the flags and the exec. Everything here
is callable from a proof with temp trees.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from cairn.tools.base.address import instance_path
from cairn.tools.rack.rack import rack

HERE = Path(__file__).resolve().parent


# THE CADENCE — RULED by Akien 2026-08-22: the ground loop beats once per minute. Its one
# definition site is here, beside the beat it paces (ticket 6208d0a27d6e: the loop owns it).
CADENCE_S = 60.0

# THE RECORD — the loop's one JSON (Akien 2026-09-30, "writes that to one JSON"). It says what
# the last beat did; it is never judged by its age (Q#53: "Is it up?" is the held lock).
RECORD_NAME = "beat.json"


def write_record(now, state: dict, pid: int, home) -> Path:
    """Write the record atomically into ``home``, creating it on first write. Temp in the SAME
    directory so ``os.replace`` is a same-filesystem rename: a reader never sees a torn record."""
    home = Path(home)
    home.mkdir(parents=True, exist_ok=True)
    final = home / RECORD_NAME
    record = {"last_run": now.isoformat(), "state": state, "pid": pid}
    fd, tmp = tempfile.mkstemp(prefix=RECORD_NAME + ".", dir=str(home))
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(record, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, final)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return final


def default_home() -> Path:
    return instance_path("cairn", 0) / "machines" / "ground_loop"


def read_record(home=None, now=None) -> dict:
    """``{record, age_s}`` — the record whole, and its age when ``now`` is given. It judges
    nothing. Absent or unreadable is ``record: None`` with the ``lack`` named, never a raise
    (Law 7: a diagnostic surface may collapse a lack into a coherent shape)."""
    home = Path(home) if home is not None else default_home()
    path = home / RECORD_NAME
    try:
        raw = path.read_text()
    except OSError:
        return {"record": None, "age_s": None,
                "lack": f"no record at {path} — the loop has never beat here, or its device space is gone"}
    try:
        record = json.loads(raw)
        age_s = None
        if now is not None:
            age_s = (now - datetime.fromisoformat(record["last_run"])).total_seconds()
    except (ValueError, KeyError, TypeError) as exc:
        return {"record": None, "age_s": None,
                "lack": f"unreadable record at {path} ({type(exc).__name__}: {exc})"}
    return {"record": record, "age_s": age_s}


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
