"""cairn/device.py — the cairn system device.

The top-level device. Its machines (ground_loop, harbor_master, bus) are the
system's own infrastructure. BaseDevice.receive() records inbound mail to a
DataRecorder for later evaluation.
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice


class CairnDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "cairn"

    @property
    def device_id(self) -> str:
        return self._device_id

    def intention(self) -> dict:
        return {
            "what": "The cairn system device — top-level holder of ground_loop, "
                    "harbor_master, and bus.",
            "why": "Every device has a presence on the bus (Akien, 2026-08-11). "
                    "The system itself is a device and answers its own mail.",
        }

    def state(self) -> dict:
        return {}

    def settings(self) -> dict:
        return {}
