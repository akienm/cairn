"""A ground loop the base shim spawns as a systemd unit under a scratch HOME carries the caller's
CAIRN_ environment and none of the user manager's (ticket 34da9a98a484).

Measured 2026-11-12 on akienasus: `systemctl --user show-environment` holds
CAIRN_BUS_HOME=akiendelllinux.local:7419, and a transient `systemd-run --user` unit prints it, so a
proof's scratch loop dialed the Dell's live bus whatever home_env stripped. The same unit with
`-p UnsetEnvironment=CAIRN_BUS_HOME` prints none.

PROVES: (1) a scratch-HOME spawn's systemd-run argv sets every CAIRN_* the caller carries and unsets
every manager CAIRN_* the caller lacks, and a real transient unit run with those flags carries no
CAIRN_BUS_HOME; (2) a spawn under the account's own HOME has the argv it always had.

The argv teeth replace subprocess.run in this process only, so nothing is spawned by them; the one
real unit is `env`, run once and waited for.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

PROVES = {"34da9a98a484": {
    "1": "test_a_scratch_spawn_unsets_the_managers_bus",
    "2": "test_a_live_spawn_argv_is_unchanged",
}}

FAKE_MANAGER = "CAIRN_BUS_HOME=x.invalid:1\nCAIRN_HOME_HOST=x.invalid\nLANG=C\n"
_failures: list[str] = []


def _captured_argv(env_home: str, lock_home: Path) -> list[str]:
    """ensure_ground_loop's systemd-run argv with HOME=env_home, nothing spawned."""
    from cairn.tools.base import shim  # bound at call time: a hollow build takes the subject away
    calls: list[list[str]] = []
    real_run = subprocess.run

    def fake_run(argv, *a, **kw):
        calls.append(list(argv))
        out = FAKE_MANAGER if list(argv[:3]) == ["systemctl", "--user", "show-environment"] else ""
        return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")

    saved = dict(os.environ)
    try:
        os.environ["HOME"] = env_home
        os.environ.pop("CAIRN_BUS_HOME", None)
        os.environ.pop("CAIRN_HOME_HOST", None)
        os.environ.pop("CAIRN_TESTER_TEST_ID", None)
        os.environ["CAIRN_ROOT"] = "/r"
        os.environ["CAIRN_GROUND_LOOP_UNIT"] = f"cairn-ground-loop-34da-{os.getpid()}"
        subprocess.run = fake_run
        out = shim.ensure_ground_loop(home=lock_home, log=lock_home / "loop.log")
    finally:
        subprocess.run = real_run
        os.environ.clear()
        os.environ.update(saved)
    units = [c for c in calls if c and c[0] == "systemd-run"]
    assert units, f"no systemd-run call was made: {out} calls={calls}"
    return units[0]


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail}"))
    if not ok:
        _failures.append(name)


def test_a_scratch_spawn_unsets_the_managers_bus() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("34da-home-")
    argv = _captured_argv(str(home), home)
    head = argv[:argv.index("--")]
    pairs = list(zip(head, head[1:]))
    ok = (("-p", "UnsetEnvironment=CAIRN_BUS_HOME") in pairs
          and ("-p", "UnsetEnvironment=CAIRN_HOME_HOST") in pairs
          and "--setenv=CAIRN_ROOT=/r" in head
          and not any("UnsetEnvironment=LANG" in a for a in head))
    detail = f"argv={head}"
    if ok and shutil.which("systemd-run"):
        from cairn.tools.base import shim
        saved = os.environ.get("HOME")
        try:
            os.environ["HOME"] = str(home)
            bus = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("CAIRN_BUS_")}
            flags = shim._manager_env_flags(str(home))
        finally:
            os.environ["HOME"] = saved or ""
            os.environ.update(bus)
        r = subprocess.run(["systemd-run", "--user", "--quiet", "--wait", "--pipe", *flags, "--", "env"],
                           capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
        leaked = [ln for ln in r.stdout.splitlines() if ln.startswith("CAIRN_BUS_HOME=")]
        ok = r.returncode == 0 and leaked == []
        detail = f"real unit rc={r.returncode} leaked={leaked} err={r.stderr[-200:]!r}"
    check("test_a_scratch_spawn_unsets_the_managers_bus", ok, detail)


def test_a_live_spawn_argv_is_unchanged() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    import pwd
    lock = scratch_dir("34da-lock-")
    argv = _captured_argv(pwd.getpwuid(os.getuid()).pw_dir, lock)
    head = argv[:argv.index("--")]
    extra = [a for a in head if "UnsetEnvironment=" in a
             or (a.startswith("--setenv=CAIRN_") and not a.startswith("--setenv=CAIRN_TESTER_TEST_ID="))]
    check("test_a_live_spawn_argv_is_unchanged", extra == [], f"live argv gained {extra}")


def main() -> int:
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                check(name, False, f"raised {type(exc).__name__}: {exc}")
    print("\nGREEN" if not _failures else f"\nRED — {len(_failures)} failure(s)")
    return 1 if _failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
