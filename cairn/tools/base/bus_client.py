"""bus_client — the standard contract: get a working bus without cross-device imports.

The device isolation ruling (2026-08-31) says no device may import another device
(db_domain is the sole exception). The bus lives in the cairn device tree; this
tool provides it to any device that needs a bus connection.

A device's shim.py on disk IS its bus declaration — no registry, no boolean flags.
``connect_bus(devices=["inference_domain"])`` discovers the shim from
``cairn/devices/inference_domain/shim.py`` and registers it with the ground loop.

Today: in-process construction. The shape is already right for out-of-process
(IPC to the running ground loop), which is why the wiring lives here rather than
in each caller — one seam to change when the process model advances.
"""
from __future__ import annotations

import importlib


def _wire(*, devices: list[str] | None = None, beat: bool = True):
    """Internal: create bus + ground loop with discovery and named device shims."""
    from datetime import datetime, timezone

    from cairn.devices.cairn.machines.bus.bus import BusDevice
    from cairn.devices.cairn.machines.bus.shim import BusShim
    from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice
    from cairn.devices.cairn.machines.ground_loop.discovery import discover, pulse_sites

    bus = BusDevice()
    loop = GroundLoopDevice(bus=bus, discover=discover, pulse_finder=pulse_sites)
    loop.subscribe(BusShim(bus, loop))

    for name in (devices or []):
        shim = _load_device_shim(name, bus)
        if shim is not None:
            loop.subscribe(shim)

    if beat:
        loop.beat(datetime.now(timezone.utc))

    return bus, loop


def connect_bus(*, devices: list[str] | None = None, beat: bool = True):
    """Return a working BusDevice with named device shims registered.

    devices: device names whose concrete shims should handle bus verbs.
             Each is discovered from ``cairn/devices/<name>/shim.py`` —
             a file that declares a BaseShim subclass is its own registration.
    beat:    fire one ground-loop beat to initialize (wires delivery, runs
             discovery). Almost always True; False only for test fixtures
             that want to inspect the wiring before the first pulse.
    """
    bus, _loop = _wire(devices=devices, beat=beat)
    return bus


def connect_system(*, devices: list[str] | None = None, beat: bool = True):
    """Return ``(bus, loop)`` — for callers that need the ground loop itself.

    The web_server uses the loop as its roster source (the nav across the top
    shows which devices the heartbeat beats to). Most callers want only the bus;
    this variant is for process entry points that run the system.
    """
    return _wire(devices=devices, beat=beat)


def harbor_source():
    """The harbor's traffic_image function — loadable without a cross-device import.

    The web_server renders the harbor view from this; importing it here (a tool)
    rather than from the device keeps the web_server's isolation clean.
    """
    from cairn.devices.cairn.machines.harbor_master.voyage import traffic_image
    return traffic_image


def inference_seam():
    """The inference domain's resolve + resolver — for subprocess use without a bus.

    Returns ``(resolve_fn, ollama_resolver_factory)`` so the caller can build a
    resolver for its model and call resolve with it, without importing
    inference_domain directly (device isolation).
    """
    from cairn.devices.inference_domain import domain, host
    return domain.resolve, host.ollama_resolver


def _load_device_shim(device_name: str, bus):
    """Discover a device's concrete shim from ``cairn/devices/<name>/shim.py``.

    The file on disk IS the declaration — same physics as probes/ folders.
    Returns None when no shim module or no BaseShim subclass is found.
    """
    from cairn.tools.base.shim import BaseShim

    try:
        mod = importlib.import_module(f"cairn.devices.{device_name}.shim")
    except ImportError:
        return None

    for attr_name in sorted(dir(mod)):
        obj = getattr(mod, attr_name)
        if (isinstance(obj, type)
                and issubclass(obj, BaseShim)
                and obj is not BaseShim
                and not attr_name.startswith("_")):
            return obj(bus=bus)
    return None
