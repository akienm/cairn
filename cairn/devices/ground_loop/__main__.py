"""python3 -m cairn.devices.ground_loop — the thin wall-clock backing for the heartbeat.

THE ONE PART UNPROVABLE WITHOUT THE OS (loop.py filed it as an edge from birth;
ticket ground-loop-writes-its-own-liveness builds it): construct the resident
GroundLoopDevice with its instance home, beat it on the ruled once-per-second
cadence (decisions/2026-07-30-the-ground-loop-scans-disk-and-posts-to-the-bus),
exit cleanly on SIGINT/SIGTERM. Nothing else — no subscription seeding, no
callback logic, no routing: the 584aa74 goof stays out (firing lives in the
shims that subscribe, per the 2026-08-04 shim-routes-everything ruling), and
everything provable lives under this wrapper, sudo_relay daemon.py's shape.

TWO KINDS OF SIDE EFFECT, and the difference is the whole of Law 7. Every beat
REPLACES ``~/.cairn/devices/ground_loop/0/liveness.json`` — a snapshot answering
"is it alive right now", true only at the instant it is read (the write is part
of the pass, in loop.py). Every gate contact APPENDS to ``diagnostics.jsonl``
beside it — a trail, where a line already written is never rewritten. The two
files sit in the same directory and that adjacency is the distinction on display.
Timestamps are timezone-aware — the read face subtracts.

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

from cairn.tools.base.address import instance_path
from cairn.devices.bus.bus import BusDevice
from cairn.devices.bus.shim import BusShim
from cairn.machines.diagnostic_inspector.log import BreadcrumbLog
from cairn.devices.ground_loop.discovery import discover, pulse_sites
from cairn.devices.ground_loop.guard import ClaimRefused, claim_singleton
from cairn.devices.ground_loop.liveness import read_liveness
from cairn.devices.ground_loop.loop import GroundLoopDevice
from cairn.devices.trouble.trouble import TroubleDevice

CADENCE_S = 1.0   # the ruled cadence: once per second (Akien, 2026-07-30)
EXIT_ALREADY_RUNNING = 3   # the loser's exit — not 1 (a crash's traceback), not 2 (argparse's)


def main(home=None, roots=None) -> int:
    # ``home`` has always meant the LIVENESS address specifically, and the two proofs that
    # inject it mean exactly that. ``roots`` redirects the whole instance tree — both trails
    # below and, when home is not given, the liveness record too — so a caller can run this
    # runner without touching the live tree it will later be read against.
    home = home if home is not None else instance_path("ground_loop", 0, roots)
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

    # THE RESIDENT LOOP IS THE WIRED ONE. The device stays provable without a filesystem or a
    # trouble store (both injected, both defaulting to None — the pure-physics proofs build it
    # bare); this runner is the one place that hands it the real world, the same way it is the
    # one place that hands it a wall clock. A loop with no discoverer beats an empty roster,
    # which is precisely the state that went unnoticed from 2026-08-09 to 2026-08-11.
    bus = BusDevice()
    # ``pulse_finder`` wires the second registration surface (ticket
    # the-pulse-file-is-the-subscription): groundloop/pulse.py at class or instance level,
    # found each beat, activated on presence, unloaded on absence. Injected here, like
    # ``discover``, because this runner is where the loop meets the real disk.
    device = GroundLoopDevice(liveness_home=home, discover=discover, trouble=TroubleDevice(),
                              bus=bus, pulse_finder=pulse_sites)
    # THE BREADCRUMBS GET A HOME (ticket a-record-reaches-disk). Until this line every emit in
    # the running system marked itself ``home='held'`` and appended to a list on an object
    # inside a process that was about to exit — ``set_diagnostic_receiver`` had no live caller
    # anywhere, so 22 emit sites wrote to nothing that outlived the run. Wired HERE because
    # this runner is the one place that hands these devices the real world, the same way it
    # hands them a wall clock and a discoverer. ONE TRAIL PER DEVICE, each in that device's own
    # instance space: the bus's records are the bus's (Law 6 on the file, not merely in the
    # code), and there is no shared file for two owners to write into. Both, not one — wiring
    # the loop and leaving the bus held would close half the finding in the same three lines.
    device.set_diagnostic_receiver(BreadcrumbLog("ground_loop", 0, roots=roots))
    bus.set_diagnostic_receiver(BreadcrumbLog("bus", 0, roots=roots))
    # THE POSTMAN, hand-subscribed. Delivery is the BUS's act, never the heartbeat's — the
    # ground_loop does not route (that clause is the 584aa74 goof's headstone) — so the bus's
    # own shim drains the transit table on each pulse and hands each envelope to the shim of
    # its addressee, reached through the roster the heartbeat already publishes. Subscribed by
    # hand because it is the one shim that must hold a reference to the heartbeat itself, and
    # a folder on disk cannot express that.
    device.subscribe(BusShim(bus, device))
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
