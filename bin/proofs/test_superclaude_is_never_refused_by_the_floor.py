"""bin/cairn's floor reports to superclaude instead of refusing it, and names the real cause.

Measured 2026-11-11 on akienasus, a fresh 24.04 box, `bin/cairn superclaude` exited 3 with
"IMPORT ROOT BROKEN … Repair: pip install -e" — over a venv that had no pip, because ensurepip
was absent. Three defects stacked in that one line, and Akien's ruling the same day sets what
the command must do instead: *"it should start by installing and launching you with a report
about what's not working so you can fix it."*

PROVES (teeth below):
  (1) superclaude is never refused: with the db floor failing, `bin/cairn superclaude --dry-run`
      exits 0, prints the launch, and carries the floor's finding into the report;
  (2) every other command is still refused by the same floor (exit 3) — the soft floor is
      superclaude's alone;
  (3) superclaude's own bin is wired even when cairn/0 already exists (the proxy that let the
      wiring walk be skipped on the fresh box);
  (4) a failed venv lay-down is refused with APPLY's measured cause, never with a re-verify's
      downstream symptom (the finding that was wiped);
  (5) a missing postgresql.service is reported as not installed, not as a sudoers problem.

Every tooth runs under a scratch HOME-shaped root, a scratch socket dir and a stand-in `sudo`,
so the live instance, venv, db and host are never touched.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
import sys
_REPO_FOR_ARGV = Path(__file__).resolve().parents[2]
if str(_REPO_FOR_ARGV) not in sys.path:
    sys.path.insert(0, str(_REPO_FOR_ARGV))
from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAIRN = ROOT / "bin" / "cairn"
UNCREATABLE = "/proc/cairn-no-such-dir/venv"

PROVES = {"superclaude-bare-box": {
    "1": "test_superclaude_launches_through_a_failing_floor",
    "2": "test_other_commands_are_still_refused",
    "3": "test_superclaude_is_wired_even_when_cairn0_exists",
    "4": "test_a_failed_lay_down_names_applys_cause",
    "5": "test_an_absent_postgres_is_named_not_installed",
}}

_failures: list[str] = []


def _scratch() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("superclaude-floor-")


def _fake_sudo(home: Path, *, unit_missing: bool) -> Path:
    """A sudo that refuses everything; optionally answering like a host with no postgres unit."""
    d = home / "fakebin"
    d.mkdir(exist_ok=True)
    msg = "Failed to start postgresql.service: Unit postgresql.service not found." if unit_missing \
        else "sudo: a password is required"
    (d / "sudo").write_text(f"#!/bin/sh\necho '{msg}' >&2\nexit 1\n")
    (d / "sudo").chmod(0o755)
    return d


def _env(home: Path, *, venv: str | None = None, unit_missing: bool = False) -> dict:
    env = dict(os.environ)
    env["PATH"] = f"{_fake_sudo(home, unit_missing=unit_missing)}:{env.get('PATH', '')}"
    env["CAIRN_INSTANCE_ROOT"] = str(home / "devices")
    env["CAIRN_VENV"] = venv or str(Path.home() / ".cairn" / "venv")
    (home / "nosock").mkdir(exist_ok=True)
    env["CAIRN_PG_SOCKET_DIR"] = str(home / "nosock")
    env["CAIRN_BOOT_LOG"] = str(home / "boot")
    for k in ("CAIRN_SUDO_PW", "SUDO_ASKPASS", "CAIRN_FLOOR_FINDINGS"):
        env.pop(k, None)
    return env


def _run(args: list, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([*bash_script_argv(CAIRN), *args], env=env, capture_output=True, text=True,
                          timeout=300, cwd="/", stdin=subprocess.DEVNULL)


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail}"))
    if not ok:
        _failures.append(name)


def test_superclaude_launches_through_a_failing_floor() -> None:
    home = _scratch()
    r = _run(["superclaude", "--dry-run"], _env(home))
    check("test_superclaude_launches_through_a_failing_floor",
          r.returncode == 0 and "exec claude" in r.stdout and "CAIRN FLOOR" in r.stdout
          and "floor: db" in r.stdout,
          f"rc={r.returncode} out={r.stdout[-400:]!r} err={r.stderr[-400:]!r}")


def test_other_commands_are_still_refused() -> None:
    home = _scratch()
    (home / "devices" / "cairn" / "0").mkdir(parents=True)
    r = _run(["librarian", "show", "status"], _env(home))
    check("test_other_commands_are_still_refused",
          r.returncode == 3 and r.stderr.startswith("cairn: floor: db — ") and r.stdout == "",
          f"rc={r.returncode} err={r.stderr[-300:]!r}")


def test_superclaude_is_wired_even_when_cairn0_exists() -> None:
    home = _scratch()
    (home / "devices" / "cairn" / "0").mkdir(parents=True)
    r = _run(["superclaude", "--dry-run"], _env(home))
    sc = home / "devices" / "superclaude" / "0" / "bin" / "superclaude"
    check("test_superclaude_is_wired_even_when_cairn0_exists",
          r.returncode == 0 and sc.exists() and "no such device" not in r.stderr,
          f"rc={r.returncode} wired={sc.exists()} err={r.stderr[-300:]!r}")


def test_a_failed_lay_down_names_applys_cause() -> None:
    home = _scratch()
    assert not Path(UNCREATABLE).exists(), f"{UNCREATABLE} exists — this tooth would be vacuous"
    r = _run(["librarian", "show", "status"], _env(home, venv=UNCREATABLE))
    check("test_a_failed_lay_down_names_applys_cause",
          r.returncode == 3 and "floor: venv" in r.stderr and "VENV CREATE FAILED" in r.stderr,
          f"rc={r.returncode} err={r.stderr[-500:]!r}")


def test_an_absent_postgres_is_named_not_installed() -> None:
    home = _scratch()
    (home / "devices" / "cairn" / "0").mkdir(parents=True)
    r = _run(["librarian", "show", "status"], _env(home, unit_missing=True))
    check("test_an_absent_postgres_is_named_not_installed",
          r.returncode == 3 and "NOT INSTALLED" in r.stderr and "apt-get install -y postgresql" in r.stderr
          and "sudoers" not in r.stderr,
          f"rc={r.returncode} err={r.stderr[-400:]!r}")


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
