"""scratch_bus — the cairn device's published fixture bus: a proof's bus of its own.

A proof that needs a bus with a real store under it (posts that persist, ``undelivered``
that reads the store, a ring that ``flush`` empties) and with nobody live listening asks for
one here. Outside the cairn device this is the ONE way to reach the bus machine's code (RULE 1;
outline 17.13.1: code in device bar may import cairn.devices.foo only through a tool foo
publishes). Measured 2026-11-11: five proofs in codemother and tester imported
``cairn.devices.cairn.machines.bus.bus`` and ``.shim`` directly for exactly these two things,
and the encapsulation_holds sieve redded all seven sites.

    from cairn.devices.cairn.tools.scratch_bus import scratch_bus
    with scratch_bus.scratch_bus("my_proof") as bus:
        roster.hold(scratch_bus.bus_shim(bus, roster))

``launch(device, env)`` is the other shape (ticket 0c2c3f53c2be): a bus PROCESS under a scratch
HOME, holding a device by name with an environment the caller names, so a proof asks a real
device over the bus without holding its shim in its own process.

Beside it, nothing here is new behaviour: ``scratch_bus`` is ``BusDevice.scratch`` (the transit table and
its companion drop on exit, or on the tester's next sweep if the process is killed), and
``bus_shim`` is the ``BusShim`` constructor. The tool holds no state of its own (Law 6).
"""
from __future__ import annotations

from contextlib import contextmanager


@contextmanager
def scratch_bus(prefix: str = "bus_traffic", device_id: str = "bus"):
    """A bus over a scratch transit table that cannot outlive this process."""
    from cairn.devices.cairn.machines.bus.bus import BusDevice
    with BusDevice.scratch(prefix, device_id=device_id) as bus:
        yield bus


@contextmanager
def launch(device: str, env: dict | None = None, *, prefix: str = "launch"):
    """A bus PROCESS under a scratch HOME, holding ``device`` by name, for the block (ticket
    0c2c3f53c2be, D2). It yields the RemoteBus and shuts the bus down at exit.

    The bus process wakes ``device`` the way the rack does: through its roster, from that
    device's own ``shim.py`` (RemoteBus.hold), so the asking process never imports it (RULE 1).
    Its environment is ``home_env(<scratch HOME>, CAIRN_BUS_HOME=<its address>, **env)``: no
    caller's bus address survives, and ``env`` is how a caller names the launched device's world
    (inspect_wire.launch sets the inspector's roots this way). A HOME other than the live one
    rides a throwaway table (bus_client.ensure_bus), so a launched device drains no live mail."""
    from cairn.tools.bus_client.remote import RemoteBus
    from cairn.tools.scratch.scratch import home_env, scratch_dir
    home = scratch_dir(f"{prefix}-{device}-")
    # The address is a short scratch directory of its own, not a path under HOME. Linux caps
    # an AF_UNIX path at 108 bytes, and <HOME>/.cairn/devices/cairn/machines/bus/0/bus.sock
    # under the scratch HOME inspect_wire.launch names ran past it (measured 2026-11-14:
    # "OSError: AF_UNIX path too long", 7 of 8 teeth red in its Linux seal; Windows dials TCP
    # and never showed it). scratch_dir sweeps it at exit like the HOME.
    address = scratch_dir("bus-")
    bus = RemoteBus(address, scratch=True,
                    env=home_env(home, CAIRN_BUS_HOME=str(address), **(env or {})))
    try:
        bus.hold(device)
        yield bus
    finally:
        try:
            bus.shutdown()
        except OSError:
            pass


def bus_shim(bus, heartbeat=None):
    """The bus's own shim over ``bus`` — what a roster holds to drain and deliver."""
    from cairn.devices.cairn.machines.bus.shim import BusShim
    return BusShim(bus, heartbeat)
