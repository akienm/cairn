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
from pathlib import Path

# Class-space root, derived from this file's own address (cairn/tools/bus_client/bus_client.py →
# three parents up). Never configured: a tool is discovered-from where it is installed, the
# same rule ``discovery.repo_root`` states for the ground loop.
_CLASS_ROOT = Path(__file__).resolve().parents[3]


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
             discovery). True when you mean to RUN the system — the beat is
             the heartbeat, and on this machine it costs ~23.5s (measured
             2026-09-09). A CLIENT that wants to ASK a device one question
             does not call this at all: it calls ``reach(<device>)`` below,
             which wires and pulses only the shims addressed (~0.23s). Five
             clients paid the beat before that was enforced; the probe at
             ``probes/a_client_reaches_and_never_beats.py`` now reds any Call
             of this face outside the runner roster. False is for a fixture
             that inspects the wiring before the first pulse.
    """
    bus, _loop = _wire(devices=devices, beat=beat)
    return bus


def reach(*devices: str):
    """A bus that can ASK the named devices — one exchange, no heartbeat.

    THE MEASUREMENT THAT BORE IT (2026-09-07, ticket 9579a6f9cec6): a ground-loop beat on this
    machine costs **104.8s** — trigger 57.5s, carry 24.0s, enough 22.6s, and 0.7s for
    everything the loop itself does (poke, reconcile, shim bookkeeping). Not the bus and not
    the DB: ``bus.read`` is 80ms and discovery is 0.3s. It is the pulse, and subscribing NO
    devices at all still pays all of it, because 78 probes re-derive their whole survey on
    every beat and a probe that fires pays for its survey three times over (trigger, carry,
    enough). That is a real defect and it is not this ticket's; what matters here is that
    ``connect_bus`` pays it, and a caller that wants one question answered should not.

    A FIRST WRITING OF THIS PARAGRAPH SAID "over nine minutes" AND BLAMED
    ``probes/hand_spelled_instance_paths.py`` for AST-parsing class-space every beat. Both
    halves were wrong and the correction is left standing here rather than quietly swapped:
    that scan is 1.17s over 457 files, 2% of the beat. The real cost was
    ``no_component_reaches_proved_with_an_uncharted_build`` at 55.6s, asking the chart chain
    of all 196 PROVED tickets while ``claiming_packets`` re-parsed all 2,552 berthed packets
    per call — 1,568 sweeps of the store per beat. Indexed 2026-09-07
    (``tools/chain/chain.py``, proof ``test_packet_index.py``); that probe now costs ~1.4s.
    THE LESSON IS THE ONE LAW 3 KEEPS TEACHING: the first plausible culprit was named from
    reading, and the census that measured it named a different one.

    WHAT THE BEAT WAS ACTUALLY FOR, from the caller's side, is one line:
    ``BaseShim._wire_delivery`` hands the bus a poke channel for its device, and until some
    pulse does that, ``request`` posts into silence and times out. So this pulses exactly the
    shims being addressed — which wires their delivery, fires their own probes, and touches
    nothing else. That is not a shortcut around the heartbeat; it is the difference between
    RUNNING the system and USING it. A build inspector reconciling its troubles is a client,
    and a client that had to start everything in order to ask one question would make the
    ask cost more than the work.

    Use ``connect_bus``/``connect_system`` when you mean to run the system (the web server's
    listener does, and wants the roster a real beat produces). Use this when you mean to ask.
    """
    from datetime import datetime, timezone

    bus, loop = _wire(devices=list(devices), beat=False)
    now = datetime.now(timezone.utc)
    for name in devices:
        shim = loop.shim_for(name)
        if shim is None:
            raise LookupError(
                f"no shim answers to {name!r} — a device's bus presence IS "
                f"cairn/devices/{name}/shim.py on disk, and nothing was discovered there")
        shim.on_pulse(now)
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


def _device_shim_module(device_name: str) -> str | None:
    """The dotted module path of ``<device folder>/shim.py``, found the way DISCOVERY
    finds a device — by walking class-space, not by assuming a shape.

    THE MEASUREMENT THAT BORE IT (2026-09-09, ticket 8754ae677af6): ``reach("harbor_master")``
    raised ``LookupError``, and the reason was that this loader spelled the address
    ``cairn.devices.<name>.shim`` while ``discovery.device_folders`` derives a device_id from
    the parent of ANY ``probes/`` folder at ANY depth. The two disagreed about exactly one
    device and it was the harbor: ``harbor_master`` is a machine held by the ``cairn`` device,
    so its shim sits at ``cairn/devices/cairn/machines/harbor_master/shim.py``. Discovery saw
    a device there; this loader could not, so the concrete ``HarborMasterShim`` had zero
    callers and the harbor was fronted on every beat by a generic ``DiscoveredShim`` whose
    ``_FeedbackDevice`` declares no verbs. Thirteen probes posting ``to="harbor_master"`` were
    landing in a mailbox, and the device's own ``crossing`` verb was unreachable over the bus.

    So the rule is discovery's rule, stated once here too: **the folder that holds the
    device's ``probes/`` is the folder that holds its ``shim.py``**, wherever that folder
    sits. The common case still resolves without touching disk — the walk is the fallback,
    not the path.
    """
    common = f"cairn.devices.{device_name}.shim"
    if (_CLASS_ROOT / "cairn" / "devices" / device_name / "shim.py").is_file():
        return common
    from cairn.devices.cairn.machines.ground_loop import discovery

    for device_id, folder in discovery.device_folders(_CLASS_ROOT):
        if device_id != device_name:
            continue
        shim_file = folder.parent / "shim.py"
        if shim_file.is_file():
            rel = shim_file.relative_to(_CLASS_ROOT).with_suffix("")
            return ".".join(rel.parts)
    return None


def _load_device_shim(device_name: str, bus):
    """Discover a device's concrete shim from ``<device folder>/shim.py``.

    The file on disk IS the declaration — same physics as probes/ folders, and the
    folder is found the same way (see ``_device_shim_module``).
    Returns None when no shim module or no BaseShim subclass is found.
    """
    from cairn.tools.base.shim import BaseShim

    module_path = _device_shim_module(device_name)
    if module_path is None:
        return None
    try:
        mod = importlib.import_module(module_path)
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
