"""Proof for ticket 152d76785229 — a ticket queues itself at a gate.

Outline 3.3.4.3 and 9.6 (Akien 2026-11-10, Q#80/Q#81 answers): a ticket is a class and a
machine; it crosses a gate by sending its fileref to devices/codemother/0/machines/<gate>/queueme;
the gate's own instance processes the pass or the fail; on a pass the ticket goes to the next
step and alerts the probes watching the gate; on a fail it asks design to queue it, and with no
handler it throws a trouble and waits.

Every tooth runs in a scratch world: a tempdir tickets store (the live store charter copied in,
one fixture plan and state), ``ticket_file._TICKETS`` pointed at it for the tooth, diagnostic
roots under the same tempdir, and a spy participant standing in for the bus. The crossing itself
is the REAL ``transitions.emit`` — the chokepoint is what passed() and failed() must ride.

    python3 cairn/machines/ticket/proofs/test_a_ticket_queues_itself_at_a_gate.py   # exit 0 = green
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
    "152d76785229": {
        "1": "test_queueme_asks_codemother_with_the_fileref_and_logs_it",
        "2": "test_a_bounce_or_a_timeout_raises_a_trouble_and_waits",
        "3": "test_a_pass_crosses_and_tells_the_harbor_and_the_watchers",
        "4": "test_a_fail_kicks_back_to_fixme_and_queues_at_design",
        "5": "test_at_resolves_an_id_or_a_path_and_refuses_nothing",
    },
    "fa4462c803d6": {
        "7": "test_a_fail_before_buildme_stays_put_and_queues_at_design",
    },
}

_TID = "fixturet2a01"
_LIVE_STORE_CHARTER = (_REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json")
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"


def _wf(cursor: str) -> str:
    steps = ["THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"]
    return "code-seam@v2: " + " -> ".join(f"[{s}]" if s == cursor else s for s in steps)


class _Spy:
    """A bus participant: records every request and post; answers request() from a script."""

    def __init__(self, replies=None):
        self.requests: list[dict] = []
        self.posts: list[dict] = []
        self._replies = list(replies or [])

    def request(self, *, to, channel="personal", why, verb="", body=None, timeout=30.0):
        self.requests.append({"to": to, "verb": verb, "body": body, "why": why})
        nxt = self._replies.pop(0) if self._replies else {"body": {"accepted": True}}
        if isinstance(nxt, BaseException):
            raise nxt
        return nxt

    def post(self, *, to, channel="personal", why, verb="", body=None, reply_to=None):
        self.posts.append({"to": to, "verb": verb, "body": body})
        return {"id": f"post-{len(self.posts)}"}


@contextmanager
def _world(cursor: str):
    import cairn.tools.base.ticket_file as tf
    tmp = Path(tempfile.mkdtemp(prefix="t2-ticket-"))
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "cairn/machines/ticket/intention+why.json"},
                               indent=2) + "\n")
    tf.state_path(plan).write_text(json.dumps({"workflow_and_state": _wf(cursor),
                                               "node_class": "code-seam"}, indent=2) + "\n")
    roots = {k: tmp / k for k in ("repo", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    was = tf._TICKETS
    tf._TICKETS = store
    try:
        yield {"tmp": tmp, "store": store, "plan": plan, "roots": roots,
               "history": str(tmp / "history.json"), "state": str(tmp / "state.json")}
    finally:
        tf._TICKETS = was
        shutil.rmtree(tmp, ignore_errors=True)


def _ticket(w):
    from cairn.machines.ticket.ticket import Ticket
    return Ticket.at(_TID, tickets_dir=w["store"], roots=w["roots"])


def _dialog(w) -> list[dict]:
    from cairn.tools.base.ticket_log import read_log
    return read_log(w["plan"], "gate_dialog")


def _state(w) -> dict:
    import cairn.tools.base.ticket_file as tf
    return json.loads(tf.state_path(w["plan"]).read_text(encoding="utf-8"))


def _troubles(w) -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="replace")
                     for p in w["tmp"].rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl"))


def test_queueme_asks_codemother_with_the_fileref_and_logs_it():
    with _world("BUILDME") as w:
        t = _ticket(w)
        spy = _Spy()
        got = t.queueme("gate_x", participant=spy)
        assert got["queued"] is True, got
        assert spy.requests == [{"to": "codemother", "verb": "machines/gate_x/queueme",
                                 "body": {"fileref": str(w["plan"])},
                                 "why": spy.requests[0]["why"]}], spy.requests
        log = _dialog(w)
        assert len(log) == 1 and log[0]["gate"] == "gate_x" and log[0]["queued"] is True, log
    print("ok test_queueme_asks_codemother_with_the_fileref_and_logs_it")


def test_a_bounce_or_a_timeout_raises_a_trouble_and_waits():
    for reply in ({"body": {"is_bounce": True, "reason": "no handler"}}, TimeoutError("no reply")):
        with _world("BUILDME") as w:
            t = _ticket(w)
            got = t.queueme("gate_x", participant=_Spy([reply]))
            ident = f"ticket-unqueued-{_TID}-at-gate_x"
            assert got["queued"] is False and got["trouble"] == ident, got
            assert ident in _troubles(w), f"{type(reply).__name__}: no trouble {ident} in the roots"
            log = _dialog(w)
            assert len(log) == 1 and log[0]["queued"] is False, log
    print("ok test_a_bounce_or_a_timeout_raises_a_trouble_and_waits")


def test_a_pass_crosses_and_tells_the_harbor_and_the_watchers():
    with _world("THINKME") as w:
        t = _ticket(w)
        spy = _Spy()
        new = t.passed("TICKETME", participant=spy, watchers=["probe_a", "probe_b"],
                       history_path=w["history"], state_path=w["state"], actor="cc",
                       why="fixture pass")
        assert "[TICKETME" in new, new
        assert _state(w)["workflow_and_state"] == new, _state(w)
        assert Path(w["history"]).is_file() and Path(w["history"]).read_text().strip(), \
            "the crossing journaled nothing to the given history"
        harbor = [p for p in spy.posts if p["to"] == "harbor_master"]
        assert len(harbor) == 1 and harbor[0]["verb"] == "crossing", spy.posts
        b = harbor[0]["body"]
        assert (b["ticket"], b["from"], b["to"], b["direction"]) == \
            (_TID, "THINKME", "TICKETME", "forward"), b
        nxt = {p["to"]: p for p in spy.posts if p["verb"] == "next_step"}
        assert set(nxt) == {"probe_a", "probe_b"}, spy.posts
        for p in nxt.values():
            assert p["body"] == {"ticket": _TID, "fileref": str(w["plan"]), "step": "TICKETME"}, p
    print("ok test_a_pass_crosses_and_tells_the_harbor_and_the_watchers")


def test_a_fail_kicks_back_to_fixme_and_queues_at_design():
    with _world("BUILDME") as w:
        t = _ticket(w)
        spy = _Spy([{"body": {"is_bounce": True, "reason": "no design device"}}])
        lacks = [{"kind": "coverage", "why": "clause 2 has no tooth"},
                 {"kind": "seal", "why": "the proof is unsealed"}]
        got = t.failed(lacks, participant=spy, history_path=w["history"],
                       state_path=w["state"], actor="cc", why="fixture fail")
        st = _state(w)
        assert "[FIXME" in st["workflow_and_state"], st
        assert st["fixme"] == [{"n": 1, "kind": "coverage", "missing": "clause 2 has no tooth"},
                               {"n": 2, "kind": "seal", "missing": "the proof is unsealed"}], st
        back = [p for p in spy.posts if p["to"] == "harbor_master"]
        assert len(back) == 1 and back[0]["body"]["direction"] == "back", spy.posts
        assert [r["verb"] for r in spy.requests] == ["machines/design/queueme"], spy.requests
        ident = f"ticket-unqueued-{_TID}-at-design"
        assert got["queued"] is False and got["trouble"] == ident, got
        assert ident in _troubles(w), f"no trouble {ident} in the roots"
    print("ok test_a_fail_kicks_back_to_fixme_and_queues_at_design")


def test_a_fail_before_buildme_stays_put_and_queues_at_design():
    """A chart stage fails a ticket that stands at TICKETME, where FIXME (anchored before BUILDME)
    cannot be entered: outline 3.3.4.3's whole fail is "it asks design to queue it"."""
    with _world("TICKETME") as w:
        t = _ticket(w)
        spy = _Spy()
        before = _state(w)["workflow_and_state"]
        hist = Path(w["history"])
        had = hist.read_bytes() if hist.is_file() else None
        lacks = [{"kind": "survey", "why": "the plan carries no chart.survey draft"}]
        got = t.failed(lacks, participant=spy, history_path=w["history"],
                       state_path=w["state"], actor="codemother", why="fixture chart fail")
        st = _state(w)
        assert st["workflow_and_state"] == before and got["workflow"] == before, (st, got)
        assert st["fixme"] == [{"n": 1, "kind": "survey",
                                "missing": "the plan carries no chart.survey draft"}], st
        assert (hist.read_bytes() if hist.is_file() else None) == had, "a journal was written"
        assert not [p for p in spy.posts if p["to"] == "harbor_master"], spy.posts
        assert [r["verb"] for r in spy.requests] == ["machines/design/queueme"], spy.requests
        assert got["queued"] is True, got
    print("ok test_a_fail_before_buildme_stays_put_and_queues_at_design")


def test_at_resolves_an_id_or_a_path_and_refuses_nothing():
    from cairn.machines.ticket.ticket import Ticket
    with _world("BUILDME") as w:
        by_id = Ticket.at(_TID, tickets_dir=w["store"])
        by_path = Ticket.at(str(w["plan"]))
        assert by_id.fileref == by_path.fileref == str(w["plan"]), (by_id.fileref, by_path.fileref)
        assert by_id.id == _TID, by_id.id
        try:
            Ticket.at("no-such-ticket", tickets_dir=w["store"])
        except FileNotFoundError as exc:
            assert "no-such-ticket" in str(exc), exc
        else:
            raise AssertionError("Ticket.at('no-such-ticket') resolved to something")
    print("ok test_at_resolves_an_id_or_a_path_and_refuses_nothing")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))
