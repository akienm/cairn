"""Proof for ground_loop — THE HEARTBEAT's records: its beat record, its single-start guard,
its cadence, and its page.

The beat itself is ``__main__.py`` (proved in test_heartbeat.py). These teeth write the beat
record through the loop's own write face (``heartbeat.write_record``), read it back through
its read face (``heartbeat.read_record``), contend for the singleton, and assemble the
heartbeat's page — a template over that record and the held lock — through the standard shim
machinery.

THE STALENESS VERDICT IS RETIRED (ticket 6208d0a27d6e, Q#53; outline 5.6.3 "what it must never
grow back: ... staleness, managers"). The record no longer answers LIVE/DEAD by its age, and a
newcomer no longer takes over from a holder it judges hung. Whether the loop is up is its held
lock (a measurement with no threshold); "is it up?" for a device is the rack's to answer
(5.7.3.5). The teeth that measured the threshold went with it.

Teeth a hollow build could not pass:
  - THE STAMP ADVANCES, the pid and state ride, the instance dir is born on first write.
  - AN ABSENT OR TORN RECORD IS A NAMED LACK, never a raise — and a reader never sees a torn one.
  - EXACTLY ONE CLAIMANT WINS the singleton; a corpse leaves no stale claim.
  - A SECOND LOOP REFUSES WITH NO TAKEOVER, whatever the record's age (6208d0a27d6e clause 6).
  - THE LOOP OWNS ITS CADENCE, 60 s, at its own address (clause 7).
  - THE BASE SHIM PROBES THE SAME LOCK FILE THE GUARD CLAIMS (clause 8).
  - THE PANE RENDERS WHAT THE RECORD AND THE LOCK SAY; the page assembles through
    the real ``BaseShim.active_page``.

Runnable bare (NO DB, NO framework):
    python3 cairn/devices/cairn/machines/ground_loop/proofs/test_ground_loop.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


PROVES = {
    "bae622881f03": {"7": "test_the_doors_loser_reports_from_the_record_and_exits_distinctly"},
    "6208d0a27d6e": {
        "6": "test_a_second_loop_refuses_with_no_takeover",
        "7": "test_the_loop_owns_its_cadence",
        "8": "test_the_shim_probes_the_guards_lock",
    },
}


# --- the beat record ----------------------------------------------------------
# The loop, while running, writes one record in its own device space on each pass —
# last-run, state, pid — atomically. All teeth run against an INJECTED scratch home and
# injected nows: nothing here touches ~/.cairn or a wall clock.

import inspect as _inspect
import json as _json
import os as _os
import tempfile as _tempfile
import threading as _threading
from datetime import datetime as _dt, timedelta as _td, timezone as _tz

from cairn.devices.cairn.machines.ground_loop import heartbeat as _hb

_T0 = _dt(2026, 8, 9, 12, 0, 0, tzinfo=_tz.utc)


def test_the_stamp_advances_across_beats_and_pid_and_state_ride():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        _hb.write_record(_T0, {"beats": 1}, _os.getpid(), home)
        first = _hb.read_record(home, _T0)
        assert first["age_s"] == 0.0 and "lack" not in first
        assert first["record"]["last_run"] == _T0.isoformat(), \
            "last-run is THIS beat's injected now — the write is part of the pass"

        t1 = _T0 + _td(seconds=1)
        _hb.write_record(t1, {"beats": 2}, _os.getpid(), home)
        second = _hb.read_record(home, t1)
        assert second["record"]["last_run"] == t1.isoformat(), "the stamp ADVANCES while the loop runs"
        assert second["record"]["pid"] == _os.getpid(), "the pid rides the record"
        assert second["record"]["state"] == {"beats": 2}, \
            "the state riding the record is the state the writer handed it, post-pass"
        assert "verdict" not in second, "the record carries no staleness verdict (6208d0a27d6e)"


def test_the_instance_dir_is_born_on_first_write():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "devices" / "ground_loop" / "0"   # does not exist yet
        assert not home.exists()
        _hb.write_record(_T0, {"beats": 1}, _os.getpid(), home)
        assert (home / _hb.RECORD_NAME).exists() and _hb.RECORD_NAME == "beat.json", \
            "the device space is born with its first record — no separate mkdir step to forget"


def test_an_absent_or_torn_record_is_a_named_lack():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        gone = _hb.read_record(home, _T0)
        assert gone["record"] is None and "no record at" in gone["lack"], \
            "absent — never ran — is a named lack, not an exception"
        assert not home.exists(), "reading creates nothing"
        _hb.write_record(_T0, {"beats": 1}, _os.getpid(), home)
        later = _hb.read_record(home, _T0 + _td(hours=5))
        assert later["record"]["pid"] == _os.getpid() and later["age_s"] == 5 * 3600.0, \
            "an old record is returned whole with its age — the reader judges nothing"
        assert _hb.read_record(home)["age_s"] is None, "no now given, no age computed"
        (home / _hb.RECORD_NAME).write_text("{torn")
        torn = _hb.read_record(home, _T0)
        assert torn["record"] is None and "lack" in torn, "garbage is a named lack, never a raise"


def test_a_reader_never_sees_a_torn_record():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        _hb.write_record(_T0, {"beats": 1}, 111, home)

        # A writer that dies MID-WRITE (before the rename) leaves the OLD record whole.
        real_replace = _os.replace
        def _crash(src, dst):
            raise OSError("simulated crash between temp-write and rename")
        _os.replace = _crash
        try:
            try:
                _hb.write_record(_T0 + _td(seconds=1), {"beats": 2}, 222, home)
                raise AssertionError("the simulated crash must surface loudly (Law 7)")
            except OSError:
                pass
        finally:
            _os.replace = real_replace
        survivor = _json.loads((home / _hb.RECORD_NAME).read_text())
        assert survivor["pid"] == 111, "the interrupted write left the OLD record intact, whole"
        assert [p.name for p in home.iterdir()] == [_hb.RECORD_NAME], \
            "no temp debris stands beside the record — the failed write cleaned itself"

        def _hammer():
            for i in range(200):
                _hb.write_record(_T0 + _td(seconds=i), {"beats": i}, _os.getpid(), home)
        w = _threading.Thread(target=_hammer)
        w.start()
        while w.is_alive():
            _json.loads((home / _hb.RECORD_NAME).read_text())   # a torn record raises here
        w.join()
        _json.loads((home / _hb.RECORD_NAME).read_text())


# --- the single-start guard ---------------------------------------------------
# The claim is ONE syscall — flock, held for life, kernel-released on death — and these
# teeth are ADVERSARIAL: real processes contend, exactly one wins, the loser is loud, and a
# corpse leaves nothing stale.

import signal as _signal
import subprocess as _subprocess
import time as _time

from cairn.devices.cairn.machines.ground_loop import guard as _guard

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

_DOOR = ("import sys\n"
         "from pathlib import Path\n"
         "from cairn.devices.cairn.machines.ground_loop.__main__ import main\n"
         "sys.exit(main(Path(sys.argv[1])))\n")


def _env():
    return dict(_os.environ, PYTHONPATH=str(_REPO_ROOT))


def _spawn_claimant(home):
    return _subprocess.Popen([sys.executable, "-c", _CLAIMANT, str(home)],
                             stdout=_subprocess.PIPE, stderr=_subprocess.PIPE,
                             env=_env(), text=True)


def test_two_claimants_exactly_one_wins_and_the_loser_refuses_loudly():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        a, b = _spawn_claimant(home), _spawn_claimant(home)
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
        claim = _guard.claim_singleton(home)   # wins IMMEDIATELY: the kernel released it
        claim.release()
        assert (home / _guard.LOCK_NAME).exists(), \
            "the leftover lock file is INERT, not stale — only the held flock ever meant anything"


def test_the_held_claim_survives_the_records_churn():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        claim = _guard.claim_singleton(home)
        for i in range(50):                # the beat's os.replace churns beat.json's inode
            _hb.write_record(_T0 + _td(seconds=i), {"beats": i}, _os.getpid(), home)
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
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        claim = _guard.claim_singleton(home)
        _hb.write_record(_dt.now(_tz.utc).astimezone(), {"beats": 4}, 4242, home)
        loser = _subprocess.run([sys.executable, "-c", _DOOR, str(home)],
                                capture_output=True, text=True, timeout=10, env=_env())
        from cairn.devices.cairn.machines.ground_loop.__main__ import EXIT_ALREADY_RUNNING
        assert loser.returncode == EXIT_ALREADY_RUNNING == 3, \
            "the door's loser exits DISTINCTLY — not 1 (a crash), not 0 (a lie)"
        assert "refusing to start a second loop" in loser.stderr
        assert "4242" in loser.stderr, \
            "the loser names the pid the RECORD said, never a process-table scan"
        claim.release()


def test_a_second_loop_refuses_with_no_takeover():
    """Clause 6: a holder whose record is an hour old is NOT judged hung. The newcomer
    refuses at once, names the pid, sends no signal, and the holder lives on."""
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        holder = _spawn_claimant(home)
        try:
            assert holder.stdout.readline().strip() == "WON"
            _hb.write_record(_dt.now(_tz.utc).astimezone() - _td(hours=1), {"beats": 4},
                             holder.pid, home)
            t0 = _time.monotonic()
            door = _subprocess.run([sys.executable, "-c", _DOOR, str(home)],
                                   capture_output=True, text=True, timeout=20, env=_env())
            assert door.returncode == 3, f"rc={door.returncode} stderr={door.stderr[-300:]!r}"
            assert str(holder.pid) in door.stderr, "the refusal names the holder's pid"
            assert "SIGTERM" not in door.stderr and "stale" not in door.stderr.lower(), \
                f"no takeover and no staleness judgement: {door.stderr[-300:]!r}"
            _time.sleep(0.3)
            assert holder.poll() is None, \
                f"the holder was signaled (rc={holder.returncode}) — a takeover happened"
            assert _time.monotonic() - t0 < 10
            src = (Path(_guard.__file__).parent / "__main__.py").read_text(encoding="utf-8")
            assert "os.kill" not in src, "the runner holds no code path that signals another loop"
        finally:
            holder.kill()
            holder.wait(timeout=5)


def test_the_loop_owns_its_cadence():
    """Clause 7: the beat interval is the ground loop's own setting, 60 s (outline 5.6.4.6),
    defined in its own heartbeat module and read by its runner; it borrows no tool's."""
    assert _hb.CADENCE_S == 60.0, f"CADENCE_S={_hb.CADENCE_S}"
    from cairn.devices.cairn.machines.ground_loop import __main__ as runner
    default = _inspect.signature(runner.main).parameters["cadence"].default
    assert default is _hb.CADENCE_S, f"main()'s cadence default is {default!r}, not the loop's own"
    assert runner.CADENCE_S is _hb.CADENCE_S, "the runner binds the loop's own value"
    import ast
    tree = ast.parse((Path(_guard.__file__).parent / "__main__.py").read_text(encoding="utf-8"))
    tools = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
             and (n.module or "").startswith("cairn.tools.") and "CADENCE_S" in [a.name for a in n.names]]
    assert not tools, f"the cadence is still imported from a tool: {tools}"


def test_the_shim_probes_the_guards_lock():
    """Clause 8: the base shim decides "is the loop up" by probing the very lock file the
    guard claims — by path, through the base singleton tool, importing nothing of this
    device (RULE 1). Held while a claim stands; free after release; the probe takes nothing."""
    from cairn.tools.base import shim as base_shim, singleton
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        assert base_shim.loop_lock_path(home) == home / _guard.LOCK_NAME, \
            "the shim's lock path is the guard's lock file"
        assert not singleton.held(base_shim.loop_lock_path(home)) and not home.exists(), \
            "an absent lock is not held, and probing creates nothing"
        claim = _guard.claim_singleton(home)
        try:
            assert singleton.held(base_shim.loop_lock_path(home)) and _guard.held(home), \
                "a held claim reads held through the shim's path"
            contender = _spawn_claimant(home)
            contender.communicate(timeout=10)
            assert contender.returncode == 3, "the probe never released or stole the claim"
        finally:
            claim.release()
        assert not singleton.held(base_shim.loop_lock_path(home)) and not _guard.held(home), \
            "released → not held"
        winner = _spawn_claimant(home)
        try:
            assert winner.stdout.readline().strip() == "WON", "the probe left no claim behind"
            assert singleton.held(base_shim.loop_lock_path(home)), "another process's claim reads held"
        finally:
            winner.kill()
            winner.wait(timeout=5)


# --- the heartbeat PANE -------------------------------------------------------
# A declared pane through the base shim's STANDARD machinery. It renders what the record
# says plus whether the lock is held — it derives nothing and judges no staleness.

from cairn.devices.cairn.machines.ground_loop.shim import GroundLoopShim, beat_pane_data


def test_the_pane_renders_what_the_record_and_the_lock_say():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        _hb.write_record(_T0, {"beats": 1}, _os.getpid(), home)
        claim = _guard.claim_singleton(home)
        try:
            pane = beat_pane_data(home=home)
            assert pane["up"] is True and pane["record"]["state"] == {"beats": 1}
            assert {k: v for k, v in pane.items() if k not in ("reports", "up", "age_s")} == \
                {k: v for k, v in _hb.read_record(home).items() if k != "age_s"}, \
                "the pane's record IS the read face's own output — render, never derive"
            assert "resident singleton" in pane["reports"]
        finally:
            claim.release()
        assert beat_pane_data(home=home)["up"] is False, "released → the pane says down"


def test_an_absent_record_renders_the_named_lack_never_blank():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        pane = beat_pane_data(home=home)
        assert pane["up"] is False and pane["record"] is None
        assert "no record at" in pane["lack"], "absent is a NAMED lack — never blank"


def test_the_page_assembles_through_the_standard_machinery():
    shim = GroundLoopShim()
    assert type(shim.device()).__name__ == "HeartbeatPage", \
        "the shim starts the heartbeat's read-only page — never a second loop"
    page = shim.active_page()
    assert page["device"] == "ground_loop"
    kinds = [p["kind"] for p in page["panes"]]
    assert kinds[:2] == ["status", "settings"], "the STATUS/SETTINGS floor first"
    assert kinds[-1] == "beat", "the device's declared pane appended last"
    pane = next(p for p in page["panes"] if p["kind"] == "beat")
    assert pane["label"] == "Heartbeat" and "absent" not in pane, \
        "the handler answered — read_record never raises"
    data = pane["data"]
    assert data["up"] in (True, False)
    assert data["record"] is not None or "no record at" in data["lack"]
    assert "resident singleton" in data["reports"]


def _main() -> int:
    for check in (test_the_stamp_advances_across_beats_and_pid_and_state_ride,
                  test_the_instance_dir_is_born_on_first_write,
                  test_an_absent_or_torn_record_is_a_named_lack,
                  test_a_reader_never_sees_a_torn_record,
                  test_two_claimants_exactly_one_wins_and_the_loser_refuses_loudly,
                  test_a_sigkilled_winner_leaves_no_stale_claim,
                  test_the_held_claim_survives_the_records_churn,
                  test_the_doors_loser_reports_from_the_record_and_exits_distinctly,
                  test_a_second_loop_refuses_with_no_takeover,
                  test_the_loop_owns_its_cadence,
                  test_the_shim_probes_the_guards_lock,
                  test_the_pane_renders_what_the_record_and_the_lock_say,
                  test_an_absent_record_renders_the_named_lack_never_blank,
                  test_the_page_assembles_through_the_standard_machinery):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — ground_loop: the beat record, the single-start guard, the cadence and the "
          "heartbeat's page hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
