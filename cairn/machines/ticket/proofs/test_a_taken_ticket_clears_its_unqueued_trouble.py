"""Proof for ticket 41a5bae3d01b — a taken ticket clears its own unqueued trouble.

Outline 3.3.4.3: a ticket queues itself at a gate and, when no handler takes it, raises
``ticket-unqueued-<id>-at-<gate>`` and waits. Measured 2026-11-11: four such troubles stood in the
live lane after their tickets had crossed, because nothing cleared the raise when a later ask at
the same gate was taken. Now ``Ticket.queueme`` clears its own standing raise when the gate takes
it, and sends no clear when nothing stands (the 5054-clears defect of 87f0fc7b3514 is the reason
for the second clause).

Every tooth runs in a scratch world: a tempdir tickets store (the live store charter copied in,
one fixture plan and state), ``ticket_file._TICKETS`` pointed at it, and the ticket's diagnostic
roots under the same tempdir, so its trail is read where it was written and never in ~/.cairn.

    python3 cairn/machines/ticket/proofs/test_a_taken_ticket_clears_its_unqueued_trouble.py
"""

from __future__ import annotations

import json
import shutil
import sys
from cairn.tools.scratch.scratch import scratch_dir
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "41a5bae3d01b": {
        "1": "test_a_refused_then_taken_ticket_leaves_its_trouble_cleared",
        "2": "test_a_taken_ticket_with_nothing_raised_sends_no_clear",
    },
}

_TID = "fixture41a5a"
_GATE = "clearance"
_IDENTITY = f"ticket-unqueued-{_TID}-at-{_GATE}"
_LIVE_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"


class _Spy:
    """A bus participant answering request() from a script; posts are recorded and dropped."""

    def __init__(self, replies):
        self._replies = list(replies)

    def request(self, **kw):
        return self._replies.pop(0)

    def post(self, **kw):
        return {"id": "post"}


@contextmanager
def _ticket():
    import cairn.tools.base.ticket_file as tf
    from cairn.machines.ticket.ticket import Ticket
    tmp = scratch_dir("t41a5-ticket-")
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "cairn/machines/ticket/intention+why.json"},
                               indent=2) + "\n")
    tf.state_path(plan).write_text(json.dumps(
        {"workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> "
                               "PROVEME -> PROVED", "node_class": "code-seam"}, indent=2) + "\n")
    roots = {k: tmp / k for k in ("repo", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    was = tf._TICKETS
    tf._TICKETS = store
    try:
        t = Ticket.at(_TID, tickets_dir=store, roots=roots)
        assert str(t.diagnostic_trail()).startswith(str(tmp)), (
            f"the ticket's trail {t.diagnostic_trail()} is outside the scratch world {tmp}")
        yield t
    finally:
        tf._TICKETS = was
        shutil.rmtree(tmp, ignore_errors=True)


def _naming(t, kind: str) -> list[str]:
    """Trail file names of ``kind`` (raise_trouble | clear_trouble) whose pointer is the identity,
    newest first."""
    trail = Path(t.diagnostic_trail())
    if not trail.is_dir():
        return []
    out = []
    for p in sorted(trail.glob(f"*.{kind}.json"), key=lambda p: p.name, reverse=True):
        if json.loads(p.read_text(encoding="utf-8")).get("pointer") == _IDENTITY:
            out.append(p.name)
    return out


def test_a_refused_then_taken_ticket_leaves_its_trouble_cleared():
    with _ticket() as t:
        spy = _Spy([{"body": {"is_bounce": True}}, {"body": {"accepted": True}}])
        first = t.queueme(_GATE, participant=spy)
        assert first["queued"] is False and first["trouble"] == _IDENTITY, first
        assert _naming(t, "raise_trouble"), "the refusal raised nothing into the scratch trail"
        second = t.queueme(_GATE, participant=spy)
        assert second["queued"] is True, second
        raises, clears = _naming(t, "raise_trouble"), _naming(t, "clear_trouble")
        assert clears, f"the taken ask sent no clear for {_IDENTITY}; raises {raises}"
        assert clears[0] > raises[0], (
            f"the newest record naming {_IDENTITY} is not the clear: raises {raises}, clears {clears}")


def test_a_taken_ticket_with_nothing_raised_sends_no_clear():
    with _ticket() as t:
        got = t.queueme(_GATE, participant=_Spy([{"body": {"accepted": True}}]))
        assert got["queued"] is True, got
        assert _naming(t, "clear_trouble") == [], (
            f"a taken ask with nothing raised sent a clear: {_naming(t, 'clear_trouble')}")


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)
