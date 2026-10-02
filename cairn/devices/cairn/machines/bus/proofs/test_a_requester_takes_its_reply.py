"""PROOF for ticket 6b1e13704e17: a requester takes its reply.

Bus.request returns the reply correlated to the envelope it posted. Once a requester holds
that reply, it has taken the mail. Measured 2026-10-02: 2791 of 3181 undelivered envelopes
were trouble->cairn 'live reply' answers. The cairn device's trouble pane had already read
each one through request() (cairn/devices/cairn/device.py:97), but no receipt was ever
written, so the store's anti-join reported every one of them undelivered forever.

One tooth per numbered falsifier clause:

  1. AN UNWIRED REQUESTER'S REPLY IS RECEIPTED: a requester with no delivery hook (like
     'cairn') asks a fixture device; after request() returns and flush() runs,
     undelivered(to=<requester>) does not hold the reply.
  2. NO DOUBLE RECEIPT: a requester WITH a wired hook already receipts the reply in post's
     poke chain. After the exchange and a flush, the delivery table holds exactly one
     receipt for that reply.
  3. ONLY THE REPLY: an envelope posted to the requester outside any request stays
     undelivered across the exchange.

Requires Postgres; every bus rides BusDevice.scratch and drops at close.

    python3 cairn/devices/cairn/machines/bus/proofs/test_a_requester_takes_its_reply.py
"""

from __future__ import annotations

import contextlib
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.shim import BaseShim, ONLINE  # noqa: E402
from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.shim import BusShim  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402
from cairn.devices.db_domain.tools.client import store  # noqa: E402

PROVES = {"6b1e13704e17": {
    "1": "an_unwired_requesters_reply_is_receipted",
    "2": "a_wired_requester_gets_one_receipt_not_two",
    "3": "mail_outside_the_request_stays_undelivered",
}}

_SCRATCH = contextlib.ExitStack()
NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
PASS = 0
FAIL = 0


class AnswerDevice(BaseDevice):
    """Answers verb 'ask' with a dict, the way trouble answers 'live': the shim posts it back."""

    def intention(self) -> dict:
        return {"what": "testing-6b1e13704e17 answer device"}

    def state(self) -> dict:
        return {"at": "running"}

    def settings(self) -> dict:
        return {}

    def declared_verbs(self) -> dict:
        return {"ask": lambda envelope: {"answer": 42}}


class TakerDevice(AnswerDevice):
    """A wired requester: takes whatever is delivered to it."""

    def declared_verbs(self) -> dict:
        return {}

    def receive(self, envelope: dict):
        return {"took": envelope["id"]}


class _Shim(BaseShim):
    def __init__(self, device_id, device, bus) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self._device = device
        self._presence = ONLINE

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        return self._device


def _rig(*pairs):
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_rtr"))
    loop = GroundLoopDevice(bus=bus)
    loop.subscribe(BusShim(bus, loop))
    for device_id, device in pairs:
        loop.subscribe(_Shim(device_id, device, bus))
    loop.beat(NOW)
    return bus


def _undelivered_ids(bus, to):
    return {e["id"] for e in bus.undelivered(to=to, limit=1000)}


def an_unwired_requesters_reply_is_receipted():
    bus = _rig(("testing-answerer-1", AnswerDevice()))
    reply = bus.request(sender="testing-asker-1", to="testing-answerer-1", verb="ask",
                        why="testing-6b1e13704e17 tooth 1")
    assert reply["body"] == {"answer": 42}, reply
    bus.flush()
    assert reply["id"] not in _undelivered_ids(bus, "testing-asker-1"), (
        "the reply request() returned still stands undelivered to its requester")


def a_wired_requester_gets_one_receipt_not_two():
    bus = _rig(("testing-answerer-2", AnswerDevice()), ("testing-asker-2", TakerDevice()))
    reply = bus.request(sender="testing-asker-2", to="testing-answerer-2", verb="ask",
                        why="testing-6b1e13704e17 tooth 2")
    bus.flush()
    rows = store.read(bus.delivery_table, where="envelope = %s", params=(reply["id"],))
    assert len(rows) == 1, f"{len(rows)} receipts for one reply: {rows}"


def mail_outside_the_request_stays_undelivered():
    bus = _rig(("testing-answerer-3", AnswerDevice()))
    stray = bus.post(sender="testing-answerer-3", to="testing-asker-3", channel="personal",
                     why="testing-6b1e13704e17 tooth 3 stray", body={"stray": True})
    reply = bus.request(sender="testing-asker-3", to="testing-answerer-3", verb="ask",
                        why="testing-6b1e13704e17 tooth 3")
    bus.flush()
    left = _undelivered_ids(bus, "testing-asker-3")
    assert stray["id"] in left, "an envelope no request returned was marked delivered"
    assert reply["id"] not in left, "the reply itself was not taken"


TEETH = [an_unwired_requesters_reply_is_receipted,
         a_wired_requester_gets_one_receipt_not_two,
         mail_outside_the_request_stays_undelivered]


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
