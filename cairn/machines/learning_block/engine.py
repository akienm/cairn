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

from cairn.tools.gate import gate
from cairn.machines.learning_block.learning_block import (
    DoorRefused,
    inspect_input,
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


def _proved(identity: str, *, expected, actual, location: str,
            lacks: list[dict], **values) -> dict:
    """One entry of the engine's proof record, in the seed's shape."""
    return gate.proved(identity=identity, expected=expected, actual=actual,
                       location=location, code="engine.py:%s" % identity,
                       source="engine.inspect_spec", lacks=list(lacks), **values)


def _data_only_lack(spec) -> list[dict]:
    """A spec is DATA — enforced by round-trip, not by review."""
    try:
        json.dumps(spec)
        return []
    except (TypeError, ValueError) as exc:
        return [{"field": "<spec>", "why": "a block spec is pure data — it must survive "
                                           f"a JSON round-trip, and this one cannot ({exc}); "
                                           "domain knowledge enters as fields, never as code"}]


def inspect_spec(spec) -> list[dict]:
    """THE PROOF RECORD THE SPEC DOOR OPENS ON: one entry per check that RAN, EXPECTED
    beside ACTUAL, passes included (Akien, 2026-08-13: "EVERYTHING ALWAYS PROVED AND
    LISTING WHAT IT PROVED ... SAME PATTERN EVERYWHERE").

    What it retires: the door accumulated lacks from three places and refused on their
    sum, so an empty sum was the same bytes whether the spec passed every check or the
    spec was not a dict and only the fallback ran. The record now says which of the three
    lanes ran, and the two DEEP lanes are GUARDED — a spec that is not a dict has no
    candidates to walk, so those entries are ABSENT rather than passed, and the shallow
    lane above has already closed the gate.

    The per-collection lanes carry their POPULATION in expected/actual: every candidate
    is expected to be named-and-provisioned and the actual is the ones that are, so a
    candidates list that shrinks to nothing shows up as an expected of zero rather than
    as an unchanged green.
    """
    record: list[dict] = []
    purity = _data_only_lack(spec)
    record.append(_proved(
        "the_spec_survives_a_json_round_trip",
        expected="pure data", actual="not JSON-serialisable" if purity else "pure data",
        location="<spec>", lacks=purity))

    if not isinstance(spec, dict):
        # GUARDED, and this is the case that used to hide: everything below walks a
        # mapping. One fault (the spec is not a spec), one entry, and the deep lanes are
        # visibly ABSENT rather than silently green.
        record.append(_proved(
            "the_spec_is_a_mapping",
            expected="a mapping", actual=type(spec).__name__,
            location="<spec>",
            lacks=[{"field": f, "why": w} for f, w in SPEC_REQUIRES.items()]))
        return record
    record.append(_proved(
        "the_spec_is_a_mapping",
        expected="a mapping", actual="a mapping", location="<spec>", lacks=[]))

    block = str(spec.get("block") or "?")
    contract = declare_contract(block if block != "?" else "engine", dict(SPEC_REQUIRES))
    record.extend(inspect_input(contract, spec))

    cands = spec.get("candidates") or []
    named = [i for i, c in enumerate(cands)
             if isinstance(c, dict) and str(c.get("name") or "").strip()]
    record.append(_proved(
        "every_candidate_is_named",
        expected=list(range(len(cands))), actual=named,
        location="candidates[].name",
        lacks=[{"field": "candidates[%d].name" % i,
                "why": "an unnamed candidate cannot be rejected BY NAME, which is what "
                       "the state log exists to record"}
               for i in range(len(cands)) if i not in named]))
    provisioned = [i for i, c in enumerate(cands)
                   if isinstance(c, dict) and isinstance(c.get("provides"), dict)]
    record.append(_proved(
        "every_candidate_declares_what_it_provides",
        expected=list(range(len(cands))), actual=provisioned,
        location="candidates[].provides",
        lacks=[{"field": "candidates[%d].provides" % i,
                "why": "a candidate with no declared properties gives the constraints "
                       "nothing to judge — it wins or dies by vibe"}
               for i in range(len(cands)) if i not in provisioned]))

    cons = spec.get("constraints") or []
    con_named = [i for i, c in enumerate(cons)
                 if isinstance(c, dict) and str(c.get("name") or "").strip()]
    record.append(_proved(
        "every_constraint_is_named",
        expected=list(range(len(cons))), actual=con_named,
        location="constraints[].name",
        lacks=[{"field": "constraints[%d].name" % i,
                "why": "the killer each loser's record names — an unnamed constraint "
                       "makes question 3 unanswerable"}
               for i in range(len(cons)) if i not in con_named]))
    con_binding = [i for i, c in enumerate(cons)
                   if isinstance(c, dict) and isinstance(c.get("requires"), dict)
                   and c.get("requires")]
    record.append(_proved(
        "every_constraint_requires_something",
        expected=list(range(len(cons))), actual=con_binding,
        location="constraints[].requires",
        lacks=[{"field": "constraints[%d].requires" % i,
                "why": "a constraint that requires nothing kills nothing and is a name "
                       "wearing a rule's seat"}
               for i in range(len(cons)) if i not in con_binding]))
    return record


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
    spec_record = inspect_spec(spec)
    spec_lacks = [l for e in spec_record if not gate.passed(e)
                  for l in e["values"]["lacks"]]
    if spec_lacks:
        write_trace(block, "send_back", "training",
                    {"at": "spec", "lacks": spec_lacks, "record": spec_record,
                     "checks_proved": len(spec_record)}, now=now, root=root)
        raise DoorRefused(block, spec_lacks)

    # THE INPUT DOOR — the spec's own declared contract over this run's payload.
    input_contract = spec.get("input_contract") or {}
    # GUARDED, and the guard is the honest part: a spec that declares no input contract
    # has no input checks to run, so the record stays EMPTY rather than collecting a
    # green nobody proved (Akien, 2026-08-13: a check that did not run is absent).
    input_record = (inspect_input(declare_contract(block, dict(input_contract)), payload)
                    if input_contract else [])
    in_lacks = [l for e in input_record if not gate.passed(e)
                for l in e["values"]["lacks"]]
    if in_lacks:
        write_trace(block, "send_back", "training",
                    {"at": "input", "lacks": in_lacks, "record": input_record,
                     "checks_proved": len(input_record)}, now=now, root=root)
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
        # THE DOORS RIDE THE GREEN RUN TOO, and this is the half that was missing: a run
        # that landed used to say nothing about what it had been checked against, so a
        # door that stopped running left the state log byte-identical. Now the log gets
        # SHORTER when a lane goes quiet (Akien, 2026-08-13: "EVERYTHING ALWAYS PROVED
        # AND LISTING WHAT IT PROVED ... SAME PATTERN EVERYWHERE").
        "doors": {"spec": spec_record, "input": input_record},
        "checks_proved": len(spec_record) + len(input_record),
    }
    return write_trace(block, RUN_EVENT, "training", data, now=now, root=root)


def inspect_state_log(record: dict) -> list[dict]:
    """THE PROOF RECORD OVER A LANDED RUN: one entry per question the five-question
    contract asks, EXPECTED beside ACTUAL, passes included.

    What it retires: ``answers_five_questions`` returned an empty list both when a record
    answered all five and when the caller handed it something that was not a record at
    all, and the proofs, the PROVED verdict and the corpus probe all read that same
    silence. Question 3 is GUARDED on question 2 — a record with no candidates has no
    rejection to explain, so its entry is ABSENT rather than passed, and question 2's
    entry above it has already closed the gate.
    """
    def entry(identity, *, expected, actual, location, missing):
        return gate.proved(identity=identity, expected=expected, actual=actual,
                           location=location, code="engine.py:%s" % identity,
                           source="engine.inspect_state_log", missing=list(missing))

    data = record.get("data") or {}
    out: list[dict] = []
    has_input = "input" in data
    out.append(entry(
        "q1_the_record_names_its_input",
        expected="data['input'] present", location="data.input",
        actual="data['input'] present" if has_input else "absent",
        missing=[] if has_input else ["1: what was the input — data['input'] absent"]))

    cands = data.get("candidates")
    named = bool(cands) and all(c.get("name") for c in cands)
    out.append(entry(
        "q2_every_candidate_generated_is_named",
        expected="a non-empty candidates list, every entry named",
        actual=("%d named candidate(s)" % len(cands)) if named
               else ("absent" if not cands else "%d candidate(s), some unnamed" % len(cands)),
        location="data.candidates",
        missing=[] if named else ["2: what candidates were generated — absent or unnamed"]))

    if named:
        rejected = [c for c in cands if c.get("outcome") == "rejected"]
        explained = [c for c in rejected if c.get("killed_by")]
        out.append(entry(
            "q3_every_rejection_names_its_killer",
            expected=[c.get("name") for c in rejected],
            actual=[c.get("name") for c in explained],
            location="data.candidates[].killed_by",
            missing=["3: what constraint killed %r — rejected with no killed_by"
                     % c.get("name") for c in rejected if not c.get("killed_by")]))

    winner = data.get("winner")
    winner_why = winner is None or bool((winner.get("why") or "").strip())
    out.append(entry(
        "q4_the_winner_carries_its_why",
        expected="a why, or no winner at all",
        actual="no winner" if winner is None
               else ("a why" if winner_why else "a winner with no why"),
        location="data.winner.why",
        missing=[] if winner_why
                else ["4: why did the winner win — winner carries no why"]))

    escalation = data.get("escalation", "\0absent")
    named_gate = (escalation != "\0absent"
                  and (escalation is None or bool((escalation.get("to") or "").strip())))
    out.append(entry(
        "q5_escalation_is_stated_even_when_null",
        expected="the key present — null is an answer, silence is not",
        actual=("the key is absent" if escalation == "\0absent"
                else "null" if escalation is None
                else ("escalates to %r" % escalation.get("to") if named_gate
                      else "present but names no gate")),
        location="data.escalation",
        missing=[] if named_gate else
                ["5: what escalated and to where — the key is absent (null is an "
                 "answer; silence is not)"] if escalation == "\0absent" else
                ["5: what escalated and to where — escalation names no gate"]))

    decided = not (winner is None and escalation in (None, "\0absent"))
    out.append(entry(
        "the_run_decided_something_or_says_it_did_not",
        expected="a winner or an escalation",
        actual="a winner" if winner is not None
               else ("an escalation" if decided else "neither"),
        location="data.winner+data.escalation",
        missing=[] if decided else
                ["4: why did the winner win — no winner AND nothing escalated: "
                 "the run decided nothing and does not say so"]))
    return out


def answers_five_questions(record: dict) -> list[str]:
    """The falsifier, mechanical: which of the five questions can this record NOT answer
    by field access alone? Empty list = a state log. Composed by the proofs, the PROVED
    verdict and the corpus probe — one reading, not three.

    A VIEW OVER ``inspect_state_log``, DERIVED AND NEVER PARALLEL: the mismatches, in
    the order the record ran them. Two mouths for one question is how a gate and the
    sentence it prints come to disagree.
    """
    return [m for e in inspect_state_log(record) if not gate.passed(e)
            for m in e["values"]["missing"]]


def rejected_count(records: list[dict]) -> int:
    """How many REJECTED candidates the corpus holds — the non-vacuity denominator
    (an engine that never rejects has no evaluation loop to log)."""
    return sum(1 for r in records
               if r.get("event") == RUN_EVENT
               for c in (r.get("data") or {}).get("candidates", [])
               if c.get("outcome") == "rejected")
