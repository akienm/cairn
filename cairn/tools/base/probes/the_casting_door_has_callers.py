"""WATCHME(the-casting-door-has-callers) — does the casting door keep its callers, and does
anything still arrive beside it? (ticket 23089d52d805, 2026-09-18)

THE FAILURE SHAPE THIS WATCHES FOR IS THE ONE THE DOOR NEXT TO IT MEASURED. The phase door
in transitions.py was built 2026-09-08, took 13 records in four days, and then had no
caller at all — physics from the outside, writes going round it on the inside. The
ticket's WRONG INTENT clause names exactly that for the casting door: "a door with no
callers is worse than no door."

WHAT IT READS: the commons artifact journal, and only that — the door writes nothing else.
An ARRIVAL is a creation entry (``sha_before == "absent"``) naming ``tickets/<x>.json``,
in journal order, at or after the LANDING (the earliest entry carrying transitions.py's
own ``cast_ticket`` frame — derived every pulse, stored nowhere). Each arrival is classed
by ``cairn.tools.base.cast.classify``: ``through_the_door`` or ``journaled_beside``. A
ticket standing in tickets/ with NO journal entry at all is ``unjournaled`` — the hand
that dropped a file — and counts against the watch the moment it appears.

ENOUGH (the ticket's watchme.enough, verbatim in its numbers): ten consecutive casts
journaled through the door with zero arrivals beside it, across at least three distinct
calendar days. One arrival beside the door re-opens it — the last ten are re-read every
pulse, so enough goes back down rather than coasting on a run that was true last week.

NO ``thresholds=`` HERE, DELIBERATELY: HEAD's Probe carries no such field. Ticket
336a781018ba's migration (uncommitted at this build) declares every probe's numbers and
must declare these two — ``_ENOUGH_CASTS`` and ``_ENOUGH_DAYS`` — when it lands.

The commons root comes from the pulse context's roots table (``context["roots"]["commons"]``)
when the holder hands one, else the live commons beside the repo; a proof hands it a scratch
one. The probe carries no authority (Law 6): it deposits and pokes.
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.cast import classify
from cairn.tools.base.probe import Probe, once, owning_ticket

_REPO_ROOT = Path(__file__).resolve().parents[4]
_COMMONS = _REPO_ROOT.parent / "CairnCommons"

_OWNING_TICKET = "23089d52d805"

_ENOUGH_CASTS = 10
_ENOUGH_DAYS = 3
_HORIZON = 1000


def _commons_root(context: dict | None) -> Path:
    roots = (context or {}).get("roots") if isinstance(context, dict) else None
    if isinstance(roots, dict) and roots.get("commons"):
        return Path(roots["commons"])
    return _COMMONS


def survey_the_casts(commons_root: Path | None = None) -> dict:
    """One read of the journal: the landing, every arrival since it in order, and the
    hand-dropped files standing in tickets/ with no entry at all."""
    root = _COMMONS if commons_root is None else Path(commons_root)
    try:
        from cairn.tools.artifact import artifact as door
        entries = door.read_journal(root)
    except Exception:  # noqa: BLE001 — a journal the probe cannot read is a loud empty, not a crash
        entries = []
    creations = [e for e in entries
                 if isinstance(e.get("path"), str) and e["path"].startswith("tickets/")
                 and not e["path"].split("/")[-1].startswith("_")
                 and e.get("sha_before") == "absent" and e.get("verb") != "genesis"]
    landing = next((e for e in creations if classify(e) == "through_the_door"), None)
    arrivals: list[dict] = []
    if landing is not None:
        seen = False
        for e in creations:
            if e is landing:
                seen = True
            if seen:
                arrivals.append({"path": e["path"], "at": str(e.get("at") or ""),
                                 "class": classify(e)})
    named = {e["path"] for e in entries if isinstance(e.get("path"), str)}
    tickets_dir = root / "tickets"
    try:
        unjournaled = sorted("tickets/" + p.name for p in tickets_dir.glob("*.json")
                             if not p.name.startswith("_") and "tickets/" + p.name not in named)
    except OSError:
        unjournaled = []
    beside = [a["path"] for a in arrivals if a["class"] != "through_the_door"]
    last = arrivals[-_ENOUGH_CASTS:]
    run_clean = (len(last) >= _ENOUGH_CASTS
                 and all(a["class"] == "through_the_door" for a in last))
    days = sorted({a["at"][:10] for a in last if a["at"]})
    return {
        "landing": None if landing is None else landing.get("at"),
        "arrivals": len(arrivals),
        "through_the_door": sum(1 for a in arrivals if a["class"] == "through_the_door"),
        "journaled_beside": beside,
        "unjournaled": unjournaled,
        "last_run_clean": run_clean,
        "days_in_last_run": days,
    }


def _survey(context: dict) -> dict:
    return once(context, "casts", lambda: survey_the_casts(_commons_root(context)))


def _enough(context: dict) -> bool:
    s = _survey(context)
    return (s["arrivals"] >= _ENOUGH_CASTS and s["last_run_clean"]
            and len(s["days_in_last_run"]) >= _ENOUGH_DAYS
            and not s["journaled_beside"] and not s["unjournaled"])


def _trigger(now, context: dict) -> bool:
    """TRUE once anything has arrived since the landing and the watch is not yet enough —
    a door with one caller and then silence, or a door with arrivals beside it."""
    s = _survey(context)
    return s["arrivals"] >= 1 and not _enough(context)


def _carry(context: dict) -> dict:
    s = _survey(context)
    if s["journaled_beside"] or s["unjournaled"]:
        finding = "tickets are arriving beside the casting door"
    elif s["arrivals"] < _ENOUGH_CASTS:
        finding = "the casting door has fewer than ten casts since it landed"
    else:
        finding = "the last ten casts span fewer than three calendar days"
    return {
        "finding": finding,
        "counts": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": ("WRONG INTENT if the door lands and hand-written tickets continue "
                              "beside it — a door with no callers reads as physics from the "
                              "outside while the writes go round it."),
        "suggests": ("ask which is true: nothing fires `cairn cast` at the moment /sorted "
                     "resolves, or casting through the door costs more than writing the file."),
    }


PROBE = Probe(
    why="does the casting door keep its callers, and does anything still arrive beside it? — "
        "the phase door beside it took 13 records in four days and then sat with no caller",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps(survey_the_casts(), indent=2))
