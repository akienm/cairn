"""Proof for ticket e56a68e651c2 — the verdict runs its instruments a few at a time.

Measured 2026-11-16: 149b9a1ab9c4's verdict ran its 74 instruments one after another in
observe_instruments, 1470 s of runs, and 62a8ecb673a7's verdict waited 562 s behind it.

1. with an injected runner sleeping 0.4 s per run, 9 runnable instruments return from
   observe_instruments in under 2 s (serial is 3.6 s);
2. the readings come back in the artifact's verdicts order, each carrying the run of its own command;
3. never more than VERDICT_WIDTH runs are in flight at once, counted by the injected runner;
4. an artifact with one unrunnable instrument still returns every reading with runnable False or
   True and zero runs made;
5. with an injected meminfo reader below 2 x SEAL_SWAP_BYTES + 1 GB, no further run starts while
   one is in flight, and runs resume when the reader rises; the first run always starts;
6. every observed run carries started and ended epochs, ended >= started, and with width 3 at
   least two runs' intervals overlap.

No fork: the runner and the memory reader are injected, and every instrument is a `true <n>`
the extractor admits (``true`` resolves on PATH). Nothing is written anywhere.

    bin/cairn test cairn/devices/codemother/machines/verdict/proofs/test_the_verdict_runs_its_instruments_a_few_at_a_time.py
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"e56a68e651c2": {
    "1": "test_nine_runs_finish_in_a_fraction_of_serial",
    "2": "test_readings_keep_planned_order_and_their_own_run",
    "3": "test_never_more_than_the_width_in_flight",
    "4": "test_an_unrunnable_instrument_makes_zero_runs",
    "5": "test_low_memory_admits_one_at_a_time_and_resumes",
    "6": "test_every_run_carries_its_epochs_and_runs_overlap",
}}

PLENTY = 64 * 1024 ** 3


def _v():
    from cairn.devices.codemother.machines.verdict import verdict
    return verdict


def _artifact(n: int, unrunnable_at: int | None = None) -> dict:
    vs = []
    for i in range(n):
        inst = "`no_such_command_e56a %d`" % i if i == unrunnable_at else "`true %d`" % i
        vs.append({"claim": "claim %d" % i, "instrument": inst, "outcome": "pass"})
    return {"verdicts": vs}


class _Counter:
    """A runner that sleeps, counts what is in flight, and remembers each start's company."""

    def __init__(self, sleep=0.4, sleep_of=None, on_start=None):
        self.lock = threading.Lock()
        self.in_flight = self.peak = self.calls = self.ended = 0
        self.starts = []
        self.sleep, self.sleep_of, self.on_start = sleep, sleep_of, on_start

    def __call__(self, command, **kw):
        with self.lock:
            self.in_flight += 1
            self.calls += 1
            self.peak = max(self.peak, self.in_flight)
            self.starts.append((self.in_flight, self.on_start() if self.on_start else None))
        time.sleep(self.sleep_of(command) if self.sleep_of else self.sleep)
        with self.lock:
            self.in_flight -= 1
            self.ended += 1
        return {"command": command, "exit": 0, "timed_out": False, "seconds": self.sleep}


def _observe(artifact, runner, mem=lambda: PLENTY):
    return _v().observe_instruments(artifact, str(REPO), runner=runner, mem_available=mem)


def test_nine_runs_finish_in_a_fraction_of_serial():
    runner = _Counter(sleep=0.4)
    t0 = time.monotonic()
    obs = _observe(_artifact(9), runner)
    took = time.monotonic() - t0
    assert runner.calls == 9 and len(obs) == 9
    assert took < 2.0, "9 runs of 0.4 s took %.2f s; serial is 3.6 s" % took


def test_readings_keep_planned_order_and_their_own_run():
    # later commands finish first, so completion order is the reverse of planned order
    runner = _Counter(sleep_of=lambda c: 0.05 * (9 - int(c.split()[1])))
    obs = _observe(_artifact(9), runner)
    assert [o["claim"] for o in obs] == ["claim %d" % i for i in range(9)]
    for i, o in enumerate(obs):
        assert o["run"]["command"] == "true %d" % i, o


def test_never_more_than_the_width_in_flight():
    v = _v()
    assert v.VERDICT_WIDTH == 3
    runner = _Counter(sleep=0.1)
    _observe(_artifact(12), runner)
    assert runner.calls == 12
    assert 1 < runner.peak <= v.VERDICT_WIDTH, runner.peak


def test_an_unrunnable_instrument_makes_zero_runs():
    runner = _Counter(sleep=0.0)
    obs = _observe(_artifact(5, unrunnable_at=3), runner)
    assert runner.calls == 0
    assert len(obs) == 5
    assert [o["runnable"] for o in obs] == [True, True, True, False, True]


def test_low_memory_admits_one_at_a_time_and_resumes():
    v = _v()
    floor = 2 * v.SEAL_SWAP_BYTES + 1024 ** 3
    box = {}
    low = lambda: box["r"].ended < 3                    # noqa: E731
    runner = _Counter(sleep=0.15, on_start=low)
    box["r"] = runner
    obs = _observe(_artifact(9), runner, mem=lambda: floor - 1 if low() else floor)
    assert runner.calls == 9 and len(obs) == 9
    low_starts = [n for n, was_low in runner.starts if was_low]
    high_starts = [n for n, was_low in runner.starts if not was_low]
    assert low_starts and all(n == 1 for n in low_starts), runner.starts
    assert any(n > 1 for n in high_starts), runner.starts


def test_every_run_carries_its_epochs_and_runs_overlap():
    obs = _observe(_artifact(6), _Counter(sleep=0.2))
    spans = []
    for o in obs:
        run = o["run"]
        assert isinstance(run.get("started"), float) and isinstance(run.get("ended"), float), run
        assert run["ended"] >= run["started"]
        spans.append((run["started"], run["ended"]))
    assert any(a[0] < b[1] and b[0] < a[1] for i, a in enumerate(spans) for b in spans[i + 1:]), spans


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
