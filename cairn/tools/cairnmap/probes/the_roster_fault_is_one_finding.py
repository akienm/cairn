"""WATCHME(the-roster-fault-is-one-finding) for ticket 7aed0fd0ba29 — did one membership
fault actually stop rendering as fifteen, and did it stay that way?

THE QUESTION THE PROOF CANNOT ANSWER. The teeth settle that the reader is right TODAY, in
a fixture tree with two skills and one command. What they cannot settle is whether the
LIVE corpus lives it: whether a fault in the node class still lands as ONE finding when
73 charters and 15 skill directories are in the room, and whether it stays one as the
corpus moves. The failure this ticket was cast against happened while every tooth in
cairnmap's proof was green — the fixture world wrote `members_so_far`, so the fixture
world and the live world had disagreed for twelve days and no tooth could see it.

WHAT IT WATCHES, AND WHY THAT AND NOT THE TOTAL. Two readings, files-and-a-function only:

  1. THE MULTIPLICATION, READ AS A DELTA. It runs the live corpus twice — once with the
     real node class, once with one that says nothing about membership — and asks what the
     fault ADDED: one failing lane, one red, and the derived lane ABSENT. The delta rather
     than the total, because the total carries the corpus's other standing findings and
     would fire on every one of them (measured while arming this probe: the absolute count
     read 7, six of which were the out-of-bounds findings the ticket named). This is a
     BEHAVIOUR read — it calls `inspect()` against a substituted node class rather than
     grepping cairnmap.py for a guard. A probe that read the source would stay quiet
     through a refactor that moved the guard and lost it.
  2. THE REAL FINDINGS, as a census beside the verdict. Measured at arming: 6, and the
     ticket named each one out of bounds. Carried as CONTEXT, not as an assertion — see
     below on why a ceiling would be the wrong watch.

DELIBERATELY NOT A CEILING ON THE FINDING COUNT. The gate's total legitimately moves: a
new `bin/cmd/` entry, a skill installed or removed, a charter whose `invoke` changes all
shift it, and every one of those is the gate working. A ceiling would poke about the
system doing its job — the sibling probe's own recorded lesson about ratios. The thing
that only moves ONE WAY is the multiplication: one fault rendering as many.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that
re-opens a node whose intention did not work is the OWNER's act (Law 6).

FILES ONLY — no device, no bus, no network, no subprocess, so it stays cheap enough to
sit on a pulse.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from cairn.tools.base.probe import Probe, once, owning_ticket
from cairn.tools.cairnmap import cairnmap
from cairn.tools.gate import gate

_OWNING_TICKET = "7aed0fd0ba29"

# This file is cairn/tools/cairnmap/probes/<name>.py.
_CLASS_SPACE = Path(__file__).resolve().parents[4]

# MEASURED 2026-09-11 AT ARMING, over the live corpus: `cairnmap --gate` reported 6
# findings across 75 charters — /ruled chartered but not installed, and five bin/cmd
# entries no charter's invoke names. Before the build it reported 21, of which 15 were the
# single membership fault wearing fifteen faces. Carried as CONTEXT, never as an assertion.
_AT_ARMING = {"findings": 6, "charters": 75, "before_the_build": 21, "false_of_those": 15}
_ARMED = "2026-09-11"

# The ticket's `enough`: ten gate runs across at least three distinct corpus states, with
# the fault never appearing more than once. Ten rather than one because a green off a
# single run reads as "the corpus did not move" — the historical-fact green this system
# keeps catching (a_pickup_is_witnessed took its 1 in August 2026 and read green forever).
_ENOUGH_RUNS = 10
_ENOUGH_STATES = 3


def _live_record(node_class_text: str) -> list[dict]:
    """THE GATE'S OWN RECORD over the LIVE corpus, with one substitution: a commons whose
    skill node class is the text handed in.

    Kept as a function taking the text so a proof can hand it the world this probe is
    watching for, without the probe ever shelling out or touching the real commons.
    """
    commons = _CLASS_SPACE.parent / "CairnCommons"
    with tempfile.TemporaryDirectory() as tmp:
        shadow = Path(tmp) / "node_classes"
        shadow.mkdir(parents=True)
        (shadow / "skill.json").write_text(node_class_text, encoding="utf-8")
        # Only node_classes/ is shadowed; everything else the gate reads it reads live.
        for entry in (commons / "node_classes").iterdir():
            if entry.name != "skill.json" and entry.is_file():
                (shadow / entry.name).write_text(entry.read_text(encoding="utf-8"),
                                                 encoding="utf-8")
        return cairnmap.inspect(commons=Path(tmp))


def multiplication_reading(record_of=_live_record) -> dict:
    """WHAT A MEMBERSHIP FAULT COSTS THE RECORD, over the live corpus — AS A DELTA.

    IT HAD TO BE A DELTA, AND THE PROBE'S OWN FIRST LIVE READ IS WHY (2026-09-11, measured
    while arming it). The first cut counted every red in the starved record and asked
    whether it was 1. It read 7 and fired — correctly counting, wrongly attributing: six of
    those were the standing findings the ticket put OUT of bounds (/ruled uninstalled, five
    bin/cmd entries no charter names), which are there whether or not the node class can
    answer anything. A probe whose trigger rides the gate's absolute red count fires on
    every unrelated defect in the corpus and is a watch on the wrong thing. So the reading
    substitutes the node class TWICE — once live, once starved — and asks what the fault
    ADDED. That number is attributable; the total never was.

    Takes the record function as an argument so a proof can hand it the PRE-BUILD
    behaviour and watch this fire. A probe that cannot be made to fire on demand is a
    probe nobody has measured.
    """
    commons = _CLASS_SPACE.parent / "CairnCommons"
    live = record_of((commons / "node_classes" / "skill.json").read_text(encoding="utf-8"))
    starved = record_of(json.dumps({"what": "a node class that says nothing about members"}))

    def reds_of(record):
        return sum(len(e["values"]["reds"]) for e in record if not gate.passed(e))

    def failing_of(record):
        return [e["identity"] for e in record if not gate.passed(e)]

    added_reds = reds_of(starved) - reds_of(live)
    added_lanes = [i for i in failing_of(starved) if i not in failing_of(live)]
    derived_absent = "every_skill_directory_carries_a_charter" not in {
        e["identity"] for e in starved}
    one_fault_one_finding = (added_reds == 1
                             and added_lanes == ["the_skill_membership_rule_is_declared"])
    return {
        "reds_live": reds_of(live),
        "reds_starved": reds_of(starved),
        "added_lanes": added_lanes,
        "reds_from_one_fault": added_reds,
        "derived_lane_absent": derived_absent,
        "fires": not one_fault_one_finding or not derived_absent,
        "what": (
            f"a node class that cannot answer the membership question ADDS {added_reds} "
            f"red(s) across lanes {added_lanes} — one fault multiplied, which is a "
            f"diagnostic surface lying about how many things are wrong (Law 7)"
            if not one_fault_one_finding else
            "a lane whose input could not be read was appended as a PASS instead of being "
            "ABSENT — the record got cleaner rather than shorter, which is falsifier "
            "clause 10"
            if not derived_absent else
            "one membership fault adds exactly one finding, and the lane that could not "
            "run is absent from the record rather than green"),
    }


def live_gate_census() -> dict:
    """What the gate says about the corpus right now, beside the verdict."""
    record = cairnmap.inspect()
    failing = [e for e in record if not gate.passed(e)]
    return {
        "lanes": [e["identity"] for e in record],
        "findings": sum(len(e["values"]["reds"]) for e in failing),
        "failing_lanes": [e["identity"] for e in failing],
        "charters": next((e["values"].get("charters_found") for e in record
                          if e["identity"] == "every_charter_parses"), None),
    }


def _trigger(now, context: dict) -> bool:
    """TRUE when one fault has gone back to costing more than one finding.

    No clause on the gate's TOTAL. That number legitimately moves with the corpus — a
    command added, a skill installed — and watching it would poke about the system
    working. The multiplication only moves one way.
    """
    return once(context, "multiplication", multiplication_reading)["fires"]


def _enough(context: dict) -> bool:
    """CLEARED once ten gate runs across three distinct corpus states have passed with the
    fault still costing exactly one finding.

    THE STATE CLAUSE IS WHAT KEEPS THIS FROM CLEARING ON A STILL CORPUS. Ten runs over an
    unchanged tree measure the same world ten times; the ticket asked for three distinct
    states because the thing being watched is how the reader behaves as the corpus MOVES.
    Distinctness is read from the charter count and the skill-directory listing — the two
    things that change when a skill or a component is added or removed.
    """
    seen = context.setdefault("corpus_states", {})
    census = once(context, "census", live_gate_census)
    seen[f"{census['charters']}:{len(census['lanes'])}"] = seen.get(
        f"{census['charters']}:{len(census['lanes'])}", 0) + 1
    runs = sum(seen.values())
    return (runs >= _ENOUGH_RUNS and len(seen) >= _ENOUGH_STATES
            and not once(context, "multiplication", multiplication_reading)["fires"])


def _carry(context: dict) -> dict:
    """The datum that rides back: what one fault costs, and the corpus it costs it in."""
    m = once(context, "multiplication", multiplication_reading)
    census = once(context, "census", live_gate_census)
    return {
        "finding": m["what"],
        "reds_from_one_fault": m["reds_from_one_fault"],
        "reds_live": m["reds_live"],
        "reds_starved": m["reds_starved"],
        "added_lanes": m["added_lanes"],
        "derived_lane_absent": m["derived_lane_absent"],
        "findings_now": census["findings"],
        "failing_lanes_now": census["failing_lanes"],
        "charters_now": census["charters"],
        "at_arming": _AT_ARMING,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "`cairnmap --gate` over the live corpus reports the membership fault ONCE if at "
            "all, never once per skill — a surface that multiplies one fault into fifteen "
            "sends a reader to fix fifteen charters when the one thing wrong is a node "
            "class, and fifteen false findings beside six real ones is how the six stop "
            "being read"),
        "suggests": (
            "read skill_membership() in cairnmap.py first — the three faults it names each "
            "return an empty set BESIDE a sentence, and the caller's `if not "
            "membership_err` guard is what keeps the derived lane absent. If this fired "
            "with reds_from_one_fault above 1, either a fault path started returning a set "
            "with no sentence (the 2026-08-28 shape: a missing answer read as an empty "
            "answer), or a new lane was added outside the guard. The gate's TOTAL moving "
            "is not by itself a defect — a command added or a skill uninstalled moves it, "
            "and that is the gate working."),
    }


# THE HORIZON. Unit is PULSES because the shim counts pulses; the wall-clock beat that
# would drive them is a filed edge rather than a built one, so nothing pulses this shim
# today and the loudness rides the read-side door (`BaseShim.overdue()`) alone. 1000 is
# "clearly a long standing" against any beat rate we would plausibly pick. Honest as a
# placeholder and dishonest as a measurement.
_HORIZON = 1000

PROBE = Probe(
    why="the proof's teeth settle that the reader is right today, in a fixture tree with "
        "two skills; whether ONE membership fault still costs ONE finding across 75 "
        "charters as the corpus moves is a fact about live traffic, and the 15 false "
        "findings this ticket was cast against accumulated while every tooth in cairnmap's "
        "own proof was green — because the fixture wrote the key the corpus had retired",
    trigger=_trigger,
    to="cairnmap",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
