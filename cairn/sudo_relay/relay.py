"""sudo_relay — a command goes in, a root-run and a permanent audit record come out.

THE INTENTION (2026-07-18, Akien): a Cairn-native 'thing-for-akien-along-the-way'.
Akien's whole ops role shrinks to two acts — **start the daemon** (one password) and
**approve** — and CC self-serves root through it. It traces to the founding
measurement: get Akien out of running the system. Today CC reaches root through the
UU-tree daemon; that is a STOPGAP Cairn must not depend on at runtime — this device is
its Cairn-native replacement, built fresh to Form v0 (charter + proofs), like the
tester and db_domain.

WHAT IT DOES (the stone Akien named): take a command → run it → emit a JSON **record of
truth** carrying the command line, the return code, stdout and stderr (Law 7 — a record
of truth keeps the error permanent and uncollapsed, so stdout/stderr are stored FULL,
never tailed). The audit folder self-cycles to a rolling one-month window
(``retention_days``, default 31): a declared retention, not a silent mutation.

THE SEAM THAT MAKES IT PROVABLE WITHOUT ROOT: ``process_pending`` runs a command through
an **injected executor**. The daemon injects ``root_executor`` (``sudo -n bash -c``); the
proof injects ``local_executor`` (plain ``bash -c``), so the whole protocol
(pending → executing → done), the audit record, and the retention window are proven green
with a non-root payload — a proof a hollow relay could not pass — while root itself never
enters the test. Same shape as the tester's isolation seam.

TEMPORARY IS PHYSICS (Law 4), and THE WINDOW IS VISIBLE. The UU daemon held live sudo for
4+ days because its lifetime was invisible. Here the daemon carries an idle timeout AND a
hard absolute cap (defaults 30 min / 24 h, both settings), calls ``sudo -k`` on exit, and
maintains a heartbeat ``daemon.status`` file so ``SudoRelayDevice.state()`` and the
``status`` command always answer 'up since when, expires in how long' — measured against a
live-pid check, never assumed (Law 3).

OWNERSHIP (Law 6): CC owns this code + its proofs. The daemon's AUTHORITY is Akien's — it
exists only while he chooses to run it, and the password act is his alone; the daemon
holds no stored credential. The audit log is a record of truth written by the relay
process (as Akien, not as root): the command runs as root, the record is written beside
it.

OPEN EDGES (filed, not faked — children of this stone):
  - The daemon's sudo acquisition + keepalive (``daemon.py``) is the one privileged part
    the proof cannot exercise (it needs a password/TTY). Everything UNDER it —
    ``process_pending``, the record, retention, ``should_expire``, the status surface — is
    proven; the daemon is a thin wrapper that wires those to ``root_executor``.
  - Approval is today the coarse act of choosing to run the daemon (consent = the password
    act, as in the UU relay). Per-command approval / an allowlist is deliberately NOT built
    — ratified scope is unrestricted root, 'the box IS the restriction'; the safeguard is
    the visible audit, not friction.
  - No pending-queue ordering / concurrency: one command at a time (atomic pending →
    executing handoff), matching a single builder's serial use.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

from cairn.base.device import BaseDevice

# The record-of-truth shape. Exactly these six — the four Akien named (command, returncode,
# stdout, stderr) plus the id + date that make it a locatable, expiring record. The proof
# pins the set so a drifted record reds (a hollow relay that drops a field cannot pass).
AUDIT_FIELDS = ("id", "date", "command", "returncode", "stdout", "stderr")

# Filenames the retention sweep is allowed to touch. Anchored to the id shape we mint, so a
# foreign file dropped in the folder is NEVER deleted (Law 7 — we do not collapse what we
# did not write).
_ID_RE = re.compile(r"^(\d{8}T\d{6})_\d{6}_\d+$")

DEFAULT_RETENTION_DAYS = 31
DEFAULT_IDLE_TIMEOUT_S = 30 * 60        # 30 minutes with no request → release root
DEFAULT_MAX_LIFETIME_S = 24 * 60 * 60   # 24 hours absolute → release root no matter what

_STATUS_NAME = "daemon.status"
_PENDING = "pending.sh"
_EXECUTING = "executing.sh"
_DONE = "done"


# ── where the instance lives (instance-space, never class-space) ─────────────


def instance_dir() -> Path:
    """The runtime home: ``~/.cairn/devices/sudo_relay/0`` (a singleton is instance 0).

    Overridable via ``CAIRN_SUDO_RELAY_DIR`` so a proof runs hermetically in a scratch dir
    and never touches real instance-space or real audit truth.
    """
    override = os.environ.get("CAIRN_SUDO_RELAY_DIR")
    if override:
        return Path(override)
    return Path.home() / ".cairn" / "devices" / "sudo_relay" / "0"


def relay_dir() -> Path:
    return instance_dir() / "relay"


def audit_dir() -> Path:
    return instance_dir() / "audit"


def _ensure(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# ── the record of truth ──────────────────────────────────────────────────────


def _mint_id(now: datetime) -> str:
    """A sortable, collision-resistant id: ``YYYYMMDDThhmmss_micros_pid``."""
    return f"{now.strftime('%Y%m%dT%H%M%S')}_{now.microsecond:06d}_{os.getpid()}"


def audit_record(command: str, returncode, stdout: str, stderr: str, *, now: datetime) -> dict:
    """Assemble the six-field record of truth. stdout/stderr kept FULL (Law 7)."""
    return {
        "id": _mint_id(now),
        "date": now.isoformat(timespec="seconds"),
        "command": command,
        "returncode": returncode,      # int, or None if the run could not complete
        "stdout": stdout,
        "stderr": stderr,
    }


def emit(record: dict, *, now: datetime, retention_days: int = DEFAULT_RETENTION_DAYS) -> Path:
    """Write ``record`` to the audit folder as an immutable JSON, then cycle the window.

    The write is the permanent record (Law 7); the sweep afterward removes only records
    whose OWN timestamp is older than ``retention_days`` — the rolling one-month folder
    Akien asked for, applied to entries we minted, never to foreign files.
    """
    adir = audit_dir()
    _ensure(adir)
    path = adir / f"{record['id']}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True))
    prune_audit(now=now, retention_days=retention_days)
    return path


def prune_audit(*, now: datetime, retention_days: int = DEFAULT_RETENTION_DAYS) -> list[str]:
    """Delete audit records older than the window. Returns the ids cycled out (for the log).

    Only files whose name matches the minted-id pattern are candidates; the embedded
    timestamp — not the file mtime — decides age (Law 3: measure the record's own time).
    """
    adir = audit_dir()
    if not adir.exists():
        return []
    cutoff = now - timedelta(days=retention_days)
    cycled: list[str] = []
    for f in adir.glob("*.json"):
        m = _ID_RE.match(f.stem)
        if not m:
            continue  # not ours — never touch it
        try:
            stamp = datetime.strptime(m.group(1), "%Y%m%dT%H%M%S")
        except ValueError:
            continue
        if stamp < cutoff:
            f.unlink()
            cycled.append(f.stem)
    return cycled


# ── the relay protocol (the seam: executor is injected) ──────────────────────


def local_executor(command: str, *, timeout: int = 120) -> tuple:
    """Run ``command`` as the current user via bash. The NON-root executor (proof + daemonless
    use). Returns ``(returncode, stdout, stderr)``; a timeout is an honest (None, ...) result,
    never a crash of the relay (CP1: say what happened — we measured a timeout, not a pass)."""
    return _run(["bash", "-c", command], timeout=timeout)


def root_executor(command: str, *, timeout: int = 120) -> tuple:
    """Run ``command`` as root via the daemon's live sudo timestamp. ``-n`` is non-interactive:
    if the daemon's sudo has lapsed this FAILS LOUDLY rather than hanging on a hidden prompt."""
    return _run(["sudo", "-n", "bash", "-c", command], timeout=timeout)


def _run(argv: list, *, timeout: int) -> tuple:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        return None, out, f"{err}\n[sudo_relay] timed out after {timeout}s".lstrip()


def submit(command: str) -> Path:
    """Client side (CC): write the command as the pending request. Returns the pending path."""
    rdir = relay_dir()
    _ensure(rdir)
    path = rdir / _PENDING
    path.write_text(command)
    return path


def process_pending(executor, *, now: datetime, retention_days: int = DEFAULT_RETENTION_DAYS):
    """One daemon iteration: pick up a pending command, run it via ``executor``, emit the
    permanent audit record, and hand the same record back to the client via ``done``.

    Returns the record, or ``None`` when there is nothing pending (the idle case). This is
    the whole relay; the daemon just calls it in a loop with ``root_executor``, and the proof
    calls it once with ``local_executor`` — same code, no root in the test.
    """
    rdir = relay_dir()
    pending = rdir / _PENDING
    if not pending.exists():
        return None

    # Atomic handoff: claim the request before running it, so a second call can't double-run.
    executing = rdir / _EXECUTING
    os.replace(pending, executing)
    command = executing.read_text()

    returncode, stdout, stderr = executor(command)
    record = audit_record(command, returncode, stdout, stderr, now=now)
    emit(record, now=now, retention_days=retention_days)

    # The client's return: the full record, not just an exit code (it wants stdout/stderr too).
    (rdir / _DONE).write_text(json.dumps(record))
    executing.unlink(missing_ok=True)
    return record


def await_result(*, timeout: float = 120.0, poll: float = 0.1) -> dict:
    """Client side (CC): block until ``done`` appears, then consume and return the record.

    Raises ``TimeoutError`` if no daemon answers inside ``timeout`` — a missing daemon is a
    loud failure, not a silent hang.
    """
    done = relay_dir() / _DONE
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if done.exists():
            record = json.loads(done.read_text())
            done.unlink(missing_ok=True)
            return record
        time.sleep(poll)
    raise TimeoutError(
        f"no result after {timeout}s — is the sudo_relay daemon running? "
        f"(start: python3 cairn/sudo_relay/daemon.py)"
    )


def request_root(command: str, *, timeout: float = 120.0) -> dict:
    """The full client call CC makes: submit a command, wait, return its audit record.

    Requires Akien's daemon to be running (his one act). The returned record is also the
    permanent audit entry — the same JSON, in the folder, for a month.
    """
    submit(command)
    return await_result(timeout=timeout)


# ── temporary-as-physics: the expiry decision, and the visible window ────────


def should_expire(
    started_at: datetime,
    last_activity: datetime,
    now: datetime,
    *,
    max_lifetime_s: int = DEFAULT_MAX_LIFETIME_S,
    idle_timeout_s: int = DEFAULT_IDLE_TIMEOUT_S,
) -> tuple:
    """Should the daemon release root now? Returns ``(expire: bool, reason: str)``.

    Pure so it is provable without a running daemon: the absolute cap bounds a forgotten
    daemon (it cannot hold root for days); the idle timeout releases root after a walk-away.
    """
    if (now - started_at).total_seconds() >= max_lifetime_s:
        return True, f"absolute cap reached ({max_lifetime_s}s since start)"
    if (now - last_activity).total_seconds() >= idle_timeout_s:
        return True, f"idle timeout reached ({idle_timeout_s}s since last request)"
    return False, ""


def write_status(
    *,
    pid: int,
    started_at: datetime,
    last_activity: datetime,
    now: datetime,
    max_lifetime_s: int = DEFAULT_MAX_LIFETIME_S,
    idle_timeout_s: int = DEFAULT_IDLE_TIMEOUT_S,
) -> Path:
    """The daemon's heartbeat — makes the root-holding window visible (Akien's requirement).

    Records both deadlines so any reader can see, without guessing, when root will be
    released. Refreshed each keepalive so ``last_activity``/idle-deadline stay current.
    """
    idir = instance_dir()
    _ensure(idir)
    status = {
        "pid": pid,
        "started_at": started_at.isoformat(timespec="seconds"),
        "last_activity": last_activity.isoformat(timespec="seconds"),
        "hard_expires_at": (started_at + timedelta(seconds=max_lifetime_s)).isoformat(timespec="seconds"),
        "idle_expires_at": (last_activity + timedelta(seconds=idle_timeout_s)).isoformat(timespec="seconds"),
        "heartbeat_at": now.isoformat(timespec="seconds"),
    }
    path = idir / _STATUS_NAME
    path.write_text(json.dumps(status, indent=2, sort_keys=True))
    return path


def clear_status() -> None:
    """Drop the heartbeat — the daemon calls this on exit, so 'no live daemon' is the truth."""
    (instance_dir() / _STATUS_NAME).unlink(missing_ok=True)


def _pid_alive(pid: int) -> bool:
    """Measure whether a pid is live — never assume the status file means a running daemon."""
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    return True


def daemon_status(*, now: datetime | None = None) -> dict:
    """The visible window, measured (Law 3): is a daemon live, and when does root release?

    ``live`` is a real pid check, not the mere presence of the file — a crashed daemon's
    stale status reads as not-live, so the window never lies.
    """
    path = instance_dir() / _STATUS_NAME
    if not path.exists():
        return {"live": False, "reason": "no daemon.status — the relay is not running"}
    try:
        s = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"live": False, "reason": f"unreadable status: {e}"}

    pid = s.get("pid")
    live = isinstance(pid, int) and _pid_alive(pid)
    out = dict(s)
    out["live"] = live
    if not live:
        out["reason"] = f"status names pid {pid}, but no such process — stale (daemon exited or crashed)"
    return out


# ── the device: Form v0 surface + the six ────────────────────────────────────


class SudoRelayDevice(BaseDevice):
    """CC's self-serve root path, as a device (carries CP1-CP6; reports intention/state/settings).

    Its capability is ``request_root(command)``; its state surfaces the visible root-holding
    window so 'how long has root been held' is always answerable, not a thing to remember to
    check.
    """

    def __init__(self, device_id: str = "sudo_relay") -> None:
        super().__init__()
        self._device_id = device_id

    @property
    def device_id(self) -> str:
        return self._device_id

    def request_root(self, command: str, *, timeout: float = 120.0) -> dict:
        """Run ``command`` as root via the daemon and return its permanent audit record."""
        return request_root(command, timeout=timeout)

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "Take a command, run it as root through Akien's daemon, and emit a permanent "
            "audit record (command, return code, stdout, stderr) — CC's self-serve path to root.",
            "why": "Shrink Akien's ops role to two acts — start the daemon, approve — so the system "
            "runs itself (the founding intention); the visible audit + the box are the safeguard.",
        }

    def state(self) -> dict:
        # The visible window (Akien's requirement) + how much truth is on hand — all measured.
        status = daemon_status()
        adir = audit_dir()
        audit_count = len(list(adir.glob("*.json"))) if adir.exists() else 0
        return {
            "daemon": status,                 # live?/started/expires — the visible root window
            "audit_records": audit_count,     # how many records currently in the month window
        }

    def settings(self) -> dict:
        return {
            "instance_dir": str(instance_dir()),
            "retention_days": DEFAULT_RETENTION_DAYS,
            "idle_timeout_s": DEFAULT_IDLE_TIMEOUT_S,
            "max_lifetime_s": DEFAULT_MAX_LIFETIME_S,
            "consent": "Akien runs the daemon once (one password); the daemon holds no stored "
            "credential and releases root (sudo -k) on idle, cap, or exit.",
        }
