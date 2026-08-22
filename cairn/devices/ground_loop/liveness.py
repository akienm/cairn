"""liveness — the ground loop's own liveness record, written as part of the pass.

Ticket ground-loop-writes-its-own-liveness (parent ground-loop-is-discoverable-
without-scanning): on each pass the loop writes a record in its own device space
(``~/.cairn/devices/ground_loop/<instance>/`` — instance 0 for the singleton)
carrying when it last ran, its state, and its pid. Consumers — the start-guard
sibling, the panes, a human — READ this record instead of scanning the process
table: liveness is an owned fact (Law 6), and this is the first device record
ever to reach instance-space disk.

THE DETECTOR (Akien's, present from the first telling): a crashed loop leaves
the file behind but STOPS ADVANCING THE TIMESTAMP. So the verdict is computed
from the stamp's age alone — LIVE iff last-run is within the ruled threshold of
the caller's ``now``, DEAD otherwise, whatever the file says about state,
whatever pid it names. The threshold lives HERE, once, at the owner's read
face; a consumer gets the verdict and never re-derives the number (Law 1).

THE WRITE IS ATOMIC — temp-then-``os.replace`` in the same directory, the same
discipline as the projector's append door: the write happens once per second,
and a reader inside a 5s window must never see a torn record and conclude DEAD.

The read face never raises on a lack: an absent or unreadable record IS a DEAD
verdict with the lack named — to every consumer, "never ran", "device space
gone", and "crashed long ago" are the same actionable fact.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from cairn.tools.base.address import instance_path

# THE STALENESS THRESHOLD — RULED by Akien 2026-07-31 (recorded on the ticket):
# five missed ticks at the ruled cadence. Three-times-the-interval is the
# standard heuristic; five gives slack for a loaded box. This is the ONE
# class-space definition site; consumers read the verdict, not this.
# Cadence moved from 1.0s to 60.0s (Akien, 2026-08-22).
STALENESS_THRESHOLD_S = 300.0

RECORD_NAME = "liveness.json"


def instance_home(instance: int = 0) -> Path:
    """The loop's own device space — instance 0 is the singleton, not a special case.

    The BODY became a call on 2026-08-12 (one-owner-for-the-instance-address) and
    nothing else about this function moved. It was the shape the resolver generalised
    from — the only one of ten hand-spellings that already took the instance as a
    parameter and already said in words why 0 is not an exemption — so the rung it now
    calls is this function widened to every device, and the sentence above is the one
    the rung inherited.
    """
    return instance_path("ground_loop", instance)


def write_liveness(now: datetime, state: dict, pid: int, home: Path) -> Path:
    """Write the liveness record atomically into ``home``, creating it on first
    write (the instance dir is born with its first record). Returns the record path."""
    home = Path(home)
    home.mkdir(parents=True, exist_ok=True)
    final = home / RECORD_NAME
    record = {"last_run": now.isoformat(), "state": state, "pid": pid}
    # Temp in the SAME directory so os.replace is a same-filesystem rename — the
    # atomicity the falsifier demands; never truncate-in-place at the read path.
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


def read_liveness(now: datetime, home: Path | None = None) -> dict:
    """The read face: ``{verdict, record, age_s}`` — LIVE iff last-run is within
    ``STALENESS_THRESHOLD_S`` of ``now``, DEAD otherwise. Absent or unreadable is
    DEAD with the ``lack`` named, never an exception (a diagnostic surface may
    collapse a lack into a coherent shape — Law 7 — and DEAD is that shape)."""
    home = Path(home) if home is not None else instance_home()
    path = home / RECORD_NAME
    try:
        raw = path.read_text()
    except OSError:
        return {"verdict": "DEAD", "record": None, "age_s": None,
                "lack": f"no record at {path} — the loop has never run here, or its device space is gone"}
    try:
        record = json.loads(raw)
        last_run = datetime.fromisoformat(record["last_run"])
        age_s = (now - last_run).total_seconds()
    except (ValueError, KeyError, TypeError) as exc:
        return {"verdict": "DEAD", "record": None, "age_s": None,
                "lack": f"unreadable record at {path} ({type(exc).__name__}: {exc})"}
    verdict = "LIVE" if age_s <= STALENESS_THRESHOLD_S else "DEAD"
    return {"verdict": verdict, "record": record, "age_s": age_s}
