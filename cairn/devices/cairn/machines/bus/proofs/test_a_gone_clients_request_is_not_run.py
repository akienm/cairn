"""PROOF for ticket ee88c2126abc: a request whose asker has gone is not run, and not replayed after a restart.

MEASURED 2026-11-12 (idea 7306eaa10907): the home bus wedged in the codemother queueme gate.
Requests to the gated shim queued behind its lock, their askers reached their deadlines or
dropped their sockets, and each queued envelope still ran to its end once the lock came free.
A bus stop handed those asks over (ticket 054a03f974f6), and the next bus's backlog pass
replayed every one of them. Only a late REPLY was receipted given up (ticket cd2d27fe3261);
the request itself still ran. Akien's answer (via the orchestrator, open-98ebd82e7a02): refuse
before delivery only. A handler already running is not cancelled.

One tooth per numbered falsifier clause. Each counts what a fixture device took:

  1. test_a_request_past_its_deadline_is_not_run: the addressee's lock is held while a request
     to it times out. Once the lock frees, the request is receipted ``bus-asker-gave-up`` and
     the device never takes it; a plain mail queued behind the same lock is taken.
  2. test_a_handed_over_ask_is_not_replayed: bus life A holds an unanswered ask and a plain
     mail and stops (hand_over_asks). Bus life B, over the same table, takes the asks over and
     wires the addressee. The ask is receipted given up and never taken; the mail is taken.
  3. test_a_request_whose_socket_closed_is_not_run: on a real bus process, a client sends a
     request over the socket while the addressee's lock is held, then closes the socket. Once
     the lock frees, the request is receipted given up and never taken; the mail is taken.

Requires Postgres; every bus rides BusDevice.scratch and drops at close. Tooth 3 runs
``serve`` in a driver subprocess at a scratch home (the method of
test_a_reply_across_a_bus_stop_is_receipted.py).

    bin/cairn test cairn/devices/cairn/machines/bus/proofs/test_a_gone_clients_request_is_not_run.py
"""
from __future__ import annotations

import atexit
import contextlib
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"ee88c2126abc": {
    "1": "test_a_request_past_its_deadline_is_not_run",
    "2": "test_a_handed_over_ask_is_not_replayed",
    "3": "test_a_request_whose_socket_closed_is_not_run",
}}

_X = "testing-ee88c2126abc-x"
_ASKER = "testing-ee88c2126abc-asker"
_GAVE_UP = "bus-asker-gave-up"
_RUN_S = 90.0

# The fixture device and shim. Tooth 3's driver execs this same text, so the two agree.
_FIXTURE = r'''
from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim


class _Took(BaseDevice):
    """Takes whatever it is handed and remembers it."""

    def __init__(self):
        super().__init__()
        self.took = []

    def intention(self):
        return {"what": "testing-ee88c2126abc taker"}

    def state(self):
        return {"took": len(self.took)}

    def settings(self):
        return {}

    def receive(self, envelope):
        self.took.append(envelope["id"])
        return {"took": envelope["id"]}


class _Sleeper(BaseShim):
    def __init__(self, device_id, bus):
        super().__init__(bus=bus)
        self._device_id = device_id
        self.dev = _Took()

    @property
    def device_id(self):
        return self._device_id

    def _start_device(self):
        return self.dev


class _Inbox:
    def __init__(self):
        self.records = []

    def receive_diagnostic(self, record):
        self.records.append(record)
'''
_fx: dict = {}
exec(_FIXTURE, _fx)  # noqa: S102 — the fixture text above, shared with tooth 3's driver

_SCRATCH = contextlib.ExitStack()
atexit.register(_SCRATCH.close)


def _held_shim(bus, proc):
    shim = _fx["_Sleeper"](_X, bus)
    shim.set_diagnostic_receiver(_fx["_Inbox"]())
    proc.roster.hold(shim)
    return shim


def _mail(bus, why: str) -> dict:
    return bus.post(sender=_ASKER, to=_X, channel="personal", why=f"testing-ee88c2126abc {why}")


def _receipts(bus, envelope_id: str) -> list:
    from cairn.devices.db_domain.tools.client import store
    bus.flush()
    return [r["by"] for r in store.read(bus.delivery_table, where="envelope = %s",
                                        params=(envelope_id,))]


@contextlib.contextmanager
def _lock_held(proc, device_id: str):
    """Hold ``device_id``'s shim lock on another thread for the body's length."""
    held, release = threading.Event(), threading.Event()

    def hold():
        with proc._holding(device_id):
            held.set()
            release.wait(30)

    t = threading.Thread(target=hold, daemon=True)
    t.start()
    assert held.wait(5), f"could not hold {device_id}'s lock"
    try:
        yield
    finally:
        release.set()
        t.join(10)


def test_a_request_past_its_deadline_is_not_run():
    from cairn.devices.cairn.machines.bus.bus import BusDevice
    from cairn.devices.cairn.machines.bus.server import BusProcess
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_gone_deadline"))
    bus.set_diagnostic_receiver(_fx["_Inbox"]())
    proc = BusProcess(bus)
    x = _held_shim(bus, proc)
    _mail(bus, "warm-up: wires the fixture")
    with _lock_held(proc, _X):
        try:
            bus.request(sender=_ASKER, to=_X, why="testing-ee88c2126abc the ask", timeout=0.5)
        except TimeoutError:
            pass
        else:
            raise AssertionError("the request was answered while its addressee's lock was held")
        ask = [e for e in bus.read(to=_X) if e.get("why") == "testing-ee88c2126abc the ask"]
        assert len(ask) == 1, ask
        plain = _mail(bus, "plain mail behind the same lock")
    assert plain["id"] in x.dev.took, f"the drain never ran: the plain mail was not taken ({x.dev.took})"
    assert ask[0]["id"] not in x.dev.took, "a request whose asker reached its deadline was run"
    assert _receipts(bus, ask[0]["id"]) == [_GAVE_UP], (
        f"the abandoned request's receipts: {_receipts(bus, ask[0]['id'])}")


def test_a_handed_over_ask_is_not_replayed():
    from cairn.devices.cairn.machines.bus.bus import BusDevice
    from cairn.devices.cairn.machines.bus.server import BusProcess
    from cairn.tools.scratch.scratch import scratch_dir
    asks = scratch_dir("testing-ee88c2126abc-asks-") / "asks_in_flight.json"
    a = _SCRATCH.enter_context(BusDevice.scratch("bus_gone_restart"))
    ask = a.post(sender=_ASKER, to=_X, channel="personal", why="testing-ee88c2126abc the ask",
                 _asked=True)
    plain = _mail(a, "plain mail from life A")
    a.flush()
    assert a.hand_over_asks(asks)["handed_over"] == 1, "life A handed over no ask"
    b = BusDevice(table=a.table, device_id="bus")
    b.set_diagnostic_receiver(_fx["_Inbox"]())
    assert b.take_over_asks(asks)["taken_over"] == 1, "life B took over no ask"
    proc = BusProcess(b)
    x = _held_shim(b, proc)
    proc.hold_name(_X)
    assert plain["id"] in x.dev.took, f"life B never drained the backlog: {x.dev.took}"
    assert ask["id"] not in x.dev.took, "a handed-over ask was replayed after the restart"
    assert _receipts(b, ask["id"]) == [_GAVE_UP], f"the handed-over ask's receipts: {_receipts(b, ask['id'])}"


_DRIVER = r"""
import json, socket, sys, threading, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
home, X, ASKER, FIXTURE = Path(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
from cairn.devices.cairn.machines.bus import server
from cairn.devices.cairn.machines.bus.bus import BusDevice
from cairn.devices.db_domain.tools.client import store
fx = {}
exec(Path(FIXTURE).read_text(), fx)
real = server._Server.serve_forever
with BusDevice.scratch("bus_gone_socket") as bus:
    def _forever(self, poll_interval=0.5):
        t = threading.Thread(target=real, args=(self,), kwargs={"poll_interval": 0.1}, daemon=True)
        t.start()
        out = {}
        try:
            for th in threading.enumerate():
                if th.name == "bus-backlog":
                    th.join(timeout=30)
            proc = self.process
            shim = fx["_Sleeper"](X, bus)
            shim.set_diagnostic_receiver(fx["_Inbox"]())
            proc.roster.hold(shim)
            bus.post(sender=ASKER, to=X, channel="personal", why="testing-ee88c2126abc warm-up")
            held, release = threading.Event(), threading.Event()
            def hold():
                with proc._holding(X):
                    held.set()
                    release.wait(30)
            h = threading.Thread(target=hold, daemon=True)
            h.start()
            assert held.wait(5)
            why = "testing-ee88c2126abc the ask over a socket"
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(str(home / "bus.sock"))
            s.sendall((json.dumps({"op": "call", "method": "request", "kwargs": {
                "sender": ASKER, "to": X, "why": why, "timeout": 8}}) + "\n").encode())
            deadline = time.monotonic() + 5
            ask = []
            while not ask and time.monotonic() < deadline:
                ask = [e["id"] for e in bus.read(to=X) if e.get("why") == why]
                time.sleep(0.05)
            s.close()
            time.sleep(1.5)
            plain = bus.post(sender=ASKER, to=X, channel="personal", why="testing-ee88c2126abc plain mail")
            release.set()
            h.join(10)
            bus.flush()
            out = {"ask": ask, "plain_taken": plain["id"] in shim.dev.took,
                   "ask_taken": bool(ask) and ask[0] in shim.dev.took,
                   "by": [r["by"] for r in store.read(bus.delivery_table, where="envelope = %s",
                                                      params=(ask[0],))] if ask else []}
        except Exception as exc:
            out = {"error": f"{type(exc).__name__}: {exc}"}
        finally:
            (home / "measured.json").write_text(json.dumps(out))
            self.shutdown()
            t.join(10)
    server._Server.serve_forever = _forever
    sys.exit(server.serve(home, bus, lan=0, scratch=True))
"""


def test_a_request_whose_socket_closed_is_not_run():
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("testing-ee88c2126abc-socket-")
    fixture = home / "fixture.py"
    fixture.write_text(_FIXTURE, encoding="utf-8")
    env = dict(os.environ)
    env["CAIRN_BUS_HOME"] = str(home)
    env["PYTHONPATH"] = str(_REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    r = subprocess.run([sys.executable, "-c", _DRIVER, str(_REPO), str(home), _X, _ASKER,
                        str(fixture)], cwd=str(_REPO), env=env, capture_output=True, text=True,
                       timeout=_RUN_S)
    measured = home / "measured.json"
    assert measured.is_file(), f"the driver measured nothing (exit {r.returncode}): {(r.stdout + r.stderr)[-1200:]}"
    got = json.loads(measured.read_text())
    assert "error" not in got, f"the driver failed: {got['error']}"
    assert got["ask"], "the request never reached the bus"
    assert got["plain_taken"], "the drain never ran: the plain mail was not taken"
    assert not got["ask_taken"], "a request whose client closed its socket was run"
    assert got["by"] == [_GAVE_UP], f"the gone client's request's receipts: {got['by']}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
