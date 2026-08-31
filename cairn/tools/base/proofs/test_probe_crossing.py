"""A POKE PER CROSSING, NOT PER PULSE — the flood the shim would otherwise produce.

Akien, 2026-07-25: "so we need an anti-bounce?" — asked after a durable-bus proof went red
on residue. Measured: yes, but for a different reason than the one that prompted it. The
shim evaluated every probe on every pulse and poked on the LEVEL, so a condition that
stays true — a CPU parked at 91% — poked forever. ``rackmount.py:129`` filed exactly this
("wants edge-detection") and left it.

Named ``crossing``, not ``edge``: this codebase already spends "filed edge" on an open design
question, and overloading it would cost a re-derivation on every read. ``crossing`` is
already native here (``diagnostic.py``'s "a boundary crossing", rackmount's ``{"crossed": …}``).

WHAT THIS PROVES:
  - A STANDING TRUE POKES ONCE. Five pulses with the trigger true = one poke, not five.
  - IT RE-ARMS. False, then true again, is a NEW crossing and pokes again.
  - ``while_true`` OPTS BACK IN, for the probe that means "keep telling me while this holds."
  - THE MEMORY IS THE SHIM'S. Two shims watching the same declaration do not share suppression;
    the Probe stays frozen and stateless.
  - A REBUILT PROBE LIST IS STILL THE SAME WATCH — identity is the declaration's content, not
    the object, because ``probes()`` may rebuild every pulse.
  - A RAISING TRIGGER DOES NOT SWALLOW THE NEXT POKE. An error tells us nothing about the line,
    so it is remembered as neither side of it (Law 7 — a swallowed error must not also swallow
    the next real message).
  - WHAT IS HELD SAYS WHY. "still true — already poked" and "trigger false" are different facts
    and the pulse-record distinguishes them (a silent hold is the thing we are removing).

    python3 cairn/tools/base/proofs/test_probe_crossing.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.base.probe import Probe
from cairn.tools.base.shim import BaseShim


class _Shim(BaseShim):
    """A shim whose probes read a mutable dial, so a proof can move the line under it."""

    def __init__(self, probes, device_id="watcher"):
        super().__init__(bus=None)          # unwired: _fire records what it WOULD have posted
        self._cbs = probes
        self._id = device_id

    @property
    def device_id(self) -> str:
        return self._id

    def probes(self):
        return list(self._cbs)              # a FRESH list every pulse, as a real shim may build


def _cb(dial, *, why="cpu over 90", **kw):
    return Probe(why=why, trigger=lambda now, ctx: dial["over"], to="test_recipient", **kw)


def _pokes(record):
    return [f for f in record["fired"] if f.get("outcome") in ("ok", "unwired")]


def test_a_standing_true_pokes_once_not_every_pulse():
    dial = {"over": True}
    shim = _Shim([_cb(dial)])
    records = [shim.on_pulse(now=f"t{i}") for i in range(5)]
    poked = [i for i, r in enumerate(records) if _pokes(r)]
    assert poked == [0], f"one crossing, one poke — poked on pulses {poked}"


def test_it_re_arms_when_the_line_is_recrossed():
    dial = {"over": True}
    shim = _Shim([_cb(dial)])
    assert _pokes(shim.on_pulse(now="t0")), "the crossing pokes"
    assert not _pokes(shim.on_pulse(now="t1")), "still true — silent"
    dial["over"] = False
    assert not _pokes(shim.on_pulse(now="t2")), "gone false — nothing to say"
    dial["over"] = True
    assert _pokes(shim.on_pulse(now="t3")), "crossed AGAIN — a new crossing, a new poke"


def test_while_true_opts_back_into_every_pulse():
    dial = {"over": True}
    shim = _Shim([_cb(dial, while_true=True)])
    records = [shim.on_pulse(now=f"t{i}") for i in range(4)]
    assert all(_pokes(r) for r in records), \
        "'keep telling me while this holds' is a legitimate declaration and must still work"


def test_a_held_poke_says_which_kind_of_held_it_is():
    dial = {"over": True}
    shim = _Shim([_cb(dial)])
    shim.on_pulse(now="t0")
    still = shim.on_pulse(now="t1")["held"]
    assert "already poked" in still[0]["reason"], still
    dial["over"] = False
    assert shim.on_pulse(now="t2")["held"][0]["reason"] == "trigger false", \
        "suppressed-because-standing and never-fired are different facts, said out loud"


def test_the_memory_is_the_shims_and_the_probe_stays_frozen():
    dial = {"over": True}
    cb = _cb(dial)
    a, b = _Shim([cb], device_id="a"), _Shim([cb], device_id="b")
    assert _pokes(a.on_pulse(now="t0")) and _pokes(b.on_pulse(now="t0")), \
        "two shims watching the same declaration do not share suppression"
    assert not hasattr(cb, "_was_true"), "the Probe holds no fire-history — it is frozen"


def test_a_rebuilt_probe_is_recognised_as_the_same_watch():
    """probes() may rebuild every pulse, so identity is the declaration, not the object."""
    dial = {"over": True}
    shim = _Shim([_cb(dial)])
    assert _pokes(shim.on_pulse(now="t0"))
    shim._cbs = [_cb(dial)]              # a brand-new object, the same standing watch
    assert not _pokes(shim.on_pulse(now="t1")), \
        "a fresh object with the same to/channel/why must not re-poke a line already crossed"


def test_a_different_why_is_a_different_watch():
    dial = {"over": True}
    shim = _Shim([_cb(dial), _cb(dial, why="cpu over 95")])
    assert len(_pokes(shim.on_pulse(now="t0"))) == 2, "two declarations, two crossings"
    assert not _pokes(shim.on_pulse(now="t1")), "and both then go quiet"


def test_a_raising_trigger_does_not_swallow_the_next_poke():
    state = {"boom": True, "over": True}

    def trigger(now, ctx):
        if state["boom"]:
            raise RuntimeError("the reading was unavailable")
        return state["over"]

    shim = _Shim([Probe(why="cpu over 90", trigger=trigger, to="test_recipient")])
    first = shim.on_pulse(now="t0")
    assert first["fired"][0]["outcome"] == "refused", "the kick-back is loud and permanent"
    state["boom"] = False
    assert _pokes(shim.on_pulse(now="t1")), \
        "an error says NOTHING about the line — the next true reading is a fresh crossing"


def test_a_vanished_probe_is_forgotten_and_pokes_when_it_returns():
    dial = {"over": True}
    cb = _cb(dial)
    shim = _Shim([cb])
    assert _pokes(shim.on_pulse(now="t0"))
    shim._cbs = []                       # the watch is torn down (a temporary instrument)
    shim.on_pulse(now="t1")
    shim._cbs = [cb]                     # and put back up later
    assert _pokes(shim.on_pulse(now="t2")), \
        "a stale memory must not suppress a re-established watch's first poke"


TESTS = [
    test_a_standing_true_pokes_once_not_every_pulse,
    test_it_re_arms_when_the_line_is_recrossed,
    test_while_true_opts_back_into_every_pulse,
    test_a_held_poke_says_which_kind_of_held_it_is,
    test_the_memory_is_the_shims_and_the_probe_stays_frozen,
    test_a_rebuilt_probe_is_recognised_as_the_same_watch,
    test_a_different_why_is_a_different_watch,
    test_a_raising_trigger_does_not_swallow_the_next_poke,
    test_a_vanished_probe_is_forgotten_and_pokes_when_it_returns,
]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
