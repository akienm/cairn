"""python3 -m cairn.devices.cairn.machines.ground_loop — the heartbeat (ticket bae622881f03).

What it does, all of it (Akien, 2026-09-30):

  - claims the singleton; a second loop refuses and exits while one holds the lock, and never
    signals it (ticket 6208d0a27d6e: no age verdict, no takeover);
  - records the mtimes of its own files;
  - each beat: compares them, launches each device's groundloop/pulse.py as a detached
    child it never waits on (ticket 81eb3e46aed9), and writes one JSON (beat.json, its own record —
    heartbeat.write_record, ticket 6208d0a27d6e) with
    the recorded and current mtimes, the devices found, the rack's ids (``cairn.tools.rack``,
    ticket a808e21d646f), and what it spawned;
  - COMMAND_EXIT stops it; a changed own file re-execs it in place unless
    COMMAND_DO_NOT_RESTART is set.

No bus, no probes, no shims, no web server, no import checks. A pulse.py is launched, never
called in-process (ticket 164da559823d retired the in-process calls). Each of those
belongs to something else: mail and probes to the device, fired by their event (a commit
fires the post-commit hook's subscribers, ticket 5a4ec289bf15), the web server to its own
shim.

THE FLAGS (Akien's design 2026-08-19): the menu lives in <home>/flags/ (``ls`` shows what is
available); a flag is active when a file of that name sits in <home> itself.

RESTART IS os.execv OF THE SAME COMMAND LINE (``sys.orig_argv``), so the pid survives and a
proof's injected arguments survive with it. The flock fd is non-inheritable (PEP 446), so
the claim drops at exec and the new image claims again. If another starter wins that
instant, the new image exits 3 and the winner runs, which is the singleton contract.

THE STOP IS AN EVENT, NOT A BOOL: PEP 475 makes ``time.sleep`` resume after a signal
handler returns, so a bool left SIGTERM waiting out the cadence (measured 2026-08-09,
proofs/test_stop_is_prompt.py). ``Event.wait`` wakes on ``set()``.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.address import instance_path
from cairn.devices.cairn.machines.ground_loop.guard import ClaimRefused, claim_singleton
from cairn.devices.cairn.machines.ground_loop.heartbeat import (
    CADENCE_S, changed, mtimes, own_files, read_record, spawn_pulses, write_record)
from cairn.tools.rack.rack import rack_ids

EXIT_ALREADY_RUNNING = 3   # the loser's exit: not 1 (a crash), not 2 (argparse)

COMMAND_EXIT = "COMMAND_EXIT.flag"
COMMAND_DO_NOT_RESTART = "COMMAND_DO_NOT_RESTART.flag"


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _claim(home: Path):
    """The claim, or None when a loop holds it. The newcomer refuses and exits; it never
    signals the holder and never judges it by its record's age (ticket 6208d0a27d6e, Q#53:
    no age verdict, no takeover). The record is read only to name the holder's pid."""
    try:
        return claim_singleton(home)
    except ClaimRefused as refusal:
        pid = (read_record(home).get("record") or {}).get("pid")
        print(f"ground_loop: a loop is running (pid {pid}); "
              f"refusing to start a second loop — {refusal}", file=sys.stderr)
        return None


def main(home=None, roots=None, *, cadence: float = CADENCE_S, watch=None, class_root=None) -> int:
    home = Path(home) if home is not None else (
        instance_path("cairn", 0, roots) / "machines" / "ground_loop")
    claim = _claim(home)  # noqa: F841 — held for the process's whole life
    if claim is None:
        return EXIT_ALREADY_RUNNING

    flags = home / "flags"
    flags.mkdir(parents=True, exist_ok=True)
    for flag in (COMMAND_EXIT, COMMAND_DO_NOT_RESTART):
        (flags / flag).touch(exist_ok=True)

    started = _now().isoformat()
    recorded = mtimes(own_files(watch))
    state = {"beats": 0, "started": started, "recorded_mtimes": recorded,
             "current_mtimes": recorded, "changed": [],
             "devices": rack_ids(class_root), "spawned": []}
    write_record(_now(), state, os.getpid(), home)
    held: list = []

    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    while not stop.is_set():
        now = _now()
        current = mtimes(own_files(watch))
        diff = changed(recorded, current)
        spawned, held = spawn_pulses(class_root, held)
        state = {"beats": state["beats"] + 1, "started": started,
                 "recorded_mtimes": recorded, "current_mtimes": current,
                 "changed": diff, "devices": rack_ids(class_root), "spawned": spawned}
        write_record(_now(), state, os.getpid(), home)
        if (home / COMMAND_EXIT).exists():
            break
        if diff and not (home / COMMAND_DO_NOT_RESTART).exists():
            print(f"ground_loop: own files changed {diff}; restarting in place", file=sys.stderr)
            sys.stderr.flush()
            os.execv(sys.executable, sys.orig_argv)
        stop.wait(cadence)
    return 0


if __name__ == "__main__":
    sys.exit(main())
