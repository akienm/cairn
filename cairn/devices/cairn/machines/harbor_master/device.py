"""harbor_master/device.py — the fleet register as a device.

The harbor_master's machinery (register.py, voyage.py, clearance.py) predates its
device class. This wraps the existing modules behind a BaseDevice face so the
harbor can be addressed on the bus — which is what 29 probes across the system are
trying to do.

Receives mail through two paths:
  - verb "crossing" — the most-sent verb in the fleet (every workflow transition)
  - verbless receive() — BaseDevice default records to DataRecorder
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice


class HarborMasterDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "harbor_master"

    @property
    def device_id(self) -> str:
        return self._device_id

    def declared_verbs(self) -> dict:
        return {"crossing": self._handle_crossing}

    def _handle_crossing(self, envelope: dict) -> dict:
        super().receive(envelope)
        return {"accepted": True, "verb": "crossing", "device": self.device_id}

    def intention(self) -> dict:
        return {
            "what": "Fleet register — compiled index over the boats' own records, "
                    "clearance gate for workflow transitions, voyage view.",
            "why": "The harbor through which workflows voyage. Every boat's standing "
                    "is read from the boat's own record (Law 7 — the register invents "
                    "no truth a boat does not already hold).",
        }

    def state(self) -> dict:
        try:
            from cairn.devices.cairn.machines.harbor_master.register import register
            reg = register()
            return {
                "total_boats": len(reg.get("boats", [])),
                "open": len([b for b in reg.get("boats", []) if b.get("berth") == "open"]),
                "in_port": len([b for b in reg.get("boats", []) if b.get("berth") == "in_port"]),
            }
        except Exception:
            return {"error": "register unavailable"}

    def settings(self) -> dict:
        return {}
