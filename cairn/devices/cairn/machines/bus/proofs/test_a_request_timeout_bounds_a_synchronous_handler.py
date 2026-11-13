"""PROOF for ticket 4d597cac9f5d: bus.request's timeout bounds a synchronous in-process handler.

Measured 2026-11-12 on akiendelllinux: a chart stage's handler ran 581.7 s inside codemother's
verb, and its asker, which had asked with timeout=180, was answered after the full 581.7 s. The
cause was the order of request(). It called post(), and post()'s poke chain ran the target's
handler on the asker's own thread, before the deadline was even set. So a timeout bounded only
the remote path and never the in-process one.

The world. A bare scratch bus has a target wired by ``wire_delivery`` whose handler sleeps for a
time the proof sets, then posts its reply by ``reply_to``, the way a shim answers a verb. The
asker is unwired, like 'cairn'. Each ask runs on a daemon thread with a join bound, so a red
cannot hang the proof.

One tooth per numbered falsifier clause:

  1. A SLOW HANDLER DOES NOT HOLD THE ASKER: a handler that runs 3 s under timeout=0.5 raises
     TimeoutError to the asker within timeout + 1 s.
  2. A HANDLER INSIDE THE TIMEOUT STILL ANSWERS: a 0.05 s handler's reply is returned.
  3. THE SLOW HANDLER FINISHES AND ITS LATE REPLY IS RECEIPTED: after the TimeoutError the
     handler runs to its end, and its reply is receipted by='bus-asker-gave-up'. It is never
     left standing as fresh mail for the asker.

Requires Postgres; every bus rides BusDevice.scratch and drops at close.

    bin/cairn test cairn/devices/cairn/machines/bus/proofs/test_a_request_timeout_bounds_a_synchronous_handler.py
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

PROVES = {"4d597cac9f5d": {
    "1": "a_slow_handler_does_not_hold_the_asker",
    "2": "a_handler_inside_the_timeout_still_answers",
    "3": "the_slow_handler_finishes_and_its_late_reply_is_receipted",
}}

TIMEOUT = 0.5
SLOW = 3.0
_SCRATCH = contextlib.ExitStack()
PASS = 0
FAIL = 0


def _rig(slow_s: float, n: int):
    """A scratch bus whose target answers after ``slow_s``; returns (bus, target, asker, ended)."""
    from cairn.devices.cairn.machines.bus.bus import BusDevice
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_rtb"))
    target, asker = f"testing-slow-{n}", f"testing-asker-{n}"
    ended = threading.Event()

    def handler(envelope):
        if envelope.get("reply_to"):
            return
        time.sleep(slow_s)
        bus.post(sender=target, to=envelope["sender"], channel="personal",
                 why="testing-4d597cac9f5d the handler's reply", body={"answer": "done"},
                 reply_to=envelope["id"])
        ended.set()
    bus.wire_delivery(target, handler)
    return bus, target, asker, ended


def _ask(bus, target, asker) -> dict:
    """request() on its own thread; returns what it gave, what it raised, and how long it took."""
    out: dict = {}

    def call():
        t0 = time.monotonic()
        try:
            out["reply"] = bus.request(sender=asker, to=target, verb="run",
                                       why="testing-4d597cac9f5d the ask", timeout=TIMEOUT)
        except BaseException as exc:  # noqa: BLE001 — the proof reads it
            out["raised"] = exc
        out["s"] = time.monotonic() - t0
    th = threading.Thread(target=call, daemon=True)
    th.start()
    th.join(SLOW + 5)
    return out


def a_slow_handler_does_not_hold_the_asker():
    bus, target, asker, ended = _rig(SLOW, 1)
    out = _ask(bus, target, asker)
    assert "s" in out, f"request() was still running {SLOW + 5:.0f} s after it asked"
    assert isinstance(out.get("raised"), TimeoutError), (
        f"a {SLOW:.0f} s in-process handler held the asker {out['s']:.2f} s under "
        f"timeout={TIMEOUT} and it got {out.get('reply') or out.get('raised')!r}, "
        "not a TimeoutError")
    assert out["s"] <= TIMEOUT + 1.0, f"TimeoutError came after {out['s']:.2f} s"
    ended.wait(SLOW + 2)


def a_handler_inside_the_timeout_still_answers():
    bus, target, asker, _ = _rig(0.05, 2)
    out = _ask(bus, target, asker)
    assert "reply" in out, f"a 0.05 s handler was not answered: {out!r}"
    assert out["reply"]["body"] == {"answer": "done"}, out["reply"]


def the_slow_handler_finishes_and_its_late_reply_is_receipted():
    from cairn.devices.db_domain.tools.client import store
    bus, target, asker, ended = _rig(SLOW, 3)
    out = _ask(bus, target, asker)
    assert isinstance(out.get("raised"), TimeoutError), (
        f"the asker was not told it timed out: {out.get('reply') or out.get('raised')!r} "
        f"after {out.get('s', float('inf')):.2f} s")
    assert ended.wait(SLOW + 2), "the slow handler never ran to its end after the timeout"
    replies = [e for e in bus.read(to=asker) if e.get("reply_to")]
    assert len(replies) == 1, replies
    bus.flush()
    standing = {e["id"] for e in bus.undelivered(to=asker, limit=1000)}
    assert replies[0]["id"] not in standing, "the late reply stands as fresh mail for the asker"
    rows = store.read(bus.delivery_table, where="envelope = %s", params=(replies[0]["id"],))
    assert [r["by"] for r in rows] == ["bus-asker-gave-up"], rows


TEETH = [a_slow_handler_does_not_hold_the_asker,
         a_handler_inside_the_timeout_still_answers,
         the_slow_handler_finishes_and_its_late_reply_is_receipted]


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
