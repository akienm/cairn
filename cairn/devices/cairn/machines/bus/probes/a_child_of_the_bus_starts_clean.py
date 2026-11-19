"""WATCHME(a_child_of_the_bus_starts_clean) for ticket 7507a6051073.

THE QUESTION THE PROOF CANNOT ANSWER. The proof beside the bus settles, in a scratch bus, that
a child spawned from a bus thread starts with HUP, INT and TERM unblocked, and that a SIGTERM
a child sends is still named by its sender. The HYPOTHESIS is wider: that unblocking on the
spawning thread around Popen's fork, plus an at-fork hook for os.fork, reaches EVERY
descendant of the live bus (some spawn path may bypass both, such as a C extension or
os.posix_spawn), and that the window it opens costs D3 nothing that matters (a stop signal
landing in it is recorded with sender_pid null).

WHAT IT READS, both halves, from the live bus only:
  - every live descendant of the live bus process, and which stop signals its SigBlk blocks;
  - every signal stop in the live bus's stops.jsonl after this ticket's PROVED crossing, and
    how many name no sender.

FILES ONLY (/proc and the bus home): no device, no bus, no subprocess.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that re-opens
the ticket is the OWNER's act (Law 6).
"""

from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path

from cairn.tools.base.probe import Probe, Threshold, once, owning_ticket, watch_carry

_OWNING_TICKET = "7507a6051073"
_STOP_BITS = {"SIGHUP": 1 << 0, "SIGINT": 1 << 1, "SIGTERM": 1 << 14}
_ENOUGH_STOPS = 20
_ENOUGH_DAYS = 30
_HOLDS_NULL_SENDERS = 1


def era_floor(ticket_path: str | None = None):
    """The ticket's PROVED crossing, read from its log; None while it has not crossed."""
    path = ticket_path or owning_ticket(_OWNING_TICKET)
    log = re.sub(r"\.json$", ".log.jsonl", str(path))
    try:
        with open(log, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return None
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = row.get("reply") or {}
        if (row.get("gate") == "clearance" and reply.get("accepted")
                and reply.get("target") == "PROVED"):
            return datetime.datetime.fromisoformat(row["at"])
    return None


def _status(pid: str, proc: Path) -> dict:
    out = {}
    try:
        for line in (proc / pid / "status").read_text().splitlines():
            k, _, v = line.partition(":")
            out[k] = v.strip()
    except OSError:
        pass
    return out


def descendants(root_pid: int, proc: Path = Path("/proc")) -> list[dict]:
    """Every live process under ``root_pid``, with the stop signals its mask blocks."""
    parent, mask = {}, {}
    for entry in proc.iterdir() if proc.is_dir() else []:
        if not entry.name.isdigit():
            continue
        st = _status(entry.name, proc)
        if "PPid" in st and "SigBlk" in st:
            parent[int(entry.name)] = int(st["PPid"])
            mask[int(entry.name)] = int(st["SigBlk"], 16)
    found = []
    for pid in parent:
        p, seen = parent.get(pid), set()
        while p and p not in seen:
            if p == root_pid:
                found.append({"pid": pid, "blocked": [n for n, b in _STOP_BITS.items()
                                                      if mask[pid] & b]})
                break
            seen.add(p)
            p = parent.get(p)
    return found


def signal_stops(stops: Path, era) -> tuple[list[dict], list[str]]:
    """The signal stops in ``stops`` after ``era``; unreadable lines are CARRIED (Law 7)."""
    found, unreadable = [], []
    if era is None or not stops.is_file():
        return found, unreadable
    for line in stops.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            at = datetime.datetime.fromisoformat(row["at"]).replace(tzinfo=None)
        except (ValueError, KeyError, TypeError) as exc:
            unreadable.append(f"{line[:120]}: {exc}")
            continue
        if row.get("cause") == "signal" and at > era:
            found.append({"at": row["at"], "signal": (row.get("detail") or {}).get("signal"),
                          "sender_pid": (row.get("detail") or {}).get("sender_pid")})
    return found, unreadable


def survey(home: Path, era, proc: Path = Path("/proc")) -> dict:
    stops, unreadable = signal_stops(home / "stops.jsonl", era)
    pid = None
    try:
        pid = int(json.loads((home / "bus.port").read_text()).get("pid") or 0) or None
    except (OSError, ValueError, AttributeError):
        pass
    if pid is None:
        for entry in proc.iterdir() if proc.is_dir() else []:
            try:
                cmd = (entry / "cmdline").read_bytes().split(b"\0")
            except OSError:
                continue
            if b"cairn.devices.cairn.machines.bus" in cmd and b"serve" in cmd and \
                    str(home).encode() in cmd:
                pid = int(entry.name)
                break
    kids = descendants(pid, proc) if pid else []
    return {"era": era.isoformat() if era else None, "bus_pid": pid,
            "descendants": len(kids), "blocked": [k for k in kids if k["blocked"]],
            "signal_stops": len(stops), "null_senders": sum(1 for s in stops if s["sender_pid"] is None),
            "stops": stops, "unreadable": unreadable}


def _live() -> dict:
    from cairn.devices.cairn.machines.bus.server import bus_home
    era = era_floor()
    s = survey(bus_home(), era)
    s["past_horizon"] = bool(era and datetime.datetime.now() >= era + datetime.timedelta(days=_ENOUGH_DAYS))
    return s


def _settled(context) -> bool:
    s = once(context, "survey", _live)
    return s["signal_stops"] >= _ENOUGH_STOPS or s["past_horizon"]


def _trigger(now, context: dict) -> bool:
    s = once(context, "survey", _live)
    return bool(s["blocked"]) or _settled(context)


def _holds(context: dict) -> bool:
    s = once(context, "survey", _live)
    return not s["blocked"] and s["null_senders"] <= _HOLDS_NULL_SENDERS


def _carry(context: dict) -> dict:
    s = once(context, "survey", _live)
    return {
        "finding": ("%d live descendants of the bus, %d with a stop signal blocked; %d signal "
                    "stops since PROVED, %d with no sender" % (
                        s["descendants"], len(s["blocked"]), s["signal_stops"], s["null_senders"])),
        "shape": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "every descendant of the live bus starts with HUP, INT and TERM unblocked, and the "
            "spawn window costs D3 at most one stop named without its sender"),
        "suggests": (
            "cc_0 reviews the hypothesis at server.py _children_start_clean: any blocked "
            "descendant names a spawn path that bypasses it (fix that path or move the fix "
            "into the child); more than 1 null sender rewrites it toward a narrower window"),
    }


PROBE = Probe(
    why="the proof settles a scratch bus's children; whether every spawn path of the live bus "
        "is covered, and what the window costs D3, is a fact about live traffic",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    verb="machines/watchme/watch",
    carry=watch_carry(_OWNING_TICKET, _carry, holds=_holds),
    enough=_settled,
    thresholds=(
        Threshold(_ENOUGH_STOPS, "signal stops after PROVED that settle the hypothesis",
                  set_by="ticket 7507a6051073 watchme.enough names the number"),
        Threshold(_ENOUGH_DAYS, "days after PROVED after which scarcity is the reading",
                  set_by="ticket 7507a6051073 watchme.enough names the number"),
        Threshold(_HOLDS_NULL_SENDERS, "signal stops with no sender for the hypothesis to hold",
                  set_by="ticket 7507a6051073 watchme.enough names the number"),
    ),
)
