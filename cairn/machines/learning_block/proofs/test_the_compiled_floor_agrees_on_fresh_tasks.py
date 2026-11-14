"""Proof for ticket 6b4209e39982 — the compiled floor agrees with the engine on fresh tasks at
lower cost.

One tooth per falsifier clause:

  1. validate_floor over fresh payloads (none in the compiled corpus) reports, for each, the
     floor's outcome beside the engine path's; on the fixture block the compiled floor agrees
     on every fresh payload. A stale payload is refused;
  2. a memorizing floor, a lookup of the corpus's traced inputs only, fails validate_floor on
     the same fresh payloads, and the report names each abstention;
  3. the report measures each path's cost: the floor makes 0 inference calls and takes fewer
     wall ms than the stubbed model path, which counts one inference call per backfill.

Every trace and floor lives under a scratch root (the world() pattern of
test_learning_block.py). The fixture is a librarian-ask-shaped block: one candidate per walked
node plus the standing loser, judged on not_refuted, clears_floor and source_kind.

    python cairn/machines/learning_block/proofs/test_the_compiled_floor_agrees_on_fresh_tasks.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.machines.learning_block import compile as C  # noqa: E402
from cairn.machines.learning_block import engine as eng  # noqa: E402
from cairn.machines.learning_block import validate as V  # noqa: E402
from cairn.machines.learning_block.learning_block import DoorRefused, read_trace  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

NOW = datetime(2026, 11, 13, 12, 0, 0, tzinfo=timezone.utc)
BLOCK = "testing-ask"
HOLDER = "testing_holder/0"

PROVES = {"6b4209e39982": {"1": "test_the_compiled_floor_agrees_on_every_fresh_payload", "2": "test_a_memorizing_floor_fails_on_the_same_fresh_payloads", "3": "test_the_floor_costs_less_than_the_stubbed_model_path"}}


def world() -> Path:
    return scratch_dir("lb-validate-testing-")


# each task's walked nodes: (tag, not_refuted, clears_floor, source_kind)
TRAINING = {
    "q1": [("a", True, True, "answered_question"), ("b", True, False, "llm-backfill")],
    "q2": [("a", True, False, "answered_question"), ("b", True, True, "answered_question")],
    "q3": [("a", False, True, "answered_question"), ("b", True, True, "llm-backfill")],
    "q4": [("a", True, True, "llm-backfill"), ("b", True, True, "llm-backfill")],
    "q5": [("a", True, True, "answered_question")],
    "q6": [("a", False, False, "llm-backfill")],
    "q7": [("a", True, True, "unknown"), ("b", True, False, "answered_question")],
}
# fresh tasks: questions the corpus never saw, built from feature values it did see, so a
# floor that LEARNED the rules can answer them and one that memorised the inputs cannot
FRESH = {
    "f1": [("a", False, True, "answered_question"), ("b", True, True, "answered_question")],
    "f2": [("a", True, True, "llm-backfill"), ("b", True, False, "answered_question"),
           ("c", True, True, "answered_question")],
    "f3": [("a", True, True, "unknown"), ("b", False, False, "llm-backfill")],
    "f4": [("a", True, True, "answered_question"), ("b", True, True, "answered_question")],
    "f5": [("a", True, False, "llm-backfill")],
}
TASKS = {**TRAINING, **FRESH}


def _payload(q: str) -> dict:
    # backfills: how many walked nodes the model path would have had to write, i.e. the ones
    # that do not carry his answer: the stub's inference-call count
    return {"question": q, "backfills": sum(1 for *_, sk in TASKS[q] if sk != "answered_question")}


def _spec(payload: dict) -> dict:
    nodes = [{"name": f"{i}:{tag}", "why": "testing",
              "provides": {"not_refuted": nr, "clears_floor": cf, "source_kind": sk}}
             for i, (tag, nr, cf, sk) in enumerate(TASKS[payload["question"]])]
    standing = {"name": "nothing_on_record", "why": "testing standing loser",
                "provides": {"not_refuted": False, "clears_floor": False, "source_kind": "none"}}
    return {"block": BLOCK, "question": "which answer settles this question?",
            "input_contract": {"question": "testing"},
            "candidates": nodes + [standing],
            "constraints": [
                {"name": "is_not_refuted", "why": "t", "source": "t",
                 "requires": {"not_refuted": True}},
                {"name": "clears_the_floor", "why": "t", "source": "t",
                 "requires": {"clears_floor": True}},
                {"name": "carries_his_answer", "why": "t", "source": "t",
                 "requires": {"source_kind": "answered_question"}}],
            "escalation": "operator"}


class StubModelPath:
    """The engine path with its model stubbed: one inference call counted per backfill."""

    def __init__(self):
        self.inference_calls = 0

    def __call__(self, spec, payload, **kw):
        self.inference_calls += int(payload.get("backfills") or 0)
        return eng.run_block(spec, payload, **kw)


def _compiled() -> tuple[dict, Path]:
    src = world()
    for q in TRAINING:
        eng.run_block(_spec(_payload(q)), _payload(q), now=NOW, root=src)
    floor = C.compile_floor(BLOCK, holder=HOLDER, root=src, floors_root=src / "floors")["floor"]
    return floor, src


def _memorizing(src: Path):
    """The hollow build: a lookup of the corpus's traced inputs and their outcomes only."""
    table = {}
    for r in read_trace(BLOCK, root=src):
        d = r["data"]
        table[json.dumps(d["input"], sort_keys=True)] = (
            (d["winner"] or {}).get("name"), (d["escalation"] or {}).get("to"))

    def apply(floor, payload, candidates):
        w, e = table.get(json.dumps(payload, sort_keys=True), (None, floor["escalation"]))
        return {"winner": w, "escalation": e}
    return apply


def _validate(floor, src, **kw):
    return V.validate_floor(floor, _spec, [_payload(q) for q in FRESH], root=world(),
                            source_root=src, model_path=kw.pop("model_path", StubModelPath()),
                            now=NOW, **kw)


def test_the_compiled_floor_agrees_on_every_fresh_payload():
    floor, src = _compiled()
    report = _validate(floor, src)
    assert len(report["payloads"]) == len(FRESH), report
    for row in report["payloads"]:
        assert {"winner", "escalation"} <= set(row["engine"]) and \
            {"winner", "escalation"} <= set(row["floor"]), row
    outcomes = {(r["engine"]["winner"], r["engine"]["escalation"]) for r in report["payloads"]}
    assert any(w for w, _ in outcomes) and any(e for _, e in outcomes), \
        f"the fresh set must hold winners and escalations, or the tooth is vacuous: {outcomes}"
    assert report["passed"] and report["agree"] == len(FRESH), report["payloads"]
    # fresh means fresh: a payload from the corpus is refused, by name
    try:
        V.validate_floor(floor, _spec, [_payload("q1"), _payload("f1")], root=world(),
                         source_root=src, now=NOW)
    except DoorRefused as e:
        assert [l["field"] for l in e.lacks] == ["fresh_payloads"], e.lacks
    else:
        raise AssertionError("a payload from the compiled corpus was validated as fresh")


def test_a_memorizing_floor_fails_on_the_same_fresh_payloads():
    floor, src = _compiled()
    memo = _memorizing(src)
    # the memoriser is no strawman: it reproduces the corpus it was built from exactly
    for q in TRAINING:
        rec = eng.run_block(_spec(_payload(q)), _payload(q), now=NOW, root=world())
        d = rec["data"]
        got = memo(floor, _payload(q), [])
        assert (got["winner"], got["escalation"]) == (
            (d["winner"] or {}).get("name"), (d["escalation"] or {}).get("to")), q
    report = _validate(floor, src, apply=memo)
    assert not report["passed"], report
    named = report["not_agreeing"]
    assert named and all(p in [_payload(q) for q in FRESH] for p in named), named
    assert report["abstain"] + report["disagree"] == len(named), report
    assert report["abstain"] >= 1, report


def test_the_floor_costs_less_than_the_stubbed_model_path():
    floor, src = _compiled()
    stub = StubModelPath()
    report = _validate(floor, src, model_path=stub)
    want = sum(_payload(q)["backfills"] for q in FRESH)
    assert want > 0, "the fresh set must carry backfills, or the cost tooth is vacuous"
    cost = report["cost"]
    assert cost["engine"]["inference_calls"] == want == stub.inference_calls, cost
    assert cost["floor"]["inference_calls"] == 0, cost
    assert cost["floor"]["wall_ms"] < cost["engine"]["wall_ms"], cost
    for row in report["payloads"]:
        assert row["floor"]["inference_calls"] == 0 and row["engine"]["inference_calls"] == \
            row["input"]["backfills"], row
    # a model path with no counter is reported unmeasured, never as a free 0
    bare = _validate(floor, src, model_path=lambda s, p, **kw: eng.run_block(s, p, **kw))
    assert bare["cost"]["engine"]["inference_calls"] is None, bare["cost"]


TEETH = [test_the_compiled_floor_agrees_on_every_fresh_payload,
         test_a_memorizing_floor_fails_on_the_same_fresh_payloads,
         test_the_floor_costs_less_than_the_stubbed_model_path]

if __name__ == "__main__":
    failed = 0
    for tooth in TEETH:
        try:
            tooth()
            print(f"  green  {tooth.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            failed += 1
            print(f"  RED    {tooth.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    sys.exit(1 if failed else 0)
