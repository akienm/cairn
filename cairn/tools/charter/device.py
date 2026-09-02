"""charter/device.py — the charter tool's bus presence.

Charter is a TOOL (Law 6: users, not an owner). Its probes post findings
back to "charter" on the bus. BaseDevice.receive() records inbound mail
to a DataRecorder for later evaluation.
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice


class CharterDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "charter"

    @property
    def device_id(self) -> str:
        return self._device_id

    def intention(self) -> dict:
        return {
            "what": "Charter tool's bus presence — receives probe findings.",
            "why": "Every device has a presence on the bus (Akien, 2026-08-11). "
                    "Charter's probes self-address findings here.",
        }

    def state(self) -> dict:
        return {}

    def settings(self) -> dict:
        return {}
