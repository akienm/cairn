"""Proof for ground_loop — THE HEARTBEAT. One pulse; nothing more.

This proof exercises the corrected shape: the heartbeat beats and pulses the shim of every
subscribed device; the FIRING lives in the shim. It composes the real BaseShim + Callback +
a spy bus, so the full beat → on_pulse → fire → poke chain is shown WITHOUT a DB (the
heartbeat holds no durable state — that is the whole point). The durable bus is proven
separately (cairn/bus/proofs/test_bus.py).

Teeth a hollow heartbeat could not pass:
  - A BEAT PULSES EVERY SUBSCRIBED SHIM, IN ORDER, and leaves a legible beat-record naming
    who was pulsed — a beat is evidence (LEARNING, not silent RUNNING).
  - THE FIRING IS THE SHIM'S: a callback due on this beat pokes the bus THROUGH its shim; one
    not due holds. The heartbeat itself pokes nothing.
  - SUBSCRIBE IS IDEMPOTENT by device_id; only a shim (device_id + on_pulse) may subscribe.
  - ONE SHIM RAISING CANNOT STOP THE BEAT reaching the others (CP2, Law 7).
  - THE GOOF IS GONE: no run_driver / no method registry — the heartbeat executes nothing.
  - IT IS A DEVICE (Law 2 / Form v0 #2).
  - THE ROSTER IS THE NAV (web-server child c): the heartbeat publishes roster() at ALL times —
    the devices it beats to, in order, each with live wakefulness — before the first beat too;
    a device absent from subscriptions is absent from the roster; the roster is DATA.

Runnable bare (NO DB, NO framework):
    python3 cairn/ground_loop/proofs/test_ground_loop.py     # exit 0 = green
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
from cairn.ground_loop.loop import GroundLoopDevice


class _SpyBus:
    def __init__(self) -> None:
        self.posted: list[dict] = []

    def post(self, **envelope) -> dict:
        envelope = {"id": f"env{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope


class _Shim(BaseShim):
    def __init__(self, device_id, bus=None, callbacks=None) -> None:
        super().__init__(bus=bus)
        self._id = device_id
        self._callbacks = callbacks or []

    @property
    def device_id(self) -> str:
        return self._id

    def callbacks(self):
        return self._callbacks

    def _start_device(self):
        return object()  # a minimal woken device — enough to flip running True


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
    due = Callback(why="wake ops", trigger=lambda now, ctx: ctx.get("hot"), to="ops/personal")
    idle = Callback(why="wake night", trigger=lambda now, ctx: False, to="night/personal")
    gl = GroundLoopDevice()
    gl.subscribe(_Shim("sensor", bus, callbacks=[due, idle]))

    gl.beat(now="t0", context={"hot": True})

    assert len(bus.posted) == 1 and bus.posted[0]["to"] == "ops/personal", \
        "the due callback pokes the bus through its shim; the heartbeat itself pokes nothing"
    # A beat where nothing is due pokes nobody.
    gl.beat(now="t1", context={"hot": False})
    assert len(bus.posted) == 1, "no callback due → no poke"


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
    gl.subscribe(_Shim("healthy", bus, callbacks=[
        Callback(why="still fires", trigger=lambda now, ctx: True, to="ok/personal")]))

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


def test_it_is_a_device():
    gl = GroundLoopDevice()
    assert isinstance(gl, CoreValuesMixin), "a device must compose the core values (Law 2)"
    assert [v.id for v in gl.CORE_VALUES] == ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]
    assert list(gl.introspect()) == ["intention", "state", "settings", "other"], "Form v0 #2 order"


def _main() -> int:
    for check in (test_a_beat_pulses_every_shim_in_order,
                  test_the_firing_is_the_shims_not_the_heartbeats,
                  test_subscribe_is_idempotent_and_typed,
                  test_one_shim_raising_cannot_stop_the_beat,
                  test_the_executor_goof_is_gone,
                  test_the_roster_is_the_nav_published_at_all_times,
                  test_it_is_a_device):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — ground_loop: the heartbeat beats and pulses subscribed shims (in order, "
          "survivably); the firing is the shim's, and the executor goof is gone")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
