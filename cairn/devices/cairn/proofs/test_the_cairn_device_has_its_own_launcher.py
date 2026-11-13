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
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAIRN = ROOT / "bin" / "cairn"
CLASS = ROOT / "cairn" / "devices" / "cairn" / "0" / "bin" / "cairn"

PROVES = {"50ca14d4489e": {
    "1": "test_the_walk_links_the_cairn_launcher",
    "2": "test_the_linked_launcher_names_the_device",
}}

_failures: list[str] = []


def _env(home: Path) -> dict:
    d = home / "fakebin"
    d.mkdir(exist_ok=True)
    (d / "sudo").write_text("#!/bin/sh\necho 'sudo: a password is required' >&2\nexit 1\n")
    (d / "sudo").chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = f"{d}:{env.get('PATH', '')}"
    env["CAIRN_INSTANCE_ROOT"] = str(home / "devices")
    env.setdefault("CAIRN_VENV", str(Path.home() / ".cairn" / "venv"))
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
    r = subprocess.run([str(at)], env=env, capture_output=True, text=True, timeout=60, cwd="/",
                       stdin=subprocess.DEVNULL)
    check("test_the_linked_launcher_names_the_device",
          r.returncode == 0 and "device: cairn" in r.stdout,
          f"rc={r.returncode} out={r.stdout[-200:]!r} err={r.stderr[-200:]!r}")


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
