"""PROBE — does the mail lane get worked?

Berth for the WATCHME that ticket ``mail-arrives-and-what-cannot-marks-itself`` (7cb1989e7825)
carries. Berthed beside ``cairn/tools/base`` because that is WHAT IT WATCHES: the base shim's
bounce lane raises the ``mail-*`` troubles (the sender raises, Akien 2026-08-11) and a shim's
genuine take clears them — the same berth as the parent's does-the-bounce-blame-the-right-party.

THE PREMISE UNDER TEST is Akien's: a self-maintaining marker lane gets WORKED. Each ``mail-*``
trouble names a device that cannot take its mail; building the receiver clears it by itself.
If they accumulate instead of draining, the lane is a second hand-kept list nobody reads.

WHAT IT COUNTS, over ``CairnCommons/troubles/mail-*.json`` first seen after the era floor:
raised, cleared (standing CLEARED), live with each one's age, and recurrences (prior_attempts
above zero — the trouble device's fold for a raise on a cleared identity).

THE ERA FLOOR is read, never hand-written: the ``at`` of the last entry in the bus's
``history.json`` whose ticket is this one and whose ``to`` is PROVED. Before that entry exists
the era has not begun and there is nothing to count. If the history holds NO entry for this
ticket at all, it has been moved to the commons (Law 5) and the survey is HOLLOW — the trigger
fires so the probe is repaired, never silently counting from nothing.

A RISING MEDIAN, MEASURED WITHOUT MEMORY: the probe holds no state between firings, so
"rising" is read off the store itself — the median age of the live troubles stands above the
median time the cleared ones took to clear. The lane is then filling faster than it drains.

FILES ONLY, by construction — like its parent. What evaluates it on the mail-* raise/clear
event is 164da559823d / acb4ecd84364's to build, not this ticket's.

AUTHORITY: none. This probe deposits and pokes; the back-edge is the owner's act (Law 6).
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket, once, watch_carry

_OWNING_TICKET = "mail-arrives-and-what-cannot-marks-itself"
_TICKET_ID = "7cb1989e7825"

_STALE_DAYS = 14
_CROWDED_LIVE = 20
_ENOUGH_RAISED = 8
_ENOUGH_CLEARED = 6


def _trouble_root() -> Path:
    return Path.home() / "dev" / "src" / "CairnCommons" / "troubles"


def _history_path() -> Path:
    return (Path(__file__).resolve().parents[3]
            / "devices" / "cairn" / "machines" / "bus" / "history.json")


def era_floor(history: Path | None = None) -> tuple[str | None, str | None]:
    """(floor, hollow): the PROVED crossing's ``at``, or why there is none to read."""
    path = history or _history_path()
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"the bus history cannot be read: {type(exc).__name__}: {exc}"
    mine = [e for e in entries if isinstance(e, dict) and e.get("ticket") == _TICKET_ID]
    if not mine:
        return None, (f"{path} holds no entry for {_TICKET_ID} — moved to the commons (Law 5)? "
                      "the era floor must be re-pointed")
    proved = [e for e in mine if e.get("to") == "PROVED" and e.get("at")]
    return (proved[-1]["at"] if proved else None), None


def _parse(stamp: str | None):
    try:
        born = datetime.fromisoformat(stamp or "")
    except (ValueError, TypeError):
        return None
    return born if born.tzinfo else born.replace(tzinfo=timezone.utc)


def survey_mail_lane(*, root: Path | None = None, history: Path | None = None,
                     now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    floor, hollow = era_floor(history)
    base = {"era_floor": floor, "hollow": hollow, "begun": floor is not None,
            "raised": 0, "cleared": 0, "live": [], "recurred": [], "clear_days": []}
    if hollow or floor is None:
        return base
    troubles_root = root or _trouble_root()
    if not troubles_root.exists():
        return {**base, "hollow": f"the troubles root {troubles_root} does not exist"}
    floor_at = _parse(floor)
    for p in sorted(troubles_root.glob("mail-*.json")):
        try:
            t = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        born = _parse(t.get("first_seen")) if isinstance(t, dict) else None
        if born is None or floor_at is None or born <= floor_at:
            continue
        base["raised"] += 1
        tid = t.get("id", p.stem)
        if (t.get("prior_attempts") or 0) > 0:
            base["recurred"].append(tid)
        if t.get("standing") == "CLEARED":
            base["cleared"] += 1
            done = _parse(((t.get("cleared_by") or [{}])[-1]).get("at"))
            if done is not None:
                base["clear_days"].append((done - born).total_seconds() / 86400)
        else:
            base["live"].append({"id": tid,
                                 "age_days": round((now - born).total_seconds() / 86400, 1)})
    return base


def _measures(s: dict) -> dict:
    ages = [t["age_days"] for t in s["live"]]
    stale = [t["id"] for t in s["live"] if t["age_days"] > _STALE_DAYS]
    live_median = statistics.median(ages) if ages else 0.0
    clear_median = statistics.median(s["clear_days"]) if s["clear_days"] else 0.0
    crowded = len(ages) > _CROWDED_LIVE and live_median > clear_median
    return {"stale": stale, "live_median_days": round(live_median, 1),
            "clear_median_days": round(clear_median, 1), "crowded": crowded}


def _survey(context: dict) -> dict:
    return once(context, "survey", survey_mail_lane)


def _trigger(now, context: dict) -> bool:
    """TRUE when the lane accumulates instead of draining — or the survey is hollow."""
    s = _survey(context)
    if s["hollow"]:
        return True
    if not s["begun"]:
        return False
    m = _measures(s)
    return bool(m["stale"]) or m["crowded"]


def _enough(context: dict) -> bool:
    """CLEARED when the lane is seen worked: >= 8 raised, >= 6 cleared, none live past 14 days."""
    s = _survey(context)
    if s["hollow"] or not s["begun"]:
        return False
    return (s["raised"] >= _ENOUGH_RAISED and s["cleared"] >= _ENOUGH_CLEARED
            and not _measures(s)["stale"])


def _carry(context: dict) -> dict:
    s = _survey(context)
    m = _measures(s)
    parts = []
    if s["hollow"]:
        parts.append(f"the survey is HOLLOW — {s['hollow']}")
    elif not s["begun"]:
        parts.append(f"the era has not begun — {_TICKET_ID} has no PROVED crossing in the bus history")
    if m["stale"]:
        parts.append(f"{len(m['stale'])} mail trouble(s) live > {_STALE_DAYS} days: {m['stale']}")
    if m["crowded"]:
        parts.append(f"{len(s['live'])} live mail troubles with median age "
                     f"{m['live_median_days']}d above the median clear time "
                     f"{m['clear_median_days']}d — the lane fills faster than it drains")
    return {
        "finding": "; ".join(parts) or (
            f"the mail lane is worked — {s['cleared']}/{s['raised']} cleared, none stale"),
        "counts": {"raised": s["raised"], "cleared": s["cleared"], "live": len(s["live"]),
                   "recurred": len(s["recurred"])},
        "live_ages": s["live"],
        "recurred_ids": s["recurred"],
        "medians": {"live_days": m["live_median_days"], "clear_days": m["clear_median_days"]},
        "era_floor": s["era_floor"],
        "thresholds": {"stale_days": _STALE_DAYS, "crowded_live": _CROWDED_LIVE,
                       "enough_raised": _ENOUGH_RAISED, "enough_cleared": _ENOUGH_CLEARED},
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "the WATCHME's premise: a self-maintaining marker lane gets worked — mail-* "
            "troubles clear by themselves when the receiver is built; a stale or crowding "
            "lane says it became a hand-kept list nobody works"),
        "suggests": (
            "repair the probe's era floor" if s["hollow"] else
            "nothing to count until the PROVED crossing" if not s["begun"] else
            "read each stale mail trouble: its addressee still has no receiver"
            if m["stale"] else
            "the lane is crowding — ask why receivers are not being built"
            if m["crowded"] else
            "no action needed"),
    }


_HORIZON = 1000

PROBE = Probe(
    why="does the mail lane get worked? — mail-* troubles that stand past 14 days, or "
        "crowd past 20 with a rising age, say the self-maintaining list is not being worked",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    verb="watch",
    carry=watch_carry(_TICKET_ID, _carry, fails=_trigger),
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps(_carry({}), indent=2, default=str))
