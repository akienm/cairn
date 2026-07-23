"""Proof for cairn-command — the user-facing dispatcher: resolve a name, hand off, stay dumb.

Teeth a hollow dispatcher could not pass:

  - ARGS VERBATIM. ``cairn <name> a 'b c' d`` reaches ``bin/cmd/<name>`` with its argv
    intact — including an argument that contains a space (not re-split). A hollow build
    that mangled or re-split args trips this.
  - EXIT CODE PROPAGATED. The subcommand's exit code IS the dispatcher's exit code (a
    non-zero passes through). A hollow build that swallowed it (the ``set -e`` bug this
    proof was written against) trips this.
  - UNKNOWN NAME FAILS LOUD. An unresolved name exits non-zero with a legible message —
    never a silent no-op (CP1).
  - NO WRAPPER NOISE. On the success path the dispatcher adds NOTHING to stdout — the
    subcommand's output is exactly what the caller sees (it is a pass-through, not a
    wrapper).

Uses the ``CAIRN_CMD_DIR`` override to point at a temp stub tree, so the proof never
touches the real bin/cmd/. Self-cleaning.

    python3 bin/proofs/test_cairn_command.py     # exit 0 = green
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

_DISPATCHER = Path(__file__).resolve().parents[1] / "cairn"     # bin/proofs -> bin -> bin/cairn


def _stub(cmd_dir: str, name: str, body: str) -> None:
    path = os.path.join(cmd_dir, name)
    with open(path, "w") as f:
        f.write("#!/usr/bin/env bash\n" + body + "\n")
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _run(cmd_dir: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CAIRN_CMD_DIR": cmd_dir}
    return subprocess.run([str(_DISPATCHER), *args], capture_output=True, text=True, env=env)


def test_args_reach_the_subcommand_verbatim():
    with tempfile.TemporaryDirectory() as d:
        _stub(d, "echoer", 'for a in "$@"; do echo "arg:$a"; done')
        r = _run(d, "echoer", "a", "b c", "d")
        lines = r.stdout.strip().splitlines()
        assert lines == ["arg:a", "arg:b c", "arg:d"], f"argv not intact: {lines!r}"
        assert r.returncode == 0


def test_exit_code_is_propagated():
    with tempfile.TemporaryDirectory() as d:
        _stub(d, "faily", "exit 3")
        r = _run(d, "faily")
        assert r.returncode == 3, f"the subcommand's exit 3 must pass through, got {r.returncode}"


def test_unknown_name_fails_loud():
    with tempfile.TemporaryDirectory() as d:
        r = _run(d, "no-such-verb")
        assert r.returncode != 0, "an unknown command must fail non-zero, never a silent no-op"
        assert "no such command" in r.stderr.lower(), f"the failure must be legible: {r.stderr!r}"


def test_no_wrapper_noise_on_the_success_path():
    with tempfile.TemporaryDirectory() as d:
        _stub(d, "quiet", 'echo "ONLY-THIS"')
        r = _run(d, "quiet")
        assert r.stdout == "ONLY-THIS\n", f"the dispatcher added output of its own: {r.stdout!r}"


def _main() -> int:
    checks = [
        test_args_reach_the_subcommand_verbatim,
        test_exit_code_is_propagated,
        test_unknown_name_fails_loud,
        test_no_wrapper_noise_on_the_success_path,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — cairn-command: the dispatcher resolves a name to bin/cmd/<name>, passes argv "
          "verbatim, propagates the exit code, fails loud on an unknown name, and adds no output "
          "of its own (a dumb runner, Law 6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
