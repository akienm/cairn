"""``python3 -m cairn.devices.cairn pulse`` — the cairn device's pulse (ticket 9b6b392ebcfe).

Runs the idle trigger once and exits: read the four activity sources, decide whether a sleep
cycle is due, ask this device's own ``sleep-cycle`` verb to mint when it is, and write the one
decision record to ``pulse.json``. What spawns it on the beat is ticket acb4ecd84364's.
"""
from __future__ import annotations

import argparse
import json
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cairn.devices.cairn")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pulse")
    ap.parse_args(argv)

    from cairn.devices.cairn.machines.sleep_cycle.idle import pulse
    record = pulse()
    print(f"cairn pulse: {'DUE' if record['due'] else 'not due'} — {record['why']}"
          + (f"; minted {json.dumps(record['minted'])}" if record["minted"] else ""))
    for name, s in record["sources"].items():
        if s["unread"]:
            print(f"  unread {name}: {s['unread']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
