"""WATCHME(does-a-red-re-run-alone-catch-contention) for ticket b7068b1ba431.

THE HYPOTHESIS IT WATCHES (outline 9.4.8.1.1, 0.6.1). The verdict runs its instruments
three at a time (e56a68e651c2), and the repo, /tmp, the network and git are shared by every
run in flight, so a red can be a neighbour's. CC's choice was to re-run each red once, alone,
after the pool drains, and to judge a red that turns green alone as contention. That is a
hypothesis, not a settled answer, and the proof cannot settle it: whether real contention
happens, and whether the re-runs are worth their seconds, are facts about live traffic.

WHAT IT READS. Every verdict berth newer than this ticket's PROVED crossing (the era floor),
and in each, every reading that carries a ``run_alone``. Berths before the era are not
counted: they were written before the re-run existed. Until the ticket is PROVED there is no
era and nothing is counted.

WHEN IT SPEAKS, AND WHAT SETTLES IT (the ticket's watchme spec, verbatim numbers):
  - settled once >= 20 post-era re-runs are recorded, or 30 days after PROVED, whichever is first;
  - HOLDS when >= 4 turned green alone and re-run seconds are <= 10% of all run seconds of the
    same verdicts (first runs plus re-runs);
  - otherwise cc_0 rewrites the hypothesis from the pairs.

FILES ONLY: no device, no bus, no subprocess. AUTHORITY: none; it deposits and pokes.
"""

from __future__ import annotations

import datetime
import glob
import json
import os
import re

from cairn.tools.base.address import instance_path
from cairn.tools.base.probe import Probe, Threshold, once, owning_ticket, watch_carry

_OWNING_TICKET = "b7068b1ba431"
_PACKETS = str(instance_path("chart", 0) / "packets")

_ENOUGH_RE_RUNS = 20
_ENOUGH_DAYS = 30
_HOLDS_CONTENTION = 4
_HOLDS_FRACTION = 0.10

_STAMP_RE = re.compile(r"verdict-(\d{8}T\d{6})-")


def era_floor(ticket_path: str | None = None):
    """The ticket's PROVED crossing, read from its log: the clearance reply that accepted
    target PROVED. None while the ticket has not crossed, or its log cannot be read."""
    path = ticket_path or owning_ticket(_OWNING_TICKET)
    log = re.sub(r"\.json$", ".log.jsonl", str(path))
    try:
        with open(log, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return None
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = row.get("reply") or {}
        if (row.get("gate") == "clearance" and reply.get("accepted")
                and reply.get("target") == "PROVED"):
            return datetime.datetime.fromisoformat(row["at"])
    return None


def _berthed_at(path: str):
    m = _STAMP_RE.search(os.path.basename(path))
    return datetime.datetime.strptime(m.group(1), "%Y%m%dT%H%M%S") if m else None


def _seconds(run) -> float:
    s = (run or {}).get("seconds")
    return float(s) if isinstance(s, (int, float)) else 0.0


def survey(packets_dir: str = _PACKETS, era=None) -> dict:
    """THE READING, over the verdict berths in ``packets_dir`` newer than ``era``.

    Takes both as arguments so a proof can hand it berths on either side of a floor. A berth
    that cannot be read, or whose name carries no stamp, is CARRIED in ``unreadable``, never
    skipped (Law 7)."""
    pairs, unreadable = [], []
    re_run_s = all_s = 0.0
    if era is not None:
        for path in sorted(glob.glob(os.path.join(packets_dir, "verdict-*.json"))):
            at = _berthed_at(path)
            if at is None:
                unreadable.append("%s: no stamp in the name" % path)
                continue
            if at <= era:
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    readings = json.load(fh).get("observed_runs") or []
            except (OSError, json.JSONDecodeError) as exc:
                unreadable.append("%s: %s" % (path, exc))
                continue
            for r in readings:
                if not isinstance(r, dict):
                    continue
                all_s += _seconds(r.get("run")) + _seconds(r.get("run_alone"))
                if "run_alone" not in r:
                    continue
                re_run_s += _seconds(r["run_alone"])
                first, alone = r.get("run") or {}, r["run_alone"]
                pairs.append({
                    "berth": path, "claim": r.get("claim"), "instrument": r.get("instrument"),
                    "first": {k: first.get(k) for k in ("exit", "seconds", "started", "ended")},
                    "alone": {k: alone.get(k) for k in ("exit", "seconds")},
                    "contention": bool(r.get("contention")),
                    "neighbours": r.get("neighbours") or []})
    contention = sum(1 for p in pairs if p["contention"])
    fraction = re_run_s / all_s if all_s else 0.0
    return {"era": era.isoformat() if era else None, "re_runs": len(pairs),
            "contention": contention, "pairs": pairs, "re_run_seconds": re_run_s,
            "all_run_seconds": all_s, "re_run_fraction": fraction,
            "unreadable": unreadable}


def _live() -> dict:
    era = era_floor()
    s = survey(_PACKETS, era)
    s["past_horizon"] = bool(era and datetime.datetime.now() >= era + datetime.timedelta(days=_ENOUGH_DAYS))
    return s


def _settled(context) -> bool:
    s = once(context, "survey", _live)
    return s["re_runs"] >= _ENOUGH_RE_RUNS or s["past_horizon"]


def _trigger(now, context: dict) -> bool:
    return _settled(context)


def _holds(context: dict) -> bool:
    s = once(context, "survey", _live)
    return s["contention"] >= _HOLDS_CONTENTION and s["re_run_fraction"] <= _HOLDS_FRACTION


def _carry(context: dict) -> dict:
    s = once(context, "survey", _live)
    return {
        "finding": ("%d post-era re-runs, %d turned green alone; re-runs cost %.1f%% of run "
                    "seconds" % (s["re_runs"], s["contention"], 100 * s["re_run_fraction"])),
        "shape": s,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "a red at width 3 may be a neighbour's, and one alone re-run after the pool drains "
            "tells the two apart at a price worth paying"),
        "suggests": (
            "cc_0 reviews outline 9.4.8.1.1 against the pairs: HOLDS at >= 4 contention reds "
            "and <= 10% of run seconds; 0 of 20, or > 25% of seconds, rewrites it to 'record "
            "the red as it came'; any other split, rewrite from the numbers"),
    }


PROBE = Probe(
    why="the proof settles that a red is re-run alone and judged by it in a fixture; whether "
        "live reds are ever a neighbour's, and whether the re-runs are worth their seconds, is "
        "a fact about live traffic that only post-era verdicts carry",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    verb="machines/watchme/watch",
    carry=watch_carry(_OWNING_TICKET, _carry, holds=_holds),
    enough=_settled,
    thresholds=(
        Threshold(_ENOUGH_RE_RUNS, "post-era re-runs that settle the hypothesis",
                  set_by="ticket b7068b1ba431 watchme.enough names the number"),
        Threshold(_ENOUGH_DAYS, "days after PROVED after which scarcity is the reading",
                  set_by="ticket b7068b1ba431 watchme.enough names the number"),
        Threshold(_HOLDS_CONTENTION, "re-runs that turned green alone for the hypothesis to hold",
                  set_by="ticket b7068b1ba431 watchme.enough names the number"),
        Threshold(_HOLDS_FRACTION, "re-run seconds over all run seconds for the hypothesis to hold",
                  set_by="ticket b7068b1ba431 watchme.enough names the number"),
    ),
)
