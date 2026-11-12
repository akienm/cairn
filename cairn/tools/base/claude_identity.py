"""Which Claude is this? (ticket a1d3c9e4b702)

Four Claude sessions now share one commons: two on akiendelllinux, one on akiendell and one
on akienasus (2026-11-12). A record that says only "CC" cannot tell them apart, and
akienasus_cc_0 opened that morning on another Claude's slate as if it were its own.

Claude Code writes one record per running session at ``~/.claude/sessions/<pid>.json``,
carrying ``sessionId``, ``name`` (superclaude sets ``<host>_cc_<instance>``; a /rename sets
the new one) and ``formerNames``. It is Claude Code's internal file, so it is read
defensively and never written: a missing directory or a torn record is no session, never
an error.

    who(session_id=None) -> {"name", "former_names", "host", "session"}

Lookup order: the record whose ``sessionId`` is the given id (the newest ``updatedAt`` when
two carry it); else the record whose pid is ``$CLAUDE_PID``; else the record of one of this
process's ancestors, read from ``/proc/<pid>/stat`` where ``/proc`` exists. Nothing found:
``name`` is ``""`` and the host is still given.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _sessions_dir(sessions_dir, environ) -> Path:
    if sessions_dir is not None:
        return Path(sessions_dir)
    return Path(environ.get("CAIRN_CLAUDE_SESSIONS_DIR")
                or (Path.home() / ".claude" / "sessions"))


def _records(d: Path) -> list[dict]:
    try:
        paths = sorted(d.glob("*.json"))
    except OSError:
        return []
    out = []
    for p in paths:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _ancestors(pid: int, limit: int = 32) -> list[int]:
    """This process's parent chain, from /proc. Empty where /proc is absent (macOS)."""
    chain = []
    for _ in range(limit):
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
        except OSError:
            break
        # comm may hold spaces and parens: the fields after the LAST ')' are fixed.
        try:
            ppid = int(stat.rsplit(")", 1)[1].split()[1])
        except (IndexError, ValueError):
            break
        if ppid <= 1:
            break
        chain.append(ppid)
        pid = ppid
    return chain


def _newest(recs: list[dict]) -> dict | None:
    if not recs:
        return None
    return max(recs, key=lambda r: r.get("updatedAt") or 0)


def _by_pid(recs: list[dict], pid) -> dict | None:
    return _newest([r for r in recs if r.get("pid") == pid])


def who(session_id: str | None = None, *, sessions_dir=None, environ=None) -> dict:
    """Name the Claude session this process runs under. Never raises."""
    env = os.environ if environ is None else environ
    recs = _records(_sessions_dir(sessions_dir, env))
    rec = None
    if session_id:
        rec = _newest([r for r in recs if r.get("sessionId") == session_id])
    if rec is None and not session_id:
        try:
            rec = _by_pid(recs, int(env.get("CLAUDE_PID") or ""))
        except ValueError:
            rec = None
        if rec is None:
            for pid in _ancestors(os.getpid()):
                rec = _by_pid(recs, pid)
                if rec is not None:
                    break
    former = []
    if rec is not None:
        for f in rec.get("formerNames") or []:
            n = f.get("name") if isinstance(f, dict) else f
            if isinstance(n, str) and n:
                former.append(n)
    name = rec.get("name") if rec is not None else ""
    return {
        "name": name if isinstance(name, str) else "",
        "former_names": former,
        "host": os.uname().nodename,
        "session": (rec.get("sessionId") if rec is not None else None) or session_id or "",
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(who(sys.argv[1] if len(sys.argv) > 1 else None), indent=2))
