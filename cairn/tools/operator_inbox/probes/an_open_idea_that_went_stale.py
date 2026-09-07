"""PROBE — is an idea the inbox still calls OPEN really waiting on Akien?

Berth for the WATCHME(idea-past-idea) that ticket 3ed960cc402e
an-idea-past-idea-is-not-an-open-idea-in-the-inbox carries. Berthed beside
cairn/tools/operator_inbox because that is WHAT IT WATCHES: the one `moved_on` reader
whose three voices (an /intent firing names it, a ticket cites it, its record carries
acted_on) decide which ideas the operator inbox and the codemother dashboard report as
open.

THE MEASUREMENT. Re-read the open ideas through `read_ideas` now, and for every open
idea whose stem date is older than fourteen days, record what each of the three voices
answered. A stale open idea is one of two things: an idea really waiting on him (the
inbox is right), or an idea that moved on through a fourth door the reader does not hear
yet (the inbox is wrong the way it was wrong at 65) — the falsifier of the ticket:
"an idea is reported open after an /intent firing, a ticket or acted_on has taken it up".
The probe cannot tell the two apart alone; it carries the stems and the voices so the
reader of the finding can, and stops on the first stale one.

TRIGGER: two consecutive beats with at least one stale open idea (patience 2, so a
single beat that sees an idea captured 14 days ago and taken up today does not bite).

ENOUGH: fourteen consecutive clean beats, or the first bite — which names the stems and
stops.

CARRIER: a verdict artifact against the ticket's falsifier: open count, moved_on count,
the stale stems, and per stem the three voices' answers.

AUTHORITY: none. This probe deposits and pokes; codemother, as owner of the care of the
code, reads it (Law 6).
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "3ed960cc402e"
_STALE_DAYS = 14
_PATIENCE = 2
_ENOUGH_CLEAN = 14
_STEM_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-")


def _stem_date(stem: str) -> date | None:
    m = _STEM_DATE.match(stem)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def survey(today: date | None = None) -> dict:
    """What the reader says now: the open ideas, the stale ones, the voices per stem."""
    from cairn.tools.operator_inbox.inbox import (
        read_ideas, ideas_named_by_intent_firings, stems_cited_by_tickets)
    today = today or datetime.now(timezone.utc).date()
    result = read_ideas()
    open_stems = [i["id"] for i in result["items"]]
    named = ideas_named_by_intent_firings()
    cited = stems_cited_by_tickets(open_stems)
    stale = []
    for stem in open_stems:
        d = _stem_date(stem)
        if d is None or (today - d).days <= _STALE_DAYS:
            continue
        stale.append({
            "stem": stem,
            "age_days": (today - d).days,
            "an /intent firing names it": stem in named,
            "a ticket cites it": stem in cited,
            "its record carries acted_on": False,       # open means the reader saw none
        })
    return {
        "open": result["count"],
        "moved_on": result.get("moved_on", 0),
        "stale": stale,
        "would_bite": bool(stale),
    }


def _trigger(now, context: dict) -> bool:
    bites = survey()["would_bite"]
    prev = context.setdefault("previous_bites", [])
    prev.append(bites)
    del prev[:-_PATIENCE]
    consecutive = len(prev) >= _PATIENCE and all(prev)
    context["clean_streak"] = 0 if bites else context.get("clean_streak", 0) + 1
    return consecutive


def _enough(context: dict) -> bool:
    prev = context.get("previous_bites", [])
    if len(prev) >= _PATIENCE and all(prev):
        return True                      # the first bite names itself and stops
    return context.get("clean_streak", 0) >= _ENOUGH_CLEAN


def _carry(context: dict) -> dict:
    s = survey()
    if s["stale"]:
        first = s["stale"][0]
        finding = (f"an idea still reads open after {first['age_days']} days: {first['stem']}"
                   f" ({len(s['stale'])} stale of {s['open']} open)")
        suggests = ("either it is really waiting on Akien, or a door the reader does not hear "
                    "took it up — add that door as a fourth voice of moved_on")
    else:
        finding = f"{s['open']} open ideas, none older than {_STALE_DAYS} days; {s['moved_on']} moved on"
        suggests = "nothing; the three voices cover every door that fired"
    return {
        "finding": finding,
        "measurement": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "an idea is reported open after an /intent firing, a ticket or "
                             "acted_on has taken it up",
        "suggests": suggests,
    }


PROBE = Probe(
    why="an idea past idea is not an open idea in the inbox; an idea that stays open past "
        "two weeks is the reader missing a door, or Akien's real backlog — the probe carries "
        "which, so the inbox never reads 65 again",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "codemother", "kind": "efficacy",
          "falsifier_tooth": "3ed960cc402e: an idea reported open after a firing, a ticket "
                             "or acted_on took it up"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)


if __name__ == "__main__":
    print(json.dumps(survey(), indent=2, default=str))
