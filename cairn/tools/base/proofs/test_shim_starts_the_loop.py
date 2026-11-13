"""The first shim starts the ground loop (ticket d6eb399ab6ad).

PROVES: falsifier clauses (1) with no loop running (its lock free), one shim construction leaves
a loop holding the lock and beating within one beat plus spawn cost; (2) two shims started inside
100ms leave exactly one loop; (3) the ground loop package gains no line; (4) the check lives in
exactly one place, the base — and in no device launcher (D19). Plus the resting case: a held lock
means no spawn at all (ticket 6208d0a27d6e clause 5).

"IS THE LOOP UP" IS ITS HELD LOCK (ticket 6208d0a27d6e, Q#53). The shim once read the loop's
record and judged it by its age; that staleness verdict is retired. It now probes the loop's
run.lock through cairn/tools/base/singleton.py: held means a loop runs, whatever its pace.

THE SHIM IS CONSTRUCTED IN A SUBPROCESS WITH A SCRATCH HOME, because the instance root is read
from HOME at import (address.py:_INSTANCE) — so the lock the shim probes, and the lock and record
the loop it spawns writes, all sit under the scratch, and the live instance is never touched.
The unit name is the proof's own (CAIRN_GROUND_LOOP_UNIT), so the live loop's unit is neither
claimed nor stopped. Teardown stops the proof's unit and kills any setsid child, always.

A hollow build could not pass: tooth 1 needs a real loop to write a real record under the
scratch, tooth 5 needs the held branch to spawn nothing (asserted by the unit NOT existing).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

try:  # a hollow revert takes singleton.py away: fail inside the tooth, never crash UNREAD
    from cairn.tools.base import singleton  # noqa: E402
except Exception as _exc:  # noqa: BLE001
    class _Absent:
        def __init__(self, exc):
            self._exc = exc

        def __getattr__(self, name):
            raise self._exc
    singleton = _Absent(_exc)
from cairn.tools.scratch.scratch import scratch_dir

# The falsifier's four DONE clauses, one tooth each (the coverage reader's contract:
# {ticket: {clause: tooth}}); the resting case is a fifth tooth beyond the clauses.
PROVES = {
    "d6eb399ab6ad": {
        "1": "test_dead_to_live_one_shim",        # lock free before, one shim, a loop holding it and beating within one beat plus spawn
        "2": "test_two_shims_one_loop",           # two shims inside 100ms leave exactly one loop
        "3": "test_ground_loop_package_untouched",  # the package gains no line
        "4": "test_check_lives_in_the_base_only",  # the check lives in the base, once
        "resting": "test_a_held_lock_spawns_nothing",  # a held lock spawns nothing
    },
    "6208d0a27d6e": {"5": "test_a_held_lock_spawns_nothing"},
    "ea6e465680a3": {"1": "test_the_setsid_path_leaves_no_scratch_process",
                     "2": "test_the_setsid_path_leaves_no_scratch_process"},
}

# The loop's first beat on this machine costs ~90-105s (cairn/tools/bus_client/bus_client.py:86,
# measured 2026-09-07) and the record is written AFTER the beat (loop.py:269), so the bound is
# five beats.
LIVE_WITHIN_S = 300.0
# Two teeth may each wait the whole bound when a hollow revert takes the loop's record away
# (ticket 6208d0a27d6e: a reverted world never writes beat.json), so the budget outlasts both.
PROOF_TIMEOUT_S = 1200

NOT_THE_HOME = "not-this-box.invalid"

CONSTRUCT = (
    "import json, sys; sys.path.insert(0, %r); "
    "from cairn.devices.tester.shim import TesterShim; "
    "s = TesterShim(); print(json.dumps(s._ground_loop))"
)


def _env(home: Path, unit: str) -> dict:
    from cairn.tools.scratch.scratch import home_env  # ticket 3301915df481: no caller bus address
    # CAIRN_HOME_HOST names no box (ticket ea6e465680a3): the scratch loop's web_server pulse reads
    # this box as not the cairn home and starts no listener, on any OS, so nothing outlives the loop.
    env = home_env(home, CAIRN_GROUND_LOOP_UNIT=unit, PYTHONPATH=str(ROOT),
                   CAIRN_HOME_HOST=NOT_THE_HOME)
    return env


def _construct(home: Path, unit: str) -> dict:
    r = subprocess.run([sys.executable, "-c", CONSTRUCT % str(ROOT)], env=_env(home, unit),
                       capture_output=True, text=True, timeout=120, cwd=str(ROOT))
    assert r.returncode == 0, r.stderr[-800:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def _loop_home(home: Path) -> Path:
    return home / ".cairn" / "devices" / "cairn" / "0" / "machines" / "ground_loop"


def _beating(home: Path) -> bool:
    """A loop is up under the scratch: its lock is held and its first record stands."""
    lh = _loop_home(home)
    return singleton.held(lh / "run.lock") and (lh / "beat.json").exists()


def _stop(unit: str) -> None:
    subprocess.run(["systemctl", "--user", "stop", f"{unit}.service"], capture_output=True, text=True)
    subprocess.run(["systemctl", "--user", "reset-failed", f"{unit}.service"], capture_output=True, text=True)


def _unit_active(unit: str) -> bool:
    r = subprocess.run(["systemctl", "--user", "is-active", f"{unit}.service"], capture_output=True, text=True)
    return r.stdout.strip() == "active"


def _kill_setsid_children(home: Path) -> list[int]:
    """Reap every process whose environment holds HOME=<scratch>, whatever it runs (ticket
    ea6e465680a3: the setsid path left a web_server listener and a scratch bus standing, because
    this once matched ground_loop cmdlines only). Returns the pids it signalled."""
    signalled = []
    for pid in _scratch_processes(home):
        try:
            os.kill(pid, 15)
            signalled.append(pid)
        except OSError:
            pass
    return signalled


def _scratch_processes(home: Path) -> list[int]:
    """Every /proc process whose environ holds HOME=<scratch> exactly, this one excepted."""
    want = f"HOME={home}".encode()
    found = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            env = (p / "environ").read_bytes()
        except OSError:
            continue
        if want in env.split(b"\0"):
            found.append(int(p.name))
    return found


def test_dead_to_live_one_shim() -> None:
    home = scratch_dir("d6eb-home-")
    unit = f"cairn-ground-loop-proof-{os.getpid()}"
    try:
        assert not singleton.held(_loop_home(home) / "run.lock")
        out = _construct(home, unit)
        assert out["up"] is False, out
        assert out["spawned"] in ("unit", "setsid"), out
        deadline = time.monotonic() + LIVE_WITHIN_S
        up = False
        while time.monotonic() < deadline:
            up = _beating(home)
            if up:
                break
            time.sleep(1)
        assert up, f"no loop holds the lock and beats under {home} within {LIVE_WITHIN_S}s after spawn {out}"
        print("ok test_dead_to_live_one_shim")
    finally:
        _stop(unit)
        _kill_setsid_children(home)
        shutil.rmtree(home, ignore_errors=True)


def test_two_shims_one_loop() -> None:
    home = scratch_dir("d6eb-home-")
    unit = f"cairn-ground-loop-proof-{os.getpid()}-two"
    try:
        procs = [subprocess.Popen([sys.executable, "-c", CONSTRUCT % str(ROOT)], env=_env(home, unit),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(ROOT))
                 for _ in range(2)]
        outs = []
        for p in procs:
            so, se = p.communicate(timeout=120)
            assert p.returncode == 0, se[-800:]
            outs.append(json.loads(so.strip().splitlines()[-1]))
        spawned = [o["spawned"] for o in outs]
        # Exactly one loop: either the second attempt was refused by the held unit name, or
        # both spawned and the runner's own flock made the loser exit 3 — which the record shows
        # as one pid. Wait for the record, then count.
        deadline = time.monotonic() + LIVE_WITHIN_S
        up = False
        while time.monotonic() < deadline:
            up = _beating(home)
            if up:
                break
            time.sleep(1)
        assert up, outs
        pids = _scratch_loops(home, unit)
        assert len(pids) == 1, f"loops alive under {home}: {pids}; attempts {spawned}"
        print(f"ok test_two_shims_one_loop  (attempts {spawned}, one pid)")
    finally:
        _stop(unit)
        _kill_setsid_children(home)
        shutil.rmtree(home, ignore_errors=True)


def _unit_main_pid(unit: str) -> str | None:
    r = subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value", f"{unit}.service"],
                       capture_output=True, text=True)
    pid = r.stdout.strip()
    return pid if pid.isdigit() and pid != "0" else None


def _scratch_loops(home: Path, unit: str) -> set[str]:
    """Every loop alive under the scratch HOME: the unit's MainPID as systemd reports it, plus
    any setsid fall-through found by its environment. The unit's process is asked of systemd,
    not read from /proc, because the seal runs this proof in a user namespace and /proc/<pid>/
    environ of a process the user manager spawned OUTSIDE it is unreadable there — the proof
    then counted zero loops with one plainly beating (sealed red 2026-09-17)."""
    pids = {p.name for p in Path("/proc").iterdir() if p.name.isdigit() and _is_scratch_loop(p, home)}
    main = _unit_main_pid(unit)
    if main:
        pids.add(main)
    return pids


def _is_scratch_loop(p: Path, home: Path) -> bool:
    try:
        env = (p / "environ").read_bytes()
        cmd = (p / "cmdline").read_bytes()
    except OSError:
        return False
    return f"HOME={home}".encode() in env and b"cairn.devices.cairn.machines.ground_loop" in cmd


def test_a_held_lock_spawns_nothing() -> None:
    # No record is written at all: the held lock alone says the loop is up (6208d0a27d6e clause 5).
    home = scratch_dir("d6eb-home-")
    unit = f"cairn-ground-loop-proof-{os.getpid()}-live"
    claim = None
    try:
        lh = _loop_home(home)
        lh.mkdir(parents=True)
        claim = singleton.claim(lh / "run.lock")
        out = _construct(home, unit)
        assert out == {"up": True, "spawned": "none", "note": out["note"]}, out
        assert not _unit_active(unit), f"{unit} exists though the lock was held"
        assert not (lh / "beat.json").exists(), "nothing wrote a record under a held lock"
        print("ok test_a_held_lock_spawns_nothing")
    finally:
        if claim is not None:
            claim.release()
        _stop(unit)
        shutil.rmtree(home, ignore_errors=True)


def test_ground_loop_package_untouched() -> None:
    # The package's CODE, top level only (:(glob) keeps * off the slash) — its proofs and
    # validations are other tickets' to move, and one of them stands uncommitted today.
    r = subprocess.run(["git", "diff", "--stat", "HEAD", "--",
                        ":(glob)cairn/devices/cairn/machines/ground_loop/*.py"],
                       cwd=str(ROOT), capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == "", r.stdout
    print("ok test_ground_loop_package_untouched")


def test_check_lives_in_the_base_only() -> None:
    base = ROOT / "cairn" / "tools" / "base" / "shim.py"
    assert "def ensure_ground_loop(" in base.read_text()
    assert base.read_text().count("ensure_ground_loop(") >= 2  # the def and the one call
    others = [p for p in (ROOT / "cairn" / "devices").glob("*/shim.py") if "ensure_ground_loop(" in p.read_text()]
    assert others == [], others
    # Widened under D19: a device launcher (cairn/devices/<d>/<i>/bin/*) is a second starter if it
    # spawns the loop module itself — the librarian's _ensure_loop was one, and it started a module
    # path that no longer resolved, so it silently started nothing.
    starts = ("-m cairn.devices.ground_loop", "-m cairn.devices.cairn.machines.ground_loop", "_ensure_loop")
    launchers = [p for p in (ROOT / "cairn" / "devices").glob("*/*/bin/*") if p.is_file()]
    assert any(p.name == "librarian" for p in launchers), "the librarian launcher is in the population"
    starters = [str(p.relative_to(ROOT)) for p in launchers
                if any(s in p.read_text(errors="replace") for s in starts)]
    assert starters == [], f"a device launcher starts the ground loop beside the shim: {starters}"
    print("ok test_check_lives_in_the_base_only")


def _path_without_systemd_run(where: Path) -> str:
    """A PATH dir holding what the loop runs, with no systemd-run, so the shim takes the setsid
    fall-through. python3 is an exec wrapper to this interpreter (a bare symlink loses the venv's
    site-packages); the rest are links to the real tools."""
    bin_ = where / "bin"
    bin_.mkdir(parents=True)
    py = bin_ / "python3"
    py.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    py.chmod(0o755)
    for tool in ("systemctl", "git", "env", "sh", "bash", "hostname"):
        real = shutil.which(tool)
        if real:
            (bin_ / tool).symlink_to(real)
    return str(bin_)


def test_the_setsid_path_leaves_no_scratch_process() -> None:
    """ea6e465680a3 clause 1: with systemd-run off PATH, the shim spawns the loop with setsid; after
    the teardown no process carrying HOME=<scratch> stands. Clause 2: the scratch loop reads this
    box as not the cairn home, so its web_server.log records no listener started."""
    home = scratch_dir("ea6e-home-")
    unit = f"cairn-ground-loop-proof-{os.getpid()}-setsid"
    env = _env(home, unit)
    env["PATH"] = _path_without_systemd_run(home)
    env["CAIRN_WEB_SERVER_PORT"] = "1"
    try:
        r = subprocess.run([sys.executable, "-c", CONSTRUCT % str(ROOT)], env=env,
                           capture_output=True, text=True, timeout=120, cwd=str(ROOT))
        assert r.returncode == 0, r.stderr[-800:]
        out = json.loads(r.stdout.strip().splitlines()[-1])
        assert out["spawned"] == "setsid", f"the shim did not take the setsid path: {out}"
        deadline = time.monotonic() + LIVE_WITHIN_S
        while time.monotonic() < deadline and not _beating(home):
            time.sleep(1)
        assert _beating(home), f"no loop beats under {home} within {LIVE_WITHIN_S}s"
        time.sleep(15)                      # the beat's pulses act
        log = home / ".cairn" / "logs" / "web_server" / "0" / "web_server.log"
        lines = log.read_text(errors="replace").splitlines() if log.exists() else []
        started = [ln for ln in lines if "started the shim" in ln]
        assert started == [], f"a scratch loop started a web_server listener: {started}"
        _stop(unit)
        _kill_setsid_children(home)
        time.sleep(3)
        left = []
        for pid in _scratch_processes(home):
            try:
                cmd = (Path("/proc") / str(pid) / "cmdline").read_bytes().replace(b"\0", b" ")[:120]
            except OSError:
                continue
            left.append((pid, cmd))
        assert left == [], f"processes of {home} outlived the teardown: {left}"
        print("ok test_the_setsid_path_leaves_no_scratch_process")
    finally:
        _stop(unit)
        _kill_setsid_children(home)
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    # The house runner: every tooth runs and prints PASS or FAIL by name, so a hollow reading
    # that takes shim.py's build away reads each tooth failing rather than one crash (UNREAD).
    rc = 0
    for t in (test_check_lives_in_the_base_only, test_ground_loop_package_untouched,
              test_a_held_lock_spawns_nothing, test_dead_to_live_one_shim, test_two_shims_one_loop,
              test_the_setsid_path_leaves_no_scratch_process):
        try:
            t()
            print(f"  PASS  {t.__name__}", flush=True)
        except Exception as exc:  # noqa: BLE001
            rc = 1
            print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}", flush=True)
    print("test_shim_starts_the_loop: green" if rc == 0 else "test_shim_starts_the_loop: RED")
    sys.exit(rc)
