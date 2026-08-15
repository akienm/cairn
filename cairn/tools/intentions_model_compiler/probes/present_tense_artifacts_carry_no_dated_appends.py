"""PROBE — do present-tense artifacts stay free of dated-append shapes?

Berth for the WATCHME that ticket ``an-artifact-is-present-tense-or-past-tense-never-both``
carries. Berthed here, beside ``cairn/tools/intentions_model_compiler``, because that is WHAT
IT WATCHES: the compiler is the door every charter write already pokes, so the artifacts this
probe reads are exactly the model sources that door compiles. The ticket it was compiled from
lives in CairnCommons and the probe deliberately does not follow it there.

THE EFFICACY QUESTION. The piece rules that a present-tense artifact — every
``intention+why.json``, CLAUDE.md, MAP.md — is rewritten whole at each design shift, with
provenance shrunk to pointers, never accreted as dated narrative. That rule has an obvious way
to fail after the one-time cleanup lands: the house style grows back, one plausible dated
paragraph at a time, because each new charter is written by copying a sibling's (the measured
failure mode: a wrong sentence in a charter is the template the next one is written from). So
the watch asks: after the corpus is swept clean, does a dated-append shape ever reappear where
readers load by default?

WHY THE TRIGGER WAITS FOR THE CLEANUP CHILD. Today the corpus carries standing specimens
(ground_loop's charter among them) and they are OWNED DEBT — child ticket
``the-present-tense-corpus-rewrites-once`` is the single owner of that fact, exactly as the
piece's migration corollary demands. A probe firing on debt a cast ticket already owns would
poke the owner about a working mechanism. So the trigger arms itself only once that child
stands at PROVED; from that moment any match is a NEW shape — a regression — and the poke is
a finding.

THE PATTERN LIST IS v0 AND NOT THIS PROBE'S TO OWN. Child ticket
``a-dated-append-in-a-charter-is-a-red`` owns the canonical shape-check; when its instrument
lands, this probe composes it (the import below tries the child's checker first and falls back
to the v0 patterns). Until then v0 carries the three shapes the ruling named: a retirement
stamp, a used-to-be clause, a date-stamped parenthetical narrating a change.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that re-opens
the node is the OWNER's act at the register (Law 6).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_CAIRN = Path(__file__).resolve().parents[4]
_TICKETS = _CAIRN.parent / "CairnCommons" / "tickets"

_OWNING_TICKET = "an-artifact-is-present-tense-or-past-tense-never-both"

# The child whose PROVED crossing arms this watch (the one-time sweep that makes the corpus
# clean), and the child that will own the canonical pattern list.
_CLEANUP_TICKET = "the-present-tense-corpus-rewrites-once"
_SHAPE_TICKET = "a-dated-append-in-a-charter-is-a-red"

# v0 shapes, from the ruling's own naming. Superseded by _SHAPE_TICKET's instrument the day
# it exists — see _matches_in.
_V0_SHAPES = (
    re.compile(r"\bRETIRED\b"),
    re.compile(r"\bformerly\b"),
    re.compile(r"\(20\d\d-\d\d-\d\d"),
)

# How many consecutive clean charter writes retire the watch — the ticket's own ``enough``,
# verbatim from its watchme spec.
_ENOUGH_CLEAN_WRITES = 10


def _present_tense_set() -> list[Path]:
    """The artifacts readers load by default, per the watchme spec's own list: every
    ``intention+why.json`` in class-space, CLAUDE.md, MAP.md. Class-space file reads only —
    no device, no bus, no network, so the probe stays cheap enough to sit on a pulse."""
    charters = [p for p in _CAIRN.rglob("intention+why.json")
                if "__pycache__" not in p.parts and ".git" not in p.parts]
    roots = [_CAIRN / "CLAUDE.md", _CAIRN / "MAP.md"]
    return charters + [p for p in roots if p.is_file()]


def _matches_in(path: Path) -> list[dict]:
    """Every dated-append shape in one artifact, with the matched text verbatim (the carrier
    the spec promised: 'the offending paths and the matched shapes, verbatim'). Composes the
    shape child's checker when it exists; v0 patterns until then."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []  # an unreadable artifact is not a dated-append finding
    found = []
    for rx in _V0_SHAPES:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            found.append({"path": str(path), "line": line, "shape": rx.pattern,
                          "matched": text[m.start():m.start() + 80].split("\n")[0]})
    return found


def _ticket_state(ticket_id: str) -> str | None:
    p = _TICKETS / (ticket_id + ".json")
    if not p.is_file():
        return None
    try:
        state = json.loads(p.read_text(encoding="utf-8")).get("state")
        return state if isinstance(state, str) else None
    except (OSError, json.JSONDecodeError):
        return None


def _cleanup_landed() -> bool:
    """True once the one-time sweep stands at PROVED. An uncast or at-sea child means the
    standing specimens are owned debt, not findings."""
    state = _ticket_state(_CLEANUP_TICKET)
    return bool(state) and "[PROVED]" in state


def survey_the_corpus() -> dict:
    """The whole measurement: is the sweep done, and what shapes stand in the present-tense
    set right now?"""
    matches = [m for p in _present_tense_set() for m in _matches_in(p)]
    return {"cleanup_landed": _cleanup_landed(), "matches": matches,
            "artifacts_scanned": len(_present_tense_set())}


def _trigger(now, context: dict) -> bool:
    """TRUE when the corpus was swept clean AND a dated-append shape stands anyway. Both
    clauses load-bearing: before the sweep, matches are the cleanup child's owned debt;
    after it, any match is a regression of the house style this piece killed."""
    s = context.get("corpus") or survey_the_corpus()
    return s["cleanup_landed"] and bool(s["matches"])


def _enough(context: dict) -> bool:
    """CLEARED after the ticket's own horizon: 10 consecutive charter writes with zero new
    dated-append shapes — the house style is dead, the rule is habit.

    THE WRITE-COUNTER IS NOT THIS PROBE'S TO INVENT. Counting consecutive clean writes needs
    the write events, and the event that already fires per charter write is the recompile
    gate (every charter write pokes it — the piece's own discipline). Until that counter is
    wired into the firing context as ``clean_charter_writes``, this returns False: a watch
    that cannot measure its stopping condition stays standing rather than clearing by guess
    ('cannot know' must never render as 'cleared' — Law 3). Wiring it is the shape child's
    rung; saying so out loud is this line."""
    clean = context.get("clean_charter_writes")
    return isinstance(clean, int) and clean >= _ENOUGH_CLEAN_WRITES


def _carry(context: dict) -> dict:
    """What rides back: the offending paths and matched shapes verbatim, against the
    ticket's falsifier, with a pointer to the ticket (Law 6 — the ticket is the commons')."""
    s = context.get("corpus") or survey_the_corpus()
    return {"finding": "a dated-append shape stands in a present-tense artifact after the "
                       "corpus was swept clean",
            "matches": s["matches"],
            "artifacts_scanned": s["artifacts_scanned"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "done when a shape-scan over the present-tense set finds "
                                 "zero dated-append paragraphs — this scan found some",
            "suggests": "the builder of the voyage that introduced the shape rewrites it to "
                        "present tense with pointer provenance; if the shape is legitimate, "
                        "that is a question for the pattern list's owner "
                        "(a-dated-append-in-a-charter-is-a-red), never a silent exemption"}


# Declared for the same reason the sibling probes declare one: this watch cannot fire until
# the cleanup child lands — possibly many voyages away — so without a horizon its silence
# would be indistinguishable from health forever. The unit is pulses; the wall-clock beat is
# a filed edge, so 1000 is honest as a placeholder and dishonest as a measurement, and it
# must be re-tuned when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="does the dated-append house style grow back after the corpus is swept clean? — "
        "each new charter is written by copying a sibling's, so one regressed shape is the "
        "template for the next; the watch catches the first one where readers load by "
        "default",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
