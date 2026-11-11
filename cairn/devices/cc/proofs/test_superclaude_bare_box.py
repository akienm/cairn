#!/usr/bin/env python3
"""Proof that superclaude on a bare box installs what it must, asks for sudo once, and launches.

Akien, 2026-11-11, on akienasus (a fresh 24.04 box): *"When i run cairn superclaude on a brnd
new box ... I should watch it automatically install everything and launch you"*; *"if claude is
not installed, it should be"*; *"it should start by installing and launching you with a report
about what's not working so you can fix it. this includes asking for the sudo pw so you can set
up everything. i suggest getting the pw, and putting it in an env var that goes away when the
session ends"*.

THE TEETH READ A DRY RUN, NOT A LAUNCH (same reason as test_superclaude_sets_cairn_user.py: a
real launch starts the ground loop and consumes live restart flags). `sudo` is a stand-in on
PATH so no tooth can touch the host: it refuses `-n`, and accepts `-S` only for the sentinel.

Teeth (PROVES below):
  (1) the askpass helper serves the held password and exits 1, printing nothing, with none held;
  (2) a held, sudo-accepted password rides as `sudo -A` guidance in the report, and its value
      appears neither in the launch line nor in the flight recorder;
  (3) with no claude on PATH or in ~/.local/bin, a dry run says it would install from the
      installer and still prints the launch;
  (4) with no sudo password and no tty, the launch neither hangs nor asks, and a report says
      sudo is not available to the session.
Hollow: before 2026-11-11 superclaude had no askpass, no install step and no sudo line, so
1-4 red.

    bin/cairn test cairn/devices/cc/proofs/test_superclaude_bare_box.py
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
_ASKPASS = _REPO / "cairn" / "devices" / "cc" / "scripts" / "sudo_askpass"

PROVES = {"superclaude-bare-box": {
    "1": "test_askpass_serves_only_what_is_held",
    "2": "test_a_held_password_is_guidance_never_text",
    "3": "test_an_absent_claude_would_be_installed",
    "4": "test_no_password_never_hangs_and_says_so",
}}

SENTINEL = "proof-sentinel-pw-7f3a"
FAILURES: list[str] = []
_SCRATCH = scratch_dir("cairn-proof-bare-box-")
_BOOT_LOG = _SCRATCH / "boot"

# The stand-in sudo: `-n` is always refused (no passwordless sudo), `-S` accepts exactly the
# sentinel on stdin, and anything else is refused. It never runs the command it is given.
_FAKE_BIN = _SCRATCH / "fakebin"
_FAKE_BIN.mkdir()
(_FAKE_BIN / "sudo").write_text(
    "#!/bin/sh\n"
    'for a in "$@"; do [ "$a" = "-n" ] && exit 1; done\n'
    'for a in "$@"; do if [ "$a" = "-S" ]; then IFS= read -r pw; '
    f'[ "$pw" = "{SENTINEL}" ] && exit 0; exit 1; fi; done\n'
    "exit 1\n")
(_FAKE_BIN / "sudo").chmod(0o755)


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _dry_run(extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PATH"] = f"{_FAKE_BIN}:{env.get('PATH', '')}"
    env["CAIRN_BOOT_LOG"] = str(_BOOT_LOG)
    env.pop("CAIRN_SUDO_PW", None)
    env.pop("SUDO_ASKPASS", None)
    # A carried floor finding forces a report, so the sudo line has something to ride beside.
    env["CAIRN_FLOOR_FINDINGS"] = "cairn: floor: db — synthetic finding for the bare-box proof\n"
    env.update(extra or {})
    return subprocess.run([str(_LAUNCHER), "--dry-run"], env=env, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, timeout=120, cwd=str(_REPO))


def test_askpass_serves_only_what_is_held() -> None:
    env = {k: v for k, v in os.environ.items() if k != "CAIRN_SUDO_PW"}
    held = subprocess.run([str(_ASKPASS)], env={**env, "CAIRN_SUDO_PW": SENTINEL},
                          capture_output=True, text=True)
    none = subprocess.run([str(_ASKPASS)], env=env, capture_output=True, text=True)
    check("test_askpass_serves_only_what_is_held",
          held.returncode == 0 and held.stdout == SENTINEL + "\n"
          and none.returncode == 1 and none.stdout == "",
          f"held rc={held.returncode} none rc={none.returncode} none out={none.stdout!r}")


def test_a_held_password_is_guidance_never_text() -> None:
    r = _dry_run({"CAIRN_SUDO_PW": SENTINEL})
    log = _BOOT_LOG.read_text() if _BOOT_LOG.exists() else ""
    check("test_a_held_password_is_guidance_never_text",
          r.returncode == 0 and "sudo -A" in r.stdout and str(_ASKPASS) in r.stdout
          and SENTINEL not in r.stdout and SENTINEL not in r.stderr and SENTINEL not in log
          and "password held for session" in log,
          f"rc={r.returncode} guidance={'sudo -A' in r.stdout} leaked_out={SENTINEL in r.stdout} "
          f"leaked_log={SENTINEL in log}")


def test_an_absent_claude_would_be_installed() -> None:
    r = _dry_run({"CLAUDE_BIN": "cairn-proof-no-such-claude",
                  "CAIRN_CLAUDE_INSTALLER": "file:///proof/installer.sh"})
    check("test_an_absent_claude_would_be_installed",
          r.returncode == 0
          and "would install it from file:///proof/installer.sh" in r.stdout
          and "exec cairn-proof-no-such-claude" in r.stdout,
          f"rc={r.returncode} out={r.stdout[-300:]!r}")


def test_no_password_never_hangs_and_says_so() -> None:
    try:
        r = _dry_run()
    except subprocess.TimeoutExpired:
        check("test_no_password_never_hangs_and_says_so", False, "the launch hung waiting on sudo")
        return
    check("test_no_password_never_hangs_and_says_so",
          r.returncode == 0 and "sudo: NOT available to this session" in r.stdout
          and "sudo password for" not in r.stderr,
          f"rc={r.returncode} stderr={r.stderr[-200:]!r}")


def main() -> int:
    for tooth in (test_askpass_serves_only_what_is_held, test_a_held_password_is_guidance_never_text,
                  test_an_absent_claude_would_be_installed, test_no_password_never_hangs_and_says_so):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
