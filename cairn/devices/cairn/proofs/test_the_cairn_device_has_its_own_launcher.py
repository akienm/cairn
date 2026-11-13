"""The cairn device carries its own self-named launcher, and the floor lays it like every other.

Measured 2026-11-12 (ticket 50ca14d4489e): cairn/tools/base/proofs/test_cli_reaches.py was red on
akienasus for the cairn device (no ~/.cairn/devices/cairn/0/bin/cairn). cairn/devices/cairn had no
0/bin/ in class-space at all — git shows cairn/devices/cairn/0/bin/cairn never existed — so the
wiring walk had nothing to link. akiendelllinux read green on a hand-placed file dated Sep 2.

PROVES (teeth below):
  (1) a scratch box's wiring walk links devices/cairn/0/bin/cairn to the class file;
  (2) that linked launcher, run with no arguments, exits 0 and prints "device: cairn".

The scratch box is 96c1's (bin/proofs/test_the_floor_links_a_class_verb_that_landed_late.py): a
scratch instance root, a scratch socket dir and a stand-in `sudo`, so nothing live is touched.

THE BOX OWNS ITS BUS (2026-11-13, kicked back from PROVEME on akiendelllinux). The launcher speaks
through cli_main, which dials the bus at CAIRN_BUS_HOME, else the LIVE home. On akienasus the live
bus answered and tooth 2 read green; on the Dell the hollow's code found the live bus stale, sent
it `shutdown` (stops.jsonl, 09:17:36Z) and then timed out at the live bus.sock. So every CAIRN_BUS_*
the caller carries is dropped, the box names a scratch bus home and its own unit, and main() shuts
that bus down after the teeth.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAIRN = ROOT / "bin" / "cairn"
CLASS = ROOT / "cairn" / "devices" / "cairn" / "0" / "bin" / "cairn"

PROVES = {"50ca14d4489e": {
    "1": "test_the_walk_links_the_cairn_launcher",
    "2": "test_the_linked_launcher_names_the_device",
}}

_failures: list[str] = []
UNIT = f"cairn-own-launcher-proof-bus-{os.getpid()}"


def _env(home: Path) -> dict:
    d = home / "fakebin"
    d.mkdir(exist_ok=True)
    (d / "sudo").write_text("#!/bin/sh\necho 'sudo: a password is required' >&2\nexit 1\n")
    (d / "sudo").chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith("CAIRN_BUS_")}
    env["CAIRN_BUS_HOME"] = str(home / "bus")      # the box's own bus, never the live one
    env["CAIRN_BUS_UNIT"] = UNIT
    env.setdefault("CAIRN_VENV", str(Path.home() / ".cairn" / "venv"))
    # the bus the launcher spawns is `python3 -m ...bus serve` off PATH; a bare system python3
    # has no psycopg2 and dies before bus.sock (measured 2026-11-13), so the venv leads
    env["PATH"] = f"{d}:{Path(env['CAIRN_VENV']) / 'bin'}:{env.get('PATH', '')}"
    env["CAIRN_INSTANCE_ROOT"] = str(home / "devices")
    (home / "nosock").mkdir(exist_ok=True)
    env["CAIRN_PG_SOCKET_DIR"] = str(home / "nosock")
    env["CAIRN_BOOT_LOG"] = str(home / "boot")
    for k in ("CAIRN_SUDO_PW", "SUDO_ASKPASS", "CAIRN_FLOOR_FINDINGS", "CAIRN_CLASS_ROOT"):
        env.pop(k, None)
    return env


_BOX: list = []


def _box() -> tuple[Path, dict]:
    """One scratch box, walked once by a bin/cairn launch (the floor's first walk)."""
    if not _BOX:
        from cairn.tools.scratch.scratch import scratch_dir
        home = scratch_dir("cairn-own-launcher-")
        env = _env(home)
        r = subprocess.run([str(CAIRN), "superclaude", "--dry-run"], env=env, capture_output=True,
                           text=True, timeout=300, cwd="/", stdin=subprocess.DEVNULL)
        assert r.returncode == 0, f"launch rc={r.returncode} err={r.stderr[-300:]!r}"
        assert (home / "devices" / "superclaude" / "0" / "bin" / "superclaude").exists(), \
            "the walk did not run — vacuous"
        _BOX.extend([home, env])
    return _BOX[0], _BOX[1]


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail}"))
    if not ok:
        _failures.append(name)


def test_the_walk_links_the_cairn_launcher() -> None:
    home, _ = _box()
    at = home / "devices" / "cairn" / "0" / "bin" / "cairn"
    check("test_the_walk_links_the_cairn_launcher",
          CLASS.is_file() and at.is_symlink() and at.resolve() == CLASS.resolve(),
          f"class_file={CLASS.is_file()} linked={at.is_symlink()}")


def test_the_linked_launcher_names_the_device() -> None:
    home, env = _box()
    at = home / "devices" / "cairn" / "0" / "bin" / "cairn"
    if not at.exists():
        check("test_the_linked_launcher_names_the_device", False, f"nothing at {at}")
        return
    # the walk ran with no pg socket so the floor brings nothing up; the scratch bus this run
    # spawns opens the store at import and dies on that empty dir (measured 2026-11-13), so the
    # launcher runs with the box's own bus home and the host's store, as every scratch-bus proof does
    run_env = {k: v for k, v in env.items() if k != "CAIRN_PG_SOCKET_DIR"}
    r = subprocess.run([str(at)], env=run_env, capture_output=True, text=True, timeout=120, cwd="/",
                       stdin=subprocess.DEVNULL)
    check("test_the_linked_launcher_names_the_device",
          r.returncode == 0 and "device: cairn" in r.stdout,
          f"rc={r.returncode} out={r.stdout[-200:]!r} err={r.stderr[-200:]!r}")


def _teardown() -> None:
    """Shut the box's scratch bus down, if one came up."""
    if not _BOX:
        return
    env = {**_BOX[1], "PYTHONPATH": str(ROOT)}
    subprocess.run([sys.executable, "-c",
                    "from cairn.tools.bus_client.remote import RemoteBus\n"
                    "try:\n    RemoteBus().shutdown()\nexcept Exception:\n    pass\n"],
                   env=env, cwd=str(ROOT), capture_output=True, timeout=90)
    subprocess.run(["systemctl", "--user", "stop", f"{UNIT}.service"], capture_output=True)
    subprocess.run(["systemctl", "--user", "reset-failed", f"{UNIT}.service"], capture_output=True)


def main() -> int:
    try:
        for name, fn in list(globals().items()):
            if name.startswith("test_") and callable(fn):
                try:
                    fn()
                except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                    check(name, False, f"raised {type(exc).__name__}: {exc}")
    finally:
        _teardown()
    print("\nGREEN" if not _failures else f"\nRED — {len(_failures)} failure(s)")
    return 1 if _failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
