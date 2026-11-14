"""compile — a block's engine traces read into a deterministic floor (ticket e889b197a3f6).

Law 1: a decision the engine has settled again and again should be code, not another run.
The engine records every run as a state log (engine.py). This module reads one block's
training-typed ``engine_run`` records and emits a FLOOR: data that ``apply_floor`` runs, with
no inference, to reproduce each traced decision (winner or escalation) from the run's
candidates.

WHAT THE FLOOR LEARNS FROM — the kills (outline 16.1.3, CC's decision on Q#97): the runs that
teach are the ones whose candidates something killed. In librarian-ask, those are the backfill
runs, where carries_his_answer killed 5, 6 and 5 of 6 candidates. A run that killed nothing
only shows the engine agreeing with itself, so it teaches no rule. EVERY run is the floor's
agreement check: a floor that cannot reproduce its own corpus is refused, not written (Law 8).

THE RULE SHAPE. For each constraint the corpus saw kill something, the compile finds every
``provides`` key whose values separate that constraint's kills from its passes with no
overlap. The rule is an ALLOW-LIST per such key: a candidate survives the constraint only when
each of its values is one the constraint passed. A value the corpus never showed is killed, so an unseen case
escalates rather than guesses. The decide order is the engine's: the first survivor in the
run's candidate order wins, and a run with no survivor escalates to the corpus's one target.

THE REFUSAL names every lack in one pass (DoorRefused, the DOOR organ's shape):
  - fewer than MIN_DISTINCT runs of distinct input: a corpus that repeats itself can only be
    memorised;
  - any candidate record without ``provides``: the features the constraints judged were
    dropped, and nothing can be learned from a name;
  - no rejection anywhere: nothing was ruled out, so there is nothing to learn;
  - a constraint whose kills no single provides key separates (it may judge against the
    run's input through a ``{"fact": f}``, which a provides-only floor cannot learn);
  - no escalation in the corpus, or more than one target;
  - a floor that disagrees with any run it was compiled from.

The floor berths under the holder that compiled it (outline 16.4.3; CLAUDE.md, a held
machine's state hangs off its holder):
``~/.cairn/devices/<holder>/<n>/machines/learning_block/floors/<block>.json``. Its body has
sorted keys and no timestamps, so two compiles over one corpus write the same bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.address import machine_path
from cairn.machines.learning_block.engine import RUN_EVENT
from cairn.machines.learning_block.learning_block import (
    DoorRefused, TraceRefused, _holder, read_trace,
)

MIN_DISTINCT = 5
_MACHINE = "learning_block"


def _key(value) -> str:
    """A provides value as a comparable, sortable token (lists and dicts included)."""
    return json.dumps(value, sort_keys=True)


def _holder_or_refuse(block: str, holder) -> tuple[str, int]:
    try:
        return _holder(holder)
    except TraceRefused as e:
        raise DoorRefused(block, [{"field": "holder", "why": str(e)}]) from None


def floor_path(block: str, *, holder: str, floors_root: Path | None = None) -> Path:
    """Where ``block``'s floor berths: under its holder, or under ``floors_root`` for proofs."""
    if floors_root is None:
        device, n = _holder_or_refuse(block, holder)
        floors_root = machine_path(device, n, _MACHINE) / "floors"
    return Path(floors_root) / (str(block).replace(":", "__") + ".json")


def _learn_rule(name: str, runs: list[dict]) -> dict | None:
    """The allow-list rule for constraint ``name``: ``{key: [allowed values]}`` for EVERY
    provides key that separates its kills from its passes, or None when no key does. When
    several separate, the corpus cannot say which one the constraint reads, so the floor
    requires all of them: that can only add kills, i.e. escalate more, never answer wrongly."""
    cands = [c for run in runs for c in run["data"]["candidates"]]
    kills = [c for c in cands if name in (c.get("killed_by") or [])]
    passes = [c for c in cands if name not in (c.get("killed_by") or [])]
    keys = sorted({k for c in cands for k in (c.get("provides") or {})})
    rule = {}
    for k in keys:
        # a key some killed candidate lacks cannot be what killed it
        if any(k not in (c.get("provides") or {}) for c in kills):
            continue
        killed = {_key(c["provides"][k]) for c in kills}
        allows = {_key(c["provides"][k]) for c in passes if k in (c.get("provides") or {})}
        if not (allows & killed):
            rule[k] = sorted(allows)
    return rule or None


def apply_floor(floor: dict, payload: dict, candidates: list[dict]) -> dict:
    """Run the floor over one task: ``candidates`` are ``{name, provides}`` in preference
    order. Returns ``{winner, escalation, killed_by}``, where ``winner`` is a name or None
    and ``escalation`` the target or None. Pure; ``payload`` is accepted for the engine's
    signature and read by no rule today."""
    killed_by = {}
    for c in candidates:
        provides = c.get("provides") or {}
        killed_by[c["name"]] = sorted(
            name for name, rule in floor["rules"].items()
            if any(k not in provides or _key(provides[k]) not in allows
                   for k, allows in rule.items()))
    survivors = [c["name"] for c in candidates if not killed_by[c["name"]]]
    winner = survivors[0] if survivors else None
    return {"winner": winner, "escalation": None if winner else floor["escalation"],
            "killed_by": killed_by}


def _outcome(run: dict) -> tuple:
    d = run["data"]
    return ((d.get("winner") or {}).get("name"), (d.get("escalation") or {}).get("to"))


def compile_floor(block: str, *, holder: str, root: Path | None = None,
                  floors_root: Path | None = None) -> dict:
    """Compile ``block``'s training engine_run traces into a floor and write it under
    ``holder``. Returns ``{"floor": <body>, "path": <str>}``. Raises DoorRefused with every
    lack named. ``root`` is the trace root (default: the holder's); ``floors_root`` overrides
    where the floor is written, for proofs."""
    _holder_or_refuse(block, holder)
    runs = [r for r in read_trace(block, root=root, holder=holder)
            if r.get("event") == RUN_EVENT and r.get("consumer") == "training"]
    lacks: list[dict] = []

    distinct = {_key((r.get("data") or {}).get("input")) for r in runs}
    if len(distinct) < MIN_DISTINCT:
        lacks.append({"field": "corpus",
                      "why": f"{len(runs)} run(s) of {len(distinct)} distinct input, fewer than "
                             f"{MIN_DISTINCT}: a corpus that repeats itself can only be memorised"})

    cands = [c for r in runs for c in (r.get("data") or {}).get("candidates") or []]
    bare = [c.get("name") for c in cands if not isinstance(c.get("provides"), dict)]
    if bare:
        lacks.append({"field": "candidates[].provides",
                      "why": f"{len(bare)} of {len(cands)} candidate record(s) carry no provides "
                             "(e.g. %r): the features the constraints judged were dropped, and "
                             "a name alone teaches nothing" % bare[0]})

    killers = sorted({k for c in cands for k in (c.get("killed_by") or [])})
    if not killers:
        lacks.append({"field": "candidates[].killed_by",
                      "why": "no candidate in the corpus was killed: nothing was ruled out, so "
                             "there is nothing to learn (outline 16.1.3: the floor learns from "
                             "the kills)"})

    targets = sorted({to for r in runs
                      for to in [((r.get("data") or {}).get("escalation") or {}).get("to")]
                      if to})
    if len(targets) != 1:
        lacks.append({"field": "escalation",
                      "why": (f"the corpus escalated to {targets}, more than one target"
                              if targets else
                              "no run in the corpus escalated, so the floor cannot say whose "
                              "gate a run with no survivor stands at")})

    rules: dict[str, dict] = {}
    if not bare:
        for name in killers:
            rule = _learn_rule(name, runs)
            if rule is None:
                lacks.append({"field": f"rule:{name}",
                              "why": f"no provides key separates what {name!r} killed from what "
                                     "it passed; it may judge against the run's input, which a "
                                     "provides-only floor cannot learn"})
            else:
                rules[name] = rule

    if lacks:
        raise DoorRefused(block, lacks)

    floor = {"block": block, "rules": rules, "escalation": targets[0],
             "order": "the run's candidate order; the first survivor wins",
             "compiled_from": {"runs": sorted(r["id"] for r in runs),
                               "distinct_inputs": len(distinct),
                               "rejections": sum(1 for c in cands if c.get("killed_by"))}}

    disagree = []
    for r in runs:
        got = apply_floor(floor, r["data"].get("input") or {}, r["data"]["candidates"])
        if (got["winner"], got["escalation"]) != _outcome(r):
            disagree.append(r["id"])
    if disagree:
        raise DoorRefused(block, [{"field": "agreement",
                                   "why": f"the floor disagrees with {len(disagree)} run(s) it "
                                          f"was compiled from ({sorted(disagree)[:5]}): it "
                                          "cannot reproduce its own corpus (Law 8)"}])

    path = floor_path(block, holder=holder, floors_root=floors_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(floor, indent=1, sort_keys=True) + "\n", encoding="utf-8",
                    newline="\n")
    return {"floor": floor, "path": str(path)}
