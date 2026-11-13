"""PROOF for ticket d58e7887cc99: constrain's floor waits the stage budget for the tester.

Measured 2026-11-12 on akiendelllinux: b0e65cf8a77e's floor ran 55 tester proofs, 5 of them
over 180 s, the longest 1040.8 s. constrain asks the tester's run verb with a timeout, and the
tester's handler runs inside the bus process. Since 4d597cac9f5d (7ae315843) bus.request's
timeout bounds that in-process handler, so with timeout=180 every proof over three minutes
raised TimeoutError, and ``_ask_once`` recorded it as unrunnable. The fix: the floor asks with
STAGE_BUDGET_S, imported from cairn/machines/ticket/ticket.py at call time, not copied.

The world. A scratch bus carries a stub ``tester`` wired by ``wire_delivery``. Its handler
sleeps for a time the proof sets, then replies by ``reply_to`` with ``body.record``, the shape
the tester's run verb hands back. ``bus_client.reach`` is patched to a wrapper that SCALES
every requested timeout by 0.001, so the old 180 s is 0.18 s and the 3600 s budget is 3.6 s.
The delays are scaled by patching the timeout, not by sleeping for real. Each ask runs on a
daemon thread with a join bound, so a red cannot hang the proof.

One tooth per numbered falsifier clause:

  1. A RUN LONGER THAN THE OLD 180 S IS READ: a 200 s run (0.2 s scaled) comes back from
     ``_ask_once`` as the tester's green. On 7ae315843 it comes back unrunnable.
  2. THE BUDGET IS IMPORTED, READ AT CALL TIME: with ticket.STAGE_BUDGET_S patched to 1234.0,
     the ask carries timeout 1234.0.
  3. THE BUDGET STILL BOUNDS: a run past the budget (3700 s, 3.7 s scaled) comes back
     unrunnable, naming TimeoutError.

Requires Postgres; the bus rides BusDevice.scratch and drops at close.

    bin/cairn test cairn/devices/codemother/machines/constrain/proofs/test_the_floor_waits_the_stage_budget_for_the_tester.py
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

PROVES = {"d58e7887cc99": {
    "1": "a_run_longer_than_the_old_180_s_is_read",
    "2": "the_budget_is_imported_and_read_at_call_time",
    "3": "the_budget_still_bounds",
}}

SCALE = 0.001  # 180 s -> 0.18 s; 3600 s -> 3.6 s
_SCRATCH = contextlib.ExitStack()
PASS = 0
FAIL = 0


class _Scaled:
    """The bus constrain reaches: every request's timeout scaled, and each one recorded."""

    def __init__(self, bus) -> None:
        self._bus = bus
        self.asked: list[float] = []

    def request(self, **kw):
        self.asked.append(kw.get("timeout"))
        kw["timeout"] = kw["timeout"] * SCALE
        return self._bus.request(**kw)

    def __getattr__(self, name):
        return getattr(self._bus, name)


@contextlib.contextmanager
def _world(run_s: float):
    """A stub tester whose run takes ``run_s`` (scaled seconds), reached by constrain."""
    from cairn.devices.cairn.machines.bus.bus import BusDevice
    from cairn.tools.bus_client import bus_client
    bus = _SCRATCH.enter_context(BusDevice.scratch("constrain_budget"))

    def tester(envelope):
        if envelope.get("reply_to"):
            return
        time.sleep(run_s * SCALE)
        bus.post(sender="tester", to=envelope["sender"], channel="personal",
                 why="testing-d58e7887cc99 the stub tester's record",
                 body={"record": {"verdict": "green", "path": envelope["body"]["path"]}},
                 reply_to=envelope["id"])
    bus.wire_delivery("tester", tester)
    scaled = _Scaled(bus)
    saved = bus_client.reach
    bus_client.reach = lambda *names, **kw: scaled
    try:
        yield scaled
    finally:
        bus_client.reach = saved


def _ask_once(bound_s: float) -> dict:
    """constrain's own ``_ask_once`` on a daemon thread; what it returned, or that it hung."""
    from cairn.devices.codemother.machines.constrain import constrain
    out: dict = {}
    th = threading.Thread(
        target=lambda: out.update(state=constrain._ask_once("/scratch/test_slow_proof.py")),
        daemon=True)
    th.start()
    th.join(bound_s)
    return out.get("state") or {"verdict": "still running after %.1f s" % bound_s}


def a_run_longer_than_the_old_180_s_is_read():
    with _world(200.0) as scaled:
        state = _ask_once(10.0)
    assert state.get("verdict") == "green", (
        f"a 200 s tester run (scaled) under the floor's ask of timeout={scaled.asked} "
        f"came back {state!r}, not the tester's green")


def the_budget_is_imported_and_read_at_call_time():
    from cairn.machines.ticket import ticket
    saved = ticket.STAGE_BUDGET_S
    ticket.STAGE_BUDGET_S = 1234.0
    try:
        with _world(0.0) as scaled:
            state = _ask_once(10.0)
    finally:
        ticket.STAGE_BUDGET_S = saved
    assert scaled.asked == [1234.0], (
        f"with ticket.STAGE_BUDGET_S patched to 1234.0 the floor asked with timeout "
        f"{scaled.asked}")
    assert state.get("verdict") == "green", state


def the_budget_still_bounds():
    with _world(3700.0) as scaled:
        state = _ask_once(10.0)
    assert state.get("verdict") == "unrunnable", (
        f"a run past the budget (3700 s scaled, asked with {scaled.asked}) came back {state!r}")
    assert "TimeoutError" in str(state.get("how")), state


TEETH = [a_run_longer_than_the_old_180_s_is_read,
         the_budget_is_imported_and_read_at_call_time,
         the_budget_still_bounds]


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
