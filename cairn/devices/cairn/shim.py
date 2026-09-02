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

    def _start_device(self):
        from cairn.devices.cairn.device import CairnDevice
        return CairnDevice()
