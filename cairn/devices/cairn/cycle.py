"""cairn start / stop / restart — bring the system up, take it down, cycle it (ticket 3264ef726e35).

Outline 5.3.4: "`cairn start` (= cairn cairn start) brings the system up: ground loop, bus, shims.
`cairn stop` takes it down." The shims live in the one bus process, so the system's parts are
two, and the order between them is containment: the loop's pulse wakes shims and their mail wakes
the bus (5.3.5.5), so stop takes the loop down first and then the bus, and start wakes the loop and
then the bus. Claude Code sessions are not touched (Akien, open-b5cabfa28fb6: "No, cairn restart
does not restart the running cc instance(s)").

Nothing here is a new mechanism. The loop is named by its lock (guard.held) and its record
(heartbeat.read_record), stopped by SIGTERM (which ends it promptly: ground_loop proof
test_stop_is_prompt) and woken by shim.ensure_ground_loop. The bus is asked through
remote.exchange, which dials and never wakes, and woken by remote.ensure_bus. Every home is read
from HOME, so the same verbs run over a scratch HOME cycle a scratch system.

Each part prints one line. A part still in the wrong state after its bounded wait is said
plainly and makes the verb exit 1 (Law 7).
"""
from __future__ import annotations

import os
import signal
import time
from pathlib import Path

from cairn.devices.cairn.machines.ground_loop.guard import held
from cairn.devices.cairn.machines.ground_loop.heartbeat import read_record
from cairn.tools.base.address import instance_path

COMMAND_EXIT = "COMMAND_EXIT.flag"   # the loop's stop flag (ground_loop/__main__.py)
LOOP_DOWN_WAIT_S = 90                # a beat in flight costs about 24 s; SIGTERM ends the sleep at once
LOOP_UP_WAIT_S = 60                  # a wake waits at most 60 s (5.3.5.4)
BUS_DOWN_WAIT_S = 60


def _loop_home() -> Path:
    return instance_path("cairn", 0) / "machines" / "ground_loop"


def _loop_pid(home: Path) -> int | None:
    return (read_record(home).get("record") or {}).get("pid")


def _bus_answer() -> dict | None:
    """The bus's answer to stats, or None when nothing answers. Dials; never wakes."""
    from cairn.tools.bus_client.remote import exchange
    try:
        return exchange({"op": "stats"}, timeout=10)
    except (OSError, ConnectionError, ValueError):
        return None


def _wait(cond, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if cond():
            return True
        time.sleep(0.25)
    return cond()


def _stop_loop() -> bool:
    home = _loop_home()
    if not held(home):
        print("ground loop: already down")
        return True
    pid = _loop_pid(home)
    if pid:
        try:
            os.kill(int(pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
    if _wait(lambda: not held(home), LOOP_DOWN_WAIT_S):
        print(f"ground loop: stopped (pid {pid})")
        return True
    print(f"ground loop: STILL UP after {LOOP_DOWN_WAIT_S}s (its record names pid {pid})")
    return False


def _stop_bus() -> bool:
    found = _bus_answer()
    if found is None:
        print("bus: already down")
        return True
    pid = (found.get("json") or {}).get("pid")
    from cairn.tools.bus_client.remote import exchange
    try:
        exchange({"op": "shutdown"}, timeout=60)
    except (OSError, ConnectionError, ValueError):
        pass
    if _wait(lambda: _bus_answer() is None, BUS_DOWN_WAIT_S):
        print(f"bus: stopped (pid {pid}; its shims with it)")
        return True
    print(f"bus: STILL ANSWERING after {BUS_DOWN_WAIT_S}s (pid {pid})")
    return False


def _start_loop() -> bool:
    from cairn.tools.base.shim import ensure_ground_loop
    home = _loop_home()
    flag = home / COMMAND_EXIT
    if flag.exists():               # a stop flag left here would end the new loop at its first beat
        flag.unlink()
    woke = ensure_ground_loop()
    if _wait(lambda: held(home), LOOP_UP_WAIT_S):
        print(f"ground loop: up (pid {_loop_pid(home)})")
        return True
    print(f"ground loop: NOT UP after {LOOP_UP_WAIT_S}s ({woke.get('note')})")
    return False


def _start_bus() -> bool:
    from cairn.tools.bus_client.remote import ensure_bus
    try:
        stats = ensure_bus()
    except (OSError, ConnectionError, RuntimeError) as exc:
        print(f"bus: NOT UP ({exc})")
        return False
    print(f"bus: up (pid {stats.get('pid')})")
    return True


def stop() -> int:
    """Take the system down: the ground loop, then the bus. 0 when both are down."""
    ok = _stop_loop()
    ok = _stop_bus() and ok
    return 0 if ok else 1


def start() -> int:
    """Bring the system up: the ground loop, then the bus. 0 when both are up."""
    ok = _start_loop()
    ok = _start_bus() and ok
    return 0 if ok else 1


def restart() -> int:
    """stop, then start; 1 if either leaves a part in the wrong state."""
    down = stop()
    up = start()
    return 0 if down == 0 and up == 0 else 1
