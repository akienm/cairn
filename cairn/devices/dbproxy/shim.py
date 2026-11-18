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

    @property
    def running(self) -> bool:
        # THE RELAY IS WHAT RUNS (ticket cad4a0d27e0a). The face is this shim's in-process
        # object; the relay is its own process and can die under it. Measured 2026-11-18 on
        # akienlivingroom: start said 'already running' over 0 listeners on 5432.
        if not super().running or self._device is None:
            return False
        return self._device.state().get("state") == "listening"

    def _ensure_device(self) -> None:
        if super().running and self._device is not None:
            self._device.wake()
            return
        super()._ensure_device()

    def _start_device(self):
        from cairn.devices.dbproxy.device import DatabaseProxyDevice
        return DatabaseProxyDevice()
