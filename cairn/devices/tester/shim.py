"""tester/shim.py — the tester's always-on front on the heartbeat.

The tester runs proofs and attests verdicts. Its shim is thin: wake a TesterDevice on
first delivery, expose its page. No constructor-injected state — the device stands alone.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim


class TesterShim(BaseShim):

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "tester"

    def _start_device(self):
        from cairn.devices.tester.device import TesterDevice
        return TesterDevice()
