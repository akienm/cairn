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
  - THE CROSSING IS NO LONGER SILENT. request_root leaves ONE diagnostic breadcrumb per
    round-trip, pointing at the audit record — the audit trail (record of truth) and the
    device breadcrumb (diagnostic) are Law 7's two kinds; neither answers for the other.
  - A REQUEST GETS BACK ONLY ITS OWN RESULT (ticket ae25d8fae5cb). a leftover result on disk
    is never handed to the next request — a relay that returned it would report a command
    that never ran as rc 0; an unanswered request times out rather than taking another's;
    the daemon runs under the request's own timeout; a leftover is a loud finding in
    state() and a breadcrumb, never returned and never deleted.

    python3 cairn/devices/sudo_relay/proofs/test_sudo_relay.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.core_values import CoreValuesMixin
from cairn.devices.sudo_relay import relay
from cairn.devices.sudo_relay.relay import AUDIT_FIELDS, SudoRelayDevice
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

_NOW = datetime(2026, 7, 18, 12, 0, 0)

PROVES = {
    "ae25d8fae5cb": {
        "1": "test_a_leftover_result_is_never_returned",
        "2": "test_an_unanswered_request_times_out_rather_than_taking_anothers",
        "3": "test_the_daemon_runs_under_the_requests_timeout",
        "4": "test_an_orphan_is_a_loud_finding",
    },
}


def _fresh_instance() -> str:
    """A scratch instance dir, wired via env so nothing touches real instance-space."""
    d = str(scratch_dir("sudo_relay_proof_"))
    os.environ["CAIRN_SUDO_RELAY_DIR"] = d
    return d


def _daemon_thread() -> threading.Thread:
    """A one-iteration 'daemon': poll process_pending until a submitted command lands, so a
    request_root exercises its REAL round-trip (submit → execute → result → record)."""
    def _once():
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if relay.process_pending(relay.local_executor, now=_NOW) is not None:
                return
            time.sleep(0.02)

    t = threading.Thread(target=_once)
    t.start()
    return t


def _plant_leftovers() -> tuple[list, list]:
    """Two results nobody collected: the old daemon's single-slot ``relay/done`` and an
    abandoned request's ``results/<id>.json``. Returns (their ids, their paths)."""
    rdir = Path(os.environ["CAIRN_SUDO_RELAY_DIR"]) / "relay"
    (rdir / "results").mkdir(parents=True, exist_ok=True)
    stale = {"id": "20261006T120000_000000_1", "date": "2026-10-06T12:00:00",
             "command": "echo A-yesterday", "returncode": 0, "stdout": "A-yesterday\n", "stderr": ""}
    abandoned = dict(stale, id="20261006T130000_000000_2", command="echo B-abandoned",
                     stdout="B-abandoned\n")
    legacy = rdir / "done"
    legacy.write_text(json.dumps(stale))
    orphan = rdir / "results" / f"{abandoned['id']}.json"
    orphan.write_text(json.dumps(abandoned))
    return [stale["id"], abandoned["id"]], [legacy, orphan]


def test_protocol_runs_the_command_and_returns_the_truth():
    _fresh_instance()
    # Client submits; the daemon's one iteration runs it via the NON-root executor.
    rid = relay.submit("echo out-line; echo err-line 1>&2; exit 7")
    record = relay.process_pending(relay.local_executor, now=_NOW)

    assert record is not None, "a pending command must be picked up"
    assert record["returncode"] == 7, "the exit code must propagate, not be laundered to 0"
    assert "out-line" in record["stdout"], "stdout must be captured"
    assert "err-line" in record["stderr"], "stderr must be captured"

    # And the client's await side consumes the same record, by the id submit minted.
    back = relay.await_result(rid, timeout=2.0)
    assert back["returncode"] == 7 and back["id"] == record["id"] == rid


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
    relay.write_audit(old, now=_NOW - timedelta(days=40), retention_days=31)
    # Writing the recent one at _NOW triggers the sweep against a 31-day window.
    relay.write_audit(recent, now=_NOW, retention_days=31)

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
    # The hard cap is the intent ('log in once a day') and the SOLE automatic release.
    expire, why = relay.should_expire(start, _NOW, _NOW + timedelta(hours=25), max_lifetime_s=24 * 3600)
    assert expire and "absolute cap" in why
    # By DEFAULT there is NO idle timeout: a long walk-away does NOT release root before the
    # cap — one login lasts the day (the dedicated box is the safety net, not a timeout).
    expire, _ = relay.should_expire(start, start, _NOW + timedelta(hours=12))  # 12h idle, under the cap
    assert not expire, "with no idle timeout (the default), only the hard cap releases root"
    # The idle timeout is OPT-IN: when a number is set, it still fires (the stop-sooner knob).
    expire, why = relay.should_expire(start, start, _NOW + timedelta(minutes=31), idle_timeout_s=30 * 60)
    assert expire and "idle" in why
    # Fresh and within the cap → hold.
    expire, _ = relay.should_expire(start, _NOW + timedelta(minutes=5), _NOW + timedelta(minutes=6))
    assert not expire, "a fresh daemon within the cap must not expire — root survives a live session"


def test_the_window_is_visible_and_honest():
    _fresh_instance()
    # No daemon → not live, and it says why (never a silent 'unknown').
    s = relay.daemon_status()
    assert s["live"] is False and "not running" in s["reason"]

    # A live pid (this process) reads live and exposes the deadline. The hard cap (once-a-day)
    # is always visible; by default there is no idle deadline, and the window says so honestly.
    relay.write_status(pid=os.getpid(), started_at=_NOW, last_activity=_NOW, now=_NOW)
    s = relay.daemon_status()
    assert s["live"] is True
    assert s["hard_expires_at"] is not None, "the once-a-day deadline must always be visible"
    assert s["idle_expires_at"] is None, "no idle timeout by default — the window says so, not a fake deadline"

    # A dead pid reads stale, never laundered into 'up' (Law 3: measured, not assumed).
    relay.write_status(pid=2_000_000_000, started_at=_NOW, last_activity=_NOW, now=_NOW)
    s = relay.daemon_status()
    assert s["live"] is False and "stale" in s["reason"]


def test_the_crossing_is_no_longer_silent():
    """The silent_device disposition (troubles/silent-devices-2026-07-27.json): the ruling
    is the DEFAULT — every device speaks the common discipline; the audit trail did not
    answer for the device surface because they are Law 7's two different kinds (record of
    truth vs diagnostic breadcrumb). One breadcrumb per round-trip, pointing at the audit
    record; SILENCED here so the crossings hold and this proof can read them.

    The silencing is not decoration (ticket a-device-logs-without-being-wired, 2026-08-18): an
    un-wired device now WRITES its trail to ~/.cairn/logs/sudo_relay/0/ rather than holding it,
    so without this line the list below is empty AND the live tree gains a trail written by a
    proof. Holding is now asked for; it used to be the accident of nobody assembling the device."""
    import threading

    _fresh_instance()
    dev = SudoRelayDevice()
    dev.set_diagnostic_receiver(None)
    assert dev.held_diagnostics() == [], "construction is not a crossing"

    # A one-iteration 'daemon': poll process_pending until the submitted command lands,
    # so request_root exercises its REAL round-trip (submit → execute → done → record).
    def _daemon_once():
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if relay.process_pending(relay.local_executor, now=_NOW) is not None:
                return
            time.sleep(0.02)

    t = threading.Thread(target=_daemon_once)
    t.start()
    try:
        record = dev.request_root("echo crossed; exit 3", timeout=10.0)
    finally:
        t.join()

    held = dev.held_diagnostics()
    assert [h["gate"] for h in held] == ["request_root"], (
        f"exactly ONE breadcrumb per round-trip, got {[h['gate'] for h in held]} — more is "
        "the firehose the discipline forbids, fewer is the silence the inspector reds"
    )
    crumb = held[0]
    assert crumb["pointer"] == record["id"], \
        "the breadcrumb points at the audit record — the diagnostic ties to the record of truth"
    assert crumb["values"] == {"returncode": 3}, \
        "thin values: the one fact worth reading without following the pointer"
    assert crumb["home"] == "held", \
        "a silenced device HOLDS the breadcrumb (Law 7) — never silently dropped"
    # Reads are not crossings: the surface emits nothing.
    dev.state(), dev.settings()
    assert len(dev.held_diagnostics()) == 1, "state()/settings() must not emit — no crossing"


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


def test_a_leftover_result_is_never_returned():
    """(1) Measured before this tooth existed: a leftover result was handed to the next
    request as its own, so a command that never ran read rc 0 (ticket ae25d8fae5cb)."""
    _fresh_instance()
    ids, paths = _plant_leftovers()
    t = _daemon_thread()
    try:
        record = relay.request_root("echo mine", timeout=10.0)
    finally:
        t.join()
    assert record["command"] == "echo mine", (
        f"the request got back {record['command']!r} — another request's result, not its own"
    )
    assert record["stdout"] == "mine\n" and record["id"] not in ids
    assert all(p.exists() for p in paths), "a leftover is a record of truth — never consumed or deleted"


def test_an_unanswered_request_times_out_rather_than_taking_anothers():
    """(2) No daemon answers: the request raises TimeoutError, it does not take a leftover."""
    _fresh_instance()
    ids, paths = _plant_leftovers()
    try:
        record = relay.request_root("echo nobody-runs-this", timeout=0.5)
    except TimeoutError:
        pass
    else:
        raise AssertionError(
            f"an unanswered request returned {record.get('command')!r} — it must time out instead"
        )
    assert all(p.exists() for p in paths), "a leftover is a record of truth — never consumed or deleted"


def test_the_daemon_runs_under_the_requests_timeout():
    """(3) The daemon runs the executor under the timeout the request asked for, and a command
    the daemon timed out still comes home as its own honest record."""
    _fresh_instance()
    seen = {}

    def recording(command, *, timeout=None):
        seen["timeout"] = timeout
        return 0, "", ""

    relay.submit("echo timed", timeout_s=7)
    relay.process_pending(recording, now=_NOW)
    assert seen.get("timeout") == 7, f"the executor ran under {seen.get('timeout')!r}, not the request's 7s"

    dev = SudoRelayDevice()
    dev.set_diagnostic_receiver(None)
    t = _daemon_thread()
    try:
        slow = dev.request_root("sleep 3", timeout=1)
    finally:
        t.join()
    assert slow["returncode"] is None, f"a timed-out run must read rc None, got {slow['returncode']!r}"
    assert "[sudo_relay] timed out after 1s" in slow["stderr"], slow["stderr"]

    t = _daemon_thread()
    try:
        quick = dev.request_root("sleep 0.2", timeout=10)
    finally:
        t.join()
    assert quick["returncode"] == 0, f"inside its timeout the run must complete, got {quick!r}"


def test_an_orphan_is_a_loud_finding():
    """(4) A result nobody collected is read in state() and named by a breadcrumb on the next
    request — loud, never returned, never deleted (Law 7)."""
    _fresh_instance()
    ids, paths = _plant_leftovers()
    dev = SudoRelayDevice()
    dev.set_diagnostic_receiver(None)
    orphans = dev.state().get("orphaned_results")
    assert orphans is not None and sorted(orphans) == sorted(ids), (
        f"state() must list every uncollected result, got {orphans!r}"
    )
    t = _daemon_thread()
    try:
        record = dev.request_root("echo after", timeout=10.0)
    finally:
        t.join()
    assert record["command"] == "echo after"
    held = dev.held_diagnostics()
    assert [h["gate"] for h in held] == ["request_root", "orphaned_results"], (
        f"the round-trip and then the orphans it found, got {[h['gate'] for h in held]}"
    )
    assert sorted(held[1]["values"]["orphans"]) == sorted(ids), held[1]
    assert all(p.exists() for p in paths), "a leftover is a record of truth — never consumed or deleted"


def _main() -> int:
    checks = [
        test_protocol_runs_the_command_and_returns_the_truth,
        test_idle_when_nothing_pending,
        test_record_is_permanent_and_complete,
        test_folder_cycles_after_a_month_but_not_before,
        test_retention_never_touches_a_foreign_file,
        test_temporary_is_physics,
        test_the_window_is_visible_and_honest,
        test_the_crossing_is_no_longer_silent,
        test_device_is_a_device_and_reports_the_window,
        test_a_leftover_result_is_never_returned,
        test_an_unanswered_request_times_out_rather_than_taking_anothers,
        test_the_daemon_runs_under_the_requests_timeout,
        test_an_orphan_is_a_loud_finding,
    ]
    # Every check runs and prints its own verdict: one red does not hide the teeth after it.
    failed = 0
    for check in checks:
        try:
            check()
        except Exception as e:  # noqa: BLE001 — a tooth's failure is its reading, printed whole
            failed += 1
            print(f"  FAILED  {check.__name__}: {type(e).__name__}: {e}")
        else:
            print(f"  PASS  {check.__name__}")
    if failed:
        print(f"red — sudo_relay: {failed} of {len(checks)} teeth failed")
        return 1
    print("green — sudo_relay: command in, root-run + permanent audit out; each request gets back only its own "
          "result; window visible, temporary by physics")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
