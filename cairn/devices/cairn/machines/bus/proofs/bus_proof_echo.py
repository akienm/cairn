"""bus_proof_echo — a fixture shim the bus process hosts during test_one_bus_process.py.

Self-describing on purpose: if an envelope addressed to ``bus_proof_echo`` ever turns up in
the live bus table, it came from the one-bus proof (ticket 48519f4789b1) and is throwaway.

The device answers one verb, ``echo`` (a reply carrying the body back), and one view, ``pid``
— the process it is running in — which is how the proof tells a shim hosted IN the bus
process from a private one built in the caller's own process.
"""
from __future__ import annotations

import os

from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim, ONLINE

DEVICE_ID = "bus_proof_echo"


class BusProofEchoDevice(BaseDevice):
    def __init__(self, bus) -> None:
        super().__init__()
        self._bus = bus

    def intention(self) -> dict:
        return {"what": "the one-bus proof's echo fixture"}

    def state(self) -> dict:
        return {"pid": os.getpid()}

    def settings(self) -> dict:
        return {}

    def declared_verbs(self) -> dict:
        return {"echo": self._handle_echo}

    def declared_views(self) -> dict:
        return {"pid": lambda: {"pid": os.getpid()}}

    def _handle_echo(self, envelope: dict) -> dict:
        self._bus.post(
            sender=DEVICE_ID, to=envelope["sender"], channel="personal",
            why="bus proof echo reply", body={"echoed": envelope["body"], "pid": os.getpid()},
            reply_to=envelope["id"],
        )
        return {"ack": envelope["id"]}


class BusProofEchoShim(BaseShim):
    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return DEVICE_ID

    def _start_device(self):
        dev = BusProofEchoDevice(self._bus)
        self._presence = ONLINE
        return dev


REENTRANT_ID = "bus_proof_reentrant"
_ECHO_SPEC = "cairn.devices.cairn.machines.bus.proofs.bus_proof_echo:BusProofEchoShim"


class BusProofReentrantShim(BusProofEchoShim):
    """A hosted shim whose wiring reaches the bus — what codemother's commit handler does
    (``watch._bus`` → ``reach()``), measured 2026-10-03 deadlocking the bus: the wiring runs
    under the hold lock, and a reach over the socket waits on it from another thread for ever.
    Held, it asks the bus (through the client's public face) to hold the echo fixture too."""

    @property
    def device_id(self) -> str:
        return REENTRANT_ID

    def _wire_delivery(self):
        result = super()._wire_delivery()
        from cairn.tools.bus_client.remote import RemoteBus
        RemoteBus().hold_shim(_ECHO_SPEC)
        return result
