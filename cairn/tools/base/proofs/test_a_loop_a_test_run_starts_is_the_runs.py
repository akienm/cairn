"""A ground loop a shim starts inside a test run is the run's (ticket 2120e74dcf44; sibling of
f04d5ef26a48, which marked the launcher's two systemd-run blocks, and of c64adc092835, which made
a tester run stop the units carrying its id). RE-AIMED 2026-11-18 by ticket dda0e72b9c67 (D6;
orchestrator ruling: the unit was the means, not the outcome) and measured BY PID, never by a
manager record.

ensure_ground_loop (cairn/tools/base/shim.py) is "cairn/devices/cc/superclaude's systemd-run block,
spelled once here for python". A systemd-run unit runs in the user MANAGER's mount namespace, so
inside the tester's seal (~/.cairn a swap) a loop started as a unit beats on the live tree. Since
dda0e72b9c67 the shim asks first whether it is beside the manager, and inside the seal spawns the
loop with setsid, which inherits the run's environment and so its CAIRN_TESTER_TEST_ID — the id
the tester's stop (runs.kill_what_it_started) collects by pid.

  1. A LOOP STARTED IN A RUN CARRIES ITS TEST ID: the loop process ensure_ground_loop starts
     inside this sealed run carries this run's CAIRN_TESTER_TEST_ID in its environment.
  2. A LOOP STARTED IN A RUN RUNS IN THE RUN'S MOUNT NAMESPACE: that loop process's mount
     namespace is this run's, so its ~/.cairn is the run's swap, never the live tree.
  3. A TESTER RUN THAT STARTS A LOOP LEAVES NO LOOP RUNNING: a proof run by the tester whose
     subject calls ensure_ground_loop sees, while it runs, a loop process carrying that run's id,
     and once the run ends no such process is running.
  4. OUTSIDE A RUN THE LOOP IS UNCHANGED: called beside the manager with no test id (a user unit,
     outside the seal), the loop is a unit that carries no id and keeps the manager's default
     CollectMode (inactive), so the live loop that fails stays where a human looks.

Teeth 1-3 call ensure_ground_loop under a scratch HOME (no loop holds the lock there, and the loop
writes under the scratch, never the live instance or the swap's live copy), with the proof's own
unit name cairn-proof-loopmark-<pid>-<n> (CAIRN_GROUND_LOOP_UNIT), so the live loop is neither
claimed nor stopped. Every loop pid is ended, and every unit stopped and reset-failed, at the end.

    bin/cairn test --seal cairn/tools/base/proofs/test_a_loop_a_test_run_starts_is_the_runs.py
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402

PROVES = {"2120e74dcf44": {
    "1": "test_a_loop_started_in_a_run_carries_its_test_id",
    "2": "test_a_loop_started_in_a_run_runs_in_the_runs_mount_namespace",
    "3": "test_a_tester_run_that_starts_a_loop_leaves_no_loop_running",
    "4": "test_outside_a_run_the_loop_is_unchanged",
},
    # 45c168cc1ff1 clause (2): the run tooth runs its fixture through bin/cairn test.
    "45c168cc1ff1": {"2": "test_a_tester_run_that_starts_a_loop_leaves_no_loop_running"}}

_ENV = "CAIRN_TESTER_TEST_ID"
_SEALED = "CAIRN_TESTER_INSTANCE_SEALED"   # isolation.INSTANCE_SEAL_MARKER, read by name
_LOOP_MODULE = "cairn.devices.cairn.machines.ground_loop"
_TAG = str(os.getpid())
_UNITS: list[str] = []
_PIDS: list[int] = []

_CALL = ("import json, sys; sys.path.insert(0, %r); "
         "from cairn.tools.base.shim import ensure_ground_loop; "
         "print(json.dumps(ensure_ground_loop()))")


def _unit(n: int) -> str:
    name = f"cairn-proof-loopmark-{_TAG}-{n}"
    _UNITS.append(name)
    return name


def _require_the_seal() -> None:
    assert os.environ.get(_SEALED) == "1" and os.environ.get(_ENV), \
        "this proof measures from inside the tester's seal: run it with bin/cairn test --seal"


def _loops(test_id: str) -> list[int]:
    """Every ground-loop process this run can see whose environment carries ``test_id``."""
    found = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            env = (p / "environ").read_bytes().split(b"\0")
        except OSError:
            continue
        if _LOOP_MODULE in cmd and f"{_ENV}={test_id}".encode() in env:
            found.append(int(p.name))
    return found


def _wait_for(test_id: str, want: bool, timeout: float = 10.0) -> list[int]:
    end = time.time() + timeout
    while True:
        pids = _loops(test_id)
        if bool(pids) == want or time.time() > end:
            return pids
        time.sleep(0.2)


_STARTED: dict = {}


def _start_in_run() -> tuple[dict, list[int]]:
    """ensure_ground_loop called inside this sealed run, under a scratch HOME, once."""
    if not _STARTED:
        from cairn.tools.scratch.scratch import home_env, scratch_dir
        home = scratch_dir("cairn-proof-loopmark-home-1-")
        env = home_env(home, CAIRN_GROUND_LOOP_UNIT=_unit(1), PYTHONPATH=str(ROOT))
        r = subprocess.run([sys.executable, "-c", _CALL % str(ROOT)], env=env,
                           capture_output=True, text=True, timeout=120, cwd=str(ROOT))
        assert r.returncode == 0, (r.stdout[-400:], r.stderr[-400:])
        _STARTED["said"] = json.loads(r.stdout.strip().splitlines()[-1])
        _STARTED["pids"] = _wait_for(os.environ[_ENV], True)
        _PIDS.extend(_STARTED["pids"])
    return _STARTED["said"], _STARTED["pids"]


def test_a_loop_started_in_a_run_carries_its_test_id():
    _require_the_seal()
    said, pids = _start_in_run()
    assert pids, (f"no ground-loop process carrying this run's {_ENV}={os.environ[_ENV]} is visible "
                  f"(the spawn said {said}): a unit on the user manager carries the manager's environment")


def test_a_loop_started_in_a_run_runs_in_the_runs_mount_namespace():
    _require_the_seal()
    said, pids = _start_in_run()
    assert pids, f"no loop of this run to measure (the spawn said {said})"
    mine = os.readlink("/proc/self/ns/mnt")
    for pid in pids:
        ns = os.readlink(f"/proc/{pid}/ns/mnt")
        assert ns == mine, f"loop pid {pid} runs in mount namespace {ns}, this run's is {mine} (spawn said {said})"


def test_a_tester_run_that_starts_a_loop_leaves_no_loop_running():
    _require_the_seal()
    from cairn.tools.scratch.scratch import scratch_dir
    unit = _unit(3)
    root = scratch_dir("cairn-proof-loopmark-run-") / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    proof, said = root / "proofs" / "test_fixture.py", root / "said.json"
    home = scratch_dir("cairn-proof-loopmark-home-3-")
    proof.write_text(
        "import json, os, subprocess, sys, time\n"
        f"env = dict(os.environ, HOME={str(home)!r}, CAIRN_GROUND_LOOP_UNIT={unit!r}, PYTHONPATH={str(ROOT)!r})\n"
        f"r = subprocess.run([sys.executable, '-c', {(_CALL % str(ROOT))!r}], env=env, capture_output=True, text=True)\n"
        "assert r.returncode == 0, r.stdout + r.stderr\n"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\n"
        f"from {Path(__file__).stem} import _wait_for\n"
        f"pids = _wait_for(os.environ[{_ENV!r}], True)\n"
        f"open({str(said)!r}, 'w').write(json.dumps({{'id': os.environ.get({_ENV!r}), 'pids': pids, "
        "'said': json.loads(r.stdout.strip().splitlines()[-1])}))\n"
        "print('ok   test_fixture_tooth')\n")
    # The tester is reached only through its interface, bin/cairn test (45c168cc1ff1).
    r = subprocess.run([*bash_script_argv(ROOT / "bin" / "cairn"), "test", str(proof)],
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0 and f"  green  {proof}" in r.stdout.splitlines(), r.stdout + r.stderr
    got = json.loads(said.read_text())
    assert got["id"] and got["id"] != os.environ[_ENV], f"the fixture ran with no run id of its own: {got}"
    assert got["pids"], (f"the fixture run saw no loop carrying its own {_ENV}={got['id']} while it ran "
                         f"(the spawn said {got['said']}), so its end has nothing to collect")
    left = [p for p in got["pids"] if Path(f"/proc/{p}").exists()] + _wait_for(got["id"], False)
    _PIDS.extend(left)
    assert not left, (f"loop pids {sorted(set(left))} carrying the fixture run's {_ENV}={got['id']} outlived "
                      f"the run (the spawn said {got['said']})")


def test_outside_a_run_the_loop_is_unchanged():
    _require_the_seal()
    unit = _unit(4)
    call = ("import json, os, sys; sys.path.insert(0, %r); "
            "from cairn.tools.scratch.scratch import scratch_dir; "
            "os.environ['HOME'] = str(scratch_dir('cairn-proof-loopmark-home-4-')); "
            "from cairn.tools.base.shim import ensure_ground_loop; "
            "print(json.dumps(ensure_ground_loop()))") % str(ROOT)
    # beside the manager: a user unit, which carries the manager's environment and no run id
    r = subprocess.run(["systemd-run", "--user", "--wait", "--pipe", "--quiet", "--unit", f"{unit}-caller",
                        "-p", "CollectMode=inactive-or-failed", f"--setenv=CAIRN_GROUND_LOOP_UNIT={unit}",
                        "--", "python3", "-c", call], capture_output=True, text=True, timeout=120)
    _UNITS.append(f"{unit}-caller")
    assert r.returncode == 0 and '"spawned": "unit"' in r.stdout, (r.stdout[-400:], r.stderr[-400:])
    show = lambda prop: subprocess.run(["systemctl", "--user", "show", "-p", prop, "--value", f"{unit}.service"],
                                       capture_output=True, text=True, timeout=30).stdout.strip()
    env, mode = show("Environment"), show("CollectMode")
    assert f"{_ENV}=" not in env and mode == "inactive", f"{unit} carries id={f'{_ENV}=' in env}, CollectMode={mode!r}"


def main() -> int:
    fails = 0
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    try:
        for name, fn in tests:
            try:
                fn()
                print(f"  ok   {name}")
            except Exception as exc:  # noqa: BLE001
                fails += 1
                print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    finally:
        for pid in set(_PIDS):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        for u in _UNITS:
            for verb in ("stop", "reset-failed"):
                subprocess.run(["systemctl", "--user", verb, f"{u}.service"], capture_output=True, timeout=30)
    print(f"\n{'GREEN' if not fails else 'RED'} — {len(tests) - fails}/{len(tests)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
