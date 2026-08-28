"""PROBE — does the ticket corpus get cleaner over time?

Berth for the WATCHME that ticket ``ticket-inspector`` carries. Berthed beside
``cairn/tools/ticket_inspector`` because that is WHAT IT WATCHES: the inspector's
own finding count over CairnCommons/tickets/.

THE EFFICACY QUESTION: are the structural gaps the inspector measures actually closing?
The inspector exists to surface gaps; this probe exists to notice whether those gaps
stay surfaced or actually get fixed. A finding count that never moves is a tool
answering a question nobody acts on.

TRIGGER: fires when the finding count is ABOVE the ``enough`` threshold — i.e. there
are still structural gaps to fix. This is the normal running state for a young corpus.

ENOUGH: clears when the finding count drops below 50 (from 71 at the time of arming)
and stays there. The inspector re-runs every time the probe fires, so the count is
always fresh.

FILES ONLY, by construction: the probe imports the inspector and runs it against the
ticket corpus on disk — no device, no bus, no network.

AUTHORITY: none. This probe deposits and pokes; fixing structural gaps in tickets is
the owner's act (Law 6).
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket
from cairn.tools.ticket_inspector.inspector import inspect_corpus

_OWNING_TICKET = "ticket-inspector"
_ENOUGH_THRESHOLD = 50


def _run_inspector(context: dict) -> dict:
    cached = context.get("corpus")
    if cached:
        return cached
    return inspect_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE when the corpus still has findings above the threshold."""
    result = _run_inspector(context)
    return result["total_findings"] > _ENOUGH_THRESHOLD


def _enough(context: dict) -> bool:
    """CLEARED when the finding count drops below the threshold."""
    result = _run_inspector(context)
    return result["total_findings"] < _ENOUGH_THRESHOLD


def _carry(context: dict) -> dict:
    result = _run_inspector(context)
    total = result["total_findings"]
    checked = result["tickets_checked"]
    clean = result["clean"]
    by_check = result["by_check"]

    if total >= _ENOUGH_THRESHOLD:
        finding = (f"{total} findings across {checked} tickets "
                   f"({clean} clean) — still above {_ENOUGH_THRESHOLD}")
    else:
        finding = (f"{total} findings across {checked} tickets "
                   f"({clean} clean) — below {_ENOUGH_THRESHOLD}, clearing")

    return {
        "finding": finding,
        "counts": {
            "total_findings": total,
            "tickets_checked": checked,
            "clean": clean,
            "with_findings": result["with_findings"],
            "by_check": by_check,
        },
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's falsifier includes: 'a ticket at BUILDME "
                             "with no how field passes silently' — the inspector "
                             "surfaces this and the probe measures whether the count "
                             "of such findings is decreasing",
        "suggests": ("read the inspector's by_check breakdown — the largest category "
                     "is the one to fix first"),
    }


_HORIZON = 1000

PROBE = Probe(
    why="does the ticket corpus get structurally cleaner over time? — the inspector "
        "surfaces gaps, and a gap that stays surfaced but never fixed is a tool "
        "answering a question nobody acts on",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps(_carry({}), indent=2, default=str))
