"""Proof for ticket 34da9a98a484: a scratch ground loop carries no manager bus.

MEASURED 2026-11-12 on akienasus: ``systemctl --user show-environment`` holds
CAIRN_BUS_HOME=akiendelllinux.local:7419, and a transient ``systemd-run --user --wait --pipe -- env``
prints it. shim.ensure_ground_loop spawned the loop through systemd-run with only HOME and PATH set
by hand, so a proof's scratch-HOME loop dialled the Dell's live bus.

  1. A SCRATCH-HOME SPAWN SETS THE CALLER'S CAIRN_* AND UNSETS THE MANAGER'S OTHERS; a unit run
     with those flags carries no CAIRN_BUS_HOME (where systemd-run is on PATH).
  2. A SPAWN UNDER THE ACCOUNT'S OWN HOME HAS THE ARGV IT HAD BEFORE THIS TICKET.

    bin/cairn test cairn/tools/base/proofs/test_a_scratch_loop_carries_no_manager_bus.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"34da9a98a484": {"1": "test_a_scratch_spawn_unsets_the_managers_bus",
                           "2": "test_a_live_spawn_argv_is_unchanged"}}

MANAGER_ENV = "CAIRN_BUS_HOME=x:1\nCAIRN_HOME_HOST=x\nLANG=C\n"


class _Answer:
    def __init__(self, stdout=""):
        self.returncode, self.stdout, self.stderr = 0, stdout, ""


def _captured_argv(home: str, env: dict) -> list[str]:
    """ensure_ground_loop's systemd-run argv under HOME=home and exactly ``env``'s CAIRN_*, with
    subprocess.run faked: show-environment answers MANAGER_ENV, systemd-run succeeds. Nothing
    is spawned."""
    from cairn.tools.base import shim
    from cairn.tools.scratch.scratch import home_env, scratch_dir
    where = scratch_dir("34da-")
    seen: list[list[str]] = []
    real_run, saved = subprocess.run, dict(os.environ)

    def fake(argv, *a, **k):
        if argv[:3] == ["systemctl", "--user", "show-environment"]:
            return _Answer(MANAGER_ENV)
        if argv and argv[0] == "systemd-run":
            seen.append(list(argv))
            return _Answer()
        return real_run(argv, *a, **k)

    try:
        # HOME comes from the published scratch env (ticket 3301915df481), never set by hand.
        target = {k: v for k, v in home_env(home).items() if not k.startswith("CAIRN_")}
        target.update(env)
        os.environ.clear()
        os.environ.update(target)
        subprocess.run = fake
        out = shim.ensure_ground_loop(home=where, log=where / "l")
        assert out["spawned"] == "unit", f"the fake spawn did not take: {out}"
    finally:
        subprocess.run = real_run
        os.environ.clear()
        os.environ.update(saved)
        shutil.rmtree(where, ignore_errors=True)
    assert len(seen) == 1, f"expected one systemd-run, saw {seen}"
    return seen[0]


def _before_dashdash(argv: list[str]) -> list[str]:
    return argv[:argv.index("--")]


def test_a_scratch_spawn_unsets_the_managers_bus() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("34da-home-")
    try:
        argv = _captured_argv(str(home), {"CAIRN_ROOT": "/r"})
    finally:
        shutil.rmtree(home, ignore_errors=True)
    head = _before_dashdash(argv)
    pairs = list(zip(head, head[1:]))
    assert ("-p", "UnsetEnvironment=CAIRN_BUS_HOME") in pairs, f"the manager's bus is not unset: {head}"
    assert ("-p", "UnsetEnvironment=CAIRN_HOME_HOST") in pairs, f"the manager's home host is not unset: {head}"
    assert "--setenv=CAIRN_ROOT=/r" in head, f"the caller's CAIRN_ROOT is not carried: {head}"
    assert not any(a == "UnsetEnvironment=LANG" for a in head), f"a non-CAIRN key was unset: {head}"
    if shutil.which("systemd-run") and shutil.which("systemctl"):
        # the shim's own flags, read against THIS box's real user manager
        from cairn.tools.base import shim
        saved = dict(os.environ)
        try:
            for k in [k for k in os.environ if k.startswith("CAIRN_")]:
                del os.environ[k]
            os.environ["CAIRN_ROOT"] = "/r"
            flags = shim._scratch_env_flags(subprocess)
        finally:
            os.environ.clear()
            os.environ.update(saved)
        cmd = ["systemd-run", "--user", "--quiet", "--wait", "--pipe", *flags]
        r = subprocess.run(cmd + ["--", "env"], capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, f"systemd-run failed: {r.stderr[-400:]}"
        leaked = [ln for ln in r.stdout.splitlines() if ln.startswith("CAIRN_BUS_HOME=")]
        assert leaked == [], f"a unit run with the flags carries the manager's bus: {leaked}"
        assert "CAIRN_ROOT=/r" in r.stdout.splitlines(), "the unit lost the caller's CAIRN_ROOT"
    print("ok test_a_scratch_spawn_unsets_the_managers_bus")


def test_a_live_spawn_argv_is_unchanged() -> None:
    import pwd
    own = pwd.getpwuid(os.getuid()).pw_dir
    argv = _captured_argv(own, {"CAIRN_ROOT": "/r", "CAIRN_TESTER_TEST_ID": "t-1"})
    head = _before_dashdash(argv)
    assert not any(a.startswith("UnsetEnvironment=") for a in head), f"a live spawn unsets: {head}"
    cairn = [a for a in head if a.startswith("--setenv=CAIRN_")]
    assert cairn == ["--setenv=CAIRN_TESTER_TEST_ID=t-1"], f"a live spawn carries extra CAIRN_: {cairn}"
    print("ok test_a_live_spawn_argv_is_unchanged")


if __name__ == "__main__":
    failed = 0
    for tooth in (test_a_scratch_spawn_unsets_the_managers_bus, test_a_live_spawn_argv_is_unchanged):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
            failed += 1
            print(f"RED {tooth.__name__}: {type(exc).__name__}: {exc}")
    raise SystemExit(1 if failed else 0)
