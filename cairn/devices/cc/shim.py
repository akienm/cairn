"""cc/shim.py — Claude Code's presence on the heartbeat.

CC's process is not started by this shim — CC starts itself. The shim gives CC
a rack address so the bus can deliver messages to it and the ground loop can
fire its probes. A shim without a device process behind it is honest, not broken:
the probes still fire (they read disk, not CC), and deliver() persists mail to
the instance mail directory so hooks can inject it into the next query.

tmux mode: when CC runs in a tmux session (superclaude --tmux), the shim can
detect idle state and inject commands. is_idle() reads the tmux pane; inject()
sends keys only when idle.

The idle poke (ticket 1e2640bad4dd): the mailcheck hook announces mail only inside
an active turn, so mail that lands while CC sits idle would wait unread. After
deliver() persists an envelope, poke_if_idle() reads Claude Code's own session
record for the session superclaude names <hostname>_cc_0 and, if it is idle,
launches one detached headless `claude -p` whose only act is SendMessage "you've
got mail". The content never rides the poke (Akien 2026-10-14: "we only use it
(if we can) to tell you that you've got mail. then you go read it"). One poke per
idle stretch: none after a poke until a consume. Every decision is ledgered.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.base.shim import BaseShim

_INSTANCE_ROOT = address.instance_path("cc", 0)
_MAIL_DIR = _INSTANCE_ROOT / "mail"
_LEDGER = _INSTANCE_ROOT / "mail_ledger.jsonl"
# Claude Code writes one <pid>.json per running session here (name, status idle|busy).
# It is Claude Code's internal record, so it is read defensively and never written.
_SESSIONS_DIR = Path.home() / ".claude" / "sessions"
_CLAUDE_CMD = ["claude"]
_CAIRN_ROOT = Path(__file__).resolve().parents[3]


def _ledger(event: dict, ledger: Path | None = None) -> None:
    """Append one line to the mail ledger: the record the mail probe counts, because
    consume_mail deletes what it reads and the mail folder cannot count deliveries."""
    p = Path(ledger) if ledger is not None else _LEDGER
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


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
        _ledger({"event": "delivered", "id": msg_id, "at": now.isoformat(),
                 "from": envelope.get("from", envelope.get("sender", "unknown"))})
        # Only the instance's own mailbox belongs to the named session; mail written
        # anywhere else (a proof's temp dir) is not its mail and pokes nobody.
        if _MAIL_DIR == _INSTANCE_ROOT / "mail":
            self.poke_if_idle()
        return {"persisted": True, "path": str(path)}

    # ── the idle poke ────────────────────────────────────────────────────

    @staticmethod
    def poke_target() -> str:
        """The session name superclaude gives CC (launchers/superclaude --name)."""
        return f"{socket.gethostname()}_cc_0"

    @staticmethod
    def session_state(target: str, sessions_dir: Path | str | None = None) -> str:
        """'idle', 'busy', 'ambiguous' (two sessions carry the name) or 'absent'.
        A missing dir or a torn record is never an error here: it is no session."""
        d = Path(sessions_dir) if sessions_dir is not None else _SESSIONS_DIR
        try:
            records = sorted(d.glob("*.json"))
        except OSError:
            return "absent"
        matches = []
        for p in records:
            try:
                rec = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(rec, dict) and rec.get("name") == target:
                matches.append(rec)
        if not matches:
            return "absent"
        if len(matches) > 1:
            return "ambiguous"
        return "idle" if matches[0].get("status") == "idle" else "busy"

    @staticmethod
    def _poked_since_consumed(ledger: Path) -> bool:
        last_poke = last_consume = -1
        try:
            lines = ledger.read_text().splitlines()
        except OSError:
            return False
        for i, line in enumerate(lines):
            try:
                event = json.loads(line).get("event")
            except (json.JSONDecodeError, AttributeError):
                continue
            if event == "poked":
                last_poke = i
            elif event == "consumed":
                last_consume = i
        return last_poke > last_consume

    def poke_if_idle(self) -> dict:
        """Tell an idle CC session it has mail; ledger the decision either way.
        Never raises: deliver() has already persisted the mail, and that stands."""
        target = self.poke_target()
        now = datetime.now(timezone.utc).isoformat()
        state = self.session_state(target)
        if state != "idle":
            reason = {"busy": "busy", "ambiguous": f"two sessions are named {target}",
                      "absent": f"no session named {target}"}[state]
            _ledger({"event": "not-poked", "reason": reason, "target": target, "at": now})
            return {"poked": False, "reason": reason}
        if self._poked_since_consumed(Path(_LEDGER)):
            _ledger({"event": "not-poked", "reason": "already poked", "target": target, "at": now})
            return {"poked": False, "reason": "already poked"}
        prompt = (f'Call SendMessage exactly once with to="{target}" and '
                  f'message="you\'ve got mail — {_MAIL_DIR}". Do nothing else.')
        try:
            subprocess.Popen(
                [*_CLAUDE_CMD, "-p", "--model", "haiku",
                 "--permission-mode", "bypassPermissions", prompt],
                cwd=str(_CAIRN_ROOT), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError as exc:
            reason = f"launch failed: {exc}"
            _ledger({"event": "not-poked", "reason": reason, "target": target, "at": now})
            return {"poked": False, "reason": reason}
        _ledger({"event": "poked", "target": target, "at": now})
        return {"poked": True, "target": target}

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
        """Read and remove all pending mail, ledgering each read with the CC session."""
        d = Path(mail_dir) if mail_dir else _MAIL_DIR
        if not d.is_dir():
            return []
        messages = []
        for p in sorted(d.glob("msg-*.json")):
            try:
                record = json.loads(p.read_text())
                p.unlink()
            except (json.JSONDecodeError, OSError):
                continue
            messages.append(record)
            _ledger({"event": "consumed", "id": record.get("id", p.stem),
                     "at": datetime.now(timezone.utc).isoformat(),
                     "session": os.environ.get("CLAUDE_CODE_SESSION_ID", "")})
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
