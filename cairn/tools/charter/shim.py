"""charter/shim.py — the charter tool's always-on front on the heartbeat.

Charter's probes post findings to "charter" on the bus. This shim wakes the
device on first delivery so findings are recorded.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim


class CharterShim(BaseShim):

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "charter"

    def _start_device(self):
        from cairn.tools.charter.device import CharterDevice
        return CharterDevice()
