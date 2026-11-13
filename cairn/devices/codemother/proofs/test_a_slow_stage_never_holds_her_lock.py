"""Proof for ticket e4714e460e32 — a slow chart stage never holds codemother's lock.

Measured 2026-11-12 on akiendelllinux: b0e65cf8a77e's constrain ran 44 tester proofs one after
another inside ``queueme`` (1858 s, 18:36-19:07), and every other box's deposit, chart and verdict
waited behind codemother's one shim lock the whole time. The fix: a deferred gate queues the
ticket, returns at once, and answers from its own worker by ``reply_to``.

The world. The stage is HELD OPEN by putting a door in place of the stage's own (``gate._door``)
that blocks on an event, so "slow" is a fact the proof controls, not a clock it waits on. The
ticket is a stand-in that records what the gate asks of it (``drafted``, ``berth``, ``berthed``,
``failed``): this proof measures the gate, and the Ticket class is proved where it lives. Tooth 1
runs the real codemother shim on a scratch bus whose delivery is wrapped in one lock per device,
the shape the bus process installs (``cairn/devices/cairn/machines/bus/server.py`` ``_locked_hook``,
one RLock per held shim), so a verb that does not return holds her mail exactly as it does live.

    bin/cairn test cairn/devices/codemother/proofs/test_a_slow_stage_never_holds_her_lock.py
"""

from __future__ import annotations

import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "e4714e460e32": {
        "1": "test_a_deposit_is_answered_while_a_stage_is_held",
        "2": "test_the_held_stage_replies_by_reply_to_with_its_berth",
        "3": "test_a_door_that_raises_still_replies_and_fails_the_ticket",
        "4": "test_two_tickets_at_one_gate_run_one_after_the_other",
    },
}

_WAIT = 10.0  # clause 1's bound, and every reply's


class _Ticket:
    """A stand-in for the ticket the gate instantiates: it records what the gate asks of it."""

    def __init__(self, tid: str) -> None:
        self.id = tid
        self.fileref = f"/scratch/{tid}.json"
        self.berthed_calls: list[tuple] = []
        self.failed_calls: list[list] = []

    def drafted(self, stage):
        return {"draft_for": stage}

    def berth(self, stage):
        return f"/scratch/berths/{stage}-{self.id}.json"

    def berthed(self, stage, berth, *, why):
        self.berthed_calls.append((stage, str(berth)))

    def failed(self, lacks, *, participant, actor, why, **journal):
        self.failed_calls.append(list(lacks))
        return {"workflow": "code-seam@v2: THINKME -> TICKETME -> [BUILDME:failed]", "trouble": None}


class _Spy:
    """The gate's participant: every post recorded, and a wait for the reply to one envelope."""

    def __init__(self) -> None:
        self.posts: list[dict] = []
        self._cv = threading.Condition()

    def post(self, **kw):
        with self._cv:
            self.posts.append(kw)
            self._cv.notify_all()
        return {"id": "spy"}

    def request(self, **kw):
        return {"accepted": True}

    def reply_to(self, envelope_id: str, timeout: float = _WAIT) -> dict | None:
        end = time.monotonic() + timeout
        with self._cv:
            while True:
                for p in self.posts:
                    if p.get("reply_to") == envelope_id:
                        return p
                left = end - time.monotonic()
                if left <= 0:
                    return None
                self._cv.wait(left)


@contextmanager
def _world(door, tickets: dict):
    """The gate's door replaced by ``door``, ``Ticket.at`` answering from ``tickets`` by fileref,
    and the fail journal read as empty; each restored on exit."""
    from cairn.devices.codemother.machines.chart_gate import gate as G
    from cairn.devices.codemother.machines.clearance import gate as C
    from cairn.machines.ticket.ticket import Ticket
    saved = (G._door, Ticket.__dict__["at"], C.journal_of)
    G._door = lambda stage: door
    Ticket.at = classmethod(lambda cls, fileref, **kw: tickets[fileref])
    C.journal_of = lambda ticket, **kw: {}
    try:
        yield
    finally:
        G._door, Ticket.at, C.journal_of = saved[0], saved[1], saved[2]


def _held_door():
    """A door that blocks until released, and says when a stage has entered it."""
    entered, release = threading.Event(), threading.Event()

    def door(packet, **kw):
        entered.set()
        release.wait(60)
        return f"/scratch/berths/constrain-{packet['ticket']}-held.json"
    return door, entered, release


def _envelope(tid: str, n: int = 0) -> dict:
    return {"id": f"env-{tid}-{n}", "sender": "proof_asker", "verb": "queueme",
            "body": {"fileref": tid}}


def _deferred_gate(stage: str, spy):
    from cairn.devices.codemother.machines.chart_gate.gate import StageGate
    return StageGate(stage, participant=spy, deferred=True)


def _queue_and_time(gate, envelope) -> tuple[object, float]:
    """``queueme`` run on its own thread, so a gate that holds the call cannot hang the proof."""
    out: dict = {}

    def call():
        t0 = time.monotonic()
        out["got"] = gate.queueme(envelope)
        out["s"] = time.monotonic() - t0
    th = threading.Thread(target=call, daemon=True)
    th.start()
    th.join(_WAIT)
    return out.get("got", "still running"), out.get("s", float("inf"))


def test_a_deposit_is_answered_while_a_stage_is_held():
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import scratch_bus
    from cairn.tools.bus_client import _load_device_shim
    door, entered, release = _held_door()
    tid = "e4714e4600c1"
    locks: dict[str, threading.RLock] = {}

    def one_lock_per_device(device_id, hook):  # server.py _locked_hook's shape
        lock = locks.setdefault(device_id, threading.RLock())  # server.py: one RLock per shim

        def locked(envelope):
            with lock:
                return hook(envelope)
        return locked

    with _world(door, {tid: _Ticket(tid)}), scratch_bus("e4714_held_stage") as bus:
        bus.set_delivery_wrapper(one_lock_per_device)
        shim = _load_device_shim("codemother", bus)
        shim._wire_delivery()
        asker = threading.Thread(target=lambda: bus.post(
            sender="proof_asker", to="codemother", channel="personal",
            verb="machines/constrain/queueme",
            body={"fileref": tid}, why="e4714 clause 1: hold the constrain stage open"),
            daemon=True)
        try:
            asker.start()
            assert entered.wait(_WAIT), "the constrain stage never entered its door"
            got: dict = {}

            def ask():
                t0 = time.monotonic()
                got["reply"] = bus.request(sender="proof_asker", to="codemother",
                                           channel="personal", verb="deposit", body={},
                                           why="e4714 clause 1: a deposit while a stage is held",
                                           timeout=_WAIT)
                got["s"] = time.monotonic() - t0
            th = threading.Thread(target=ask, daemon=True)
            th.start()
            th.join(_WAIT + 1)
            assert "reply" in got, ("the deposit was not answered within "
                                    f"{_WAIT:.0f} s while the constrain stage was held")
            assert got["s"] <= _WAIT, got
            body = got["reply"].get("body") or got["reply"]
            assert body.get("verb") == "deposit" or "deposit" in str(body), got["reply"]
        finally:
            release.set()
            asker.join(_WAIT)
            from cairn.devices.codemother.machines.chart_gate import gate as G
            getattr(G, "settled", lambda stage: None)("constrain")
    print(f"ok test_a_deposit_is_answered_while_a_stage_is_held ({got['s']:.2f} s)")


def test_the_held_stage_replies_by_reply_to_with_its_berth():
    door, entered, release = _held_door()
    tid = "e4714e4600c2"
    ticket, spy = _Ticket(tid), _Spy()
    with _world(door, {tid: ticket}):
        gate = _deferred_gate("constrain", spy)
        env = _envelope(tid)
        try:
            got, s = _queue_and_time(gate, env)
            assert got is None and s < 1.0, (f"queueme held the call {s:.2f} s while the stage "
                                             f"ran, and returned {got!r}")
            assert entered.wait(_WAIT), "the queued stage never ran"
            assert spy.reply_to(env["id"], timeout=0.2) is None, "replied before the stage ended"
        finally:
            release.set()
        reply = spy.reply_to(env["id"])
        assert reply is not None, "the released stage posted no reply by reply_to"
        assert reply["to"] == "proof_asker", reply
        body = reply["body"]
        berth = f"/scratch/berths/constrain-{tid}-held.json"
        assert body.get("passed") is True and body.get("berth") == berth, body
        assert body.get("ticket") == tid and body.get("stage") == "constrain", body
        assert ticket.berthed_calls == [("constrain", berth)], ticket.berthed_calls
        assert any(p.get("verb") == "deposit" and p["body"] == {"berth": berth}
                   for p in spy.posts), spy.posts
    print("ok test_the_held_stage_replies_by_reply_to_with_its_berth")


def test_a_door_that_raises_still_replies_and_fails_the_ticket():
    for exc in (RuntimeError("the constrain door refused: no bounds"),
                TypeError("an unexpected raise the gate does not name")):
        tid = "e4714e4600c3"
        ticket, spy = _Ticket(tid), _Spy()

        def door(packet, _exc=exc, **kw):
            raise _exc
        with _world(door, {tid: ticket}):
            gate = _deferred_gate("constrain", spy)
            env = _envelope(tid)
            got, s = _queue_and_time(gate, env)
            assert got is None, got
            reply = spy.reply_to(env["id"])
            assert reply is not None, f"a door raising {type(exc).__name__} left the asker unanswered"
            body = reply["body"]
            assert body.get("passed") is False, body
            assert any(str(exc) in lack.get("why", "") for lack in body.get("lacks") or []), body
            assert len(ticket.failed_calls) == 1 and str(exc) in str(ticket.failed_calls[0]), \
                ticket.failed_calls
            assert ticket.berthed_calls == [], ticket.berthed_calls
    print("ok test_a_door_that_raises_still_replies_and_fails_the_ticket")


def test_two_tickets_at_one_gate_run_one_after_the_other():
    a, b = "e4714e4600c4", "e4714e4600c5"
    live, peak, order = [0], [0], []
    guard = threading.Lock()

    def door(packet, **kw):
        with guard:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
            order.append(("in", packet["ticket"]))
        time.sleep(0.3)
        with guard:
            live[0] -= 1
            order.append(("out", packet["ticket"]))
        return f"/scratch/berths/constrain-{packet['ticket']}.json"
    spy = _Spy()
    with _world(door, {a: _Ticket(a), b: _Ticket(b)}):
        # two gate objects for one stage: her device builds its gates afresh at each lookup
        ea, eb = _envelope(a), _envelope(b)
        got_a, _ = _queue_and_time(_deferred_gate("constrain", spy), ea)
        got_b, _ = _queue_and_time(_deferred_gate("constrain", spy), eb)
        assert got_a is None and got_b is None, (got_a, got_b)
        ra, rb = spy.reply_to(ea["id"]), spy.reply_to(eb["id"])
        assert ra and rb and ra["body"]["passed"] and rb["body"]["passed"], (ra, rb)
    assert peak[0] == 1, f"{peak[0]} stages ran at once at one gate"
    assert order == [("in", a), ("out", a), ("in", b), ("out", b)], order
    print("ok test_two_tickets_at_one_gate_run_one_after_the_other")


def main() -> int:
    failed = 0
    for name in PROVES["e4714e460e32"].values():
        try:
            globals()[name]()
        except Exception as exc:  # noqa: BLE001 — every tooth runs; each red is named
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
