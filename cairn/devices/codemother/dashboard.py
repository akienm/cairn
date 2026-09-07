"""codemother/dashboard.py — the whole coding system at a glance.

The consumer is the operator scanning the full picture. Shows every category
in priority order (troubles → email → review → design → the tickets by status
→ done), each ticket as the standard atom: date, label, id, title.

Reads are from operator_inbox readers — the SINGLE SOURCE of live-state reads
(Law 1). This module formats; it reads nothing of its own and derives no label
of its own: a ticket's status token here is the one ``read_tickets`` gave it,
byte-identical to the inbox and the harbor map (ticket 3feb201c84ea — before
it, this file re-walked tickets/ and re-parsed the cursor a second way).
"""

from __future__ import annotations

from cairn.tools.operator_inbox.inbox import (
    gather_all,
    read_done_tickets,
    format_ticket_row,
)

_LINE = "=" * 76


def format_dashboard(data: dict | None = None, **kw) -> str:
    if data is None:
        data = gather_all(**kw)
    troubles = data["troubles"]
    email = data["email"]
    adjudications = data["adjudications"]
    questions = data["questions"]
    intentions = data["intentions"]
    ideas = data["ideas"]
    tickets = data["tickets"]
    done = read_done_tickets(tickets_dir=kw.get("tickets_dir"))

    records = tickets["records"]
    by_label = tickets["by_label"]

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
        f"{questions['count']} open question(s)",
        f"{tickets['total_not_done']} active ticket(s)",
        f"{done['total']} done",
        f"{ideas['count']} open idea(s)",
    ]
    lines.append("  " + " | ".join(parts))
    lines.append("")

    # 1. Troubles
    if troubles["live_count"]:
        lines.append(f"  TROUBLES ({troubles['live_count']} live):")
        for t in troubles["live"]:
            lines.append(f"    {t.get('id', '?')}  ({t.get('standing', '?')})")
    else:
        lines.append(f"  TROUBLES: 0 live ({troubles['total_count']} exist, all CLEARED)")

    # 2. Email — one line
    lines.append(f"  EMAIL: {email.get('count', 0)} undelivered")

    # 3. Awaiting review — one line, one name
    lines.append(f"  ARTIFACT REVIEWS: {adjudications['count']} awaiting review")

    # 4. Design queue
    lines.append(f"  QUESTIONS: {questions['count']} open")
    thinkme = [r for r in records if r["label"].split(":")[0] == "THINKME"]
    lines.append(f"  DESIGN: {len(thinkme)} tickets at THINKME")

    # 5. Tickets by label, priority order (by_label arrives ordered), the standard atom
    lines.append("")
    by_id = {r["id"]: r for r in records}
    for label, ids in by_label.items():
        if not ids:
            continue
        lines.append(f"  {label} ({len(ids)}):")
        for tid in ids:
            lines.append(format_ticket_row(by_id[tid]))

    # 6. Done (counts only)
    lines.append("")
    done_parts = [f"{label} ({len(ids)})" for label, ids in done["by_label"].items()]
    lines.append(f"  DONE ({done['total']}): " + " | ".join(done_parts))

    # INTENTIONS + IDEAS
    # OPEN counts, not the folder census (ticket 3ed960cc402e, Akien 2026-09-07): an
    # artifact that moved to the next stage stops being reported at the earlier one.
    lines.append(f"  INTENTIONS: {intentions['count']} open (no ticket yet; "
                 f"{intentions.get('moved_on', 0)} moved on)")
    lines.append(f"  IDEAS: {ideas['count']} open (not yet at intent; "
                 f"{ideas.get('moved_on', 0)} moved on)")

    lines.append("")
    lines.append(_LINE)
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    print(format_dashboard())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
