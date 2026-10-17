"""The idle trigger — when the cairn device starts a sleep cycle (ticket 9b6b392ebcfe).

Akien's answer (open-91f17c211689) names what counts as activity: *"any time i interact with
you, or any of our creations in cairn. so right now, you, the librarian, the web server, or the
command line."* Each of the four is read from a record its OWNER already writes, by path, so
nothing here imports cc, the librarian or the web server (RULE 1):

  cc            Claude Code transcripts (``~/.claude/projects/*/*.jsonl``): a user entry whose
                ``origin.kind`` is ``human``, or an origin-less ``cli`` entry that is neither a
                tool result nor meta — a typed slash command carries no origin (measured
                2026-10-17). ``sdk-cli`` entries are rehearsal reads, ``peer`` and
                ``task-notification`` are machines, and none of those count.
  command_line  ``/dev/pts/N`` atime — the kernel's last-input stamp on each terminal.
  web_server    ``serve`` records under ``logs/web_server/0``, stamped in the file name.
  librarian     ``chat`` records under ``logs/librarian/0``, stamped in the file name.

THE SAFE DIRECTION. A reading that sees activity where there was none only delays sleep; one
that misses activity sleeps on Akien mid-work, which is the falsifier. So every doubt leans to
activity: a source that cannot be read is named ``unread`` and holds sleep (never silence), a
gap in what was scanned is filled with the later of the two possible stamps, and an origin-less
cli entry counts as a hand.

The pulse is a RECEIVER: ``python3 -m cairn.devices.cairn pulse`` runs it once and exits. What
spawns it on the beat is ticket acb4ecd84364's; nothing here waits, polls or sleeps.
"""

from __future__ import annotations

import glob
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cairn.tools.base.address import instance_path, log_path
from cairn.devices.cairn.machines.sleep_cycle import token

# Three hours of quiet starts a sleep cycle — Akien, 2026-08-24 (ticket 9b6b392ebcfe's HOW).
# A parameter of every decision below, never read as a constant inside one.
IDLE_THRESHOLD_S = 3 * 3600
IDLE_THRESHOLD_PROVENANCE = "Akien 2026-08-24, ticket 9b6b392ebcfe: three hours idle"

SOURCES = ("cc", "command_line", "web_server", "librarian")
TRANSCRIPTS = Path.home() / ".claude" / "projects"
PTS = Path("/dev/pts")


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat()


def _parse(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _later(a: datetime | None, b: datetime | None) -> datetime | None:
    return b if a is None else a if b is None else max(a, b)


# ── the four readers: each returns the newest human stamp after `since`, or None ──

def _human_entry(e: dict) -> bool:
    if e.get("type") != "user":
        return False
    kind = (e.get("origin") or {}).get("kind")
    if kind is not None:
        return kind == "human"
    if e.get("entrypoint") != "cli" or e.get("isMeta") or e.get("isCompactSummary"):
        return False
    content = (e.get("message") or {}).get("content")
    return not (isinstance(content, list)
                and any(isinstance(x, dict) and x.get("type") == "tool_result" for x in content))


def read_cc(since: datetime, transcripts: Path) -> datetime | None:
    if not transcripts.is_dir():
        raise FileNotFoundError(f"no transcripts folder at {transcripts}")
    newest = None
    for f in glob.glob(os.path.join(glob.escape(str(transcripts)), "*", "*.jsonl")):
        if os.path.getmtime(f) < since.timestamp():
            continue  # untouched since the floor: nothing in it can be newer
        with open(f, errors="replace") as fh:
            for line in fh:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if _human_entry(e):
                    newest = _later(newest, _parse(e.get("timestamp")))
    return newest if newest and newest > since else None


def read_command_line(since: datetime, pts: Path) -> datetime | None:
    if not pts.is_dir():
        raise FileNotFoundError(f"no terminal folder at {pts}")
    newest = None
    for p in pts.iterdir():
        if p.name.isdigit():
            newest = _later(newest, datetime.fromtimestamp(p.stat().st_atime, timezone.utc))
    return newest if newest and newest > since else None


def _read_log_stamps(device: str, gate: str, since: datetime, roots) -> datetime | None:
    d = log_path(device, 0, roots)
    if not d.is_dir():
        raise FileNotFoundError(f"no logs folder at {d}")
    newest = None
    for p in d.iterdir():
        if not p.name.endswith(f".{gate}.json"):
            continue
        stamp = datetime.strptime(".".join(p.name.split(".")[:3]), "%Y%m%d.%H%M%S.%f")
        newest = _later(newest, stamp.replace(tzinfo=timezone.utc))
    return newest if newest and newest > since else None


def latest_activity(since: datetime, *, roots=None, transcripts: Path | None = None,
                    pts: Path | None = None) -> dict:
    """Per source ``{"at": iso|None, "unread": reason|None}`` — ``at`` None means read, and
    nothing human after ``since``; ``unread`` means it could not be read at all."""
    readers = {
        "cc": lambda: read_cc(since, transcripts or TRANSCRIPTS),
        "command_line": lambda: read_command_line(since, pts or PTS),
        "web_server": lambda: _read_log_stamps("web_server", "WebServerDevice.serve", since, roots),
        "librarian": lambda: _read_log_stamps("librarian", "LibrarianDevice.chat", since, roots),
    }
    out = {}
    for name in SOURCES:
        try:
            at = readers[name]()
            out[name] = {"at": _iso(at) if at else None, "unread": None}
        except Exception as exc:  # noqa: BLE001 — named, never silence (Law 7)
            out[name] = {"at": None, "unread": f"{type(exc).__name__}: {exc}"}
    return out


# ── the away window: Akien's declared absence, held by the cairn device alone ──

def away_path(roots=None) -> Path:
    return instance_path("cairn", 0, roots) / "away.json"


def read_away(roots=None) -> dict | None:
    p = away_path(roots)
    return json.loads(p.read_text()) if p.is_file() else None


def set_away(start: str, end: str, why: str, *, roots=None, now=None) -> dict:
    s, e = _parse(start), _parse(end)
    if s is None or e is None or e <= s:
        raise ValueError(f"an away window needs start < end, got {start!r} .. {end!r}")
    window = {"start": _iso(s), "end": _iso(e), "why": why,
              "set_at": _iso(now or datetime.now(timezone.utc))}
    p = away_path(roots)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(window, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, p)
    return window


def clear_away(roots=None) -> dict | None:
    window = read_away(roots)
    away_path(roots).unlink(missing_ok=True)
    return window


# ── the decision and the pulse ──

def pulse_path(roots=None) -> Path:
    return token.cycle_dir(roots) / "pulse.json"


def decide(sources: dict, last_activity: datetime, *, now: datetime, threshold_s: float,
           away: dict | None, cycle: dict | None) -> tuple[bool, str]:
    """Due when quiet past the threshold, or inside an away window — and no cycle is open, and
    none was opened since the last activity (or the window's start): one sleep per quiet spell."""
    in_window = bool(away) and _parse(away["start"]) <= now < _parse(away["end"])
    if cycle is not None and cycle.get("closed_at") is None:
        return False, f"cycle {cycle['cycle_id']} is still open"
    anchor = _parse(away["start"]) if in_window else last_activity
    if cycle is not None and _parse(cycle["opened_at"]) >= anchor:
        return False, f"cycle {cycle['cycle_id']} already ran since {_iso(anchor)}"
    if in_window:
        return True, f"inside the away window {away['start']} .. {away['end']}"
    unread = sorted(n for n, s in sources.items() if s["unread"])
    if unread:
        return False, f"unread source(s) {unread} hold sleep: an unread source is never silence"
    quiet = (now - last_activity).total_seconds()
    if quiet < threshold_s:
        return False, f"active: quiet {int(quiet)}s of {int(threshold_s)}s"
    return True, f"quiet {int(quiet)}s >= {int(threshold_s)}s"


def _ask_mint() -> dict:
    from cairn.tools.bus_client import reach
    reply = reach("cairn").request(sender="cairn", to="cairn", verb="sleep-cycle",
                                   why="idle trigger: the system has been quiet past the threshold",
                                   body={"act": "mint"})
    return reply["body"]


def pulse(*, roots=None, now: datetime | None = None, threshold_s: float = IDLE_THRESHOLD_S,
          transcripts: Path | None = None, pts: Path | None = None, ask=None) -> dict:
    """Read, decide, mint when due, and write the one decision record to pulse.json."""
    now = now or datetime.now(timezone.utc)
    prior = json.loads(pulse_path(roots).read_text()) if pulse_path(roots).is_file() else {}
    carried = _parse(prior.get("last_activity"))
    floor = now - timedelta(seconds=threshold_s)
    since = _later(carried, floor)
    sources = latest_activity(since, roots=roots, transcripts=transcripts, pts=pts)
    seen = None
    for s in sources.values():
        seen = _later(seen, _parse(s["at"]))
    # Nothing seen after `since` means the last activity is at or before it: take `since`, the
    # later bound, so a gap in what was scanned only ever delays sleep.
    last_activity = _later(seen, carried) or floor
    due, why = decide(sources, last_activity, now=now, threshold_s=threshold_s,
                      away=read_away(roots), cycle=token.standing(roots))
    record = {"at": _iso(now), "due": due, "why": why, "threshold_s": threshold_s,
              "last_activity": _iso(last_activity), "sources": sources, "minted": None}
    if due:
        answer = (ask or _ask_mint)()
        record["minted"] = (answer.get("cycle") or {}).get("cycle_id") or answer
    p = pulse_path(roots)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, p)
    return record
