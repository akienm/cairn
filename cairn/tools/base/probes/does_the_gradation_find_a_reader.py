"""PROBE — the gradation is emitted at the general level; does anyone ever read it?

Berth for the WATCHME that ticket ``banding-berths-at-the-general-level`` carries.
Berthed beside ``cairn/tools/base`` because that is WHAT IT WATCHES: the nest primitive
lives at ``cairn/tools/base/nest.py``, and the one way the ruling
(2026-08-07-the-nest-is-block-general) fails silently is generality standing
DECORATIVE — the lift landed, build_inspector rides it as tenant #1, gradations are
produced at the general address on every inspection, and no second carrier ever
arrives: no second tenant shaking its own nest, no consumer reading the gradation.
The ruling's stated point was "the general level, where a consumer can read the
gradation"; the named candidate consumer is the sieve-learning nexus (Akien,
2026-08-07: "ever learning... we can keep making it smarter"). This probe is the
standing pressure toward building that reader.

THE EFFICACY QUESTION: inspections accumulate for FREE — every gated PROVEME
crossing journals a ``build_gate`` annotation, each one a gradation emitted — while
a second carrier is the opposite: somebody must import the general berth on
purpose. Counting the free half against the deliberate half is the honest measure
(the same shape as ``a_pickup_is_witnessed`` beside this one).

THE HOME-FIELD EXCLUSION, third appearance and now the standard shape at this
address: cairn/tools/base's own proof carries a toy second tenant importing
``cairn.tools.base.nest`` — load-bearing there precisely BECAUSE it exercises the berth —
and build_inspector is tenant #1 whose rewire is the lift itself. Counting either
would clear the watch at birth. The question is whether anyone ELSE ever carries
it; the author and the first tenant are not evidence for that.

CARRIERS ARE READ BY IMPORT, NEVER BY MENTION: the corpus taught twice (import_
sieve's header) that grepping text fires on honest docstrings — this very file
names ``cairn.tools.base.nest`` a dozen times and carries it zero. The census parses
``ast`` import nodes only.

FILES ONLY, by construction: class-space ``.py`` and ``history.json`` files — no
device, no bus, no network — cheap enough to sit on a pulse.

AUTHORITY: none. This probe deposits and pokes; acting on the finding — building
the nexus reader, or back-edging the ticket because the lift was premature — is the
owner's call at the register (Law 6).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_REPO_ROOT = Path(__file__).resolve().parents[4]

# The sample size below which silence cannot be judged: a couple of inspections with
# no reader is a young berth; twelve gradations emitted and not one carrier is a
# pattern. Same floor, same reasoning, as both siblings at this address — and a
# hand-set constant is a learns-its-gates IOU, named in the owning ticket's horizon.
_ENOUGH = 12

_OWNING_TICKET = "banding-berths-at-the-general-level"

# THE ERA FLOOR — the denominator counts gradations emitted AT THE GENERAL LEVEL, so
# it starts when the lift landed. Before this moment a build_gate record's gradation
# was produced by the tenant-local shake; counting those would fire the trigger at the
# probe's own birth (33 stood on the day it was written), poking the owner about a
# berth nobody had had one pulse's time to reach. The newest pre-lift record stood at
# 2026-08-07T13:28:21; the first general-level gradation is this ticket's own PROVEME
# crossing. A date is provenance here (when the berth landed — a fact), not a tunable.
_GENERAL_ERA = "2026-08-07T14:30:00"

# Home-field, both of them: base authored the berth (its proof's toy tenant imports
# it), build_inspector is tenant #1 (its rewire IS the lift).
_EXCLUDED = (Path(__file__).resolve().parents[1],
             _REPO_ROOT / "cairn" / "machines" / "build_inspector")


def _imports_the_berth(source: str) -> bool:
    """True iff the source IMPORTS cairn.tools.base.nest — ``import cairn.tools.base.nest``,
    ``from cairn.tools.base.nest import X``, or ``from cairn.tools.base import nest`` — read from
    the AST, never from the text."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name == "cairn.tools.base.nest" for a in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module == "cairn.tools.base.nest":
                return True
            if node.module == "cairn.tools.base" and any(a.name == "nest" for a in node.names):
                return True
    return False


def survey_the_corpus() -> dict:
    """Count, over class-space: history records carrying a ``build_gate`` annotation
    (inspections actually RUN — each one a gradation emitted at the general level)
    against real second carriers of ``cairn.tools.base.nest`` (importing .py files outside
    the two home-field components). Carriers are named, so the finding that rides
    back says who reads the gradation, not just that somebody does."""
    inspections = 0
    for hist in sorted(_REPO_ROOT.rglob("history.json")):
        if ".git" in hist.parts:
            continue
        try:
            records = json.loads(hist.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a corpus this probe cannot read is not a finding
            continue
        if not isinstance(records, list):
            continue
        inspections += sum(1 for rec in records
                           if isinstance(rec, dict) and rec.get("build_gate")
                           and rec.get("at", "") >= _GENERAL_ERA)
    carriers: list[str] = []
    for py in sorted(_REPO_ROOT.rglob("*.py")):
        if ".git" in py.parts or "__pycache__" in py.parts:
            continue
        if any(exc in py.parents for exc in _EXCLUDED):
            continue
        try:
            if _imports_the_berth(py.read_text(encoding="utf-8")):
                carriers.append(str(py.relative_to(_REPO_ROOT)))
        except OSError:
            continue
    return {"inspections_run": inspections, "carriers": carriers}


def _trigger(now, context: dict) -> bool:
    """TRUE when gradations are many and carriers are ZERO. Both clauses load-bearing:
    firing early would poke the owner about a berth nobody has had time to reach;
    firing while any carrier stands would poke about generality that demonstrably
    earns its keep."""
    s = context.get("corpus") or survey_the_corpus()
    return s["inspections_run"] >= _ENOUGH and not s["carriers"]


def _enough(context: dict) -> bool:
    """CLEARED by ONE real second carrier — a second tenant shaking its own nest or a
    consumer reading the gradation (the sieve-learning nexus is the named candidate).
    Mutually exclusive with the trigger BY CONSTRUCTION: the pair shares the one
    variable (``carriers`` empty vs non-empty), no floor asymmetry to rot quiet."""
    s = context.get("corpus") or survey_the_corpus()
    return bool(s["carriers"])


def _carry(context: dict) -> dict:
    s = context.get("corpus") or survey_the_corpus()
    return {"finding": "the gradation is emitted at the general level on every "
                       "inspection and nothing has ever read it — generality "
                       "standing decorative",
            "counts": s,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the lift promised 'a general level, where a "
                                 "consumer can read the gradation'; the berth is "
                                 "general, the reading never happens",
            "suggests": "build the sieve-learning nexus reader the watch exists to "
                        "pressure into existence — or the lift was premature at "
                        "n=1 tenant, and the honest disposition says so at the "
                        "register"}


# THE HORIZON (falsifier clause: armed, correct, and silent is indistinguishable from
# health without one). Same placeholder, same tracked debt, as both siblings at this
# address: the beat rate is not yet a real number, so 1000 pulses is "clearly a long
# standing" and MUST be re-tuned when it becomes one.
_HORIZON = 1000

PROBE = Probe(
    why="does the gradation, now emitted at the general level on every inspection, "
        "ever find a reader? — many gradations with zero second carriers is the "
        "ruled generality standing decorative",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the counts, and what the pair would do with them right now.
    s = survey_the_corpus()
    print(json.dumps({"corpus": s,
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2))
