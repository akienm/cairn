"""Proof for ticket 239740d9db04: a refused ask names the refusal, not a missing handler.

Measured 2026-11-16: 9 live ticket-unqueued-<id>-at-clearance troubles, 12 occurrences between
2026-11-14 and 2026-11-16, every one saying "asked codemother to queue it at clearance and no
handler took it". In every one the recorded reply was codemother's clearance gate answering
``accepted: False`` with a reason ("PROVEME crossing refused: component 'base' reds the
build_inspector ...", "'CC' may not move boat ... onto code that is not in proven-space ..."). No
reply was a bounce, and none was silence. ``Ticket.queueme`` wrote one why for every reply that
was not a take, so the trouble lane's why was false for all of them (Law 7), and the reason the
gate gave was left only in the occurrence's detail.

  1. a gate that answers and refuses: the trouble's why says the holder refused and does not say
     no handler took it, in the same words for two different reasons (outline 3.4.3.2.3), and
     the holder's reason rides in the detail; the ticket is not queued;
  2. a bounce, and a reply that never comes, still raise "no handler took it";
  3. the refusal raises the same ticket-unqueued identity, so a later taken ask still clears it.

Every tooth runs in a scratch world, as test_a_taken_ticket_clears_its_unqueued_trouble.py does:
a scratch tickets store with the live store charter, one fixture plan and state, and the
ticket's diagnostic roots under the same scratch dir, so its trail is never in ~/.cairn.

    python3 cairn/machines/ticket/proofs/test_a_refused_ask_names_the_refusal_not_a_missing_handler.py
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

PROVES = {"239740d9db04": {
    "1": "test_a_refusal_says_the_holder_refused_and_why",
    "2": "test_a_bounce_or_silence_still_says_no_handler_took_it",
    "3": "test_a_refusal_is_cleared_by_a_later_take"}}

_TID = "fixture2397a"
_GATE = "clearance"
_IDENTITY = f"ticket-unqueued-{_TID}-at-{_GATE}"
_NO_HANDLER = "no handler took it"
_REASON = ("PROVEME crossing refused: component 'fixture' reds the build_inspector "
           "(1 finding(s) across 44 check(s))")
_REFUSAL = {"body": {"accepted": False, "device": "codemother", "door": "clearance",
                     "refusal": "CrossingRefused", "reason": _REASON + "\n  [component_color] ..."}}
_LIVE_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"


class _Spy:
    """A bus participant answering request() from a script. A script entry that is an
    exception is raised; posts are recorded and dropped."""

    def __init__(self, replies):
        self._replies = list(replies)

    def request(self, **kw):
        got = self._replies.pop(0)
        if isinstance(got, BaseException):
            raise got
        return got

    def post(self, **kw):
        return {"id": "post"}


@contextmanager
def _ticket():
    import cairn.tools.base.ticket_file as tf
    from cairn.machines.ticket.ticket import Ticket
    tmp = scratch_dir("testing-2397-ticket-")
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "cairn/machines/ticket/intention+why.json"},
                               indent=2) + "\n")
    tf.state_path(plan).write_text(json.dumps(
        {"workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> "
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


def _records(t, kind: str) -> list[dict]:
    """Trail records of ``kind`` (raise_trouble | clear_trouble) naming the identity, newest
    first, each with its file name under ``_name``."""
    trail = Path(t.diagnostic_trail())
    if not trail.is_dir():
        return []
    out = []
    for p in sorted(trail.glob(f"*.{kind}.json"), key=lambda p: p.name, reverse=True):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("pointer") == _IDENTITY:
            out.append({**rec, "_name": p.name})
    return out


def _why(rec: dict) -> str:
    return str((rec.get("values") or {}).get("why") or "")


def test_a_refusal_says_the_holder_refused_and_why():
    other = {"body": {**_REFUSAL["body"], "reason": "fixme_gate refused: a different reason"}}
    whys = []
    for reply in (_REFUSAL, other):
        with _ticket() as t:
            got = t.queueme(_GATE, participant=_Spy([reply]))
            assert got["queued"] is False, got
            raised = _records(t, "raise_trouble")
            assert len(raised) == 1, raised
            why = _why(raised[0])
            assert _NO_HANDLER not in why, f"a refusal is recorded as a missing handler: {why!r}"
            assert "refused" in why, f"the why does not say the holder refused: {why!r}"
            detail = (raised[0].get("values") or {}).get("detail") or {}
            assert detail.get("reason") == reply["body"]["reason"], detail.get("reason")
            whys.append(why)
    assert whys[0] == whys[1], f"the why varies with the reason (outline 3.4.3.2.3): {whys}"


def test_a_bounce_or_silence_still_says_no_handler_took_it():
    for reply in ({"body": {"is_bounce": True, "reason": "codemother has no verb 'x'"}},
                  TimeoutError("no reply within 30s")):
        with _ticket() as t:
            got = t.queueme(_GATE, participant=_Spy([reply]))
            assert got["queued"] is False, got
            raised = _records(t, "raise_trouble")
            assert len(raised) == 1, raised
            assert _NO_HANDLER in _why(raised[0]), (reply, _why(raised[0]))


def test_a_refusal_is_cleared_by_a_later_take():
    with _ticket() as t:
        first = t.queueme(_GATE, participant=_Spy([_REFUSAL]))
        assert first["trouble"] == _IDENTITY, first
        second = t.queueme(_GATE, participant=_Spy([{"body": {"accepted": True}}]))
        assert second["queued"] is True, second
        raises, clears = _records(t, "raise_trouble"), _records(t, "clear_trouble")
        assert raises and clears, (raises, clears)
        assert clears[0]["_name"] > raises[0]["_name"], (raises, clears)


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
