"""Proof for ticket cd8a1de6139c — a ticket charts itself stage by stage.

Outline 9.6 (Akien 2026-11-10, Q#81): each chart stage and the verdict is a gate machine that
answers ``queueme <fileref>``, and the ticket class queues itself to each in turn. Outline
3.3.4.3: the ticket sends only its fileref and its life is data on disk, so a stage's draft
stands on the ticket (the plan's ``chart``) and the berth the gate wrote is recorded there too
(``<stage>_berth`` in the state's ``chart_claim``, the shape it already carries).

The world is a scratch tickets store (the live store charter copied in), ``ticket_file._TICKETS``
pointed at it for each tooth, and a spy participant standing in for the bus. ``Ticket`` is bound
inside each tooth, never at import.

    python3 cairn/machines/ticket/proofs/test_a_ticket_charts_itself_stage_by_stage.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "cd8a1de6139c": {
        "1": "test_a_draft_lands_on_the_plan_and_an_unknown_stage_writes_nothing",
        "2": "test_a_berth_lands_on_the_state_beside_the_earlier_ones",
        "3": "test_chart_queues_at_every_stage_in_order_with_only_the_fileref",
        "4": "test_chart_stops_at_the_first_stage_that_does_not_pass",
        "5": "test_the_store_charter_shapes_chart_and_the_cast_door_enforces_it",
    },
}

_TID = "fixturech4a1"
_LIVE_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"
_STAGES = ["orient", "constrain", "survey", "decompose", "triage", "hypothesize", "validate"]
_WF = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"


class _Spy:
    """A bus participant: records every request and post; answers request() from a script."""

    def __init__(self, replies=None):
        self.requests: list[dict] = []
        self.posts: list[dict] = []
        self._replies = list(replies or [])

    def request(self, *, to, channel="personal", why, verb="", body=None, timeout=30.0):
        self.requests.append({"to": to, "verb": verb, "body": body})
        if self._replies:
            return self._replies.pop(0)
        return {"body": {"accepted": True, "passed": True}}

    def post(self, *, to, channel="personal", why, verb="", body=None, reply_to=None):
        self.posts.append({"to": to, "verb": verb, "body": body})
        return {"id": f"post-{len(self.posts)}"}


@contextmanager
def _world():
    import cairn.tools.base.ticket_file as tf
    tmp = Path(tempfile.mkdtemp(prefix="t4a-chart-"))
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "cairn/machines/ticket/intention+why.json"},
                               indent=2) + "\n")
    tf.state_path(plan).write_text(json.dumps({"workflow_and_state": _WF,
                                               "node_class": "code-seam"}, indent=2) + "\n")
    roots = {k: tmp / k for k in ("repo", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    was = tf._TICKETS
    tf._TICKETS = store
    try:
        yield {"tmp": tmp, "store": store, "plan": plan, "roots": roots}
    finally:
        tf._TICKETS = was
        shutil.rmtree(tmp, ignore_errors=True)


def _ticket(w):
    from cairn.machines.ticket.ticket import Ticket
    return Ticket.at(_TID, tickets_dir=w["store"], roots=w["roots"])


def _plan(w) -> dict:
    return json.loads(w["plan"].read_text(encoding="utf-8"))


def _state(w) -> dict:
    import cairn.tools.base.ticket_file as tf
    return json.loads(tf.state_path(w["plan"]).read_text(encoding="utf-8"))


def test_a_draft_lands_on_the_plan_and_an_unknown_stage_writes_nothing():
    with _world() as w:
        t = _ticket(w)
        packet = {"sought": ["x"], "holdings": [], "absences": []}
        t.draft("survey", packet, why="fixture draft")
        assert _plan(w).get("chart") == {"survey": packet}, _plan(w)
        assert "chart" not in _state(w), _state(w)
        assert t.drafted("survey") == packet and t.drafted("orient") is None
        before = w["plan"].read_bytes()
        try:
            t.draft("nosuchstage", packet, why="fixture")
        except ValueError as exc:
            assert "orient" in str(exc) and "validate" in str(exc), exc
        else:
            raise AssertionError("an unknown stage was drafted")
        assert w["plan"].read_bytes() == before
    print("ok test_a_draft_lands_on_the_plan_and_an_unknown_stage_writes_nothing")


def test_a_berth_lands_on_the_state_beside_the_earlier_ones():
    with _world() as w:
        t = _ticket(w)
        t.berthed("orient", "/b/orient-1.json", why="fixture")
        t.berthed("constrain", "/b/constrain-1.json", why="fixture")
        st = _state(w)
        assert st.get("chart_claim") == {"orient_berth": "/b/orient-1.json",
                                         "constrain_berth": "/b/constrain-1.json"}, st
        assert st.get("workflow_and_state") == _WF, st
        assert "chart_claim" not in _plan(w)
        assert t.berth("orient") == "/b/orient-1.json" and t.berth("validate") is None
    print("ok test_a_berth_lands_on_the_state_beside_the_earlier_ones")


def test_chart_queues_at_every_stage_in_order_with_only_the_fileref():
    with _world() as w:
        t = _ticket(w)
        spy = _Spy()
        got = t.chart(participant=spy)
        assert [r["verb"] for r in spy.requests] == [f"machines/{s}/queueme" for s in _STAGES], spy.requests
        assert all(r["to"] == "codemother" for r in spy.requests), spy.requests
        assert all(r["body"] == {"fileref": str(w["plan"])} for r in spy.requests), spy.requests
        assert got["charted"] is True and got["stopped_at"] is None, got
        assert [s["stage"] for s in got["stages"]] == _STAGES, got
    print("ok test_chart_queues_at_every_stage_in_order_with_only_the_fileref")


def test_chart_stops_at_the_first_stage_that_does_not_pass():
    with _world() as w:
        t = _ticket(w)
        ok = {"body": {"accepted": True, "passed": True}}
        spy = _Spy([ok, ok, {"body": {"accepted": True, "passed": False, "lacks": ["x"]}}])
        got = t.chart(participant=spy)
        assert len(spy.requests) == 3, spy.requests
        assert got["charted"] is False and got["stopped_at"] == "survey", got
    with _world() as w:
        t = _ticket(w)
        spy = _Spy([{"body": {"accepted": False, "reason": "no"}}])
        got = t.chart(participant=spy)
        assert len(spy.requests) == 1 and got["stopped_at"] == "orient", (spy.requests, got)
    print("ok test_chart_stops_at_the_first_stage_that_does_not_pass")


def test_the_store_charter_shapes_chart_and_the_cast_door_enforces_it():
    from cairn.tools.base.transitions import _shape_lacks
    live = json.loads(_LIVE_STORE_CHARTER.read_text(encoding="utf-8"))
    assert "chart" in live["plan_fields"], live["plan_fields"]
    assert "chart" in (live.get("plan_shapes") or {}), list(live.get("plan_shapes") or {})
    assert "chart_berths" not in live["state_fields"], live["state_fields"]
    assert "chart_claim" in live["state_fields"], live["state_fields"]
    good = _shape_lacks({"chart": {"survey": {"sought": []}}}, _LIVE_STORE_CHARTER)
    assert not [x for x in good if x.startswith("chart")], good
    bad = _shape_lacks({"chart": {"nosuchstage": {}, "orient": "a string"}}, _LIVE_STORE_CHARTER)
    assert any("chart.nosuchstage" in x for x in bad) and any("chart.orient" in x for x in bad), bad
    print("ok test_the_store_charter_shapes_chart_and_the_cast_door_enforces_it")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))
