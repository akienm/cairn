"""Proof for ticket 8bb8b4729f17: a ticket queues itself at a far box's gate by its id.

MEASURED 2026-11-12 on akienasus, its bus home on akiendelllinux: ``sail.py chart ee88c2126abc``
was refused
    codemother verb 'machines/orient/queueme' handler raised NotImplementedError:
    Non-relative patterns are unsupported
Ticket.queueme sent this box's absolute plan path. The far gate's Ticket.at could not open it,
so find_ticket globbed it, and pathlib refuses an absolute glob pattern.

  1. test_queueme_names_the_ticket_by_its_id: the request body is {"fileref": <the id>};
  2. test_a_far_box_resolves_what_queueme_sent: a spy captures the body; the sender's store
     is then removed (it is not on the far box), and Ticket.at over the captured fileref, in a
     far store holding a copy of the plan, resolves to that copy with the same id.

Both stores are scratch directories. This proof measures only cairn/machines/ticket.

    bin/cairn test cairn/machines/ticket/proofs/test_a_ticket_queues_itself_by_its_id.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"8bb8b4729f17": {
    "1": "test_queueme_names_the_ticket_by_its_id",
    "2": "test_a_far_box_resolves_what_queueme_sent",
}}

_TID = "testing8bb8a"
_WF = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"


class _Spy:
    """Stands in for the bus: records each request body, and takes every ask."""

    def __init__(self):
        self.bodies: list = []

    def request(self, *, to, channel="personal", why, verb="", body=None, timeout=30.0):
        self.bodies.append(body)
        return {"body": {"accepted": True}}

    def post(self, *, to, channel="personal", why, verb="", body=None, reply_to=None):
        return {"id": "post"}


def _store(root: Path) -> Path:
    import cairn.tools.base.ticket_file as tf
    store = root / "tickets"
    store.mkdir(parents=True)
    plan = store / f"{_TID}-a-testing-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a testing ticket",
                                "owning_intention": "cairn/machines/ticket/intention+why.json"}) + "\n")
    tf.state_path(plan).write_text(json.dumps({"workflow_and_state": _WF,
                                               "node_class": "code-seam"}) + "\n")
    return plan


def _sent(tmp: Path) -> tuple:
    """Queue a ticket from a sender store under ``tmp``; return (spy, the sender plan)."""
    from cairn.machines.ticket.ticket import Ticket
    plan = _store(tmp / "this-box")
    roots = {k: tmp / "this-box" / k for k in ("repo", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    spy = _Spy()
    Ticket(plan, roots=roots).queueme("orient", participant=spy)
    assert len(spy.bodies) == 1, f"queueme sent {len(spy.bodies)} requests"
    return spy, plan


def test_queueme_names_the_ticket_by_its_id():
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-8bb8b4729f17-id-")
    try:
        spy, plan = _sent(tmp)
        assert spy.bodies[0] == {"fileref": _TID}, (
            f"queueme named the ticket {spy.bodies[0]!r}, not by its id {_TID!r}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_a_far_box_resolves_what_queueme_sent():
    from cairn.machines.ticket.ticket import Ticket
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-8bb8b4729f17-far-")
    try:
        spy, plan = _sent(tmp)
        far_plan = _store(tmp / "far-box")
        shutil.rmtree(tmp / "this-box")
        assert not plan.exists(), "the sender's plan must not exist on the far box"
        ref = spy.bodies[0]["fileref"]
        try:
            got = Ticket.at(ref, tickets_dir=far_plan.parent)
        except Exception as exc:  # the measured failure is NotImplementedError from find_ticket
            raise AssertionError(f"the far box could not resolve {ref!r}: "
                                 f"{type(exc).__name__}: {exc}") from exc
        assert Path(got.fileref) == far_plan, f"resolved to {got.fileref}, not the far copy {far_plan}"
        assert got.id == _TID, f"resolved ticket id {got.id!r}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
