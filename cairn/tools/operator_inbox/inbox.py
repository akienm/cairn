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

from cairn.tools.base.transitions import TERMINAL_STATES

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


def _cursor(state: str) -> str | None:
    if not state:
        return None
    for part in state.split():
        if part.startswith("[") and part.endswith("]"):
            return part.strip("[]")
        if ":" in part:
            base = part.split(":")[0]
            if base.startswith("["):
                return base.strip("[]")
    return None


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
    d = tickets_dir or TICKETS_DIR
    if not d.exists():
        return {"by_state": {}, "total_not_done": 0}
    by_state: dict[str, list[str]] = {}
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            t = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if t.get("role") in ("store-charter", "charter"):
            continue
        state = t.get("workflow_and_state", "")
        cursor = _cursor(state)
        if cursor in TERMINAL_STATES:
            continue
        bucket = cursor or "UNKNOWN"
        by_state.setdefault(bucket, []).append(p.stem)
    total = sum(len(v) for v in by_state.values())
    return {"by_state": by_state, "total_not_done": total}


def read_intentions(*, intentions_dir: Path | None = None) -> dict:
    d = intentions_dir or INTENTIONS_DIR
    if not d.exists():
        return {"count": 0, "items": []}
    items = sorted(p.stem for p in d.glob("I-*.md"))
    return {"count": len(items), "items": items}


def _acted_on_idea_ids(*, tickets_dir: Path | None = None,
                       ideas_dir: Path | None = None) -> set[str]:
    td = tickets_dir or TICKETS_DIR
    id_ = ideas_dir or IDEAS_DIR
    acted: set[str] = set()
    if not td.exists():
        return acted
    all_idea_ids: set[str] = set()
    if id_.exists():
        for p in id_.glob("*.json"):
            if not p.stem.startswith("_"):
                all_idea_ids.add(p.stem)
    for p in td.glob("*.json"):
        try:
            d = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        fi = d.get("from_idea", "")
        if isinstance(fi, str) and fi and not fi.startswith("none"):
            acted.add(fi)
        prov = d.get("provenance", "")
        if isinstance(prov, str):
            for idea_id in all_idea_ids:
                if idea_id in prov:
                    acted.add(idea_id)
    return acted


def read_ideas(*, ideas_dir: Path | None = None,
               tickets_dir: Path | None = None) -> dict:
    d = ideas_dir or IDEAS_DIR
    if not d.exists():
        return {"count": 0, "items": []}
    acted = _acted_on_idea_ids(tickets_dir=tickets_dir, ideas_dir=d)
    items = []
    for p in sorted(d.glob("*.json")):
        if p.stem.startswith("_"):
            continue
        try:
            data = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if p.stem in acted:
            continue
        items.append({
            "id": p.stem,
            "author": data.get("author", "?"),
            "prose_prefix": (data.get("prose", "") or "")[:80],
        })
    return {"count": len(items), "items": items}


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
        "intentions": read_intentions(intentions_dir=kw.get("intentions_dir")),
        "ideas": read_ideas(ideas_dir=kw.get("ideas_dir"),
                            tickets_dir=kw.get("tickets_dir")),
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

    by_state = tickets["by_state"]
    state_parts = []
    for s in ["BUILDME", "PROVEME", "TICKETME", "THINKME"]:
        count = len(by_state.get(s, []))
        if count:
            state_parts.append(f"{s} {count}")
    waiting = sum(len(v) for k, v in by_state.items()
                  if k not in ("BUILDME", "PROVEME", "TICKETME", "THINKME"))
    if waiting:
        state_parts.append(f"other {waiting}")
    if state_parts:
        parts.append(f"{tickets['total_not_done']} tickets ({', '.join(state_parts)})")
    else:
        parts.append(f"{tickets['total_not_done']} tickets")

    parts.append(f"{ideas['count']} idea(s)")
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

    by_state = tickets["by_state"]
    thinkme = by_state.get("THINKME", [])

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
        for t in thinkme:
            lines.append(f"    {t}")
        lines.append("")

    # TICKETS (priority order: design → PROVEME → BUILDME; WATCHMEs omitted)
    _TICKET_PRIORITY = [
        "THINKME", "TICKETME", "TICKETME:waiting",
        "PROVEME", "PROVEME:waiting",
        "BUILDME", "BUILDME:waiting",
    ]
    lines.append("")
    state_parts = []
    watchme_count = 0
    shown_keys: set[str] = set()
    for s in _TICKET_PRIORITY:
        bucket = by_state.get(s, [])
        if bucket:
            state_parts.append(f"{s} ({len(bucket)})")
            shown_keys.add(s)
    for k, v in sorted(by_state.items()):
        if k in shown_keys:
            continue
        if k.startswith("WATCHME"):
            watchme_count += len(v)
            continue
        if v:
            state_parts.append(f"{k} ({len(v)})")
    if watchme_count:
        state_parts.append(f"WATCHME ({watchme_count})")
    lines.append(f"  TICKETS ({tickets['total_not_done']} not done): "
                 + " | ".join(state_parts))

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


# ---------------------------------------------------------------------------
# Artifact deep view
# ---------------------------------------------------------------------------

def show_artifact(id_prefix: str) -> str:
    """Show a pending artifact or ticket by id prefix."""
    from cairn.machines.skill_block.skill_block import pending_reviews, read_berth
    pending = pending_reviews()
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

    if args[0] == "show":
        if len(args) < 2:
            print(USAGE)
            return 2
        target = args[1]

        if target == "inbox":
            if "--summary" in args:
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
    if args == ["inbox"]:
        print(build_inbox())
        return 0

    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
