"""PROBE — is the process beating the same one holding the claim?

Three outcomes:
  MATCH    — the flock holder's pid equals the beater's pid (green)
  MISMATCH — a DIFFERENT pid holds the flock than the one beating (the 80-minute condition)
  UNABLE   — /proc/locks unreadable or lock file absent; reported, never silently green

The probe reads two numbers that already exist — the kernel's /proc/locks and the beater's
own pid in liveness.json — and compares them. It carries no authority (Law 6): it reads and
records, gates nothing, kills nothing.

Ticket: the-beater-holds-the-claim (2026-08-18).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from cairn.devices.cairn.machines.ground_loop.guard import LOCK_NAME
from cairn.devices.cairn.machines.ground_loop.liveness import RECORD_NAME, instance_home
from cairn.tools.base.probe import Probe, owning_ticket

_PROC_LOCKS = Path("/proc/locks")
_OWNING_TICKET = "the-beater-holds-the-claim"
_HORIZON = 1000


def lock_holder_pid(home: Path) -> dict:
    """Ask the kernel who holds the flock on run.lock.

    Returns ``{"pid": int, "inode": int}`` on success,
    ``{"pid": None, "inode": ..., "lack": str}`` on inability.
    """
    lock_path = home / LOCK_NAME
    if not lock_path.exists():
        return {"pid": None, "inode": None, "lack": f"no lock file at {lock_path}"}

    try:
        inode = os.stat(lock_path).st_ino
    except OSError as e:
        return {"pid": None, "inode": None, "lack": f"cannot stat {lock_path}: {e}"}

    try:
        lines = _PROC_LOCKS.read_text().splitlines()
    except OSError as e:
        return {"pid": None, "inode": inode,
                "lack": f"cannot read {_PROC_LOCKS}: {e}"}

    # /proc/locks format: "N: TYPE ADVISORY R/W PID MAJOR:MINOR:INODE START END"
    for line in lines:
        parts = line.split()
        if len(parts) < 6:
            continue
        dev_inode = parts[5]  # "103:02:28593212"
        if dev_inode.endswith(f":{inode}"):
            try:
                return {"pid": int(parts[4]), "inode": inode}
            except (ValueError, IndexError):
                continue

    return {"pid": None, "inode": inode,
            "lack": f"inode {inode} not found in {_PROC_LOCKS} — no flock held"}


def beater_pid(home: Path) -> int | None:
    """Read the pid the beating process wrote into liveness.json."""
    import json
    path = home / RECORD_NAME
    try:
        record = json.loads(path.read_text())
        return record.get("pid")
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def check(home: Path) -> dict:
    """The comparison: three outcomes.

    Returns ``{"outcome": "MATCH"|"MISMATCH"|"UNABLE", ...}`` with both pids
    and the lock's inode so a reader gets the full picture without inspecting the host.
    """
    holder = lock_holder_pid(home)
    beating = beater_pid(home)

    if holder["pid"] is None:
        return {"outcome": "UNABLE", "holder": holder, "beater_pid": beating,
                "detail": holder.get("lack", "unknown")}

    if beating is None:
        return {"outcome": "UNABLE", "holder": holder, "beater_pid": None,
                "detail": "no beater pid in liveness record"}

    if holder["pid"] == beating:
        return {"outcome": "MATCH", "holder_pid": holder["pid"],
                "beater_pid": beating, "inode": holder["inode"]}

    return {"outcome": "MISMATCH", "holder_pid": holder["pid"],
            "beater_pid": beating, "inode": holder["inode"],
            "detail": (f"the flock holder (pid {holder['pid']}) is not the beater "
                       f"(pid {beating}) — two loops or a leaked claim")}


def _trigger(now, context: dict) -> bool:
    """TRUE on MISMATCH or UNABLE — the conditions that must be loud (Law 7).
    A MATCH is the healthy state and needs no poke."""
    result = check(instance_home())
    context["_result"] = result
    return result["outcome"] in ("MISMATCH", "UNABLE")


def _carry(context: dict) -> dict:
    result = context.get("_result") or check(instance_home())
    return {
        "finding": result.get("detail", result["outcome"]),
        "outcome": result["outcome"],
        "holder_pid": result.get("holder_pid") or (result.get("holder") or {}).get("pid"),
        "beater_pid": result.get("beater_pid"),
        "inode": result.get("inode") or (result.get("holder") or {}).get("inode"),
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="the 80-minute double-loop incident was measurable the whole time it went "
        "unmeasured — two numbers, both already on the machine; this watches the "
        "comparison every beat and makes a mismatch permanent and loud (Law 7)",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "ground_loop", "kind": "efficacy"},
    carry=_carry,
    horizon=_HORIZON,
)
