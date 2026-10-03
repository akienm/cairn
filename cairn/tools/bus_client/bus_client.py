"""bus_client — the standard contract: get a working bus without cross-device imports.

The device isolation ruling (2026-08-31) says no device may import another device
(db_domain is the sole exception). The bus lives in the cairn device tree; this
tool provides it to any device that needs a bus connection.

A device's shim.py on disk IS its bus declaration — no registry, no boolean flags.
``connect_bus(devices=["inference_domain"])`` discovers the shim from
``cairn/devices/inference_domain/shim.py`` and holds it in a ``DeviceRoster``
(``roster.py``) — no ground loop is built inside a client (ticket efb670ff1dd8).

Since ticket 48519f4789b1: one bus process per instance hosts every shim, and this tool
hands callers a ``RemoteBus`` (``remote.py``) speaking to it. The wiring lives here rather
than in each caller — the one seam that changed when the process model advanced.
"""
from __future__ import annotations

import importlib
from pathlib import Path

# Class-space root, derived from this file's own address (cairn/tools/bus_client/bus_client.py →
# three parents up). Never configured: a tool is discovered-from where it is installed, the
# same rule ``cairn.tools.rack.rack.repo_root`` states for the rack.
_CLASS_ROOT = Path(__file__).resolve().parents[3]


def _wire(*, devices: list[str] | None = None, beat: bool = True):
    """Internal: the instance's one bus process (started if it is not answering), a
    ``RemoteBus`` speaking to it, and a ``DeviceRoster`` over that remote. Returns
    ``(bus, roster)``.

    ONE BUS PER INSTANCE (ticket 48519f4789b1 decision 7). Until then this built a private
    ``BusDevice`` and held private shims in the caller's own process — two commands were two
    rings. Now the named devices are HELD IN THE BUS PROCESS, where holding wires each one's
    delivery onto the one ring (decision 12 — wired, never pulsed); nothing is held here. ``beat`` is kept for the
    callers' signature: a hold in the bus process is the only wiring there is, so a client
    that names devices gets them wired either way, and one that names none touches no shim."""
    from cairn.tools.bus_client.remote import RemoteBus, ensure_bus
    from cairn.tools.bus_client.roster import DeviceRoster

    ensure_bus()
    bus = RemoteBus()
    if devices:
        bus.hold(*devices)
    return bus, DeviceRoster(bus)


def connect_bus(*, devices: list[str] | None = None, beat: bool = True):
    """Return a bus handle (a ``RemoteBus`` on the instance's one bus process) with the named
    devices held in that process.

    devices: device names whose shims should handle bus verbs. Each is loaded IN THE BUS
             PROCESS from ``<device folder>/shim.py`` — a file that declares a BaseShim
             subclass is its own registration — or, for a fitted device with no shim.py, a
             DiscoveredShim. A name no shim answers to raises LookupError.
    beat:    kept for the signature; see ``_wire``. A CLIENT that wants to ASK a device one
             question calls ``reach(<device>)``; the probe at
             ``probes/a_client_reaches_and_never_beats.py`` reds any Call of this face outside
             the runner roster.
    """
    bus, _roster = _wire(devices=devices, beat=beat)
    return bus


def reach(*devices: str):
    """A bus that can ASK the named devices — each held (and so wired) in the bus process,
    with no beat: a client asks a question, it never pays for the system's heartbeat
    (ticket fc93d8cd5961). Named with no devices it is the bus alone, for reading and posting.

    Raises LookupError for a name no shim answers to. Use ``connect_bus``/``connect_system``
    when you mean to run the system; use this when you mean to ask.
    """
    bus, _roster = _wire(devices=list(devices), beat=False)
    return bus


def connect_system(*, devices: list[str] | None = None, beat: bool = True):
    """Return ``(bus, roster)`` — for process entry points that run the system.

    The roster is a ``DeviceRoster`` over the remote bus: the web server's nav (every fitted
    device on disk) and the source of each device's shim for rendering (``shim_for``). The
    bus's own shim lives in the bus process, never here. Most callers want only the bus.
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
    """The dotted module path of the ``shim.py`` that answers mail to ``device_name`` —
    ``cairn.tools.rack.rack.shim_of``: the device's own ``cairn/devices/<name>/shim.py``,
    else a held machine's ``cairn/devices/<d>/machines/<name>/shim.py``.

    THE MEASUREMENT THAT BORE IT (2026-09-09, ticket 8754ae677af6): ``reach("harbor_master")``
    raised ``LookupError`` because this loader spelled the address
    ``cairn.devices.<name>.shim``, and ``harbor_master`` is a machine held by the ``cairn``
    device, its shim at ``cairn/devices/cairn/machines/harbor_master/shim.py``. Probes posting
    ``to="harbor_master"`` landed in a mailbox and its ``crossing`` verb was unreachable.

    The mail address is NOT the roster (ticket a808e21d646f): a held machine is not a rack
    device, yet 83 probes post to it (measured 2026-10-03), so the address book is wider than
    the rack on purpose and narrowing the roster must not cut a delivery address.
    """
    from cairn.tools.rack.rack import shim_of

    shim_file = shim_of(device_name, _CLASS_ROOT)
    if shim_file is None:
        return None
    return ".".join(shim_file.relative_to(_CLASS_ROOT).with_suffix("").parts)


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
