"""Proof for ticket 1029d5146152: a bus shutdown waits for the requests it holds, and serves while it waits.

MEASURED 2026-11-12 (idea 7306eaa10907): at 11:52:18 `sail.py chart b2e4dafc5813` replaced a
stale bus while `sail.py chart a1d3c9e4b702` was 14 min into a constrain ask. The asker got
"the bus process closed the socket without an answer", and the new bus took over 2 unanswered
asks as given up. The shutdown verb flushed and ended serve_forever, and the daemon handler
threads holding requests died with the process.

  1. test_a_request_in_flight_gets_its_answer: a slow request in flight when shutdown arrives
     gets its own answer, not a closed socket;
  2. test_a_draining_bus_serves_a_newer_caller: while draining, a request from a caller whose
     code is newer than the bus (the bus made stale on cue) is served, not refused stale, in
     under 60 s (outline 5.5.3.9: a wake never takes more than 60 s);
  3. test_the_bus_exits_at_the_first_idle_moment: once the held request answers, the bus exits
     promptly, and its stop line says cause 'verb';
  4. test_the_drain_cap_cuts_and_names_what_it_held: at the cap (CAIRN_BUS_DRAIN_S) the bus exits
     with a request still in flight, and its log names that request's op;
  5. test_an_idle_shutdown_is_unchanged: with nothing in flight, shutdown replies with the
     final_flush result (no draining) and the bus exits with cause 'verb'.

Each tooth starts a real bus over a scratch table at a scratch home, through a driver that adds
two testing ops to BusProcess: ``testing_slow`` (sleeps, then answers) and ``testing_stale``
(sets the process's code stamp below the tree's, so every later local request reads stale).
The server module is imported by the driver at run time, never by this proof.

    python3 cairn/devices/cairn/machines/bus/proofs/test_a_shutdown_drains_what_it_holds.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"1029d5146152": {
    "1": "test_a_request_in_flight_gets_its_answer",
    "2": "test_a_draining_bus_serves_a_newer_caller",
    "3": "test_the_bus_exits_at_the_first_idle_moment",
    "4": "test_the_drain_cap_cuts_and_names_what_it_held",
    "5": "test_an_idle_shutdown_is_unchanged",
}}

_START_S = 30.0
_STOP_S = 30.0
_WAKE_S = 60.0   # outline 5.5.3.9

_DRIVER = r"""
import sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
home = Path(sys.argv[2])
from cairn.devices.cairn.machines.bus import server
from cairn.devices.cairn.machines.bus.bus import BusDevice
def op_testing_slow(self, req):
    s = float(req.get("s", 1))
    time.sleep(s)
    return {"ok": True, "slept": s}
def op_testing_stale(self, req):
    self.stamp = -1.0
    return {"ok": True, "stale_on_cue": True}
server.BusProcess.op_testing_slow = op_testing_slow
server.BusProcess.op_testing_stale = op_testing_stale
with BusDevice.scratch("bus_drain_proof") as bus:
    sys.exit(server.serve(home, bus, lan=0, scratch=True))
"""


def _home() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("testing-1029d5146152-bus-drain-")


def _env(home: Path, drain_s: float | None) -> dict:
    env = dict(os.environ)
    env["CAIRN_BUS_HOME"] = str(home)
    env["PYTHONPATH"] = str(_REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("CAIRN_BUS_DRAIN_S", None)
    if drain_s is not None:
        env["CAIRN_BUS_DRAIN_S"] = str(drain_s)
    return env


def _serve(home: Path, drain_s: float | None = None) -> subprocess.Popen:
    proc = subprocess.Popen([sys.executable, "-c", _DRIVER, str(_REPO), str(home)],
                            cwd=str(_REPO), env=_env(home, drain_s), stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    deadline = time.monotonic() + _START_S
    while time.monotonic() < deadline:
        if (home / "bus.sock").exists():
            return proc
        if proc.poll() is not None:
            raise AssertionError(f"the bus exited {proc.returncode} before it answered: "
                                 f"{proc.stdout.read()[-800:]}")
        time.sleep(0.05)
    proc.kill()
    raise AssertionError(f"no bus.sock at {home} within {_START_S:.0f}s")


def _stopped(proc: subprocess.Popen, within: float = _STOP_S) -> str:
    try:
        out, _ = proc.communicate(timeout=within)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
        raise AssertionError(f"the bus did not stop within {within:.0f}s: {out[-800:]}")
    return out


def _ask(home: Path, req: dict, timeout: float = 60) -> dict:
    from cairn.tools.bus_client.remote import exchange
    return exchange(req, home, timeout=timeout)


class _InFlight:
    """One request on its own thread; ``result`` is its reply, or the exception it raised."""

    def __init__(self, home: Path, req: dict) -> None:
        self.result: object = None
        self.answered_at: float | None = None
        self._t = threading.Thread(target=self._run, args=(home, req), daemon=True)
        self._t.start()

    def _run(self, home: Path, req: dict) -> None:
        try:
            self.result = _ask(home, req, timeout=120)
        except Exception as exc:  # noqa: BLE001 — the reply is what the tooth reads
            self.result = exc
        self.answered_at = time.monotonic()

    def join(self, timeout: float) -> None:
        self._t.join(timeout)


def _stop_lines(home: Path) -> list[dict]:
    path = home / "stops.jsonl"
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _held(home: Path, proc: subprocess.Popen, s: float) -> _InFlight:
    """A slow request in flight, given time to reach its handler."""
    held = _InFlight(home, {"op": "testing_slow", "s": s})
    time.sleep(0.5)
    assert proc.poll() is None, "the bus died before the slow request was held"
    return held


def test_a_request_in_flight_gets_its_answer():
    home = _home()
    proc = _serve(home)
    held = _held(home, proc, 3)
    _ask(home, {"op": "shutdown"}, timeout=30)
    held.join(30)
    out = _stopped(proc)
    assert held.result == {"ok": True, "slept": 3.0}, (
        f"the held request got {held.result!r}, not its own answer; bus said {out[-800:]}")


def test_a_draining_bus_serves_a_newer_caller():
    home = _home()
    proc = _serve(home)
    held = _held(home, proc, 4)
    assert _ask(home, {"op": "testing_stale"}).get("stale_on_cue"), "the bus was not made stale"
    before = _ask(home, {"op": "stats"})
    assert before.get("stale"), f"a stale bus must refuse before any drain: {before!r}"
    reply = _ask(home, {"op": "shutdown"}, timeout=30)
    assert reply.get("draining") == 1, f"the shutdown reply names no drain: {reply!r}"
    t0 = time.monotonic()
    served = _ask(home, {"op": "testing_slow", "s": 0}, timeout=_WAKE_S)
    took = time.monotonic() - t0
    stats = _ask(home, {"op": "stats"})
    held.join(30)
    _stopped(proc)
    assert served == {"ok": True, "slept": 0.0}, f"a newer caller during the drain got {served!r}"
    assert took < _WAKE_S, f"the draining bus took {took:.1f}s to serve, past the {_WAKE_S:.0f}s wake"
    assert stats.get("ok") and not stats.get("stale"), f"stats during the drain: {stats!r}"


def test_the_bus_exits_at_the_first_idle_moment():
    home = _home()
    proc = _serve(home)
    held = _held(home, proc, 3)
    _ask(home, {"op": "shutdown"}, timeout=30)
    time.sleep(1.0)
    alive = proc.poll() is None   # the held request has ~1.5 s left: the bus must still be up
    held.join(30)
    out = _stopped(proc, within=15)
    assert alive, f"the bus exited while it held a request: {out[-800:]}"
    assert held.result == {"ok": True, "slept": 3.0}, f"the held request got {held.result!r}"
    gone = time.monotonic() - held.answered_at
    assert gone < 10, f"the bus lived {gone:.1f}s past its last request"
    lines = _stop_lines(home)
    assert len(lines) == 1 and lines[0].get("cause") == "verb", (
        f"stop lines {lines!r}; bus said {out[-800:]}")


def test_the_drain_cap_cuts_and_names_what_it_held():
    home = _home()
    proc = _serve(home, drain_s=2)
    held = _held(home, proc, 60)
    t0 = time.monotonic()
    reply = _ask(home, {"op": "shutdown"}, timeout=30)
    out = _stopped(proc, within=20)
    took = time.monotonic() - t0
    held.join(10)
    assert reply.get("draining") == 1, f"the shutdown reply names no drain: {reply!r}"
    assert took < 15, f"a 2 s cap held the bus {took:.1f}s"
    assert "drain cut 1 request(s)" in out and "testing_slow" in out, (
        f"the cut is not named in the bus log: {out[-800:]}")
    assert isinstance(held.result, Exception), f"a cut request cannot have answered: {held.result!r}"


def test_an_idle_shutdown_is_unchanged():
    home = _home()
    proc = _serve(home)
    reply = _ask(home, {"op": "shutdown"}, timeout=30)
    out = _stopped(proc)
    assert reply.get("ok") is True and "json" in reply and "draining" not in reply, (
        f"an idle shutdown must reply the final_flush result: {reply!r}")
    lines = _stop_lines(home)
    assert len(lines) == 1 and lines[0].get("cause") == "verb", (
        f"stop lines {lines!r}; bus said {out[-800:]}")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
