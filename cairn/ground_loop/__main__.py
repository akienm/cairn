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
"""

from __future__ import annotations

import signal
import sys
import time
from datetime import datetime, timezone

from cairn.ground_loop.liveness import instance_home
from cairn.ground_loop.loop import GroundLoopDevice

CADENCE_S = 1.0   # the ruled cadence: once per second (Akien, 2026-07-30)


def main() -> int:
    device = GroundLoopDevice(liveness_home=instance_home())
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
