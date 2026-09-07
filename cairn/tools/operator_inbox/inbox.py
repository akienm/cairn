"""Deterministic operator inbox — reads live state, stores nothing.

THE SINGLE SOURCE of live-state reads for every surface: the session-open banner
(bin/cmd/slate), the standalone ``cairn operator show inbox``, and any future
consumer. Each reader calls the source's own API and the script assembles the
results. A new data source is a new reader function added here, not a reimplementation
in another file.

Paths are injectable via env vars for proofs (same idiom as the slate and the
skill_block berths).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from cairn.tools.system_word import fold, is_word

CAIRN_ROOT = Path(os.environ.get(
    "CAIRN_ROOT", Path.home() / "dev" / "src" / "cairn"))
COMMONS_ROOT = Path(os.environ.get(
    "CAIRN_COMMONS_ROOT", Path.home() / "dev" / "src" / "CairnCommons"))
TICKETS_DIR = Path(os.environ.get(
    "CAIRN_TICKETS_DIR", COMMONS_ROOT / "tickets"))
IDEAS_DIR = Path(os.environ.get(
    "CAIRN_IDEAS_DIR", COMMONS_ROOT / "ideas"))
QUESTIONS_DIR = Path(os.environ.get(
    "CAIRN_QUESTIONS_DIR", COMMONS_ROOT / "questions"))
INTENTIONS_DIR = Path(os.environ.get(
    "CAIRN_INTENTIONS_DIR", COMMONS_ROOT / "intentions-not-beside-code"))
ADJUDICATIONS_DIR = Path(os.environ.get(
    "CAIRN_ADJUDICATIONS_DIR", COMMONS_ROOT / "adjudications"))

from cairn.tools.base.transitions import (
    TERMINAL_STATES,
    MalformedWorkflow,
    parse_workflow,
)

# THE ONE DISPLAY ORDER for a ticket's status label (ticket 3feb201c84ea, 2026-09-06):
# what needs a hand first. Every report that lists tickets by status walks this list
# through ``label_sort_key`` — the inbox, the codemother dashboard, the harbor map.
# A label the list does not know sorts after all of these, never silently first.
LABEL_ORDER = [
    "THINKME", "TICKETME", "SORTEDME",
    "PROVEME",
    "BUILDME",
    "WATCHME",
    "PROVED", "SUPERSEDED", "RETIRED", "DROPPED", "KILLED", "ABSORBED",
]

# A ticket whose workflow_and_state does not parse still has ONE status, and it is this
# word — loud on every surface (Law 7), never a quiet "UNKNOWN" bucket.
UNPARSED = "UNPARSED"

SECTION_ORDER = [
    "troubles",
    "email",
    "adjudications",
    "lap",
    "questions",
    "design",
    "tickets",
    "intentions",
    "ideas",
]


def _slugify(text: str, max_len: int = 60) -> str:
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'\s+', '-', s)
    return s[:max_len].rstrip('-')


# ---------------------------------------------------------------------------
# A ticket has ONE status (ticket 3feb201c84ea; Akien 2026-09-06: "for a given
# ticket that appers in all the places, i should see the same status. it has one
# status."). The cursor is read ONCE, here, through transitions.parse_workflow —
# the grammar's own parser, not a regex of this file's — and the label every
# report prints is derived ONCE, here. Measured before this: three readers globbed
# tickets/ and derived the label three ways, and the same ticket wore four statuses
# across the inbox, the dashboard and the harbor map.
# ---------------------------------------------------------------------------

def cursor_of(workflow_and_state: str) -> str | None:
    """The ticket's cursor TOKEN — ``WATCHME(one-status-everywhere):waiting``,
    ``PROVEME:waiting``, ``PROVED`` — read through the grammar. None when the
    string does not parse (prose, no bracket, unknown phase): the caller labels
    that UNPARSED rather than guessing."""
    if not isinstance(workflow_and_state, str) or not workflow_and_state.strip():
        return None
    try:
        wf = parse_workflow(workflow_and_state)
    except MalformedWorkflow:
        return None
    token = wf.here
    if wf.here_object:
        token += f"({wf.here_object})"
    if wf.phase:
        token += f":{wf.phase}"
    return token


def status_label(cursor: str | None) -> str:
    """The ONE display label for a cursor token: the base stage, plus ``:waiting``
    when the pickup phase is waiting, the WATCHME object stripped.
    ``WATCHME(x):waiting`` -> ``WATCHME:waiting``; ``PROVEME:in-process`` -> ``PROVEME``;
    None -> ``UNPARSED``."""
    if not cursor:
        return UNPARSED
    base = cursor.split("(")[0].split(":")[0]
    if cursor.endswith(":waiting"):
        return f"{base}:waiting"
    return base


def is_stage_token(text: str | None) -> bool:
    """Whether a standing string is a stage token of the grammar (``BUILDME``,
    ``WATCHME(x):waiting``, ``PROVED``) rather than prose. Vocabulary-based, no
    regex: a summons ends in ME, a rest is in TERMINAL_STATES."""
    if not isinstance(text, str) or not text.strip() or " " in text.strip():
        return False
    base = text.strip().split("(")[0].split(":")[0]
    return base.isupper() and base.isidentifier() and (
        base.endswith("ME") or base in TERMINAL_STATES)


def label_sort_key(label: str) -> tuple:
    """Priority rank of a label — LABEL_ORDER by base, waiting after its bare stage."""
    base = label.split(":")[0]
    try:
        rank = LABEL_ORDER.index(base)
    except ValueError:
        rank = len(LABEL_ORDER)
    return (rank, label.endswith(":waiting"), label)


def owning_component(owning_intention) -> str:
    """The component a ticket is berthed at, from its owning_intention address:
    ``cairn/tools/operator_inbox/intention+why.json`` -> ``tools/operator_inbox``;
    ``bin/intention+why.json`` -> ``bin``. No address -> ``unassigned``."""
    if not isinstance(owning_intention, str) or not owning_intention.strip():
        return "unassigned"
    addr = owning_intention.strip()
    if addr.startswith("cairn/"):
        addr = addr[len("cairn/"):]
    for suffix in ("/intention+why.json", "/_charter+why.json"):
        if addr.endswith(suffix):
            addr = addr[:-len(suffix)]
            break
    return addr or "unassigned"


def _ticket_record(path: Path, ticket: dict) -> dict:
    cursor = cursor_of(ticket.get("workflow_and_state", ""))
    return {
        "id": ticket.get("id") or path.stem[:12],
        "title": ticket.get("title", "") or "",
        "date": (ticket.get("date") or ticket.get("cast") or "")[:10],
        "cursor": cursor,
        "label": status_label(cursor),
        "owning_component": owning_component(ticket.get("owning_intention")),
        "node_class": ticket.get("node_class"),
        "source": str(path),
    }


def _scan_tickets(tickets_dir: Path | None) -> list[dict]:
    """THE ONE WALK of tickets/ — every record every report consumes comes from here.
    Sorted by (label priority, date, id), so every surface lists in the same order."""
    d = tickets_dir or TICKETS_DIR
    if not d.exists():
        return []
    records: list[dict] = []
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            t = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(t, dict) or t.get("role") in ("store-charter", "charter"):
            continue
        if not isinstance(t.get("workflow_and_state"), str):
            continue          # not a boat (the folder's schema doc, a note)
        records.append(_ticket_record(p, t))
    records.sort(key=lambda r: (label_sort_key(r["label"]), r["date"], r["id"]))
    return records


def _by_label(records: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for r in records:            # records arrive in priority order, so the dict does too
        out.setdefault(r["label"], []).append(r["id"])
    return out


# ---------------------------------------------------------------------------
# Readers — each calls the source's own API, never stores.
# ---------------------------------------------------------------------------

def read_troubles(*, path: str | None = None) -> dict:
    from cairn.devices.trouble.trouble import TroubleDevice
    td = TroubleDevice(path)
    live = td.live()
    total = td.all()
    return {"live": live, "live_count": len(live), "total_count": len(total)}


def read_adjudications() -> dict:
    from cairn.machines.skill_block.skill_block import pending_reviews
    pr = pending_reviews()
    return {"findings": pr, "count": len(pr)}


def read_lap(*, adjudications_dir: Path | None = None) -> dict:
    """The 'needs adjudication' lane — things needing a decision before they can
    be anything else. An unresolved item is one whose ``resolved`` is null/absent.
    A malformed item counts as UNRESOLVED (Law 7)."""
    d = adjudications_dir or ADJUDICATIONS_DIR
    if not d.is_dir():
        return {"items": [], "count": 0, "error": None}
    out: list[dict] = []
    bad: list[str] = []
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            bad.append(f"{p.name}: {exc}")
            out.append({"id": p.stem, "what": "UNREADABLE — counts as unresolved",
                        "whose": "?", "blocks": "?"})
            continue
        if not data.get("resolved"):
            out.append(data)
    error = ("unreadable adjudication(s): " + "; ".join(bad)) if bad else None
    return {"items": out, "count": len(out), "error": error}


def read_questions(*, questions_dir: Path | None = None) -> dict:
    d = questions_dir or QUESTIONS_DIR
    if not d.exists():
        return {"open": [], "count": 0}
    items: list[dict] = []
    bad: list[str] = []
    for p in sorted(d.glob("open-*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            bad.append(f"{p.name}: {exc}")
            items.append({"id": p.stem, "question": "UNREADABLE — counts as unresolved",
                          "raised_by": "?"})
            continue
        if not data.get("resolved"):
            items.append(data)
    all_q = sorted(p.stem for p in d.glob("*.json")
                   if not p.stem.startswith("_"))
    error = ("unreadable open question(s): " + "; ".join(bad)) if bad else None
    return {"open": items, "count": len(items), "total": len(all_q), "error": error}


def read_tickets(*, tickets_dir: Path | None = None) -> dict:
    """THE ONE READER of open tickets. Returns
    ``{'records': [ {id, title, date, cursor, label, owning_component, node_class, source} ],
       'by_label': {label: [ids]}, 'total_not_done': n}``
    — non-terminal tickets only, in priority order. The inbox, the codemother
    dashboard and the harbor map all consume these records; none re-derives a label."""
    records = [r for r in _scan_tickets(tickets_dir)
               if r["label"].split(":")[0] not in TERMINAL_STATES]
    return {"records": records, "by_label": _by_label(records),
            "total_not_done": len(records)}


def read_done_tickets(*, tickets_dir: Path | None = None) -> dict:
    """The terminal tickets still living in tickets/ — same records, same labels."""
    records = [r for r in _scan_tickets(tickets_dir)
               if r["label"].split(":")[0] in TERMINAL_STATES]
    return {"records": records, "by_label": _by_label(records), "total": len(records)}


# ---------------------------------------------------------------------------
# MOVED ON — the one reader that answers "has this artifact left its stage?"
# (ticket 3ed960cc402e, Akien 2026-09-07: "once an idea has moved to intention it's
# no long open as an idea. once it's a ticket we don't disply it as an intention
# anymore either. for the operator inbox, it's about things i need to take action on.")
#
# Each stage's door writes its own record and none writes back to the record it
# displaced, so the displacement is DERIVED here from the downstream records, once:
#   - an /intent firing names the idea in answers.from_idea (every firing berths under
#     skill_block's instance — berths/intent, logs/adjudicated/intent,
#     logs/reviewed/intent — one glob covers all three lanes);
#   - a ticket's serialized text carries the stem (linked_ideas, traces_to,
#     intent.from_idea, owning_intention, links, prose — the FIELD NAMES are what
#     drifted last time, so the reader stops caring which field);
#   - the idea record's own acted_on flag (hand-set beside an acted_on_note).
# This reader stores nothing and never writes the idea or intention records — they are
# Akien's verbatim capture and authored text. The inventory of everything on disk is a
# different surface with different display constraints (Akien 2026-09-07); this is
# status reporting.
# ---------------------------------------------------------------------------

_NONE_PREFIX = "none"


def _firings_root(firings_root: Path | None = None) -> Path:
    """Where every /intent firing lands: skill_block's instance root (the parent of its
    berth root, so the swept lanes under logs/ are covered by the same glob)."""
    if firings_root is not None:
        return Path(firings_root)
    from cairn.machines.skill_block.skill_block import berth_root
    return berth_root().parent


def _idea_stem(value: str) -> str:
    return value[:-5] if value.endswith(".json") else value


def ideas_named_by_intent_firings(*, firings_root: Path | None = None) -> set[str]:
    """The idea stems some /intent firing took up (answers.from_idea), across every lane."""
    root = _firings_root(firings_root)
    named: set[str] = set()
    if not root.exists():
        return named
    for p in root.glob("**/intent/*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        fi = (d.get("answers") or {}).get("from_idea") if isinstance(d, dict) else None
        if isinstance(fi, str) and fi and not fold(fi).startswith(_NONE_PREFIX):
            named.add(_idea_stem(fi.strip()))
    return named


def _ticket_texts(tickets_dir: Path | None = None) -> list[str]:
    td = tickets_dir or TICKETS_DIR
    if not td.exists():
        return []
    out: list[str] = []
    for p in td.glob("*.json"):
        if p.name.startswith("_"):
            continue
        try:
            out.append(p.read_text(encoding="utf-8"))
        except OSError:
            continue
    return out


def stems_cited_by_tickets(stems, *, tickets_dir: Path | None = None) -> set[str]:
    """Which of ``stems`` appear anywhere in some ticket's serialized text."""
    texts = _ticket_texts(tickets_dir)
    return {s for s in stems if any(s in t for t in texts)}


def moved_on(stems, *, tickets_dir: Path | None = None,
             firings_root: Path | None = None,
             acted_on: set[str] | None = None) -> dict[str, list[str]]:
    """{stem: [reasons]} for every stem that has moved on; a stem with no reason is
    absent from the result, which is what 'open' means. The three voices are OR'd."""
    named = ideas_named_by_intent_firings(firings_root=firings_root)
    cited = stems_cited_by_tickets(stems, tickets_dir=tickets_dir)
    out: dict[str, list[str]] = {}
    for s in stems:
        reasons = []
        if s in named:
            reasons.append("an /intent firing names it")
        if s in cited:
            reasons.append("a ticket cites it")
        if acted_on and s in acted_on:
            reasons.append("its record carries acted_on")
        if reasons:
            out[s] = reasons
    return out


def read_intentions(*, intentions_dir: Path | None = None,
                    tickets_dir: Path | None = None) -> dict:
    """The OPEN intentions: I-*.md that no ticket cites. An intention with a ticket has
    moved on and is not reported here (Akien 2026-09-07)."""
    d = intentions_dir or INTENTIONS_DIR
    if not d.exists():
        return {"count": 0, "items": [], "moved_on": 0}
    stems = sorted(p.stem for p in d.glob("I-*.md"))
    gone = stems_cited_by_tickets(stems, tickets_dir=tickets_dir)
    items = [s for s in stems if s not in gone]
    return {"count": len(items), "items": items, "moved_on": len(gone)}


def read_ideas(*, ideas_dir: Path | None = None,
               tickets_dir: Path | None = None,
               firings_root: Path | None = None) -> dict:
    """The OPEN ideas: records that no /intent firing names, no ticket cites, and that
    carry no acted_on. Everything else has moved on and is not reported here."""
    d = ideas_dir or IDEAS_DIR
    if not d.exists():
        return {"count": 0, "items": [], "moved_on": 0}
    records: dict[str, dict] = {}
    for p in sorted(d.glob("*.json")):
        if p.stem.startswith("_"):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict):
            records[p.stem] = data
    acted = {s for s, r in records.items() if r.get("acted_on") is True}
    gone = moved_on(list(records), tickets_dir=tickets_dir,
                    firings_root=firings_root, acted_on=acted)
    items = [{
        "id": stem,
        "author": data.get("author", "?"),
        "prose_prefix": (data.get("prose", "") or "")[:80],
    } for stem, data in records.items() if stem not in gone]
    return {"count": len(items), "items": items, "moved_on": len(gone)}


def read_email() -> dict:
    """Undelivered bus messages — a live measurement, never stored."""
    try:
        from cairn.devices.cairn.machines.bus.bus import BusDevice
        bus = BusDevice()
        waiting = bus.undelivered(limit=10000)
    except Exception:
        return {"count": 0, "note": "bus unavailable"}
    if not waiting:
        return {"count": 0}
    by_addressee: dict[str, int] = {}
    for env in waiting:
        addr = env.get("addressee", "?")
        by_addressee[addr] = by_addressee.get(addr, 0) + 1
    return {"count": len(waiting), "by_addressee": by_addressee}


def gather_all(**kw) -> dict:
    return {
        "troubles": read_troubles(path=kw.get("troubles_dir")),
        "email": read_email(),
        "adjudications": read_adjudications(),
        "lap": read_lap(adjudications_dir=kw.get("adjudications_dir")),
        "questions": read_questions(questions_dir=kw.get("questions_dir")),
        "design": {},
        "tickets": read_tickets(tickets_dir=kw.get("tickets_dir")),
        "intentions": read_intentions(intentions_dir=kw.get("intentions_dir"),
                                      tickets_dir=kw.get("tickets_dir")),
        "ideas": read_ideas(ideas_dir=kw.get("ideas_dir"),
                            tickets_dir=kw.get("tickets_dir"),
                            firings_root=kw.get("firings_root")),
    }


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def _line(width: int = 76) -> str:
    return "=" * width


def _section_line(title: str, width: int = 76) -> str:
    dashes = "-" * (width - len(title) - 4)
    return f"-- {title} {dashes}"


def _wrap(text: str, indent: str = "  ", width: int = 76) -> str:
    out, line = [], indent
    for word in str(text).split():
        if len(line) + len(word) + 1 > width and line.strip():
            out.append(line.rstrip())
            line = indent + word + " "
        else:
            line += word + " "
    if line.strip():
        out.append(line.rstrip())
    return "\n".join(out)


def format_ticket_row(record: dict, indent: str = "    ") -> str:
    """THE TICKET ATOM every report prints: date, label, id, title — one shape, one
    label. The dashboard and the harbor map call this; they do not compose their own."""
    return (f"{indent}{record.get('date', ''):<12s}{record.get('label', UNPARSED):<20s}"
            f"{(record.get('id') or '?')[:12]:<14s}{record.get('title', '')}")


def format_summary(data: dict) -> str:
    """One-line summary of live state — the shape the receipt carries."""
    troubles = data["troubles"]
    adjudications = data["adjudications"]
    questions = data["questions"]
    tickets = data["tickets"]
    ideas = data["ideas"]
    lap = data.get("lap", {"count": 0})

    parts = []
    if troubles["live_count"]:
        parts.append(f"{troubles['live_count']} live trouble(s)")
    else:
        parts.append("0 live troubles")
    parts.append(f"{adjudications['count']} artifact(s) awaiting review")
    parts.append(f"{questions['count']} open question(s)")

    # Every label, in priority order, summing to the total — no 'other' bucket.
    # (Measured 2026-09-06: the header said 'other 39' against its own listing.)
    state_parts = [f"{label} {len(ids)}" for label, ids in tickets["by_label"].items() if ids]
    if state_parts:
        parts.append(f"{tickets['total_not_done']} tickets ({', '.join(state_parts)})")
    else:
        parts.append(f"{tickets['total_not_done']} tickets")

    parts.append(f"{ideas['count']} open idea(s)")
    return " | ".join(parts)


def format_inbox(data: dict) -> str:
    lines: list[str] = []
    troubles = data["troubles"]
    adjudications = data["adjudications"]
    questions = data["questions"]
    tickets = data["tickets"]
    intentions = data["intentions"]
    ideas = data["ideas"]
    email = data["email"]
    lap = data.get("lap", {"items": [], "count": 0, "error": None})

    by_label = tickets["by_label"]
    thinkme = [r for r in tickets["records"] if r["label"].split(":")[0] == "THINKME"]

    lines.append("")
    lines.append(_line())
    lines.append("                    OPERATOR INBOX")
    lines.append(_line())
    lines.append("")

    # Summary line
    lines.append("  " + format_summary(data))
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
        lines.append(f"    {email['count']} undelivered message(s)")
        for addr, n in sorted((email.get("by_addressee") or {}).items(),
                               key=lambda x: -x[1]):
            lines.append(f"      {addr}: {n}")
        lines.append("")

    # ARTIFACT REVIEWS
    if adjudications["count"] == 0:
        lines.append("  ARTIFACT REVIEWS: 0 awaiting review")
    else:
        lines.append("")
        lines.append(_section_line(f"ARTIFACTS AWAITING REVIEW ({adjudications['count']})"))
        lines.append("")
        for f in adjudications["findings"]:
            bid = (f.get("berth_id") or f.get("id") or "?")[:12]
            skill = f.get("skill", f.get("block", "?"))
            when = (f.get("when", "") or "")[:19]
            bullets = f.get("bullets", [])
            if not isinstance(bullets, list):
                bullets = (f.get("data", {}) or {}).get("bullets", [])
            title = f.get("title", "")
            lines.append(f"    {bid}  [{skill}]  {title or when}")
            if not title:
                for b in bullets[:2]:
                    lines.append(f"        {b.get('text', '')[:90]}")
        lines.append(f"  review with: cairn review <id> \"your words\"")
        lines.append(f"  deep view:   cairn operator show artifact <id>")
        lines.append("")

    # THE LAP
    if lap["error"]:
        lines.append(f"  !! {lap['error']}")
    if lap["count"]:
        lines.append("")
        lines.append(_section_line(f"NEEDS ADJUDICATION ({lap['count']})"))
        lines.append("")
        for a in lap["items"]:
            lines.append(f"    [{a.get('whose', '?')}] {a.get('id', '?')}")
            what = a.get("what", "<no what recorded>")
            lines.append(f"      {what[:90]}")
            blocks = a.get("blocks")
            if blocks:
                lines.append(f"      blocks: {blocks}")
        lines.append("")

    # QUESTIONS
    if questions["count"] == 0:
        lines.append("  QUESTIONS: 0 open")
    else:
        lines.append("")
        lines.append(_section_line(f"QUESTIONS FOR OPERATOR ({questions['count']})"))
        lines.append("")
        for q in questions["open"]:
            qid = q.get("id", "?") if isinstance(q, dict) else str(q)
            lines.append(f"    {qid}")
        lines.append("")

    # DESIGN (THINKME tickets — not yet designed, need operator input)
    if not thinkme:
        lines.append("  DESIGN: 0 tickets at THINKME")
    else:
        lines.append("")
        lines.append(_section_line(f"DESIGN NEEDING OPERATOR ATTENTION ({len(thinkme)})"))
        lines.append("")
        for r in thinkme:
            lines.append(format_ticket_row(r))
        lines.append("")

    # TICKETS — every label in priority order (by_label arrives ordered), same
    # tokens the dashboard and the harbor map print for the same tickets.
    lines.append("")
    state_parts = [f"{label} ({len(ids)})" for label, ids in by_label.items() if ids]
    lines.append(f"  TICKETS ({tickets['total_not_done']} not done): "
                 + " | ".join(state_parts))

    # IDEAS
    lines.append("")
    lines.append(_section_line(
        f"IDEAS ({ideas['count']} open, not yet at intent; "
        f"{ideas.get('moved_on', 0)} moved on)"))
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


# ---------------------------------------------------------------------------
# Artifact deep view
# ---------------------------------------------------------------------------

def show_artifact(id_prefix: str) -> str:
    """Show a pending artifact or ticket by id prefix."""
    from cairn.machines.skill_block.skill_block import pending_reviews, read_berth
    pending = pending_reviews()
    id_prefix = fold(id_prefix)   # ids are system-minted lowercase hex; his prefix folds
    matches = [p for p in pending if p["berth_id"].startswith(id_prefix)]

    if matches:
        if len(matches) > 1:
            lines = [f"ambiguous — {len(matches)} match {id_prefix!r}:"]
            for m in matches:
                lines.append(f"  [{m['skill']}] {m['berth_id']}")
            return "\n".join(lines)
        hit = matches[0]
        berth_path = Path(hit["path"])
        doc = read_berth(berth_path)
        if doc is None:
            return f"berth file unreadable: {berth_path}"
        return _format_artifact(doc, berth_path)

    ticket_matches = [p for p in sorted(TICKETS_DIR.glob("*.json"))
                      if not p.name.startswith("_")
                      and p.name.startswith(id_prefix)]
    if ticket_matches:
        if len(ticket_matches) > 1:
            lines = [f"ambiguous — {len(ticket_matches)} tickets match {id_prefix!r}:"]
            for p in ticket_matches:
                lines.append(f"  {p.stem}")
            return "\n".join(lines)
        path = ticket_matches[0]
        try:
            doc = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return f"ticket file unreadable: {path}"
        return _format_ticket(doc, path)

    return f"no pending artifact or ticket matches {id_prefix!r}"


def _format_artifact(doc: dict, path: Path) -> str:
    lines: list[str] = []
    width = 76

    skill = doc.get("skill", "?")
    bid = doc.get("finding_id", "?")
    when = (doc.get("when", "") or "")[:19]
    exit_val = doc.get("exit", "?")

    title = doc.get("title", "")

    lines.append("=" * width)
    lines.append(f"  ARTIFACT: [{skill}] {bid}")
    if title:
        lines.append(f"  {title}")
    lines.append(f"  when: {when}   exit: {exit_val}")
    lines.append(f"  path: {path}")
    lines.append("=" * width)
    lines.append("")

    # Bullets
    bullets = doc.get("bullets", [])
    if bullets:
        lines.append("BULLETS:")
        for b in bullets:
            lines.append(f"  [{b.get('stratum', '?')}] {b.get('text', '')}")
        lines.append("")

    # Answers — the substantive content
    answers = doc.get("answers", {})
    if answers:
        lines.append("ANSWERS:")
        for key in sorted(answers.keys()):
            val = answers[key]
            lines.append(f"  {key}:")
            if isinstance(val, str):
                lines.append(_wrap(val, "    ", width))
            elif isinstance(val, dict):
                for k2, v2 in val.items():
                    lines.append(f"    {k2}:")
                    lines.append(_wrap(str(v2), "      ", width))
            elif isinstance(val, list):
                for item in val:
                    lines.append(_wrap(f"· {item}", "    ", width))
            else:
                lines.append(f"    {val}")
            lines.append("")

    # Trace
    trace_id = doc.get("trace_id")
    if trace_id:
        lines.append(f"  trace_id: {trace_id}")

    lines.append("")
    return "\n".join(lines)


def _format_ticket(doc: dict, path: Path) -> str:
    lines: list[str] = []
    width = 76
    tid = doc.get("id", "?")
    title = doc.get("title", doc.get("slug", "?"))
    node_class = doc.get("node_class", "?")
    ws = doc.get("workflow_and_state", "")

    lines.append("=" * width)
    lines.append(f"  TICKET: {tid}")
    lines.append(f"  {title}")
    lines.append(f"  class: {node_class}   state: {ws[:60]}")
    lines.append(f"  path: {path}")
    lines.append("=" * width)
    lines.append("")

    for field in ("intention", "what", "why", "how"):
        val = doc.get(field)
        if val:
            lines.append(f"{field.upper()}:")
            lines.append(_wrap(str(val), "  ", width))
            lines.append("")

    falsifier = doc.get("falsifier")
    if falsifier:
        lines.append("FALSIFIER:")
        if isinstance(falsifier, dict):
            for k, v in falsifier.items():
                if v:
                    lines.append(f"  {k}: {v}")
        else:
            lines.append(_wrap(str(falsifier), "  ", width))
        lines.append("")

    deps = doc.get("dependencies", [])
    if deps:
        lines.append("DEPENDENCIES:")
        for d in deps:
            lines.append(_wrap(f"· {d}", "  ", width))
        lines.append("")

    ms = doc.get("measurements_since_cast", [])
    if ms:
        lines.append("MEASUREMENTS:")
        for m in ms[-5:]:
            lines.append(_wrap(f"· {m}", "  ", width))
        lines.append("")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def build_inbox(**kw) -> str:
    return format_inbox(gather_all(**kw))


USAGE = """usage: cairn operator <command>

commands:
  show inbox              full operator inbox
  show inbox --summary    one-line summary only
  show artifact <id>      deep view of a pending artifact or ticket (id prefix match)
"""


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])

    if not args:
        print(build_inbox())
        return 0

    if is_word(args[0], "show"):  # system words fold (ruled 2026-09-07)
        if len(args) < 2:
            print(USAGE)
            return 2
        target = fold(args[1])

        if target == "inbox":
            if any(is_word(a, "--summary") for a in args):
                data = gather_all()
                print(format_summary(data))
            else:
                print(build_inbox())
            return 0

        if target == "artifact":
            if len(args) < 3:
                print("usage: cairn operator show artifact <id-prefix>",
                      file=sys.stderr)
                return 2
            result = show_artifact(args[2])
            print(result)
            return 0

        print(f"unknown target: {target!r}\n\n{USAGE}", file=sys.stderr)
        return 2

    # Bare invocation with no subcommand — show the inbox
    if len(args) == 1 and is_word(args[0], "inbox"):
        print(build_inbox())
        return 0

    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
