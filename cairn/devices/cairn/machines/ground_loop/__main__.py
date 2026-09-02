"""python3 -m cairn.devices.cairn.machines.ground_loop — the thin wall-clock backing for the heartbeat.

THE ONE PART UNPROVABLE WITHOUT THE OS (loop.py filed it as an edge from birth;
ticket ground-loop-writes-its-own-liveness builds it): construct the resident
GroundLoopDevice with its instance home, beat it on the ruled once-per-second
cadence (decisions/2026-07-30-the-ground-loop-scans-disk-and-posts-to-the-bus),
exit cleanly on SIGINT/SIGTERM. Nothing else — no subscription seeding, no
callback logic, no routing: the 584aa74 goof stays out (firing lives in the
shims that subscribe, per the 2026-08-04 shim-routes-everything ruling), and
everything provable lives under this wrapper, sudo_relay daemon.py's shape.

TWO KINDS OF SIDE EFFECT, and the difference is the whole of Law 7. Every beat
REPLACES ``~/.cairn/devices/cairn/machines/ground_loop/0/liveness.json`` — a snapshot answering
"is it alive right now", true only at the instant it is read (the write is part
of the pass, in loop.py). Every gate contact EMITS one JSON file per record under
``~/.cairn/logs/<device>/<instance>/`` — a trail, where a file already written is
never rewritten. The snapshot and the trail sit in different directories and that
separation is the distinction on display.
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
from pathlib import Path

from cairn.tools.base.address import instance_path
from cairn.devices.cairn.machines.bus.bus import BusDevice
from cairn.devices.cairn.machines.bus.shim import BusShim
from cairn.devices.cairn.machines.ground_loop.discovery import discover, pulse_sites
from cairn.devices.cairn.machines.harbor_master.shim import HarborMasterShim
from cairn.devices.cairn.shim import CairnShim
from cairn.devices.inference_domain.shim import InferenceDomainShim
from cairn.tools.charter.shim import CharterShim
from cairn.devices.cairn.machines.ground_loop.guard import ClaimRefused, claim_singleton
from cairn.devices.cairn.machines.ground_loop.liveness import read_liveness
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice, arbitrate_newcomer
CADENCE_S = 60.0  # the ruled cadence: once per minute (Akien, 2026-08-22; was 1.0s)
EXIT_ALREADY_RUNNING = 3   # the loser's exit — not 1 (a crash's traceback), not 2 (argparse's)

# THE FLAGS (ticket a-stale-loop-restarts-itself, Akien's design 2026-08-19).
# Menu in <instance>/flags/ (permanent, ls shows all); active signals as zero-byte copies
# in the instance folder. The runner checks the signal folder once per beat — two stats.
COMMAND_EXIT = "COMMAND_EXIT.flag"
COMMAND_DO_NOT_RESTART = "COMMAND_DO_NOT_RESTART.flag"


def main(home=None, roots=None) -> int:
    # ``home`` has always meant the LIVENESS address specifically, and the two proofs that
    # inject it mean exactly that. ``roots`` redirects the whole instance tree — both trails
    # below and, when home is not given, the liveness record too — so a caller can run this
    # runner without touching the live tree it will later be read against.
    home = home if home is not None else instance_path("cairn", 0, roots) / "machines" / "ground_loop"
    try:
        claim = claim_singleton(home)  # noqa: F841 — held for the process's whole life
    except ClaimRefused as refusal:
        now = datetime.now(timezone.utc).astimezone()
        decision = arbitrate_newcomer(now, home)
        if decision["action"] == "takeover" and decision.get("pid"):
            import os as _os
            print(f"ground_loop: incumbent is stale ({decision['reason']}), "
                  f"killing pid {decision['pid']}", file=sys.stderr)
            try:
                _os.kill(decision["pid"], signal.SIGTERM)
                time.sleep(2)
            except OSError as kill_err:
                print(f"ground_loop: kill failed ({kill_err}), "
                      "proceeding to reclaim", file=sys.stderr)
            try:
                claim = claim_singleton(home)  # noqa: F841
            except ClaimRefused:
                print("ground_loop: reclaim failed after killing stale incumbent — "
                      "another newcomer may have taken it", file=sys.stderr)
                return EXIT_ALREADY_RUNNING
        else:
            found = read_liveness(now, home)
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
    device = GroundLoopDevice(liveness_home=home, discover=discover,
                              bus=bus, pulse_finder=pulse_sites)
    # THE BREADCRUMBS GET A WORLD — and no longer a NAME (ticket a-device-logs-without-being-wired,
    # 2026-08-18). These two lines used to read ``set_diagnostic_receiver(BreadcrumbLog("ground_loop",
    # 0, roots=roots))`` and the same for the bus, and they were the ONLY place in the running
    # system that knew those two strings. That is why they were also the only two trails that
    # existed: 17 components emit, one runner wired, and the other 15 appended to a list on an
    # object inside a process about to exit. A device now derives its own component name from its
    # class's module address and writes to ~/.cairn/logs/<device>/<instance>/ with nobody wiring
    # anything, so the naming half of these lines is gone and the trails are unchanged.
    #
    # WHAT STAYS IS THE WORLD-HANDING, which was always this runner's actual job — the same
    # reason it hands these devices a wall clock and a discoverer. ``roots`` is ``None`` in
    # production (the live tree) and a temp table for a caller running the whole loop against a
    # fixture; passing it here is what keeps such a caller from seeding the tree it is about to
    # read. Both devices, not one: the bus's records are the bus's (Law 6 on the file, not merely
    # in the code), and redirecting the loop while leaving the bus pointed at the live tree would
    # be half a fixture, which is worse than none.
    device.set_diagnostic_roots(roots)
    bus.set_diagnostic_roots(roots)
    # HAND-SUBSCRIBED SHIMS — devices that need a real shim beyond what disk discovery gives.
    # Each shim checks its own inbox on each pulse (BaseShim._check_mail); the BusShim's old
    # postman role (drain-and-dispatch) is dissolved. The bus still needs a shim for its probes.
    # The harbor_master needs a real shim so it can wake and receive the 29 probes' findings
    # that are addressed to it — as a DiscoveredShim it could only be pulsed, not paged.
    device.subscribe(BusShim(bus, device))
    device.subscribe(HarborMasterShim(bus=bus))
    device.subscribe(CairnShim(bus=bus))
    device.subscribe(InferenceDomainShim(bus=bus))
    device.subscribe(CharterShim(bus=bus))

    # THE FLAGS MENU (permanent; ls flags/ shows what is available).
    flags_dir = Path(home) / "flags"
    flags_dir.mkdir(parents=True, exist_ok=True)
    for flag in (COMMAND_EXIT, COMMAND_DO_NOT_RESTART):
        (flags_dir / flag).touch(exist_ok=True)

    stopping = {"now": False}

    def _stop(signum, frame):  # noqa: ARG001 — the signal API's shape
        stopping["now"] = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    while not stopping["now"]:
        device.beat(datetime.now(timezone.utc).astimezone())
        # TWO STAT CALLS PER BEAT — the flag check IS the poll (no inotify, no daemon).
        if (Path(home) / COMMAND_EXIT).exists():
            break
        if device.stale and not (Path(home) / COMMAND_DO_NOT_RESTART).exists():
            break
        time.sleep(CADENCE_S)
    return 0


if __name__ == "__main__":
    sys.exit(main())
