"""house_paths.py <id> <commons> — the dirty house paths a close or prove step of ticket <id> commits, one per line.

Run with cwd = the cairn house tree. close.sh and prove.sh stage exactly these, never 'git add -u'
(ticket 91908f3b3bb3; measured 2026-11-19: close.sh's 'git add -u' swept an uncommitted proof edit into
38e3f8323 "39fdea889714: hollow sealed, verdict", pushed before BUILDME refused).

What a step writes in the house is a seal: the validation records of the ticket's own proofs. Crossings
commit their own history.json and state.json (79875eb17ac2, ee9637b02525), and 'bin/cairn cleanup' writes
nothing in the house (measured at 9996bf7186e3's PROVED close, 37dd9dc28). So a path belongs to the step
when it is a validations/*.json the ticket's plan names, or the validation beside a proof the plan names
(proofs/<stem>.py -> validations/<stem>.json); the plan is the ticket's top-level writes_to, every
decision's writes_to and bounds.in. Source, a proof included, is never selected: it lands by its own
hand's commit. The shared journal rides along only when a validation is selected.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # the repo root, so the helper imports
try:
    from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs
except ImportError:   # a transient script copy has no tree beside it: no flags, same behaviour as before
    def windowless_kwargs(*_a, **_k):
        return {}

JOURNAL = ".artifact-journal.jsonl"


def _dirty() -> set[str]:
    out = subprocess.run(["git", "status", "--porcelain", "-uall", "-z"],
                         capture_output=True, text=True, check=True,
                         **windowless_kwargs()).stdout
    paths, tokens, i = set(), out.split("\0"), 0
    while i < len(tokens):
        t = tokens[i]
        i += 1
        if len(t) < 4:
            continue
        paths.add(t[3:])
        if t[0] in "RC":
            i += 1
    return paths


def _plan(tid: str, commons: str) -> dict | None:
    hits = [p for p in glob.glob(os.path.join(commons, "tickets", f"{tid}-*.json"))
            if not p.endswith(".state.json")]
    if len(hits) != 1:
        print(f"house_paths: {len(hits)} plan files for {tid} under {commons}/tickets; nothing selected",
              file=sys.stderr)
        return None
    with open(hits[0], encoding="utf-8") as f:
        return json.load(f)


def _named(plan: dict) -> set[str]:
    named = set(plan.get("writes_to") or [])
    for d in plan.get("decisions") or []:
        if isinstance(d, dict):
            named |= set(d.get("writes_to") or [])
    named |= set((plan.get("bounds") or {}).get("in") or [])
    return {p for p in named if isinstance(p, str)}


def seals_of(paths: set[str]) -> set[str]:
    out = set()
    for p in paths:
        head, _, name = p.rpartition("/")
        parent, _, leaf = head.rpartition("/")
        if leaf == "validations" and name.endswith(".json"):
            out.add(p)
        elif leaf == "proofs" and name.endswith(".py"):
            out.add(f"{parent}/validations/{name[:-3]}.json" if parent else f"validations/{name[:-3]}.json")
    return out


def own_paths(tid: str, commons: str) -> list[str]:
    plan = _plan(tid, commons)
    if plan is None:
        return []
    dirty = _dirty()
    own = sorted(seals_of(_named(plan)) & dirty)
    if own and JOURNAL in dirty:
        own.append(JOURNAL)
    return own


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[0]:
        print("usage: house_paths.py <ticket id> <commons>   (cwd = the cairn house tree)", file=sys.stderr)
        return 2
    for p in own_paths(argv[0], argv[1]):
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
