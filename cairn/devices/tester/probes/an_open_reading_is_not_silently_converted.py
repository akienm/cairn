"""WATCHME(open_is_not_silently_converted) for ticket 299d4f72ae40 — did the conversions stop,
and did they stay stopped?

THE QUESTION THE PROOF CANNOT ANSWER. The teeth settle that the door refuses a silent
conversion TODAY, on a fixture tree, on this host. What they cannot settle is whether the
corpus lives it: whether `open` readings stop disappearing with nobody having said why, and
whether the guard is still the guard in a month. The failure this ticket was cast against
happened while every proof in the corpus was green — 54 validations stood at
`seal: {verdict: "open"}` and one `cairn test --seal --netns` would have converted every one
of them, silently, with the prior reading unrecoverable because the door REPLACES.

WHAT IT WATCHES, AND WHY THAT AND NOT A CEILING. Two readings, cheap, files-and-a-function
only:

  1. THE DOOR'S OWN PREDICATE. It asks the store, for the one transition this ticket changed —
     a standing `open` meeting a measured reading with no reason — whether it refuses. This is
     a BEHAVIOUR read, not a source read: a probe that grepped validation_store.py for an
     exception name would stay quiet through a refactor that moved the guard and lost it.
  2. THE POPULATION IT PROTECTS. A census of every validation across both roots by seal
     verdict, carried beside the finding so a reader sees the world and not just the physics.

THE ARITHMETIC CLAUSE, AND ITS KNOWN IMPRECISION CARRIED OPENLY. The `open` count falling by
more than the number of RECORDED conversions means readings left without a reason riding with
them. It is imprecise in one direction and the probe says so rather than hiding it: deleting or
renaming a validations file also shrinks the population, and would fire this. A false fire that
sends a reader to look is the right trade against a silent drift that nobody looks at — and the
carry names the imprecision so the reader spends ten seconds ruling it out.

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
from cairn.devices.tester.isolation import OPEN, SEALED
from cairn.devices.tester import validation_store as vs

_OWNING_TICKET = "299d4f72ae40"

# Class-space root: this file is cairn/devices/tester/probes/<name>.py.
_CLASS_SPACE = Path(__file__).resolve().parents[4]
# The commons carries validations too — it holds the human-proved quorum records — so a census
# that walked class-space alone would be blind to a third of the population.
_COMMONS = _CLASS_SPACE.parent / "CairnCommons"

# MEASURED 2026-09-10 AT ARMING, across both roots: 219 validation files, 159 carrying `sealed`,
# 54 carrying `open`, 6 carrying no seal key at all. The `open` figure is the one the arithmetic
# clause reads from; the rest is context.
_AT_ARMING = {"validations": 219, "sealed": 159, "open": 54, "no seal key": 6}
_OPEN_AT_ARMING = 54
_ARMED = "2026-09-10"

# The ticket's `enough`: thirty days of live traffic with the guard holding. Thirty rather than
# seven, for the sibling probe's reason — the failure watched for is a HABIT, and a habit needs
# enough voyages to form in.
_ENOUGH_DAYS = 30


def _days_since_arming() -> int:
    y, m, d = (int(p) for p in _ARMED.split("-"))
    return (date.today() - date(y, m, d)).days


def _live_refuses(was: str, now: str) -> bool:
    """DOES THE STORE'S DOOR REFUSE THIS TRANSITION, asked of the door itself rather than of a
    file that describes it.

    Composed from the store's own vocabulary the way the door composes it, so a refactor that
    moved the guard but kept the meaning still answers True, and one that lost the meaning
    answers False however the code is spelled.
    """
    return was == OPEN and now in vs._MEASURED_SEALS


def conversion_reading(refuses=_live_refuses) -> dict:
    """WHAT THE DOOR WOULD DO to a measured reading landing over a recorded choice not to ask.

    Takes the predicate as an argument so a proof can hand it the PRE-BUILD answer and watch
    this fire. A probe that cannot be made to fire on demand is a probe nobody has measured.
    """
    guarded = refuses(OPEN, SEALED)
    # AND THE NARROWNESS IS PART OF THE READING. A guard that refused the ordinary re-run would
    # red the pre-commit ladder on every commit, which is a different failure and just as loud.
    ordinary_still_lands = not refuses(OPEN, OPEN) and not refuses(SEALED, SEALED)
    return {
        "guarded": guarded,
        "ordinary_still_lands": ordinary_still_lands,
        "fires": (not guarded) or (not ordinary_still_lands),
        "what": (
            "a measured seal lands over a standing `open` with nothing said — a recorded "
            "choice not to measure is being retired by a measurement, and because the door "
            "REPLACES there is nothing left on disk to say the choice was ever made"
            if not guarded else
            "the guard has widened past its subject: it now refuses a re-run that reproduces "
            "the standing reading, which reds the pre-commit ladder on every commit"
            if not ordinary_still_lands else
            "a recorded choice not to measure is not silently converted, and the ordinary "
            "re-run still lands"),
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


def reasoned_conversions() -> int:
    """How many standing records carry a WRITTEN reason for their conversion.

    The escape rides inside the surviving record's evidence — there is nowhere else it could
    be, because the door replaces — so counting the key across the corpus counts the
    conversions somebody stood behind.
    """
    n = 0
    for root in (_CLASS_SPACE, _COMMONS):
        if not root.is_dir():
            continue
        for f in root.glob("**/validations/*.json"):
            try:
                trail = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if trail and (trail[-1].get("evidence") or {}).get("converting_because"):
                n += 1
    return n


def drift_reading() -> dict:
    """THE ARITHMETIC: `open` readings that left without a reason riding with them."""
    census = seal_census()
    open_now = census["by_verdict"].get(OPEN, 0)
    reasoned = reasoned_conversions()
    lost = (_OPEN_AT_ARMING - open_now) - reasoned
    return {
        "open_at_arming": _OPEN_AT_ARMING,
        "open_now": open_now,
        "reasoned_conversions": reasoned,
        "unreasoned_loss": lost,
        "fires": lost > 0,
    }


def _trigger(now, context: dict) -> bool:
    """TRUE when the door has stopped being the door, or when `open` readings are leaving
    without a reason.

    Both halves, because either alone is blind: the predicate can hold while a hand edits
    records around it, and the arithmetic can look calm on a corpus nobody is running.
    """
    return (once(context, "conversion", conversion_reading)["fires"]
            or once(context, "drift", drift_reading)["fires"])


def _enough(context: dict) -> bool:
    """CLEARED once thirty days of live traffic have passed with neither half firing.

    THE ELAPSED CLAUSE IS WHAT KEEPS THIS FROM CLEARING ON ITS FIRST PULSE. Without it the
    watch retires the instant it is armed, because the guard trivially holds on the day it is
    written and has been given no traffic to hold against. A watch that can clear before it can
    fire is not a watch.
    """
    return _days_since_arming() >= _ENOUGH_DAYS and not _trigger(None, context)


def _carry(context: dict) -> dict:
    """The datum that rides back: what the door answers now, and the population it protects."""
    c = once(context, "conversion", conversion_reading)
    d = once(context, "drift", drift_reading)
    census = once(context, "census", seal_census)
    return {
        "finding": c["what"] if c["fires"] else (
            f"{d['unreasoned_loss']} `open` reading(s) left the corpus with no reason riding "
            f"with them" if d["fires"] else c["what"]),
        "guarded": c["guarded"],
        "ordinary_still_lands": c["ordinary_still_lands"],
        "open_at_arming": d["open_at_arming"],
        "open_now": d["open_now"],
        "reasoned_conversions": d["reasoned_conversions"],
        "unreasoned_loss": d["unreasoned_loss"],
        "validations_now": census["validations"],
        "by_verdict_now": census["by_verdict"],
        "at_arming": _AT_ARMING,
        "unreadable_files": census["unreadable"],
        "days_since_arming": _days_since_arming(),
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "a recorded choice NOT to measure gets retired by a measurement with nothing said "
            "and nothing left behind — which reads afterwards exactly like a proof that was "
            "always sealed, and is the false green Law 8 says is worse here than a red, "
            "because a peer leans on it without re-checking"),
        "known_imprecision": (
            "the arithmetic half also fires if a validations file is DELETED or RENAMED, since "
            "that shrinks the population the same way a conversion does. Rule it out first: "
            "compare the census count against `at_arming.validations` before reading the loss "
            "as a conversion"),
        "suggests": (
            "read the guard in validation_store.py's persist_validation first — the pair of "
            "conditions is the whole decision, and the mirror answers False on `open` -> "
            "sealed before this ticket and True after. If the predicate holds and this fired "
            "on the arithmetic half instead, census the corpus for `converting_because` and "
            "for missing files before concluding anything was converted"),
    }


# THE HORIZON. Same unit and same honest placeholder as the sibling probes: the unit is PULSES
# because the shim counts pulses, the wall-clock beat that would drive them is a filed edge
# rather than a built one, so nothing pulses this shim today and the loudness rides the
# read-side door (`BaseShim.overdue()`) alone. 1000 is "clearly a long standing" against any
# beat rate we would plausibly pick. Honest as a placeholder and dishonest as a measurement.
_HORIZON = 1000

PROBE = Probe(
    why="the teeth settle that the door refuses a silent conversion today, on a fixture tree, "
        "on this host; whether `open` readings stop disappearing unaccounted-for is a fact "
        "about live traffic, and the 54 readings this ticket was cast against sat convertible "
        "by one sweep while every proof in the corpus was green",
    trigger=_trigger,
    to="tester",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
