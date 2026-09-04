"""codemother/dashboard.py — the whole coding system at a glance.

The consumer is the operator scanning the full picture. Shows every category
in priority order (unexpected → troubles → email → adjudication → design →
PROVEME → BUILDME → WATCHME → done), each ticket as the standard atom:
date, state, hex, title.

Reads are from operator_inbox readers — the SINGLE SOURCE of live-state reads
(Law 1). This module formats; it reads nothing of its own.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.transitions import TERMINAL_STATES
from cairn.tools.operator_inbox.inbox import (
    gather_all,
    read_tickets,
    _cursor,
    TICKETS_DIR,
)

_TICKET_PRIORITY = [
    "THINKME", "THINKME:waiting",
    "TICKETME", "TICKETME:waiting",
    "PROVEME", "PROVEME:waiting",
    "BUILDME", "BUILDME:waiting",
    "WATCHME",
]

_LINE = "=" * 76


def _count_done(*, tickets_dir: Path | None = None) -> dict:
    d = tickets_dir or TICKETS_DIR
    if not d.exists():
        return {"total": 0, "by_state": {}}
    by_state: dict[str, int] = {}
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            t = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if t.get("role") in ("store-charter", "charter"):
            continue
        cursor = _cursor(t.get("workflow_and_state", ""))
        if cursor in TERMINAL_STATES:
            by_state[cursor] = by_state.get(cursor, 0) + 1
    return {"total": sum(by_state.values()), "by_state": by_state}


def _read_tickets_with_detail(*, tickets_dir: Path | None = None) -> dict:
    """Read non-terminal tickets with date/title for the atom display."""
    d = tickets_dir or TICKETS_DIR
    if not d.exists():
        return {"by_state": {}, "total": 0}
    by_state: dict[str, list[dict]] = {}
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            t = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if t.get("role") in ("store-charter", "charter"):
            continue
        cursor = _cursor(t.get("workflow_and_state", ""))
        if cursor in TERMINAL_STATES:
            continue
        base = (cursor or "UNKNOWN").split("(")[0].split(":")[0]
        is_waiting = ":waiting" in (cursor or "")
        group = f"{base}:waiting" if is_waiting else base
        if group.startswith("WATCHME"):
            group = "WATCHME:waiting" if is_waiting else "WATCHME"
        by_state.setdefault(group, []).append({
            "date": t.get("date", t.get("cast", "")) or "",
            "state": cursor or "UNKNOWN",
            "hex": t.get("id", "")[:12],
            "title": t.get("title", ""),
        })
    total = sum(len(v) for v in by_state.values())
    return {"by_state": by_state, "total": total}


def _format_atom(ticket: dict) -> str:
    date = (ticket.get("date") or "")[:10]
    state = ticket.get("state", "?")
    base = state.split("(")[0].split(":")[0]
    short_state = f"{base}:waiting" if ":waiting" in state else base
    hex_id = ticket.get("hex", "?")
    title = ticket.get("title", "")
    return f"    {date:<12s}{short_state:<20s}{hex_id:<14s}{title}"


def format_dashboard(data: dict | None = None, **kw) -> str:
    if data is None:
        data = gather_all(**kw)
    troubles = data["troubles"]
    email = data["email"]
    adjudications = data["adjudications"]
    lap = data.get("lap", {"items": [], "count": 0})
    questions = data["questions"]
    intentions = data["intentions"]
    ideas = data["ideas"]

    tickets = _read_tickets_with_detail(tickets_dir=kw.get("tickets_dir"))
    done = _count_done(tickets_dir=kw.get("tickets_dir"))
    by_state = tickets["by_state"]

    lines: list[str] = []
    lines.append("")
    lines.append(_LINE)
    lines.append("                  CODEMOTHER DASHBOARD")
    lines.append(_LINE)
    lines.append("")

    # Summary line
    parts = [
        f"{troubles['live_count']} live trouble(s)",
        f"{email.get('count', 0)} lost email",
        f"{adjudications['count']} awaiting review",
        f"{lap['count']} adjudication(s)",
        f"{questions['count']} open question(s)",
        f"{tickets['total']} active ticket(s)",
        f"{done['total']} done",
        f"{ideas['count']} idea(s)",
    ]
    lines.append("  " + " | ".join(parts))
    lines.append("")

    # 0. Unexpected — IOUs from CLAUDE.md (counted only, not read here)
    # 1. Troubles
    if troubles["live_count"]:
        lines.append(f"  TROUBLES ({troubles['live_count']} live):")
        for t in troubles["live"]:
            lines.append(f"    {t.get('id', '?')}  ({t.get('standing', '?')})")
    else:
        lines.append(f"  TROUBLES: 0 live ({troubles['total_count']} exist, all CLEARED)")

    # 2. Email
    if email.get("count", 0):
        lines.append(f"  EMAIL: {email['count']} undelivered")
    else:
        lines.append(f"  EMAIL: 0 unresolved")

    # 3. Awaiting review / adjudication
    lines.append(f"  ARTIFACT REVIEWS: {adjudications['count']} awaiting review")
    if lap["count"]:
        lines.append(f"  ADJUDICATION: {lap['count']} pending")

    # 4. Design queue
    lines.append(f"  QUESTIONS: {questions['count']} open")
    thinkme = by_state.get("THINKME", [])
    lines.append(f"  DESIGN: {len(thinkme)} tickets at THINKME")

    # 5–7. Tickets by priority with atom format
    lines.append("")
    for group in _TICKET_PRIORITY:
        bucket = by_state.get(group, [])
        if not bucket:
            continue
        sorted_bucket = sorted(bucket, key=lambda t: t.get("date", ""))
        lines.append(f"  {group} ({len(bucket)}):")
        for t in sorted_bucket:
            lines.append(_format_atom(t))
    remaining = {k: v for k, v in by_state.items()
                 if k not in _TICKET_PRIORITY and k != "THINKME" and v}
    for k in sorted(remaining):
        lines.append(f"  {k} ({len(remaining[k])}):")
        for t in sorted(remaining[k], key=lambda t: t.get("date", "")):
            lines.append(_format_atom(t))

    # 8. Done (counts only)
    lines.append("")
    done_parts = [f"{s} ({c})" for s, c in sorted(done["by_state"].items())]
    lines.append(f"  DONE ({done['total']}): " + " | ".join(done_parts))

    # INTENTIONS + IDEAS
    lines.append(f"  INTENTIONS: {intentions['count']} in intentions-not-beside-code")
    lines.append(f"  IDEAS: {ideas['count']}")

    lines.append("")
    lines.append(_LINE)
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import sys
    print(format_dashboard())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
