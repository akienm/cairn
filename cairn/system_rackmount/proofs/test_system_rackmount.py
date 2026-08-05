"""Proof for system_rackmount — THE SYSTEM DEVICE: advertise → subscribe → poke, Law 6.

This is the capstone of the heartbeat+probe+bus rework: it composes ALL the reworked
pieces at once — the heartbeat (ground_loop), the shim's per-pulse firing, the Probe
primitive, the real bus (durable via db_domain), and the system device that owns the host's
CPU predicate. It proves the worked example "alert me at 80% CPU" end to end.

Teeth a hollow system device could not pass:
  - IT ADVERTISES A MENU. ``advertises()`` offers ``cpu_threshold`` (takes a value) — a caller
    inspects offerings, then subscribes by menu name. An UNADVERTISED name is refused (CP1).
  - TWO DOORS, ONE PREDICATE. ``ask`` answers the same menu item as ``subscribe``, and the two
    agree on every reading — flip the host and both flip together. A build that grew a second
    implementation for the pull door dies when they disagree.
  - THE ASK RETURNS A VERDICT, NOT A READING (Law 6). ``ask`` hands back a bool. The number it
    was derived from appears nowhere in what the caller receives.
  - THE FLOOR RUNS THE OTHER WAY. ``memory_floor`` is crossed when available memory falls
    BELOW the line — a build that reused the threshold comparator for both passes cpu and dies
    on memory.
  - THE HOST READING IS INSTANTANEOUS (the admission-control tooth). Load real work onto the
    box and the device's own CPU reading must reflect it within a second. The decaying load
    average this device served until 2026-08-04 needs ~60s to show the same event — measured —
    so an admission gate reading it lets every builder in. That sampler cannot pass this.
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
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CoreValuesMixin
from cairn.bus.bus import BusDevice
from cairn.db_domain import store
from cairn.ground_loop.loop import GroundLoopDevice
from cairn.system_rackmount.rackmount import (
    SystemRackmountDevice,
    SystemRackmountShim,
    _default_sampler,
)

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
    menu = {item["probe"] for item in dev.advertises()}
    assert "cpu_threshold" in menu, "the system device advertises the cpu_threshold probe"
    try:
        dev.subscribe("gpu_threshold", address="a/personal", why="w", value=50)
        raise AssertionError("subscribing to an unadvertised probe must be refused (CP1)")
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

    # Law 6: the poke carries the caller's own line (80), but the device's private READING (95)
    # leaked NOWHERE. Scope the leak-check to what the DEVICE authored — the bus assigns the
    # transport fields (a random uuid `id`, a timestamp `date`) a device never fills, and a random
    # 32-char hex id contains the substring "95" ~12% of the time. Scanning the whole envelope for
    # the reading was this proof's FLAKE: a red decided partly by a coin toss (Law 8), not a real
    # leak — the exact-body check above already proves the payload is clean.
    assert poke["body"] == {"alert": "cpu_threshold", "crossed": 80}
    authored = {k: v for k, v in poke.items() if k not in ("id", "date")}
    assert "95" not in json.dumps(authored), "the raw reading must never cross the bus (Law 6)"

    # Under the line, the same subscription pokes no one new.
    reading["cpu"] = 50
    gl.beat(now="t1")
    assert len(bus.read(to="ops/personal", channel="personal")) == 1, "under the line → no new poke"


def test_the_ask_door_answers_the_same_predicate_as_the_subscribe_door():
    # TWO DOORS, ONE PREDICATE. The pull door must not be a second implementation of the push
    # door — so drive the SAME device across the SAME readings and require they never disagree.
    reading = {"cpu": 10, "memory_available_mb": 8000}
    gl, bus, dev = _rig(reading)
    dev.subscribe("cpu_threshold", address="admission/personal", why="watch", value=80)

    assert dev.ask("cpu_threshold", 80) is False, "10% is under an 80% line"
    gl.beat(now="t0")
    assert bus.read(to="admission/personal", channel="personal") == [], "and the poke door agrees"

    reading["cpu"] = 95
    assert dev.ask("cpu_threshold", 80) is True, "95% crosses an 80% line"
    gl.beat(now="t1")
    assert len(bus.read(to="admission/personal", channel="personal")) == 1, "and the poke door agrees"

    # A VERDICT, NOT A READING (Law 6). Checked as the TYPE, not by scanning the value for the
    # reading's digits: `95 not in True` is true of every possible bool, and a check that cannot
    # fail proves nothing. What is actually claimed is that the door's return type carries no
    # room for a number — so that is what is asserted.
    verdict = dev.ask("cpu_threshold", 80)
    assert type(verdict) is bool, "the ask door hands back a verdict; a number has no way out"

    # And the ask door is the same menu — an unadvertised name is refused there too (CP1).
    try:
        dev.ask("gpu_threshold", 50)
        raise AssertionError("asking an unadvertised probe must be refused (CP1)")
    except KeyError:
        pass


def test_the_memory_floor_runs_the_other_direction():
    # A floor is crossed by falling BELOW it. A build that reused the threshold comparator for
    # every metric passes every cpu tooth in this file and dies right here.
    reading = {"cpu": 5, "memory_available_mb": 8000}
    _, _, dev = _rig(reading)
    assert dev.ask("memory_floor", 1024) is False, "8 GB available is comfortably above a 1 GB floor"
    reading["memory_available_mb"] = 512
    assert dev.ask("memory_floor", 1024) is True, "512 MB available is BELOW a 1 GB floor — crossed"
    # An unavailable metric never manufactures a crossing, in either direction (CP1).
    reading["memory_available_mb"] = None
    assert dev.ask("memory_floor", 1024) is False, "an unknown reading is honestly not-crossed"


def test_the_real_host_reading_is_instantaneous():
    # THE ADMISSION-CONTROL TOOTH, and the reason the sampler changed. The gate must see a
    # launch before the NEXT asker arrives, so load the box for real and require the device's
    # own reading to move within a second.
    #
    # Measured 2026-08-04 on this 8-core box with these same 4 burners: the runnable count went
    # 2 -> 6 within one second, while the 1-minute load average — what this device served until
    # today — went 5.5% -> 9.1% and was still reading 15.4% twelve seconds in. The threshold
    # below is set so that the instantaneous field clears it easily and the decaying one cannot
    # clear it at all: this test IS the falsifier for the sampler that was replaced.
    cores = os.cpu_count() or 1
    burners = max(2, min(4, cores))
    expected_rise = burners / cores * 100

    base = _default_sampler()
    if base["cpu"] is None:
        print("     SKIP  no /proc/loadavg on this host — the reading is honestly unavailable")
        return

    procs = [
        subprocess.Popen([sys.executable, "-c", "while True: pass"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(burners)
    ]
    try:
        time.sleep(1.0)                      # one second — the whole point of the tooth
        loaded = _default_sampler()
    finally:
        for p in procs:
            p.kill()
        for p in procs:
            p.wait()

    rise = loaded["cpu"] - base["cpu"]
    assert rise >= expected_rise / 2, (
        f"the device's CPU reading rose only {rise:.1f} points one second after {burners} "
        f"real burners started (expected ~{expected_rise:.1f}). A reading that lags this far "
        f"behind the box lets every builder in — the gate would be blind exactly when it "
        f"matters (Law 3: this is measured, not asserted)"
    )

    # Memory comes from the same door and must be the live figure, not a cached or nominal one.
    mem = base["memory_available_mb"]
    if mem is not None:
        with open("/proc/meminfo") as fh:
            truth = next(int(l.split()[1]) / 1024 for l in fh if l.startswith("MemAvailable:"))
        assert abs(mem - truth) / truth < 0.2, "the memory reading must be the host's live figure"


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
        test_the_ask_door_answers_the_same_predicate_as_the_subscribe_door,
        test_the_memory_floor_runs_the_other_direction,
        test_the_real_host_reading_is_instantaneous,
        test_the_scheduler_goof_is_gone,
        test_it_is_a_device_and_its_shim_is_a_shim,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — system_rackmount: the system device advertises resource-threshold probes "
          "and pokes subscribers through the heartbeat + bus, evaluating locally so the reading "
          "never leaves (Law 6); the central-scheduler goof is gone")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
