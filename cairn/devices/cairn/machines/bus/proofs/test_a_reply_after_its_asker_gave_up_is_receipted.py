"""PROOF for ticket cd2d27fe3261: a reply that lands after its asker gave up is receipted.

Bus.request posts, polls for the correlated reply, and raises TimeoutError at its deadline.
After that nobody holds the request any more, so a reply landing later has no asker to take
it, and it stands undelivered until report_stood raises mail-<asker>-stood-600s. Measured
2026-10-18 by CC: of the 6 envelopes standing undelivered, 5 were tester->constrain 'run'
replies. Each one came 3-13 minutes after its request, and the constrain floor asks with
timeout=180 (cairn/devices/codemother/machines/constrain/constrain.py:371). That gave
trouble mail-constrain-stood-600s a count of 39.

One tooth per numbered falsifier clause:

  1. THE LATE REPLY IS RECEIPTED: a request times out, the answerer's reply lands after, and
     after flush() undelivered(to=<asker>) does not hold it.
  2. THE RECEIPT SAYS THE ASKER GAVE UP: the one delivery row for that reply carries
     by='bus-asker-gave-up', so the record of truth says why nobody took it (Law 7).
  3. ONLY AN ABANDONED REQUEST'S REPLY: a reply to an envelope that was never a request
     stays undelivered across the same flush.

Requires Postgres; every bus rides BusDevice.scratch and drops at close.

    python3 cairn/devices/cairn/machines/bus/proofs/test_a_reply_after_its_asker_gave_up_is_receipted.py
"""

from __future__ import annotations

import contextlib
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.shim import BusShim  # noqa: E402
from cairn.tools.bus_client.roster import DeviceRoster  # noqa: E402
from cairn.devices.db_domain.tools.client import store  # noqa: E402

PROVES = {"cd2d27fe3261": {
    "1": "a_reply_after_the_asker_gave_up_is_receipted",
    "2": "the_receipt_says_the_asker_gave_up",
    "3": "a_reply_to_no_request_stays_undelivered",
}}

_SCRATCH = contextlib.ExitStack()
NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
PASS = 0
FAIL = 0


def _rig():
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_rag"))
    loop = DeviceRoster(bus)
    loop.hold(BusShim(bus, loop))
    loop.pulse(NOW)
    return bus


def _abandoned(bus, asker, slow):
    """Ask a device nobody holds, so request() reaches its deadline; return the request."""
    try:
        bus.request(sender=asker, to=slow, verb="run", why="testing-cd2d27fe3261 the ask",
                    timeout=0.3)
    except TimeoutError:
        pass
    else:
        raise AssertionError("the request was answered; the rig needs a silent addressee")
    asks = [e for e in bus.read(to=slow) if e.get("sender") == asker]
    assert len(asks) == 1, asks
    return asks[0]


def _late_reply(bus, ask, slow, asker):
    return bus.post(sender=slow, to=asker, channel="personal", why="testing-cd2d27fe3261 run reply",
                    body={"verdict": "green"}, reply_to=ask["id"])


def _undelivered_ids(bus, to):
    return {e["id"] for e in bus.undelivered(to=to, limit=1000)}


def a_reply_after_the_asker_gave_up_is_receipted():
    bus = _rig()
    ask = _abandoned(bus, "testing-asker-1", "testing-slow-1")
    reply = _late_reply(bus, ask, "testing-slow-1", "testing-asker-1")
    bus.flush()
    assert reply["id"] not in _undelivered_ids(bus, "testing-asker-1"), (
        "the reply that landed after request() gave up still stands undelivered")


def the_receipt_says_the_asker_gave_up():
    bus = _rig()
    ask = _abandoned(bus, "testing-asker-2", "testing-slow-2")
    reply = _late_reply(bus, ask, "testing-slow-2", "testing-asker-2")
    bus.flush()
    rows = store.read(bus.delivery_table, where="envelope = %s", params=(reply["id"],))
    assert [r["by"] for r in rows] == ["bus-asker-gave-up"], rows


def a_reply_to_no_request_stays_undelivered():
    bus = _rig()
    _abandoned(bus, "testing-asker-3", "testing-slow-3")
    plain = bus.post(sender="testing-asker-3", to="testing-slow-3", channel="personal",
                     why="testing-cd2d27fe3261 a letter, not a request", body={})
    stray = bus.post(sender="testing-slow-3", to="testing-asker-3", channel="personal",
                     why="testing-cd2d27fe3261 an answer to the letter", body={},
                     reply_to=plain["id"])
    bus.flush()
    assert stray["id"] in _undelivered_ids(bus, "testing-asker-3"), (
        "a reply to an envelope nobody asked through request() was receipted")


TEETH = [a_reply_after_the_asker_gave_up_is_receipted,
         the_receipt_says_the_asker_gave_up,
         a_reply_to_no_request_stays_undelivered]


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {fn.__name__}")


if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn)
    finally:
        _SCRATCH.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
