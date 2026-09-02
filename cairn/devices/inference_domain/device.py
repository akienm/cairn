"""inference_domain/device.py — the inference domain as a device.

The inference domain's machinery (domain.py, host.py, route.py) predates its device
class. This wraps the module behind a BaseDevice face so the domain can be addressed
on the bus — two probes send findings here. BaseDevice.receive() records inbound
mail to a DataRecorder for later evaluation.
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice


class InferenceDomainDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "inference_domain"

    @property
    def device_id(self) -> str:
        return self._device_id

    def intention(self) -> dict:
        return {
            "what": "The one path to the inference host, and the compile-once gate.",
            "why": "A resource with exactly one owner, reached only through the "
                    "owner's gate (Law 6 + Law 4). The cache is the point: an answered "
                    "question becomes structure (Law 1).",
        }

    def state(self) -> dict:
        return {}

    def settings(self) -> dict:
        return {}
