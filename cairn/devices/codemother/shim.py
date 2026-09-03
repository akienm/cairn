"""codemother/shim.py — CodeMother's presence on the heartbeat.

CodeMother is its own PID, shim-launched on demand via MCP/chat/CLI/skill.
The shim gives CodeMother a rack address so the bus can deliver messages to it
and the ground loop can fire its probes. deliver() persists mail to the instance
mail directory; the device process reads it when woken.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.shim import BaseShim
from cairn.tools.base.address import instance_path

_INSTANCE_ROOT = instance_path("codemother", 0)
_MAIL_DIR = _INSTANCE_ROOT / "mail"


class CodeMotherShim(BaseShim):

    declared_verbs = ("activate", "commit", "question")

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "codemother"

    def _start_device(self):
        return None

    def handle_verb(self, verb: str, envelope: dict) -> dict | None:
        """Route watcher verbs to the watcher face."""
        body = envelope.get("body") or {}
        if verb == "activate":
            from cairn.devices.codemother.watch import activate
            return activate(
                body.get("area", ""),
                body.get("reason", "bus verb"),
                context=body.get("context"),
            )
        if verb == "commit":
            from cairn.devices.codemother.watch import on_commit
            return on_commit(
                body.get("hash", ""),
                body.get("files", []),
                body.get("message", ""),
            )
        if verb == "question":
            from cairn.devices.codemother.watch import on_question
            return on_question(
                body.get("question", ""),
                area=body.get("area"),
            )
        return None

    def deliver(self, envelope: dict):
        """Persist the envelope to the instance mail directory."""
        _MAIL_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        msg_id = f"msg-{now.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
        record = {
            "id": msg_id,
            "received": now.isoformat(),
            "envelope": envelope,
        }
        path = _MAIL_DIR / f"{msg_id}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
        return {"persisted": True, "path": str(path)}
