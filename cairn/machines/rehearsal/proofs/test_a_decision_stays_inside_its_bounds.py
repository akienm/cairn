"""Proof for ticket 4be9d02c71a6: ``rehearse --decide`` runs the cast door's shape check, and a
ticket's ``bounds.out`` is a hard edge.

Measured 2026-11-16: 96c1c2ea5ce9 and f695fac922cd took writes outside bounds.in at decide
commits afa3a151/149d6c28 and f00cddf1, and nothing checked them; decide never called
transitions._shape_lacks. The orchestrator, 2026-11-16: "The bounds' out list is a hard edge
('out is out'). So decide refuses outright a write to a path in bounds.out; no widening. Only a
path in neither list may widen bounds.in, and the decision line names it as a widening."

  1. a decision writing a path bounds.out names is refused with nothing written, the ticket
     byte-identical.
  2. a decision writing a path in neither list lands; bounds.in gains the path; the line's text
     names the widening. A decision writing only inside bounds.in widens nothing and says so
     nowhere.
  3. a decision whose plan the shape check would newly refuse (a reads path that resolves to no
     file) is refused naming the lack, the ticket byte-identical; a lack the ticket already
     carried does not stop a clean decision.

The world: a scratch commons holding the live store charter and testing-marked fixture tickets.
Nothing reads or writes the live corpus.

    PYTHONPATH=. python3 cairn/machines/rehearsal/proofs/test_a_decision_stays_inside_its_bounds.py
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

PROVES = {"4be9d02c71a6": {
    "1": "test_a_write_into_bounds_out_is_refused",
    "2": "test_a_write_in_neither_list_widens_bounds_in_by_name",
    "3": "test_a_newly_shapeless_plan_is_refused"}}

PROOF_TIMEOUT_S = 120

_LIVE = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE.is_file():
    _LIVE = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"

READ = "cairn/machines/rehearsal/rehearsal.py"
WF = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
TID = "4be900000001"
DOC = {"id": TID, "title": "testing-4be9d02c71a6 bounds",
       "falsifier": {"clauses": [{"n": 1, "claim": "testing: the widget is wired"}]},
       "decisions": [{"n": 1, "text": "D1: build the widget", "by": "cc",
                      "writes_to": ["a.py"], "reads": [READ]}],
       "bounds": {"in": ["a.py"], "out": ["b.py", "every other component"]},
       "measured": [{"when": "2026-11-16", "saw": "testing", "how": "testing"}]}


@contextmanager
def _world(doc=DOC, tag="w"):
    top = Path(scratch_dir(f"testing-4be9d02c71a6-{tag}-"))
    tickets = top / "CairnCommons" / "tickets"
    tickets.mkdir(parents=True)
    shutil.copyfile(_LIVE, tickets / "_charter+why.json")
    plan = tickets / f"{doc['id']}-testing-bounds.json"
    plan.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    plan.with_name(plan.name[:-5] + ".state.json").write_text(
        json.dumps({"workflow_and_state": WF, "node_class": "code-seam"}, indent=2) + "\n",
        encoding="utf-8")
    try:
        yield top / "CairnCommons", plan
    finally:
        shutil.rmtree(top, ignore_errors=True)


def _refused(fn) -> str | None:
    from cairn.machines.rehearsal.rehearsal import Refused
    try:
        fn()
    except Refused as exc:
        return str(exc)
    return None


def test_a_write_into_bounds_out_is_refused():
    from cairn.machines.rehearsal import rehearsal as R
    with _world(tag="out") as (c, plan):
        before = plan.read_bytes()
        why = _refused(lambda: R.decide(TID, "FIXME 1", "write the sibling", by="cc", root=c,
                                        writes_to=["a.py", "b.py"], reads=[READ]))
        assert why and "out is out" in why and "b.py" in why, why
        assert plan.read_bytes() == before


def test_a_write_in_neither_list_widens_bounds_in_by_name():
    from cairn.machines.rehearsal import rehearsal as R
    with _world(tag="wide") as (c, plan):
        e = R.decide(TID, "FIXME 1", "wire the rack", by="cc", root=c,
                     writes_to=["a.py", "rack.py"], reads=[READ])
        doc = json.loads(plan.read_text(encoding="utf-8"))
        assert doc["bounds"]["in"] == ["a.py", "rack.py"], doc["bounds"]
        assert doc["bounds"]["out"] == DOC["bounds"]["out"], doc["bounds"]
        assert e["text"].endswith("(widens bounds.in: rack.py)"), e
        line = [d for d in doc["decisions"] if d["n"] == e["n"]][0]
        assert line["text"] == e["text"], line
        e2 = R.decide(TID, "FIXME 2", "touch the widget again", by="cc", root=c,
                      writes_to=["a.py"], reads=[])
        assert "widens" not in e2["text"], e2
        assert json.loads(plan.read_text(encoding="utf-8"))["bounds"]["in"] == ["a.py", "rack.py"]


def test_a_newly_shapeless_plan_is_refused():
    from cairn.machines.rehearsal import rehearsal as R
    with _world(tag="shape") as (c, plan):
        before = plan.read_bytes()
        why = _refused(lambda: R.decide(TID, "FIXME 1", "read a ghost", by="cc", root=c,
                                        writes_to=["a.py"], reads=["no/such/file.py"]))
        assert why and "shape check" in why and "no/such/file.py" in why, why
        assert plan.read_bytes() == before
    stale = json.loads(json.dumps(DOC))
    stale["decisions"][0]["reads"] = ["no/such/old.py"]  # a lack the ticket already carries
    with _world(stale, tag="stale") as (c, plan):
        e = R.decide(TID, "FIXME 1", "a clean line", by="cc", root=c, writes_to=["a.py"], reads=[READ])
        assert e["n"] == 2, e


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
