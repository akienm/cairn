"""cc/shim.py — Claude Code's presence on the heartbeat.

CC's process is not started by this shim — CC starts itself. The shim gives CC
a rack address so the bus can deliver messages to it and the ground loop can
fire its probes. A shim without a device process behind it is honest, not broken:
the probes still fire (they read disk, not CC), and deliver() persists mail to
the instance mail directory so hooks can inject it into the next query.

tmux mode: when CC runs in a tmux session (superclaude --tmux), the shim can
detect idle state and inject commands. is_idle() reads the tmux pane; inject()
sends keys only when idle.
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.base.shim import BaseShim

_INSTANCE_ROOT = address.instance_path("cc", 0)
_MAIL_DIR = _INSTANCE_ROOT / "mail"


class CCShim(BaseShim):

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "cc"

    def _start_device(self):
        return None

    # ── mail persistence ─────────────────────────────────────────────────
    # deliver() writes to disk so hooks can find waiting mail between queries.

    def deliver(self, envelope: dict):
        """Persist the envelope to the instance mail directory.

        CC is not started by the shim, so routing to a device is not possible.
        Instead, messages land as files that the mailcheck hook picks up."""
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

    @staticmethod
    def pending_mail(mail_dir: Path | str | None = None) -> list[dict]:
        """Read pending mail from the instance directory."""
        d = Path(mail_dir) if mail_dir else _MAIL_DIR
        if not d.is_dir():
            return []
        messages = []
        for p in sorted(d.glob("msg-*.json")):
            try:
                messages.append(json.loads(p.read_text()))
            except (json.JSONDecodeError, OSError):
                continue
        return messages

    @staticmethod
    def consume_mail(mail_dir: Path | str | None = None) -> list[dict]:
        """Read and remove all pending mail."""
        d = Path(mail_dir) if mail_dir else _MAIL_DIR
        if not d.is_dir():
            return []
        messages = []
        for p in sorted(d.glob("msg-*.json")):
            try:
                messages.append(json.loads(p.read_text()))
                p.unlink()
            except (json.JSONDecodeError, OSError):
                continue
        return messages

    # ── tmux idle detection and command injection ────────────────────────

    @staticmethod
    def is_idle(session_name: str) -> bool:
        """Detect whether CC is idle in a tmux session.

        Reads the last line of the tmux pane. CC is idle when the pane ends with
        the input prompt ("> " or "$ ") and there is no running command. Returns
        False on any error (session not found, tmux not running)."""
        try:
            output = subprocess.run(
                ["tmux", "capture-pane", "-t", session_name, "-p"],
                capture_output=True, text=True, timeout=5,
            )
            if output.returncode != 0:
                return False
            lines = output.stdout.rstrip("\n").split("\n")
            if not lines:
                return False
            last = lines[-1].rstrip()
            return last.endswith("> ") or last.endswith("$ ") or last == ">"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    @staticmethod
    def inject_command(session_name: str, command: str) -> dict:
        """Inject a command into an idle tmux CC session.

        Refuses if the session is not idle (never inject into an active session).
        Returns a dict with the outcome."""
        if not CCShim.is_idle(session_name):
            return {"injected": False, "reason": "session is not idle"}
        try:
            result = subprocess.run(
                ["tmux", "send-keys", "-t", session_name, command, "Enter"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return {"injected": False, "reason": f"tmux send-keys failed: {result.stderr}"}
            return {"injected": True, "command": command, "session": session_name}
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            return {"injected": False, "reason": str(exc)}
