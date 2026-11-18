"""dbproxy/shim.py — the database proxy's front on the bus; it answers as ``database``."""

from __future__ import annotations

import json
import os
import signal

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

    def _relay(self) -> dict:
        """The relay's record, as the face reads it; with no face up, read the same way."""
        if super().running and self._device is not None:
            return self._device.state()
        from cairn.devices.dbproxy.__main__ import record_path
        from cairn.devices.dbproxy.device import pid_alive
        try:
            rec = json.loads(record_path().read_text())
        except (OSError, ValueError):
            return {}
        if rec.get("state") == "listening" and not pid_alive(rec.get("pid")):
            rec = {**rec, "state": "stopped"}
        return rec

    @property
    def running(self) -> bool:
        # THE RELAY IS WHAT RUNS (tickets cad4a0d27e0a, 68d8d3add713). The face is this shim's
        # in-process object; the relay is its own process, and it can die under a live face or
        # outlive the face host that spawned it. Measured 2026-11-18 on akienlivingroom: start
        # said 'already running' over 0 listeners, and stop said 'not running' over a listening
        # orphan. A live relay with no face is ADOPTED (the face's wake is a no-op over a
        # listening relay), so the base resolver never reads running with no face to ask.
        if self._relay().get("state") != "listening":
            return False
        if not super().running or self._device is None:
            super()._ensure_device()
        return True

    @staticmethod
    def _kill(pid: int) -> None:
        os.kill(pid, signal.SIGTERM)        # TerminateProcess on Windows

    def _stop_device(self) -> None:
        pid = self._relay().get("pid")
        if self._relay().get("state") == "listening" and isinstance(pid, int):
            self._kill(pid)
        super()._stop_device()

    def _ensure_device(self) -> None:
        if super().running and self._device is not None:
            self._device.wake()
            return
        super()._ensure_device()

    def _start_device(self):
        from cairn.devices.dbproxy.device import DatabaseProxyDevice
        return DatabaseProxyDevice()
