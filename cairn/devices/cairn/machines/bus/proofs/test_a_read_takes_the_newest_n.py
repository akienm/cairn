"""Teeth for ticket f8a97b570073 — a bus read can ask for only the newest N, and how many there are.

MEASURED 2026-10-10 (trouble chat-pane-is-unbounded): GET /device/cairn took ~25 s for a
99,981-byte page, because ``BusDevice.read`` had no limit and every pane read the whole channel
to show its newest 200.

Every tooth runs over a bus of its own, ``BusDevice.scratch()`` — a test-marked transit table
that drops at exit (or at the tester's next sweep). 300 messages go to one addressee on one
channel, the first 180 flushed to the table and the last 120 still in the ring, so a newest-N
read has to merge both halves; 10 more go to a second addressee so a filter that is ignored
shows. Rows are compared by envelope id, the one field both halves carry identically.

    python3 cairn/devices/cairn/machines/bus/proofs/test_a_read_takes_the_newest_n.py   # exit 0 = green
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402

PROVES = {
    "f8a97b570073": {
        "1": "a_limited_read_returns_the_newest_n_oldest_first",
        "2": "count_returns_how_many_match",
        "3": "an_unlimited_read_returns_every_message",
    },
}

READER, OTHER, CHANNEL = "newest-n-reader", "newest-n-other", "personal"
FLUSHED, IN_RING, OTHERS = 180, 120, 10
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:400]}")
    if not ok:
        FAILURES.append(name)


def _fill(bus: BusDevice) -> list[str]:
    """300 to READER (180 flushed, 120 in the ring) and 10 to OTHER; READER's ids in order."""
    ids = []
    for n in range(FLUSHED + IN_RING):
        if n == FLUSHED:
            bus.flush()
        env = bus.post(sender="newest-n-proof", to=READER, channel=CHANNEL,
                       why="the newest-N proof's fixture", body={"n": n})
        ids.append(env["id"])
        if n % 30 == 0:
            bus.post(sender="newest-n-proof", to=OTHER, channel=CHANNEL,
                     why="the newest-N proof's other addressee", body={"n": n})
    return ids


def _ids(rows) -> list[str]:
    return [r["id"] for r in rows]


def tooth_1(bus: BusDevice, ids: list[str]) -> None:
    name = PROVES["f8a97b570073"]["1"]
    try:
        got50 = _ids(bus.read(to=READER, channel=CHANNEL, limit=50))      # all in the ring
        got200 = _ids(bus.read(to=READER, channel=CHANNEL, limit=200))    # spans table + ring
        got5 = _ids(bus.read(to=READER, channel=CHANNEL, limit=5))
        check(name, got50 == ids[-50:] and got200 == ids[-200:] and got5 == ids[-5:],
              f"50: {len(got50)} match={got50 == ids[-50:]}; 200: {len(got200)} "
              f"match={got200 == ids[-200:]}; 5: match={got5 == ids[-5:]}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(bus: BusDevice) -> None:
    name = PROVES["f8a97b570073"]["2"]
    try:
        mine = bus.count(to=READER, channel=CHANNEL)
        other = bus.count(to=OTHER, channel=CHANNEL)
        check(name, mine == FLUSHED + IN_RING and other == OTHERS,
              f"count(reader)={mine} (want {FLUSHED + IN_RING}); count(other)={other} (want {OTHERS})")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(bus: BusDevice, ids: list[str]) -> None:
    name = PROVES["f8a97b570073"]["3"]
    try:
        got = _ids(bus.read(to=READER, channel=CHANNEL))
        check(name, got == ids, f"read() returned {len(got)} of {len(ids)}, in order={got == ids}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    with BusDevice.scratch(prefix="bus_newest_n") as bus:
        ids = _fill(bus)
        tooth_1(bus, ids)
        tooth_2(bus)
        tooth_3(bus, ids)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
