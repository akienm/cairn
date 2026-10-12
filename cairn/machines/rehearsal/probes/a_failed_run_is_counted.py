"""WATCHME probe: a_failed_run_is_counted.

Ticket ba4166fe51c4's claim is that a rehearsal pass whose reader never returns a tree is a
RUN: rehearse() writes a ran:false record through the artifact door, passes_since_clean counts
it, and nothing reads it as clean or as a gap list. This probe counts those records over the
live commons — it never calls the reader.

FIRES once the first ran:false record lands on a live ticket (one whose ticket file is in the
commons — a proof's scratch ticket never is). FAILS when any such record is MISREAD: written
clean, carrying gaps, or named by its ticket's rehearsal pointer (the lane would then stand on a
pass that never ran). ENOUGH at ten ran:false records on live tickets with none misread. Nexus:
the machine's own record of what a pass costs, per the ticket's watchme spec.
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.artifact import artifact as door
from cairn.tools.base.probe import Probe, watch_carry

_TICKET_ID = "ba4166fe51c4"

ENOUGH_FAILED = 10


def _pointer(ticket_path: Path) -> str | None:
    """The record the BUILDME lane would stand on — the latest rehearsal log line's record."""
    from cairn.tools.base import ticket_log
    try:
        lines = ticket_log.read_log(ticket_path, "rehearsal")
    except Exception:  # noqa: BLE001 — an unreadable log names no pointer; the lane reds it itself
        return None
    return lines[-1].get("record") if lines else None


def _measure(context: dict, commons: Path | None = None) -> dict:
    commons = commons or door.roots()["CairnCommons"]
    d = commons / "rehearsals"
    failed, misread = [], []
    for p in sorted(d.glob("*.json")) if d.is_dir() else []:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(rec, dict) or rec.get("ran") is not False:
            continue
        tickets = sorted((commons / "tickets").glob(f"{rec.get('ticket')}-*.json"))
        if not rec.get("ticket") or not tickets:
            continue
        row = {"ticket": rec["ticket"], "record": p.name}
        failed.append(row)
        ptr = _pointer(tickets[0])
        if rec.get("clean") is not False or rec.get("gaps") or (ptr and Path(str(ptr)).name == p.name):
            misread.append(row)
    context.update({"failed": len(failed), "misread": len(misread),
                    "records": failed, "misread_records": misread})
    return context


def _trigger(now, context: dict) -> bool:
    _measure(context)
    return context["failed"] > 0


def _fails(now, context: dict) -> bool:
    if "failed" not in context:
        _measure(context)
    return context["misread"] > 0


def _carry(context: dict) -> dict:
    if "failed" not in context:
        _measure(context)
    n, m = context["failed"], context["misread"]
    return {
        "failed": n, "misread": m, "records": context["records"][:20],
        "misread_records": context["misread_records"][:20],
        "finding": (
            "%d of %d ran:false rehearsal records were misread (clean, carrying gaps, or the "
            "ticket's rehearsal pointer) — ticket ba4166fe51c4's falsifier" % (m, n)
        ) if m else "%d failed-to-run rehearsal pass(es) recorded on live tickets, none misread" % n,
    }


def _enough(context: dict) -> bool:
    if "failed" not in context:
        _measure(context)
    return context["failed"] >= ENOUGH_FAILED and context["misread"] == 0


PROBE = Probe(
    why="a rehearsal pass whose reader failed used to leave no record and no count — about "
        "twenty minutes of runs the record said never happened (Law 7); this counts the "
        "ran:false records that now land, and reds the first one read as clean or as gaps.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "cairn/machines/rehearsal/state.json", "kind": "efficacy"},
    verb="watch",
    carry=watch_carry(_TICKET_ID, _carry, fails=_fails),
    enough=_enough,
    horizon=1000,
)
