"""WATCHME probe: raise_rate_falls_as_the_table_grows.

The counting block's whole claim is that (path class, verb, caller class) is the right
prior — that as the table fills, the unseen triple becomes rare. If the raise rate does
not fall as rows fill, the triple is the wrong prior and the block routes back to Akien
with the table (ticket 5a4ec289bf15, WRONG-INTENT clause).

The measurement reads the table the block wrote on the last beat, never the journals:
the block already folded them, and a probe that re-folded would be a second reader of
the same corpus with its own chance to disagree. FIRES on every raise and every 100
post-arming appends — both by comparing the table against the acknowledgement the block
wrote beside it (the ack lags one beat, so each crossing fires exactly once; no poller).
ENOUGH once 1000 appends have landed after arming with the raise rate over the last 200
appends below the rate over the first 200, AND at least one akien-class clearance has
incremented a row. Does not clear on a timer. If the rate does not fall, that is the
finding, and it rides the carry.
"""
from __future__ import annotations

import json

from cairn.machines.counting_block import block
from cairn.tools.base.probe import Probe

ENOUGH_APPENDS = 1000


def _load(name: str) -> dict | None:
    try:
        return json.loads((block.table_dir() / name).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _measure(context: dict) -> dict:
    table = _load(block.TABLE_FILE)
    ack = _load(block.ACK_FILE)
    if table is None:
        context.update({"compiled": False, "raises": 0, "post_appends": 0, "windows": {},
                        "increments": 0, "rows": 0, "entries": 0, "ack": ack})
        return context
    context.update({
        "compiled": True,
        "raises": len(table.get("raises", [])),
        "post_appends": int(table.get("post_appends", 0)),
        "windows": dict(table.get("windows", {})),
        "increments": len(table.get("increments", [])),
        "rows": len(table.get("rows", {})),
        "entries": sum(table.get("compiled_to", {}).values()),
        "raised": [{"triple": r["triple"], "at": r.get("at"), "disposition": r.get("disposition")}
                   for r in table.get("raises", [])],
        "ack": ack,
    })
    return context


def _rates(context: dict) -> tuple[float | None, float | None]:
    """Raises per WINDOW appends over the first window and over the last COMPLETE window."""
    post = context["post_appends"]
    if post < block.WINDOW:
        return None, None
    w = context["windows"]
    first = w.get("0", 0) / block.WINDOW
    last_idx = post // block.WINDOW - 1  # the last window that has all WINDOW appends in it
    last = w.get(str(last_idx), 0) / block.WINDOW
    return first, last


def _trigger(now, context: dict) -> bool:
    _measure(context)
    ack = context.get("ack") or {}
    if not context["compiled"] or not ack:
        return False
    bucket = context["post_appends"] // block.BUCKET
    return context["raises"] > ack.get("raises", 0) or bucket > ack.get("bucket", 0)


def _carry(context: dict) -> dict:
    if "compiled" not in context:
        _measure(context)
    first, last = _rates(context)
    falls = None if first is None else last < first
    return {
        "rows": context["rows"],
        "entries": context["entries"],
        "post_appends": context["post_appends"],
        "raise_rate_per_window": context["windows"],
        "first_window_rate": first,
        "last_window_rate": last,
        "increments": context["increments"],
        "raised": context.get("raised", [])[:50],
        "finding": (
            "the table is not compiled yet" if not context["compiled"] else
            "fewer than %d appends since arming — no window to compare" % block.WINDOW
            if first is None else
            "the raise rate FALLS as the table grows (%.3f → %.3f per append) — the triple is "
            "holding as a prior" % (first, last) if falls else
            "the raise rate does NOT fall as the table grows (%.3f → %.3f per append) — the "
            "triple is the wrong prior; route back to Akien with the table" % (first, last)
        ),
    }


def _enough(context: dict) -> bool:
    if "compiled" not in context:
        _measure(context)
    first, last = _rates(context)
    return (context["post_appends"] >= ENOUGH_APPENDS and first is not None
            and last < first and context["increments"] >= 1)


PROBE = Probe(
    why="the counting block's claim is that (path class, verb, caller class) is the right "
        "prior — that the unseen triple gets rarer as the table fills. This watches the "
        "raise rate per 200 post-arming appends against the first 200, and carries every "
        "raised triple with its disposition, so a rate that does not fall routes the ticket "
        "back to Akien with the table instead of standing as a quiet wrong prior.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)
