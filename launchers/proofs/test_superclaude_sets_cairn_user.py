#!/usr/bin/env python3
"""Proof that superclaude exports CAIRN_USER=cc<instance> to the session it launches (8c899e9ea338).

Akien, 2026-10-13: *"when we use cairn superclaude or cairn cc0 ... we also set the otherwise
unset variable CAIRN_USER= which can be librarian or cc0 or whatever. if CAIRN_USER is set,
then it's you."* The launcher exports it right after the session name is decided, overwriting
any inherited value, so everything the session runs can say which Claude it is.

THE TEETH READ A DRY RUN, NOT A LAUNCH. Measured 2026-10-13: a real launch (even with
CLAUDE_BIN faked) starts the ground loop and the web server through ``systemd-run --user``,
and its inner loop consumes a live COMMAND_RESTART flag at
~/.cairn/launchers/superclaude/<instance>/ — a proof must not restart a running session. The
dry run prints ``# CAIRN_USER=`` from ``printenv``, which sees only EXPORTED variables, so the
line is the environment the exec would hand claude, not a shell variable that never leaves.

Teeth, one per falsifier clause (PROVES below):
  (1) a default launch carries CAIRN_USER=cc0;
  (2) --instance=2 carries CAIRN_USER=cc2;
  (3) a parent environment carrying CAIRN_USER=zzz still yields cc0.
Hollow: today's superclaude reds 1-3.

And --name (Akien, 2026-10-28: *"cairn\\bin\\cairn superclaude --name builder"*), a word in
the instance slot, read off the same dry run:
  (4) --name builder and --name=builder both carry CAIRN_USER=ccbuilder and launch
      claude as <host>_cc_builder, remote control under the same name;
  (5) claude sees exactly one --name — the launcher's, never the operator's forwarded raw.

    bin/cairn test launchers/proofs/test_superclaude_sets_cairn_user.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_LAUNCHER = _REPO / "launchers" / "superclaude"

PROVES = {"8c899e9ea338": {
    "1": "test_a_default_launch_is_cc0",
    "2": "test_an_instance_names_its_cc",
    "3": "test_an_inherited_value_is_overwritten",
}, "superclaude-name": {
    "4": "test_a_name_fills_the_instance_slot",
    "5": "test_claude_gets_one_name",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _dry_run(*args: str, inherit: str | None = None) -> str:
    env = {k: v for k, v in os.environ.items() if k != "CAIRN_USER"}
    env.update({"CLAUDE_BIN": "true", "PYTHONPATH": str(_REPO)})
    if inherit is not None:
        env["CAIRN_USER"] = inherit
    r = subprocess.run([shutil.which("bash") or "bash", _LAUNCHER.as_posix(), "--dry-run", "--no-preflight", *args],
                       capture_output=True, text=True, env=env, timeout=60)
    return r.stdout


def _cairn_user(*args: str, inherit: str | None = None) -> str | None:
    """The CAIRN_USER a dry run reports, or None when the line is absent."""
    for line in _dry_run(*args, inherit=inherit).splitlines():
        if line.startswith("# CAIRN_USER="):
            return line.split("=", 1)[1]
    return None


def test_a_default_launch_is_cc0() -> None:
    got = _cairn_user()
    check("test_a_default_launch_is_cc0", got == "cc0", repr(got))


def test_an_instance_names_its_cc() -> None:
    got = _cairn_user("--instance=2")
    check("test_an_instance_names_its_cc", got == "cc2", repr(got))


def test_an_inherited_value_is_overwritten() -> None:
    got = _cairn_user(inherit="zzz")
    check("test_an_inherited_value_is_overwritten", got == "cc0", repr(got))


def _exec_argv(*args: str) -> list[str]:
    """The claude argv a dry run prints, after ``exec <bin>``."""
    import shlex
    for line in _dry_run(*args).splitlines():
        if line.startswith("exec "):
            return shlex.split(line)[2:]
    return []


def test_a_name_fills_the_instance_slot() -> None:
    import socket
    host = socket.gethostname().split(".")[0].lower()
    want = f"{host}_cc_builder"
    for form in (("--name", "builder"), ("--name=builder",)):
        argv = _exec_argv(*form)
        named = argv[argv.index("--name") + 1] if "--name" in argv else None
        remote = argv[argv.index("--remote-control") + 1] if "--remote-control" in argv else None
        user = _cairn_user(*form)
        check("test_a_name_fills_the_instance_slot",
              (named, remote, user) == (want, want, "ccbuilder"),
              f"{' '.join(form)}: name={named!r} remote={remote!r} CAIRN_USER={user!r}")


def test_claude_gets_one_name() -> None:
    argv = _exec_argv("--name", "builder")
    check("test_claude_gets_one_name", argv.count("--name") == 1 and "builder" not in argv,
          repr(argv))


def main() -> int:
    for tooth in (test_a_default_launch_is_cc0, test_an_instance_names_its_cc,
                  test_an_inherited_value_is_overwritten, test_a_name_fills_the_instance_slot,
                  test_claude_gets_one_name):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
