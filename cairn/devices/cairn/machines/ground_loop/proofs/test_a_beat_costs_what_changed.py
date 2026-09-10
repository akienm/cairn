"""A BEAT COSTS WHAT CHANGED — the timed proof, not a structural claim about it.

Ticket ``2f0a6ea8c966-a-beat-costs-what-changed``. Cast 2026-08-18 against a measured warm
beat of 8.7-9.3s; measured again 2026-09-07 at **104.8s** after the watch set grew. Four
fixes landed between: the chart-chain packet index (``42c9e15``), ``once()`` + ``_pulse()``
for a pulse context nothing had ever populated (``11d2ec0``), ``settled()`` for corpus scans
being re-derived on a clock (``e53a973``), and the ``context or {}`` at ``shim.py`` and
``loop.py`` that had every shim swapping out the beat's own dict (``af50ab8``). Steady state
after them: **23.7s**.

WHY THE TEETH ARE SHAPED LIKE THIS. The ticket's own ``proves_green`` names the hollow build
it is written against: *"a hollow build that cached everything forever passes the first and
fails the second."* So the first tooth is a TIMED beat and the second is a real file landing
in the real corpus between two reads — a memo that never expired would sail through the timer
and die here. The third closes the ticket's WRONG INTENT clause behaviourally rather than by
reading the source for a time-to-live: it compares the SET of probes evaluated on two
consecutive beats, because buying the number by looking less often is the failure the ticket
forbids by name. The fourth pins the bound to the runner's own constant, so the number can never be made
to pass by widening it — the ticket's ``owner`` field says that bound is not CC's to move.

WHAT THIS COSTS TO RUN: two real beats over the live corpus, about 55s. That is the price of
a timed tooth and it is the point — a fast structural proxy for "is the beat cheap" is the
thing this ticket exists because we had.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cairn.tools.base import settled as S
from cairn.tools.base.probe import Probe

PROVES = {
    "2f0a6ea8c966": {
        "1": "test_a_warm_beat_costs_less_than_the_ruled_cadence",
        "2": "test_a_file_touched_between_beats_is_seen_by_the_second",
        "3": "test_every_standing_probe_is_evaluated_on_every_beat",
        "4": "test_the_bound_is_the_runners_and_cannot_be_widened_here",
    },
}

# .../cairn/cairn/devices/cairn/machines/ground_loop/proofs/this_file.py — parents[5] is the
# PACKAGE root, which is the default root of both settled-backed scans below. Derived from
# __file__ rather than named, so a move of this proof cannot silently point it at a tree the
# beat does not read.
_PACKAGE = Path(__file__).resolve().parents[5]

# Self-describing on purpose: if a kill leaks it, the name tells the next reader what it is
# and that removing it is safe.
_FIXTURE = _PACKAGE / ".a-beat-costs-what-changed-PROOF-FIXTURE-safe-to-delete"

_MEASURED = None


def _two_beats() -> dict:
    """Two real beats in ONE process — cold, then warm — with every ``fires`` counted.

    One process is not an optimisation here, it is the measurement: ``settled``'s memo spans
    pulses by design, so a fresh-process beat is always beat #1 and shows none of the win.
    Every earlier measurement of this loop made exactly that mistake.
    """
    global _MEASURED
    if _MEASURED is not None:
        return _MEASURED

    from cairn.tools.bus_client import _wire

    seen = {"ids": set()}
    original = Probe.fires

    def counting(self, *a, **kw):
        seen["ids"].add(self.identity)
        return original(self, *a, **kw)

    def retired(loop) -> set:
        """Every probe the shims have retired — ``enough()`` said so and ``on_pulse``'s
        CLEARED-IS-TERMINAL branch will not evaluate it again."""
        out = set()
        for shim in loop._shims:
            out |= set(shim._cleared)
        return out

    Probe.fires = counting
    try:
        now = datetime.now(timezone.utc).astimezone()
        _bus, loop = _wire(devices=[], beat=False)

        seen["ids"] = set()
        t = time.monotonic()
        loop.beat(now + timedelta(seconds=60))
        cold_s, cold_ids = time.monotonic() - t, set(seen["ids"])
        cold_retired = retired(loop)

        seen["ids"] = set()
        t = time.monotonic()
        loop.beat(now + timedelta(seconds=120))
        warm_s, warm_ids = time.monotonic() - t, set(seen["ids"])
    finally:
        Probe.fires = original

    _MEASURED = {"cold_s": cold_s, "warm_s": warm_s,
                 "cold_ids": cold_ids, "warm_ids": warm_ids,
                 "cold_retired": cold_retired}
    return _MEASURED


def test_a_warm_beat_costs_less_than_the_ruled_cadence():
    """CLAUSE (1). The cadence is 60.0s — Akien 2026-08-22, recorded as ruling
    2026-09-08-the-60s-cadence-is-the-bound-a-beat-is-measured-against. The ticket's original
    clause said 1.0s and named a cadence superseded before this ticket was built."""
    from cairn.devices.cairn.machines.ground_loop.__main__ import CADENCE_S

    m = _two_beats()
    assert m["warm_s"] < CADENCE_S, (
        f"a warm beat cost {m['warm_s']:.1f}s against a {CADENCE_S}s cadence — the loop cannot "
        f"hold its period, and the beat is re-deriving what did not change (cold beat was "
        f"{m['cold_s']:.1f}s)")


def test_a_file_touched_between_beats_is_seen_by_the_second():
    """CLAUSE (2), and the tooth the ticket names as the hollow-build killer: a build that
    cached everything forever passes the timer and fails here.

    Fired at the two ``settled``-backed scans the beat actually calls, over the REAL package
    tree, with a real file landing in it between the two reads. A temp tree would prove
    ``settled``; only the live root proves the beat's own memo expires."""
    from cairn.tools.base.address_rule import scan
    from cairn.tools.orient.orient import device_census

    S.forget()
    device_census()
    scan()
    warm = S.DERIVATIONS
    device_census()
    scan()
    assert S.DERIVATIONS == warm, (
        f"the memo re-derived {S.DERIVATIONS - warm} time(s) over an unchanged tree — there is "
        "no memo, and the timing tooth above is measuring nothing")

    try:
        _FIXTURE.write_text("a real file landing in the real corpus between two reads\n")
        device_census()
        scan()
        after = S.DERIVATIONS
    finally:
        if _FIXTURE.exists():
            os.unlink(_FIXTURE)

    assert after == warm + 2, (
        f"a file landed in {_PACKAGE} and the beat's scans re-derived {after - warm} of 2 — "
        "the corpus moved and the memo did not notice, which is a beat reporting on a world "
        "that is gone. THIS IS THE HOLLOW BUILD the ticket names: cache everything forever "
        "and the timer goes green while the answers go stale")


def test_every_standing_probe_is_evaluated_on_every_beat():
    """CLAUSE (3) — the WRONG INTENT clause, closed behaviourally.

    The ticket forbids buying the number by looking less often: *"a time-to-live, an
    every-Nth-beat probe, a staggered schedule."* Reading the source for those three patterns
    would catch the spellings someone thought of; comparing the SETS of probes evaluated on
    two consecutive beats catches every spelling there is, including next year's.

    WHY SETS AND NOT A COUNT, and this is a measurement, not a preference. The first shape of
    this tooth counted ``Probe.fires`` calls and demanded the two beats match. It went red at
    79 cold / 73 warm. Measured 2026-09-08: the six that stopped are EXACTLY the six that
    retired on beat 1 — ``_cleared`` went 0 to 6, every dropped identity was in it, and none
    dropped for any other reason. Retirement is an ending a probe declares about ITSELF
    through ``enough()``, and ``on_pulse``'s CLEARED-IS-TERMINAL branch then stops evaluating
    it ("retired deliberately — an ending, not a silence"). A count cannot tell that apart
    from a throttle; the set difference can, and the ticket is about probes that are still
    STANDING being asked less often.

    BOTH DIRECTIONS ARE ASSERTED. Dropping without retiring is a time-to-live. APPEARING on
    the second beat having been skipped on the first is a staggered schedule, and a tooth
    that only watched the drop side would call that green."""
    m = _two_beats()
    assert m["cold_ids"], "no probe was evaluated at all — the loop discovered nothing"

    stopped = m["cold_ids"] - m["warm_ids"]
    throttled = stopped - m["cold_retired"]
    assert not throttled, (
        f"{len(throttled)} probe(s) were evaluated on the cold beat, not on the warm one, and "
        f"did not retire: {sorted(throttled)}. A standing watch asked less often than every "
        "beat buys the beat's cost by looking less often — that is the ticket's stated WRONG "
        "INTENT, not its fix")

    staggered = m["warm_ids"] - m["cold_ids"]
    assert not staggered, (
        f"{len(staggered)} probe(s) were skipped on the cold beat and evaluated on the warm "
        f"one: {sorted(staggered)}. That is a staggered schedule — the beat is cheap because "
        "each beat asks only some of the questions, which the ticket forbids by name")


def test_the_bound_is_the_runners_and_cannot_be_widened_here():
    """CLAUSE (4). The cadence is Akien's, not CC's — the ticket's ``owner`` field says so in
    as many words: *"Widening either to make the numbers below look better is the plaster the
    2026-08-14 rule forbids."* So the watch may not carry its own softer copy of it."""
    from cairn.devices.cairn.machines.ground_loop.__main__ import CADENCE_S as RUNNER
    from cairn.devices.cairn.machines.ground_loop.probes import does_a_beat_cost_what_changed as P

    assert P.CADENCE_S == RUNNER, (
        f"the watch reads a {P.CADENCE_S}s cadence and the runner sleeps {RUNNER}s — a watch "
        "holding its own copy of a ruled bound is how the bound gets widened without a ruling")
    assert 0 < P._HEADROOM < 1.0, (
        f"the headroom is {P._HEADROOM} — at 1.0 or above the watch permits a beat that spends "
        "the whole cadence, which is the margin this ticket exists to protect")


def test_a_dead_loop_is_not_read_as_a_beat_cost():
    """Not a falsifier clause — the defect the probe had for its first ten minutes of life,
    caught by running it (2026-09-08): the loop was down, ``age_s`` was 312,173s, and the naive
    subtraction reported a 3.6-DAY 'beat cost'. A stopped loop is the liveness watch's finding,
    and a watch that fires on another watch's defect is noise at a diagnostic surface."""
    from cairn.devices.cairn.machines.ground_loop.probes import does_a_beat_cost_what_changed as P

    dead = P.judge({"verdict": "DEAD", "age_s": 312173.7,
                    "record": {"pid": 1, "state": {"beats": 32}}})
    assert dead["measurable"] is False, dead
    assert dead["beat_cost_s"] is None, (
        f"a 3.6-day-old record yielded a beat cost of {dead['beat_cost_s']} — the subtraction "
        "ran on a number that is not an inter-beat interval")
    assert P._trigger(None, {"corpus": dead}) is False, (
        "the watch fired on a loop that is not beating — that is the liveness watch's finding")
    assert P._enough({"corpus": dead}) is False, (
        "a dead loop was counted as evidence the beat is cheap")


def test_the_watch_fires_when_the_beat_overruns_its_budget():
    """Not a falsifier clause — the watch's own non-hollow check. A watch that cannot go red
    is a green that means nothing (Law 9)."""
    from cairn.devices.cairn.machines.ground_loop.probes import does_a_beat_cost_what_changed as P

    fine = P.judge({"age_s": P.CADENCE_S + 5.0, "record": {"state": {"beats": 10}}})
    assert fine["measurable"] and fine["inside_budget"], fine
    assert P._trigger(None, {"corpus": fine}) is False, fine

    over = P.judge({"age_s": P.CADENCE_S + (P.CADENCE_S * P._HEADROOM) + 1.0,
                    "record": {"state": {"beats": 10}}})
    assert over["measurable"] and not over["inside_budget"], over
    assert P._trigger(None, {"corpus": over}) is True, (
        "a beat one second past its budget did not fire the watch")
    assert "re-derived" in P._carry({"corpus": over})["finding"], (
        "the red arrived without saying what it means — the carry is the whole point of a "
        "watch that pokes a lane it cannot fix")


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    if _MEASURED:
        print(f"\n  cold beat {_MEASURED['cold_s']:.1f}s · warm beat {_MEASURED['warm_s']:.1f}s "
              f"· {len(_MEASURED['cold_ids'])} probes evaluated cold, "
              f"{len(_MEASURED['warm_ids'])} warm "
              f"({len(_MEASURED['cold_retired'])} retired on the cold beat)")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
