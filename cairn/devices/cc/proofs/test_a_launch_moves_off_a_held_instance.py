#!/usr/bin/env python3
"""Proof for ticket ae4d581be071 — a restart from one session never targets another session's loop.

MEASURED 2026-10-06 by the peer akiendelllinux_cc_0: two superclaude loops (441666, 512525) both
launched at instance 0, so they shared one loop.pid and one restart-flag set, and
`cairn cc restart now` from one would have killed the other's CC with nothing to relaunch it.
Akien answered open-62a7f29771e6: "b, next free instance" — a launch whose instance is held moves
itself to the next free one, as `cairn cc restart spawn` already does. Distinct instances have
distinct flags homes, so restart (which reads SUPERCLAUDE_FLAGS_HOME) reaches only its own loop.

THE TEETH READ DRY RUNS under a scratch HOME and TMUX_TMPDIR, never a launch (the reason is in
test_superclaude_sets_cairn_user.py: a real launch starts the ground loop and consumes live
restart flags). A held instance is staged as a loop.pid naming this proof's own live child, or
a tmux session on the scratch tmux socket.

  1. test_a_held_default_moves_to_the_next_instance: loop.pid at 0 live -> session _cc_1,
     CAIRN_USER=cc1, flags home .../superclaude/1, and the move is named;
  2. test_a_dead_pid_does_not_hold: loop.pid at 0 dead -> stays at 0, and the dry run says so
     ("# instance: asked 0, launching 0");
  3. test_two_held_moves_to_the_third: 0 and 1 live -> 2;
  4. test_a_held_word_keeps_its_name: --name builder held -> builder_1;
  5. test_a_tmux_session_holds_like_a_loop: tmux session cairn_cc_0 -> 1.

    python3 cairn/devices/cc/proofs/test_a_launch_moves_off_a_held_instance.py
"""
from __future__ import annotations

import os
import shutil
import platform
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
_LAUNCHER = _REPO / "cairn" / "devices" / "cc" / "superclaude"

PROVES = {"ae4d581be071": {
    "1": "test_a_held_default_moves_to_the_next_instance",
    "2": "test_a_dead_pid_does_not_hold",
    "3": "test_two_held_moves_to_the_third",
    "4": "test_a_held_word_keeps_its_name",
    "5": "test_a_tmux_session_holds_like_a_loop",
}}

_HOST = platform.node().split(".")[0].lower()


def _world() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("testing-ae4d581be071-held-")


def _hold(home: Path, instance: str, pid: int) -> None:
    d = home / ".cairn" / "launchers" / "superclaude" / instance
    d.mkdir(parents=True, exist_ok=True)
    (d / "loop.pid").write_text(f"{pid}\n")


def _env(home: Path) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in ("CAIRN_USER", "TMUX", "SUPERCLAUDE_INNER", "SUPERCLAUDE_INNER_HOME")}
    env.update({"HOME": str(home), "TMUX_TMPDIR": str(home), "CLAUDE_BIN": "true",
                "PYTHONPATH": str(_REPO)})
    return env


def _dry(home: Path, *args: str) -> dict:
    """What a dry run says: session (the --name claude gets), CAIRN_USER, flags home, moved."""
    r = subprocess.run([shutil.which("bash") or "bash", _LAUNCHER.as_posix(), "--dry-run",
                        "--no-preflight", *args],
                       capture_output=True, text=True, env=_env(home), timeout=60)
    out = {"raw": r.stdout + r.stderr, "moved": None, "session": None, "user": None, "flags": None,
           "instance": None}
    for line in r.stdout.splitlines():
        if line.startswith("# CAIRN_USER="):
            out["user"] = line.split("=", 1)[1]
        elif line.startswith("# flags home: "):
            out["flags"] = line.split(": ", 1)[1]
        elif line.startswith("# instance: "):
            out["instance"] = line.split(": ", 1)[1]
        elif line.startswith("# moved: "):
            out["moved"] = line.split(": ", 1)[1]
        elif line.startswith("exec "):
            parts = line.split()
            if "--name" in parts:
                out["session"] = parts[parts.index("--name") + 1]
    return out


def _alive() -> subprocess.Popen:
    return subprocess.Popen(["sleep", "300"], stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _dead_pid() -> int:
    p = subprocess.Popen(["true"])
    p.wait()
    return p.pid


def _at(got: dict, instance: str, home: Path) -> None:
    want_flags = str(home / ".cairn" / "launchers" / "superclaude" / instance)
    assert got["session"] == f"{_HOST}_cc_{instance}", f"session {got['session']!r}: {got['raw'][-600:]}"
    assert got["user"] == f"cc{instance}", f"CAIRN_USER {got['user']!r}"
    assert got["flags"] == want_flags, f"flags home {got['flags']!r}, want {want_flags}"


def test_a_held_default_moves_to_the_next_instance():
    home, held = _world(), _alive()
    try:
        _hold(home, "0", held.pid)
        got = _dry(home)
        _at(got, "1", home)
        assert got["moved"] and str(held.pid) in got["moved"], (
            f"the move does not name the live loop {held.pid}: {got['moved']!r}")
    finally:
        held.kill()


def test_a_dead_pid_does_not_hold():
    home = _world()
    _hold(home, "0", _dead_pid())
    got = _dry(home)
    _at(got, "0", home)
    assert got["instance"] == "asked 0, launching 0", (
        f"the dry run does not state the occupancy verdict: {got['instance']!r}")
    assert got["moved"] is None, f"a dead pid moved the launch: {got['moved']!r}"


def test_two_held_moves_to_the_third():
    home, a, b = _world(), _alive(), _alive()
    try:
        _hold(home, "0", a.pid)
        _hold(home, "1", b.pid)
        _at(_dry(home), "2", home)
    finally:
        a.kill()
        b.kill()


def test_a_held_word_keeps_its_name():
    home, held = _world(), _alive()
    try:
        _hold(home, "builder", held.pid)
        _at(_dry(home, "--name", "builder"), "builder_1", home)
    finally:
        held.kill()


def test_a_tmux_session_holds_like_a_loop():
    if not shutil.which("tmux"):
        raise AssertionError("tmux is not installed; this tooth needs it to stage the hold")
    home = _world()
    env = _env(home)
    subprocess.run(["tmux", "new-session", "-d", "-s", "cairn_cc_0", "sleep", "300"],
                   env=env, check=True, timeout=30)
    try:
        _at(_dry(home), "1", home)
    finally:
        subprocess.run(["tmux", "kill-server"], env=env, timeout=30)


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
