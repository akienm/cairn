"""python3 -m cairn.ground_loop — the thin wall-clock backing for the heartbeat.

THE ONE PART UNPROVABLE WITHOUT THE OS (loop.py filed it as an edge from birth;
ticket ground-loop-writes-its-own-liveness builds it): construct the resident
GroundLoopDevice with its instance home, beat it on the ruled once-per-second
cadence (decisions/2026-07-30-the-ground-loop-scans-disk-and-posts-to-the-bus),
exit cleanly on SIGINT/SIGTERM. Nothing else — no subscription seeding, no
callback logic, no routing: the 584aa74 goof stays out (firing lives in the
shims that subscribe, per the 2026-08-04 shim-routes-everything ruling), and
everything provable lives under this wrapper, sudo_relay daemon.py's shape.

The liveness record is this process's only side effect: every beat touches
``~/.cairn/devices/ground_loop/0/liveness.json`` (the write is part of the
pass, in loop.py). Timestamps are timezone-aware — the read face subtracts.

THE DOOR GUARDS ITSELF (ticket an-entry-point-starts-the-loop-only-once): the
runner claims the singleton BEFORE constructing the device, so any entry point
— superclaude is one of them — gets the only-once guarantee by spawning this
module, a CALL, not a policy (Law 1: no caller re-derives the guard; Law 6: it
lives with the thing it protects). The winner holds the claim until death; a
loser reads the RECORD to say what is running (never the process table) and
exits ``EXIT_ALREADY_RUNNING`` — distinct from a crash, so a launcher can tell
"refused, one is running" (fine) from "broke" (not fine).
"""

from __future__ import annotations

import signal
import sys
import time
from datetime import datetime, timezone

from cairn.ground_loop.guard import ClaimRefused, claim_singleton
from cairn.ground_loop.liveness import instance_home, read_liveness
from cairn.ground_loop.loop import GroundLoopDevice

CADENCE_S = 1.0   # the ruled cadence: once per second (Akien, 2026-07-30)
EXIT_ALREADY_RUNNING = 3   # the loser's exit — not 1 (a crash's traceback), not 2 (argparse's)


def main(home=None) -> int:
    home = home if home is not None else instance_home()
    try:
        claim = claim_singleton(home)  # noqa: F841 — held for the process's whole life
    except ClaimRefused as refusal:
        found = read_liveness(datetime.now(timezone.utc).astimezone(), home)
        record = found.get("record") or {}
        if found["verdict"] == "LIVE":
            detail = (f"the record says pid {record.get('pid')} last ran "
                      f"{found['age_s']:.2f}s ago")
        else:
            detail = ("the claim is held but the record is "
                      f"{found.get('lack', 'stale')} — a loop alive inside its first beats "
                      "or merely slow; the held lock outranks the stale read")
        print(f"ground_loop: refusing to start a second loop — {refusal}\n"
              f"ground_loop: {detail}", file=sys.stderr)
        return EXIT_ALREADY_RUNNING

    device = GroundLoopDevice(liveness_home=home)
    stopping = {"now": False}

    def _stop(signum, frame):  # noqa: ARG001 — the signal API's shape
        stopping["now"] = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    while not stopping["now"]:
        device.beat(datetime.now(timezone.utc).astimezone())
        time.sleep(CADENCE_S)
    return 0


if __name__ == "__main__":
    sys.exit(main())
