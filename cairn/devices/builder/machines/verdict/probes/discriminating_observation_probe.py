"""PROBE — the_discriminating_observation_names_a_second_tree

Berth for the WATCHME that ticket
``an-instrument-that-cannot-bite-is-refused-at-the-verdict`` carries.
Berthed beside ``cairn/devices/builder/machines/verdict`` because that is
WHAT IT WATCHES — the verdict artifacts going through write_verdict.

THE QUESTION: does a discriminating_observation that is required to be
non-empty actually name a CHECKABLE second reading (a commit hash, a
worktree path, a mutated line, a reverted disposition) — or is it prose
that happens to satisfy the non-empty check? The field was built to catch
hollow instruments; this probe watches whether the field itself is hollow.

THE HIDDEN ASSUMPTION, named at the ticket: a builder who took no
discriminating observation will say so instead of writing a plausible
sentence. The early stop at n>=4 and falling-below-half is aimed at
exactly that.
"""

from __future__ import annotations

import datetime
import glob
import json
import re

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "an-instrument-that-cannot-bite-is-refused-at-the-verdict"
_PACKETS = "/home/akien/.cairn/devices/chart/0/packets"
_ENOUGH_COUNT = 10
_DEADLINE = datetime.date(2026, 9, 17)

_SECOND_TREE_PATTERNS = [
    re.compile(r"\b[0-9a-f]{7,40}\b"),           # git commit hash
    re.compile(r"worktree", re.IGNORECASE),       # worktree reference
    re.compile(r"\brevert", re.IGNORECASE),       # revert / reverted
    re.compile(r"\bmutat", re.IGNORECASE),        # mutate / mutated / mutation
    re.compile(r"\bremoving lines?\b", re.IGNORECASE),
    re.compile(r"\bdeleting\b", re.IGNORECASE),
    re.compile(r"\bwithout (the|lines|this)\b", re.IGNORECASE),
]


def _read_new_verdicts() -> list[dict]:
    """Read verdict artifacts that carry discriminating_observation."""
    results = []
    for vp in sorted(glob.glob(f"{_PACKETS}/verdict-*.json")):
        d = json.load(open(vp))
        for i, v in enumerate(d.get("verdicts", [])):
            obs = v.get("discriminating_observation")
            if isinstance(obs, str) and obs.strip():
                results.append({
                    "file": vp,
                    "criterion_index": i,
                    "claim": v.get("claim", ""),
                    "observation": obs,
                })
    return results


def _names_second_tree(obs: str) -> bool:
    return any(p.search(obs) for p in _SECOND_TREE_PATTERNS)


def _classify(observations: list[dict]) -> dict:
    names_tree = [o for o in observations if _names_second_tree(o["observation"])]
    prose_only = [o for o in observations if not _names_second_tree(o["observation"])]
    n = len(observations)
    fraction = len(names_tree) / n if n else 0.0
    return {
        "total": n,
        "names_second_tree": len(names_tree),
        "prose_only": len(prose_only),
        "fraction_naming_tree": round(fraction, 3),
        "details_tree": [{"claim": o["claim"], "observation": o["observation"][:120]}
                         for o in names_tree[:5]],
        "details_prose": [{"claim": o["claim"], "observation": o["observation"][:120]}
                          for o in prose_only[:5]],
    }


def survey() -> dict:
    observations = _read_new_verdicts()
    classified = _classify(observations)
    classified["past_deadline"] = datetime.date.today() >= _DEADLINE
    return classified


def _trigger(now, context: dict) -> bool:
    """TRUE when new verdicts with the field exist — any new data is worth reporting."""
    s = context.get("survey") or survey()
    return s["total"] > 0


def _enough(context: dict) -> bool:
    s = context.get("survey") or survey()
    if s["past_deadline"]:
        return True
    if s["total"] >= _ENOUGH_COUNT:
        return True
    if s["total"] >= 4 and s["fraction_naming_tree"] < 0.5:
        return True
    return False


def _carry(context: dict) -> dict:
    s = context.get("survey") or survey()
    if s["total"] >= 4 and s["fraction_naming_tree"] < 0.5:
        finding = (
            f"EARLY STOP — {s['names_second_tree']}/{s['total']} observations name a "
            f"second tree (fraction {s['fraction_naming_tree']}). The hidden assumption "
            "is failing: builders are writing plausible prose rather than naming a "
            "checkable second reading. The answer is a runnable instrument form, not "
            "more watching"
        )
    elif s["total"] >= _ENOUGH_COUNT:
        finding = (
            f"{s['names_second_tree']}/{s['total']} discriminating observations name "
            f"a second tree (fraction {s['fraction_naming_tree']})"
        )
    elif s["past_deadline"]:
        finding = (
            f"DEADLINE — {s['names_second_tree']}/{s['total']} observations name "
            f"a second tree at the 2026-09-17 horizon"
        )
    else:
        finding = (
            f"ACCUMULATING — {s['total']}/{_ENOUGH_COUNT} verdicts with the field so far, "
            f"{s['names_second_tree']} naming a second tree"
        )
    return {
        "finding": finding,
        "classified": s,
        "ticket": owning_ticket(_OWNING_TICKET),
    }


_HORIZON = 1000

PROBE = Probe(
    why="the discriminating_observation field was built to stop hollow instruments — "
        "but a non-empty string that names no second tree is itself hollow, and the "
        "check cannot tell prose from a real observation. This probe watches whether "
        "builders actually name a checkable second reading (commit, worktree, mutation, "
        "revert) or write plausible prose that satisfies the gate",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "the_discriminating_observation_names_a_second_tree"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey()
    print(json.dumps({
        "survey": s,
        "would_trigger": _trigger(None, {"survey": s}),
        "enough": _enough({"survey": s}),
        "carry": _carry({"survey": s}),
    }, indent=2, default=str))
