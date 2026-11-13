"""Proof for ticket b3f999c452a1 — logtrim trims where flock is absent and never takes its caller down.

Measured 2026-11-13 on Windows: test_trim_keeps_the_newest_lines in test_logger_for_bash.py reds
with "expected exactly 10 lines after trim, got 201". Git Bash ships no flock(1); logtrim ran
``flock -x -w 5 9 || exit 0``, so on a host without flock the cut never happened, and ``exit 0``
inside a redirected brace group exits the CALLER's shell, not a subshell.

Both teeth red on Linux against the unedited bin/logger_for_bash: a shell function named flock
shadows the real one, returning 127 (what a missing flock returns) or 1 (what a timed-out flock
returns). Neither tooth spawns anything but bash.

    python <this file>
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOGGER = REPO / "bin" / "logger_for_bash"
BASH = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"

PROVES = {
    "b3f999c452a1": {
        "1": "logtrim_cuts_to_the_newest_lines_when_flock_is_missing",
        "2": "a_timed_out_flock_leaves_the_caller_alive_and_the_file_whole",
    },
}


def _run(fake_flock: str, body: str, loglen: str = "10"):
    with tempfile.TemporaryDirectory() as d:
        target = os.path.join(d, "bash")
        env = {k: v for k, v in os.environ.items()
               if k not in ("CAIRN_LOGTARGET", "logtarget", "CAIRN_LOGLEN", "loglen")}
        env.update(CAIRN_LOGTARGET=target, CAIRN_LOGLEN=loglen, CAIRN_LB_TRACE_ROOT=d,
                   PYTHONPATH=str(REPO))
        script = f'source "{LOGGER}"\nflock() {{ {fake_flock}; }}\n{body}\n'
        r = subprocess.run([BASH, "-c", script], capture_output=True, text=True, env=env)
        text = Path(target).read_text(encoding="utf-8", errors="replace") if os.path.exists(target) else ""
        return r, text.strip().splitlines()


def logtrim_cuts_to_the_newest_lines_when_flock_is_missing():
    r, lines = _run("return 127",
                    'for i in $(seq 1 200); do lognote "entry-$i"; done; logtrim; echo SURVIVED')
    assert "SURVIVED" in r.stdout, f"the caller died: {r.stdout!r} {r.stderr!r}"
    assert len(lines) == 10, f"expected 10 lines after trim with flock missing, got {len(lines)}"
    assert "entry-200" in lines[-2] or "entry-200" in lines[-1], f"the newest entry was cut: {lines[-3:]}"


def a_timed_out_flock_leaves_the_caller_alive_and_the_file_whole():
    r, lines = _run("return 1",
                    'for i in $(seq 1 200); do lognote "entry-$i"; done; logtrim; echo SURVIVED')
    assert "SURVIVED" in r.stdout, f"a flock timeout took the caller's shell down: {r.stdout!r} {r.stderr!r}"
    assert len([ln for ln in lines if "entry-" in ln]) == 200, \
        f"a timed-out trim must not cut: {len(lines)} lines"


TEETH = [logtrim_cuts_to_the_newest_lines_when_flock_is_missing,
         a_timed_out_flock_leaves_the_caller_alive_and_the_file_whole]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {type(e).__name__}: {e}  [{t.__name__}]")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
