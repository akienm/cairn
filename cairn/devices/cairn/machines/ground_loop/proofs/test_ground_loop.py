"""Proof for ground_loop — THE HEARTBEAT's records: its liveness stamp, its single-start
guard, and its page.

The beat itself is ``__main__.py`` (proved in test_heartbeat.py). Since ticket efb670ff1dd8
there is no in-process loop device to beat: these teeth write the liveness record through the
tool's own write face (``write_liveness``), read it back through the read face, and assemble
the heartbeat's page — a template over that record — through the standard shim machinery.

Teeth a hollow build could not pass:
  - THE STAMP ADVANCES, the pid and state ride, the instance dir is born on first write.
  - LIVE on fresh, DEAD on stale / absent / torn — and a reader never sees a torn record.
  - EXACTLY ONE CLAIMANT WINS the singleton; a corpse leaves no stale claim.
  - THE PANE RENDERS WHAT THE RECORD SAYS and never derives; an absent record is a named lack.
  - THE PAGE ASSEMBLES through the real ``BaseShim.active_page``.

Runnable bare (NO DB, NO framework):
    python3 cairn/devices/cairn/machines/ground_loop/proofs/test_ground_loop.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


PROVES = {"bae622881f03": {"7": "test_the_doors_loser_reports_from_the_record_and_exits_distinctly"}}


# --- the liveness record (ticket ground-loop-writes-its-own-liveness) ----------
# The loop, while actually running, writes a record in its own device space on
# each pass — last-run, state, pid — atomically; the read face answers LIVE/DEAD
# at the ruled 5s threshold. All teeth run against an INJECTED scratch home and
# injected nows: nothing here touches ~/.cairn or a wall clock.

import json as _json
import os as _os
import tempfile as _tempfile
import threading as _threading
from datetime import datetime as _dt, timedelta as _td, timezone as _tz

from cairn.tools.liveness.liveness import (
    RECORD_NAME, STALENESS_THRESHOLD_S, read_liveness, write_liveness,
)

_T0 = _dt(2026, 8, 9, 12, 0, 0, tzinfo=_tz.utc)


def test_the_stamp_advances_across_beats_and_pid_and_state_ride():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        write_liveness(_T0, {"beats": 1}, _os.getpid(), home)
        first = read_liveness(_T0, home=home)
        assert first["verdict"] == "LIVE" and first["age_s"] == 0.0
        assert first["record"]["last_run"] == _T0.isoformat(), \
            "last-run is THIS beat's injected now — the write is part of the pass"

        t1 = _T0 + _td(seconds=1)
        write_liveness(t1, {"beats": 2}, _os.getpid(), home)
        second = read_liveness(t1, home=home)
        assert second["record"]["last_run"] == t1.isoformat(), \
            "the stamp ADVANCES while the loop runs — the falsifier's first clause"
        assert second["record"]["pid"] == _os.getpid(), "the pid rides the record"
        assert second["record"]["state"] == {"beats": 2}, \
            "the state riding the record is the state the writer handed it, post-pass"


def test_the_instance_dir_is_born_on_first_write():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "devices" / "ground_loop" / "0"   # does not exist yet
        assert not home.exists()
        write_liveness(_T0, {"beats": 1}, _os.getpid(), home)
        assert (home / RECORD_NAME).exists(), \
            "the device space is born with its first record — no separate mkdir step to forget"


def test_dead_on_stale_live_on_fresh_dead_on_absent_or_torn():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        # Absent — never ran — is a DEAD verdict with the lack named, not an exception.
        gone = read_liveness(_T0, home=home)
        assert gone["verdict"] == "DEAD" and gone["record"] is None and "lack" in gone

        write_liveness(_T0, {"beats": 1}, _os.getpid(), home)
        fresh = read_liveness(_T0 + _td(seconds=3), home=home)
        assert fresh["verdict"] == "LIVE" and fresh["age_s"] == 3.0, \
            "within the ruled threshold → LIVE (a second loop must NOT start over a live one)"
        stale = read_liveness(_T0 + _td(seconds=STALENESS_THRESHOLD_S + 1), home=home)
        assert stale["verdict"] == "DEAD", \
            "past the ruled threshold → DEAD, whatever the file says — the crashed loop " \
            "leaves the file behind but stops advancing the stamp; that is the whole detector"
        assert stale["record"]["pid"] == _os.getpid(), \
            "the record returns WHOLE beside the DEAD verdict — the reader sees what the corpse said"

        # Garbage at the read path is DEAD with the lack named, never a raise.
        (home / RECORD_NAME).write_text("{torn")
        torn = read_liveness(_T0, home=home)
        assert torn["verdict"] == "DEAD" and "lack" in torn


def test_a_reader_never_sees_a_torn_record():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        write_liveness(_T0, {"beats": 1}, 111, home)

        # A writer that dies MID-WRITE (before the rename) leaves the OLD record whole:
        # the temp never stands at the read path, so there is no torn state to see.
        real_replace = _os.replace
        def _crash(src, dst):
            raise OSError("simulated crash between temp-write and rename")
        _os.replace = _crash
        try:
            try:
                write_liveness(_T0 + _td(seconds=1), {"beats": 2}, 222, home)
                raise AssertionError("the simulated crash must surface loudly (Law 7)")
            except OSError:
                pass
        finally:
            _os.replace = real_replace
        survivor = _json.loads((home / RECORD_NAME).read_text())
        assert survivor["pid"] == 111, "the interrupted write left the OLD record intact, whole"
        assert [p.name for p in home.iterdir()] == [RECORD_NAME], \
            "no temp debris stands beside the record — the failed write cleaned itself"

        # And under a live hammer — one thread writing, this thread reading — every
        # read parses: old or new, never partial (os.replace is atomic on one fs).
        def _hammer():
            for i in range(200):
                write_liveness(_T0 + _td(seconds=i), {"beats": i}, _os.getpid(), home)
        w = _threading.Thread(target=_hammer)
        w.start()
        while w.is_alive():
            _json.loads((home / RECORD_NAME).read_text())   # a torn record raises here
        w.join()
        _json.loads((home / RECORD_NAME).read_text())


# --- the single-start guard (ticket an-entry-point-starts-the-loop-only-once) ---
# Read-then-act is not atomic: two entry points can both read DEAD inside the
# same 5s window. So the claim is ONE syscall — flock, held for life, kernel-
# released on death — and these teeth are ADVERSARIAL: real processes contend,
# exactly one wins, the loser is loud, and a corpse leaves nothing stale.

import subprocess as _subprocess
import time as _time

from cairn.devices.cairn.machines.ground_loop.guard import LOCK_NAME, claim_singleton
# EXIT_ALREADY_RUNNING is read at call time (below), never bound here: the heartbeat
# rewrite (bae622881f03) is what this module imports, and a proof that crashes at import when
# its subject is reverted prints no teeth for the hollow reading to count.

_CLAIMANT = (
    "import sys, time\n"
    "from pathlib import Path\n"
    "from cairn.devices.cairn.machines.ground_loop.guard import ClaimRefused, claim_singleton\n"
    "try:\n"
    "    claim = claim_singleton(Path(sys.argv[1]))\n"
    "except ClaimRefused:\n"
    "    print('LOST', flush=True); sys.exit(3)\n"
    "print('WON', flush=True)\n"
    "time.sleep(15)\n"
)


def _spawn_claimant(home):
    env = dict(_os.environ, PYTHONPATH=str(_REPO_ROOT))
    return _subprocess.Popen([sys.executable, "-c", _CLAIMANT, str(home)],
                             stdout=_subprocess.PIPE, stderr=_subprocess.PIPE,
                             env=env, text=True)


def test_two_claimants_exactly_one_wins_and_the_loser_refuses_loudly():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        a, b = _spawn_claimant(home), _spawn_claimant(home)
        # A generous ceiling so a loaded box cannot flake this: the loser must
        # REFUSE (never block) well inside it.
        deadline = _time.time() + 10
        loser = None
        while _time.time() < deadline and loser is None:
            for p in (a, b):
                if p.poll() is not None:
                    loser = p
            if loser is None:
                _time.sleep(0.05)
        assert loser is not None, \
            "one claimant must lose within the bound — a blocked (or doubly-won) race is the defect"
        winner = b if loser is a else a
        assert winner.poll() is None, "exactly ONE winner — the other still holds its claim"
        out, _ = loser.communicate(timeout=5)
        assert loser.returncode == 3 and out.strip() == "LOST", \
            "the loser's refusal is loud and typed — nonzero, distinct, never a silent exit"
        winner.kill()
        winner.wait(timeout=5)


def test_a_sigkilled_winner_leaves_no_stale_claim():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        holder = _spawn_claimant(home)
        assert holder.stdout.readline().strip() == "WON"
        holder.kill()                      # SIGKILL — no cleanup code runs, by design
        holder.wait(timeout=5)
        claim = claim_singleton(home)      # must win IMMEDIATELY: no break-the-claim dance,
        claim.release()                    # no staleness protocol — the kernel released it
        assert (home / LOCK_NAME).exists(), \
            "the leftover lock file is INERT, not stale — only the held flock ever meant anything"


def test_the_held_claim_survives_the_records_churn():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        claim = claim_singleton(home)
        for i in range(50):                # the beat's os.replace churns liveness.json's inode
            write_liveness(_T0 + _td(seconds=i), {"beats": i}, _os.getpid(), home)
        contender = _spawn_claimant(home)
        contender.communicate(timeout=10)
        assert contender.returncode == 3, \
            "the claim rides its own file's inode — 50 record replaces cannot shake it loose"
        claim.release()
        after = _spawn_claimant(home)
        assert after.stdout.readline().strip() == "WON", "released → the very next claimant wins"
        after.kill()
        after.wait(timeout=5)


def test_the_doors_loser_reports_from_the_record_and_exits_distinctly():
    door = ("import sys\n"
            "from pathlib import Path\n"
            "from cairn.devices.cairn.machines.ground_loop.__main__ import main\n"
            "sys.exit(main(Path(sys.argv[1])))\n")
    env = dict(_os.environ, PYTHONPATH=str(_REPO_ROOT))
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        claim = claim_singleton(home)
        # A LIVE record behind the held claim: the loser names pid and age FROM THE
        # RECORD (the owned answer, Law 6) — the one tooth that must ride the wall
        # clock, because main() does; the 5s window is generous against startup cost.
        write_liveness(_dt.now(_tz.utc).astimezone(), {"beats": 4}, 4242, home)
        loser = _subprocess.run([sys.executable, "-c", door, str(home)],
                                capture_output=True, text=True, timeout=10, env=env)
        from cairn.devices.cairn.machines.ground_loop.__main__ import EXIT_ALREADY_RUNNING
        assert loser.returncode == EXIT_ALREADY_RUNNING == 3, \
            "the door's loser exits DISTINCTLY — not 1 (a crash), not 0 (a lie)"
        assert "refusing to start a second loop" in loser.stderr
        assert "4242" in loser.stderr, \
            "the loser reports what the RECORD said (pid), never a process-table scan"
        # A STALE record behind a still-held claim — the newcomer TRIES to take over
        # (arbitration says "takeover"), kills the pid (which fails — 4242 is not real),
        # attempts reclaim (fails — the lock is still held), and exits ALREADY_RUNNING.
        # The core invariant holds: no second loop starts while the claim is held.
        write_liveness(_dt.now(_tz.utc).astimezone() - _td(seconds=STALENESS_THRESHOLD_S + 60),
                       {"beats": 4}, 4242, home)
        slow = _subprocess.run([sys.executable, "-c", door, str(home)],
                               capture_output=True, text=True, timeout=10, env=env)
        assert slow.returncode == EXIT_ALREADY_RUNNING
        assert "stale" in slow.stderr.lower(), \
            "the newcomer names the staleness in its refusal"
        claim.release()


# --- the liveness PANE (ticket the-ground-loop-pane-shows-its-state) ------------
# The heartbeat's device page — a declared pane through the base shim's STANDARD
# machinery, never a route or a port of its own. The pane RENDERS what the
# record says: its data IS read_liveness's own output plus one presentation
# label, so it cannot derive, cache, or grow a second staleness opinion.

from cairn.tools.liveness.liveness import liveness_pane_data
from cairn.devices.cairn.machines.ground_loop.shim import GroundLoopShim


def test_the_pane_renders_what_the_record_says_and_never_derives():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        write_liveness(_T0, {"beats": 1}, _os.getpid(), home)
        for probe_now, verdict in ((_T0 + _td(seconds=3), "LIVE"),
                                   (_T0 + _td(seconds=STALENESS_THRESHOLD_S + 1), "DEAD")):
            pane = liveness_pane_data(probe_now, home=home)
            assert {k: v for k, v in pane.items() if k != "reports"} == \
                read_liveness(probe_now, home=home), \
                "the pane's verdict/record/age ARE the read face's own output — render, never derive"
            assert pane["verdict"] == verdict, \
                "LIVE and DEAD both flow from the one ruled threshold at its one address"
            assert "resident singleton" in pane["reports"], \
                "the pane names WHICH loop it reports — the resident record, not the serving process"


def test_an_absent_record_renders_the_named_lack_never_blank():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"                      # no record has ever been written here
        pane = liveness_pane_data(_T0, home=home)
        assert pane["verdict"] == "DEAD" and pane["record"] is None
        assert "no record at" in pane["lack"], \
            "absent is a NAMED lack — never blank, never a last-known-good"


def test_the_page_assembles_through_the_standard_machinery():
    shim = GroundLoopShim()                        # the standard loader contract, no loop handed
    assert type(shim.device()).__name__ == "HeartbeatPage", \
        "the shim starts the heartbeat's read-only page — never a second loop"

    page = shim.active_page()                      # the REAL BaseShim method, unoverridden
    assert page["device"] == "ground_loop"
    kinds = [p["kind"] for p in page["panes"]]
    assert kinds[:2] == ["status", "settings"], \
        "the STATUS/SETTINGS floor first (Form v0 #2, projected free)"
    assert kinds[-1] == "liveness", \
        "the device's declared pane appended last"
    pane = next(p for p in page["panes"] if p["kind"] == "liveness")
    assert pane["label"] == "Liveness" and "absent" not in pane, \
        "the handler answered — read_liveness never raises; an absent record is DATA, not a refusal"
    # The deployed handler reads the RESIDENT record (the wall clock, the real home),
    # so this tooth pins INVARIANTS, never a snapshot: a verdict either way, the lack
    # named exactly when the record is absent, the reports label riding.
    data = pane["data"]
    assert data["verdict"] in ("LIVE", "DEAD")
    assert data["record"] is not None or "no record at" in data["lack"]
    assert "resident singleton" in data["reports"]


def _main() -> int:
    for check in (test_the_stamp_advances_across_beats_and_pid_and_state_ride,
                  test_the_instance_dir_is_born_on_first_write,
                  test_dead_on_stale_live_on_fresh_dead_on_absent_or_torn,
                  test_a_reader_never_sees_a_torn_record,
                  test_two_claimants_exactly_one_wins_and_the_loser_refuses_loudly,
                  test_a_sigkilled_winner_leaves_no_stale_claim,
                  test_the_held_claim_survives_the_records_churn,
                  test_the_doors_loser_reports_from_the_record_and_exits_distinctly,
                  test_the_pane_renders_what_the_record_says_and_never_derives,
                  test_an_absent_record_renders_the_named_lack_never_blank,
                  test_the_page_assembles_through_the_standard_machinery):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — ground_loop: the liveness record, the single-start guard and the "
          "heartbeat's page hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
