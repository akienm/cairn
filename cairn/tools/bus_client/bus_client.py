"""bus_client — the standard contract: get a working bus without cross-device imports.

The device isolation ruling (2026-08-31) says no device may import another device
(db_domain is the sole exception). The bus lives in the cairn device tree; this
tool provides it to any device that needs a bus connection.

A device's shim.py on disk IS its bus declaration — no registry, no boolean flags.
``connect_bus(devices=["inference_domain"])`` discovers the shim from
``cairn/devices/inference_domain/shim.py`` and holds it in a ``DeviceRoster``
(``roster.py``) — no ground loop is built inside a client (ticket efb670ff1dd8).

Today: in-process construction. The wiring lives here rather than in each caller —
one seam to change when the process model advances.
"""
from __future__ import annotations

import importlib
from pathlib import Path

# Class-space root, derived from this file's own address (cairn/tools/bus_client/bus_client.py →
# three parents up). Never configured: a tool is discovered-from where it is installed, the
# same rule ``discovery.repo_root`` states for the ground loop.
_CLASS_ROOT = Path(__file__).resolve().parents[3]


def _wire(*, devices: list[str] | None = None, beat: bool = True):
    """Internal: a bus, a DeviceRoster holding the bus's own shim and each named device's
    shim, and — with ``beat`` — one pulse of those held shims. Returns ``(bus, roster)``.

    No ground loop is built here (ticket efb670ff1dd8): the heartbeat is the resident one,
    and no device is special-cased — ``ground_loop`` loads its own shim from disk like any
    other name."""
    from datetime import datetime, timezone

    from cairn.devices.cairn.machines.bus.bus import BusDevice
    from cairn.devices.cairn.machines.bus.shim import BusShim
    from cairn.tools.bus_client.roster import DeviceRoster

    bus = BusDevice()
    roster = DeviceRoster(bus)
    roster.hold(BusShim(bus, roster))

    for name in (devices or []):
        shim = roster.shim_for(name)
        if shim is not None:
            roster.hold(shim)

    if beat:
        roster.pulse(datetime.now(timezone.utc))

    return bus, roster


def connect_bus(*, devices: list[str] | None = None, beat: bool = True):
    """Return a working BusDevice with named device shims held.

    devices: device names whose shims should handle bus verbs. Each is loaded from
             ``<device folder>/shim.py`` — a file that declares a BaseShim subclass is its
             own registration — or, for a fitted device with no shim.py, a DiscoveredShim.
    beat:    pulse the held shims once (the bus's own shim first, then each named one),
             which wires their delivery. True when you mean to RUN the system. A CLIENT
             that wants to ASK a device one question calls ``reach(<device>)`` instead; the
             probe at ``probes/a_client_reaches_and_never_beats.py`` reds any Call of this
             face outside the runner roster. False is for a fixture that inspects the
             wiring before the first pulse.
    """
    bus, _roster = _wire(devices=devices, beat=beat)
    return bus


def reach(*devices: str):
    """A bus that can ASK the named devices — one exchange, no heartbeat.

    ``BaseShim._wire_delivery`` hands the bus a poke channel for its device, and until some
    pulse does that, ``request`` posts into silence and times out. So this pulses exactly the
    shims being addressed — which wires their delivery, fires their own probes, and touches
    nothing else. That is the difference between RUNNING the system and USING it.

    Raises LookupError for a name no shim answers to. Use ``connect_bus``/``connect_system``
    when you mean to run the system; use this when you mean to ask.
    """
    from datetime import datetime, timezone

    bus, roster = _wire(devices=list(devices), beat=False)
    now = datetime.now(timezone.utc)
    for name in devices:
        shim = roster.shim_for(name)
        if shim is None:
            raise LookupError(
                f"no shim answers to {name!r} — a device's bus presence IS "
                f"cairn/devices/{name}/shim.py on disk, and nothing was discovered there")
        shim.on_pulse(now)
    return bus


def connect_system(*, devices: list[str] | None = None, beat: bool = True):
    """Return ``(bus, roster)`` — for process entry points that run the system.

    The roster is a ``DeviceRoster``: the web server's nav (every fitted device on disk) and
    the source of each device's shim (``shim_for``). Most callers want only the bus.
    """
    return _wire(devices=devices, beat=beat)


def harbor_source():
    """The harbor's traffic_image function — loadable without a cross-device import.

    The web_server renders the harbor view from this; importing it here (a tool)
    rather than from the device keeps the web_server's isolation clean.
    """
    from cairn.devices.cairn.machines.harbor_master.voyage import traffic_image
    return traffic_image


def inference_bus():
    """A bus that can ask inference_domain — for subprocess use without a bus of its own.

    Until 2026-09-18 this tool held ``inference_seam()``: a direct import of
    ``cairn.devices.inference_domain`` handing back ``domain.resolve`` and the host's
    resolver factory, so a consumer with no bus (aider's venv subprocess) could call the
    domain in-process "without importing inference_domain directly". That kept the
    IMPORT out of the consumer and left the CALL off the bus — the half ticket
    87a7f1c7ae21 is written against ("every inference call routes through bus.request()
    or bus.post()"). A tool holding the door is still a path around it. Now the answer
    is the same one every device gets: a ``reach`` bus with inference_domain's shim
    pulsed, and the consumer asks ``resolve`` / ``get`` over it. Nothing here imports
    the device; measured 2026-09-18, a reach bus answers ``get``/``what=models`` in ~3s
    in-process, no DB, no host.
    """
    return reach("inference_domain")


def models_stack() -> dict:
    """inference_domain's parsed models stack — for subprocess use without a bus.

    The twin of :func:`inference_bus`, and it rides it: ``get`` / ``what=models`` on
    inference_domain, the same door a consumer WITH a bus uses (aider_shim's
    ``_stack``). A consumer (aider_shim, ticket 50ad391f4e95) never reaches into
    inference_domain's tree for ``stacks/models.json``, and since 87a7f1c7ae21 neither
    does this tool.
    """
    reply = inference_bus().request(
        sender="bus_client", to="inference_domain", verb="get",
        why="the models stack, asked of its owner over the bus",
        body={"what": "models"},
    )
    return reply["body"]["data"]


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
