"""Proof for ticket fad76bb5d1f5 — the rehearsal writes its trail to the ticket log and counts
what the plan lacked.

A ticket is a plan and a log (Akien 2026-10-10, "Flat plan + .log.jsonl"): the plan is "the
'current what to do'", the log beside it holds "the questions and the answering of them". The
rehearsal machine was the last writer still parking trail on the plan — the ``rehearsal``
pointer, and retired decision lines kept in place. Here it moves both to the log, and every
record says which of its gaps a log entry already answers (``log_reaches``): words the reader
was never handed because they sit in the log, not the plan.

Every tooth runs over a SCRATCH commons handed to the artifact door (one fixture ticket,
testing-marked, removed at exit); the reader is a stub replaying recorded trees.

  1. A CLEAN PASS APPENDS A LOG LINE AND LEAVES THE PLAN. The plan's bytes are unchanged, no
     ``rehearsal`` key is written, one 'rehearsal' log line names the record, and standing()
     returns that record ok. A v1 plan still carrying its pointer and no log line stands on the
     pointer (until 29569fca68a3 splits every ticket).
  2. A RETIRED DECISION MOVES WHOLE TO THE LOG. retire([3]) leaves the plan without D3 and one
     'decision_retired' line carries it whole with its retired stamp; a live line citing a
     retired id is still refused, writing neither file; the next decide() does not reuse a
     retired n.
  3. LOG REACHES COUNT THE GAPS A LOG ENTRY ANSWERS. A gap whose step repeats a log entry's
     words is one reach naming that entry's index; a gap sharing nothing is none; a log of
     unrelated words yields zero.

    bin/cairn test cairn/machines/rehearsal/proofs/test_the_rehearsal_writes_to_the_log.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {"fad76bb5d1f5": {"1": "test_a_clean_pass_appends_a_log_line_and_leaves_the_plan",
                           "2": "test_a_retired_decision_moves_whole_to_the_log",
                           "3": "test_log_reaches_count_the_gaps_a_log_entry_answers"}}

TID = "fad7f00dfeed"
STEM = f"{TID}-testing-fad76bb5d1f5-rehearsal-writes-to-the-log"
TICKET = {
    "id": TID, "title": "testing-fad76bb5d1f5-rehearsal-writes-to-the-log",
    "intention": "testing: a fixture ticket for the fad76bb5d1f5 proof",
    "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED",
    "decisions": [{"n": 1, "text": "write the widget", "by": "cc"},
                  {"n": 2, "text": "prove the widget", "by": "cc"}],
    "questions": [],
}
FLUX = "unlisted: calibrate the flux capacitor gauge"
SHED = "unlisted: paint the shed blue"


def _node(step, state="builds_as_written", assumption="", would_settle=""):
    return {"step": step, "state": state, "assumption": assumption,
            "would_settle": would_settle, "confidence": 0.9}


CLEAN_TREE = {"nodes": [_node("D1"), _node("D2")]}
TWO_UNLISTED = {"nodes": [_node("D1"), _node(FLUX), _node(SHED), _node("D2")]}


class Stub:
    def __init__(self, tree):
        self.tree = tree

    def __call__(self, text, schema_doc):
        return json.loads(json.dumps(self.tree)), {"model": "stub", "cost_usd": 0.0, "duration_ms": 1}


def _fixture_charter(tickets: Path) -> None:
    """A store charter in the scratch tickets dir: ticket_log reads the declared log kinds beside
    the plan, and a worktree (the hollow reading's) has no live commons beside it to fall back on."""
    (tickets / "_charter+why.json").write_text(json.dumps({
        "plan_fields": ["id", "title", "intention", "workflow_and_state", "decisions", "questions"],
        "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}}) + "\n")


class World:
    def __init__(self, ticket=None):
        from cairn.tools.artifact import artifact as door
        from cairn.tools.scratch.scratch import scratch_dir
        self.door = door
        self.dir = Path(scratch_dir("testing-fad76bb5d1f5-log-"))
        self.commons = self.dir / "CairnCommons"
        self.cairn = self.dir / "cairn"
        for d in ("tickets", "rehearsals", "questions"):
            (self.commons / d).mkdir(parents=True)
        self.cairn.mkdir()
        _fixture_charter(self.commons / "tickets")
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.ticket.write_text(json.dumps(ticket or TICKET, indent=2) + "\n", encoding="utf-8")
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def kw(self):
        return dict(root=self.commons, berths_root=self.dir / "no-berths", repo=self.dir / "no-repo")

    def doc(self):
        return json.loads(self.ticket.read_text(encoding="utf-8"))

    def log(self, kind=None):
        from cairn.tools.base.ticket_log import read_log
        return read_log(self.ticket, kind)


def _R():
    from cairn.machines.rehearsal import rehearsal as R   # at call time: hollow reverts this file
    return R


def test_a_clean_pass_appends_a_log_line_and_leaves_the_plan():
    R = _R()
    with World() as w:
        before = w.ticket.read_bytes()
        rec = R.rehearse(TID, reader=Stub(CLEAN_TREE), **w.kw())
        assert rec["clean"], rec["gaps"]
        assert w.ticket.read_bytes() == before, "a clean pass rewrote the plan"
        assert "rehearsal" not in w.doc(), "the pointer was written onto the plan"
        lines = w.log("rehearsal")
        assert len(lines) == 1 and lines[0]["record"] == rec["record"], lines
        st = R.standing(TID, w.commons)
        assert st["ok"] and st["record"] == rec["record"], st
        assert rec["ticket_sha256"] == R._sha(before), "the record hashes the plan the lane will see"
    # a v1 plan (not yet split by 29569fca68a3) stands on the pointer it carries
    with World() as w:
        rec = R.rehearse(TID, reader=Stub(CLEAN_TREE), **w.kw())
        log = w.ticket.with_name(w.ticket.name[:-5] + ".log.jsonl")
        log.unlink()
        doc = w.doc()
        doc["rehearsal"] = rec["record"]
        w.ticket.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        st = R.standing(TID, w.commons)
        assert st["ok"] and st["record"] == rec["record"], st


def _refuses(fn, needle):
    R = _R()
    try:
        fn()
    except R.Refused as exc:
        assert needle in str(exc), f"the refusal does not name {needle!r}: {exc}"
        return
    raise AssertionError("did not refuse")


def test_a_retired_decision_moves_whole_to_the_log():
    R = _R()
    t = dict(TICKET, decisions=[{"n": 1, "text": "write the widget", "by": "cc"},
                                {"n": 3, "text": "seal it plainly", "by": "cc"},
                                {"n": 4, "text": "seal it under the ruling", "by": "cc"},
                                {"n": 5, "text": "push both repos", "by": "cc"}])
    with World(t) as w:
        R.retire(TID, [3], by="cc", because="folded into D4", into=4, root=w.commons)
        ns = [d["n"] for d in w.doc()["decisions"]]
        assert ns == [1, 4, 5], f"the plan still carries a retired line: {ns}"
        lines = w.log("decision_retired")
        assert len(lines) == 1, lines
        d = lines[0]["decision"]
        assert d["n"] == 3 and d["text"] == "seal it plainly" and d["by"] == "cc", d
        r = d.get("retired") or {}
        assert r.get("by") == "cc" and r.get("at") and r.get("because") == "folded into D4" \
            and r.get("into") == 4, f"the retired stamp did not travel whole: {r}"
        # the next decision never reuses a retired n — the log still owns D3's name
        e = R.decide(TID, "unlisted: lint", "lint the widget", by="cc", root=w.commons)
        assert e["n"] == 6, f"decide reused or skipped a number: D{e['n']}"
    t2 = dict(TICKET, decisions=[{"n": 3, "text": "seal it plainly", "by": "cc"},
                                 {"n": 4, "text": "seal the tester proof per D3", "by": "cc"}])
    with World(t2) as w:
        plan = w.ticket.read_bytes()
        _refuses(lambda: R.retire(TID, [3], by="cc", because="superseded", root=w.commons), "D4")
        assert w.ticket.read_bytes() == plan and w.log() == [], "a refused retire wrote something"


def _log_field(w, value):
    from cairn.tools.base.ticket_log import append_log
    append_log(w.ticket, "field", {"field": "notes", "value": value}, actor="the proof",
               why="testing: a fixture log entry")


def test_log_reaches_count_the_gaps_a_log_entry_answers():
    R = _R()
    with World() as w:
        _log_field(w, "the rack hums quietly at night")
        _log_field(w, "calibrate the flux capacitor gauge against the bench reference")
        rec = R.rehearse(TID, reader=Stub(TWO_UNLISTED), **w.kw())
        steps = sorted(g["step"] for g in rec["gaps"])
        assert steps == sorted([FLUX, SHED]), steps
        assert rec["log_reach_count"] == 1, rec.get("log_reaches")
        (reach,) = rec["log_reaches"]
        assert reach["gap_step"] == FLUX and reach["log_index"] == 1 and reach["kind"] == "field" \
            and reach["overlap"] >= 4, reach
        on_disk = json.loads((w.commons / rec["record"]).read_text(encoding="utf-8"))
        assert on_disk["log_reach_count"] == 1, "the record on disk does not carry the count"
    with World() as w:
        _log_field(w, "the rack hums quietly at night")
        rec = R.rehearse(TID, reader=Stub(TWO_UNLISTED), **w.kw())
        assert len(rec["gaps"]) == 2 and rec["log_reach_count"] == 0 and rec["log_reaches"] == [], \
            rec.get("log_reaches")


TEETH = [test_a_clean_pass_appends_a_log_line_and_leaves_the_plan,
         test_a_retired_decision_moves_whole_to_the_log,
         test_log_reaches_count_the_gaps_a_log_entry_answers]


def main() -> int:
    failed = []
    for tooth in TEETH:
        try:
            tooth()
        except Exception as e:                       # noqa: BLE001 — the reason is the record
            failed.append(tooth.__name__)
            print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {str(e)[:300]}")
            continue
        print(f"  PASS  {tooth.__name__}")
    if failed:
        print(f"red — {len(failed)} of {len(TEETH)} teeth")
        return 1
    print(f"green — {len(TEETH)} teeth: the rehearsal's pointer and retired lines live on the log, "
          "and every record counts the gaps a log entry already answers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
