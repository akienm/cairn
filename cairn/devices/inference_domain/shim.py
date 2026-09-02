"""inference_domain/shim.py — the inference domain's always-on front on the heartbeat.

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
        return "inference_domain"

    def _start_device(self):
        from cairn.devices.inference_domain.device import InferenceDomainDevice
        return InferenceDomainDevice()
