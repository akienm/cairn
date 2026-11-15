#!/usr/bin/env python3
"""Proof that superclaude on Windows never asks for, tests, or holds a sudo password.

Measured 2026-11-14 on akienlivingroom (a fresh Windows 11 box, elevated PowerShell): `bin/cairn
superclaude` asked for the sudo password and refused the right one, so the launch was dead. The
`sudo` on a Windows PATH is Windows' sudo.exe: UAC-gated, no password, and it rejects the Unix
flags outright (`sudo -n true` -> "error: unexpected argument '-n' found", rc=2; same for -S).
Every check the launcher made with it failed, so every password read as refused. On Windows
elevation belongs to the launching terminal, and `net session` succeeds only when it is elevated.

THE TEETH READ A DRY RUN (as test_superclaude_bare_box.py does; a real launch starts the ground
loop). The platform is FAKED so this runs on any host: a stand-in `uname` says MINGW64, a
stand-in `sudo` behaves like sudo.exe and records every call, and a stand-in `net` answers
`net session` with NET_RC. A carried floor finding forces the report the sudo line rides in.

Teeth (PROVES below):
  (1) elevated (net session rc 0): the report says the session is ELEVATED, not that sudo
      "needs a password", and the boot log records "windows, elevated";
  (2) not elevated (net session rc 2): the report says sudo is NOT available, names UAC, and does
      not say it "needs a password";
  (3) with CAIRN_SUDO_PW set, sudo is never called at all, no `sudo -A` guidance is given, and
      the value appears nowhere in the output.
Hollow: before this ticket the launcher ran `sudo -n` and `sudo -S` on Windows and reported
"it needs a password and none was given", so 1-3 are red on it (measured: red 3/3 at 3bab43c08's
launcher, green 3/3 with the fix).

    bin/cairn test cairn/devices/cc/proofs/test_superclaude_never_asks_a_sudo_password_on_windows.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

_LAUNCHER = _REPO / "cairn" / "devices" / "cc" / "superclaude"

PROVES = {"superclaude-never-asks-a-sudo-password-on-windows": {
    "1": "test_an_elevated_windows_launch_says_so",
    "2": "test_an_unelevated_windows_launch_names_uac_not_a_password",
    "3": "test_a_held_password_is_never_used_on_windows",
}}

SENTINEL = "proof-sentinel-pw-windows-41c2"
FAILURES: list[str] = []
_SCRATCH = scratch_dir("cairn-proof-sc-windows-sudo-")
_BOOT_LOG = _SCRATCH / "boot"
_SUDO_CALLS = _SCRATCH / "sudo_calls"

_FAKE_BIN = _SCRATCH / "fakebin"
_FAKE_BIN.mkdir()
_STUBS = {
    # Git Bash's own answer: the launcher's one platform read.
    "uname": '#!/bin/sh\ncase "$1" in -s|"") echo MINGW64_NT-10.0-26100 ;; '
             '*) exec /usr/bin/uname "$@" ;; esac\n',
    # sudo.exe: rejects the Unix flags (measured wording), and logs every call.
    "sudo": f'#!/bin/sh\necho "$*" >> "{_SUDO_CALLS.as_posix()}"\n'
            'for a in "$@"; do case "$a" in -*) '
            'echo "error: unexpected argument \'$a\' found" >&2; exit 2 ;; esac; done\nexit 0\n',
    # `net session`: 0 when elevated, 2 when not (Windows' own exit for access denied).
    "net": '#!/bin/sh\nexit "${NET_RC:-2}"\n',
}
for _name, _body in _STUBS.items():
    (_FAKE_BIN / _name).write_text(_body)
    (_FAKE_BIN / _name).chmod(0o755)


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _dry_run(extra: dict | None = None) -> subprocess.CompletedProcess:
    from cairn.tools.base.script_argv import bash_script_argv
    for f in (_BOOT_LOG, _SUDO_CALLS):
        f.unlink(missing_ok=True)
    env = dict(os.environ)
    env["PATH"] = f"{_FAKE_BIN}:{env.get('PATH', '')}"   # the bare-box proof's spelling, measured on both
    env["CAIRN_BOOT_LOG"] = str(_BOOT_LOG)
    env.pop("CAIRN_SUDO_PW", None)
    env.pop("SUDO_ASKPASS", None)
    env["CAIRN_FLOOR_FINDINGS"] = "cairn: floor: db — synthetic finding for the windows-sudo proof\n"
    env.update(extra or {})
    return subprocess.run([*bash_script_argv(_LAUNCHER), "--dry-run"], env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          stdin=subprocess.DEVNULL, timeout=120, cwd=str(_REPO))


def _log() -> str:
    return _BOOT_LOG.read_text(encoding="utf-8", errors="replace") if _BOOT_LOG.exists() else ""


def test_an_elevated_windows_launch_says_so() -> None:
    r = _dry_run({"NET_RC": "0"})
    check("test_an_elevated_windows_launch_says_so",
          r.returncode == 0 and "ELEVATED" in r.stdout and "needs a password" not in r.stdout
          and "windows, elevated" in _log(),
          f"rc={r.returncode} elevated={'ELEVATED' in r.stdout} "
          f"needs_pw={'needs a password' in r.stdout} log_ok={'windows, elevated' in _log()}")


def test_an_unelevated_windows_launch_names_uac_not_a_password() -> None:
    r = _dry_run({"NET_RC": "2"})
    check("test_an_unelevated_windows_launch_names_uac_not_a_password",
          r.returncode == 0 and "sudo: NOT available to this session" in r.stdout
          and "UAC" in r.stdout and "needs a password" not in r.stdout,
          f"rc={r.returncode} uac={'UAC' in r.stdout} needs_pw={'needs a password' in r.stdout}")


def test_a_held_password_is_never_used_on_windows() -> None:
    r = _dry_run({"NET_RC": "0", "CAIRN_SUDO_PW": SENTINEL})
    calls = _SUDO_CALLS.read_text() if _SUDO_CALLS.exists() else ""
    check("test_a_held_password_is_never_used_on_windows",
          r.returncode == 0 and calls == "" and "sudo -A" not in r.stdout
          and SENTINEL not in r.stdout and SENTINEL not in r.stderr and SENTINEL not in _log(),
          f"rc={r.returncode} sudo_calls={calls.split(chr(10))[:3]!r} "
          f"guidance={'sudo -A' in r.stdout} leaked={SENTINEL in r.stdout + r.stderr + _log()}")


def main() -> int:
    for tooth in (test_an_elevated_windows_launch_says_so,
                  test_an_unelevated_windows_launch_names_uac_not_a_password,
                  test_a_held_password_is_never_used_on_windows):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
