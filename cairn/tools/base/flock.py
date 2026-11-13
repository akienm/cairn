"""One advisory file lock that stands for ``fcntl.flock`` on every host.

``fcntl`` does not exist on Windows; ``msvcrt.locking`` does. Callers hold a descriptor (an int or
anything with ``fileno()``) and take or free an exclusive lock on it:

    flock.lock(fd)                   # block until held
    flock.lock(fd, block=False)      # raise BlockingIOError if another descriptor holds it
    flock.unlock(fd)

Both hosts lock the file's first byte, so two descriptors on one file contend, in one process or two.
The platform module is imported inside the call, never at module top.
"""

from __future__ import annotations

import os
import time


def _fd(f) -> int:
    return f if isinstance(f, int) else f.fileno()


def lock(f, exclusive: bool = True, block: bool = True) -> None:
    fd = _fd(f)
    if os.name != "nt":
        import fcntl
        how = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        if not block:
            how |= fcntl.LOCK_NB
        fcntl.flock(fd, how)
        return
    import msvcrt
    while True:
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return
        except OSError as e:
            if not block:
                raise BlockingIOError(*e.args) from e
            time.sleep(0.05)


def unlock(f) -> None:
    fd = _fd(f)
    if os.name != "nt":
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)
        return
    import msvcrt
    os.lseek(fd, 0, os.SEEK_SET)
    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
