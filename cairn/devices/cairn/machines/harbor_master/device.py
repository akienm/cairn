"""harbor_master/device.py — the fleet register as a device.

The harbor_master's machinery (register.py, voyage.py, clearance.py) predates its
device class. This wraps the existing modules behind a BaseDevice face so the
harbor can be addressed on the bus — which is what 29 probes across the system are
trying to do.

Receives mail through two paths:
  - verb "crossing" — the most-sent verb in the fleet (every workflow transition)
  - verbless receive() — anything else a probe might post

Both record to a DataRecorder for later evaluation by the scheduled LLM inspection.
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice


class HarborMasterDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "harbor_master"
        self._recorder = None

    @property
    def device_id(self) -> str:
        return self._device_id

    def _get_recorder(self):
        if self._recorder is None:
            from cairn.tools.data_recorder.data_recorder import DataRecorder
            from cairn.tools.base.address import instance_path
            self._recorder = DataRecorder(
                instance_path("harbor_master", 0) / "tools" / "data_recorder" / "inbound")
        return self._recorder

    def _record(self, envelope: dict) -> None:
        self._get_recorder().write({
            "finding": envelope.get("why", "bus message received"),
            "inspector_target": "harbor_master",
            "probe_source": envelope.get("sender", "unknown"),
            "envelope_id": envelope.get("id"),
            "verb": envelope.get("verb", ""),
            "body": envelope.get("body", {}),
        })
        self.emit("received", pointer=envelope.get("sender", "unknown"),
                  values={"why": (envelope.get("why") or "")[:120]})

    def declared_verbs(self) -> dict:
        return {"crossing": self._handle_crossing}

    def _handle_crossing(self, envelope: dict) -> dict:
        self._record(envelope)
        return {"accepted": True, "verb": "crossing", "device": self.device_id}

    def receive(self, envelope: dict) -> dict:
        """Accept an incoming bus envelope — probe findings from across the fleet."""
        self._record(envelope)
        return {"accepted": True, "device": self.device_id}

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
