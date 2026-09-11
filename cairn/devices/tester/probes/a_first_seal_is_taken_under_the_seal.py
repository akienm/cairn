"""WATCHME(first_seal_isolation) for ticket 481221f45884 — did first seals actually start
getting taken under the seal, and did they stay that way?

THE QUESTION THE PROOF CANNOT ANSWER. Its teeth settle that the decision is right TODAY, in a
fixture tree, on this host. What they cannot settle is whether the corpus lives it: whether the
``open`` population stopped growing, and whether the branch is still the branch in six weeks.
The failure this ticket was cast against happened while every proof in the corpus was green —
54 validations stood at ``seal: {verdict: "open"}`` and nothing anywhere was red about it,
because ``open`` is a legal verdict that means *nobody asked*.

WHAT IT WATCHES, AND WHY THAT AND NOT THE RATIO. Two readings, cheap, files-and-a-function only:

  1. THE DECISION. It calls the tester's own mapping the way the CLI does, for the one case this
     ticket changed — ``standing_seal`` found nothing — and asks what isolation comes back. The
     answer must be ``netns``. This is a BEHAVIOUR read, not a source read: a probe that grepped
     cli.py for a word would stay quiet through a refactor that moved the decision and lost it.
  2. THE POPULATION IT IS SUPPOSED TO MOVE. A census of every validation across both roots by
     seal verdict, carried beside the finding so a reader sees the world, not just the physics.

Deliberately NOT a ceiling on the ``open`` count, which was the first cut. A proof can honestly
be run at isolation ``none`` through ``run_proof`` directly, and ``--reseal`` correctly
reproduces a standing ``open`` — both mint ``open`` readings that are right. A ceiling would
poke about the system working, which is the sibling probe's own recorded lesson about ratios.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that re-opens a
node whose intention did not work is the OWNER's act (Law 6).

FILES ONLY — no device, no bus, no network, no subprocess, so it stays cheap enough to sit on a
pulse.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from cairn.tools.base.probe import Probe, once, owning_ticket
from cairn.devices.tester.validation_store import isolation_for_seal

_OWNING_TICKET = "481221f45884"

# Class-space root: this file is cairn/devices/tester/probes/<name>.py.
_CLASS_SPACE = Path(__file__).resolve().parents[4]
# The commons carries validations too — it holds the human-proved quorum records — so a census
# that walked class-space alone would be blind to a third of the population.
_COMMONS = _CLASS_SPACE.parent / "CairnCommons"

# MEASURED 2026-09-10 AT ARMING, across both roots: 218 validation files, 158 carrying `sealed`,
# 54 carrying `open`, 6 carrying no seal key at all. Carried as CONTEXT, never as an assertion —
# see the header on why a ceiling would be the wrong watch.
_AT_ARMING = {"validations": 218, "sealed": 158, "open": 54, "no seal key": 6}
_ARMED = "2026-09-10"

# The ticket's `enough`: thirty days of live traffic with the decision holding. Thirty rather than
# seven for the sibling probe's reason — the failure watched for is a HABIT re-forming, and a
# habit needs enough voyages to form in.
_ENOUGH_DAYS = 30


def _days_since_arming() -> int:
    y, m, d = (int(p) for p in _ARMED.split("-"))
    return (date.today() - date(y, m, d)).days


def _live_decision(standing: str | None) -> str:
    """THE CLI'S OWN ANSWER for a sealing run, composed from the device's vocabulary exactly as
    ``cli.isolation_for`` composes it. Kept as a function so the reading below can be taken
    against a substitute in a proof, without the probe ever shelling out."""
    return isolation_for_seal(standing) or "netns"


def decision_reading(decide=_live_decision) -> dict:
    """WHAT THE SEALING RUN WOULD DO to a proof that has never been sealed.

    Takes the decision function as an argument so a proof can hand it the PRE-BUILD answer and
    watch this fire. A probe that cannot be made to fire on demand is a probe nobody has measured.
    """
    first = decide(None)
    standing_open = decide("open")
    return {
        "first_seal_isolation": first,
        "standing_open_isolation": standing_open,
        "fires": first != "netns" or standing_open != "none",
        "what": (
            f"a proof with nothing standing would be sealed at {first!r} — a first seal taken "
            f"beside the seal writes the ABSENCE of a reading into the one record that admits "
            f"the proof to proven-space"
            if first != "netns" else
            f"a proof whose standing record says `open` would be re-run at {standing_open!r} — "
            f"the stronger default has overrun ticket 4431cf2bc625's guard instead of sitting "
            f"beneath it"
            if standing_open != "none" else
            "a first seal is taken under the seal, and the standing-open guard still holds"),
    }


def seal_census() -> dict:
    """Every validation across both roots, counted by the seal verdict standing on it."""
    by_verdict: dict[str, int] = {}
    unreadable: list[str] = []
    total = 0
    for root in (_CLASS_SPACE, _COMMONS):
        if not root.is_dir():
            continue
        for f in root.glob("**/validations/*.json"):
            try:
                trail = json.loads(f.read_text(encoding="utf-8"))
            except Exception as exc:
                unreadable.append(f"{f}: {exc}")
                continue
            if not trail:
                continue
            total += 1
            v = ((trail[-1].get("evidence") or {}).get("seal") or {}).get("verdict") or "no seal key"
            by_verdict[v] = by_verdict.get(v, 0) + 1
    return {"validations": total, "by_verdict": by_verdict, "unreadable": unreadable}


def _trigger(now, context: dict) -> bool:
    """TRUE when the decision has stopped being the one this ticket built.

    No population clause. The corpus can legitimately grow `open` readings — a direct
    ``run_proof(isolation="none")`` and a ``--reseal`` reproducing a standing open both do — so
    counting them would poke about the system working. The decision itself only moves one way.
    """
    return once(context, "decision", decision_reading)["fires"]


def _enough(context: dict) -> bool:
    """CLEARED once thirty days of live traffic have passed with the decision still holding.

    THE ELAPSED CLAUSE IS WHAT KEEPS THIS FROM CLEARING ON ITS FIRST PULSE. Without it the watch
    retires the instant it is armed, because the decision trivially holds on the day it is
    written and has not yet been given any traffic to hold against. A watch that can clear before
    it can fire is not a watch.
    """
    return _days_since_arming() >= _ENOUGH_DAYS and not once(
        context, "decision", decision_reading)["fires"]


def _carry(context: dict) -> dict:
    """The datum that rides back: what the decision answers now, and the population it moves."""
    d = once(context, "decision", decision_reading)
    census = once(context, "census", seal_census)
    return {
        "finding": d["what"],
        "first_seal_isolation": d["first_seal_isolation"],
        "standing_open_isolation": d["standing_open_isolation"],
        "validations_now": census["validations"],
        "by_verdict_now": census["by_verdict"],
        "at_arming": _AT_ARMING,
        "unreadable_files": census["unreadable"],
        "days_since_arming": _days_since_arming(),
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "a proof entering proven-space gets its first seal taken with the route open, so the "
            "one record that admits it carries the ABSENCE of a network reading dressed as a "
            "reading — which is the false green Law 8 says is worse here than a red, because a "
            "peer leans on it without re-checking"),
        # THE WORDING HERE IS LOAD-BEARING, AND THE REASON IS A TOOTH (ticket 1accdc1781aa).
        # `test_reseal_door.py::test_no_pulse_path_reaches_the_door` greps every probe for the
        # name of the reseal door, over the file's CODE rather than its prose — comments and
        # docstrings come off first, live string literals deliberately do not, because that is
        # where a dynamic reach would hide. This field is a live string, so naming the flag here
        # reds that tooth even though a `suggests` sentence reaches nothing. Measured 2026-09-10:
        # it did exactly that. Describing the behaviour instead of naming the flag is the honest
        # fix, not a dodge — the probe genuinely does not reach the door, and after the reword the
        # tooth's claim is simply true of this file. Do not "helpfully" put the flag name back.
        "suggests": (
            "read cli.isolation_for first — the last branch is the whole decision, and it answers "
            "'none' before this ticket and 'netns' after. If it still answers 'netns' and this "
            "fired on the standing-open half instead, the regression is in isolation_for_seal and "
            "belongs to ticket 4431cf2bc625, not to this one. The population carried beside the "
            "finding is CONTEXT: a rising `open` count is not by itself a defect, because "
            "re-proving a proof whose standing record already reads open reproduces that "
            "reading, and reproducing it is correct behaviour."),
    }


# THE HORIZON. Same unit and same honest placeholder as the sibling probes: the unit is PULSES
# because the shim counts pulses, the wall-clock beat that would drive them is a filed edge rather
# than a built one, so nothing pulses this shim today and the loudness rides the read-side door
# (`BaseShim.overdue()`) alone. 1000 is "clearly a long standing" against any beat rate we would
# plausibly pick. Honest as a placeholder and dishonest as a measurement.
_HORIZON = 1000

PROBE = Probe(
    why="the proof's teeth settle that the decision is right today, in a fixture tree, on this "
        "host; whether first seals are still being taken under the seal weeks from now is a fact "
        "about live traffic, and the 54 open readings this ticket was cast against accumulated "
        "while every proof in the corpus was green",
    trigger=_trigger,
    to="tester",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
