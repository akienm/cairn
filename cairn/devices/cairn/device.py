"""cairn/device.py — the cairn system device.

The top-level device. Its machines (ground_loop, harbor_master, bus) are the
system's own infrastructure. BaseDevice.receive() records inbound mail to a
DataRecorder for later evaluation.
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice
from cairn.devices.trouble.trouble import TroubleDevice


class CairnDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "cairn"
        self._trouble = TroubleDevice()

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

    def declared_panes(self) -> list[dict]:
        return [
            {
                "kind": "trouble",
                "label": "troubles",
                "handler": self._trouble_pane_data,
            },
        ]

    def _trouble_pane_data(self) -> list[dict]:
        return [
            {
                "id": t.get("id", "?"),
                "standing": t.get("standing", "?"),
                "why": t.get("why", ""),
                "count": t.get("count", 0),
                "first_seen": t.get("first_seen", ""),
                "last_seen": t.get("last_seen", ""),
            }
            for t in self._trouble.live()
        ]
