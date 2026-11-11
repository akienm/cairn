"""Proof for ticket 0be964512fb0, clause 8 — a passed ticket crosses through the gate's door.

Outline 3.3.4.3 and 9.6 (Akien 2026-11-10): the gate instantiates the ticket from its fileref
and the ticket processes the pass. The clearance gate is a door that itself records the
crossing (``clearance.clear`` wraps ``transitions.emit``), so ``Ticket.passed`` takes that door
as its ``cross`` callable: the crossing rides it exactly once and never a second time through
``transitions.emit``, and the cursor written onto the ticket is the one the door returned.

The world is a scratch tickets store (the live store charter copied in), ``ticket_file._TICKETS``
pointed at it for the tooth, and a spy participant standing in for the bus.

    python3 cairn/machines/ticket/proofs/test_a_passed_ticket_crosses_through_the_gates_door.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"0be964512fb0": {"8": "test_a_pass_crosses_through_the_door_it_is_handed"}}

_TID = "fixturecr0s8"
_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
_OLD = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
_NEW = "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"


class _Spy:
    def __init__(self):
        self.posts: list[dict] = []

    def request(self, **kw):
        raise AssertionError(f"a pass asked something: {kw}")

    def post(self, *, to, verb="", why="", body=None, **_):
        self.posts.append({"to": to, "verb": verb, "body": body})


def test_a_pass_crosses_through_the_door_it_is_handed():
    import cairn.tools.base.ticket_file as tf
    import cairn.tools.base.transitions as transitions
    from cairn.machines.ticket.ticket import Ticket

    tmp = Path(tempfile.mkdtemp(prefix="t-cross-door-"))
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "cairn/machines/ticket/" + "intention" + "+why.json"},
                               indent=2) + "\n")
    tf.state_path(plan).write_text(json.dumps({"workflow_and_state": _OLD,
                                               "node_class": "code-seam"}, indent=2) + "\n")
    roots = {k: tmp / k for k in ("repo", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    calls: list[tuple] = []

    def door(workflow, target, **kw):
        calls.append((workflow, target, kw))
        return _NEW

    def no_emit(*a, **kw):
        raise AssertionError("transitions.emit was reached beside the door it was handed")

    was_tickets, was_emit = tf._TICKETS, transitions.emit
    tf._TICKETS, transitions.emit = store, no_emit
    try:
        t = Ticket.at(_TID, tickets_dir=store, roots=roots)
        spy = _Spy()
        new = t.passed("BUILDME", participant=spy, history_path=str(tmp / "history.json"),
                       state_path=str(tmp / "state.json"), actor="codemother",
                       why="fixture pass", cross=door)
        state = json.loads(tf.state_path(plan).read_text(encoding="utf-8"))
    finally:
        tf._TICKETS, transitions.emit = was_tickets, was_emit
        shutil.rmtree(tmp, ignore_errors=True)
    assert len(calls) == 1, calls
    workflow, target, kw = calls[0]
    assert (workflow, target) == (_OLD, "BUILDME"), calls[0]
    assert kw.get("ticket") == _TID and kw.get("actor") == "codemother", kw
    assert new == _NEW and state["workflow_and_state"] == _NEW, (new, state)
    harbor = [p for p in spy.posts if p["to"] == "harbor_master"]
    assert len(harbor) == 1 and harbor[0]["body"]["to"] == "BUILDME", spy.posts
    print("ok test_a_pass_crosses_through_the_door_it_is_handed")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))
