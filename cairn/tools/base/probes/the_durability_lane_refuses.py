"""PROBE — the-durability-lane-refuses-and-is-not-exempted

Berth for the WATCHME that ticket ``c2460ae6c3d1`` carries. Berthed beside
``cairn/tools/base`` because that is WHERE THE LANE LIVES — ``the_stones_are_pushed``,
the second lane of the PROVED exit gate (``transitions.inspect_durability``).

THE QUESTION: does the lane BITE, and is it left alone? A lane that has never refused
is indistinguishable from a lane that cannot — so enough is the FIRST real refusal
(proofs stub the ledger, so a line in it is a live one). A lane that sees twenty
consecutive PROVED crossings with no refusal is reading the wrong thing, not guarding a
clean corpus. And an exemption roster naming the lane is the lane being switched off:
that is a red on sight, whatever the counts say.
"""

from __future__ import annotations

import json
import os
import re

from cairn.tools.base.probe import Probe, owning_ticket, once

_OWNING_TICKET = "c2460ae6c3d1"
_LANE = "the_stones_are_pushed"
_CAIRN_ROOT = os.path.expanduser("~/dev/src/cairn")
_LEDGER = os.path.expanduser("~/.cairn/devices/cairn/0/machines/sail/durability_refusals.jsonl")
_ENOUGH_REFUSALS = 1
_SILENT_CROSSINGS = 20


def _lane_crossings() -> list[dict]:
    """Every PROVED crossing in class-space whose proof record carries the lane, by 'at'."""
    from cairn.tools.charter import projector
    out = []
    for root, _dirs, files in os.walk(_CAIRN_ROOT):
        if "history.json" not in files:
            continue
        path = os.path.join(root, "history.json")
        try:
            entries = projector.read_history(path)
        except Exception:
            continue
        for e in entries:
            if e.get("to") != "PROVED":
                continue
            lanes = [f for f in e.get("proved", []) if f.get("identity") == _LANE]
            if not lanes:
                continue
            repos = lanes[0].get("values", {}).get("repos", [])
            measured = [r for r in repos if r.get("measured")]
            out.append({
                "component": os.path.relpath(root, _CAIRN_ROOT),
                "at": e.get("at", ""),
                "max_ahead": max((r.get("ahead_of_upstream") or 0 for r in measured), default=0),
                "max_dirty": max((r.get("dirty_paths") or 0 for r in measured), default=0),
                "measured": len(measured),
            })
    out.sort(key=lambda c: c["at"])
    return out


def _refusals() -> int:
    try:
        with open(_LEDGER, encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
    except OSError:
        return 0


def _exemption_tenants() -> list[str]:
    """Any roster in transitions.py naming the lane — a live read of the module's rosters
    plus a grep of the source for a ``*_ROSTER`` whose tenants name the lane."""
    from cairn.tools.base import transitions
    tenants = []
    for name in ("_CLEARANCE_EXEMPT_ROSTER", "_EXEMPT_ROSTER"):
        roster = getattr(transitions, name, frozenset())
        if any(_LANE in str(t) for t in roster):
            tenants.append(name)
    src = open(transitions.__file__, encoding="utf-8").read()
    for m in re.finditer(r"^(\w+_ROSTER)\s*(?::[^=]*)?=\s*(.*?)(?=^\S)", src, re.M | re.S):
        if _LANE in m.group(2) and m.group(1) not in tenants:
            tenants.append(m.group(1))
    return tenants


def survey() -> dict:
    crossings = _lane_crossings()
    refusals = _refusals()
    tenants = _exemption_tenants()
    return {
        "lane_crossings": len(crossings),
        "latest": crossings[-1] if crossings else None,
        "max_ahead_seen": max((c["max_ahead"] for c in crossings), default=0),
        "max_dirty_seen": max((c["max_dirty"] for c in crossings), default=0),
        "refusals_ledgered": refusals,
        "exemption_tenants": tenants,
    }


def _trigger(now, context: dict) -> bool:
    s = once(context, "survey", survey)
    if s["exemption_tenants"]:
        return True
    if s["lane_crossings"] >= _SILENT_CROSSINGS and s["refusals_ledgered"] == 0:
        return True
    return False


def _enough(context: dict) -> bool:
    s = once(context, "survey", survey)
    return s["refusals_ledgered"] >= _ENOUGH_REFUSALS and not s["exemption_tenants"]


def _carry(context: dict) -> dict:
    s = once(context, "survey", survey)
    if s["exemption_tenants"]:
        finding = (f"EXEMPTED — {', '.join(s['exemption_tenants'])} names {_LANE}: the durability "
                   "lane has been switched off by roster, which is the corrosion this watch exists for")
    elif s["lane_crossings"] >= _SILENT_CROSSINGS and s["refusals_ledgered"] == 0:
        finding = (f"SILENT — {s['lane_crossings']} PROVED crossings carried the lane and it never "
                   "refused once: a lane that never sees unpushed work is reading the wrong thing")
    elif s["refusals_ledgered"] >= _ENOUGH_REFUSALS:
        finding = (f"BITES — {s['refusals_ledgered']} real refusal(s) ledgered across "
                   f"{s['lane_crossings']} lane-carrying PROVED crossings; the lane is physics")
    else:
        finding = (f"ACCUMULATING — {s['lane_crossings']}/{_SILENT_CROSSINGS} lane-carrying PROVED "
                   f"crossings, {s['refusals_ledgered']}/{_ENOUGH_REFUSALS} refusals, "
                   f"max dirty journaled {s['max_dirty_seen']}")
    return {"finding": finding, "survey": s, "ticket": owning_ticket(_OWNING_TICKET)}


PROBE = Probe(
    why="a PROVED crossing over unpushed stones is a green nobody else can pull (Law 8); "
        "this probe watches whether the durability lane actually bites — the first real "
        "refusal is the proof it can — and reds if it goes silent over twenty crossings or "
        "if an exemption roster ever names it",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "the-durability-lane-refuses-and-is-not-exempted"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)


if __name__ == "__main__":
    s = survey()
    print(json.dumps({
        "survey": s,
        "would_trigger": _trigger(None, {"survey": s}),
        "enough": _enough({"survey": s}),
        "carry": _carry({"survey": s}),
    }, indent=2, default=str))
