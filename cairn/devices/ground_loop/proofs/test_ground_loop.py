"""Proof for ground_loop — THE HEARTBEAT. One pulse; nothing more.

This proof exercises the corrected shape: the heartbeat beats and pulses the shim of every
subscribed device; the FIRING lives in the shim. It composes the real BaseShim + Probe +
a spy bus, so the full beat → on_pulse → fire → poke chain is shown WITHOUT a DB (the
heartbeat holds no durable state — that is the whole point). The durable bus is proven
separately (cairn/devices/bus/proofs/test_bus.py).

Teeth a hollow heartbeat could not pass:
  - A BEAT PULSES EVERY SUBSCRIBED SHIM, IN ORDER, and leaves a legible beat-record naming
    who was pulsed — a beat is evidence, a record, never a silent ``RUNNING``. (This line
    said "LEARNING, not silent RUNNING" until 2026-07-30, when ticket watchme-emits-a-probe
    dissolved ``LEARNING`` as a node state; the tooth never changed — EVIDENCE was always
    what a beat yields.)
  - THE FIRING IS THE SHIM'S: a probe due on this beat pokes the bus THROUGH its shim; one
    not due holds. The heartbeat itself pokes nothing.
  - SUBSCRIBE IS IDEMPOTENT by device_id; only a shim (device_id + on_pulse) may subscribe.
  - ONE SHIM RAISING CANNOT STOP THE BEAT reaching the others (CP2, Law 7).
  - THE GOOF IS GONE: no run_driver / no method registry — the heartbeat executes nothing.
  - IT IS A DEVICE (Law 2 / Form v0 #2).
  - THE ROSTER IS THE NAV (web-server child c): the heartbeat publishes roster() at ALL times —
    the devices it beats to, in order, each with live wakefulness — before the first beat too;
    a device absent from subscriptions is absent from the roster; the roster is DATA.
  - THE CROSSINGS ARE NO LONGER SILENT — and the beat is NOT a crossing. Breadcrumbs on
    roster changes and pulse failures only; a healthy beat emits nothing (per anomaly,
    never per pulse — the firehose is the failure mode on this device).

Runnable bare (NO DB, NO framework):
    python3 cairn/devices/ground_loop/proofs/test_ground_loop.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.probe import Probe
from cairn.tools.base.core_values import CoreValuesMixin
from cairn.tools.base.shim import BaseShim
from cairn.devices.ground_loop.loop import GroundLoopDevice


class _SpyBus:
    def __init__(self) -> None:
        self.posted: list[dict] = []

    def post(self, **envelope) -> dict:
        envelope = {"id": f"env{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope


class _Shim(BaseShim):
    def __init__(self, device_id, bus=None, probes=None) -> None:
        super().__init__(bus=bus)
        self._id = device_id
        self._probes = probes or []

    @property
    def device_id(self) -> str:
        return self._id

    def probes(self):
        return self._probes

    def _start_device(self):
        # A minimal woken device — enough to flip running True, and it declares a ``receive``
        # because since 2026-08-11 a device that is delivered to and cannot receive REFUSES
        # rather than swallowing the envelope (``BaseShim.deliver``). A bare ``object()`` here
        # used to stand in for a real device and quietly proved the opposite of the contract.
        class _Woken:
            def __init__(self):
                self.mail = []

            def receive(self, envelope):
                self.mail.append(envelope)
                return {"ack": envelope.get("id")}

        return _Woken()


class _AngryShim(BaseShim):
    @property
    def device_id(self) -> str:
        return "angry"

    def on_pulse(self, now, context=None):
        raise RuntimeError("this shim throws on pulse")


def test_a_beat_pulses_every_shim_in_order():
    bus = _SpyBus()
    gl = GroundLoopDevice()
    gl.subscribe(_Shim("a", bus))
    gl.subscribe(_Shim("b", bus))

    rec = gl.beat(now="t0")

    assert rec["pulsed"] == ["a", "b"], "every subscribed shim is pulsed, in subscription order"
    assert [p["device"] for p in rec["pulses"]] == ["a", "b"]
    assert gl.state()["beats"] == 1


def test_the_firing_is_the_shims_not_the_heartbeats():
    bus = _SpyBus()
    due = Probe(why="wake ops", trigger=lambda now, ctx: ctx.get("hot"), to="ops/personal")
    idle = Probe(why="wake night", trigger=lambda now, ctx: False, to="night/personal")
    gl = GroundLoopDevice()
    gl.subscribe(_Shim("sensor", bus, probes=[due, idle]))

    gl.beat(now="t0", context={"hot": True})

    assert len(bus.posted) == 1 and bus.posted[0]["to"] == "ops/personal", \
        "the due probe pokes the bus through its shim; the heartbeat itself pokes nothing"
    # A beat where nothing is due pokes nobody.
    gl.beat(now="t1", context={"hot": False})
    assert len(bus.posted) == 1, "no probe due → no poke"


def test_subscribe_is_idempotent_and_typed():
    gl = GroundLoopDevice()
    s = _Shim("once")
    gl.subscribe(s)
    gl.subscribe(s)  # same device_id — must not double-subscribe
    assert gl.subscribers == ["once"]
    try:
        gl.subscribe(object())
        raise AssertionError("only a shim (device_id + on_pulse) may subscribe to the heartbeat")
    except TypeError:
        pass


def test_one_shim_raising_cannot_stop_the_beat():
    bus = _SpyBus()
    gl = GroundLoopDevice()
    gl.subscribe(_AngryShim())
    gl.subscribe(_Shim("healthy", bus, probes=[
        Probe(why="still fires", trigger=lambda now, ctx: True, to="ok/personal")]))

    rec = gl.beat(now="t0")

    outcomes = {p["device"]: p.get("outcome", "ok") for p in rec["pulses"]}
    assert outcomes["angry"] == "refused", "the throwing shim is a loud, permanent entry (Law 7)"
    assert len(bus.posted) == 1 and bus.posted[0]["to"] == "ok/personal", \
        "the healthy shim still fired after the angry one (CP2)"


def test_the_executor_goof_is_gone():
    gl = GroundLoopDevice()
    assert not hasattr(gl, "run_driver"), "the heartbeat executes nothing — run_driver is retired"
    assert not hasattr(gl, "registry"), "the heartbeat holds no method registry — that was the goof"


def test_the_roster_is_the_nav_published_at_all_times():
    import json
    gl = GroundLoopDevice()
    # Published BEFORE any subscribe or beat — an empty nav is honest, not broken.
    empty = gl.roster()
    assert empty == {"beats": 0, "devices": []}, "the roster is published at all times, even empty"

    a, b = _Shim("alpha"), _Shim("beta")
    gl.subscribe(a)
    gl.subscribe(b)
    roster = gl.roster()
    assert [d["device"] for d in roster["devices"]] == ["alpha", "beta"], \
        "the roster is the subscription list, in order — the nav across the top"
    assert all(d["awake"] is False for d in roster["devices"]), "no device woken yet → all asleep in the nav"

    # Wakefulness is LIVE: wake one device (deliver mail) and the nav reflects it.
    a.deliver({"id": "e1"})
    assert gl.roster()["devices"][0]["awake"] is True, "the roster shows live wakefulness (shim.running)"
    # A device NOT subscribed cannot appear in the nav — you navigate to what the heartbeat beats.
    assert "gamma" not in [d["device"] for d in gl.roster()["devices"]]
    # The roster is DATA the web server renders — json-round-trips unchanged.
    assert json.loads(json.dumps(roster)) == roster


def test_the_crossings_are_no_longer_silent():
    """The silent_device disposition (troubles/silent-devices-2026-07-27.json): the
    heartbeat's crossings are ROSTER CHANGES and pulse FAILURES — never the beat itself.
    A breadcrumb per beat would be the per-pulse firehose the discipline forbids; a
    healthy beat's evidence is the beat-record it already returns.

    SILENCED, DELIBERATELY (ticket a-device-logs-without-being-wired, 2026-08-18). This tooth
    used to say "HELD when no receiver is wired" and lean on it: un-wired meant held, so the
    proof read ``held_diagnostics()`` for free. Un-wired now WRITES to
    ``~/.cairn/logs/ground_loop/0/`` — which would empty this list and seed the live tree in the
    same stroke. ``set_diagnostic_receiver(None)`` asks for the holding that used to be an
    accident; what Law 7 forbids (a silent drop) is what the assertions below still check."""
    bus = _SpyBus()
    gl = GroundLoopDevice()
    gl.set_diagnostic_receiver(None)
    s = _Shim("steady", bus)
    gl.subscribe(s)
    gl.subscribe(s)                      # idempotent re-subscribe: no roster change, no breadcrumb
    gl.beat(now="t0")                    # a healthy beat is SILENT
    assert [h["gate"] for h in gl.held_diagnostics()] == ["subscribe"], \
        "one roster change → one breadcrumb; the healthy beat and the re-subscribe add none"
    assert gl.held_diagnostics()[0]["pointer"] == "steady"

    gl.subscribe(_AngryShim())
    rec = gl.beat(now="t1")              # the angry shim fails ITS pulse; the beat survives (CP2)
    held = gl.held_diagnostics()
    assert [h["gate"] for h in held] == ["subscribe", "subscribe", "pulse_refused"], (
        f"a FAILED pulse is the anomaly worth a breadcrumb, got {[h['gate'] for h in held]} — "
        "per anomaly, never per beat"
    )
    refused = held[-1]
    assert refused["pointer"] == "angry", "the breadcrumb points at the shim whose pulse failed"
    assert refused["values"]["beat"] == rec["beat"] and "RuntimeError" in refused["values"]["error"], \
        "the error rides the breadcrumb whole — complete on first pass, no re-run to gather it"
    assert all(h["home"] == "held" for h in held), \
        "a SILENCED device holds its records (Law 7) — never silently dropped"
    # More healthy beats: still nothing new from health.
    gl2 = GroundLoopDevice()
    gl2.set_diagnostic_receiver(None)
    gl2.subscribe(_Shim("quiet"))
    for t in ("t0", "t1", "t2"):
        gl2.beat(now=t)
    assert [h["gate"] for h in gl2.held_diagnostics()] == ["subscribe"], \
        "three healthy beats, zero breadcrumbs — the heartbeat does not narrate its own pulse"


def test_it_is_a_device():
    gl = GroundLoopDevice()
    assert isinstance(gl, CoreValuesMixin), "a device must compose the core values (Law 2)"
    assert [v.id for v in gl.CORE_VALUES] == ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]
    assert list(gl.introspect()) == ["intention", "state", "settings", "other"], "Form v0 #2 order"


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

from cairn.devices.ground_loop.liveness import (
    RECORD_NAME, STALENESS_THRESHOLD_S, read_liveness, write_liveness,
)

_T0 = _dt(2026, 8, 9, 12, 0, 0, tzinfo=_tz.utc)


def test_the_stamp_advances_across_beats_and_pid_and_state_ride():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        gl = GroundLoopDevice(liveness_home=home)
        gl.subscribe(_Shim("rider"))

        gl.beat(now=_T0)
        first = read_liveness(_T0, home=home)
        assert first["verdict"] == "LIVE" and first["age_s"] == 0.0
        assert first["record"]["last_run"] == _T0.isoformat(), \
            "last-run is THIS beat's injected now — the write is part of the pass"

        t1 = _T0 + _td(seconds=1)
        gl.beat(now=t1)
        second = read_liveness(t1, home=home)
        assert second["record"]["last_run"] == t1.isoformat(), \
            "the stamp ADVANCES while the loop runs — the falsifier's first clause"
        assert second["record"]["pid"] == _os.getpid(), "the pid rides the record"
        assert second["record"]["state"]["beats"] == 2 and \
            second["record"]["state"]["subscribers"] == ["rider"], \
            "the state riding the record is the device's own state() surface, post-pass"


def test_the_instance_dir_is_born_on_first_write():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "devices" / "ground_loop" / "0"   # does not exist yet
        assert not home.exists()
        GroundLoopDevice(liveness_home=home).beat(now=_T0)
        assert (home / RECORD_NAME).exists(), \
            "the device space is born with its first record — no separate mkdir step to forget"


def test_dead_on_stale_live_on_fresh_dead_on_absent_or_torn():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        # Absent — never ran — is a DEAD verdict with the lack named, not an exception.
        gone = read_liveness(_T0, home=home)
        assert gone["verdict"] == "DEAD" and gone["record"] is None and "lack" in gone

        GroundLoopDevice(liveness_home=home).beat(now=_T0)
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


def test_a_homeless_device_writes_nothing():
    # Constructed without a liveness home, the device is an anonymous in-process
    # heartbeat: beat() attempts NO write — proven by beating with a string now,
    # which any write path would choke on (str has no isoformat), exactly as every
    # pre-existing tooth in this file already beats.
    gl = GroundLoopDevice()
    gl.beat(now="t0")
    assert gl._liveness_home is None


# --- the single-start guard (ticket an-entry-point-starts-the-loop-only-once) ---
# Read-then-act is not atomic: two entry points can both read DEAD inside the
# same 5s window. So the claim is ONE syscall — flock, held for life, kernel-
# released on death — and these teeth are ADVERSARIAL: real processes contend,
# exactly one wins, the loser is loud, and a corpse leaves nothing stale.

import subprocess as _subprocess
import time as _time

from cairn.devices.ground_loop.guard import LOCK_NAME, claim_singleton
from cairn.devices.ground_loop.__main__ import EXIT_ALREADY_RUNNING

_CLAIMANT = (
    "import sys, time\n"
    "from pathlib import Path\n"
    "from cairn.devices.ground_loop.guard import ClaimRefused, claim_singleton\n"
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
            "from cairn.devices.ground_loop.__main__ import main\n"
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
        assert loser.returncode == EXIT_ALREADY_RUNNING == 3, \
            "the door's loser exits DISTINCTLY — not 1 (a crash), not 0 (a lie)"
        assert "refusing to start a second loop" in loser.stderr
        assert "4242" in loser.stderr, \
            "the loser reports what the RECORD said (pid), never a process-table scan"
        # A STALE record behind a still-held claim — alive inside its first beats or
        # merely slow: the lock outranks the read, so still no second loop.
        write_liveness(_dt.now(_tz.utc).astimezone() - _td(seconds=60),
                       {"beats": 4}, 4242, home)
        slow = _subprocess.run([sys.executable, "-c", door, str(home)],
                               capture_output=True, text=True, timeout=10, env=env)
        assert slow.returncode == EXIT_ALREADY_RUNNING
        assert "outranks the stale read" in slow.stderr, \
            "alive-but-slow is NOT declared dead — the falsifier's second clause"
        claim.release()


# --- the liveness PANE (ticket the-ground-loop-pane-shows-its-state) ------------
# The loop's device page — a declared pane through the base shim's STANDARD
# machinery, never a route or a port of its own. The pane RENDERS what the
# record says: its data IS read_liveness's own output plus one presentation
# label, so it cannot derive, cache, or grow a second staleness opinion.

from cairn.devices.ground_loop.loop import liveness_pane_data
from cairn.devices.ground_loop.shim import GroundLoopShim


def test_the_pane_renders_what_the_record_says_and_never_derives():
    with _tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        GroundLoopDevice(liveness_home=home).beat(now=_T0)
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
    gl = GroundLoopDevice()
    shim = GroundLoopShim(gl)
    gl.subscribe(shim)                             # the self-join the listener wires
    assert shim.device() is gl, "the shim fronts the HANDED chassis — never a second loop"

    page = shim.active_page()                      # the REAL BaseShim method, unoverridden
    assert page["device"] == "ground_loop"
    assert [p["kind"] for p in page["panes"]] == ["status", "settings", "liveness"], \
        "the STATUS/SETTINGS floor first (Form v0 #2, projected free), the declared pane appended"
    pane = page["panes"][2]
    assert pane["label"] == "Liveness" and "absent" not in pane, \
        "the handler answered — read_liveness never raises; an absent record is DATA, not a refusal"
    # The deployed handler reads the RESIDENT record (the wall clock, the real home),
    # so this tooth pins INVARIANTS, never a snapshot: a verdict either way, the lack
    # named exactly when the record is absent, the reports label riding.
    data = pane["data"]
    assert data["verdict"] in ("LIVE", "DEAD")
    assert data["record"] is not None or "no record at" in data["lack"]
    assert "resident singleton" in data["reports"]


def test_the_self_subscription_is_inert_under_the_beat():
    bus = _SpyBus()
    plain = GroundLoopDevice()
    plain.subscribe(_Shim("rider", bus))
    baseline = plain.beat(now="t0")

    looped = GroundLoopDevice()
    looped.subscribe(GroundLoopShim(looped))
    looped.subscribe(_Shim("rider", bus))
    rec = looped.beat(now="t0")

    assert [p["device"] for p in rec["pulses"]] == ["ground_loop", "rider"]
    own = rec["pulses"][0]
    assert own.get("fired", []) == [] and own.get("outcome") != "refused", \
        "the loop pulsing its own probe-less shim evaluates nothing, fires nothing, raises nothing"
    assert rec["pulses"][1] == baseline["pulses"][0], \
        "the rider's pulse-record is identical with the self-subscription present"
    assert bus.posted == [], "no pokes either way — the self-join changes no firing"
    assert [d["device"] for d in looped.roster()["devices"]] == ["ground_loop", "rider"], \
        "the one difference is the honest one: the roster (and so the nav) carries ground_loop"


def _main() -> int:
    for check in (test_a_beat_pulses_every_shim_in_order,
                  test_the_firing_is_the_shims_not_the_heartbeats,
                  test_subscribe_is_idempotent_and_typed,
                  test_one_shim_raising_cannot_stop_the_beat,
                  test_the_executor_goof_is_gone,
                  test_the_roster_is_the_nav_published_at_all_times,
                  test_the_crossings_are_no_longer_silent,
                  test_it_is_a_device,
                  test_the_stamp_advances_across_beats_and_pid_and_state_ride,
                  test_the_instance_dir_is_born_on_first_write,
                  test_dead_on_stale_live_on_fresh_dead_on_absent_or_torn,
                  test_a_reader_never_sees_a_torn_record,
                  test_a_homeless_device_writes_nothing,
                  test_two_claimants_exactly_one_wins_and_the_loser_refuses_loudly,
                  test_a_sigkilled_winner_leaves_no_stale_claim,
                  test_the_held_claim_survives_the_records_churn,
                  test_the_doors_loser_reports_from_the_record_and_exits_distinctly,
                  test_the_pane_renders_what_the_record_says_and_never_derives,
                  test_an_absent_record_renders_the_named_lack_never_blank,
                  test_the_page_assembles_through_the_standard_machinery,
                  test_the_self_subscription_is_inert_under_the_beat):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — ground_loop: the heartbeat beats and pulses subscribed shims (in order, "
          "survivably); the firing is the shim's, and the executor goof is gone")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
