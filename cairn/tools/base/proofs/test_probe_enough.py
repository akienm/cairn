"""A PROBE CAN SAY WHEN IT HAS GATHERED ENOUGH — and CLEARED never reads as RE-ARMED.

Ticket ``watchme-emits-a-probe`` (2026-07-30). A ``WATCHME`` node emits a probe to gather
efficacy data for its own intention; a gatherer with no stopping condition is a watcher that
runs forever, which is the standing cost the shrinking-footprint discipline refuses. The
survey measured this as the ONE of the five spec'd fields (trigger, enough-condition,
carrier, nexus, consumer) with no home in the primitive — the other four already had one.

``enough`` gets the SAME treatment as ``trigger`` and ``carry``, deliberately: an open
predicate, never an enum of condition kinds. The module header warns against exactly that
reification (the shipped ``interval/date/quantity/state`` set was the last one), and a
count-of-firings field would have been the same mistake wearing a new name.

THE DISTINCTION THIS PROOF EXISTS FOR: a probe stops firing for two OPPOSITE reasons.
  - RE-ARMED — the trigger went false. The watch STANDS; the next crossing pokes.
  - CLEARED  — enough was gathered. The watch is OVER; no later crossing pokes.
A mechanism that cannot tell them apart ships a watcher that looks alive and is dead (or
one believed dead that is still costing pulses). So they live in different memories on the
shim, report different reasons in the pulse record, and answer from different surfaces.

WHAT THIS PROVES:
  - NO ``enough`` IS A STANDING WATCH. The default is unchanged: no probe acquires a
    stopping condition it never declared.
  - AN ``enough`` THAT SAYS TRUE RETIRES THE WATCH — and a later re-crossing does NOT poke.
  - AN ``enough`` THAT SAYS FALSE CHANGES NOTHING. Re-crossing still pokes.
  - IT IS ASKED ONLY AFTER A FIRE. A probe that never poked has gathered nothing, so its
    stopping condition is never consulted.
  - CLEARED AND RE-ARMED ARE DISTINGUISHABLE — by the held reason and by ``shim.cleared()``.
  - A RAISING ``enough`` LEAVES THE WATCH STANDING, loudly (Law 7 — the failure that hides
    is a watcher that quietly stopped watching).
  - THE MEMORY IS THE SHIM'S. The Probe stays frozen; two shims watching the same
    declaration do not share a clearing.
  - A NON-CALLABLE ``enough`` IS REFUSED AT CONSTRUCTION (CP1, caught at n=1).

    python3 cairn/tools/base/proofs/test_probe_enough.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.base.probe import Probe
from cairn.tools.base.shim import BaseShim


class _Shim(BaseShim):
    """A shim whose probes read a mutable dial, so a proof can move the line under it."""

    def __init__(self, probes, device_id="gatherer"):
        super().__init__(bus=None)          # unwired: _fire records what it WOULD have posted
        self._cbs = probes

    @property
    def device_id(self) -> str:
        return "gatherer"

    def probes(self):
        return list(self._cbs)              # a FRESH list every pulse, as a real shim may build


def _cb(dial, *, why="gather efficacy for this intention", **kw):
    return Probe(why=why, trigger=lambda now, ctx: dial["over"], to="dave", **kw)


def _pokes(record):
    return [f for f in record["fired"] if f.get("outcome") in ("ok", "unwired")]


def _held_reason(record, why="gather efficacy for this intention"):
    for h in record["held"]:
        if h["why"] == why:
            return h["reason"]
    return None


def test_no_enough_is_a_standing_watch():
    dial = {"over": True}
    cb = _cb(dial)
    shim = _Shim([cb])
    assert cb.gathered_enough({}) is False, "no enough declared must never answer 'retire me'"
    for i in range(3):
        shim.on_pulse(now=f"t{i}")
        dial["over"] = not dial["over"]
    assert shim.cleared() == set(), \
        "a probe that declared no stopping condition must not acquire one"


def test_enough_true_retires_the_watch_and_a_later_crossing_does_not_poke():
    dial = {"over": True}
    cb = _cb(dial, enough=lambda ctx: True)
    shim = _Shim([cb])
    assert _pokes(shim.on_pulse(now="t0")), "the first crossing still pokes — enough is asked AFTER"
    dial["over"] = False
    shim.on_pulse(now="t1")
    dial["over"] = True                                   # a genuine re-crossing
    assert not _pokes(shim.on_pulse(now="t2")), \
        "CLEARED is terminal — a retired watch must not poke on a later crossing"
    assert cb.identity in shim.cleared()


def test_enough_false_changes_nothing():
    dial = {"over": True}
    cb = _cb(dial, enough=lambda ctx: False)
    shim = _Shim([cb])
    assert _pokes(shim.on_pulse(now="t0"))
    dial["over"] = False
    shim.on_pulse(now="t1")
    dial["over"] = True
    assert _pokes(shim.on_pulse(now="t2")), \
        "an enough that says 'not yet' must leave the watch exactly as it was"
    assert shim.cleared() == set()


def test_enough_is_asked_only_after_a_fire():
    asked = []
    dial = {"over": False}
    cb = _cb(dial, enough=lambda ctx: asked.append("asked") or True)
    shim = _Shim([cb])
    shim.on_pulse(now="t0")
    shim.on_pulse(now="t1")
    assert asked == [], "a probe that has not poked has gathered nothing — do not ask it"
    dial["over"] = True
    shim.on_pulse(now="t2")
    assert asked == ["asked"], "asked exactly once, at the fire that produced the yield"


def test_cleared_and_re_armed_are_distinguishable():
    """THE ROW THE WHOLE FIELD IS WORTHLESS WITHOUT. Both probes are silent on the last
    pulse; the mechanism must say WHICH silence each one is."""
    resting_dial = {"over": True}
    retired_dial = {"over": True}
    resting = _cb(resting_dial, why="resting watch")
    retired = _cb(retired_dial, why="retired watch", enough=lambda ctx: True)
    shim = _Shim([resting, retired])
    shim.on_pulse(now="t0")                               # both cross and poke
    resting_dial["over"] = False                          # one goes false — RE-ARMED
    record = shim.on_pulse(now="t1")

    assert _held_reason(record, "resting watch") == "trigger false"
    assert _held_reason(record, "retired watch") == "cleared — gathered enough, retired"
    assert _held_reason(record, "resting watch") != _held_reason(record, "retired watch"), \
        "two opposite states must never render as the same reason"
    assert shim.cleared() == {retired.identity}, \
        "the terminal memory holds the retired watch and NOT the resting one"

    resting_dial["over"] = True                           # the resting watch re-crosses...
    after = shim.on_pulse(now="t2")
    poked = {f["why"] for f in _pokes(after)}
    assert poked == {"resting watch"}, \
        f"re-armed pokes, cleared does not — poked {poked}"


def test_a_raising_enough_leaves_the_watch_standing_and_says_so():
    dial = {"over": True}

    def boom(ctx):
        raise RuntimeError("the accumulator is unreachable")

    cb = _cb(dial, enough=boom)
    shim = _Shim([cb])
    record = shim.on_pulse(now="t0")
    poke = _pokes(record)[0]
    assert poke["enough_failed"].startswith("RuntimeError:"), \
        "a broken stopping condition is recorded on the record of truth, never swallowed"
    assert shim.cleared() == set(), "a broken stop must leave the watch STANDING, not retire it"
    dial["over"] = False
    shim.on_pulse(now="t1")
    dial["over"] = True
    assert _pokes(shim.on_pulse(now="t2")), "and the standing watch still pokes on re-crossing"


def test_the_memory_is_the_shims_and_the_probe_stays_frozen():
    dial = {"over": True}
    cb = _cb(dial, enough=lambda ctx: True)
    mine, theirs = _Shim([cb]), _Shim([cb])
    mine.on_pulse(now="t0")
    assert mine.cleared() == {cb.identity}
    assert theirs.cleared() == set(), \
        "clearing is the FIRER's memory — a frozen declaration carries none of it"
    assert _pokes(theirs.on_pulse(now="t0")), "so another shim's watch is untouched"


def test_a_non_callable_enough_is_refused_at_construction():
    try:
        Probe(why="w", trigger=lambda now, ctx: True, to="dave", enough=5)
    except TypeError as exc:
        assert "callable" in str(exc), exc
    else:
        raise AssertionError("a count is not an enough-condition — an enum by another name")


TESTS = [
    test_no_enough_is_a_standing_watch,
    test_enough_true_retires_the_watch_and_a_later_crossing_does_not_poke,
    test_enough_false_changes_nothing,
    test_enough_is_asked_only_after_a_fire,
    test_cleared_and_re_armed_are_distinguishable,
    test_a_raising_enough_leaves_the_watch_standing_and_says_so,
    test_the_memory_is_the_shims_and_the_probe_stays_frozen,
    test_a_non_callable_enough_is_refused_at_construction,
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
