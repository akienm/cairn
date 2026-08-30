"""PROOF — the announce menu is COMPILED from declared_verbs(), not hand-listed.

Add a handler to a device, it appears on the menu. No second edit, no second registry
(Law 1). The menu is a record on the device's announce channel — inspecting a device is
reading its feed.

What a hollow build cannot pass (Law 8):

  - A hand-listed menu passes every count check and fails
    ``test_menu_matches_declared_verbs`` — the tooth pins that the menu is DERIVED from
    the device's declared_verbs(), not authored separately.
  - A menu that lives outside the bus passes the content checks and fails
    ``test_menu_is_on_the_announce_channel`` — the tooth reads the bus feed, not a side
    surface.
  - A menu that fires on the personal channel fails
    ``test_menu_does_not_trigger_delivery`` — announce is a RECORD, not a poke.

Requires Postgres (db_domain's durable transit). Self-cleaning.

    python3 cairn/devices/cairn/machines/bus/proofs/test_announce_menu.py   # exit 0 = green
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
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.shim import BusShim  # noqa: E402
from cairn.devices.db_domain import store  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLES: list[str] = []
NOW = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)


class MenuDevice(BaseDevice):
    """A device with declared verbs — the smallest honest menu publisher."""

    def __init__(self, verbs: dict | None = None) -> None:
        super().__init__()
        self._verbs = verbs or {}

    def intention(self) -> dict:
        return {"what": "proof device with verbs"}

    def state(self) -> dict:
        return {"at": "running"}

    def settings(self) -> dict:
        return {}

    def declared_verbs(self) -> dict:
        return dict(self._verbs)

    def receive(self, envelope: dict):
        return {"ack": envelope["id"]}


class MenuShim(BaseShim):
    def __init__(self, device_id: str, device: MenuDevice, bus=None) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self._device = device
        self._presence = ONLINE

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        return self._device


class EmptyDevice(BaseDevice):
    """A device with no verbs — empty menu is honest, not broken."""

    def intention(self) -> dict:
        return {"what": "proof device with no verbs"}

    def state(self) -> dict:
        return {"at": "running"}

    def settings(self) -> dict:
        return {}

    def receive(self, envelope: dict):
        return {"ack": envelope["id"]}


class EmptyShim(BaseShim):
    def __init__(self, device_id: str, device: EmptyDevice, bus=None) -> None:
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
    bus = BusDevice(table=f"_bus_menu_{_NONCE}_{len(_TABLES)}")
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

def test_menu_matches_declared_verbs():
    """The menu is COMPILED from declared_verbs() — add a verb, it appears. A hand-listed
    menu that doesn't call declared_verbs() passes every static check and fails here."""
    dev = MenuDevice(verbs={
        "inspect": lambda env: {"ok": True},
        "reload": lambda env: {"ok": True},
    })
    bus = _fresh_bus()
    loop = _rig(bus, MenuShim("menu_a", dev, bus=bus))
    loop.beat(NOW)  # first pulse wires delivery + announces menu
    feed = bus.read(to="menu_a", channel="announce")
    menu_posts = [e for e in feed if e.get("body", {}).get("verbs") is not None]
    assert len(menu_posts) >= 1, f"no menu on announce channel, feed has {len(feed)} entries"
    verbs = menu_posts[-1]["body"]["verbs"]
    assert sorted(verbs) == ["inspect", "reload"], verbs


def test_empty_menu_is_published():
    """A device with no verbs publishes an empty menu — honest, not silent."""
    dev = EmptyDevice()
    bus = _fresh_bus()
    loop = _rig(bus, EmptyShim("menu_b", dev, bus=bus))
    loop.beat(NOW)
    feed = bus.read(to="menu_b", channel="announce")
    menu_posts = [e for e in feed if e.get("body", {}).get("verbs") is not None]
    assert len(menu_posts) >= 1, f"no menu on announce channel"
    assert menu_posts[-1]["body"]["verbs"] == []


def test_menu_is_on_the_announce_channel():
    """The menu lives on the bus's announce channel — inspecting a device is reading its
    feed. A menu that lives on a side surface passes the content checks and fails here."""
    dev = MenuDevice(verbs={"ping": lambda env: {"pong": True}})
    bus = _fresh_bus()
    loop = _rig(bus, MenuShim("menu_c", dev, bus=bus))
    loop.beat(NOW)
    announce = bus.read(to="menu_c", channel="announce")
    personal = bus.read(to="menu_c", channel="personal")
    assert any(e.get("body", {}).get("verbs") is not None for e in announce), \
        "menu not on announce channel"
    assert not any(e.get("body", {}).get("verbs") is not None for e in personal), \
        "menu should not be on personal channel"


def test_menu_does_not_trigger_delivery():
    """The announce menu is a RECORD, not a deliverable message. A menu published on
    the personal channel would trigger delivery and land in the device's deliver() —
    which would try to dispatch on a verb and either bounce or error."""
    dev = MenuDevice(verbs={"test": lambda env: {"ok": True}})
    bus = _fresh_bus()
    shim = MenuShim("menu_d", dev, bus=bus)
    loop = _rig(bus, shim)
    loop.beat(NOW)
    assert bus.undelivered(to="menu_d") == [], \
        "announce post should not appear as undelivered"


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
    print("green — the announce menu is compiled, published, and does not interfere")
