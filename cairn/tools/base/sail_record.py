"""sail_record — the derived read behind ``in-process``.

Ticket 6ec9b384b451 (the-pickup-phase-says-why-a-ticket-is-not-moving), ruling
2026-09-08-a-fleet-of-one-reshapes-the-pickup-phase.

WHY THIS EXISTS AND WHY IT IS NOT A PHASE ON THE STRING. The other four pickup
phases are written onto the ticket's cursor and committed. ``in-process`` cannot
be, and the reason is measured rather than argued: the ticket file is git-tracked
and SHARED, so a committed ``:in-process`` claims a hand that is gone the moment
the session ends, and is false on every machine that pulls it. Nothing would clear
it, because the thing that would clear it is a process that has already died. Zero
of 258 tickets have ever carried it — that is not a door that failed to fire, it is
a phase that was never storable.

So it is DERIVED. A live sail stamps a record in instance-space (``~/.cairn/``,
never git), and the phase is read back from that record, statelessly, by anyone who
asks. A session that dies takes its claim with it, which is exactly the property a
stored phase could not have.

THE DETECTOR, AND WHERE IT DELIBERATELY DIVERGES FROM ITS ANCESTOR. This composes
``ground_loop/liveness.py`` — its atomic temp-then-``os.replace`` write, and its
read face that names a lack instead of raising. It DIVERGES on the verdict: liveness
judges by the stamp's AGE against a 300s threshold, because a loop ticks on a cadence
and a stopped clock is the whole signal. A sail has no cadence. A build that thinks
for twenty minutes is healthy, and an age test would call it DEAD. So the verdict here
is PID LIVENESS: the record names the session's pid AND that pid's ``/proc`` start
time, and the read answers LIVE only while the pid is alive and its start time still
matches. The start time is what makes a RECYCLED pid detectable — without it, an
unrelated process inheriting the number would inherit the claim.

The pid recorded is the SESSION's, never the writer's. ``emit`` runs inside a
short-lived subprocess whose pid dies within the second; ``CLAUDE_PID`` names the
process that is actually holding the ticket.

NO AUTHORITY, AND NO ABILITY TO FAIL A CROSSING. Writing this record is a side
effect of a crossing, never a precondition of one: every writer here swallows its
own I/O failure and returns None. A record that cannot be written costs a derived
read, and must never cost the crossing itself.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.address import instance_path

RECORD_NAME = "sail.json"

# /proc/<pid>/stat field 22 (1-indexed) is starttime in clock ticks since boot. Fields 2 and
# 3 (comm, state) can contain spaces and parens, so the split is taken AFTER the last ')'.
_STARTTIME_FIELD = 22 - 3  # index into the post-')' remainder, which BEGINS at field 3


def instance_home(instance: int = 0) -> Path:
    """Where a sail's record berths. instance 0 is the singleton, not an exemption — the
    same sentence ``ground_loop.instance_home`` carries, and the same rung it calls."""
    return instance_path("cairn", instance) / "machines" / "sail"


def session_pid() -> int | None:
    """The pid of the live session holding the ticket — NOT this process's.

    Measured 2026-09-08: ``emit`` runs inside a ``python3 -c`` subprocess that exits within
    the second, so ``os.getpid()`` here would record a pid that is already dead by the time
    anyone reads it. ``CLAUDE_PID`` names the session process, which is the hand actually on
    the work."""
    raw = os.environ.get("CLAUDE_PID")
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def pid_starttime(pid: int) -> int | None:
    """That pid's start time in clock ticks since boot, or None if it is not running.

    This is the anti-recycling tooth: a pid number alone is reused by the kernel, so a
    record naming one could be answered LIVE by an unrelated process that happened to
    inherit it. The pair (pid, starttime) is unique for the life of the box."""
    try:
        raw = Path(f"/proc/{int(pid)}/stat").read_text()
    except (OSError, ValueError):
        return None
    try:
        return int(raw[raw.rindex(")") + 1:].split()[_STARTTIME_FIELD])
    except (ValueError, IndexError):
        return None


def write_sail(ticket: str, *, home: Path | None = None, pid: int | None = None) -> Path | None:
    """Stamp (or refresh) the record for ``ticket``. Returns the path, or None if the record
    could not be written OR there is no session pid to name.

    NEVER RAISES. This is called from inside ``emit``'s tail, and a crossing is a record of
    truth (Law 7): losing the ability to derive a phase must not cost the crossing."""
    pid = session_pid() if pid is None else pid
    if pid is None:
        return None
    started = pid_starttime(pid)
    if started is None:
        return None
    home = Path(home) if home is not None else instance_home()
    record = {
        "ticket": ticket,
        "pid": pid,
        "starttime": started,
        "opened": datetime.now(timezone.utc).isoformat(),
    }
    try:
        home.mkdir(parents=True, exist_ok=True)
        final = home / RECORD_NAME
        # Same directory, so os.replace is a same-filesystem rename — a reader must never
        # catch a torn record and conclude the sail is dead.
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
    except OSError:
        return None


def clear_sail(home: Path | None = None) -> bool:
    """Drop the record — the voyage closed. Returns whether a record was there to drop.
    NEVER RAISES, for the same reason ``write_sail`` does not."""
    home = Path(home) if home is not None else instance_home()
    try:
        (home / RECORD_NAME).unlink()
        return True
    except OSError:
        return False


def read_sail(home: Path | None = None) -> dict:
    """The read face: ``{verdict, record, lack}`` — LIVE iff the recorded pid is still
    running AND its start time still matches. Absent, unreadable, exited and recycled are all
    DEAD with the lack NAMED — never an exception. A consumer asking "is a hand on this?"
    can act on DEAD; it cannot act on a traceback."""
    home = Path(home) if home is not None else instance_home()
    path = home / RECORD_NAME
    try:
        raw = path.read_text()
    except OSError:
        return {"verdict": "DEAD", "record": None,
                "lack": f"no record at {path} — no sail has opened here, or the last one closed"}
    try:
        record = json.loads(raw)
        pid = int(record["pid"])
        started = int(record["starttime"])
    except (ValueError, KeyError, TypeError) as exc:
        return {"verdict": "DEAD", "record": None,
                "lack": f"unreadable record at {path} ({type(exc).__name__}: {exc})"}
    now_started = pid_starttime(pid)
    if now_started is None:
        return {"verdict": "DEAD", "record": record,
                "lack": f"pid {pid} is not running — the session that held this ticket has ended"}
    if now_started != started:
        return {"verdict": "DEAD", "record": record,
                "lack": (f"pid {pid} is running but started at {now_started}, not {started} — "
                         f"the number was RECYCLED by an unrelated process, and a recycled pid "
                         f"must not inherit the claim")}
    return {"verdict": "LIVE", "record": record, "lack": None}


def derived_phase(ticket: str, *, home: Path | None = None) -> str | None:
    """``'in-process'`` iff a LIVE sail record names THIS ticket, else None.

    This is the whole public answer. It is stateless by construction — the question is asked
    of the world at read time, and nothing anywhere has to remember to clear it."""
    seen = read_sail(home)
    if seen["verdict"] != "LIVE":
        return None
    return "in-process" if (seen["record"] or {}).get("ticket") == ticket else None


if __name__ == "__main__":
    print(json.dumps(read_sail(), indent=2))
