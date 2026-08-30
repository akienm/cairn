"""PROOF — probe envelopes ARRIVE at their target device.

The first real rider: shim._fire has posted probe envelopes since 2026-07-18 and
nothing ever received one. This proof closes the loop — a fired probe reaches its
addressee through the bus, event-driven by the delivery poke.

What a hollow build cannot pass (Law 8):

  - A post() that writes but never pokes (the pre-delivery-poke state) fails
    ``test_probe_arrives_at_target`` — the envelope sits in transit forever.
  - A poke that fires but never calls deliver() fails the same tooth — the target
    device never sees the envelope.
  - A target that receives the envelope but loses the body/verb fails
    ``test_probe_body_arrives_intact`` — the payload the trigger saw must be what
    the receiver reads.
  - A probe that fires to a device with no shim (not on the roster) fails
    ``test_probe_to_unwired_device_sits`` — mail waits honestly rather than being
    dropped or erroring the sender.

Requires Postgres (db_domain's durable transit). Self-cleaning.

    python3 cairn/devices/cairn/machines/bus/proofs/test_first_rider.py   # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.shim import BaseShim, ONLINE  # noqa: E402
from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.tools.base.probe import Probe  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.shim import BusShim  # noqa: E402
from cairn.devices.db_domain import store  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLES: list[str] = []
NOW = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)


class ReceiverDevice(BaseDevice):
    """A device that records what it receives."""

    def __init__(self) -> None:
        super().__init__()
        self.got: list[dict] = []

    def intention(self) -> dict:
        return {"what": "proof receiver"}

    def state(self) -> dict:
        return {"at": "running"}

    def settings(self) -> dict:
        return {}

    def receive(self, envelope: dict):
        self.got.append(envelope)
        return {"ack": envelope["id"]}


class ReceiverShim(BaseShim):
    def __init__(self, device_id: str, device: ReceiverDevice, bus=None) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self._device = device
        self._presence = ONLINE

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        return self._device


class SenderDevice(BaseDevice):
    """A device whose probes fire TO a target."""

    def __init__(self) -> None:
        super().__init__()

    def intention(self) -> dict:
        return {"what": "proof sender"}

    def state(self) -> dict:
        return {"at": "running"}

    def settings(self) -> dict:
        return {}


class SenderShim(BaseShim):
    def __init__(self, device_id: str, device: SenderDevice, bus=None,
                 target: str = "", probe_body: dict | None = None) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self._device = device
        self._presence = ONLINE
        self._target = target
        self._probe_body = probe_body or {"nexus": "test", "kind": "rider"}

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        return self._device

    def probes(self) -> list[Probe]:
        return [Probe(
            why="first real rider proof",
            trigger=lambda now, ctx: True,
            to=self._target,
            body=self._probe_body,
        )]


def _fresh_bus():
    bus = BusDevice(table=f"_bus_rider_{_NONCE}_{len(_TABLES)}")
    _TABLES.append(bus.table)
    return bus


def _rig(bus, *shims):
    loop = GroundLoopDevice(bus=bus)
    bus_shim = BusShim(bus, loop)
    loop.subscribe(bus_shim)
    for shim in shims:
        loop.subscribe(shim)
    return loop


# --- teeth ------------------------------------------------------------------

def test_probe_arrives_at_target():
    """A probe fires from sender, arrives at receiver — end-to-end through the bus.
    This is the loop that was open since 2026-07-18."""
    receiver_dev = ReceiverDevice()
    sender_dev = SenderDevice()
    bus = _fresh_bus()
    receiver_shim = ReceiverShim("receiver_a", receiver_dev, bus=bus)
    sender_shim = SenderShim("sender_a", sender_dev, bus=bus, target="receiver_a")
    loop = _rig(bus, receiver_shim, sender_shim)
    loop.beat(NOW)  # first beat: wires delivery for both, sender's probe fires
    assert len(receiver_dev.got) == 1, \
        f"expected 1 envelope at receiver, got {len(receiver_dev.got)}"
    assert receiver_dev.got[0]["sender"] == "sender_a"
    assert receiver_dev.got[0]["addressee"] == "receiver_a"


def test_probe_body_arrives_intact():
    """The probe's body — the artifact at the gate — arrives bit-identical at the receiver."""
    receiver_dev = ReceiverDevice()
    sender_dev = SenderDevice()
    bus = _fresh_bus()
    body = {"nexus": "triage", "kind": "efficacy", "detail": {"score": 0.95}}
    receiver_shim = ReceiverShim("receiver_b", receiver_dev, bus=bus)
    sender_shim = SenderShim("sender_b", sender_dev, bus=bus,
                             target="receiver_b", probe_body=body)
    loop = _rig(bus, receiver_shim, sender_shim)
    loop.beat(NOW)
    assert len(receiver_dev.got) == 1
    assert receiver_dev.got[0]["body"] == body


def test_probe_to_unwired_device_sits():
    """A probe fired to a device with no shim on the roster: the envelope sits in transit
    honestly. No error, no drop — the mail waits."""
    sender_dev = SenderDevice()
    bus = _fresh_bus()
    sender_shim = SenderShim("sender_c", sender_dev, bus=bus, target="nobody_home")
    loop = _rig(bus, sender_shim)
    loop.beat(NOW)
    waiting = bus.undelivered(to="nobody_home")
    assert len(waiting) == 1, f"expected 1 waiting envelope, got {len(waiting)}"
    assert waiting[0]["sender"] == "sender_c"


def test_receipt_is_written_after_delivery():
    """The receipt proves the envelope was delivered — the bus knows it arrived."""
    receiver_dev = ReceiverDevice()
    sender_dev = SenderDevice()
    bus = _fresh_bus()
    receiver_shim = ReceiverShim("receiver_d", receiver_dev, bus=bus)
    sender_shim = SenderShim("sender_d", sender_dev, bus=bus, target="receiver_d")
    loop = _rig(bus, receiver_shim, sender_shim)
    loop.beat(NOW)
    assert bus.undelivered(to="receiver_d") == [], \
        "delivered envelope should not appear as undelivered"
    assert len(receiver_dev.got) == 1


if __name__ == "__main__":
    failures = 0
    try:
        for name, fn in sorted(globals().items()):
            if not name.startswith("test_") or not callable(fn):
                continue
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    finally:
        try:
            conn = store.connect()
            with conn.cursor() as cur:
                for base in _TABLES:
                    for table in (f"{base}_delivery", base):
                        cur.execute(f'DROP TABLE IF EXISTS "{table}"')
                        cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s',
                                    (table,))
            conn.close()
        except Exception as exc:  # noqa: BLE001
            print(f"  (cleanup refused: {type(exc).__name__}: {exc})")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — the first real rider: probes fire, arrive, and the loop is closed")
