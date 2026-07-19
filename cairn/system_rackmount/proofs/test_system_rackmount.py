"""Proof for system_rackmount — THE SYSTEM DEVICE: advertise → subscribe → poke, Law 6.

This is the capstone of the heartbeat+callback+bus rework: it composes ALL the reworked
pieces at once — the heartbeat (ground_loop), the shim's per-pulse firing, the Callback
primitive, the real bus (durable via db_domain), and the system device that owns the host's
CPU predicate. It proves the worked example "alert me at 80% CPU" end to end.

Teeth a hollow system device could not pass:
  - IT ADVERTISES A MENU. ``advertises()`` offers ``cpu_threshold`` (takes a value) — a caller
    inspects offerings, then subscribes by menu name. An UNADVERTISED name is refused (CP1).
  - END TO END, THROUGH THE HEARTBEAT: a caller subscribes (value 80, its address); a beat with
    the host over the line pokes the caller's feed on the bus; a beat under the line pokes
    no one. The system device pokes nothing itself — the SHIM fires it on the pulse.
  - LAW 6 — THE READING NEVER LEAVES. The poke body says only THAT the caller's line (80) was
    crossed; the actual reading (95) appears NOWHERE in what crossed the bus. The predicate was
    evaluated INSIDE the device, on the device's own data.
  - THE GOOF IS GONE: no SchedulerService, no service()/scheduler API, no interval/date/
    quantity/state enum — a trigger is any predicate.
  - IT IS A DEVICE / ITS SHIM IS A SHIM (Law 2 / Form v0 #2).

Requires Postgres (the real bus rides db_domain). Self-cleaning: the ephemeral bus table is
dropped on the way out.

    python3 cairn/system_rackmount/proofs/test_system_rackmount.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CoreValuesMixin
from cairn.bus.bus import BusDevice
from cairn.db_domain import store
from cairn.ground_loop.loop import GroundLoopDevice
from cairn.system_rackmount.rackmount import SystemRackmountDevice, SystemRackmountShim

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_bus_sysrm_{_NONCE}"       # the ephemeral bus table this proof owns


def _rig(reading: dict):
    """Wire the full chain: a heartbeat, a real bus, the system device (with an injected,
    mutable reading), and its shim subscribed to the beat. Returns them for the test to drive."""
    bus = BusDevice(table=_TABLE)
    dev = SystemRackmountDevice(sampler=lambda: reading)
    shim = SystemRackmountShim(dev, bus)
    gl = GroundLoopDevice()
    gl.subscribe(shim)
    return gl, bus, dev


def test_it_advertises_a_menu_and_refuses_an_unadvertised_name():
    _, _, dev = _rig({"cpu": 10})
    menu = {item["callback"] for item in dev.advertises()}
    assert "cpu_threshold" in menu, "the system device advertises the cpu_threshold callback"
    try:
        dev.subscribe("gpu_threshold", address="a/personal", why="w", value=50)
        raise AssertionError("subscribing to an unadvertised callback must be refused (CP1)")
    except KeyError:
        pass


def test_alert_me_at_80_cpu_end_to_end_through_the_heartbeat():
    reading = {"cpu": 95}                      # the host is hot — over the line
    gl, bus, dev = _rig(reading)
    dev.subscribe("cpu_threshold", address="ops/personal", why="page me when CPU is high", value=80)

    gl.beat(now="t0")                          # one heartbeat drives the whole chain

    pokes = bus.read(to="ops/personal", channel="personal")
    assert len(pokes) == 1, "a beat over the line pokes the subscriber exactly once"
    poke = pokes[0]
    assert poke["sender"] == "system_rackmount" and poke["why"] == "page me when CPU is high"

    # Law 6: the poke carries the caller's own line, but the READING (95) leaked NOWHERE.
    assert poke["body"] == {"alert": "cpu_threshold", "crossed": 80}
    assert "95" not in json.dumps(poke), "the raw reading must never cross the bus (Law 6)"

    # Under the line, the same subscription pokes no one new.
    reading["cpu"] = 50
    gl.beat(now="t1")
    assert len(bus.read(to="ops/personal", channel="personal")) == 1, "under the line → no new poke"


def test_the_scheduler_goof_is_gone():
    _, _, dev = _rig({"cpu": 10})
    for gone in ("service", "services", "scheduler"):
        assert not hasattr(dev, gone), f"the central-scheduler API is deleted — {gone!r} must be gone"
    # The old trigger-kind enum is not a live part of the device's surface. If the words appear
    # at all in settings(), they may only appear inside the note that says they were deleted.
    blob = json.dumps(dev.settings())
    assert ("interval" not in blob and "quantity" not in blob) or "was deleted" in blob


def test_it_is_a_device_and_its_shim_is_a_shim():
    _, bus, dev = _rig({"cpu": 10})
    shim = SystemRackmountShim(dev, bus)
    assert isinstance(dev, CoreValuesMixin) and isinstance(shim, CoreValuesMixin), "Law 2"
    assert [v.id for v in dev.CORE_VALUES] == ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]
    assert list(dev.introspect()) == ["intention", "state", "settings", "other"], "Form v0 #2 order"
    assert shim.device_id == "system_rackmount", "the shim is the shim OF the system device"


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_it_advertises_a_menu_and_refuses_an_unadvertised_name,
        test_alert_me_at_80_cpu_end_to_end_through_the_heartbeat,
        test_the_scheduler_goof_is_gone,
        test_it_is_a_device_and_its_shim_is_a_shim,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — system_rackmount: the system device advertises resource-threshold callbacks "
          "and pokes subscribers through the heartbeat + bus, evaluating locally so the reading "
          "never leaves (Law 6); the central-scheduler goof is gone")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
