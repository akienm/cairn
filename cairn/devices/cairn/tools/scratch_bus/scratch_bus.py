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

Nothing here is new behaviour: ``scratch_bus`` is ``BusDevice.scratch`` (the transit table and
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


def bus_shim(bus, heartbeat=None):
    """The bus's own shim over ``bus`` — what a roster holds to drain and deliver."""
    from cairn.devices.cairn.machines.bus.shim import BusShim
    return BusShim(bus, heartbeat)
