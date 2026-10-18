"""PROOF for ticket c2036433beaf: two shims that request each other at once both get answered.

Measured 2026-10-17 before the build (py-spy on scratch bus pid 87681): an ABBA deadlock
between the per-shim RLocks ``BusProcess._wire`` puts around each delivery hook. One thread
held codemother's lock (on_commit -> watch._escalate_to_hex -> a request to inference_domain)
and waited on inference_domain's; another held inference_domain's (an infer; its
``_check_mail`` delivered codemother's queued request and ``deliver`` posted the reply to
codemother) and waited on codemother's. The asker hung the full 900s client timeout.

One tooth per shape, each on its own scratch bus and its own pair of shims, so a red cannot
leave a lock held for the next tooth:

  * two shims that ask each other are both answered — A's ``ask`` handler and B's ``ask``
    handler each hold their own lock (a two-party barrier sees to it) and then request the
    other's ``echo``; 20 of 20 tries answered inside 10s;
  * a reply posted under the replier's lock reaches an asker holding its own — the measured
    shape: B is inside a handler, A's request lands in B's mailbox, B's own post re-enters
    its mailbox and answers A while A still holds A's lock; 20 of 20 inside 10s;
  * one shim's handlers never run on two threads at once — 48519f4789b1's property, read off
    every handler entry the two teeth above made;
  * every envelope is delivered once — no envelope id reaches a device's handler twice.

Each try runs in a daemon thread joined at the bound: a hang is a red, never a hung suite.
Every bus rides ``BusDevice.scratch``; every name is ``testing-c203-...`` so a leak explains
itself; diagnostics go to a list, never the live trouble lane.

    python3 cairn/devices/cairn/machines/bus/proofs/test_two_shims_ask_each_other.py
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

# "all" is the key the clearance gate joins on: the ticket's falsifier is unnumbered prose,
# so it asks for exactly one clause. The descriptive keys let the hollow runner attribute a
# reverted file to the tooth that reds.
PROVES = {"c2036433beaf": {
    "all": "two_shims_that_ask_each_other_are_both_answered",
    "two bus-hosted shims send each other requests at the same moment, both answered inside "
    "10s on 20 of 20 tries": "two_shims_that_ask_each_other_are_both_answered",
    "the measured shape: a reply posted under one shim's lock to an asker holding its own":
        "a_reply_under_the_repliers_lock_reaches_an_asker_holding_its_own",
    "one shim's hook never runs on two threads at once (48519f4789b1)":
        "one_shims_handlers_never_run_on_two_threads_at_once",
    "no envelope is delivered twice": "every_envelope_is_delivered_once",
}}

TRIES = 20
BOUND_S = 10.0

_SCRATCH = contextlib.ExitStack()
PASS = 0
FAIL = 0
# Every handler entry the rigs saw: (device_id, thread ident, envelope id).
_ENTRIES: list[tuple[str, int, str]] = []
_OVERLAPS: list[str] = []
_COMPLETED = {"mutual": 0, "under_lock": 0}


class _Inbox:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)


class _Peer(BaseDevice):
    """Answers ``ask`` (request the peer's echo, return what it said), ``echo`` and ``hold``;
    takes replies through ``receive``. Every entry is recorded with its thread."""

    def __init__(self, device_id: str, bus) -> None:
        super().__init__()
        self.device_id = device_id
        self.peer = ""
        self.bus = bus
        self.barrier: threading.Barrier | None = None
        self.entered = threading.Event()
        self._active: dict[int, int] = {}
        self._guard = threading.Lock()

    def intention(self) -> dict:
        return {"what": f"{self.device_id}: the c2036433beaf proof's peer fixture"}

    def state(self) -> dict:
        return {}

    def settings(self) -> dict:
        return {}

    def declared_verbs(self) -> dict:
        return {"ask": self._entry(self._ask), "echo": self._entry(self._echo),
                "hold": self._entry(self._hold)}

    def receive(self, envelope: dict):
        return self._entry(lambda e: {"took": e["id"]})(envelope)

    def _entry(self, fn):
        def run(envelope):
            me = threading.get_ident()
            with self._guard:
                others = [t for t, n in self._active.items() if n and t != me]
                if others:
                    _OVERLAPS.append(f"{self.device_id} entered on thread {me} while "
                                     f"{others} were inside it")
                self._active[me] = self._active.get(me, 0) + 1
                _ENTRIES.append((self.device_id, me, envelope["id"]))
            try:
                return fn(envelope)
            finally:
                with self._guard:
                    self._active[me] -= 1
        return run

    def _ask(self, envelope: dict) -> dict:
        if self.barrier is not None:
            self.barrier.wait(timeout=BOUND_S)
        reply = self.bus.request(sender=self.device_id, to=self.peer, verb="echo",
                                 why="testing-c203 ask the peer while holding my own lock",
                                 body={"n": envelope["body"].get("n")}, timeout=BOUND_S)
        return {"peer_said": reply.get("body")}

    def _echo(self, envelope: dict) -> dict:
        return {"echo": envelope["body"]}

    def _hold(self, envelope: dict) -> dict:
        """The measured shape's replier: wait inside this handler until the peer's request is
        in this mailbox, then post to self — the re-entry that delivered it under the lock."""
        self.entered.set()
        deadline = time.monotonic() + BOUND_S / 2
        while time.monotonic() < deadline:
            waiting = self.bus.undelivered(to=self.device_id, limit=200)
            if any(e.get("verb") == "echo" and e.get("sender") == self.peer for e in waiting):
                break
            time.sleep(0.01)
        self.bus.post(sender=self.device_id, to=self.device_id, channel="personal",
                      why="testing-c203 a note to self, re-entering my own mailbox",
                      body={"note": envelope["body"].get("n")})
        return {"held": envelope["body"].get("n")}


class _PeerShim(BaseShim):
    def __init__(self, device_id: str, bus) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self.dev = _Peer(device_id, bus)

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        return self.dev


def _rig(tag: str):
    """A scratch bus, its bus process, and two peer shims held AND wired — each one's
    delivery hook wrapped in its own lock, exactly as the live bus process holds them."""
    bus = _SCRATCH.enter_context(BusDevice.scratch(f"bus_c203_{tag}"))
    bus.set_diagnostic_receiver(_Inbox())
    proc = BusProcess(bus)
    a = _PeerShim(f"testing-c203-{tag}-a", bus)
    b = _PeerShim(f"testing-c203-{tag}-b", bus)
    a.dev.peer, b.dev.peer = b.device_id, a.device_id
    for shim in (a, b):
        shim.set_diagnostic_receiver(_Inbox())
        proc.roster.hold(shim)
        proc.hold_name(shim.device_id)
    return bus, a, b


def _ask_in_thread(bus, to: str, verb: str, n: int, out: dict, key: str):
    def run():
        try:
            out[key] = bus.request(sender=f"testing-c203-asker-{key}", to=to, verb=verb,
                                   why=f"testing-c203 try {n}", body={"n": n},
                                   timeout=BOUND_S)
        except Exception as exc:  # noqa: BLE001 — the tooth reports it
            out[key] = exc
    t = threading.Thread(target=run, daemon=True, name=f"testing-c203-{key}-{n}")
    t.start()
    return t


def _joined(threads, started: float) -> bool:
    for t in threads:
        t.join(max(0.0, BOUND_S - (time.monotonic() - started)))
    return not any(t.is_alive() for t in threads)


def two_shims_that_ask_each_other_are_both_answered():
    bus, a, b = _rig("mutual")
    for n in range(1, TRIES + 1):
        barrier = threading.Barrier(2)
        a.dev.barrier = b.dev.barrier = barrier
        out: dict = {}
        started = time.monotonic()
        threads = [_ask_in_thread(bus, a.device_id, "ask", n, out, "a"),
                   _ask_in_thread(bus, b.device_id, "ask", n, out, "b")]
        if not _joined(threads, started):
            raise AssertionError(f"try {n} of {TRIES}: still waiting at {BOUND_S}s — "
                                 "the two shims are deadlocked on each other's lock")
        for key in ("a", "b"):
            reply = out.get(key)
            if isinstance(reply, Exception):
                raise AssertionError(f"try {n}: {key}'s ask raised "
                                     f"{type(reply).__name__}: {reply}")
            said = ((reply or {}).get("body") or {}).get("peer_said") or {}
            if (said.get("echo") or {}).get("n") != n:
                raise AssertionError(f"try {n}: {key}'s ask came back without the peer's "
                                     f"echo of {n}: {reply}")
        _COMPLETED["mutual"] += 1


def a_reply_under_the_repliers_lock_reaches_an_asker_holding_its_own():
    bus, a, b = _rig("underlock")
    for n in range(1, TRIES + 1):
        b.dev.entered.clear()
        out: dict = {}
        started = time.monotonic()
        holder = _ask_in_thread(bus, b.device_id, "hold", n, out, "hold")
        if not b.dev.entered.wait(BOUND_S):
            raise AssertionError(f"try {n}: B's hold handler never ran")
        asker = _ask_in_thread(bus, a.device_id, "ask", n, out, "ask")
        if not _joined([holder, asker], started):
            raise AssertionError(f"try {n} of {TRIES}: still waiting at {BOUND_S}s — B's "
                                 "reply under its own lock cannot reach A, which holds A's")
        for key in ("hold", "ask"):
            if isinstance(out.get(key), Exception):
                raise AssertionError(f"try {n}: {key} raised {out[key]}")
        said = ((out["ask"] or {}).get("body") or {}).get("peer_said") or {}
        if (said.get("echo") or {}).get("n") != n:
            raise AssertionError(f"try {n}: A's ask came back without B's echo: {out['ask']}")
        _COMPLETED["under_lock"] += 1


def _both_ran() -> None:
    if _COMPLETED != {"mutual": TRIES, "under_lock": TRIES}:
        raise AssertionError(f"nothing to judge: the exchange teeth completed {_COMPLETED} "
                             f"of {TRIES} each")


def one_shims_handlers_never_run_on_two_threads_at_once():
    _both_ran()
    if _OVERLAPS:
        raise AssertionError(f"{len(_OVERLAPS)} overlap(s); first: {_OVERLAPS[0]}")
    threads = {t for _, t, _ in _ENTRIES}
    if len(threads) < 2:
        raise AssertionError(f"only {len(threads)} thread(s) ever entered a handler — the "
                             "rig never ran two at once, so the property was not exercised")


def every_envelope_is_delivered_once():
    _both_ran()
    seen: dict[tuple[str, str], int] = {}
    for device, _, eid in _ENTRIES:
        seen[(device, eid)] = seen.get((device, eid), 0) + 1
    twice = [k for k, n in seen.items() if n > 1]
    if twice:
        raise AssertionError(f"{len(twice)} envelope(s) delivered more than once; first: "
                             f"{twice[0]}")


TEETH = [two_shims_that_ask_each_other_are_both_answered,
         a_reply_under_the_repliers_lock_reaches_an_asker_holding_its_own,
         one_shims_handlers_never_run_on_two_threads_at_once,
         every_envelope_is_delivered_once]


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}", flush=True)
    else:
        PASS += 1
        print(f"  green {fn.__name__}", flush=True)


if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn)
    finally:
        _SCRATCH.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
