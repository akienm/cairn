"""Proof for ticket b7068b1ba431 — a verdict re-runs a red alone and records a contention red beside it.

Measured 2026-11-16 (Q#119): e56a68e651c2 runs a verdict's instruments three at a time, and the
repo, /tmp, the network and git are shared by all three, so a red can be a neighbour's.

1. with an injected runner whose first run of one command disagrees and whose second agrees, that
   reading carries run and run_alone, and the alone run starts only after every pooled run has
   ended, with nothing else in flight;
2. a red that agrees alone is marked contention true and the verdict's checks do not refuse on it;
   a red that disagrees alone too is marked contention false and refuses as before;
3. a reading that agreed on its first run is not re-run: zero extra runs;
4. each re-run reading names the neighbours whose started/ended interval overlapped its first run;
5. the probe, over scratch verdict berths before and after an era floor, counts only post-era
   re-runs and returns the pairs, the contention count and re-run seconds against all run seconds.

No fork: the runner is injected and every instrument is a `true <n>` the extractor admits. The
probe reads a scratch packets dir under tmp_path. Nothing else is written.

    bin/cairn test cairn/devices/codemother/machines/verdict/proofs/test_a_red_is_re_run_alone.py
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"b7068b1ba431": {
    "1": "test_a_red_is_re_run_alone_after_the_pool_drains",
    "2": "test_contention_does_not_refuse_and_a_steady_red_does",
    "3": "test_an_agreeing_reading_is_not_re_run",
    "4": "test_a_re_run_names_its_neighbours",
    "5": "test_the_probe_counts_only_post_era_re_runs",
}}

PLENTY = 64 * 1024 ** 3
PROBE_FILE = REPO / "cairn/devices/codemother/machines/verdict/probes/a_red_re_run_alone_catches_contention.py"


def _v():
    from cairn.devices.codemother.machines.verdict import verdict
    return verdict


def _artifact(n: int) -> dict:
    return {"verdicts": [{"claim": "claim %d" % i, "instrument": "`true %d`" % i, "outcome": "pass"}
                         for i in range(n)]}


class _Runner:
    """Sleeps, counts what is in flight, and answers exit 1 for a red command's first
    `red_times` calls, 0 otherwise."""

    def __init__(self, red=(), red_times=1, sleep=0.1):
        self.lock = threading.Lock()
        self.in_flight = 0
        self.calls = []          # (command, in_flight at start, started)
        self.red, self.red_times, self.sleep = set(red), red_times, sleep
        self.seen = {}

    def __call__(self, command, **kw):
        with self.lock:
            self.in_flight += 1
            self.calls.append((command, self.in_flight, time.time()))
            k = self.seen[command] = self.seen.get(command, 0) + 1
        time.sleep(self.sleep)
        with self.lock:
            self.in_flight -= 1
        code = 1 if command in self.red and k <= self.red_times else 0
        return {"command": command, "exit": code, "timed_out": False, "seconds": self.sleep}


def _observe(artifact, runner):
    return _v().observe_instruments(artifact, str(REPO), runner=runner, mem_available=lambda: PLENTY)


def test_a_red_is_re_run_alone_after_the_pool_drains():
    runner = _Runner(red={"true 2"})
    obs = _observe(_artifact(6), runner)
    o = obs[2]
    assert o["run"]["exit"] == 1 and o["run_alone"]["exit"] == 0, o
    last_pooled_end = max(r["run"]["ended"] for r in obs)
    assert o["run_alone"]["started"] >= last_pooled_end, (o["run_alone"], last_pooled_end)
    alone = [c for c in runner.calls if c[0] == "true 2"][1]
    assert alone[1] == 1, runner.calls


def test_contention_does_not_refuse_and_a_steady_red_does():
    v = _v()
    obs = _observe(_artifact(4), _Runner(red={"true 1"}, red_times=1))
    assert obs[1]["contention"] is True
    assert v.lacks_of(v._observed_entries(obs)) == [], v._observed_entries(obs)

    obs = _observe(_artifact(4), _Runner(red={"true 1"}, red_times=2))
    assert obs[1]["contention"] is False
    lacks = v.lacks_of(v._observed_entries(obs))
    assert lacks and "claim 1" in lacks[0], lacks


def test_an_agreeing_reading_is_not_re_run():
    # one red beside four agreeing readings: exactly one extra run, and it is the red's
    runner = _Runner(red={"true 3"})
    obs = _observe(_artifact(5), runner)
    assert len(runner.calls) == 6, runner.calls
    assert runner.calls[-1][0] == "true 3", runner.calls
    assert [("run_alone" in o) for o in obs] == [False, False, False, True, False], obs
    assert not any("contention" in o for i, o in enumerate(obs) if i != 3), obs


def test_a_re_run_names_its_neighbours():
    obs = _observe(_artifact(5), _Runner(red={"true 0"}, sleep=0.2))
    me = obs[0]["run"]
    want = sorted(o["claim"] for o in obs[1:]
                  if o["run"]["started"] < me["ended"] and me["started"] < o["run"]["ended"])
    assert want, "width 3 put no run beside the first one"
    got = obs[0]["neighbours"]
    assert sorted(n["claim"] for n in got) == want, got
    assert all(isinstance(n["started"], float) and isinstance(n["ended"], float) for n in got), got


def _load_probe():
    spec = importlib.util.spec_from_file_location("a_red_re_run_alone_catches_contention", PROBE_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _reading(claim, first_s, alone=None):
    r = {"claim": claim, "instrument": "`true`", "expect_exit": 0,
         "run": {"command": "true", "exit": 0 if alone is None else 1, "seconds": first_s,
                 "started": 1.0, "ended": 1.0 + first_s}}
    if alone is not None:
        exit_alone, alone_s = alone
        r["run_alone"] = {"command": "true", "exit": exit_alone, "seconds": alone_s,
                          "started": 9.0, "ended": 9.0 + alone_s}
        r["contention"] = exit_alone == 0
        r["neighbours"] = []
    return r


def test_the_probe_counts_only_post_era_re_runs(tmp_path):
    probe = _load_probe()
    assert probe.PROBE.carry is not None and probe.PROBE.enough is not None
    pre = tmp_path / "verdict-20261101T090000-aaaaaaaaaaaa.json"
    post = tmp_path / "verdict-20261120T090000-bbbbbbbbbbbb.json"
    pre.write_text(json.dumps({"observed_runs": [_reading("old", 5.0, (0, 5.0))]}))
    post.write_text(json.dumps({"observed_runs": [
        _reading("a", 10.0, (0, 4.0)), _reading("b", 10.0, (1, 6.0)), _reading("c", 70.0)]}))
    era = datetime.datetime(2026, 11, 18, 12, 0, 0)
    s = probe.survey(str(tmp_path), era)
    assert s["re_runs"] == 2 and s["contention"] == 1, s
    assert sorted(p["claim"] for p in s["pairs"]) == ["a", "b"], s["pairs"]
    assert all(p["berth"] == str(post) for p in s["pairs"]), s["pairs"]
    assert s["re_run_seconds"] == 10.0 and s["all_run_seconds"] == 100.0, s
    assert abs(s["re_run_fraction"] - 0.1) < 1e-9, s
    none = probe.survey(str(tmp_path), None)
    assert none["re_runs"] == 0, "before PROVED there is no era and nothing is counted"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))
