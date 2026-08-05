"""PROBE — has the engine's training corpus grown enough to cast the compile step?

Berth for the WATCHME(engine-trace-corpus) that ticket ``engine-runs-one-block`` carries.
Berthed HERE, beside ``cairn/learning_block/``, because that component OWNS the trace
store this probe reads — the subject is the corpus the engine writes, and a probe berths
with what it watches, never with the ticket it was compiled from (``cairn/base/probe.py``).

THE EFFICACY QUESTION. The engine's claim is that a block's reasoning now lands in the
record instead of in anyone's attention. The parent ticket's staircase only moves when
that record ACCUMULATES: child 2 (infer-compile-reads-the-traces) casts at >= 5
training-typed engine runs for one block — a threshold the parent names as a HYPOTHESIS
(Law 3), which is exactly why a probe reports it instead of a session remembering to
count. Without this watch the track goes quiet at the precise moment it is supposed to
learn: traces pile up with no reader and nobody is poked to cast the reader.

TWO HALVES TO THE REPORT, not one. A count of 5 wire-thin records would satisfy a naive
counter and starve the compile step anyway — the pre-engine corpus was measured exactly
that shape (36 records, zero inner-loop fields, 2026-08-02). So the carrier reports the
count AND whether each record answers the five mechanical questions, composing the
engine's own checker rather than minting a second reading.

THE CORPUS IS THE LIVE STORE ONLY. The engine's proofs run against injected temp roots
(``world()``), so fixture runs never land where this probe counts — the home-field
advantage the librarian measured, kept out structurally rather than filtered here.

AUTHORITY: none, by construction. This probe deposits and pokes; casting child 2 is the
/sorted session's act, and any back-edge is the owner's (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.base.probe import Probe, owning_ticket
from cairn.learning_block.engine import RUN_EVENT, answers_five_questions, rejected_count

# Env-first, default second, resolved PER CALL — a probe that froze the path at import
# would keep reading a root the instance had already left (the precedent probe's rule).
_TRACE_ENV = "CAIRN_LB_TRACE_ROOT"
_TRACE_DEFAULT = Path.home() / ".cairn" / "devices" / "learning_block" / "0" / "traces"

# The casting threshold child 2 waits on — the parent ticket's number, a labeled
# hypothesis ('5-10 traces suffice to compile' is what child 2's cast TESTS first).
_ENOUGH = 5

_TICKET = owning_ticket("engine-runs-one-block")


def survey_the_corpus() -> dict:
    """Count engine runs per block over the LIVE trace store, and judge each record
    against the five mechanical questions. Unreadable lines are skipped, never counted
    as evidence in either direction (a claim resting on a parse failure is worse than a
    smaller n)."""
    root = Path(os.environ.get(_TRACE_ENV) or _TRACE_DEFAULT)
    blocks: dict[str, dict] = {}
    if root.is_dir():
        for path in sorted(root.glob("*.jsonl")):
            runs, complete, records = 0, 0, []
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("event") != RUN_EVENT or rec.get("consumer") != "training":
                    continue
                runs += 1
                records.append(rec)
                if not answers_five_questions(rec):
                    complete += 1
            if runs:
                blocks[path.stem] = {"runs": runs, "answer_all_five": complete,
                                     "rejected_candidates": rejected_count(records)}
    best = max(blocks.items(), key=lambda kv: kv[1]["runs"], default=(None, None))
    return {"blocks": blocks, "front_runner": best[0], "front_counts": best[1]}


def _trigger(now, context: dict) -> bool:
    """TRUE once any block's engine corpus exists at all — the watch reports growth from
    the first real run; an empty store is silence, not a zero worth poking about."""
    s = context.get("corpus") or survey_the_corpus()
    return bool(s["blocks"])


def _enough(context: dict) -> bool:
    """CLEARED when one block holds >= 5 training-typed engine runs that ALL answer the
    five questions — the parent's casting condition for child 2, with the wire-thin
    loophole closed: five records the compile step cannot read clear nothing."""
    s = context.get("corpus") or survey_the_corpus()
    return any(b["runs"] >= _ENOUGH and b["answer_all_five"] >= _ENOUGH
               for b in s["blocks"].values())


def _carry(context: dict) -> dict:
    """The verdict artifact's raw material, against THIS ticket's falsifier: per-block
    run counts, five-question answerability, and the non-vacuity denominator."""
    s = context.get("corpus") or survey_the_corpus()
    return {"ticket": _TICKET,
            "corpus": s,
            "against_falsifier": "the state log answers input / candidates / "
                                 "killer-constraint / winner-why / escalation "
                                 "mechanically, and >= 1 rejected candidate exists",
            "casts_when_enough": "infer-compile-reads-the-traces (parent's child 2) — "
                                 "the consumer is the /sorted session, not this probe"}


# Honest as a placeholder, dishonest as a measurement — same tracked debt as the sibling
# probes: nothing pulses this shim yet, so loudness rides BaseShim.overdue() alone.
# Re-tune when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="does the engine's training corpus actually accumulate — and accumulate RECORDS "
        "THE COMPILE STEP CAN READ? Five wire-thin lines would look like readiness and "
        "starve child 2 on cast day; this watch counts only what answers the five "
        "questions, and pokes when one block crosses the casting threshold.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "sorted", "kind": "casting-condition", "ticket": _TICKET},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
