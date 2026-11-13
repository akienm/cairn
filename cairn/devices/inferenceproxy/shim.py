"""inferenceproxy/shim.py — the inference domain's always-on front on the heartbeat.

Two probes address the inference domain with findings about its own behavior. This shim
is what makes that delivery path whole.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim


class InferenceDomainShim(BaseShim):

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "inference"

    def _bare(self) -> dict:
        """A bare ``cairn inferenceproxy`` names both: the name it answers to (outline 11.4.2) and
        the folder its class stands in (11.4), which differ here (ticket f942a413f26d)."""
        return {"exit": 0, "text": f"device: {self.device_id}\nclass:  cairn/devices/inferenceproxy/",
                "data": None, "cached": None}

    def _start_device(self):
        from cairn.devices.inferenceproxy.device import InferenceDomainDevice
        return InferenceDomainDevice()
