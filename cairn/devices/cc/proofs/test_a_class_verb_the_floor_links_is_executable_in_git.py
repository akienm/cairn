"""Every cc verb the floor links is executable in git, and superclaude launches.

Measured 2026-11-23 on akiendelllinux (ticket 846b6ca0eaf7): `cairn superclaude --dry-run` from the
house answered rc 127 "no such verb: superclaude". 60de22e64, a build made on Windows, created
cairn/devices/cc/superclaude.py as git mode 100644. The floor (bin/cairn.py _wire_instances) links
the instance's superclaude verb to it, and the dispatch refuses a file without the exec bit. The
class of defect: a script born on Windows lands as 100644, because Windows has no exec bit.

PROVES (teeth below):
  (1) every file git holds at cairn/devices/cc/superclaude.py and cairn/devices/cc/0/bin/* (the cc
      verbs the floor links) is mode 100755 in `git ls-files -s`;
  (2) `bin/cairn superclaude --dry-run` over a scratch instance root (cairn/0 already made, no
      superclaude link) exits 0, and the link it lays resolves to cairn/devices/cc/superclaude.py.

It measures only the cc component (outline 19.6, 9.4.2.3.7.1). Other devices' verb modes, and the
two proofs of other components the 100644 mode redded, are outside it: those two are resealed at
PROVEME, not run from here.

Every launch runs under a scratch instance root, a scratch socket dir and a stand-in `sudo` (the
env of bin/proofs/test_the_floor_links_a_class_verb_that_landed_late.py), so the live instance,
venv, db and host are never touched.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402

CAIRN = ROOT / "bin" / "cairn"
SUPERCLAUDE = ROOT / "cairn" / "devices" / "cc" / "superclaude.py"
GLOBS = ("cairn/devices/cc/superclaude.py", "cairn/devices/cc/0/bin/*")

PROVES = {"846b6ca0eaf7": {
    "1": "test_every_linked_class_verb_is_100755_in_git",
    "2": "test_superclaude_launches_over_a_scratch_box",
}, "b0931d04a912": {
    "1": "test_superclaude_launches_over_a_scratch_box",
}}

_failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail}"))
    if not ok:
        _failures.append(name)


def _scratch() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("class-verb-exec-")


def _env(home: Path) -> dict:
    d = home / "fakebin"
    d.mkdir(exist_ok=True)
    (d / "sudo").write_text("#!/bin/sh\necho 'sudo: a password is required' >&2\nexit 1\n")
    (d / "sudo").chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith("CAIRN_BUS_")}
    env["CAIRN_BUS_HOME"] = str(home / "bus")
    env["PATH"] = f"{d}:{env.get('PATH', '')}"
    env["CAIRN_INSTANCE_ROOT"] = str(home / "devices")
    env.setdefault("CAIRN_VENV", str(Path.home() / ".cairn" / "venv"))
    (home / "nosock").mkdir(exist_ok=True)
    env["CAIRN_PG_SOCKET_DIR"] = str(home / "nosock")
    env["CAIRN_BOOT_LOG"] = str(home / "boot")
    # MSYS bash's `ln -s` COPIES the file unless told to make a native symlink (measured 2026-11-24
    # on akiendell, ticket b0931d04a912): the copy sat in the scratch bin, so superclaude.py ran from
    # there, looked for scripts/memory_link.py beside itself, and tooth (2)'s resolve() check could
    # not hold. Elsewhere the variable is inert.
    env["MSYS"] = "winsymlinks:nativestrict"
    for k in ("CAIRN_SUDO_PW", "SUDO_ASKPASS", "CAIRN_FLOOR_FINDINGS", "CAIRN_CLASS_ROOT"):
        env.pop(k, None)
    return env


def test_every_linked_class_verb_is_100755_in_git() -> None:
    got = subprocess.run(["git", "ls-files", "-s", "--", *GLOBS], cwd=ROOT, capture_output=True,
                         text=True, timeout=60)
    rows = [line.split(None, 3) for line in got.stdout.splitlines() if line.strip()]
    wrong = sorted(f"{r[-1]} {r[0]}" for r in rows if r[0] != "100755")
    sc = [r for r in rows if r[-1].endswith("cairn/devices/cc/superclaude.py")]
    check("test_every_linked_class_verb_is_100755_in_git",
          got.returncode == 0 and len(rows) > 1 and bool(sc) and not wrong,
          f"rc={got.returncode} files={len(rows)} superclaude_listed={bool(sc)} not_100755={wrong}")


def test_superclaude_launches_over_a_scratch_box() -> None:
    home = _scratch()
    (home / "devices" / "cairn" / "0").mkdir(parents=True)
    r = subprocess.run([*bash_script_argv(CAIRN), "superclaude", "--dry-run"], env=_env(home),
                       capture_output=True, text=True, timeout=300, cwd="/", stdin=subprocess.DEVNULL)
    at = home / "devices" / "superclaude" / "0" / "bin" / "superclaude"
    linked = at.exists() and at.resolve() == SUPERCLAUDE.resolve()
    check("test_superclaude_launches_over_a_scratch_box", r.returncode == 0 and linked,
          f"rc={r.returncode} linked_to_py={linked} err={r.stderr[-300:]!r}")


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
