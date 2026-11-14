"""The scheduler — each device instance's own list of verbs to run on a clock (ticket 185cee7cce24).

Outline 9.4.2.3.7 (test tiers): the hourly, daily and weekly runs are entries on a list, and
the list belongs to the device instance that runs them. So the list is declared CONFIG, and it
berths where the instance's declared config berths, in class-space:

    cairn/devices/<device>/<instance>/schedule.json   [{name, cadence, verb, why}]

and when each entry last fired is the instance's LIFE, so it berths in instance-space:

    ~/.cairn/devices/<device>/<instance>/scheduler/last_fired.json   {name: iso time}

A cadence is one of ``hourly``, ``daily@HH:MM`` or ``weekly@<Mon..Sun> HH:MM``, read in local
time. An entry is DUE when the most recent slot of its cadence at or before ``now`` is later
than its last firing (or it has never fired). Because "due" compares against the latest slot
only, a pulse after a gap spanning several slots fires the entry ONCE, never once per missed
slot.

The base shim's ``on_pulse`` asks ``due`` before its probes and fires each due entry as a
probe that invokes the entry's verb on the device itself; ``cairn <device> scheduler
list|show|get|set`` reads and writes the list (``resolve`` below). ``set`` writes through the
artifact door and refuses, by name, a verb the device does not declare and a cadence this
module cannot read.

This module imports nothing from any device (RULE 1): what it knows of the device it is
handed by the shim that calls it.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from cairn.tools.base.address import ROOTS, instance_path

FIELDS = ("name", "cadence", "verb", "why")
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
USAGE = ("cairn <device> scheduler list | show <name> | get [<name>] | "
         "set <name> --cadence <c> --verb <v> [--why <w>]")


class Unreadable(ValueError):
    """A cadence or a schedule this module cannot read. The message names what it could not."""


# --- the two addresses ---------------------------------------------------------------------

def schedule_path(device: str, instance: int = 0, repo: Path | None = None) -> Path:
    return (repo or ROOTS["repo"]) / "cairn" / "devices" / str(device) / str(instance) / "schedule.json"


def last_fired_path(device: str, instance: int = 0, roots: dict | None = None) -> Path:
    return instance_path(device, instance, roots) / "scheduler" / "last_fired.json"


# --- reading -------------------------------------------------------------------------------

def load(path: Path) -> list[dict]:
    """The entries as written. A missing file is an empty list; an unreadable one raises."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Unreadable(f"{p}: not JSON ({exc})") from exc
    if not isinstance(doc, list) or not all(isinstance(e, dict) for e in doc):
        raise Unreadable(f"{p}: a schedule is a list of {{{', '.join(FIELDS)}}} entries")
    return doc


def load_last_fired(path: Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    doc = json.loads(p.read_text(encoding="utf-8"))
    return doc if isinstance(doc, dict) else {}


def save_last_fired(path: Path, doc: dict) -> None:
    """Instance-space runtime state, written atomically (never a record of truth)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".last_fired.", dir=str(p.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, p)


# --- the clock -----------------------------------------------------------------------------

def local(now) -> datetime:
    """``now`` as a naive local datetime. A pulse's ``now`` may be a datetime (aware or not),
    a date, or epoch seconds; anything else is unreadable, said so."""
    if isinstance(now, datetime):
        return now.astimezone().replace(tzinfo=None) if now.tzinfo else now
    if isinstance(now, date):
        return datetime(now.year, now.month, now.day)
    if isinstance(now, (int, float)) and not isinstance(now, bool):
        return datetime.fromtimestamp(now)
    raise Unreadable(f"the pulse's now {now!r} is not a time")


def _hhmm(text: str, cadence: str) -> tuple[int, int]:
    h, sep, m = text.partition(":")
    if not sep or not (h.isdigit() and m.isdigit()) or len(m) != 2:
        raise Unreadable(f"cadence {cadence!r}: {text!r} is not HH:MM")
    hh, mm = int(h), int(m)
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise Unreadable(f"cadence {cadence!r}: {text!r} is not a time of day")
    return hh, mm


def slot(cadence: str, now) -> datetime:
    """The most recent slot of ``cadence`` at or before ``now``. Raises Unreadable, naming the
    cadence, for anything not ``hourly``, ``daily@HH:MM`` or ``weekly@<Day> HH:MM``."""
    t = local(now)
    c = str(cadence or "").strip()
    if c == "hourly":
        return t.replace(minute=0, second=0, microsecond=0)
    kind, sep, at = c.partition("@")
    if sep and kind == "daily":
        hh, mm = _hhmm(at.strip(), c)
        s = t.replace(hour=hh, minute=mm, second=0, microsecond=0)
        return s if s <= t else s - timedelta(days=1)
    if sep and kind == "weekly":
        day, _, clock = at.strip().partition(" ")
        if day not in DAYS:
            raise Unreadable(f"cadence {cadence!r}: {day!r} is not one of {' '.join(DAYS)}")
        hh, mm = _hhmm(clock.strip(), c)
        back = (t.weekday() - DAYS.index(day)) % 7
        s = (t - timedelta(days=back)).replace(hour=hh, minute=mm, second=0, microsecond=0)
        return s if s <= t else s - timedelta(days=7)
    raise Unreadable(f"cadence {cadence!r} is not hourly, daily@HH:MM or weekly@<Day> HH:MM")


def due(entries: list[dict], now, last_fired: dict) -> list[dict]:
    """The entries whose latest slot at or before ``now`` is later than their last firing.
    An entry with an unreadable cadence is never due here; ``refusals`` names it."""
    out = []
    for e in entries:
        try:
            s = slot(e.get("cadence"), now)
        except Unreadable:
            continue
        last = last_fired.get(e.get("name"))
        if last is None or local(datetime.fromisoformat(last)) < s:
            out.append(e)
    return out


def refusals(entries: list[dict], verbs) -> list[str]:
    """Every reason ``entries`` cannot stand, each naming what it refuses — one pass."""
    known = set(verbs)
    out: list[str] = []
    seen: set = set()
    for i, e in enumerate(entries):
        name = e.get("name")
        if not name or not isinstance(name, str):
            out.append(f"entry {i}: no name")
        elif name in seen:
            out.append(f"entry {name!r}: the name is already on the list")
        seen.add(name)
        missing = [f for f in FIELDS if not e.get(f)]
        if missing:
            out.append(f"entry {name!r}: missing {', '.join(missing)}")
        if e.get("verb") and e["verb"] not in known:
            out.append(f"entry {name!r}: verb {e['verb']!r} is not one this device declares "
                       f"({', '.join(sorted(known)) or 'it declares none'})")
        if e.get("cadence"):
            try:
                slot(e["cadence"], datetime(2026, 1, 1))
            except Unreadable as exc:
                out.append(f"entry {name!r}: {exc}")
    return out


# --- the CLI segment: cairn <device> scheduler ... ----------------------------------------

def _answer(code: int, text: str, data=None) -> dict:
    return {"exit": code, "text": text, "data": data, "cached": None}


def _flags(tokens: list[str]) -> dict | str:
    out: dict = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if not tok.startswith("--") or len(tok) < 3 or i + 1 >= len(tokens):
            return f"{tok!r} is not an argument — arguments are --key value"
        out[tok[2:]] = tokens[i + 1]
        i += 2
    return out


def resolve(shim, argv: list[str]) -> dict:
    """``cairn <device> scheduler <verb> ...`` for the shim that holds the list. The shim
    supplies the two paths (``_schedule_path``, ``_last_fired_path``) and the verbs its device
    declares (``_schedulable_verbs``); nothing else is read from it."""
    dev = shim.device_id
    if not argv:
        return _answer(2, f"cairn {dev} scheduler: a verb is needed — {USAGE}")
    verb, rest = argv[0], argv[1:]
    path = shim._schedule_path()
    entries = load(path)
    if verb == "list":
        lines = [f"{e.get('name')}  {e.get('cadence')}  {e.get('verb')}" for e in entries]
        return _answer(0, "\n".join(lines) if lines else f"{dev}: no scheduled entries ({path})", entries)
    if verb in ("show", "get"):
        fired = load_last_fired(shim._last_fired_path())
        if rest:
            hit = [e for e in entries if e.get("name") == rest[0]]
            if not hit:
                return _answer(1, f"cairn {dev} scheduler: no entry named {rest[0]!r}")
            data = dict(hit[0], last_fired=fired.get(rest[0]))
        else:
            data = [dict(e, last_fired=fired.get(e.get("name"))) for e in entries]
        if verb == "get":
            return _answer(0, json.dumps(data, sort_keys=True), data)
        rows = data if isinstance(data, list) else [data]
        text = "\n".join(f"{r.get('name')}: {r.get('cadence')} -> {r.get('verb')}  "
                         f"last fired {r.get('last_fired') or 'never'}\n  why: {r.get('why')}" for r in rows)
        return _answer(0, text or f"{dev}: no scheduled entries ({path})", data)
    if verb == "set":
        if not rest or rest[0].startswith("--"):
            return _answer(2, f"cairn {dev} scheduler set: an entry name is needed — {USAGE}")
        name, flags = rest[0], _flags(rest[1:])
        if isinstance(flags, str):
            return _answer(2, f"cairn {dev} scheduler set: {flags}")
        unknown = sorted(set(flags) - {"cadence", "verb", "why"})
        if unknown:
            return _answer(2, f"cairn {dev} scheduler set: unknown argument(s) {', '.join(unknown)}")
        old = next((e for e in entries if e.get("name") == name), {})
        entry = {"name": name, **{f: flags.get(f, old.get(f, "")) for f in FIELDS[1:]}}
        if not entry["why"]:
            entry["why"] = f"set from cairn {dev} scheduler set"
        new = [entry if e.get("name") == name else e for e in entries]
        if not old:
            new.append(entry)
        lacks = refusals(new, shim._schedulable_verbs())
        if lacks:
            return _answer(2, f"cairn {dev} scheduler set refused, nothing written:\n  " + "\n  ".join(lacks))
        from cairn.tools.artifact import artifact  # the door; imported only when a write happens
        artifact.write_json(path, new, verb="schedule", why=f"cairn {dev} scheduler set {name}")
        return _answer(0, f"{dev}: {name} {entry['cadence']} -> {entry['verb']}", entry)
    return _answer(2, f"cairn {dev} scheduler: no such verb {verb!r} — {USAGE}")
