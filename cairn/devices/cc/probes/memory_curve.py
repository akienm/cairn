"""PROBE — records the memory curve so it is a durable series, not a number
in Akien's visual memory.

Two readings per firing: (1) the scope's cgroup memory.current — the same number
the kernel gates MemoryHigh/MemoryMax on; (2) per-process RSS from /proc/self/statm
— what Akien was actually watching in the process monitor. Both in one series record,
same firing.

The probe rides the heartbeat: the ground loop fires CC's probes because CC is in the
rack. What this probe measures is CC's business, not the ground loop's.

Berth for the WATCHME that ticket the-memory-curve-is-recorded-not-eyeballed carries
(object the_memory_curve_is_recorded). Berthed beside cairn/devices/cc because that
is WHAT IT WATCHES.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.base.probe import Probe

_SERIES_PATH = address.instance_path("cc", 0) / "memory_series.jsonl"


def _cgroup_path() -> str | None:
    try:
        raw = Path("/proc/self/cgroup").read_text()
    except OSError:
        return None
    for line in raw.splitlines():
        if line.startswith("0::"):
            return line[3:].removesuffix(" (deleted)")
    return None


def _read_cgroup_memory(cgroup: str) -> int | None:
    try:
        return int(Path(f"/sys/fs/cgroup{cgroup}/memory.current").read_text().strip())
    except (OSError, ValueError):
        return None


def _read_rss() -> int | None:
    try:
        fields = Path("/proc/self/statm").read_text().split()
        page_size = os.sysconf("SC_PAGE_SIZE")
        return int(fields[1]) * page_size
    except (OSError, ValueError, IndexError):
        return None


def sample() -> dict:
    """Take one sample and append it to the series. Returns the record written."""
    cgroup = _cgroup_path()
    cgroup_bytes = _read_cgroup_memory(cgroup) if cgroup else None
    rss_bytes = _read_rss()
    record = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cgroup_bytes": cgroup_bytes,
        "rss_bytes": rss_bytes,
        "cgroup": cgroup,
        "pid": os.getpid(),
    }
    _SERIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_SERIES_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    return record


def _trigger(now, context: dict) -> bool:
    sample()
    return True


def _carry(context: dict) -> dict:
    if _SERIES_PATH.exists():
        try:
            lines = _SERIES_PATH.read_text().strip().splitlines()
            last = json.loads(lines[-1]) if lines else {}
            return {
                "samples": len(lines),
                "last_cgroup_bytes": last.get("cgroup_bytes"),
                "last_rss_bytes": last.get("rss_bytes"),
            }
        except (OSError, json.JSONDecodeError):
            pass
    return {"samples": 0}


def _enough(context: dict) -> bool:
    return False


PROBE = Probe(
    why="the memory trend is currently a hypothesis held in Akien's visual memory — "
        "Law 3: nothing is known until measured, and Law 10: the instrument simply "
        "has not been built. This probe builds it.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=100,
)


if __name__ == "__main__":
    rec = sample()
    print(json.dumps(rec, indent=2))
