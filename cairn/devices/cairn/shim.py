"""cairn/shim.py — the cairn system device's always-on front on the heartbeat.

The cairn device receives system-level feedback (operator_inbox accuracy, etc.).
This shim wakes the device on first delivery.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim


class CairnShim(BaseShim):

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "cairn"

    def on_pulse(self, now, context: dict | None = None) -> dict:
        """Seed the pulse context with this shim's bus, then pulse as usual.

        A probe berthed under this device may need to ASK another device something — the
        trouble pane's watch is the first that does (ticket 9579a6f9cec6) — and a probe
        carries no authority (Law 6), so it must not dial a bus of its own. Doing that from
        inside a pulse would also fire a ground-loop beat from inside a ground-loop beat.
        The shim is the one thing that knows both its device and its bus, which is the same
        answer BaseShim has given every routing question since 2026-08-04, so the bus rides
        down in the context the probes already receive.

        ``setdefault``, not assignment: a caller that handed a bus in deliberately — a
        proof pointing the pane at a stand-in — keeps the one it chose."""
        context = context if context is not None else {}
        if self._bus is not None:
            context.setdefault("bus", self._bus)
        return super().on_pulse(now, context)

    def _start_device(self):
        from cairn.devices.cairn.device import CairnDevice
        # The bus rides in: the cairn device asks the trouble lane for its pane over the
        # bus now instead of importing it (ticket 9579a6f9cec6), and the shim is the one
        # thing that knows both the device and the bus.
        return CairnDevice(bus=self._bus)
