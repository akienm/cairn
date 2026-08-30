"""PROOF — external participants are native bus citizens with no poke path.

An external participant (CC, Akien) has an address, a feed, and verbs like any
device — but no shim, no delivery poke, no running process. It reads its own
feed at its own arrival moment.

What a hollow build cannot pass (Law 8):

  - An adapter that creates a different kind of bus message fails
    ``test_external_post_uses_same_bus`` — the envelope is on the same transit table.
  - An adapter that requires a running device fails
    ``test_no_device_process_needed`` — ExternalParticipant works without a shim.
  - An adapter whose menu is hand-listed fails
    ``test_menu_on_announce_channel`` — the menu is compiled from declared verbs.

Requires Postgres (db_domain's durable transit). Self-cleaning.

    python3 cairn/devices/cairn/machines/bus/proofs/test_external_adapter.py  # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.external import ExternalParticipant  # noqa: E402
from cairn.tools.base.shim import BaseShim, ONLINE  # noqa: E402
from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.shim import BusShim  # noqa: E402
from cairn.devices.db_domain import store  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLES: list[str] = []
NOW = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)


class ReceiverDevice(BaseDevice):
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


def _fresh_bus():
    bus = BusDevice(table=f"_bus_ext_{_NONCE}_{len(_TABLES)}")
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

def test_external_post_uses_same_bus():
    """An external participant posts via the same bus.post() — one transit table, one
    substrate. A second kind of message fails here."""
    bus = _fresh_bus()
    ext = ExternalParticipant("cc_0", bus)
    envelope = ext.post(to="some_device", why="proof", body={"test": True})
    assert envelope["sender"] == "cc_0"
    all_mail = bus.read(to="some_device")
    assert len(all_mail) == 1
    assert all_mail[0]["id"] == envelope["id"]


def test_external_reads_own_feed():
    """An external participant reads its own feed — the pull-based arrival surface."""
    bus = _fresh_bus()
    receiver_dev = ReceiverDevice()
    receiver_shim = ReceiverShim("device_a", receiver_dev, bus=bus)
    loop = _rig(bus, receiver_shim)
    loop.beat(NOW)
    ext = ExternalParticipant("cc_0", bus)
    bus.post(sender="device_a", to="cc_0", channel="personal",
             why="hello CC", body={"greeting": True})
    feed = ext.read(channel="personal")
    assert len(feed) == 1
    assert feed[0]["body"] == {"greeting": True}
    assert feed[0]["sender"] == "device_a"


def test_no_device_process_needed():
    """An external participant works without a shim or device process — no poke path,
    no _start_device, no device class."""
    bus = _fresh_bus()
    ext = ExternalParticipant("akien_0", bus, verbs=["review", "approve"])
    ext.announce()
    ext.post(to="akien_0", channel="announce", why="self-test", body={"ok": True})
    feed = ext.read(channel="announce")
    assert len(feed) >= 2  # menu + self-test


def test_menu_on_announce_channel():
    """The external participant's menu is published on the announce channel, matching
    a device's _announce_menu — compiled from declared verbs."""
    bus = _fresh_bus()
    ext = ExternalParticipant("cc_0", bus, verbs=["build", "review", "diagnose"])
    ext.announce()
    feed = ext.read(channel="announce")
    menu_posts = [e for e in feed if e.get("body", {}).get("verbs") is not None]
    assert len(menu_posts) >= 1
    assert menu_posts[-1]["body"]["verbs"] == ["build", "diagnose", "review"]


def test_external_can_read_device_announce():
    """An external participant reads another device's announce feed to discover its
    verbs — the menu is the interface."""
    bus = _fresh_bus()
    # A device with verbs
    receiver_dev = ReceiverDevice()
    receiver_shim = ReceiverShim("device_b", receiver_dev, bus=bus)
    loop = _rig(bus, receiver_shim)
    loop.beat(NOW)  # wires delivery + announces menu
    ext = ExternalParticipant("cc_0", bus)
    target_announce = bus.read(to="device_b", channel="announce")
    menu_posts = [e for e in target_announce if e.get("body", {}).get("verbs") is not None]
    assert len(menu_posts) >= 1, "device should have an announce menu"


def test_unread_mail_waits():
    """Mail to an external participant with no poke path waits in transit — the
    participant reads it at its own arrival moment."""
    bus = _fresh_bus()
    ext = ExternalParticipant("cc_0", bus)
    bus.post(sender="device_x", to="cc_0", channel="personal",
             why="waiting for CC", body={"urgent": True})
    waiting = ext.unread()
    assert len(waiting) == 1
    assert waiting[0]["body"] == {"urgent": True}


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
    print("green — external participants: same bus, own feed, no poke needed")
