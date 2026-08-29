"""cairn groundloop stop|start|restart|status — the operator's interface to the heartbeat.

The ground loop's daemon process is managed through presence-based flag files
(ticket a-stale-loop-restarts-itself, Akien's design 2026-08-19) and the liveness
record (ticket ground-loop-writes-its-own-liveness). This CLI composes with both:
stop copies a flag, start spawns the runner, status reads the record. It adds no
mechanism — it is the human interface to mechanisms that already exist and are proved.

The missing piece surfaced 2026-08-29 when the trouble ticket
ground-loop-is-older-than-the-code-it-judges stayed open because nobody restarted
the loop. Akien: 'i do not believe there was ever an intent for [superclaude to
respawn it].' The detection (staleness) and the response (clean exit on drift) are
proved; the restart was a policy the operator had to remember. This command makes it
physics.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from shutil import copy2

from cairn.tools.base.address import instance_path
from cairn.devices.cairn.machines.ground_loop.liveness import read_liveness

INSTANCE = 0
COMMAND_EXIT = "COMMAND_EXIT.flag"


def _home() -> Path:
    return instance_path("cairn", INSTANCE) / "machines" / "ground_loop"


def _status() -> int:
    now = datetime.now(timezone.utc).astimezone()
    home = _home()
    found = read_liveness(now, home)
    record = found.get("record") or {}
    verdict = found["verdict"]
    pid = record.get("pid")
    beats = (record.get("state") or {}).get("beats")
    age_s = found.get("age_s")
    subscribers = (record.get("state") or {}).get("subscribers") or []

    print(f"ground_loop: {verdict}")
    if pid:
        print(f"  pid:         {pid}")
    if beats is not None:
        print(f"  beats:       {beats}")
    if age_s is not None:
        print(f"  last beat:   {age_s:.1f}s ago")
    if subscribers:
        print(f"  subscribers: {len(subscribers)}")
    if found.get("lack"):
        print(f"  note:        {found['lack']}")

    signal_file = home / COMMAND_EXIT
    if signal_file.exists():
        print(f"  signal:      COMMAND_EXIT.flag active (stop requested)")
    return 0


def _stop() -> int:
    home = _home()
    flags_dir = home / "flags"
    source = flags_dir / COMMAND_EXIT
    target = home / COMMAND_EXIT

    if target.exists():
        print("ground_loop: stop already signaled", file=sys.stderr)
        return 0

    if not source.exists():
        print(f"ground_loop: flag menu missing {COMMAND_EXIT} at {flags_dir}",
              file=sys.stderr)
        return 1

    copy2(str(source), str(target))
    print("ground_loop: stop signaled (flag copied to instance folder)")

    now = datetime.now(timezone.utc).astimezone()
    found = read_liveness(now, home)
    record = found.get("record") or {}
    pid = record.get("pid")
    if pid:
        print(f"  pid {pid} will exit on next beat cycle")
    return 0


def _start() -> int:
    home = _home()

    signal_file = home / COMMAND_EXIT
    if signal_file.exists():
        signal_file.unlink()
        print("ground_loop: cleared stale COMMAND_EXIT signal")

    repo = Path(__file__).resolve().parent.parent.parent.parent
    proc = subprocess.Popen(
        [sys.executable, "-m", "cairn.devices.cairn.machines.ground_loop"],
        cwd=str(repo),
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"ground_loop: started (pid {proc.pid})")
    print(f"  first beat in ~60s (the ruled cadence)")
    return 0


def _restart() -> int:
    home = _home()

    now = datetime.now(timezone.utc).astimezone()
    found = read_liveness(now, home)
    record = found.get("record") or {}
    old_pid = record.get("pid")

    if found["verdict"] == "LIVE" and old_pid:
        _stop()
        print("ground_loop: waiting for old process to exit...")
        for _ in range(10):
            time.sleep(1)
            try:
                os.kill(old_pid, 0)
            except OSError:
                break
        else:
            print(f"ground_loop: pid {old_pid} still alive after 10s, sending SIGTERM",
                  file=sys.stderr)
            try:
                os.kill(old_pid, signal.SIGTERM)
                time.sleep(2)
            except OSError:
                pass

    return _start()


def _clear_trouble() -> int:
    from cairn.devices.trouble.trouble import TroubleDevice
    trouble = TroubleDevice()
    identity = "ground-loop-is-older-than-the-code-it-judges"
    live = trouble.live()
    found = [t for t in live if t.get("id") == identity]
    if not found:
        print(f"ground_loop: no live trouble ticket '{identity}'")
        return 0
    trouble.clear(identity, by="cairn groundloop clear-trouble",
                  what_changed="The loop was restarted via `cairn groundloop restart`. "
                  "The new process holds current code.")
    print(f"ground_loop: cleared trouble '{identity}'")
    return 0


COMMANDS = {
    "status": _status,
    "stop": _stop,
    "start": _start,
    "restart": _restart,
    "clear-trouble": _clear_trouble,
}

USAGE = """\
usage: cairn groundloop <command>

commands:
  status          report LIVE/DEAD, pid, beats, age
  stop            signal the loop to exit on next beat
  start           spawn the ground loop daemon
  restart         stop + start
  clear-trouble   clear the ground-loop-is-older trouble ticket
"""


def main(args: list[str] | None = None) -> int:
    args = args if args is not None else sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    cmd = args[0]
    if cmd not in COMMANDS:
        print(f"ground_loop: unknown command '{cmd}'", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 1
    return COMMANDS[cmd]()


if __name__ == "__main__":
    sys.exit(main())
