"""cairn/logs_sweep.py — the cairn device forgets the logs tree past 30 days (ticket ff881672ac57).

WHY HERE. ``address.log_path`` gave every thing's logs ONE root so that one deletion could
forget them without crossing anybody's gate (Law 6, agreed 2026-08-18), and nothing ever
deleted there: 36719 of the 228531 files under ``~/.cairn/logs`` were past 30 days on
2026-10-02. Akien placed the deletion in the cairn device's sleep cycle (open-9d9c0b1ac3a9:
"cairn device's sleep cycle should be where that cleanup happens"), so it lives inside the
cairn device and ``device.py`` runs it when a rotation closes (RULE 1: one component).

WHAT IT TOUCHES. Only what sits below ``<instance root>/logs``. Every entry is judged by its
OWN ``lstat``: a symlink is removed as itself and its target is never read or touched, and a
link to a directory is never descended. Directories left empty below the root go; the root
itself never does. A file that vanishes under the walk, or a directory a writer fills between
the listdir and the rmdir, was a writer racing it and is skipped;
any other OSError is raised, loud (Law 7).
"""

from __future__ import annotations

import errno
import os
import time

from cairn.tools.base.address import resolve

DAY = 86400


def sweep_logs(older_than_days: int = 30, roots: dict | None = None, now: float | None = None) -> dict:
    """Delete every entry under the logs root whose own mtime is older than the cutoff, then the
    directories left empty below the root. Returns {'deleted', 'bytes', 'kept'}."""
    root = resolve("instance/logs", roots)
    counts = {"deleted": 0, "bytes": 0, "kept": 0}
    if not root.is_dir():
        return counts
    cutoff = (time.time() if now is None else now) - older_than_days * DAY
    for here, dirs, files in os.walk(root, topdown=False, followlinks=False):
        links = [d for d in dirs if os.path.islink(os.path.join(here, d))]
        for name in files + links:
            path = os.path.join(here, name)
            try:
                st = os.lstat(path)
                if st.st_mtime < cutoff:
                    os.unlink(path)
                    counts["deleted"] += 1
                    counts["bytes"] += st.st_size
                else:
                    counts["kept"] += 1
            except FileNotFoundError:
                continue
        if here == str(root):
            continue
        try:
            if not os.listdir(here):
                os.rmdir(here)
        except FileNotFoundError:
            continue
        except OSError as exc:
            if exc.errno != errno.ENOTEMPTY:   # a writer filled it after the listdir
                raise
    return counts
