"""``python3 -m cairn.devices.cairn.machines.bus serve|pulse`` (ticket 48519f4789b1).

``serve [--home H] [--scratch]`` runs the instance's one bus process (``server.py``);
``--scratch`` puts it over a throwaway table (``BusDevice.scratch``) for proofs.

``pulse [--home H]`` is what the ground loop's spawned pulse runs (decision 1): it asks the
bus process to flush its ring and exits. No bus process running means no ring holds anything,
so that is exit 0, recorded — never a reason to start one.
"""
from __future__ import annotations

import argparse
import json
import sys


def _pulse(home) -> int:
    # THROUGH THE PUBLISHED CLIENT, never a socket of its own: a second dialer here was a
    # second door, and the sole-path sieve reds any `socket` import outside inference_domain.
    from cairn.devices.cairn.machines.bus.server import bus_home
    from cairn.tools.bus_client.remote import exchange

    sock = bus_home(home) / "bus.sock"
    try:
        reply = exchange({"op": "flush"}, home, timeout=60)
    except (FileNotFoundError, ConnectionRefusedError):
        print(f"bus pulse: no bus process at {sock} — nothing in any ring")
        return 0
    if not reply.get("ok"):
        print(f"bus pulse: flush refused: {reply}", file=sys.stderr)
        return 1
    print(f"bus pulse: flushed {json.dumps(reply.get('json'))}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cairn.devices.cairn.machines.bus")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--home")
    s.add_argument("--scratch", action="store_true")
    p = sub.add_parser("pulse")
    p.add_argument("--home")
    args = ap.parse_args(argv)
    if args.cmd == "pulse":
        return _pulse(args.home)

    from cairn.devices.cairn.machines.bus.bus import BusDevice
    from cairn.devices.cairn.machines.bus.server import bus_home, serve

    home = bus_home(args.home)
    if args.scratch:
        with BusDevice.scratch("bus_proc") as bus:
            return serve(home, bus)
    return serve(home, BusDevice())


if __name__ == "__main__":
    sys.exit(main())
