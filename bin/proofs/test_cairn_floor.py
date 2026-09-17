"""The cairn command checks the floor before it resolves (ticket 0853294fe972).

PROVES: falsifier clauses (1) with the venv absent, one invocation lays a venv and then
answers; (2) with the db down, the same command starts it — or, for a user sudo refuses
(this box today, D7), refuses loud and named with exit 3 and the resolver never runs;
(3) on the happy path the floor adds under 10ms to bin/cairn's time-to-exec (n=15,
interleaved, HEAD's bin/cairn as the control arm); (4) `grep -n venv bin/cairn` is no
longer empty. Plus the resting case: with all three present, no lay-down runs.

Every tooth runs bin/cairn as a subprocess under a scratch HOME / CAIRN_INSTANCE_ROOT /
CAIRN_VENV / CAIRN_PG_SOCKET_DIR, so the live instance, venv and db are never touched.
The falsifier's `cairn librarian show status` is today `cairn librarian --status` (the
launcher's status face: prints whether port 80 listens, exits 0/1, spawns nothing), D10.

A hollow build could not pass: tooth 1 needs a real pip install into the scratch, tooth 3
needs a floor that costs nothing on the happy path, tooth 2 needs the refusal to reach
stderr BEFORE the librarian launcher would have printed.
"""
from __future__ import annotations

import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAIRN = ROOT / "bin" / "cairn"

PROVES = {
    "0853294fe972": {
        "1": "test_absent_venv_is_laid_then_answers",
        "2": "test_down_db_refuses_named_and_never_resolves",
        "3": "test_happy_path_costs_under_10ms",
        "4": "test_bin_cairn_names_the_venv",
        "resting": "test_present_floor_lays_nothing",
    },
}

BUDGET_MS = 10.0
N = 15


def _scratch() -> Path:
    return Path(tempfile.mkdtemp(prefix="0853-floor-"))


def _env(home: Path, *, venv: Path | None = None, sock: Path | None = None) -> dict:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["CAIRN_INSTANCE_ROOT"] = str(home / "devices")
    env["CAIRN_VENV"] = str(venv or Path.home() / ".cairn" / "venv")
    env["CAIRN_PG_SOCKET_DIR"] = str(sock or Path("/var/run/postgresql"))
    return env


def _probe_device(home: Path) -> None:
    # A stand-in device whose verb exits 0 at once, and the cairn/0 home already present —
    # so a run against it measures bin/cairn to exec and nothing after.
    d = home / "devices" / "probe" / "0" / "bin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "probe").write_text("#!/bin/sh\nexit 0\n")
    (d / "probe").chmod(0o755)
    (home / "devices" / "cairn" / "0").mkdir(parents=True, exist_ok=True)


def _run(cairn: Path, args: list, env: dict, timeout: float = 600) -> subprocess.CompletedProcess:
    return subprocess.run([str(cairn), *args], env=env, capture_output=True, text=True, timeout=timeout, cwd="/")


def test_absent_venv_is_laid_then_answers() -> None:
    home = _scratch()
    try:
        venv = home / "venv"
        assert not venv.exists()
        (home / "devices").mkdir()
        t = time.monotonic()
        r = _run(CAIRN, ["librarian", "--status"], _env(home, venv=venv))
        cost = time.monotonic() - t
        assert (venv / "bin" / "python3").exists(), f"no venv laid at {venv}: {r.stderr[-600:]}"
        assert r.stdout.startswith("librarian: web server is"), (r.returncode, r.stdout, r.stderr[-600:])
        assert r.returncode in (0, 1), r.returncode
        out = subprocess.run([str(venv / "bin" / "python3"), "-c", "import cairn; print(cairn.__file__)"],
                             capture_output=True, text=True, cwd="/")
        assert out.stdout.strip().startswith(str(ROOT)), out.stdout + out.stderr
        print(f"ok test_absent_venv_is_laid_then_answers  (laid + answered in {cost:.0f}s)")
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_down_db_refuses_named_and_never_resolves() -> None:
    home = _scratch()
    try:
        _probe_device(home)
        nosock = home / "nosock"
        nosock.mkdir()
        r = _run(CAIRN, ["librarian", "--status"], _env(home, sock=nosock))
        assert r.returncode == 3, (r.returncode, r.stdout, r.stderr)
        assert r.stderr.startswith("cairn: floor: db — "), r.stderr
        assert str(nosock / ".s.PGSQL.5432") in r.stderr, r.stderr
        assert r.stdout == "", f"the resolver ran: {r.stdout!r}"
        # The refusal carries the remedy: sudo's own words and the one line to lay, or the relay.
        assert "sudorelay" in r.stderr and "systemctl start postgresql.service" in r.stderr, r.stderr
        print("ok test_down_db_refuses_named_and_never_resolves")
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _control_cairn(into: Path) -> Path:
    # HEAD's bin/cairn as the control arm — the floor's cost is the treatment, measured
    # against the same dispatcher without it. Written beside the real one so $HERE/cmd resolves.
    r = subprocess.run(["git", "show", "HEAD:bin/cairn"], cwd=str(ROOT), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    p = into / "cairn"
    p.write_text(r.stdout)
    p.chmod(0o755)
    return p


def test_happy_path_costs_under_10ms() -> None:
    home = _scratch()
    try:
        _probe_device(home)
        env = _env(home)
        control_dir = home / "control-bin"
        control_dir.mkdir()
        control = _control_cairn(control_dir)
        env["CAIRN_CMD_DIR"] = str(ROOT / "bin" / "cmd")
        treat, ctrl = [], []
        for _ in range(N):  # interleaved: sequential arms measure drift as treatment
            t = time.perf_counter(); _run(CAIRN, ["probe"], env, timeout=30); treat.append((time.perf_counter() - t) * 1000)
            t = time.perf_counter(); _run(control, ["probe"], env, timeout=30); ctrl.append((time.perf_counter() - t) * 1000)
        mt, mc = statistics.median(treat), statistics.median(ctrl)
        delta = mt - mc
        assert delta < BUDGET_MS, f"floor adds {delta:.1f}ms (with {mt:.1f}, without {mc:.1f})"
        print(f"ok test_happy_path_costs_under_10ms  (with floor {mt:.1f}ms, without {mc:.1f}ms, delta {delta:+.1f}ms, n={N} interleaved)")
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_bin_cairn_names_the_venv() -> None:
    r = subprocess.run(["grep", "-n", "venv", str(CAIRN)], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip(), "grep -n venv bin/cairn is empty"
    print("ok test_bin_cairn_names_the_venv")


def test_present_floor_lays_nothing() -> None:
    home = _scratch()
    try:
        _probe_device(home)
        # A venv that is only a stub: verify would refuse it and apply would rebuild it —
        # so the stub surviving intact is the measurement that the heavy path never ran.
        stub = home / "stubvenv"
        (stub / "bin").mkdir(parents=True)
        (stub / "bin" / "python3").write_text("#!/bin/sh\nexit 0\n")
        (stub / "bin" / "python3").chmod(0o755)
        before = sorted(p.relative_to(stub) for p in stub.rglob("*"))
        r = _run(CAIRN, ["probe"], _env(home, venv=stub), timeout=30)
        assert r.returncode == 0, (r.returncode, r.stderr)
        after = sorted(p.relative_to(stub) for p in stub.rglob("*"))
        assert before == after, f"the lay-down ran over a present venv: {after}"
        print("ok test_present_floor_lays_nothing")
    finally:
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    test_bin_cairn_names_the_venv()
    test_present_floor_lays_nothing()
    test_down_db_refuses_named_and_never_resolves()
    test_happy_path_costs_under_10ms()
    test_absent_venv_is_laid_then_answers()
    print("test_cairn_floor: green")
