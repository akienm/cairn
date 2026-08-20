"""Proof for the-beater-holds-the-claim: the process beating is the process holding the claim.

Teeth a hollow build could not pass:

  - AN INDUCED MISMATCH IS CAUGHT. A lock held by one pid and a liveness record naming a
    different pid produces MISMATCH, naming both. A build that always reports MATCH fails.
  - A MATCH IS GREEN. When the holder IS the beater, the outcome is MATCH. Proves the
    comparator works in both directions.
  - INABILITY IS NEVER GREEN. When the lock file is absent or /proc/locks cannot name the
    holder, the outcome is UNABLE — never MATCH.
  - THE BEATER PID IS READ FROM LIVENESS, NOT FROM os.getpid(). Verified by constructing
    a liveness record naming a pid that is not this process.

    python3 cairn/devices/ground_loop/proofs/test_beater_holds_claim.py   # exit 0 = green
"""

from __future__ import annotations

import fcntl
import json
import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.ground_loop.probes.does_the_beater_hold_the_claim import (
    check, lock_holder_pid, beater_pid,
)
from cairn.devices.ground_loop.guard import LOCK_NAME
from cairn.devices.ground_loop.liveness import RECORD_NAME


def _make_home(d: str, lock_pid: int | None, liveness_pid: int | None) -> Path:
    """Build an isolated instance root with a held lock and a liveness record."""
    home = Path(d) / "devices" / "ground_loop" / "0"
    home.mkdir(parents=True)

    if liveness_pid is not None:
        record = {"last_run": "2026-08-20T12:00:00", "state": {}, "pid": liveness_pid}
        (home / RECORD_NAME).write_text(json.dumps(record))

    if lock_pid is not None:
        lock_path = home / LOCK_NAME
        fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return home, fd
    return home, None


def test_induced_mismatch_is_caught():
    """The ticket's core tooth: holder != beater → MISMATCH naming both pids."""
    with tempfile.TemporaryDirectory() as d:
        my_pid = os.getpid()
        other_pid = my_pid + 99999
        home, fd = _make_home(d, lock_pid=my_pid, liveness_pid=other_pid)
        try:
            result = check(home)
            assert result["outcome"] == "MISMATCH", (
                f"holder pid {my_pid} != beater pid {other_pid} must be MISMATCH, "
                f"got {result}")
            assert result["holder_pid"] == my_pid
            assert result["beater_pid"] == other_pid
        finally:
            if fd is not None:
                os.close(fd)


def test_match_is_green():
    """When the holder IS the beater, outcome is MATCH."""
    with tempfile.TemporaryDirectory() as d:
        my_pid = os.getpid()
        home, fd = _make_home(d, lock_pid=my_pid, liveness_pid=my_pid)
        try:
            result = check(home)
            assert result["outcome"] == "MATCH", (
                f"same pid {my_pid} on both sides must be MATCH, got {result}")
            assert result["holder_pid"] == my_pid
            assert result["beater_pid"] == my_pid
        finally:
            if fd is not None:
                os.close(fd)


def test_no_lock_file_is_unable():
    """A missing lock file cannot be green — it must be UNABLE."""
    with tempfile.TemporaryDirectory() as d:
        home, _ = _make_home(d, lock_pid=None, liveness_pid=os.getpid())
        result = check(home)
        assert result["outcome"] == "UNABLE", (
            f"no lock file must be UNABLE, got {result}")


def test_no_liveness_is_unable():
    """A missing liveness record cannot be green — it must be UNABLE."""
    with tempfile.TemporaryDirectory() as d:
        home, fd = _make_home(d, lock_pid=os.getpid(), liveness_pid=None)
        try:
            result = check(home)
            assert result["outcome"] == "UNABLE", (
                f"no liveness record must be UNABLE, got {result}")
        finally:
            if fd is not None:
                os.close(fd)


def test_beater_pid_reads_from_liveness_not_getpid():
    """The beater pid comes from the liveness record, not from this process."""
    with tempfile.TemporaryDirectory() as d:
        planted_pid = 12345
        home, _ = _make_home(d, lock_pid=None, liveness_pid=planted_pid)
        pid = beater_pid(home)
        assert pid == planted_pid, (
            f"beater_pid must read from liveness.json ({planted_pid}), "
            f"not os.getpid() ({os.getpid()}), got {pid}")


def _main() -> int:
    checks = [
        test_induced_mismatch_is_caught,
        test_match_is_green,
        test_no_lock_file_is_unable,
        test_no_liveness_is_unable,
        test_beater_pid_reads_from_liveness_not_getpid,
    ]
    for c in checks:
        c()
        print(f"  PASS  {c.__name__}")
    print(f"green — the-beater-holds-the-claim ({len(checks)} teeth): induced mismatch "
          "caught naming both pids, match is green, inability is never green, beater pid "
          "read from liveness not getpid")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
