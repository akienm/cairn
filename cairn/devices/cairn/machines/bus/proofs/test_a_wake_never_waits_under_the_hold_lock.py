"""PROOF for ticket 445e66f32ba0: waking a shim never waits on another shim while holding the bus's hold lock.

Read 2026-10-18 off server.py: ``hold_name`` and ``hold_class`` take the one ``_hold_lock``
and, still holding it, ``_wire`` waits on the shim's own lock. So a thread answering a cold
verb on shim X (X's lock held) whose handler mails a sleeping Y waits on ``_hold_lock``,
while a second thread waking X for its mail holds ``_hold_lock`` and waits on X's lock —
each holds what the other waits on. ``_holding``'s wait serves only the queues of locks the
waiter already holds, and the second thread holds none, so nothing breaks the cycle. And
while one shim is busy, every other wake on the bus queues behind ``_hold_lock``.

The teeth, each on its own scratch bus:

  * a verb that mails a sleeper while its own mail arrives finishes — the two-thread cycle
    above, on public paths (``op_verbs`` and ``post``); both threads end inside 10s;
  * a busy shim never stalls an unrelated wake — while X's verb handler is still working
    and X's mail is waiting on X, mail to an unrelated sleeper Z is taken inside 2s;
  * a shim woken from two threads at once is wired once — two concurrent posts to one
    sleeper start its device once and both envelopes are taken.

Every bus rides ``BusDevice.scratch``; every name is ``testing-a1d2-...`` so a leak explains
itself; the bus's diagnostics go to a list, never the live trouble lane. Threads are daemons,
so a red cycle cannot keep the proof from exiting.

    python3 cairn/devices/cairn/machines/bus/proofs/test_a_wake_never_waits_under_the_hold_lock.py
"""
from __future__ import annotations

import contextlib
import sys
import threading
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.tools.base.shim import BaseShim  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.server import BusProcess  # noqa: E402

# Keyed to the ticket falsifier's clause markers (1)-(3).
PROVES = {"445e66f32ba0": {
    "1": "a_verb_that_mails_a_sleeper_while_its_own_mail_arrives_finishes",
    "2": "a_busy_shim_never_stalls_an_unrelated_wake",
    "3": "a_shim_woken_from_two_threads_is_wired_once",
}}

_SCRATCH = contextlib.ExitStack()
PASS = 0
FAIL = 0


class _Took(BaseDevice):
    """Takes whatever it is handed and remembers it."""

    def __init__(self) -> None:
        super().__init__()
        self.took: list[str] = []

    def intention(self) -> dict:
        return {"what": "testing-a1d2 taker"}

    def state(self) -> dict:
        return {"took": len(self.took)}

    def settings(self) -> dict:
        return {}

    def receive(self, envelope: dict):
        self.took.append(envelope["id"])
        return {"took": envelope["id"]}


class _Sleeper(BaseShim):
    """A shim whose device is asleep until mail wakes it; counts the wakes. ``on_verb``, when
    set, runs as the shim's verb handler — on the thread ``op_verbs`` answers on."""

    def __init__(self, device_id: str, bus) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self.wakes = 0
        self.dev = _Took()
        self.on_verb = None

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        self.wakes += 1
        time.sleep(0.2)  # a device takes a moment to start, so two wakes can overlap
        return self.dev

    def resolve(self, argv: list[str]) -> dict:
        if self.on_verb is not None:
            self.on_verb()
            return {"exit": 0, "text": "testing-a1d2 answered"}
        return super().resolve(argv)


class _Inbox:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)


def _rig(*names):
    """A scratch bus, its bus process, and one sleeping shim per name, held UNWIRED."""
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_a1d2"))
    bus.set_diagnostic_receiver(_Inbox())
    proc = BusProcess(bus)
    held = []
    for name in names:
        shim = _Sleeper(name, bus)
        shim.set_diagnostic_receiver(_Inbox())
        proc.roster.hold(shim)
        held.append(shim)
    return bus, proc, held


def _thread(fn) -> threading.Thread:
    t = threading.Thread(target=fn, daemon=True)
    t.start()
    return t


def _mail(bus, to: str) -> dict:
    return bus.post(sender="testing-a1d2-sender", to=to, channel="personal",
                    why=f"testing-a1d2 mail for {to}")


def a_verb_that_mails_a_sleeper_while_its_own_mail_arrives_finishes():
    bus, proc, (x, y) = _rig("testing-a1d2-x", "testing-a1d2-y")
    in_handler = threading.Event()
    mailed = {}

    def handler():
        in_handler.set()
        time.sleep(0.5)  # X's own mail is now waking X, and waits on X's lock
        mailed["y"] = _mail(bus, "testing-a1d2-y")

    x.on_verb = handler
    a = _thread(lambda: proc.answer({"op": "verbs", "device": "testing-a1d2-x",
                                     "verbs": ["testing-a1d2-verb"]}, in_process=True))
    assert in_handler.wait(5), "X's verb handler never ran"
    b = _thread(lambda: mailed.setdefault("x", _mail(bus, "testing-a1d2-x")))
    a.join(10)
    b.join(10)
    stuck = [n for n, t in (("the verb on X", a), ("the mail to X", b)) if t.is_alive()]
    assert not stuck, f"still waiting after 10s: {', '.join(stuck)} — each holds what the other waits on"
    assert mailed["y"]["id"] in y.dev.took and mailed["x"]["id"] in x.dev.took, (
        f"both finished but the mail was not taken: x took {x.dev.took}, y took {y.dev.took}")


def a_busy_shim_never_stalls_an_unrelated_wake():
    bus, proc, (x, z) = _rig("testing-a1d2-x", "testing-a1d2-z")
    in_handler = threading.Event()
    release = threading.Event()

    def handler():
        in_handler.set()
        release.wait(15)

    x.on_verb = handler
    a = _thread(lambda: proc.answer({"op": "verbs", "device": "testing-a1d2-x",
                                     "verbs": ["testing-a1d2-verb"]}, in_process=True))
    try:
        assert in_handler.wait(5), "X's verb handler never ran"
        _thread(lambda: _mail(bus, "testing-a1d2-x"))
        time.sleep(0.5)  # X's mail is waking X, and waits on X's busy lock
        took = {}
        c = _thread(lambda: took.setdefault("z", _mail(bus, "testing-a1d2-z")))
        c.join(2)
        assert not c.is_alive(), "mail to an unrelated sleeper waited 2s behind a busy shim"
        assert took["z"]["id"] in z.dev.took, f"z did not take its mail: {z.dev.took}"
    finally:
        release.set()
        a.join(10)


def a_shim_woken_from_two_threads_is_wired_once():
    bus, proc, (w,) = _rig("testing-a1d2-w")
    got = []
    ts = [_thread(lambda: got.append(_mail(bus, "testing-a1d2-w"))) for _ in range(2)]
    for t in ts:
        t.join(10)
    assert not any(t.is_alive() for t in ts), "a concurrent wake did not finish in 10s"
    assert w.wakes == 1, f"one sleeper woken from two threads started its device {w.wakes} times"
    assert {e["id"] for e in got} <= set(w.dev.took), (
        f"an envelope was not taken: posted {[e['id'] for e in got]}, took {w.dev.took}")


TEETH = [a_verb_that_mails_a_sleeper_while_its_own_mail_arrives_finishes,
         a_busy_shim_never_stalls_an_unrelated_wake,
         a_shim_woken_from_two_threads_is_wired_once]


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {fn.__name__}")


if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn)
    finally:
        _SCRATCH.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
