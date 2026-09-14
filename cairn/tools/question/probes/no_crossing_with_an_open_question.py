"""WATCHME probe: a_ticket_with_an_open_question_cannot_cross_to_buildme.

The question door's whole claim is that a decision Akien has not made yet HOLDS the build:
the BUILDME entry lane ``the_ticket_has_every_answer_it_needs`` refuses the crossing while
an unresolved question cites the ticket. This probe measures that claim in the wild rather
than in the proof — over every BUILDME crossing journaled in class-space since the gate
exists, and over every answer's caller class in the questions store.

The measurement, from the ticket's watchme (9adc6fddf185): for each ``history.json`` entry
whose ``to`` is BUILDME and whose ``at`` is after the gate's birth, count the questions
bound to that ticket that were still unresolved AT THAT MOMENT (unresolved now, or
answered after the crossing). FIRES on the first crossing that went through with one
standing — the WRONG-INTENT clause. ENOUGH once 20 tickets have crossed clean AND at least
5 answers spawned questions (the loop went around at least once outside the proof).
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from cairn.tools.base.probe import Probe
from cairn.tools.question import question as Q

GATE_BORN = "2026-09-14T00:00:00"
ENOUGH_CROSSINGS = 20
ENOUGH_SPAWNED = 5
_REPO = Path(__file__).resolve().parents[4]


def _crossings() -> list[dict]:
    out = []
    for h in _REPO.rglob("history.json"):
        if "__pycache__" in h.parts or ".git" in h.parts:
            continue
        try:
            entries = json.loads(h.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(entries, list):
            continue
        for e in entries:
            if isinstance(e, dict) and e.get("to") == "BUILDME" and (e.get("at") or "") >= GATE_BORN:
                out.append({"ticket": e.get("ticket"), "at": e.get("at"), "history": str(h.relative_to(_REPO))})
    return out


def _measure(context: dict) -> dict:
    questions = Q._all()
    by_ticket: dict = collections.defaultdict(list)
    for q in questions:
        by_ticket[q.get("ticket")].append(q)
    crossings = _crossings()
    leaked = []
    for c in crossings:
        standing = [q["id"] for q in by_ticket.get(c["ticket"], [])
                    if not q.get("resolved") or (q.get("answered_at") or "") > (c["at"] or "")]
        c["open_at_crossing"] = len(standing)
        if standing:
            leaked.append(dict(c, questions=standing))
    answered = [q for q in questions if q.get("resolved")]
    classes: collections.Counter = collections.Counter(
        (q.get("answered_by") or "?").rsplit(" ", 1)[-1] for q in answered)
    depth: collections.Counter = collections.Counter()
    for q in questions:
        d, cur, seen = 0, q, set()
        while cur.get("born_of") and cur["born_of"] not in seen:
            seen.add(cur["born_of"])
            d += 1
            cur = next((p for p in questions if p.get("id") == cur["born_of"]), {})
        depth[d] += 1
    context.update({
        "crossings": len(crossings), "leaked": leaked,
        "answers": len(answered), "answer_classes": dict(classes),
        "with_spawned": sum(1 for q in answered if Q.spawned_of(q)),
        "spawned_depth": dict(depth),
    })
    return context


def _trigger(now, context: dict) -> bool:
    _measure(context)
    return bool(context["leaked"])


def _carry(context: dict) -> dict:
    if "crossings" not in context:
        _measure(context)
    n = len(context["leaked"])
    return {
        "crossings": context["crossings"], "leaked": context["leaked"][:20],
        "answers": context["answers"], "answer_classes": context["answer_classes"],
        "with_spawned": context["with_spawned"], "spawned_depth": context["spawned_depth"],
        "finding": (
            "%d BUILDME crossing(s) went through while a question on the ticket stood open — "
            "the gate the_ticket_has_every_answer_it_needs did not hold; the WRONG-INTENT "
            "clause of ticket 9adc6fddf185" % n
        ) if n else (
            "every one of %d BUILDME crossings since the gate had no open question standing "
            "(%d answers, %d that spawned questions)" % (context["crossings"], context["answers"],
                                                   context["with_spawned"])
        ),
    }


def _enough(context: dict) -> bool:
    if "crossings" not in context:
        _measure(context)
    return (not context["leaked"] and context["crossings"] >= ENOUGH_CROSSINGS
            and context["with_spawned"] >= ENOUGH_SPAWNED)


PROBE = Probe(
    why="'until you have all the answers you need' is a crossing gate now, and a gate that "
        "lets one through with a question standing is the wrong intent; this counts the "
        "crossings and the answers in the wild so the claim is measured, not assumed.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)
