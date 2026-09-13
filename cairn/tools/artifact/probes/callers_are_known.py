"""WATCHME probe: every_journaled_write_names_a_known_caller.

The artifact door journals WHO wrote each record of truth from the kernel's cgroup for
the caller — gate, cc or akien. The class ``unknown`` is the door saying it could not
tell, and a journal that fills with unknowns is a door that measures nothing: the
classification is a regex over this host's cgroup names, and the host drifts (a new
launcher, a renamed unit, a session started some way nobody measured on 2026-09-13).

The measurement, from the ticket's watchme: over both live journals, count entries by
caller class. FIRES when any entry names ``unknown`` — carrying the paths and cgroups so
the regex can be taught the new shape. ENOUGH once 500 non-genesis writes have landed
across all three classes with zero unknown AND the hand-edit route has been exercised
once (a ``hand-edit`` verb in either journal) — the horizon the ticket declared.

Ticket: 30531f6e1c5d-records-of-truth-change-only-through-the-artifact-door.
"""
from __future__ import annotations

import collections
import json

from cairn.tools.artifact import artifact as door
from cairn.tools.base.probe import Probe

ENOUGH_WRITES = 500


def _measure(context: dict) -> dict:
    by_class: collections.Counter = collections.Counter()
    unknown: list[dict] = []
    writes = 0
    hand_edits = 0
    for name, root in door.roots().items():
        try:
            entries = door.read_journal(root)
        except door.Refused as exc:
            context.setdefault("chain_faults", []).append(str(exc))
            continue
        for e in entries:
            if e.get("verb") == "genesis":
                continue
            writes += 1
            cls = (e.get("caller") or {}).get("class", "unknown")
            by_class[cls] += 1
            if cls == "unknown":
                unknown.append({"root": name, "path": e.get("path"),
                                "cgroup": (e.get("caller") or {}).get("cgroup"),
                                "at": e.get("at")})
            if e.get("verb") == "hand-edit":
                hand_edits += 1
    context.update({"writes": writes, "by_class": dict(by_class), "unknown": unknown,
                    "hand_edits": hand_edits})
    return context


def _trigger(now, context: dict) -> bool:
    _measure(context)
    return bool(context["unknown"]) or bool(context.get("chain_faults"))


def _carry(context: dict) -> dict:
    if "writes" not in context:
        _measure(context)
    n = len(context["unknown"])
    return {
        "writes": context["writes"],
        "by_class": context["by_class"],
        "unknown": context["unknown"][:20],
        "chain_faults": context.get("chain_faults", []),
        "finding": (
            "%d journaled write(s) name caller class UNKNOWN — the door could not read a "
            "gate, cc or akien off the caller's cgroup; teach cairn/tools/artifact/"
            "artifact.py the new unit shape, and until then these writes have no WHO" % n
        ) if n else (
            "every one of %d journaled writes names a known caller (%s)"
            % (context["writes"], context["by_class"])
        ),
    }


def _enough(context: dict) -> bool:
    if "writes" not in context:
        _measure(context)
    by = context["by_class"]
    return (context["writes"] >= ENOUGH_WRITES and not context["unknown"]
            and all(by.get(c, 0) > 0 for c in ("gate", "cc", "akien"))
            and context["hand_edits"] >= 1)


PROBE = Probe(
    why="the artifact door's whole claim is WHO wrote a record, read from the kernel; a "
        "caller it cannot classify is a write with no who, and the classifier is a regex "
        "over one host's unit names on one day. This fires on the first unknown so the "
        "regex is taught before the journal fills with them.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)
