"""Proof (ticket bcd271c63764) — a scratch HOME leaves no ground_loop behind when its run ends.

MEASURED 2026-11-14 on akienyoga9i: 27 ground_loop pairs were alive under scratch HOMEs whose
proofs had exited hours before (testing-ae0d88a55edb-*, testing-42ddfe3b7256-*, testing-4356-*),
each holding its HOME's ``.cairn/devices/cairn/0/machines/ground_loop/run.lock`` (Windows Restart
Manager, read-only), so every one of those HOMEs outlived its run — the falsifier this tool's
charter names. The proofs had run as plain ``python <proof>``, outside the tester's run_owned job
(ticket 715d2205a2ec), and a plain run is the standing rule, so the door that made the HOME is
the one that must end what ran under it. On Windows the sweep also met those HOMEs as
``[WinError 32]`` and skipped them; it now ends the holder and says so on stderr.

The cast's three clauses, each in real processes, because "the run ended" exists nowhere else:
  (1) a PLAIN-python stand-in proof that makes a scratch HOME and brings up a REAL ground_loop
      under it leaves no live holder of that HOME's run.lock once it exits, and the HOME is gone;
  (2) the same stand-in run as a TESTER run (``bin/cairn test <file>``, the tester's published
      entry — RULE 1) leaves none either;
  (3) the house loop is alive and holds its run.lock after both: a real ground_loop under a HOME
      that is not a scratch dir survives both runs, a run.lock under a DIFFERENT scratch dir
      survives, and the live ``~/.cairn`` loop, where this run can see it, holds its lock after
      if it held it before. The reap is bounded to the HOME being removed, never "every loop".

All run with TMPDIR/TEMP/TMP at a scratch world of this proof's own, so the host's temp root is
never the population read. Tooth (1) reds against a scratch.py that only rmtrees: the loop lives on.

    python cairn/tools/scratch/proofs/test_a_scratch_home_leaves_no_ground_loop_behind.py
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402
from cairn.tools.base.singleton import held  # noqa: E402
from cairn.tools.scratch.scratch import git_env, home_env, scratch_dir  # noqa: E402
from cairn.tools.windowless_spawn.windowless_spawn import background_pythonw, detached_kwargs  # noqa: E402

PROOF_TIMEOUT_S = 600

PROVES = {
    "bcd271c63764": {
        "1": "test_a_plain_run_leaves_no_live_holder_of_its_scratch_homes_run_lock",
        "2": "test_a_tester_run_leaves_no_live_holder_of_its_scratch_homes_run_lock",
        "3": "test_the_house_loop_holds_its_run_lock_after_both_runs",
        "3b": "test_a_run_lock_under_another_scratch_dir_survives",
        "3c": "test_the_kill_set_refuses_a_dir_that_is_not_a_scratch_dir",
    },
}

_GL_LOCK = Path(".cairn", "devices", "cairn", "0", "machines", "ground_loop", "run.lock")
_GL_ARGS = ["-m", "cairn.devices.cairn.machines.ground_loop"]
_WAIT_S = 60.0
_CAIRN_ARGV = bash_script_argv(str(REPO / "bin" / "cairn"))


def _world_env(world: Path) -> dict:
    env = git_env()
    for k in ("TMPDIR", "TEMP", "TMP"):
        env[k] = str(world)
    return env


def _end(pid: int) -> None:
    """Fixture cleanup for a red run, so a red leaves nothing behind either."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except OSError:
            pass


def _spawn_loop(home: Path) -> subprocess.Popen:
    return subprocess.Popen([background_pythonw(), *_GL_ARGS], cwd=str(REPO), env=home_env(home),
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, **detached_kwargs())


def _is_held(lock: Path) -> bool:
    return lock.exists() and held(lock)


def _wait_held(lock: Path, want: bool, within: float) -> bool:
    deadline = time.time() + within
    while _is_held(lock) != want and time.time() < deadline:
        time.sleep(0.2)
    return _is_held(lock) == want


# The stand-in proof: a python process that makes a scratch HOME the way the leaking proofs did,
# brings up the real ground_loop under it through the windowless door, waits until the loop
# holds its lock, writes the HOME and the spawned pid to REPORT, and exits normally. The same
# source runs as ``python -c`` (a plain run) and as a proof file under ``bin/cairn test``.
_STAND_IN = """
import sys, time, subprocess
sys.path.insert(0, {repo!r})
from pathlib import Path
from cairn.tools.scratch.scratch import scratch_dir, home_env
from cairn.tools.windowless_spawn.windowless_spawn import background_pythonw, detached_kwargs
from cairn.tools.base.singleton import held
home = scratch_dir("testing-fixture-reap-")
p = subprocess.Popen([background_pythonw(), "-m", "cairn.devices.cairn.machines.ground_loop"],
                     cwd={repo!r}, env=home_env(home), stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **detached_kwargs())
lock = home / {lock!r}
deadline = time.time() + {wait}
ok = True
while not held(lock):
    if time.time() > deadline:
        ok = False
        break
    time.sleep(0.2)
Path({report!r}).write_text(("" if ok else "NOLOCK ") + str(home) + " " + str(p.pid))
print(("PASS" if ok else "FAIL") + " stand_in_brings_up_a_ground_loop", flush=True)
sys.exit(0 if ok else 3)
"""


def _stand_in(report: Path) -> str:
    return _STAND_IN.format(repo=str(REPO), lock=str(_GL_LOCK), wait=_WAIT_S, report=str(report))


def _run_plain(world: Path, report: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", _stand_in(report)], capture_output=True, text=True,
                          env=_world_env(world), timeout=_WAIT_S + 60)


def _run_tester(world: Path, report: Path) -> subprocess.CompletedProcess:
    proof = world / f"test_reap_stand_in_{report.name.replace('-', '_')}.py"
    proof.write_bytes(_stand_in(report).encode())
    return subprocess.run([*_CAIRN_ARGV, "test", str(proof), "--timeout", str(int(_WAIT_S + 60))],
                          capture_output=True, text=True, cwd=str(REPO), env=_world_env(world),
                          timeout=_WAIT_S + 240)


def _left_nothing(kind: str, run: subprocess.CompletedProcess, report: Path) -> None:
    """The run has exited: the HOME it made is gone and nothing live holds its run.lock."""
    tail = f"rc {run.returncode}; stdout: {run.stdout[-600:]}; stderr: {run.stderr[-600:]}"
    assert report.exists(), f"the {kind} stand-in reported no HOME ({tail})"
    out = report.read_text().split()
    if out[0] == "NOLOCK":
        _end(int(out[2]))
        raise AssertionError(f"the ground_loop never held its lock in {_WAIT_S}s — the {kind} "
                             f"fixture measures nothing ({tail})")
    home, pid = Path(out[0]), int(out[1])
    lock = home / _GL_LOCK
    try:
        assert _wait_held(lock, False, 10), (
            f"the {kind} run exited and a live process still holds {lock} ({tail})")
        assert not home.exists(), f"the scratch HOME outlived its {kind} run: {home} ({tail})"
    finally:
        _end(pid)


def test_a_plain_run_leaves_no_live_holder_of_its_scratch_homes_run_lock():
    world = scratch_dir("scratch-reap-world-")
    report = world / "report"
    _left_nothing("plain", _run_plain(world, report), report)


def test_a_tester_run_leaves_no_live_holder_of_its_scratch_homes_run_lock():
    world = scratch_dir("scratch-reap-tester-world-")
    report = world / "report"
    _left_nothing("tester", _run_tester(world, report), report)


def test_the_house_loop_holds_its_run_lock_after_both_runs():
    # A real ground_loop under a HOME that is NOT a scratch dir (no scratch mark, so no door
    # removes it): the shape of the house loop, measurable on every box and under every seal.
    world = scratch_dir("scratch-reap-house-world-")
    house = world / "house-home"
    house.mkdir()
    house_lock = house / _GL_LOCK
    # The live house loop, where this run can see it (a sealed run swaps ~/.cairn out of reach).
    live_lock = Path.home() / _GL_LOCK
    live_before = _is_held(live_lock)
    loop = _spawn_loop(house)
    try:
        assert _wait_held(house_lock, True, _WAIT_S), "the house stand-in loop never held its lock"
        for kind, run in (("plain", _run_plain), ("tester", _run_tester)):
            report = world / f"report-{kind}"
            _left_nothing(kind, run(world, report), report)
            assert _is_held(house_lock), (
                f"a {kind} run's reap ended the house loop: {house_lock} is no longer held")
        if live_before:
            assert held(live_lock), f"the live house loop lost {live_lock} across the two runs"
    finally:
        _end(loop.pid)


_HOLDER = """
import sys, time
sys.path.insert(0, {repo!r})
from pathlib import Path
from cairn.tools.base.singleton import claim
c = claim(Path({lock!r}))
print("held", flush=True)
time.sleep(600)
"""


def test_a_run_lock_under_another_scratch_dir_survives():
    world = scratch_dir("scratch-reap-guard-world-")
    other = scratch_dir("scratch-reap-guard-other-")
    lock = other / _GL_LOCK
    lock.parent.mkdir(parents=True)
    holder = subprocess.Popen([sys.executable, "-c", _HOLDER.format(repo=str(REPO), lock=str(lock))],
                              stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held", "the guard's holder never claimed its lock"
        src = ("import sys; sys.path.insert(0, %r)\n"
               "from cairn.tools.scratch.scratch import scratch_dir\n"
               "scratch_dir('testing-fixture-reap-guard-')\n") % str(REPO)
        r = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True,
                           env=_world_env(world), timeout=120)
        assert r.returncode == 0, f"the guard's runner failed: {r.stderr}"
        assert holder.poll() is None and held(lock), "a run.lock outside the exiting run's HOME was reaped"
    finally:
        holder.kill()
        holder.wait(timeout=30)


def test_the_kill_set_refuses_a_dir_that_is_not_a_scratch_dir():
    # A live python holder under an UNMARKED directory: the kill set is asked directly, and must
    # refuse it — the bound is in the door, not only in which callers happen to reach it.
    from cairn.tools.scratch import scratch as _scratch
    world = scratch_dir("scratch-reap-refuse-world-")
    plain = world / "not-a-scratch-dir"
    lock = plain / _GL_LOCK
    lock.parent.mkdir(parents=True)
    holder = subprocess.Popen([sys.executable, "-c", _HOLDER.format(repo=str(REPO), lock=str(lock))],
                              stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held", "the refusal's holder never claimed its lock"
        ended = _scratch._end_what_holds(plain)
        assert ended == [], f"the kill set ended holders under an unmarked dir: {ended}"
        assert holder.poll() is None and held(lock), "a holder under an unmarked dir was ended"
    finally:
        holder.kill()
        holder.wait(timeout=30)


if __name__ == "__main__":
    failed = 0
    for name in [n for p in PROVES.values() for n in p.values()]:
        try:
            globals()[name]()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(e).__name__}: {e}")
    sys.exit(1 if failed else 0)
