"""charter/device.py — the charter tool's bus presence.

Charter is a TOOL (Law 6: users, not an owner). Its probes post findings
back to "charter" on the bus. This device is what receives those findings
and records them for later evaluation.
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice


class CharterDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "charter"
        self._recorder = None

    @property
    def device_id(self) -> str:
        return self._device_id

    def _get_recorder(self):
        if self._recorder is None:
            from cairn.tools.data_recorder.data_recorder import DataRecorder
            from cairn.tools.base.address import instance_path
            self._recorder = DataRecorder(
                instance_path("charter", 0) / "tools" / "data_recorder" / "inbound")
        return self._recorder

    def receive(self, envelope: dict) -> dict:
        """Accept an incoming bus envelope — charter probe findings."""
        self._get_recorder().write({
            "finding": envelope.get("why", "bus message received"),
            "inspector_target": "charter",
            "probe_source": envelope.get("sender", "unknown"),
            "envelope_id": envelope.get("id"),
            "verb": envelope.get("verb", ""),
            "body": envelope.get("body", {}),
        })
        self.emit("received", pointer=envelope.get("sender", "unknown"),
                  values={"why": (envelope.get("why") or "")[:120]})
        return {"accepted": True, "device": self.device_id}

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
