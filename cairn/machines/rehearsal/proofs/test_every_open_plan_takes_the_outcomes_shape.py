"""Proof for ticket aa3e9a70db47: every not-PROVED ticket's plan migrates to outcomes, its
trail and by-lines moved whole to its log.

Measured 2026-11-14: 79 of 276 open tickets failed transitions._shape_lacks, and 62 carried 165
trail-like decision lines. Akien, on d421051bc1f7: "a ticket shouldn't look like that ... all
tickets were supposed to migrate to that format." Q#100 (outline 9.3.5.1.2.1) draws the format:
a plan is constraints, outcomes, resources. This is the mechanical step, and it judges nothing.

  1. after the run no open ticket carries ``decisions``, and none whose falsifier had numbered
     clauses carries ``falsifier``. Clause n is outcome n; the i-th remaining decision is
     outcome k+i with its label dropped, its paths, after [] and no claim;
  2. no outcome's text opens with a trail marker, and no outcome carries ``by``;
  3. every moved trail line and every dropped ``by`` stands verbatim in the ticket's log;
  4. a PROVED ticket's plan, state and log are byte-identical before and after;
  5. a second run moves nothing and writes nothing;
  6. retire accepts a line whose ``by`` differs from the retirer's;
  7. the migration invents nothing: no decision-made outcome has a claim, no after or via, no
     constraints or resources, and bounds and measured are unchanged;
  8. the report names awaiting outcomes, too_big past 7, and a prose falsifier, and names
     nothing for a coherent ticket;
  9. rehearsal's readers (render's labeled steps, decide, scope) read a migrated ticket as they
     read the same ticket before migration: same n, same text, same paths.

The world: a scratch commons holding the live store charter and fixture tickets, each
testing-marked. Nothing reads the live corpus or calls a reader.

    python3 cairn/machines/rehearsal/proofs/test_every_open_plan_takes_the_outcomes_shape.py
"""
from __future__ import annotations

import json
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"aa3e9a70db47": {
    "1": "test_clauses_then_decisions_become_outcomes",
    "2": "test_no_outcome_opens_with_trail_or_carries_by",
    "3": "test_every_moved_line_stands_in_the_log",
    "4": "test_a_proved_ticket_is_byte_identical",
    "5": "test_a_second_run_writes_nothing",
    "6": "test_retire_accepts_a_foreign_by",
    "7": "test_the_migration_invents_nothing",
    "8": "test_the_report_names_what_waits_for_judgement",
    "9": "test_rehearsal_reads_a_migrated_ticket_alike"}}

PROOF_TIMEOUT_S = 300

_LIVE = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE.is_file():
    _LIVE = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"

READ = "cairn/machines/rehearsal/rehearsal.py"
OPEN_WF = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
PROVED_WF = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]"
BOUNDS = {"in": ["a.py"], "out": ["b.py"]}
MEASURED = [{"when": "2026-11-16", "saw": "testing", "how": "testing"}]

TRAIL = [
    {"n": 3, "text": "MEASURED 2026-11-14: the widget already exists at a.py", "by": "cc"},
    {"n": 4, "text": "D4: folded into D1 on 2026-11-14 — D1 carries this whole", "by": "cc"},
    {"n": 5, "text": "SETTLES the seam D1 names", "by": "akien"},
    {"n": 6, "text": "re-point the old caller (superseded plan)", "by": "cc"},
    {"n": 7, "text": "Superseded by D1.", "by": "cc"},
]
NUMBERED = {
    "id": "aa3e00000001", "title": "testing-aa3e9a70db47 numbered",
    "falsifier": {"clauses": [{"n": 1, "claim": "testing: the widget is wired"},
                              {"n": 2, "claim": "testing: the widget is proved"}]},
    "decisions": [
        {"n": 1, "text": "D1: build the widget in a.py", "by": "cc", "writes_to": ["a.py"],
         "reads": [READ], "step": "FIXME 1", "source": "rehearsal", "at": "2026-11-14T00:00:00"},
        {"n": 2, "text": "wire the widget", "by": "akien", "writes_to": ["a.py"], "reads": []},
        *TRAIL,
        {"n": 8, "text": "D8: repoint the sibling proof to the widget", "by": "cc",
         "writes_to": ["a_proof.py"], "reads": []},
    ],
    "bounds": BOUNDS, "measured": MEASURED}
PROSE = {"id": "aa3e00000002", "title": "testing-aa3e9a70db47 prose",
         "falsifier": "RED if the widget is not wired (testing)",
         "decisions": [{"n": 1, "text": "D1: wire the widget", "by": "cc"}],
         "bounds": BOUNDS, "measured": MEASURED}
TOO_BIG = {"id": "aa3e00000003", "title": "testing-aa3e9a70db47 too big",
           "falsifier": {"clauses": [{"n": i, "claim": f"testing: claim {i}"} for i in range(1, 7)]},
           "decisions": [{"n": 1, "text": "one", "writes_to": [], "reads": []},
                         {"n": 2, "text": "two", "writes_to": [], "reads": []}],
           "bounds": BOUNDS, "measured": MEASURED}
COHERENT = {"id": "aa3e00000004", "title": "testing-aa3e9a70db47 coherent",
            "falsifier": {"clauses": [{"n": 1, "claim": "testing: the one claim"}]},
            "bounds": BOUNDS, "measured": MEASURED}
PROVED = {"id": "aa3e00000005", "title": "testing-aa3e9a70db47 proved",
          "falsifier": {"clauses": [{"n": 1, "claim": "testing: done"}]},
          "decisions": [{"n": 1, "text": "MEASURED: done", "by": "cc"},
                        {"n": 2, "text": "D2: build it", "by": "cc"}],
          "bounds": BOUNDS, "measured": MEASURED}
ALREADY = {"id": "aa3e00000006", "title": "testing-aa3e9a70db47 already",
           "outcomes": [{"n": 1, "claim": "testing: shaped", "writes_to": [], "reads": [], "after": []}],
           "bounds": BOUNDS, "measured": MEASURED}
FIXTURES = (NUMBERED, PROSE, TOO_BIG, COHERENT, PROVED, ALREADY)
OPEN = [f["id"] for f in FIXTURES if f is not PROVED]
MARKERS = ("fold", "measured", "settles", "re-point", "superseded")


def _stem(doc: dict) -> str:
    return f"{doc['id']}-{doc['title'].replace(' ', '-')}"


@contextmanager
def _world(fixtures=FIXTURES, tag="store"):
    top = Path(scratch_dir(f"testing-aa3e9a70db47-{tag}-"))
    commons = top / "CairnCommons"
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    shutil.copyfile(_LIVE, tickets / "_charter+why.json")
    for doc in fixtures:
        plan = tickets / f"{_stem(doc)}.json"
        plan.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        wf = PROVED_WF if doc is PROVED else OPEN_WF
        plan.with_name(plan.name[:-5] + ".state.json").write_text(
            json.dumps({"workflow_and_state": wf, "node_class": "code-seam"}, indent=2) + "\n",
            encoding="utf-8")
        if doc is PROVED:
            plan.with_name(plan.name[:-5] + ".log.jsonl").write_text(
                json.dumps({"kind": "field", "at": "2026-11-01T00:00:00", "actor": "cc",
                            "field": "notes", "value": "testing"}) + "\n", encoding="utf-8")
    try:
        yield commons
    finally:
        shutil.rmtree(top, ignore_errors=True)


def _plan(commons: Path, doc: dict) -> Path:
    return commons / "tickets" / f"{_stem(doc)}.json"


def _doc(commons: Path, doc: dict) -> dict:
    return json.loads(_plan(commons, doc).read_text(encoding="utf-8"))


def _migrate(commons: Path) -> dict:
    from cairn.machines.rehearsal import plan_migration
    return plan_migration.migrate(commons)


def _bytes(commons: Path) -> dict:
    return {p.name: p.read_bytes() for p in sorted((commons / "tickets").iterdir()) if p.is_file()}


def test_clauses_then_decisions_become_outcomes():
    with _world() as c:
        _migrate(c)
        for f in FIXTURES:
            if f is PROVED:
                continue
            d = _doc(c, f)
            assert "decisions" not in d, (f["id"], d)
            if isinstance(f.get("falsifier"), dict):
                assert "falsifier" not in d, (f["id"], d)
        got = _doc(c, NUMBERED)["outcomes"]
        assert got[:2] == [{"n": 1, "claim": "testing: the widget is wired", "writes_to": [], "reads": [], "after": []},
                           {"n": 2, "claim": "testing: the widget is proved", "writes_to": [], "reads": [], "after": []}], got
        assert got[2:] == [
            {"n": 3, "text": "build the widget in a.py", "writes_to": ["a.py"], "reads": [READ], "after": []},
            {"n": 4, "text": "wire the widget", "writes_to": ["a.py"], "reads": [], "after": []},
            {"n": 5, "text": "D8: repoint the sibling proof to the widget".split(": ", 1)[1],
             "writes_to": ["a_proof.py"], "reads": [], "after": []}], got
        assert _doc(c, PROSE)["outcomes"] == [{"n": 1, "text": "wire the widget", "after": []}]
        assert _doc(c, PROSE)["falsifier"] == PROSE["falsifier"]


def test_no_outcome_opens_with_trail_or_carries_by():
    with _world() as c:
        _migrate(c)
        for f in FIXTURES:
            if f is PROVED:
                continue
            for o in _doc(c, f)["outcomes"]:
                assert "by" not in o, (f["id"], o)
                text = str(o.get("text") or o.get("claim") or "").casefold()
                assert not text.startswith(MARKERS), (f["id"], o)


def test_every_moved_line_stands_in_the_log():
    from cairn.tools.base.ticket_log import read_log
    with _world() as c:
        _migrate(c)
        plan = _plan(c, NUMBERED)
        moved = [x["decision"] for x in read_log(plan, "decision_retired")]
        assert moved == TRAIL, moved
        bys = [x["value"] for x in read_log(plan, "field") if x.get("field") == "by"]
        assert bys == [{"n": 1, "by": "cc"}, {"n": 2, "by": "akien"}, {"n": 8, "by": "cc"}], bys
        keys = [x["value"] for x in read_log(plan, "field") if x.get("field") == "decision_keys"]
        assert keys == [{"n": 1, "step": "FIXME 1", "source": "rehearsal", "at": "2026-11-14T00:00:00"}], keys
        assert [x["value"] for x in read_log(_plan(c, PROSE), "field")] == [{"n": 1, "by": "cc"}]


def test_a_proved_ticket_is_byte_identical():
    with _world() as c:
        stem = _stem(PROVED)
        before = {k: v for k, v in _bytes(c).items() if k.startswith(stem)}
        assert len(before) == 3, sorted(before)
        got = _migrate(c)
        after = {k: v for k, v in _bytes(c).items() if k.startswith(stem)}
        assert after == before, "a PROVED ticket's files changed"
        assert PROVED["id"] not in got, got


def test_a_second_run_writes_nothing():
    with _world() as c:
        first = _migrate(c)
        assert first[NUMBERED["id"]]["changed"] and not first[ALREADY["id"]]["changed"], first
        snap = _bytes(c)
        second = _migrate(c)
        assert _bytes(c) == snap, "a second run wrote a ticket or a log"
        assert not any(r["changed"] or r["trail_moved"] or r["by_moved"] for r in second.values()), second


def test_retire_accepts_a_foreign_by():
    from cairn.machines.rehearsal import rehearsal as R
    doc = {"id": "aa3e00000007", "title": "testing-aa3e9a70db47 retire",
           "decisions": [{"n": 1, "text": "his words", "by": "akien"}, {"n": 2, "text": "mine", "by": "cc"}]}
    with _world((doc,), tag="retire") as c:
        R.retire(doc["id"], [1], by="cc", because="testing: superseded", root=c)
        assert [d["n"] for d in _doc(c, doc)["decisions"]] == [2]
        try:
            R._retire_lacks({"decisions": doc["decisions"]}, _plan(c, doc), [2], "cc", "x", None)
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(f"the lack check raised: {exc}")
        lacks = R._retire_lacks({"decisions": doc["decisions"]}, _plan(c, doc), [1], "someone", "x", None)
        assert not [x for x in lacks if "not yours" in x], lacks


def test_the_migration_invents_nothing():
    with _world() as c:
        _migrate(c)
        for f in FIXTURES:
            if f is PROVED:
                continue
            d = _doc(c, f)
            k = len((f.get("falsifier") or {}).get("clauses") or []) if isinstance(f.get("falsifier"), dict) else 0
            if f is ALREADY:
                k = len(f["outcomes"])
            for o in d["outcomes"]:
                if o["n"] > k:
                    assert "claim" not in o, (f["id"], o)
                assert o.get("after") == [] and "via" not in o, (f["id"], o)
            assert "constraints" not in d and "resources" not in d, (f["id"], sorted(d))
            assert json.dumps(d["bounds"]) == json.dumps(f["bounds"]), f["id"]
            assert json.dumps(d["measured"]) == json.dumps(f["measured"]), f["id"]
        assert "writes_to" not in _doc(c, PROSE)["outcomes"][0], "an absent path list was invented"


def test_the_report_names_what_waits_for_judgement():
    with _world() as c:
        got = _migrate(c)
        assert sorted(got) == sorted(OPEN), sorted(got)
        assert got[NUMBERED["id"]]["awaiting"] == [3, 4, 5], got[NUMBERED["id"]]
        assert got[NUMBERED["id"]]["trail_moved"] == 5 and got[NUMBERED["id"]]["by_moved"] == 3
        assert got[TOO_BIG["id"]]["too_big"] is True, got[TOO_BIG["id"]]
        assert got[PROSE["id"]]["prose_falsifier"] is True, got[PROSE["id"]]
        for tid in (NUMBERED["id"], PROSE["id"]):
            assert got[tid]["too_big"] is False, got[tid]
        for tid in (COHERENT["id"], ALREADY["id"]):
            r = got[tid]
            assert r["awaiting"] == [] and not r["too_big"] and not r["prose_falsifier"], r


def _plan_section(text: str) -> dict:
    body = text[text.index("# THE PLAN"):text.index("# WHAT EXISTS")]
    return json.loads(body[body.index("```json") + 7:body.rindex("```")])


def _reads(R, tid: str, c: Path) -> dict:
    from cairn.tools.base import plan as plan_view
    tk = R.ticket_file(tid, c)
    doc = json.loads(tk.read_text(encoding="utf-8"))
    sect = _plan_section(R.render(tid, root=c)[0])
    return {"steps": sect["steps"], "context": sect.get("context"),
            "ids": sorted(R.decision_ids_of(doc)),
            "lines": [{k: s[k] for k in ("n", "text", "writes_to", "reads")} for s in plan_view.steps(doc)]}


def test_rehearsal_reads_a_migrated_ticket_alike():
    from cairn.machines.rehearsal import rehearsal as R
    doc = {"id": "aa3e00000008", "title": "testing-aa3e9a70db47 alike",
           "intention": "testing: one ticket read in two shapes",
           "falsifier": "RED if the widget is not wired (testing)",
           "decisions": [{"n": 1, "text": "build the widget", "writes_to": ["a.py"], "reads": [READ]},
                         {"n": 2, "text": "wire the widget", "writes_to": ["a.py"], "reads": []},
                         {"n": 3, "text": "note the widget's history", "writes_to": [], "reads": []}]}
    with _world((doc,), tag="before") as old, _world((doc,), tag="after") as new:
        _migrate(new)
        assert "outcomes" in _doc(new, doc) and "decisions" in _doc(old, doc)
        tid = doc["id"]
        assert _reads(R, tid, old) == _reads(R, tid, new), (_reads(R, tid, old), _reads(R, tid, new))
        for c in (old, new):
            R.decide(tid, "D2", "wire the widget at the rack", by="cc", root=c,
                     writes_to=["a.py", "rack.py"], reads=[READ])
        assert _reads(R, tid, old) == _reads(R, tid, new), (_reads(R, tid, old), _reads(R, tid, new))
        for c in (old, new):
            R.scope(tid, [3], by="cc", because="testing: context, not a step", root=c)
        a, b = _reads(R, tid, old), _reads(R, tid, new)
        assert a == b and a["context"] and a["ids"] == [1, 2], (a, b)


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
