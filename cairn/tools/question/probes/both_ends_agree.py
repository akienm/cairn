"""WATCHME probe: a_question_and_its_ticket_name_each_other.

The links ticket's claim (bc7b64626405) is that the question door writes BOTH ends of the
question<->ticket link in one act, and that an answer's ``spawned`` is a recorded claim the
inspector can check — so the two ends can never disagree in the wild. The proof pins that
over a scratch world; this probe measures it over the live commons, over time: it runs the
build inspector's own ``question_links_agree`` predicate (the sieve IS the measurement, the
probe only counts) and reads the artifact journal for the question events since the build.

FIRES on a lack over a record the door itself wrote (verb ``question`` or ``answer`` in the
journal) — WRONG-INTENT: the door was supposed to make disagreement impossible and produced
one. A lack over a hand-written record (verb ``hand-edit`` or nothing journaled) is the sieve
doing its job, carried but not fired on. ENOUGH once 50 question events have been journaled
with zero lacks AND at least 5 answers recorded a non-empty ``spawned`` — the loop went
around, through the door, outside the proof.
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.artifact import artifact as door
from cairn.tools.base.probe import Probe
from cairn.tools.question import question as Q

BUILD_AT = "2026-09-14T22:38:00"   # the BUILDME crossing of bc7b64626405
ENOUGH_EVENTS = 50
ENOUGH_SPAWNED = 5
_REPO = Path(__file__).resolve().parents[4]


def _events(commons: Path) -> list[dict]:
    """Question events the door journaled since the build: verb question|answer on a
    questions/open-*.json path."""
    out = []
    for e in door.read_journal(commons):
        if (e.get("path") or "").startswith("questions/" + Q.PREFIX) \
                and e.get("verb") in ("question", "answer") and (e.get("at") or "") >= BUILD_AT:
            out.append({"at": e["at"], "verb": e["verb"], "path": e["path"],
                        "caller": (e.get("caller") or {}).get("class")})
    return out


def _measure(context: dict, commons: Path | None = None) -> dict:
    from cairn.machines.build_inspector import inspector as I
    commons = commons or door.roots()["CairnCommons"]
    lacks = I.question_links_agree({"component": "question"}, _REPO / "cairn/tools/question",
                                   commons=commons)
    events = _events(commons)
    door_written = {e["path"].rsplit("/", 1)[-1][:-5] for e in events}
    wrong_intent = [f for f in lacks if f.get("question") in door_written]
    questions = Q._all(commons / "questions")
    spawned = sum(1 for q in questions if q.get("resolved") and Q.spawned_of(q))
    context.update({
        "events": len(events), "answers": sum(1 for e in events if e["verb"] == "answer"),
        "lacks": lacks, "wrong_intent": wrong_intent, "with_spawned": spawned,
        "questions": len(questions),
    })
    return context


def _trigger(now, context: dict) -> bool:
    _measure(context)
    return bool(context["wrong_intent"])


def _carry(context: dict) -> dict:
    if "events" not in context:
        _measure(context)
    n = len(context["wrong_intent"])
    return {
        "events": context["events"], "answers": context["answers"],
        "with_spawned": context["with_spawned"], "questions": context["questions"],
        "lacks": context["lacks"][:20], "wrong_intent": context["wrong_intent"][:20],
        "finding": (
            "%d link(s) the door itself wrote disagree at the two ends — the door was supposed "
            "to make that impossible; the WRONG-INTENT clause of ticket bc7b64626405" % n
        ) if n else (
            "every one of %d question events since the build left both ends agreeing "
            "(%d lacks over hand-written records; %d answers spawned questions)"
            % (context["events"], len(context["lacks"]), context["with_spawned"])
        ),
    }


def _enough(context: dict) -> bool:
    if "events" not in context:
        _measure(context)
    return (not context["lacks"] and context["events"] >= ENOUGH_EVENTS
            and context["with_spawned"] >= ENOUGH_SPAWNED)


PROBE = Probe(
    why="a link with two stored ends can disagree, and the door's whole claim is that it "
        "writes both in one act; this runs the inspector's predicate over the live corpus "
        "and counts the door's own question events so the claim is measured, not assumed.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)
