"""The first shim starts the ground loop (ticket d6eb399ab6ad).

PROVES: falsifier clauses (1) with no loop running (liveness DEAD), one shim construction leaves
liveness LIVE within one beat plus spawn cost; (2) two shims started inside 100ms leave exactly
one loop; (3) the ground loop package gains no line; (4) the check lives in exactly one place,
the base. Plus the resting case: a LIVE record means no spawn at all.

THE SHIM IS CONSTRUCTED IN A SUBPROCESS WITH A SCRATCH HOME, because the instance root is read
from HOME at import (address.py:_INSTANCE) — so the liveness the shim reads, and the liveness
the loop it spawns writes, both sit under the scratch, and the live instance is never touched.
The unit name is the proof's own (CAIRN_GROUND_LOOP_UNIT), so the live loop's unit is neither
claimed nor stopped. Teardown stops the proof's unit and kills any setsid child, always.

A hollow build could not pass: tooth 1 needs a real loop to write a real record under the
scratch, tooth 5 needs the LIVE branch to spawn nothing (asserted by the unit NOT existing).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cairn.devices.cairn.machines.ground_loop.liveness import read_liveness, write_liveness  # noqa: E402

# The falsifier's four DONE clauses, one tooth each (the coverage reader's contract:
# {ticket: {clause: tooth}}); the resting case is a fifth tooth beyond the clauses.
PROVES = {
    "d6eb399ab6ad": {
        "1": "test_dead_to_live_one_shim",        # DEAD before, one shim, LIVE within one beat plus spawn
        "2": "test_two_shims_one_loop",           # two shims inside 100ms leave exactly one loop
        "3": "test_ground_loop_package_untouched",  # the package gains no line
        "4": "test_check_lives_in_the_base_only",  # the check lives in the base, once
        "resting": "test_live_record_spawns_nothing",  # a LIVE record spawns nothing
    },
}

# The loop's first beat on this machine costs ~90-105s (cairn/tools/bus_client/bus_client.py:86,
# measured 2026-09-07) and the record is written AFTER the beat (loop.py:269), so the bound is
# the staleness threshold itself: a loop that cannot beat once inside it is not LIVE by definition.
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


def _liveness_home(home: Path) -> Path:
    return home / ".cairn" / "devices" / "cairn" / "0" / "machines" / "ground_loop"


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
    home = Path(tempfile.mkdtemp(prefix="d6eb-home-"))
    unit = f"cairn-ground-loop-proof-{os.getpid()}"
    try:
        now = datetime.now(timezone.utc)
        assert read_liveness(now, _liveness_home(home))["verdict"] == "DEAD"
        out = _construct(home, unit)
        assert out["verdict"] == "DEAD", out
        assert out["spawned"] in ("unit", "setsid"), out
        deadline = time.monotonic() + LIVE_WITHIN_S
        verdict = "DEAD"
        while time.monotonic() < deadline:
            verdict = read_liveness(datetime.now(timezone.utc).astimezone(), _liveness_home(home))["verdict"]
            if verdict == "LIVE":
                break
            time.sleep(1)
        assert verdict == "LIVE", f"no LIVE record under {home} within {LIVE_WITHIN_S}s after spawn {out}"
        print("ok test_dead_to_live_one_shim")
    finally:
        _stop(unit)
        _kill_setsid_children(home)
        shutil.rmtree(home, ignore_errors=True)


def test_two_shims_one_loop() -> None:
    home = Path(tempfile.mkdtemp(prefix="d6eb-home-"))
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
        found = None
        while time.monotonic() < deadline:
            found = read_liveness(datetime.now(timezone.utc).astimezone(), _liveness_home(home))
            if found["verdict"] == "LIVE":
                break
            time.sleep(1)
        assert found and found["verdict"] == "LIVE", (found, outs)
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


def test_live_record_spawns_nothing() -> None:
    home = Path(tempfile.mkdtemp(prefix="d6eb-home-"))
    unit = f"cairn-ground-loop-proof-{os.getpid()}-live"
    try:
        lh = _liveness_home(home)
        lh.mkdir(parents=True)
        write_liveness(datetime.now(timezone.utc).astimezone(), {"beats": 1, "subscribers": []}, os.getpid(), lh)
        out = _construct(home, unit)
        assert out == {"verdict": "LIVE", "spawned": "none", "note": out["note"]}, out
        assert not _unit_active(unit), f"{unit} exists though the record was LIVE"
        print("ok test_live_record_spawns_nothing")
    finally:
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
    print("ok test_check_lives_in_the_base_only")


if __name__ == "__main__":
    test_check_lives_in_the_base_only()
    test_ground_loop_package_untouched()
    test_live_record_spawns_nothing()
    test_dead_to_live_one_shim()
    test_two_shims_one_loop()
    print("test_shim_starts_the_loop: green")
