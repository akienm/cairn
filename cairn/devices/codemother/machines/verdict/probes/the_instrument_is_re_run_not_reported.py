"""WATCHME(the_instrument_is_re_run_not_reported) for ticket 8e5db5f3edb2.

THE QUESTION THE PROOF CANNOT ANSWER. The teeth beside this file settle that the
physics is right today: the door extracts, runs, compares, and refuses a report
its re-run contradicts. What they cannot settle is the ticket's own WRONG INTENT
clause, which is about the CORPUS and not the door — *"WRONG INTENT if instruments
collapse into trivially-green commands — `true`, a bare `ls`, an `echo` — so every
re-run agrees by construction. The measurement is the SHAPE of the instruments
arriving, not the count of refusals: a door that never refuses because nobody
hands it anything falsifiable has moved the silence, not removed it."*

That is the exact failure this ticket was cast against, one turn later. The old
door asked the builder whether the build worked; a door that runs `true` asks
nothing of anybody while producing a record that reads like a measurement. No
fixture can see it, because the shape of what arrives is a fact about live
traffic.

WHAT IT WATCHES, AND WHY THIS AND NOT THE REFUSAL RATE. A refusal count would poke
about the system working: a door can be perfectly built and never refuse, because
every builder handed it something true. The thing that goes wrong silently is the
instruments getting cheaper, so the reading is over the instruments themselves —
what fraction of the runs stamped into berthed verdicts are commands that cannot
say no.

DELIBERATELY NOT A CEILING ON PROSE. Everything berthed before 2026-09-11 carries
no stamp at all and is invisible here by construction, which is correct: those
artifacts were shape-checked under the contract that stood when they were written,
and counting them would measure the past rather than the traffic.

FILES ONLY — no device, no bus, no network, no subprocess, so it stays cheap
enough to sit on a pulse.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge
that re-opens a node whose intention did not work is the OWNER's act (Law 6).
"""

from __future__ import annotations

import datetime
import glob
import json
import re
import shlex

from cairn.tools.base.address import instance_path
from cairn.tools.base.probe import Probe, once, owning_ticket

_OWNING_TICKET = "8e5db5f3edb2"
_PACKETS = str(instance_path("chart", 0) / "packets")

# The ticket's horizon, both halves: ten artifacts written through the new door,
# or a month, whichever comes first.
_ENOUGH_COUNT = 10
_DEADLINE = datetime.date(2026, 10, 11)

# COMMANDS THAT CANNOT SAY NO. Named as the ticket named them, and kept short for
# the same reason the extractor's shell-head list is short: every entry added here
# is a word this probe stops trusting, and a long list becomes a style opinion
# rather than a measurement. The test is the HEAD of the command, after leading
# VAR=value assignments — a pipeline whose head is `true` is still `true`.
_CANNOT_BITE = frozenset(("true", ":", "echo", "printf", "ls", "pwd", "cat", "date"))
_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# The fraction below which the corpus is the shape the ticket calls WRONG INTENT.
# Half, and stated once here rather than inline, because it is the number a later
# reader will want to argue with.
_FLOOR = 0.5
_MIN_TO_JUDGE = 3


def _head(command: str) -> str:
    try:
        tokens = shlex.split(command, comments=False)
    except ValueError:
        return ""
    while tokens and _ASSIGNMENT_RE.match(tokens[0]):
        tokens.pop(0)
    return tokens[0] if tokens else ""


def cannot_bite(instrument) -> bool:
    """A command whose head is a no-op: it agrees with any declaration by
    construction, so a verdict resting on it measured nothing."""
    if not isinstance(instrument, str):
        return True
    return _head(instrument.strip()) in _CANNOT_BITE


def instrument_shape(readings: list) -> dict:
    """THE READING, over a list of stamped observations.

    Takes the corpus as an argument so a proof can hand it a shape that should
    fire and one that should not. A probe that cannot be made to fire on demand is
    a probe nobody has measured."""
    total = len(readings)
    toothless = [r for r in readings if cannot_bite(r.get("instrument"))]
    fraction = (total - len(toothless)) / total if total else 1.0
    judgeable = total >= _MIN_TO_JUDGE
    fires = judgeable and fraction < _FLOOR
    return {
        "runs_observed": total,
        "cannot_bite": len(toothless),
        "fraction_that_can_bite": round(fraction, 3),
        "examples": [str(r.get("instrument"))[:120] for r in toothless[:5]],
        "fires": fires,
        "what": (
            "%d of %d stamped instruments are trivially green — a command whose head "
            "is one of %s agrees with any declaration by construction, so the door "
            "ran something and measured nothing. The silence moved; it did not go"
            % (len(toothless), total, ", ".join(sorted(_CANNOT_BITE)))
            if fires else
            "%d of %d stamped instruments can say no (floor %.2f)%s"
            % (total - len(toothless), total, _FLOOR,
               "" if judgeable else " — too few to judge yet")),
    }


def survey_the_berth() -> dict:
    """Every stamped run across the berthed verdict artifacts. Unreadable files are
    CARRIED, never skipped: a verdict this probe cannot open is a finding about the
    berth, and swallowing it is how a census learns to lie (Law 7)."""
    readings, unreadable = [], []
    for path in sorted(glob.glob("%s/verdict-*.json" % _PACKETS)):
        try:
            with open(path, encoding="utf-8") as fh:
                artifact = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            unreadable.append("%s: %s" % (path, exc))
            continue
        for reading in artifact.get("observed_runs") or []:
            if isinstance(reading, dict):
                readings.append(reading)
    shape = instrument_shape(readings)
    shape["unreadable_files"] = unreadable
    shape["artifacts_with_a_stamp"] = len({
        p for p in sorted(glob.glob("%s/verdict-*.json" % _PACKETS))
        if _has_stamp(p)})
    shape["past_deadline"] = datetime.date.today() >= _DEADLINE
    return shape


def _has_stamp(path: str) -> bool:
    try:
        with open(path, encoding="utf-8") as fh:
            return isinstance(json.load(fh).get("observed_runs"), list)
    except (OSError, json.JSONDecodeError):
        return False


def _trigger(now, context: dict) -> bool:
    return once(context, "survey", survey_the_berth)["fires"]


def _enough(context: dict) -> bool:
    """CLEARED at the ticket's own horizon: ten artifacts through the new door, or
    2026-10-11. Not on the first pulse — on the day this is armed the berth holds
    zero stamped runs, and a watch that can clear before it can fire is not a
    watch."""
    s = once(context, "survey", survey_the_berth)
    if s["past_deadline"]:
        return True
    return s["artifacts_with_a_stamp"] >= _ENOUGH_COUNT and not s["fires"]


def _carry(context: dict) -> dict:
    s = once(context, "survey", survey_the_berth)
    return {
        "finding": s["what"],
        "shape": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "the door runs the instrument it is handed, so a verdict now rests on a "
            "measurement rather than on the builder's report — unless the instruments "
            "themselves stop being able to fail, in which case the record reads like a "
            "measurement and is one only in shape"),
        "suggests": (
            "read the `examples` first — they are the actual command strings. If they "
            "are genuinely trivial the work is upstream at /chart's validate stage, "
            "where the criterion's instrument is authored, not at this door. If they "
            "look substantial and the head merely matched (a `cat` that pipes into a "
            "real check, say), the finding is in this probe's head test and belongs to "
            "it, not to the corpus."),
    }


# THE HORIZON, in PULSES, and honest as a placeholder rather than a measurement:
# the shim counts pulses, the wall-clock beat that would drive them is a filed edge
# rather than a built one, so nothing pulses this shim today and the loudness rides
# the read-side door (BaseShim.overdue()) alone.
_HORIZON = 1000

PROBE = Probe(
    why="the teeth settle that the door extracts, runs and refuses correctly today, "
        "in a fixture tree; whether the instruments ARRIVING can still say no is a "
        "fact about live traffic, and the ticket's own WRONG INTENT clause names "
        "trivially-green instruments as the way this build fails while reading green",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
