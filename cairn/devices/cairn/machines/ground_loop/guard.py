"""guard — the atomic single-start claim (ticket an-entry-point-starts-the-loop-only-once).

READ-THEN-ACT IS NOT ATOMIC. Two entry points can both read DEAD inside the same
5s window and both start a loop — the falsifier's expensive direction (every
callback fires twice). So starting is decided by ONE syscall, not by a read:
``claim_singleton`` takes ``fcntl.flock(LOCK_EX | LOCK_NB)`` on a stable lock
file in the loop's own device space, and exactly one claimant wins.

WHY flock AND NOT O_EXCL: the kernel releases a flock when its holder dies —
clean exit, SIGKILL, power event, all the same. A bare O_EXCL claim file would
survive its dead creator as a stale claim, and breaking it would need a second
staleness protocol — reopening at the break-the-claim step exactly the race
this module exists to close. flock has no stale state to break.

WHY A SEPARATE FILE AND NOT liveness.json: the record is rewritten atomically
every beat via ``os.replace``, which swaps the inode out from under any held
lock. The lock file (``run.lock``) is never replaced, so the winner's claim
rides one inode for the process's whole life.

The claim DECIDES; the record EXPLAINS. A losing claimant reads
``read_liveness`` to name what is running (pid, age — the owned answer, Law 6),
but its refusal never rests on that read: a loop alive-but-slow past the 5s
threshold still HOLDS ITS LOCK, so no second loop starts beside it.
"""

from __future__ import annotations

import fcntl
import os
from dataclasses import dataclass
from pathlib import Path

LOCK_NAME = "run.lock"


class ClaimRefused(RuntimeError):
    """Another process holds the singleton claim — the loser's LOUD refusal (CP1).

    Deliberately carries no verdict about WHO holds it: that is the record's to
    say (``read_liveness``), and the door that catches this reads it there."""


@dataclass
class SingletonClaim:
    """The winner's held claim: an open fd whose flock the kernel keeps until this
    process exits or dies. Hold the object for the process's whole life — closing
    the fd IS releasing the claim, so ``release`` exists for proofs, not for the
    runner (the runner's release is its death, by design: no unlock code path
    means no way to drop the claim while the loop still beats)."""

    fd: int
    path: Path

    def release(self) -> None:
        os.close(self.fd)


def claim_singleton(home: Path) -> SingletonClaim:
    """ONE atomic claim on the loop's own device space; win or refuse loudly, never block.

    The lock file is created if absent (its existence means nothing — only the
    held flock does, so a leftover file from a dead loop is inert, not stale)."""
    home.mkdir(parents=True, exist_ok=True)
    path = home / LOCK_NAME
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        raise ClaimRefused(
            f"the singleton claim at {path} is already held — a ground loop is running "
            "(or holding its lock while slow); this claimant must not become a second one"
        ) from None
    return SingletonClaim(fd=fd, path=path)
