"""Proof for ticket 049249b867ec: a state write keeps every standing field it does not name.

Measured 2026-11-14: CairnCommons commit 4bf3b3cb shrank four tickets' ``.state.json``
(033f607c5316, 44347787f7d3, aa1459b4ccd4, a9709b744bf5) to {intent_berth, sorted_berth}. Their
cursors, questions, chart claims and watchmes were gone. The journal stack reads
berths_none.py -> ticket_file.rewrite_ticket -> write_ticket -> write_state. The script read the
PLAN alone, laid two berths on it and put it back; write_ticket split the two berths off as
the state, and write_state wrote them as the whole file.

  1. test_a_two_key_write_keeps_the_rest: write_state of two keys over a state that holds
     workflow_and_state, questions and both berths replaces the two keys and leaves the rest equal.
  2. test_the_4bf3_path_keeps_the_rest: berths_none.py's own body, read verbatim off akiendell
     on 2026-11-14 with only its store path pointed at a scratch commons, runs as a subprocess.
     After it runs, the state's other fields are equal and the two berths are the script's.
  3. test_a_named_drop_removes_only_that_key: a key named in ``drop=`` is gone and the rest stay.

Every write lands in a scratch commons (the artifact door's roots are bent in-process and, for
the subprocess, through CAIRN_ARTIFACT_ROOTS). The live store is never touched.

    python3 cairn/tools/base/proofs/test_a_partial_state_write_keeps_the_standing_fields.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"049249b867ec": {
    "1": "test_a_two_key_write_keeps_the_rest",
    "2": "test_the_4bf3_path_keeps_the_rest",
    "3": "test_a_named_drop_removes_only_that_key",
}}

TICKET = "fa1e70492000"
STANDING = {
    "date": "2026-11-14",
    "owner": "CC",
    "node_class": "code-seam",
    "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> [FIXME:waiting] -> BUILDME -> PROVEME -> PROVED",
    "watchme": "none, because the fixture stands for cairn/tools/base/ticket_file.py",
    "intent_berth": "/old/intent-berth.json",
    "sorted_berth": "/old/sorted-berth.json",
    "questions": ["open-fa1e70492001"],
    "chart_claim": {"chart": "fixture", "at": "2026-11-14T00:00:00+00:00"},
}
PLAN = {"id": TICKET, "title": "the proof's fixture ticket", "why": "fixture"}

# berths_none.py, verbatim but for two lines: its glob names the scratch store (STORE), not
# C:/automation/local/CairnCommons/tickets/, and its four ids are the fixture's one.
BERTHS_NONE = r'''
import json, glob, os
from cairn.tools.base.ticket_file import rewrite_ticket

for p in [TICKET]:
    f = [x for x in glob.glob(STORE + p + "-*.json")
         if not x.endswith((".state.json", ".log.jsonl"))][0]
    name = os.path.basename(f)
    d = json.load(open(f, encoding="utf-8"))
    ref = "CairnCommons/tickets/" + name
    d["intent_berth"] = ("none, because this ticket was cast without an /intent berth by the cast that wrote it; "
                         "its own plan is the record: " + ref)
    d["sorted_berth"] = ("none, because this ticket was cast without a /sorted door firing that recorded a berth; "
                         "its own plan is the record: " + ref)
    rewrite_ticket(f, d, why=("clearance refused the ticket for lacking rides_the_intent and rides_the_sorted "
                              "(trouble ticket-unqueued-" + p[:4] + "-at-clearance); the berths were never recorded, "
                              "so each is written as 'none, because <referent>' as the orchestrator directed (2026-11-14)"))
    print("ok", p)
'''


def _live_charter() -> Path:
    for c in (REPO.parent / "CairnCommons", Path.home() / "dev" / "src" / "CairnCommons"):
        f = c / "tickets" / "_charter+why.json"
        if f.is_file():
            return f
    raise FileNotFoundError("no live tickets/_charter+why.json beside the repo or under ~/dev/src")


def _world() -> tuple[Path, Path]:
    """A scratch commons holding one ticket, plan and state. Returns (roots dir, plan)."""
    from cairn.tools.scratch.scratch import scratch_dir
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_file import write_state
    tmp = scratch_dir("testing-049249b867ec-")
    commons, cairn = tmp / "CairnCommons", tmp / "cairn"
    (commons / "tickets").mkdir(parents=True)
    cairn.mkdir()
    shutil.copy(_live_charter(), commons / "tickets" / "_charter+why.json")
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    plan = commons / "tickets" / f"{TICKET}-the-proof-s-fixture-ticket.json"
    A.write(plan, json.dumps(PLAN, indent=2) + "\n", verb="cast", why="049249b867ec fixture")
    write_state(plan, dict(STANDING), why="049249b867ec fixture", verb="cast")
    return tmp, plan


def _state(plan: Path) -> dict:
    from cairn.tools.base.ticket_file import state_path
    return json.loads(state_path(plan).read_text(encoding="utf-8"))


def _rest(d: dict, *gone: str) -> dict:
    return {k: v for k, v in d.items() if k not in gone}


def test_a_two_key_write_keeps_the_rest():
    from cairn.tools.base.ticket_file import write_state
    _, plan = _world()
    write_state(plan, {"intent_berth": "none, because a", "sorted_berth": "none, because b"},
                why="049249b867ec tooth 1", verb="phase")
    got = _state(plan)
    assert _rest(got, "intent_berth", "sorted_berth") == _rest(STANDING, "intent_berth", "sorted_berth"), (
        f"a two-key write dropped standing fields: kept {sorted(got)}, stood {sorted(STANDING)}")
    assert (got["intent_berth"], got["sorted_berth"]) == ("none, because a", "none, because b"), got


def test_the_4bf3_path_keeps_the_rest():
    tmp, plan = _world()
    store = str(plan.parent).replace("\\", "/") + "/"
    code = f"TICKET = {TICKET!r}\nSTORE = {store!r}\n" + BERTHS_NONE
    env = dict(os.environ, PYTHONPATH=str(REPO),
               CAIRN_ARTIFACT_ROOTS=json.dumps({"CairnCommons": str(tmp / "CairnCommons"),
                                                "cairn": str(tmp / "cairn"),
                                                "parked": str(tmp / "parked")}))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       env=env, cwd=str(REPO), timeout=120)
    assert r.returncode == 0 and f"ok {TICKET}" in r.stdout, (r.stdout[-400:], r.stderr[-800:])
    got = _state(plan)
    assert _rest(got, "intent_berth", "sorted_berth") == _rest(STANDING, "intent_berth", "sorted_berth"), (
        f"berths_none.py's rewrite_ticket dropped standing fields: kept {sorted(got)}, stood {sorted(STANDING)}")
    assert got["intent_berth"].startswith("none, because") and got["sorted_berth"].startswith("none, because"), got


def test_a_named_drop_removes_only_that_key():
    from cairn.tools.base.ticket_file import write_state
    _, plan = _world()
    write_state(plan, {}, why="049249b867ec tooth 3", verb="phase", drop=("chart_claim",))
    got = _state(plan)
    assert "chart_claim" not in got, f"drop=('chart_claim',) left it standing: {got.get('chart_claim')!r}"
    assert got == _rest(STANDING, "chart_claim"), f"a named drop touched other fields: {sorted(got)}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
