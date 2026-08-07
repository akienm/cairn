"""PROBE — do captured ideas get reached for, or does the queue rot?

Berth for the WATCHME that ticket ``an-idea-has-an-address`` carries. Berthed here,
beside ``skills/idea/``, because that is WHAT IT WATCHES; the ticket it was compiled
from lives in CairnCommons and this probe deliberately does not follow it there (the
rule in ``cairn/base/probe.py``: a probe berths with its subject).

THE EFFICACY QUESTION, and why it is the SECOND of the charter's two signals. /idea's
own ``how_it_learns`` names them: an idea /intent routes OUT says something about what
is being captured; an idea that NEVER GETS REACHED FOR says something about whether the
queue is being worked. The first signal rides /intent's own records. The second is this
probe — the charter wrote it as prose ending "NOT-YET: nothing reads it", and this file
is that reader, compiled.

WHY THE CLEAR IS A POPULATION CLAIM AND NOT AN EXISTENCE ONE — the sharpest decision in
this spec, and it is the morning's own lesson applied. "Does capture -> pickup work
end-to-end at all?" was MEASURED LIVE on 2026-08-07: the capture
``2026-08-07-yes-we-need-to-build-out-idea`` was cited by two /intent births within the
hour. An existence clear would therefore be born pre-satisfied — the watch would retire
at the corpus floor without ever being able to bite, which is the guaranteed-to-retire
bug the sibling probe (``does_optional_mean_never_carried``) recorded against itself. So
the settled existence is CITED, not re-watched (Law 1), and what stands is the one
question today's fire could not answer: the RATE — does the queue drain, or accumulate?

TRIGGER AND CLEAR ARE MUTUALLY EXCLUSIVE BY CONSTRUCTION: fire needs unpicked >= floor,
clear needs unpicked < floor — the sibling's clear-before-fire asymmetry cannot be
rebuilt here by drift, only by an edit.

A PICKUP IS A FIRING THAT RODE THE DOOR. A human reading the store directly leaves no
record, so a zero here means "nothing rode the door", never "nothing was read" — the
carry says so rather than letting the sharper reading win by default. And a pickup that
/intent then routed OUT still counts: the idea was REACHED FOR; the kill is /intent's
legal outcome and the first signal's business, not rot.

AUTHORITY: none, by construction. This probe deposits and pokes; acting on a rotting
queue is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.base.probe import Probe, owning_ticket

# Read the live roots the way the components themselves do — env first, default second —
# resolved per call, never captured at import: a probe that froze the path at import
# time would keep reading a root the system had already left. The commons env name is
# the one the recompile gate's proof already uses; no new name is coined.
_COMMONS_ENV = "CAIRN_COMMONS_ROOT"
_BERTH_ENV = "CAIRN_SKILL_BERTHS"
_COMMONS_DEFAULT = Path(__file__).resolve().parents[4] / "CairnCommons"
_BERTH_DEFAULT = Path.home() / ".cairn/devices/skill_block/0/berths"

# The floor on BOTH predicates, one number on purpose. Twelve unpicked captures is a
# pattern, not a lull (at the store's measured cadence — two captures in its first three
# days — that is weeks of standing rot); twelve picked-through-the-door captures is a
# population's worth of evidence that working the queue is a practice, not an accident.
# A HAND-SET PRIOR, named as such on the ticket: the learns-its-gates intention says a
# constant in a gate is a learned value stranded in a head, and this one is an IOU
# against the store's real cadence once the store has one.
_FLOOR = 12


def survey_the_queue() -> dict:
    """Count, over the commons ideas store and /intent's live berths: captures, the ones
    some /intent firing has cited (``answers.from_idea``), and the rotting remainder.
    Reads files only — no device, no bus, no network — so the probe stays cheap enough
    to sit on a pulse.

    An unreadable record is skipped rather than counted as evidence in either direction:
    the counts a probe reports are a claim (Law 3), and a claim resting on a parse
    failure is worse than a smaller n.
    """
    ideas_dir = Path(os.environ.get(_COMMONS_ENV) or _COMMONS_DEFAULT) / "ideas"
    berths = Path(os.environ.get(_BERTH_ENV) or _BERTH_DEFAULT) / "intent"

    captured: list[str] = []
    if ideas_dir.is_dir():
        captured = [p.stem for p in sorted(ideas_dir.glob("*.json"))
                    if not p.name.startswith("_")]

    cited: set[str] = set()
    for p in sorted(berths.glob("*.json")) if berths.is_dir() else []:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        ref = (rec.get("answers") or {}).get("from_idea")
        if not isinstance(ref, str) or ref.lower().startswith("none"):
            continue
        # The field cites an id or a path to the record; either way the record's stem
        # is in it. Matched per capture so a path form and an id form count the same.
        for stem in captured:
            if stem in ref:
                cited.add(stem)

    unpicked = [s for s in captured if s not in cited]
    return {"captured": len(captured), "picked": len(cited),
            "unpicked": len(unpicked), "rotting": unpicked}


def _trigger(now, context: dict) -> bool:
    """TRUE when the rot is a pattern: at least ``_FLOOR`` captures stand uncited. Not
    conditioned on picked==0 — a queue where twelve rot while three get picked is still
    a rotting queue, and the three would mask it."""
    s = context.get("queue") or survey_the_queue()
    return s["unpicked"] >= _FLOOR


def _enough(context: dict) -> bool:
    """CLEARED once working the queue is demonstrated AT SCALE with no standing rot:
    ``_FLOOR`` captures picked up through the door AND fewer than ``_FLOOR`` waiting.
    At that moment the question this watch was carried for — is the queue being
    worked? — is answered on a real population, and a standing watch on a settled
    question is the re-derivation Law 1 refuses. If the practice later decays, that is
    a NEW watch a node carries deliberately, not this one silently resuming."""
    s = context.get("queue") or survey_the_queue()
    return s["picked"] >= _FLOOR and s["unpicked"] < _FLOOR


def _carry(context: dict) -> dict:
    """The datum that rides back: the counts against the ticket's own falsifier, the
    rotting ids BY NAME (a poke that says 'twelve rot' without saying which twelve
    makes the owner re-run the survey, which is the complete-on-first-pass defect),
    and a POINTER to the ticket rather than a copy of it (Law 6)."""
    s = context.get("queue") or survey_the_queue()
    return {"finding": "captured ideas are standing unworked in CairnCommons/ideas/",
            "counts": {k: s[k] for k in ("captured", "picked", "unpicked")},
            "rotting": s["rotting"],
            "ticket": _TICKET,
            "against_falsifier": "a queue that accumulates without draining means the "
                                 "capture door is writing addresses nobody reaches for — "
                                 "the lived symptom /idea exists to close, standing again "
                                 "one step later",
            "suggests": "two readings, and the probe cannot tell them apart: the queue "
                        "is not being worked (work the rotting list, or rule some of it "
                        "dead), or ideas are being consumed OFF-DOOR — read directly and "
                        "acted on without an /intent firing citing them, which no berth "
                        "records. Both are the owner's call, not the probe's."}


_TICKET = owning_ticket("an-idea-has-an-address")

# THE HORIZON, and the residual it does NOT cover — the same tracked debt every probe in
# the roster carries: the unit is PULSES because the shim counts pulses, but nothing
# pulses this shim yet (the wall-clock backing is a filed edge in
# cairn/ground_loop/loop.py), so today the loudness rides the READ-SIDE door
# (``BaseShim.overdue()``) alone. 1000 is honest as a placeholder and dishonest as a
# measurement, and MUST be re-tuned when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="do captured ideas get reached for, or does the queue rot? — the capture door's "
        "whole promise is an address someone later reaches for; a store that only grows "
        "is that promise failing silently. Fires on a standing rot pattern; cleared only "
        "by demonstrated working of the queue at scale.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
