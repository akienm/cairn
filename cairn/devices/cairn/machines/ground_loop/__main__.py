"""python3 -m cairn.devices.cairn.machines.ground_loop — the heartbeat (ticket bae622881f03).

What it does, all of it (Akien, 2026-09-30):

  - claims the singleton; a second loop exits while one runs and is LIVE;
  - records the mtimes of its own files;
  - each beat: compares them, calls every groundloop/pulse.py and lists the calls, writes
    one JSON (liveness.json) with the recorded and current mtimes and the calls;
  - COMMAND_EXIT stops it; a changed own file re-execs it in place unless
    COMMAND_DO_NOT_RESTART is set.

No bus, no probes, no shims, no web server, no import checks. Each of those belongs to
something else: mail and probes to the device (on its own pulse file, or on the event that
fires them), the web server to its own shim.

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
import time
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.address import instance_path
from cairn.devices.cairn.machines.ground_loop.discovery import pulse_sites
from cairn.devices.cairn.machines.ground_loop.guard import ClaimRefused, claim_singleton
from cairn.devices.cairn.machines.ground_loop.heartbeat import Triggers, changed, mtimes, own_files
from cairn.tools.liveness.liveness import read_liveness, write_liveness

CADENCE_S = 60.0  # the ruled cadence: once per minute (Akien, 2026-08-22)
EXIT_ALREADY_RUNNING = 3   # the loser's exit: not 1 (a crash), not 2 (argparse)

COMMAND_EXIT = "COMMAND_EXIT.flag"
COMMAND_DO_NOT_RESTART = "COMMAND_DO_NOT_RESTART.flag"


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _claim(home: Path):
    """The claim, or None when a LIVE loop holds it. A holder whose record is DEAD is hung:
    it is sent SIGTERM and the claim is taken once more."""
    try:
        return claim_singleton(home)
    except ClaimRefused as refusal:
        found = read_liveness(_now(), home)
        pid = (found.get("record") or {}).get("pid")
        if found["verdict"] == "LIVE" or not pid:
            print(f"ground_loop: a loop is running (pid {pid}, {found['verdict']}); "
                  f"refusing to start a second loop — {refusal}", file=sys.stderr)
            return None
        print(f"ground_loop: the claim holder pid {pid} is stale, not beating "
              f"({found.get('age_s')}s); sending SIGTERM", file=sys.stderr)
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        time.sleep(2)
        try:
            return claim_singleton(home)
        except ClaimRefused:
            print(f"ground_loop: the stale holder pid {pid} still holds the claim; "
                  "refusing to start a second loop", file=sys.stderr)
            return None


def main(home=None, roots=None, *, cadence: float = CADENCE_S, watch=None, class_root=None) -> int:
    home = Path(home) if home is not None else (
        instance_path("cairn", 0, roots) / "machines" / "ground_loop")
    instance_home = Path(roots["instance"]) / "devices" if roots else None
    claim = _claim(home)  # noqa: F841 — held for the process's whole life
    if claim is None:
        return EXIT_ALREADY_RUNNING

    flags = home / "flags"
    flags.mkdir(parents=True, exist_ok=True)
    for flag in (COMMAND_EXIT, COMMAND_DO_NOT_RESTART):
        (flags / flag).touch(exist_ok=True)

    started = _now().isoformat()
    recorded = mtimes(own_files(watch))
    triggers = Triggers()
    state = {"beats": 0, "started": started, "recorded_mtimes": recorded,
             "current_mtimes": recorded, "changed": [], "triggers": []}
    write_liveness(_now(), state, os.getpid(), home)

    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    while not stop.is_set():
        now = _now()
        current = mtimes(own_files(watch))
        diff = changed(recorded, current)
        calls = triggers.fire(now, pulse_sites(class_root, instance_home))
        state = {"beats": state["beats"] + 1, "started": started,
                 "recorded_mtimes": recorded, "current_mtimes": current,
                 "changed": diff, "triggers": calls}
        write_liveness(_now(), state, os.getpid(), home)
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
