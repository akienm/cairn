"""sudo_relay — a command goes in, a root-run and a permanent audit record come out.

THE INTENTION (2026-07-18, Akien): a Cairn-native 'thing-for-akien-along-the-way'.
Akien's whole ops role shrinks to two acts — **start the daemon** (one password) and
**approve** — and CC self-serves root through it. It traces to the founding
measurement: get Akien out of running the system. Today CC reaches root through the
UU-tree daemon; that is a STOPGAP Cairn must not depend on at runtime — this device is
its Cairn-native replacement, built fresh to Form v0 (charter + proofs), like the
tester and db_domain.

WHAT IT DOES (the stone Akien named): take a command → run it → write a JSON **record of
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
4+ days because its lifetime was invisible. Here the daemon carries a hard absolute cap
(default 24 h — 'log in once a day', the sole automatic release), calls ``sudo -k`` on exit,
and maintains a heartbeat ``daemon.status`` file so ``SudoRelayDevice.state()`` and the
``status`` command always answer 'up since when, expires in how long' — measured against a
live-pid check, never assumed (Law 3). There is NO idle timeout by default: one login lasts
the day, no re-login on a walk-away (the dedicated box is the safety net, not a timeout — the
ratified scope rejects friction). An idle timeout stays as an opt-in knob; Ctrl-C is the
everyday stop-sooner lever.

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
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cairn.tools.base.address import instance_path
from cairn.tools.base.device import BaseDevice

# The record-of-truth shape. Exactly these six — the four Akien named (command, returncode,
# stdout, stderr) plus the id + date that make it a locatable, expiring record. The proof
# pins the set so a drifted record reds (a hollow relay that drops a field cannot pass).
AUDIT_FIELDS = ("id", "date", "command", "returncode", "stdout", "stderr")

# Filenames the retention sweep is allowed to touch. Anchored to the id shape we mint, so a
# foreign file dropped in the folder is NEVER deleted (Law 7 — we do not collapse what we
# did not write).
_ID_RE = re.compile(r"^(\d{8}T\d{6})_\d{6}_\d+$")

DEFAULT_RETENTION_DAYS = 31
# The intent is 'log in once a day' — so the ONLY automatic release is the hard cap; one
# password lasts up to a full day of use. There is NO idle timeout by default (an idle
# release would force a re-login after a walk-away — friction the ratified scope rejects:
# the box + the visible audit are the safeguard, not friction). The idle timeout stays as
# an OPT-IN knob (set idle_timeout_s to a number) for anyone who wants a stop-sooner rule;
# the everyday stop-sooner lever is Ctrl-C.
DEFAULT_IDLE_TIMEOUT_S = None           # off by default — opt-in; None = no idle release
DEFAULT_MAX_LIFETIME_S = 24 * 60 * 60   # 24 hours — 'log in once a day'; the sole automatic release

_STATUS_NAME = "daemon.status"
# A request carries its own id from the moment it is submitted (ticket ae25d8fae5cb): the
# daemon answers into results/<id>.json, the client reads ONLY its own file, and an
# awaiting/<id> marker says somebody is still waiting for it. Measured before this: a single
# relay/done slot handed whatever it held to the next request, so a command that never ran
# read rc 0. relay/done is still READ (as an orphan) when an old daemon left one; never written.
_PENDING = "pending.json"
_EXECUTING = "executing.json"
_RESULTS = "results"
_AWAITING = "awaiting"
_LEGACY_DONE = "done"
# The client waits the request's own timeout plus this, so a command the DAEMON timed out
# still comes home as its own honest record (rc None) rather than racing the client's clock.
_AWAIT_GRACE_S = 5.0


# ── where the instance lives (instance-space, never class-space) ─────────────


def instance_dir() -> Path:
    """The runtime home: ``~/.cairn/devices/sudo_relay/0`` (a singleton is instance 0).

    Overridable via ``CAIRN_SUDO_RELAY_DIR`` so a proof runs hermetically in a scratch dir
    and never touches real instance-space or real audit truth.
    """
    override = os.environ.get("CAIRN_SUDO_RELAY_DIR")
    if override:
        return Path(override)
    return instance_path("sudo_relay", 0)


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


def audit_record(command: str, returncode, stdout: str, stderr: str, *, now: datetime,
                 rid: str | None = None) -> dict:
    """Assemble the six-field record of truth. stdout/stderr kept FULL (Law 7).

    ``rid`` is the id the request was submitted under; the record carries it so the result,
    the audit entry and the request are one id."""
    return {
        "id": rid or _mint_id(now),
        "date": now.isoformat(timespec="seconds"),
        "command": command,
        "returncode": returncode,      # int, or None if the run could not complete
        "stdout": stdout,
        "stderr": stderr,
    }


def write_audit(record: dict, *, now: datetime, retention_days: int = DEFAULT_RETENTION_DAYS) -> Path:
    """Write ``record`` to the audit folder as an immutable JSON, then cycle the window.

    (Named ``emit`` until 2026-07-27 — a homonym of DiagnosticBase's device surface that
    let this component pass the silent_device sweep on the word alone. This writes a
    RECORD OF TRUTH; ``self.emit`` on the device leaves a diagnostic breadcrumb — Law 7's
    two kinds, so neither answers for the other, and they no longer share a name.)

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


def _write_json(path: Path, obj: dict) -> None:
    """Write whole or not at all: a reader never sees half a request or half a result."""
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(obj))
    os.replace(tmp, path)


def submit(command: str, *, timeout_s: float = 120.0) -> str:
    """Client side (CC): mint the request's id, mark it awaited, write the pending request.

    Returns the id — the only handle ``await_result`` takes, so a client can never be handed
    a result it did not ask for."""
    rdir = relay_dir()
    _ensure(rdir, rdir / _AWAITING)
    rid = _mint_id(datetime.now(timezone.utc))
    (rdir / _AWAITING / rid).touch()
    _write_json(rdir / _PENDING, {"id": rid, "command": command, "timeout_s": timeout_s})
    return rid


def process_pending(executor, *, now: datetime, retention_days: int = DEFAULT_RETENTION_DAYS):
    """One daemon iteration: pick up a pending command, run it via ``executor``, write the
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
    request = json.loads(executing.read_text())
    command, timeout_s = request["command"], request["timeout_s"]

    # The request's own timeout, never the executor's default (ticket ae25d8fae5cb).
    returncode, stdout, stderr = executor(command, timeout=timeout_s)
    record = audit_record(command, returncode, stdout, stderr, now=now, rid=request["id"])
    write_audit(record, now=now, retention_days=retention_days)

    # The client's return: the full record, under the request's own id.
    _ensure(rdir / _RESULTS)
    _write_json(rdir / _RESULTS / f"{record['id']}.json", record)
    executing.unlink(missing_ok=True)
    return record


def await_result(rid: str, *, timeout: float = 120.0, poll: float = 0.1) -> dict:
    """Client side (CC): block until request ``rid``'s own result appears, consume and return it.

    Reads ONLY ``results/<rid>.json`` — another request's result is never this one's. Raises
    ``TimeoutError`` naming ``rid`` if no daemon answers inside ``timeout`` — a missing daemon
    is a loud failure, not a silent hang, and the request stops being awaited (a result that
    lands later is an orphan, read loudly by ``orphaned_results``).
    """
    rdir = relay_dir()
    result = rdir / _RESULTS / f"{rid}.json"
    marker = rdir / _AWAITING / rid
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if result.exists():
            record = json.loads(result.read_text())
            result.unlink(missing_ok=True)
            marker.unlink(missing_ok=True)
            return record
        time.sleep(poll)
    marker.unlink(missing_ok=True)
    raise TimeoutError(
        f"no result for request {rid} after {timeout}s — is the sudo_relay daemon running? "
        f"(start: python3 cairn/devices/sudo_relay/daemon.py)"
    )


def request_root(command: str, *, timeout: float = 120.0) -> dict:
    """The full client call CC makes: submit a command, wait, return its audit record.

    Requires Akien's daemon to be running (his one act). The returned record is also the
    permanent audit entry — the same JSON, in the folder, for a month.
    """
    rid = submit(command, timeout_s=timeout)
    return await_result(rid, timeout=timeout + _AWAIT_GRACE_S)


def orphaned_results() -> list[str]:
    """The ids of results nobody is waiting for: ``results/<id>.json`` with no awaiting
    marker, plus the id inside a legacy ``relay/done`` an old daemon left. Read, never deleted
    — an uncollected result is a record of truth (Law 7)."""
    rdir = relay_dir()
    found: list[str] = []
    rsdir = rdir / _RESULTS
    if rsdir.exists():
        for f in sorted(rsdir.glob("*.json")):
            if not (rdir / _AWAITING / f.stem).exists():
                found.append(f.stem)
    legacy = rdir / _LEGACY_DONE
    if legacy.exists():
        try:
            found.append(str(json.loads(legacy.read_text())["id"]))
        except (json.JSONDecodeError, KeyError, TypeError, OSError):
            found.append(_LEGACY_DONE)  # unreadable is still a leftover — named, not hidden
    return found


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

    Pure so it is provable without a running daemon. The absolute cap is the intent —
    'log in once a day' — and by default the SOLE automatic release: one password lasts up
    to a full day of use, no re-login on a walk-away (the dedicated box is the safety net,
    not a timeout). The idle timeout is opt-in: when ``idle_timeout_s`` is None it never
    fires; set it to a number for a stop-sooner rule.
    """
    if (now - started_at).total_seconds() >= max_lifetime_s:
        return True, f"absolute cap reached ({max_lifetime_s}s since start)"
    if idle_timeout_s is not None and (now - last_activity).total_seconds() >= idle_timeout_s:
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
        # None when there is no idle timeout (the default) — the hard cap is then the only deadline.
        "idle_expires_at": (last_activity + timedelta(seconds=idle_timeout_s)).isoformat(timespec="seconds")
        if idle_timeout_s is not None else None,
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
        record = request_root(command, timeout=timeout)
        # GATE CONTACT (DiagnosticBase): a command CROSSED to root and its record came back —
        # per crossing, never per pulse. Emitted AFTER the round-trip lands, so the breadcrumb
        # describes a crossing that happened; a missing daemon raises before this line (loud,
        # no phantom breadcrumb). Thin: pointer is the audit record's id (the record of truth
        # carries command + full stdout/stderr — Law 7's other kind; the breadcrumb never
        # duplicates it); values carry the one fact worth reading without following the
        # pointer. state()/settings() emit nothing — a read crosses no boundary.
        self.emit("request_root", pointer=record["id"],
                  values={"returncode": record["returncode"]})
        # A result nobody collected is a finding, said on the crossing that found it (Law 7):
        # one breadcrumb naming them all, emitted only when there is one.
        orphans = orphaned_results()
        if orphans:
            self.emit("orphaned_results", pointer=orphans[0], values={"orphans": orphans})
        return record

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
            "orphaned_results": orphaned_results(),  # results nobody collected — loud, never deleted
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
