"""validate — the compiled floor beside the engine path on fresh tasks (ticket 6b4209e39982).

A floor that reproduces its own corpus (compile.py's agreement check) may only have memorised
it. The claim worth trusting (Law 8) is that the floor agrees with the engine on tasks it was
NOT compiled from, and does so cheaper. ``validate_floor`` runs each fresh payload down both
paths and reports, per payload, the two outcomes, the verdict, and each path's cost.

THE VERDICT per payload:
  - ``agree``: same winner, or both escalate to the same target;
  - ``abstain``: the floor escalates where the engine named a winner. It did not guess, but
    it did not do the work either, so it does not count as agreement;
  - ``disagree``: anything else, i.e. the floor named a different winner, or named one where
    the engine escalated.
The report passes only when every payload agrees.

FRESH MEANS FRESH. A payload whose input appears in any run the floor was compiled from is
refused, all such payloads named in one DoorRefused. The source runs are read back from the
traces by the ids the floor records, and a floor whose source runs cannot all be found is
refused too, because then freshness cannot be shown.

THE COST, each path measured and never assumed (Law 3):
  - inference calls on the engine path are read from the injected model path's own
    ``inference_calls`` counter (before and after each call). A model path that carries no
    counter reports ``None``, i.e. unmeasured, never 0;
  - the floor path's calls are counted the same way, through ``apply``'s counter when it has
    one. ``apply_floor`` is pure and calls no model, so its count is 0 by measurement of the
    call it makes: none;
  - wall ms on each path is taken with ``time.perf_counter``.

The engine path writes its traces under ``root``, which the caller must name and which must
not be the floor's source root: a validation run that landed in the training corpus would
make the next compile's fresh tasks stale.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from cairn.machines.learning_block.compile import apply_floor
from cairn.machines.learning_block.engine import RUN_EVENT, run_block
from cairn.machines.learning_block.learning_block import DoorRefused, read_trace


def _key(value) -> str:
    return json.dumps(value, sort_keys=True)


def _calls(fn):
    n = getattr(fn, "inference_calls", None)
    return n if isinstance(n, int) else None


def _source_inputs(floor: dict, *, source_root, holder) -> tuple[set, list]:
    ids = set((floor.get("compiled_from") or {}).get("runs") or [])
    found = {r["id"]: (r.get("data") or {}).get("input")
             for r in read_trace(floor["block"], root=source_root, holder=holder)
             if r.get("event") == RUN_EVENT and r.get("id") in ids}
    return {_key(v) for v in found.values()}, sorted(ids - set(found))


def _verdict(engine: tuple, floor: tuple) -> str:
    if engine == floor:
        return "agree"
    if floor[0] is None and engine[0] is not None:
        return "abstain"
    return "disagree"


def validate_floor(floor: dict, spec, fresh_payloads: list[dict], *, root: Path,
                   source_root: Path | None = None, holder: str | None = None,
                   model_path=run_block, apply=apply_floor, now=None) -> dict:
    """Run every fresh payload through the engine (``model_path``) and the floor (``apply``).

    ``spec`` is the block's spec, or a callable ``payload -> spec`` when each task carries its
    own candidates (librarian-ask's walked nodes). ``root`` is where the engine path's traces
    land; ``source_root``/``holder`` find the runs the floor was compiled from. Raises
    DoorRefused, every lack named, for stale payloads, unfound source runs, or a ``root``
    equal to the source root."""
    block = floor.get("block", "?")
    lacks = []
    if source_root is not None and Path(root).resolve() == Path(source_root).resolve():
        lacks.append({"field": "root",
                      "why": "the engine path would trace into the floor's own source root, so "
                             "this validation would become the next compile's training"})
    seen, missing = _source_inputs(floor, source_root=source_root, holder=holder)
    if missing:
        lacks.append({"field": "compiled_from.runs",
                      "why": f"{len(missing)} source run(s) not found in the traces "
                             f"({missing[:5]}): freshness cannot be shown"})
    stale = [p for p in fresh_payloads if _key(p) in seen]
    if stale:
        lacks.append({"field": "fresh_payloads",
                      "why": f"{len(stale)} payload(s) appear in the floor's source runs "
                             f"(e.g. {stale[0]!r}): fresh means fresh"})
    if not fresh_payloads:
        lacks.append({"field": "fresh_payloads", "why": "no fresh payload: nothing to validate"})
    if lacks:
        raise DoorRefused(block, lacks)

    rows = []
    cost = {"engine": {"inference_calls": 0, "wall_ms": 0.0},
            "floor": {"inference_calls": 0, "wall_ms": 0.0}}
    for payload in fresh_payloads:
        s = spec(payload) if callable(spec) else spec

        before = _calls(model_path)
        t0 = time.perf_counter()
        rec = model_path(s, payload, root=root, now=now)
        e_ms = (time.perf_counter() - t0) * 1000
        after = _calls(model_path)
        e_calls = after - before if before is not None and after is not None else None
        d = rec["data"]
        engine = ((d.get("winner") or {}).get("name"), (d.get("escalation") or {}).get("to"))

        cands = [{"name": c["name"], "provides": c.get("provides", {})} for c in s["candidates"]]
        before = _calls(apply)
        t0 = time.perf_counter()
        got = apply(floor, payload, cands)
        f_ms = (time.perf_counter() - t0) * 1000
        after = _calls(apply)
        # a counter on apply is read; a pure apply (no counter) made no model call: it has none
        f_calls = after - before if before is not None and after is not None else 0
        floor_out = (got.get("winner"), got.get("escalation"))

        rows.append({"input": payload, "verdict": _verdict(engine, floor_out),
                     "engine": {"winner": engine[0], "escalation": engine[1],
                                "inference_calls": e_calls, "wall_ms": e_ms},
                     "floor": {"winner": floor_out[0], "escalation": floor_out[1],
                               "inference_calls": f_calls, "wall_ms": f_ms}})
        for path, calls, ms in (("engine", e_calls, e_ms), ("floor", f_calls, f_ms)):
            c = cost[path]
            c["inference_calls"] = None if calls is None or c["inference_calls"] is None \
                else c["inference_calls"] + calls
            c["wall_ms"] += ms

    tally = {v: sum(1 for r in rows if r["verdict"] == v) for v in ("agree", "abstain", "disagree")}
    return {"block": block, "payloads": rows, **tally, "cost": cost,
            "not_agreeing": [r["input"] for r in rows if r["verdict"] != "agree"],
            "passed": tally["agree"] == len(rows)}
