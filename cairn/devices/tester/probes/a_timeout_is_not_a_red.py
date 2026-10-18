"""WATCHME(timeout_is_not_a_red) for ticket 3dfceaa272ec — did timed-out proofs actually stop
landing as red validations, and are timeouts still being REPORTED while that holds?

THE QUESTION THE PROOF CANNOT ANSWER. Its teeth settle that a run over the budget writes nothing,
prints its own column and still fails the run — today, in a fixture tree. What they cannot settle
is whether the corpus lives it: whether a validation at ``verdict: red`` whose ``stderr_tail``
begins ``timed out after`` ever lands again, from any door, under any future refactor of the arm.

WHAT IT WATCHES, AND WHY ``enough`` NEEDS A REPORTED TIMEOUT. The falsifier's own measurement is
the count of standing validations at red whose stderr_tail begins 'timed out after' — it must
reach zero and STAY there WHILE proofs go on timing out and being reported. Stillness proves
nothing: a corpus where no proof ever times out would read zero with the arm still writing red.
So ``enough`` asks for thirty days at zero AND at least one timeout on the tester's own trail in
the window — the trail ``device.run_proof`` writes one file per run, TIMEOUT runs included, at
``~/.cairn/logs/tester/0/<ts>.TesterDevice.run_proof.json``.

Two readings, files only:

  1. THE RECORD OF TRUTH. Every ``validations/*.json`` across both roots, last record: count
     verdict ``red`` with a ``timed out after`` stderr_tail (the defect this ticket was cast
     against), and count verdict ``timeout`` (a timeout is NEVER persisted — one on disk means
     the guard at device.py's persist site is gone).
  2. THE TRAFFIC. The tester's emit trail, counted for ``values.verdict == "timeout"`` inside
     the window — the evidence that the arm is still being exercised.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that re-opens a
node whose intention did not work is the OWNER's act (Law 6).

FILES ONLY — no device, no bus, no network, no subprocess, so it stays cheap enough to sit on a
pulse.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from cairn.tools.base.probe import Probe, once, owning_ticket

_OWNING_TICKET = "3dfceaa272ec"

# Class-space root: this file is cairn/devices/tester/probes/<name>.py.
_CLASS_SPACE = Path(__file__).resolve().parents[4]
# The commons carries validations too — the human-proved quorum records — so a census that
# walked class-space alone would be blind to part of the population.
_COMMONS = _CLASS_SPACE.parent / "CairnCommons"
# The tester's own trail: one JSON per run_proof, written by DiagnosticBase.emit.
_TRAIL = Path.home() / ".cairn" / "logs" / "tester" / "0"

# MEASURED 2026-10-18 AT ARMING, across both roots: 0 standing red validations whose stderr_tail
# begins 'timed out after', 0 persisted at verdict timeout. Carried as CONTEXT, never asserted.
_AT_ARMING = {"red_timeouts": 0, "persisted_timeouts": 0}
_ARMED = "2026-10-18"

# The ticket's `enough`: thirty days at zero, with at least one timeout reported in the window.
_ENOUGH_DAYS = 30


def _days_since_arming() -> int:
    y, m, d = (int(p) for p in _ARMED.split("-"))
    return (date.today() - date(y, m, d)).days


def timeout_census() -> dict:
    """Every validation across both roots, last record: the two counts the falsifier names."""
    red_timeouts: list[str] = []
    persisted_timeouts: list[str] = []
    budgets: set[str] = set()
    unreadable: list[str] = []
    for root in (_CLASS_SPACE, _COMMONS):
        if not root.is_dir():
            continue
        for f in root.glob("**/validations/*.json"):
            try:
                trail = json.loads(f.read_text(encoding="utf-8"))
            except Exception as exc:
                unreadable.append(f"{f}: {exc}")
                continue
            if not trail or not isinstance(trail, list):
                continue
            last = trail[-1]
            tail = str((last.get("evidence") or {}).get("stderr_tail") or "")
            if last.get("verdict") == "red" and tail.startswith("timed out after"):
                red_timeouts.append(str(f))
                budgets.add(tail.splitlines()[0])
            if last.get("verdict") == "timeout":
                persisted_timeouts.append(str(f))
    return {
        "red_timeouts": len(red_timeouts),
        "red_timeout_files": red_timeouts,
        "persisted_timeouts": len(persisted_timeouts),
        "persisted_timeout_files": persisted_timeouts,
        "budgets_seen": sorted(budgets),
        "unreadable": unreadable,
        "fires": bool(red_timeouts or persisted_timeouts),
    }


def timeouts_reported(days: int = _ENOUGH_DAYS) -> int:
    """How many run_proof emits on the tester's trail carried verdict ``timeout`` in the window."""
    if not _TRAIL.is_dir():
        return 0
    since = datetime.now(timezone.utc) - timedelta(days=days)
    n = 0
    for f in _TRAIL.glob("*.TesterDevice.run_proof.json"):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
            if (rec.get("values") or {}).get("verdict") != "timeout":
                continue
            ts = datetime.fromisoformat(str(rec.get("ts")))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if ts >= since:
            n += 1
    return n


def _trigger(now, context: dict) -> bool:
    """TRUE when a timed-out run has landed in a record of truth — as a red, or as itself."""
    return once(context, "timeout_census", timeout_census)["fires"]


def _enough(context: dict) -> bool:
    """CLEARED once thirty days have passed at zero AND at least one timeout was reported.

    THE REPORTED CLAUSE IS WHAT KEEPS STILLNESS FROM CLEARING IT: a corpus where nothing ever
    timed out reads zero with the arm untested, and that is not the fact this ticket claims.
    """
    return (_days_since_arming() >= _ENOUGH_DAYS
            and not once(context, "timeout_census", timeout_census)["fires"]
            and once(context, "reported", lambda: timeouts_reported(_ENOUGH_DAYS)) >= 1)


def _carry(context: dict) -> dict:
    """The datum that rides back: both counts, the traffic, and the budgets seen."""
    c = once(context, "timeout_census", timeout_census)
    reported = once(context, "reported", lambda: timeouts_reported(_ENOUGH_DAYS))
    return {
        "red_timeouts": c["red_timeouts"],
        "red_timeout_files": c["red_timeout_files"],
        "persisted_timeouts": c["persisted_timeouts"],
        "persisted_timeout_files": c["persisted_timeout_files"],
        "timeouts_reported_in_window": reported,
        "budgets_seen": c["budgets_seen"],
        "unreadable_files": c["unreadable"],
        "at_arming": _AT_ARMING,
        "days_since_arming": _days_since_arming(),
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "the count of standing validations at verdict red whose evidence.stderr_tail begins "
            "'timed out after' must reach zero and stay there WHILE proofs go on timing out and "
            "being reported"),
        "suggests": (
            "a red whose stderr_tail begins 'timed out after' was written by a tester older than "
            "this ticket, or by an arm that has gone back to calling a timeout red — seal that "
            "proof again with a budget it fits inside and read device.py's TimeoutExpired arm; a persisted "
            "verdict 'timeout' means the persist site's guard is gone. If both counts are zero "
            "and this cleared with no timeout reported, the window was quiet, not proven."),
    }


# THE HORIZON. Same unit and same honest placeholder as the sibling probes: PULSES, because the
# shim counts pulses; 1000 is "clearly a long standing" against any beat rate we would pick.
_HORIZON = 1000

PROBE = Probe(
    why="the proof's teeth settle that a run over the budget writes nothing, prints its own column "
        "and still fails the run — today, in a fixture tree; whether a timed-out proof ever again "
        "lands as a red validation is a fact about live traffic, and the falsifier asks for zero "
        "WHILE timeouts keep being reported, so stillness cannot clear it",
    trigger=_trigger,
    to="tester",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
