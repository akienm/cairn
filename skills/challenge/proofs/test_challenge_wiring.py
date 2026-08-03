"""Proof for skill:/challenge — the firing event is real (ticket
challenge-fires-at-intent, 2026-08-03).

WHAT ONLY THIS COMPONENT CAN BE ASKED. The seam's teeth
(cairn/skill_block/proofs/test_skill_block.py) prove the intent door refuses an
unchallenged birth, and /intent's own proof holds its markdown and charter
together. What neither owns is THIS skill's claim about itself: that it has a
firing event at all — the defect the ticket measured was five questions that
included "prior art?" while nothing anywhere asked them (referenced three
times, fired zero, and a cadence claimed against a clock that did not exist).
These teeth pin the wiring from the challenge side: the event is named in this
skill's own text, the two skills' question sets cannot drift apart, and the
contract this skill's answers ride actually stands at the door it names.

    python3 skills/challenge/proofs/test_challenge_wiring.py     # exit 0 = green
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
REPO = SKILL_DIR.parents[1]
sys.path.insert(0, str(REPO))

from cairn.skill_block import skill_block as sb  # noqa: E402

SKILL_MD = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
INTENT_MD = (REPO / "skills" / "intent" / "SKILL.md").read_text(encoding="utf-8")

# The five challenge questions as this skill asks them, mapped to the answer key
# each one lands in inside the intent packet's `challenge` field. Written down
# once, here — the drift detector between the asking skill and the carrying one.
ANSWERS = {"Better approach": "better_approach", "Prior art": "prior_art",
           "Hidden assumption": "hidden_assumption", "Real collision": "real_collision",
           "back up": "back_up"}


def test_this_skill_names_its_own_firing_event():
    """The ticket's whole point: a trigger that exists. The event (a node being
    born at /intent) and the ticket that ruled it must stand in THIS file's text —
    a skill that cannot say when it fires is the orphan this proof retires."""
    assert "firing event" in SKILL_MD.lower(), \
        "SKILL.md no longer names a firing event section"
    assert re.search(r"node birth|node being born", SKILL_MD, re.I), \
        "the event (a node being born) vanished from the skill's own text"
    assert "challenge-fires-at-intent" in SKILL_MD, \
        "the ruling ticket is no longer cited beside the event"


def test_no_live_clock_is_claimed():
    """The retired defect must not creep back: 'cadence' may survive only as the
    record of its own retirement, never as a live trigger in the description the
    picker reads."""
    header = SKILL_MD.split("\n---", 1)[0] if SKILL_MD.startswith("---") else ""
    assert "description:" in header, "the frontmatter split missed the header"
    assert "cadence" not in header.lower(), \
        "the description claims a cadence again — a schedule nothing runs"
    for line in SKILL_MD.splitlines():
        if "cadence" in line.lower():
            context = SKILL_MD[max(0, SKILL_MD.find(line) - 300):SKILL_MD.find(line) + 300]
            assert re.search(r"earlier|retire|described a schedule", context, re.I), \
                f"a live cadence claim is back: {line!r}"


def test_the_two_skills_question_sets_cannot_drift():
    """This skill asks five questions; the intent packet carries five answer keys.
    Two files, one meaning — nothing but this tooth holds them together, and an
    answer key with no question behind it is a field nobody will ever fill honestly."""
    for question, key in ANSWERS.items():
        assert re.search(re.escape(question), SKILL_MD, re.I), \
            f"question {question!r} vanished from this skill's text"
        assert re.search(rf"`?{key}`?", INTENT_MD), \
            f"answer key {key!r} is never named where /intent fills the packet"


def test_the_door_this_skill_rides_actually_requires_it():
    """From the challenge side, re-checked end to end through the REAL charter:
    the contract the answers ride must exist at the door the text points at.
    Membership, never a snapshot — reworded whys survive, a dropped field reds."""
    c = sb.load_contract("intent")
    assert "challenge" in c["requires"], \
        "the intent door no longer requires the challenge pass — the wiring is cut"
    for key in ANSWERS.values():
        assert key in c["requires"]["challenge"], \
            f"the contract's why no longer names answer key {key!r}"


TEETH = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for tooth in TEETH:
        try:
            tooth()
            print(f"  green  {tooth.__name__}")
        except Exception as exc:
            failed += 1
            print(f"  RED    {tooth.__name__}: {exc}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    sys.exit(1 if failed else 0)
