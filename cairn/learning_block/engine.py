"""engine — the Learning Block's uniform inner loop: ONE shape, instantiated from data.

THE LIVED SYMPTOM THIS RETIRES (Akien, 2026-08-02): "as soon as we switch from fable to
opus, we start spiralling down. I CANNOT keep track of all those details." The same
morning he ran a design session on the smallest model successfully — by feeding it one
bounded question per turn and carrying the state himself. This module is that property
given to every block with the ARTIFACT as the carrier: the run's whole reasoning lands in
a training-typed trace, so neither a model's attention nor Akien's head has to hold it.

THE SHAPE (ticket engine-runs-one-block, parent learning-block-engine-track):

    input -> candidates loop -> evaluation loop -> decide or escalate -> output
                                                        |
                            every step of which lands in ONE state-log record

THE SPEC CARRIES THE DIFFERENCE — the engine is deliberately branchless about blocks.
A block spec is pure DATA (mechanically enforced: it must survive a JSON round-trip):

    {"block":          the trace corpus this block's runs land under,
     "question":       what one run answers,
     "input_contract": {field: why} — the DOOR organ's grammar, fired over the payload,
     "candidates":     [{name, why, provides: {property: value-or-list}}, ...]
                       in PREFERENCE ORDER (first = preferred among survivors),
     "constraints":    [{name, why, source, requires: {property: expected}}, ...]
                       where expected is a literal, a list (any-of), or {"fact": f}
                       resolved against the run's input at evaluation time,
     "escalation":     whose gate a run with no survivor stands at}

If expressing a block's difference ever requires code in here rather than fields in
there, the 'one engine, different data' hypothesis is FALSIFIED — stop and reconcile
(the parent ticket's wrong-intent tell); do not accrete cases.

THE FIVE MECHANICAL QUESTIONS every state-log record answers by field access alone
(the ticket's falsifier — a log that cannot answer these is not a state log):
  1. what was the input                       -> data["input"]
  2. what candidates were generated          -> data["candidates"][*]["name"]
  3. what constraint killed each loser       -> data["candidates"][*]["killed_by"]
  4. why did the winner win                  -> data["winner"]["why"]
  5. what escalated, and to where            -> data["escalation"] (explicitly null
                                                when nothing did — silence is not an
                                                answer, so the key is always present)

``answers_five_questions`` is the checker — the proofs, the PROVED verdict and the
corpus probe all compose it rather than each inventing a reading.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from cairn.learning_block.learning_block import (
    DoorRefused,
    check_input,
    declare_contract,
    write_trace,
)

RUN_EVENT = "engine_run"

# The spec's own door: field -> why (the DOOR organ's grammar — the engine declares its
# contract; the organ owns refusal).
SPEC_REQUIRES = {
    "block": "the run's trace must land under the block it reasons for — an unowned "
             "record teaches nobody's corpus",
    "question": "a run that cannot say what it is answering cannot be adjudicated (CP3)",
    "candidates": "the loop needs somewhere to stand — at least one candidate, each "
                  "carrying the properties the constraints judge",
    "constraints": "an evaluation loop with nothing to evaluate against decides by "
                   "accident, and an accident cannot be compiled",
    "escalation": "the run no candidate survives must know whose gate to stand at "
                  "(Law 6) — an unnamed escalation vanishes into conversation",
}


def _data_only_lack(spec) -> list[dict]:
    """A spec is DATA — enforced by round-trip, not by review."""
    try:
        json.dumps(spec)
        return []
    except (TypeError, ValueError) as exc:
        return [{"field": "<spec>", "why": "a block spec is pure data — it must survive "
                                           f"a JSON round-trip, and this one cannot ({exc}); "
                                           "domain knowledge enters as fields, never as code"}]


def _shape_lacks(spec: dict) -> list[dict]:
    """Deep shape, collected whole — every lack named in the one refusal (Law 7)."""
    lacks: list[dict] = []
    for i, cand in enumerate(spec.get("candidates") or []):
        if not isinstance(cand, dict) or not str(cand.get("name") or "").strip():
            lacks.append({"field": f"candidates[{i}].name",
                          "why": "an unnamed candidate cannot be rejected BY NAME, which "
                                 "is what the state log exists to record"})
        if not isinstance(cand, dict) or not isinstance(cand.get("provides"), dict):
            lacks.append({"field": f"candidates[{i}].provides",
                          "why": "a candidate with no declared properties gives the "
                                 "constraints nothing to judge — it wins or dies by vibe"})
    for i, con in enumerate(spec.get("constraints") or []):
        if not isinstance(con, dict) or not str(con.get("name") or "").strip():
            lacks.append({"field": f"constraints[{i}].name",
                          "why": "the killer each loser's record names — an unnamed "
                                 "constraint makes question 3 unanswerable"})
        if not isinstance(con, dict) or not isinstance(con.get("requires"), dict) \
                or not con.get("requires"):
            lacks.append({"field": f"constraints[{i}].requires",
                          "why": "a constraint that requires nothing kills nothing and "
                                 "is a name wearing a rule's seat"})
    return lacks


def _satisfies(candidate: dict, constraint: dict, facts: dict) -> bool:
    """Does this candidate survive this constraint, given the run's measured facts?

    Uniform predicate, no special cases: every required property must be provided,
    either equal to the expected value or (when the candidate provides a list) as
    one of its members. ``{"fact": f}`` resolves the expectation against the input —
    which is how a constraint judges against the world as measured, not as hoped.
    """
    provides = candidate.get("provides", {})
    for key, expected in constraint.get("requires", {}).items():
        if isinstance(expected, dict) and "fact" in expected:
            expected = facts.get(expected["fact"])
        got = provides.get(key)
        if got != expected and not (isinstance(got, list) and expected in got):
            return False
    return True


def run_block(spec: dict, payload: dict, *,
              root: Path | None = None, now: datetime | None = None) -> dict:
    """One run of one block: refuse-or-reason, and either way leave a record.

    Returns the trace record written (its ``data`` is the state log). Raises
    ``DoorRefused`` — with EVERY lack named, send-back traced — when the spec or the
    payload is insufficient. A green run and an escalating run trace with the same
    fidelity: the denominator must exist.
    """
    block = str(spec.get("block") or "?") if isinstance(spec, dict) else "?"

    # THE SPEC DOOR — shallow (the organ's check) + deep (shape) + purity, one refusal.
    spec_lacks = _data_only_lack(spec)
    if isinstance(spec, dict):
        contract = declare_contract(block if block != "?" else "engine",
                                    dict(SPEC_REQUIRES))
        spec_lacks += check_input(contract, spec)
        spec_lacks += _shape_lacks(spec)
    else:
        spec_lacks += [{"field": f, "why": w} for f, w in SPEC_REQUIRES.items()]
    if spec_lacks:
        write_trace(block, "send_back", "training",
                    {"at": "spec", "lacks": spec_lacks}, now=now, root=root)
        raise DoorRefused(block, spec_lacks)

    # THE INPUT DOOR — the spec's own declared contract over this run's payload.
    input_contract = spec.get("input_contract") or {}
    if input_contract:
        in_lacks = check_input(declare_contract(block, dict(input_contract)), payload)
        if in_lacks:
            write_trace(block, "send_back", "training",
                        {"at": "input", "lacks": in_lacks}, now=now, root=root)
            raise DoorRefused(block, in_lacks)

    # THE CANDIDATES LOOP + THE EVALUATION LOOP — every candidate judged against every
    # constraint; nothing is skipped, so every death has a recorded killer.
    evaluations: list[tuple[dict, list[str]]] = []
    for cand in spec["candidates"]:
        killed_by = [con["name"] for con in spec["constraints"]
                     if not _satisfies(cand, con, payload)]
        evaluations.append((cand, killed_by))

    survivors = [cand for cand, killed in evaluations if not killed]

    # DECIDE OR ESCALATE — preference is the spec's candidate order (the author ranked
    # them; the engine does not re-rank), escalation is the spec's named gate.
    winner = escalation = None
    if survivors:
        top = survivors[0]
        winner = {
            "name": top["name"],
            "why": ("cleared all %d constraint(s); highest-preference survivor "
                    "(the spec's candidate order ranks it%s). Domain why: %s"
                    % (len(spec["constraints"]),
                       "" if len(survivors) == 1
                       else f" above {len(survivors) - 1} other survivor(s)",
                       top.get("why", "(none declared)"))),
        }
    else:
        escalation = {
            "to": spec["escalation"],
            "why": "no candidate survived the constraints — " + "; ".join(
                f"{cand['name']} killed by {', '.join(killed)}"
                for cand, killed in evaluations),
        }

    candidates_log = []
    for cand, killed in evaluations:
        if killed:
            outcome = "rejected"
        elif winner is not None and cand["name"] == winner["name"]:
            outcome = "winner"
        else:
            outcome = "outranked"
        candidates_log.append({
            "name": cand["name"],
            "outcome": outcome,
            "killed_by": killed,
            "outranked_by": (winner["name"]
                             if outcome == "outranked" else None),
        })

    # THE STATE LOG — one record, five questions, written through the TRACE organ in the
    # same act as the reasoning (a run that decided but did not land is a run that
    # happened only in attention — the exact silence this module exists to end).
    data = {
        "question": spec["question"],
        "input": payload,
        "candidates": candidates_log,
        "winner": winner,
        "escalation": escalation,
    }
    return write_trace(block, RUN_EVENT, "training", data, now=now, root=root)


def answers_five_questions(record: dict) -> list[str]:
    """The falsifier, mechanical: which of the five questions can this record NOT answer
    by field access alone? Empty list = a state log. Composed by the proofs, the PROVED
    verdict and the corpus probe — one reading, not three."""
    missing: list[str] = []
    data = record.get("data") or {}
    if "input" not in data:
        missing.append("1: what was the input — data['input'] absent")
    cands = data.get("candidates")
    if not cands or any(not c.get("name") for c in cands):
        missing.append("2: what candidates were generated — absent or unnamed")
    else:
        for c in cands:
            if c.get("outcome") == "rejected" and not c.get("killed_by"):
                missing.append("3: what constraint killed %r — rejected with no "
                               "killed_by" % c.get("name"))
    winner = data.get("winner")
    escalation = data.get("escalation", "\0absent")
    if winner is not None and not (winner.get("why") or "").strip():
        missing.append("4: why did the winner win — winner carries no why")
    if escalation == "\0absent":
        missing.append("5: what escalated and to where — the key is absent (null is an "
                       "answer; silence is not)")
    elif escalation is not None and not (escalation.get("to") or "").strip():
        missing.append("5: what escalated and to where — escalation names no gate")
    if winner is None and (escalation in (None, "\0absent")):
        missing.append("4: why did the winner win — no winner AND nothing escalated: "
                       "the run decided nothing and does not say so")
    return missing


def rejected_count(records: list[dict]) -> int:
    """How many REJECTED candidates the corpus holds — the non-vacuity denominator
    (an engine that never rejects has no evaluation loop to log)."""
    return sum(1 for r in records
               if r.get("event") == RUN_EVENT
               for c in (r.get("data") or {}).get("candidates", [])
               if c.get("outcome") == "rejected")
