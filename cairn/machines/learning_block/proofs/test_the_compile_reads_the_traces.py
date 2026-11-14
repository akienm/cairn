"""Proof for ticket e889b197a3f6 — the compile reads a block's engine traces into a floor.

One tooth per falsifier clause:

  1. over >=5 engine runs of one block with distinct inputs, compile_floor emits a floor, and
     apply_floor reproduces every traced run's outcome (winner name or escalation target) from
     that run's recorded input and candidates;
  2. two compiles over one corpus write byte-identical floors, and compile.py imports no
     inference client (its imports are a closed, named set);
  3. compile_floor refuses, naming every lack in one refusal, a corpus of fewer than 5
     distinct inputs and a corpus whose candidates carry no provides; a fixture shaped like
     the live librarian-ask corpus as measured 2026-11-13 is refused on both;
  4. run_block writes each candidate's provides into candidates_log, and the engine teeth in
     test_learning_block.py stay green.

Every trace and floor lives under a scratch root (the world() pattern of
test_learning_block.py); the live trace berth is never read or written.

    python cairn/machines/learning_block/proofs/test_the_compile_reads_the_traces.py
"""

from __future__ import annotations

import ast
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.machines.learning_block import compile as C  # noqa: E402
from cairn.machines.learning_block import engine as eng  # noqa: E402
from cairn.machines.learning_block import learning_block as lb  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

NOW = datetime(2026, 11, 13, 12, 0, 0, tzinfo=timezone.utc)
BLOCK = "testing-ask"
HOLDER = "testing_holder/0"

PROVES = {"e889b197a3f6": {"1": "test_the_floor_reproduces_every_traced_run", "2": "test_two_compiles_are_byte_identical_and_compile_imports_no_inference", "3": "test_a_thin_or_featureless_corpus_is_refused_with_every_lack", "4": "test_run_block_logs_provides_and_the_engine_teeth_stay_green"}}


def world() -> Path:
    return scratch_dir("lb-compile-testing-")


def _spec(cands: list[tuple]) -> dict:
    """A librarian-ask-shaped spec: one candidate per walked node, then the standing loser."""
    nodes = [{"name": f"{i}:{tag}", "why": "testing",
              "provides": {"not_refuted": nr, "clears_floor": cf, "source_kind": sk}}
             for i, (tag, nr, cf, sk) in enumerate(cands)]
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


# Seven tasks, every input distinct: three resolve, four escalate, and each constraint both
# kills and passes somewhere, so each rule is learned from both sides.
TASKS = [
    ("q1", [("a", True, True, "answered_question"), ("b", True, False, "llm-backfill")]),
    ("q2", [("a", True, False, "answered_question"), ("b", True, True, "answered_question")]),
    ("q3", [("a", False, True, "answered_question"), ("b", True, True, "llm-backfill")]),
    ("q4", [("a", True, True, "llm-backfill"), ("b", True, True, "llm-backfill")]),
    ("q5", [("a", True, True, "answered_question")]),
    ("q6", [("a", False, False, "llm-backfill")]),
    ("q7", [("a", True, True, "unknown"), ("b", True, False, "answered_question")]),
]


def _corpus(root: Path) -> list[dict]:
    return [eng.run_block(_spec(cands), {"question": q}, now=NOW, root=root)
            for q, cands in TASKS]


def _compile(root: Path) -> dict:
    return C.compile_floor(BLOCK, holder=HOLDER, root=root, floors_root=root / "floors")


def _refusal(fn) -> C.DoorRefused:
    try:
        fn()
    except C.DoorRefused as e:
        return e
    raise AssertionError("the compile wrote a floor it should have refused")


def test_the_floor_reproduces_every_traced_run():
    root = world()
    runs = _corpus(root)
    outcomes = {((r["data"]["winner"] or {}).get("name"),
                 (r["data"]["escalation"] or {}).get("to")) for r in runs}
    assert any(w for w, _ in outcomes) and any(e for _, e in outcomes), \
        f"the fixture must hold winners and escalations, or the tooth is vacuous: {outcomes}"
    floor = _compile(root)["floor"]
    assert set(floor["rules"]) == {"is_not_refuted", "clears_the_floor", "carries_his_answer"}, \
        floor["rules"]
    for r in runs:
        d = r["data"]
        got = C.apply_floor(floor, d["input"], d["candidates"])
        want = ((d["winner"] or {}).get("name"), (d["escalation"] or {}).get("to"))
        assert (got["winner"], got["escalation"]) == want, (d["input"], got, want)
    # an unseen source kind is killed, so a task the corpus never showed escalates
    fresh = C.apply_floor(floor, {"question": "q-unseen"},
                          [{"name": "0:x", "provides": {"not_refuted": True, "clears_floor": True,
                                                        "source_kind": "testing-never-seen"}}])
    assert fresh["winner"] is None and fresh["escalation"] == "operator", fresh


def test_two_compiles_are_byte_identical_and_compile_imports_no_inference():
    root = world()
    _corpus(root)
    first = Path(_compile(root)["path"]).read_bytes()
    second = Path(_compile(root)["path"]).read_bytes()
    assert first == second and first, "two compiles over one corpus must write the same bytes"
    tree = ast.parse((REPO / "cairn/machines/learning_block/compile.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    allowed = {"__future__", "json", "pathlib", "cairn.tools.base.address",
               "cairn.machines.learning_block.engine",
               "cairn.machines.learning_block.learning_block"}
    assert imported <= allowed, f"compile.py imports outside its closed set: {imported - allowed}"


def _live_shaped(root: Path) -> None:
    """The live librarian-ask corpus as measured 2026-11-13: 7 runs, 4 of one question with
    one winner, 3 backfill escalations, and candidates_log entries with no provides."""
    def run(q, winner, killed, backfills):
        cands = [{"name": f"{i}:n{i}", "outcome": "rejected" if i < killed else "winner",
                  "killed_by": ["carries_his_answer"] if i < killed else [],
                  "outranked_by": None} for i in range(6)]
        data = {"question": "which answer?", "input": {"question": q, "backfills": backfills},
                "candidates": cands,
                "winner": {"name": winner, "why": "t"} if winner else None,
                "escalation": None if winner else {"to": "operator", "why": "t"}}
        lb.write_trace(BLOCK, eng.RUN_EVENT, "training", data, now=NOW, root=root)
    for _ in range(4):
        run("Is CC allowed to seal concept-pieces on its own?", "5:n5", 5, 0)
    for q, k in (("backfill one", 6), ("backfill two", 6), ("backfill three", 6)):
        run(q, None, k, 3)


def test_a_thin_or_featureless_corpus_is_refused_with_every_lack():
    live = world()
    _live_shaped(live)
    fields = {l["field"] for l in _refusal(lambda: _compile(live)).lacks}
    assert {"corpus", "candidates[].provides"} <= fields, fields

    thin = world()
    for q, cands in TASKS[:3]:
        eng.run_block(_spec(cands), {"question": q}, now=NOW, root=thin)
        eng.run_block(_spec(cands), {"question": q}, now=NOW, root=thin)
    fields = {l["field"] for l in _refusal(lambda: _compile(thin)).lacks}
    assert fields == {"corpus"}, f"6 runs of 3 distinct inputs must red on the corpus alone: {fields}"

    bare = world()
    for r in _corpus(world()):
        data = dict(r["data"])
        data["candidates"] = [{k: v for k, v in c.items() if k != "provides"}
                              for c in data["candidates"]]
        lb.write_trace(BLOCK, eng.RUN_EVENT, "training", data, now=NOW, root=bare)
    fields = {l["field"] for l in _refusal(lambda: _compile(bare)).lacks}
    assert fields == {"candidates[].provides"}, fields

    for holder in (None, "", "testing-no-instance"):
        e = _refusal(lambda: C.compile_floor(BLOCK, holder=holder, root=live,
                                             floors_root=live / "floors"))
        assert [l["field"] for l in e.lacks] == ["holder"], e.lacks
    assert not (live / "floors").exists(), "a refused compile must write no floor"


def test_run_block_logs_provides_and_the_engine_teeth_stay_green():
    root = world()
    spec = _spec(TASKS[0][1])
    rec = eng.run_block(spec, {"question": "q1"}, now=NOW, root=root)
    logged = {c["name"]: c["provides"] for c in rec["data"]["candidates"]}
    declared = {c["name"]: c["provides"] for c in spec["candidates"]}
    assert logged == declared, (logged, declared)
    r = subprocess.run([sys.executable, str(REPO / "cairn/machines/learning_block/proofs/"
                                                  "test_learning_block.py")],
                       cwd=REPO, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]


TEETH = [test_the_floor_reproduces_every_traced_run,
         test_two_compiles_are_byte_identical_and_compile_imports_no_inference,
         test_a_thin_or_featureless_corpus_is_refused_with_every_lack,
         test_run_block_logs_provides_and_the_engine_teeth_stay_green]

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
