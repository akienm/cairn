"""Deterministic operator inbox — reads live state, stores nothing."""

from __future__ import annotations

import json
from pathlib import Path

CAIRN_ROOT = Path.home() / "dev" / "src" / "cairn"
COMMONS_ROOT = Path.home() / "dev" / "src" / "CairnCommons"
TICKETS_DIR = COMMONS_ROOT / "tickets"
IDEAS_DIR = COMMONS_ROOT / "ideas"
QUESTIONS_DIR = COMMONS_ROOT / "questions"
INTENTIONS_DIR = COMMONS_ROOT / "intentions-not-beside-code"

TERMINAL_STATES = {"PROVED", "SUPERSEDED", "RETIRED", "KILLED", "ABSORBED"}

SECTION_ORDER = [
    "troubles",
    "email",
    "adjudications",
    "questions",
    "design",
    "tickets",
    "intentions",
    "ideas",
]


def _cursor(state: str) -> str | None:
    if not state:
        return None
    for part in state.split():
        if part.startswith("[") and part.endswith("]"):
            return part.strip("[]")
    return None


def read_troubles() -> dict:
    from cairn.devices.trouble.trouble import TroubleDevice
    td = TroubleDevice()
    live = td.live()
    total = td.all()
    return {"live": live, "live_count": len(live), "total_count": len(total)}


def read_adjudications() -> dict:
    from cairn.machines.learning_block.learning_block import pending_findings
    pf = pending_findings()
    return {"findings": pf, "count": len(pf)}


def read_questions() -> dict:
    if not QUESTIONS_DIR.exists():
        return {"open": [], "count": 0}
    open_q = sorted(p.stem for p in QUESTIONS_DIR.glob("open-*.json"))
    all_q = sorted(p.stem for p in QUESTIONS_DIR.glob("*.json")
                   if not p.stem.startswith("_"))
    return {"open": open_q, "count": len(open_q), "total": len(all_q)}


def read_tickets() -> dict:
    if not TICKETS_DIR.exists():
        return {"by_state": {}, "total_not_done": 0}
    by_state: dict[str, list[str]] = {}
    for p in sorted(TICKETS_DIR.glob("*.json")):
        try:
            t = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if t.get("role") in ("store-charter", "charter"):
            continue
        state = t.get("state", "")
        cursor = _cursor(state)
        if cursor in TERMINAL_STATES:
            continue
        bucket = cursor or "UNKNOWN"
        by_state.setdefault(bucket, []).append(p.stem)
    total = sum(len(v) for v in by_state.values())
    return {"by_state": by_state, "total_not_done": total}


def read_intentions() -> dict:
    if not INTENTIONS_DIR.exists():
        return {"count": 0, "items": []}
    items = sorted(p.stem for p in INTENTIONS_DIR.glob("I-*.md"))
    return {"count": len(items), "items": items}


def read_ideas() -> dict:
    if not IDEAS_DIR.exists():
        return {"count": 0, "items": []}
    items = []
    for p in sorted(IDEAS_DIR.glob("*.json")):
        if p.stem.startswith("_"):
            continue
        try:
            d = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        items.append({
            "id": p.stem,
            "author": d.get("author", "?"),
            "prose_prefix": (d.get("prose", "") or "")[:80],
        })
    return {"count": len(items), "items": items}


def read_email() -> dict:
    return {"count": 0, "note": "bus unresolved-messages query not yet built"}


def gather_all() -> dict:
    return {
        "troubles": read_troubles(),
        "email": read_email(),
        "adjudications": read_adjudications(),
        "questions": read_questions(),
        "design": {},
        "tickets": read_tickets(),
        "intentions": read_intentions(),
        "ideas": read_ideas(),
    }


def _line(width: int = 76) -> str:
    return "=" * width


def _section_line(title: str, width: int = 76) -> str:
    dashes = "-" * (width - len(title) - 4)
    return f"-- {title} {dashes}"


def format_inbox(data: dict) -> str:
    lines: list[str] = []
    troubles = data["troubles"]
    adjudications = data["adjudications"]
    questions = data["questions"]
    tickets = data["tickets"]
    intentions = data["intentions"]
    ideas = data["ideas"]
    email = data["email"]

    by_state = tickets["by_state"]
    thinkme = by_state.get("THINKME", [])

    lines.append("")
    lines.append(_line())
    lines.append("                    OPERATOR INBOX")
    lines.append(_line())
    lines.append("")

    # Totals
    parts = []
    if troubles["live_count"]:
        parts.append(f"{troubles['live_count']} live trouble(s)")
    else:
        parts.append("0 live troubles")
    parts.append(f"{adjudications['count']} adjudication(s)")
    parts.append(f"{questions['count']} open question(s)")
    parts.append(f"{tickets['total_not_done']} tickets (CC work)")
    parts.append(f"{ideas['count']} idea(s)")
    lines.append("  " + " | ".join(parts))
    lines.append("")

    # TROUBLES
    if troubles["live_count"] == 0:
        lines.append(f"  TROUBLES: 0 live ({troubles['total_count']} exist, all CLEARED)")
    else:
        lines.append(_section_line("TROUBLES NEEDING OPERATOR ATTENTION"))
        lines.append("")
        for t in troubles["live"]:
            tid = t.get("id", "?")
            standing = t.get("standing", "?")
            why = t.get("why", "")
            lines.append(f"    {tid}  ({standing})")
            if why:
                lines.append(f"      {why[:100]}")
        lines.append("")

    # EMAIL
    if email["count"] == 0:
        lines.append(f"  EMAIL: {email.get('note', '0 unresolved')}")
    else:
        lines.append(_section_line("EMAIL NEEDING OPERATOR ATTENTION"))
        lines.append("")
        lines.append(f"    {email['count']} unresolved message(s)")
        lines.append("")

    # ADJUDICATIONS
    if adjudications["count"] == 0:
        lines.append("  ADJUDICATIONS: 0 at the gate")
    else:
        lines.append("")
        lines.append(_section_line(f"ADJUDICATIONS ({adjudications['count']})"))
        lines.append("")
        for f in adjudications["findings"]:
            fid = f.get("id", "?")[:12]
            block = f.get("block", "?")
            when = (f.get("when", "") or "")[:10]
            bullets = f.get("data", {}).get("bullets", [])
            lines.append(f"    {fid}  [{block}]  {when}")
            for b in bullets[:2]:
                text = b.get("text", "") if isinstance(b, dict) else str(b)
                lines.append(f"        {text[:90]}")
        lines.append("")

    # QUESTIONS
    if questions["count"] == 0:
        lines.append("  QUESTIONS: 0 open")
    else:
        lines.append("")
        lines.append(_section_line(f"QUESTIONS FOR OPERATOR ({questions['count']})"))
        lines.append("")
        for q in questions["open"]:
            lines.append(f"    {q}")
        lines.append("")

    # DESIGN (THINKME tickets — not yet designed, need operator input)
    if not thinkme:
        lines.append("  DESIGN: 0 tickets at THINKME")
    else:
        lines.append("")
        lines.append(_section_line(f"DESIGN NEEDING OPERATOR ATTENTION ({len(thinkme)})"))
        lines.append("")
        for t in thinkme:
            lines.append(f"    {t}")
        lines.append("")

    # TICKETS (all CC work — summary only)
    lines.append("")
    state_parts = []
    for s in ["THINKME", "TICKETME", "BUILDME", "PROVEME", "WATCHME"]:
        count = len(by_state.get(s, []))
        if count:
            state_parts.append(f"{s} ({count})")
    lines.append(f"  TICKETS ({tickets['total_not_done']} not done, all CC work): "
                 + " | ".join(state_parts))

    # INTENTIONS
    lines.append(f"  INTENTIONS: {intentions['count']} in intentions-not-beside-code (settled design documents)")

    # IDEAS
    lines.append("")
    lines.append(_section_line(f"IDEAS ({ideas['count']})"))
    lines.append("")
    for item in ideas["items"]:
        iid = item["id"]
        date = iid[:10] if len(iid) >= 10 else ""
        slug = iid[11:] if len(iid) > 11 else iid
        lines.append(f"    {date}  {slug}")
    lines.append("")

    lines.append(_line())
    lines.append("")
    return "\n".join(lines)


def build_inbox() -> str:
    return format_inbox(gather_all())


if __name__ == "__main__":
    print(build_inbox())
