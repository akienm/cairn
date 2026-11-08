"""singleton — one process holds a lock file; anyone can ask whether it is held (ticket 6208d0a27d6e).

A TOOL, so any component can ask "is that singleton up?" without importing the device that
holds it (RULE 1). Its first user is the ground loop: the loop claims its run.lock for its
whole life, and the base shim asks ``held`` before it spawns one (Akien, Q#53: "Is it up?"
is answered by the lock, never by the age of a record — a slow loop still holds its lock).

WHY flock AND NOT O_EXCL: the kernel releases a flock when its holder dies — clean exit,
SIGKILL, power event, all the same. A bare O_EXCL claim file would survive its dead creator
as a stale claim, and breaking it would need a staleness protocol, which is exactly what this
tool exists to not have. A leftover lock file is inert: only a held lock means anything.

THE PROBE TAKES A SHARED LOCK FOR AN INSTANT. ``held`` asks with LOCK_SH|LOCK_NB and drops
it at once; a claimant that lands inside that instant would see its LOCK_EX refused. So a
claim retries a few times over ~0.1 s before it refuses — a probe can never make a real
starter lose, and a real holder still refuses every newcomer (it never lets go).

On Windows, msvcrt's 1-byte lock plays flock (held by the fd, dies with the process); it
has no shared mode, so the probe takes and drops the same exclusive byte.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:
    import fcntl

_RETRIES = 4
_RETRY_GAP_S = 0.025


class ClaimRefused(RuntimeError):
    """Another process holds the lock — the loser's LOUD refusal (CP1). It says nothing about
    WHO holds it: that is the holder's own record to say."""


@dataclass
class Claim:
    """The winner's held lock: an open fd the kernel keeps locked until this process exits or
    dies. Closing the fd IS releasing it."""

    fd: int
    path: Path

    def release(self) -> None:
        os.close(self.fd)


def _try(fd: int, exclusive: bool) -> bool:
    try:
        if os.name == "nt":
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _drop(fd: int) -> None:
    try:
        if os.name == "nt":
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass


def claim(path) -> Claim:
    """Take the lock at ``path`` (the file is created if absent; its parent must exist). Win or
    refuse loudly; never block beyond the probe-race retries."""
    path = Path(path)
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
    for attempt in range(_RETRIES):
        if _try(fd, exclusive=True):
            return Claim(fd=fd, path=path)
        if attempt < _RETRIES - 1:
            time.sleep(_RETRY_GAP_S)
    os.close(fd)
    raise ClaimRefused(f"the lock at {path} is already held — its singleton is running "
                       "(or holding its lock while slow); this claimant must not become a second one")


def held(path) -> bool:
    """Is the lock at ``path`` held by anyone? An absent file is False, and asking creates
    nothing. Never raises."""
    path = Path(path)
    try:
        fd = os.open(str(path), os.O_RDWR if os.name == "nt" else os.O_RDONLY)
    except OSError:
        return False
    try:
        if _try(fd, exclusive=os.name == "nt"):
            _drop(fd)
            return False
        return True
    finally:
        os.close(fd)
