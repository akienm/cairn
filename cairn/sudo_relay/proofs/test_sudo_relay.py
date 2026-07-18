"""Proof for sudo_relay — a command in, a root-run and a permanent audit record out.

Proven UNDER the tester's discipline and WITHOUT root: the protocol runs through the
injected ``local_executor`` seam, so the whole thing — pending → executing → done, the
audit record, the rolling-month retention, the expiry decision, the visible window — is
green with a non-root payload. Root itself never enters the test; the daemon (the one
privileged part) is a thin wrapper over exactly this proven code.

Hermetic: every test runs against a scratch ``CAIRN_SUDO_RELAY_DIR``, so real
instance-space and real audit truth are never touched.

Teeth a hollow relay could not pass:
  - THE COMMAND RUNS AND THE RESULT IS TRUE. exit code, stdout, stderr all propagate; a
    relay that lost the exit code or dropped stderr trips this.
  - THE RECORD IS PERMANENT AND COMPLETE (Law 7). exactly the six fields; stdout kept FULL,
    not tailed — a relay that truncated the error trips this.
  - THE FOLDER CYCLES AFTER A MONTH — and not before. an over-a-month record is pruned; a
    recent one survives; a foreign file is never touched.
  - TEMPORARY IS PHYSICS. past the absolute cap → expire; idle past the timeout → expire;
    fresh and active → do not — a daemon that could hold root forever trips this.
  - THE WINDOW IS VISIBLE AND HONEST. a live pid reads live; a dead pid reads stale, never
    laundered into 'up' (Law 3).

    python3 cairn/sudo_relay/proofs/test_sudo_relay.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CoreValuesMixin
from cairn.sudo_relay import relay
from cairn.sudo_relay.relay import AUDIT_FIELDS, SudoRelayDevice

_NOW = datetime(2026, 7, 18, 12, 0, 0)


def _fresh_instance() -> str:
    """A scratch instance dir, wired via env so nothing touches real instance-space."""
    d = tempfile.mkdtemp(prefix="sudo_relay_proof_")
    os.environ["CAIRN_SUDO_RELAY_DIR"] = d
    return d


def test_protocol_runs_the_command_and_returns_the_truth():
    _fresh_instance()
    # Client submits; the daemon's one iteration runs it via the NON-root executor.
    relay.submit("echo out-line; echo err-line 1>&2; exit 7")
    record = relay.process_pending(relay.local_executor, now=_NOW)

    assert record is not None, "a pending command must be picked up"
    assert record["returncode"] == 7, "the exit code must propagate, not be laundered to 0"
    assert "out-line" in record["stdout"], "stdout must be captured"
    assert "err-line" in record["stderr"], "stderr must be captured"

    # And the client's await side consumes the same record from `done`.
    back = relay.await_result(timeout=2.0)
    assert back["returncode"] == 7 and back["id"] == record["id"]


def test_idle_when_nothing_pending():
    _fresh_instance()
    assert relay.process_pending(relay.local_executor, now=_NOW) is None


def test_record_is_permanent_and_complete():
    _fresh_instance()
    big = "x" * 10000  # a record of truth keeps the whole thing (Law 7) — not a tail.
    relay.submit(f"printf %s '{big}'")
    record = relay.process_pending(relay.local_executor, now=_NOW)

    assert set(record) == set(AUDIT_FIELDS), f"exactly the six fields; got {sorted(record)}"
    assert len(record["stdout"]) == len(big), "stdout must be stored FULL, never truncated (Law 7)"

    # It landed on disk as an immutable JSON and round-trips.
    import json
    files = list(relay.audit_dir().glob("*.json"))
    assert len(files) == 1, "the run must leave exactly one audit record"
    on_disk = json.loads(files[0].read_text())
    assert on_disk == record, "the durable record must equal what was returned"


def test_folder_cycles_after_a_month_but_not_before():
    _fresh_instance()
    # An old record (40 days ago) and a recent one (yesterday) written directly.
    old = relay.audit_record("old-cmd", 0, "", "", now=_NOW - timedelta(days=40))
    recent = relay.audit_record("recent-cmd", 0, "", "", now=_NOW - timedelta(days=1))
    relay.emit(old, now=_NOW - timedelta(days=40), retention_days=31)
    # Emitting the recent one at _NOW triggers the sweep against a 31-day window.
    relay.emit(recent, now=_NOW, retention_days=31)

    stems = {f.stem for f in relay.audit_dir().glob("*.json")}
    assert recent["id"] in stems, "a within-the-month record must survive"
    assert old["id"] not in stems, "an over-a-month record must cycle out"


def test_retention_never_touches_a_foreign_file():
    _fresh_instance()
    relay._ensure(relay.audit_dir())
    foreign = relay.audit_dir() / "not-ours.json"
    foreign.write_text("{}")
    relay.prune_audit(now=_NOW, retention_days=31)
    assert foreign.exists(), "the sweep must never delete a file it did not mint (Law 7)"


def test_temporary_is_physics():
    start = _NOW
    active = _NOW
    # Past the absolute cap → expire, even if active.
    expire, why = relay.should_expire(start, _NOW, _NOW + timedelta(hours=25), max_lifetime_s=24 * 3600)
    assert expire and "absolute cap" in why
    # Idle past the timeout → expire.
    expire, why = relay.should_expire(start, active, _NOW + timedelta(minutes=31), idle_timeout_s=30 * 60)
    assert expire and "idle" in why
    # Fresh and recently active → hold.
    expire, _ = relay.should_expire(start, _NOW + timedelta(minutes=5), _NOW + timedelta(minutes=6))
    assert not expire, "a fresh, active daemon must not expire — root survives a live session"


def test_the_window_is_visible_and_honest():
    _fresh_instance()
    # No daemon → not live, and it says why (never a silent 'unknown').
    s = relay.daemon_status()
    assert s["live"] is False and "not running" in s["reason"]

    # A live pid (this process) reads live and exposes both deadlines.
    relay.write_status(pid=os.getpid(), started_at=_NOW, last_activity=_NOW, now=_NOW)
    s = relay.daemon_status()
    assert s["live"] is True
    assert "hard_expires_at" in s and "idle_expires_at" in s, "the window must be visible"

    # A dead pid reads stale, never laundered into 'up' (Law 3: measured, not assumed).
    relay.write_status(pid=2_000_000_000, started_at=_NOW, last_activity=_NOW, now=_NOW)
    s = relay.daemon_status()
    assert s["live"] is False and "stale" in s["reason"]


def test_device_is_a_device_and_reports_the_window():
    _fresh_instance()
    dev = SudoRelayDevice()
    # The base's composition tooth: a device carries CP1-CP6, in order (Law 2).
    assert isinstance(dev, CoreValuesMixin), "a device must compose the core values"
    assert [v.id for v in dev.CORE_VALUES] == ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]
    surface = dev.introspect()
    assert list(surface) == ["intention", "state", "settings", "other"], "Form v0 #2 order"
    assert "daemon" in surface["state"], "state must surface the visible root window"
    assert surface["settings"]["max_lifetime_s"] == relay.DEFAULT_MAX_LIFETIME_S


def _main() -> int:
    checks = [
        test_protocol_runs_the_command_and_returns_the_truth,
        test_idle_when_nothing_pending,
        test_record_is_permanent_and_complete,
        test_folder_cycles_after_a_month_but_not_before,
        test_retention_never_touches_a_foreign_file,
        test_temporary_is_physics,
        test_the_window_is_visible_and_honest,
        test_device_is_a_device_and_reports_the_window,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — sudo_relay: command in, root-run + permanent audit out; window visible, temporary by physics")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
