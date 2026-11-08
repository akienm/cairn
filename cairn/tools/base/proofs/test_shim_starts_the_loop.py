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

from cairn.tools.base import singleton  # noqa: E402
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
}

# The loop's first beat on this machine costs ~90-105s (cairn/tools/bus_client/bus_client.py:86,
# measured 2026-09-07) and the record is written AFTER the beat (loop.py:269), so the bound is
# five beats.
LIVE_WITHIN_S = 300.0

CONSTRUCT = (
    "import json, sys; sys.path.insert(0, %r); "
    "from cairn.devices.tester.shim import TesterShim; "
    "s = TesterShim(); print(json.dumps(s._ground_loop))"
)


def _env(home: Path, unit: str) -> dict:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["CAIRN_GROUND_LOOP_UNIT"] = unit
    env["PYTHONPATH"] = str(ROOT)
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


def _kill_setsid_children(home: Path) -> None:
    # A fall-through spawn is a python process whose HOME is the scratch — find it by its
    # environment, never by name alone.
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            env = (p / "environ").read_bytes()
        except OSError:
            continue
        if f"HOME={home}".encode() in env and b"cairn.devices.cairn.machines.ground_loop" in (p / "cmdline").read_bytes():
            try:
                os.kill(int(p.name), 15)
            except OSError:
                pass


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


if __name__ == "__main__":
    # The house runner: every tooth runs and prints PASS or FAIL by name, so a hollow reading
    # that takes shim.py's build away reads each tooth failing rather than one crash (UNREAD).
    rc = 0
    for t in (test_check_lives_in_the_base_only, test_ground_loop_package_untouched,
              test_a_held_lock_spawns_nothing, test_dead_to_live_one_shim, test_two_shims_one_loop):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            rc = 1
            print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}")
    print("test_shim_starts_the_loop: green" if rc == 0 else "test_shim_starts_the_loop: RED")
    sys.exit(rc)
