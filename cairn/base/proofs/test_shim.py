"""Proof for BaseShim — the device's always-on front: fires callbacks, receives mail, wakes.

The shim is where the goof is corrected: the ground_loop only BEATS; the FIRING lives here.
This proof exercises the three jobs against a spy bus (hermetic — no DB; the real bus is
proven in cairn/bus/proofs/test_bus.py, and the full heartbeat→shim→bus chain in the system
device's proof).

Teeth a hollow shim could not pass:
  - ON A PULSE, DUE CALLBACKS POKE THE BUS; held ones do not. The pulse-record names what
    fired and what held — a pulse is evidence (LEARNING, not silent RUNNING).
  - A BATCH DOES NOT DIE ON ONE BAD CALLBACK (CP2, Law 7): a trigger that raises becomes a
    permanent 'refused' entry and the rest still fire.
  - THE DEVICE IS STARTED ON DEMAND (the wake-to-a-poke): delivering mail wakes the device
    (its ``receive`` gets the envelope) and flips it running; a shim delivered to with no
    ``_start_device`` refuses loudly (CP1).
  - IT IS A SHIM (Law 2): composes CP1-CP6.

Runnable bare (no DB, no framework):
    python3 cairn/base/proofs/test_shim.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.callback import Callback
from cairn.base.core_values import CoreValuesMixin
from cairn.base.shim import BaseShim


class _SpyBus:
    """A stand-in for the bus that records posts — the shim's contract is 'it pokes via post'."""

    def __init__(self) -> None:
        self.posted: list[dict] = []

    def post(self, **envelope) -> dict:
        envelope = {"id": f"env{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope


class _Woken:
    """A minimal device the shim wakes on demand; records what it received."""

    def __init__(self) -> None:
        self.mail: list[dict] = []

    def receive(self, envelope: dict) -> str:
        self.mail.append(envelope)
        return "handled"


class _Shim(BaseShim):
    """A concrete shim carrying a fixed callback list and a device it wakes on demand."""

    def __init__(self, bus=None, callbacks=None) -> None:
        super().__init__(bus=bus)
        self._callbacks = callbacks or []
        self.started = 0

    @property
    def device_id(self) -> str:
        return "spec"

    def callbacks(self):
        return self._callbacks

    def _start_device(self):
        self.started += 1
        return _Woken()


def test_a_pulse_fires_due_callbacks_and_holds_the_rest():
    bus = _SpyBus()
    due = Callback(why="wake ops", trigger=lambda now, ctx: ctx.get("cpu", 0) >= 80,
                   to="ops/personal", body={"crossed": 80})
    not_due = Callback(why="wake night", trigger=lambda now, ctx: now == "midnight", to="night/personal")
    shim = _Shim(bus=bus, callbacks=[due, not_due])

    rec = shim.on_pulse(now="noon", context={"cpu": 95})

    assert rec["fired_count"] == 1 and len(rec["held"]) == 1
    assert len(bus.posted) == 1, "only the due callback pokes the bus"
    poke = bus.posted[0]
    assert poke["to"] == "ops/personal" and poke["sender"] == "spec"
    assert poke["body"] == {"crossed": 80}, "the poke carries only that the line was crossed"
    assert rec["held"][0]["to"] == "night/personal"


def test_a_batch_does_not_die_on_one_bad_callback():
    bus = _SpyBus()
    def boom(now, ctx):
        raise RuntimeError("trigger blew up")
    bad = Callback(why="explodes", trigger=boom, to="x/personal")
    good = Callback(why="fine", trigger=lambda now, ctx: True, to="y/personal")
    shim = _Shim(bus=bus, callbacks=[bad, good])

    rec = shim.on_pulse(now="noon")

    outcomes = {f["to"]: f["outcome"] for f in rec["fired"]}
    assert outcomes["x/personal"] == "refused" and "RuntimeError" in dict(
        (f["to"], f.get("error", "")) for f in rec["fired"])["x/personal"]
    assert outcomes["y/personal"] == "ok", "the good callback still fires after the bad one"
    assert len(bus.posted) == 1, "the kicked-back callback did not poke; the good one did"


def test_the_device_is_started_on_demand():
    shim = _Shim()
    assert not shim.running, "a shim starts with its device asleep"
    out = shim.deliver({"id": "e1", "body": {"hi": 1}})
    assert out == "handled" and shim.running and shim.started == 1
    # A second delivery does NOT restart the device — it is already awake.
    shim.deliver({"id": "e2"})
    assert shim.started == 1, "the device is woken once, then stays awake"


def test_a_shim_with_no_start_hook_refuses_loudly():
    class _NoStart(BaseShim):
        @property
        def device_id(self) -> str:
            return "nostart"
    try:
        _NoStart().deliver({"id": "e"})
        raise AssertionError("a shim delivered to with no _start_device must refuse loudly (CP1)")
    except NotImplementedError:
        pass


def test_it_is_a_shim():
    shim = _Shim()
    assert isinstance(shim, CoreValuesMixin), "a shim must compose the core values (Law 2)"
    assert [v.id for v in shim.CORE_VALUES] == ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]


def _main() -> int:
    for check in (test_a_pulse_fires_due_callbacks_and_holds_the_rest,
                  test_a_batch_does_not_die_on_one_bad_callback,
                  test_the_device_is_started_on_demand,
                  test_a_shim_with_no_start_hook_refuses_loudly,
                  test_it_is_a_shim):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — BaseShim: a pulse fires due callbacks onto the bus (holding the rest), a bad "
          "callback can't abort the batch, and the device is woken on demand")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
