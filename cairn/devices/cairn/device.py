"""cairn/device.py — the cairn system device.

The top-level device. Its machines (ground_loop, harbor_master, bus) are the
system's own infrastructure. Receives feedback from probes that target the
system itself — operator_inbox accuracy, system-level efficacy findings.

All inbound mail is recorded to a DataRecorder for later evaluation.
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice


class CairnDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "cairn"
        self._recorder = None

    @property
    def device_id(self) -> str:
        return self._device_id

    def _get_recorder(self):
        if self._recorder is None:
            from cairn.tools.data_recorder.data_recorder import DataRecorder
            from cairn.tools.base.address import instance_path
            self._recorder = DataRecorder(
                instance_path("cairn", 0) / "tools" / "data_recorder" / "inbound")
        return self._recorder

    def receive(self, envelope: dict) -> dict:
        """Accept an incoming bus envelope — system-level feedback."""
        self._get_recorder().write({
            "finding": envelope.get("why", "bus message received"),
            "inspector_target": "cairn",
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
            "what": "The cairn system device — top-level holder of ground_loop, "
                    "harbor_master, and bus.",
            "why": "Every device has a presence on the bus (Akien, 2026-08-11). "
                    "The system itself is a device and answers its own mail.",
        }

    def state(self) -> dict:
        return {}

    def settings(self) -> dict:
        return {}
