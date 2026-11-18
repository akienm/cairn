"""dbproxy/shim.py — the database proxy's front on the bus; it answers as ``database``."""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim


class DatabaseProxyShim(BaseShim):

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "database"

    def _bare(self) -> dict:
        return {"exit": 0, "text": f"device: {self.device_id}\nclass:  cairn/devices/dbproxy/",
                "data": None, "cached": None}

    def _start_device(self):
        from cairn.devices.dbproxy.device import DatabaseProxyDevice
        return DatabaseProxyDevice()
