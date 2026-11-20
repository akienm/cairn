"""Proof for ticket c234aae2c0b9 — a scratch bus with nothing open or standing ends itself; the live bus never does.

MEASURED 2026-11-19: a --scratch bus whose caller is gone served on for hours (an orphan on
akienasus). The bus alone knows whether anything is open or standing, so the bound sits in
the bus: after N seconds (CAIRN_BUS_IDLE_S, default 1800) with no open connection, no request
in flight, no ask unanswered, no mail undelivered and no shim held by spec and wired, a
--scratch bus leaves by the home-gone door with cause 'idle' in ``<home>/stops.jsonl``.

Every bus here runs at a scratch home over a throwaway table (``BusDevice.scratch``), N short
by env. A non-scratch bus is served by a driver over a scratch table, so no tooth touches the
live table. Every unit and child a tooth starts is stopped in its finally, the unit by name.

  1. test_a_scratch_bus_with_nothing_open_ends_itself: serve --scratch, N=2: it exits on its
     own after N, not before, with one stop line of cause 'idle' (idle_s >= N, n_s = N);
  +  test_a_live_bus_never_idles: serve(scratch=False), N=1: still serving and answering at
     6 s; a SIGTERM then records cause 'signal' with idle_s_max past N;
  2. test_nothing_standing_is_lost_across_an_idle_exit: past N it stays up while a connection
     is open, a request is in flight, an ask is unanswered, an envelope is undelivered, or a
     shim held by spec is wired — and exits 'idle' once each is released. Then a RemoteBus
     handle opened before an idle exit respawns a bus at the same home, and a re-held fixture
     echo (bus_proof_echo, never a real device) is answered by the new pid;
  3. test_n_is_read_not_guessed: with CAIRN_BUS_IDLE_S unset N is 1800 (a bus so served is
     still up past 3 s), and every stop record (idle, signal, verb) carries idle_s_max.

    python3 cairn/devices/cairn/machines/bus/proofs/test_a_scratch_bus_with_no_caller_ends_itself.py
"""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"c234aae2c0b9": {
    "1": "test_a_scratch_bus_with_nothing_open_ends_itself",
    "2": "test_nothing_standing_is_lost_across_an_idle_exit",
    "3": "test_n_is_read_not_guessed",
}}

_MODULE = "cairn.devices.cairn.machines.bus"
_ECHO_SPEC = "cairn.devices.cairn.machines.bus.proofs.bus_proof_echo:BusProofEchoShim"
_START_S = 30.0
_EXIT_S = 30.0
_N = 2.0
_HOLD_S = 3 * _N   # a guard holds the bus this long: well past N

# serve() at a scratch home over a throwaway table. mode 'none' serves as it is; any other
# mode arms one standing thing before serve_forever and releases it after _HOLD_S, so the
# bus's own exit, after the release and not before, is the guard's measurement.
_DRIVER = r"""
import sys, threading
from pathlib import Path
sys.path.insert(0, sys.argv[1])
home, mode, scratch, hold = Path(sys.argv[2]), sys.argv[3], sys.argv[4] == "1", float(sys.argv[5])
from cairn.devices.cairn.machines.bus import server
from cairn.devices.cairn.machines.bus.bus import BusDevice
ECHO = "cairn.devices.cairn.machines.bus.proofs.bus_proof_echo:BusProofEchoShim"
orig = server._Server.serve_forever

def arm(srv):
    process, bus = srv.process, srv.process.bus
    if mode == "flight":
        t = process.in_flight.enter("testing-c234aae2c0b9")
        return lambda: process.in_flight.leave(t)
    if mode == "asked":
        with bus._lock:
            bus._asked["testing-c234aae2c0b9-ask"] = "testing-c234aae2c0b9"
        return lambda: bus._asked.pop("testing-c234aae2c0b9-ask", None)
    if mode == "pending":
        with bus._lock:
            bus._pending["testing-c234aae2c0b9-env"] = {
                "id": "testing-c234aae2c0b9-env", "addressee": "testing-c234aae2c0b9",
                "channel": "personal"}
        return lambda: bus._pending.pop("testing-c234aae2c0b9-env", None)
    if mode == "wired":
        process.hold_class(ECHO, wire=True)
        assert process._is_wired("bus_proof_echo"), "the echo did not wire"
        return lambda: process._by_spec.clear()   # the subscription ends
    return None

def forever(self, poll_interval=0.5):
    for th in threading.enumerate():
        if th.name == "bus-backlog":
            th.join(30)   # the start's backlog pass first: nothing it does touches what is armed
    release = arm(self)
    if release is not None:
        print(f"driver: armed {mode}", file=sys.stderr, flush=True)
        def _let_go():
            release()
            print(f"driver: released {mode}", file=sys.stderr, flush=True)
        t = threading.Timer(hold, _let_go)
        t.daemon = True
        t.start()
    return orig(self, poll_interval)

server._Server.serve_forever = forever
with BusDevice.scratch("bus_idle_proof") as bus:
    sys.exit(server.serve(home, bus, lan=0, scratch=scratch))
"""


def _home(tag: str) -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir(f"testing-c234aae2c0b9-{tag}-")


def _env(home: Path, n: float | None) -> dict:
    env = dict(os.environ)
    env["CAIRN_BUS_HOME"] = str(home)
    env["PYTHONPATH"] = str(_REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if n is None:
        env.pop("CAIRN_BUS_IDLE_S", None)
    else:
        env["CAIRN_BUS_IDLE_S"] = str(n)
    return env


def _stops(home: Path) -> list[dict]:
    path = home / "stops.jsonl"
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _answering(proc: subprocess.Popen, home: Path) -> float:
    """Wait for bus.sock; returns the monotonic moment it appeared."""
    deadline = time.monotonic() + _START_S
    while time.monotonic() < deadline:
        if (home / "bus.sock").exists():
            return time.monotonic()
        if proc.poll() is not None:
            raise AssertionError(f"the bus exited {proc.returncode} before it answered: "
                                 f"{proc.stdout.read()[-800:]}")
        time.sleep(0.05)
    raise AssertionError(f"no bus.sock at {home} within {_START_S:.0f}s")


def _serve(home: Path, n: float | None) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", _MODULE, "serve", "--home", str(home), "--scratch", "--lan", "0"],
        cwd=str(_REPO), env=_env(home, n), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def _driven(home: Path, mode: str, *, scratch: bool, n: float | None) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", _DRIVER, str(_REPO), str(home), mode, "1" if scratch else "0",
         str(_HOLD_S)],
        cwd=str(_REPO), env=_env(home, n), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def _ended(proc: subprocess.Popen, within: float) -> tuple[int, str]:
    try:
        out, _ = proc.communicate(timeout=within)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
        raise AssertionError(f"the bus did not exit within {within:.0f}s: {out[-800:]}")
    return proc.returncode, out


def _reap(proc: subprocess.Popen) -> None:
    """A finally's stop: a child still running is ended and waited for."""
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=_EXIT_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def _idle_line(home: Path, out: str, n: float) -> dict:
    lines = _stops(home)
    assert len(lines) == 1, f"expected one stop line, got {len(lines)}: {lines!r}; bus said {out[-800:]}"
    line = lines[0]
    assert line.get("cause") == "idle", f"cause is {line.get('cause')!r}: {line!r}; bus said {out[-600:]}"
    detail = line.get("detail") or {}
    assert detail.get("n_s") == n, f"n_s is {detail.get('n_s')!r}, N was {n}: {line!r}"
    assert float(detail.get("idle_s") or 0) >= n, f"idle_s {detail.get('idle_s')!r} < N {n}: {line!r}"
    return line


def test_a_scratch_bus_with_nothing_open_ends_itself():
    home = _home("idles")
    proc = _serve(home, _N)
    try:
        at = _answering(proc, home)
        rc, out = _ended(proc, _N + _EXIT_S)
        lived = time.monotonic() - at
        assert rc == 0, f"an idle exit is a clean exit, got {rc}: {out[-800:]}"
        assert lived >= _N, f"the bus exited {lived:.2f}s after it answered, before N={_N}"
        line = _idle_line(home, out, _N)
        assert float(line.get("idle_s_max") or 0) >= _N, f"idle_s_max below N: {line!r}"
        assert "idle" in out and "nothing open or standing" in out, f"no idle line in the bus log: {out[-600:]}"
    finally:
        _reap(proc)


def test_a_live_bus_never_idles():
    from cairn.tools.bus_client.remote import exchange
    home = _home("live")
    proc = _driven(home, "none", scratch=False, n=1.0)
    try:
        _answering(proc, home)
        time.sleep(6.0)
        assert proc.poll() is None, f"a live bus exited at N=1: {proc.stdout.read()[-800:]}"
        assert _stops(home) == [], f"a live bus recorded a stop: {_stops(home)!r}"
        reply = exchange({"op": "stats"}, home, timeout=30)
        assert reply.get("ok"), f"the live bus did not answer stats at 6 s: {reply!r}"
        proc.send_signal(signal.SIGTERM)
        _rc, out = _ended(proc, _EXIT_S)
        lines = _stops(home)
        assert len(lines) == 1 and lines[0].get("cause") == "signal", (
            f"the live bus's one stop must be the signal: {lines!r}; {out[-600:]}")
        assert float(lines[0].get("idle_s_max") or 0) >= 5.0, (
            f"the live bus sat idle ~6 s past N=1 and recorded idle_s_max {lines[0].get('idle_s_max')!r}")
    finally:
        _reap(proc)


def _guard(mode: str) -> None:
    """One standing thing keeps a short-N scratch bus up past N; released, the bus idles out."""
    home = _home(f"guard-{mode}")
    proc = _driven(home, mode, scratch=True, n=_N)
    try:
        _answering(proc, home)
        time.sleep(_HOLD_S - 1.0)   # past N by 2N, and before the release
        assert proc.poll() is None, (
            f"[{mode}] the bus exited while it stood: {proc.stdout.read()[-800:]}")
        assert _stops(home) == [], f"[{mode}] a stop while it stood: {_stops(home)!r}"
        rc, out = _ended(proc, 1.0 + _N + _EXIT_S)
        assert f"driver: released {mode}" in out, f"[{mode}] never released: {out[-800:]}"
        line = _idle_line(home, out, _N)
        assert rc == 0, f"[{mode}] rc {rc}: {line!r}"
    finally:
        _reap(proc)


def _open_connection_guard() -> None:
    home = _home("guard-conn")
    proc = _serve(home, _N)
    sock = None
    try:
        _answering(proc, home)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(home / "bus.sock"))
        time.sleep(_HOLD_S)
        assert proc.poll() is None, f"[conn] the bus exited with a connection open: {proc.stdout.read()[-800:]}"
        assert _stops(home) == [], f"[conn] a stop with a connection open: {_stops(home)!r}"
        sock.close()
        sock = None
        rc, out = _ended(proc, _N + _EXIT_S)
        _idle_line(home, out, _N)
    finally:
        if sock is not None:
            sock.close()
        _reap(proc)


def _unit_stop(home: Path) -> None:
    """Stop the unit a RemoteBus spawned for ``home``, by name."""
    from cairn.tools.bus_client.remote import _unit
    try:
        subprocess.run(["systemctl", "--user", "stop", f"{_unit(home)}.service"],
                       capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        pass   # no systemd: the bus was spawned with setsid and the shutdown verb ended it


def _respawn() -> None:
    from cairn.tools.bus_client.remote import RemoteBus, exchange
    home = _home("respawn")
    env = _env(home, _N)
    rb = RemoteBus(str(home), scratch=True, env=env)   # opened before the exit
    try:
        rb.stats()                                      # the handle starts the first bus
        deadline = time.monotonic() + _N + _EXIT_S
        while time.monotonic() < deadline and not _stops(home):
            time.sleep(0.2)
        first = _stops(home)
        assert len(first) == 1 and first[0].get("cause") == "idle", (
            f"[respawn] the first bus did not idle out: {first!r}")
        gone = first[0]["pid"]
        held = rb.hold_shim(_ECHO_SPEC)                 # the same handle: a respawn at the same home
        assert "bus_proof_echo" in (held.get("held") or []), f"[respawn] echo not held: {held!r}"
        reply = rb.request(sender="testing-c234aae2c0b9", to="bus_proof_echo", channel="personal",
                           verb="echo", why="testing-c234aae2c0b9: mail across an idle exit",
                           body={"n": 1}, timeout=30)
        body = (reply or {}).get("body") or {}
        assert body.get("echoed") == {"n": 1}, f"[respawn] the echo did not carry the mail: {reply!r}"
        now = body.get("pid")
        assert now and now != gone, f"[respawn] answered by pid {now!r}; the bus that idled was {gone}"
        os.kill(now, 0)                                  # the answering bus is alive
    finally:
        try:
            exchange({"op": "shutdown"}, home, timeout=10)
        except (OSError, ValueError):
            pass
        _unit_stop(home)


def test_nothing_standing_is_lost_across_an_idle_exit():
    _open_connection_guard()
    for mode in ("flight", "asked", "pending", "wired"):
        _guard(mode)
    _respawn()


def test_n_is_read_not_guessed():
    from cairn.devices.cairn.machines.bus import server   # bound at call time: the default is the subject
    from cairn.tools.bus_client.remote import exchange
    saved = os.environ.pop("CAIRN_BUS_IDLE_S", None)
    try:
        assert server._idle_n() == 1800.0, f"N unset reads {server._idle_n()!r}, not 1800"
    finally:
        if saved is not None:
            os.environ["CAIRN_BUS_IDLE_S"] = saved
    causes = {}
    # verb: an unset-N scratch bus is still up past 3 s, then the shutdown verb ends it
    home = _home("n-verb")
    proc = _serve(home, None)
    try:
        _answering(proc, home)
        time.sleep(3.0)
        assert proc.poll() is None, f"an unset-N scratch bus exited inside 3 s: {proc.stdout.read()[-600:]}"
        exchange({"op": "shutdown"}, home, timeout=30)
        _ended(proc, _EXIT_S)
        causes["verb"] = _stops(home)
    finally:
        _reap(proc)
    home = _home("n-signal")
    proc = _serve(home, _N)
    try:
        _answering(proc, home)
        proc.send_signal(signal.SIGTERM)
        _ended(proc, _EXIT_S)
        causes["signal"] = _stops(home)
    finally:
        _reap(proc)
    home = _home("n-idle")
    proc = _serve(home, 1.0)
    try:
        _answering(proc, home)
        _ended(proc, 1.0 + _EXIT_S)
        causes["idle"] = _stops(home)
    finally:
        _reap(proc)
    for cause, lines in causes.items():
        assert len(lines) == 1 and lines[0].get("cause") == cause, f"[{cause}] stop lines {lines!r}"
        v = lines[0].get("idle_s_max")
        assert isinstance(v, (int, float)) and v >= 0, f"[{cause}] no idle_s_max: {lines[0]!r}"
    assert causes["verb"][0]["idle_s_max"] >= 3.0, f"the 3 s gap is not in idle_s_max: {causes['verb']!r}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
