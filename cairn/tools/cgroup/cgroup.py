"""cgroup — read a process's cgroup v2 path, once, for everyone who needs it.

THE ONE READER OF ``/proc/<pid>/cgroup`` IN THIS CORPUS. Nothing else may open that
file: three files had grown the same eight-line parse (the heartbeat's residency probe,
CC's memory-curve probe, and the superclaude memory-scope proof), which is Law 1's
defect — a settled answer re-derived — and it went unseen because the census that would
have caught it lived in a proof under a directory-scoped seal that the growth never
touched.

WHY A TOOL AND NOT A SHARED PROBE: the second consumer sits on a different device
(``cairn/devices/cc``) from the first (``cairn/devices/cairn``), and devices do not
import each other. A complete primitive with users rather than an owner is exactly a
tool (Law 6), and this is one: pure, stateless, no gate of its own to keep.
"""

from __future__ import annotations

from pathlib import Path


def cgroup_of(pid: int | str = "self") -> str | None:
    """The cgroup v2 path of ``pid``, or ``None`` when there is no unified line to read.

    ``None`` is a real answer and not an error: a v1-only host, a pid that exited between
    the listing and the read, and a container with no unified hierarchy all land here, and
    each is a fact about the world rather than a broken reader (Law 7 — the lack is named
    by the caller that reports it, not swallowed here into a plausible default)."""
    try:
        raw = Path(f"/proc/{pid}/cgroup").read_text()
    except OSError:
        return None
    return parse(raw)


def parse(raw: str) -> str | None:
    """The parse alone, over the file's text — so a proof can pin it without a live pid.

    The kernel appends ``" (deleted)"`` when the cgroup has been removed out from under a
    still-living process, which is exactly what a killed caller's scope looks like for the
    moment between the kill and the last exit. The path is still the identity; the marker
    is not part of it, and dropping it here keeps every downstream comparison from
    silently missing."""
    for line in raw.splitlines():
        if line.startswith("0::"):
            return line[3:].removesuffix(" (deleted)")
    return None
