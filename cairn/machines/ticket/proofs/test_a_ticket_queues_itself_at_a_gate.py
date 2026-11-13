"""Proof for ticket 152d76785229 — a ticket queues itself at a gate.

Outline 3.3.4.3 and 9.6 (Akien 2026-11-10, Q#80/Q#81 answers): a ticket is a class and a
machine; it crosses a gate by sending its fileref to devices/codemother/0/machines/<gate>/queueme;
the gate's own instance processes the pass or the fail; on a pass the ticket goes to the next
step and alerts the probes watching the gate. On a fail it waits in the trouble lane CC and Akien
read (outline 3.3.4, Q#85, ticket 794835a34ec9): one trouble naming the gate and every lack, and
no post to a design verb no machine answers.

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
from cairn.tools.scratch.scratch import scratch_dir
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
        # clause 4's design request is superseded by 794835a34ec9; the kick-back still holds
        "4": "test_a_fail_kicks_back_to_fixme_and_waits_in_the_trouble_lane",
        "5": "test_at_resolves_an_id_or_a_path_and_refuses_nothing",
    },
    "fa4462c803d6": {
        # clause 7's design request is superseded by 794835a34ec9; the stand-still still holds
        "7": "test_a_fail_before_buildme_stays_put_and_waits_in_the_trouble_lane",
    },
    "794835a34ec9": {
        "1": "test_a_fail_kicks_back_to_fixme_and_waits_in_the_trouble_lane",
        "2": "test_a_fail_before_buildme_stays_put_and_waits_in_the_trouble_lane",
        "3": "test_a_pass_at_the_refusing_gate_clears_the_refused_trouble",
    },
    "e5e05e96f0c0": {"1": "test_a_fail_at_fixme_stays_put_and_waits_in_the_trouble_lane"},
}

_TID = "fixturet2a01"
_LIVE_STORE_CHARTER = (_REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json")
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"

# hollow runs this proof in a worktree with no CairnCommons beside it, where transitions'
# repo-relative class table points at nothing (measured 2026-11-11, fa4462c803d6's first hollow):
# so with no sibling, the class-table defaults read the home checkout, for this process only.
if not (_REPO_ROOT.parent / "CairnCommons").is_dir():
    from cairn.tools.base import transitions as _transitions
    _transitions._NODE_CLASSES = _LIVE_STORE_CHARTER.parents[1] / "node_classes"
    for _fn in (_transitions.emit, _transitions.load_class_def):
        for _k in ("node_class_root", "root"):
            if _k in (_fn.__kwdefaults__ or {}):
                _fn.__kwdefaults__[_k] = _LIVE_STORE_CHARTER.parents[1] / "node_classes"


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
    tmp = scratch_dir("t2-ticket-")
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
                                 "body": {"fileref": _TID},  # by id since 8bb8b4729f17
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


def _refused(w, ident) -> dict:
    """The detail of the newest raise naming ``ident`` in the world's roots (None: no raise)."""
    found = None
    for p in sorted(w["tmp"].rglob("*.raise_trouble.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("pointer") == ident:
            found = rec
    return found


def test_a_fail_kicks_back_to_fixme_and_waits_in_the_trouble_lane():
    """Clause 1: FIXME, the harbor told, NO request at all, one trouble naming every lack."""
    with _world("BUILDME") as w:
        t = _ticket(w)
        spy = _Spy()
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
        assert spy.requests == [], f"a refused ticket asked something: {spy.requests}"
        assert len(spy.posts) == 1, f"a refused ticket posted beyond the harbor: {spy.posts}"
        ident = f"ticket-refused-{_TID}-at-coverage"
        assert got["queued"] is False and got["trouble"] == ident, got
        assert got["workflow"] == st["workflow_and_state"], got
        rec = _refused(w, ident)
        assert rec is not None, f"no trouble {ident} raised in the roots"
        said = json.dumps(rec)
        for one in lacks:
            assert one["why"] in said, f"the refused trouble does not name {one['why']!r}: {rec}"
        assert t._stands_raised(ident), f"{ident} does not stand on the ticket's trail"
    print("ok test_a_fail_kicks_back_to_fixme_and_waits_in_the_trouble_lane")


def test_a_fail_before_buildme_stays_put_and_waits_in_the_trouble_lane():
    """Clause 2: a chart stage fails a ticket that stands at TICKETME, where FIXME (anchored
    before BUILDME) cannot be entered: the cursor stands, the lack lands, nothing is sent."""
    with _world("TICKETME") as w:
        t = _ticket(w)
        spy = _Spy()
        before = _state(w)["workflow_and_state"]
        hist = Path(w["history"])
        had = hist.read_bytes() if hist.is_file() else None
        lacks = [{"kind": "chart", "why": "the plan carries no chart.survey draft"}]
        got = t.failed(lacks, participant=spy, history_path=w["history"],
                       state_path=w["state"], actor="codemother", why="fixture chart fail",
                       gate="survey")
        st = _state(w)
        assert st["workflow_and_state"] == before and got["workflow"] == before, (st, got)
        assert st["fixme"] == [{"n": 1, "kind": "chart",
                                "missing": "the plan carries no chart.survey draft"}], st
        assert (hist.read_bytes() if hist.is_file() else None) == had, "a journal was written"
        assert spy.posts == [] and spy.requests == [], (spy.posts, spy.requests)
        ident = f"ticket-refused-{_TID}-at-survey"
        assert got["queued"] is False and got["trouble"] == ident, got
        assert t._stands_raised(ident), f"{ident} does not stand: the gate= keyword was ignored"
    print("ok test_a_fail_before_buildme_stays_put_and_waits_in_the_trouble_lane")


def test_a_fail_at_fixme_stays_put_and_waits_in_the_trouble_lane():
    """A gate fails a ticket that already stands at FIXME (a concept-piece repaired in place,
    measured 2026-11-12 on 0682e51ab011): FIXME -> FIXME is no crossing, so the cursor stands,
    the lacks land, nothing is journaled, and the refusal waits in the trouble lane — never
    ``IllegalTransition: 'FIXME' -> 'FIXME' is a no-op``."""
    import cairn.tools.base.ticket_file as tf
    with _world("TICKETME") as w:
        at_fixme = ("concept-piece@v1: THINKME -> TICKETME -> [FIXME:waiting] -> BUILDME -> "
                    "PROVEME -> PROVED")
        tf.state_path(w["plan"]).write_text(json.dumps(
            {"workflow_and_state": at_fixme, "node_class": "concept-piece"}, indent=2) + "\n")
        t = _ticket(w)
        hist = Path(w["history"])
        had = hist.read_bytes() if hist.is_file() else None
        lacks = [{"kind": "chart", "why": "decompose names no writes_to"}]
        got = t.failed(lacks, participant=_Spy(), history_path=w["history"],
                       state_path=w["state"], actor="codemother", why="fixture fail at FIXME",
                       gate="decompose")
        st = _state(w)
        assert st["workflow_and_state"] == at_fixme and got["workflow"] == at_fixme, (st, got)
        assert st["fixme"] == [{"n": 1, "kind": "chart",
                                "missing": "decompose names no writes_to"}], st
        assert (hist.read_bytes() if hist.is_file() else None) == had, "a journal was written"
        ident = f"ticket-refused-{_TID}-at-decompose"
        assert got["queued"] is False and got["trouble"] == ident, got
        assert t._stands_raised(ident), f"{ident} does not stand"
    print("ok test_a_fail_at_fixme_stays_put_and_waits_in_the_trouble_lane")


def test_a_pass_at_the_refusing_gate_clears_the_refused_trouble():
    """Clause 3: queued-but-not-passed leaves the refusal standing; passed true clears it."""
    with _world("TICKETME") as w:
        t = _ticket(w)
        ident = f"ticket-refused-{_TID}-at-gate_x"
        t.failed([{"kind": "gate_x", "why": "a fixture lack"}], participant=_Spy(),
                 history_path=w["history"], state_path=w["state"], actor="cc", why="fixture")
        assert t._stands_raised(ident), f"{ident} was not raised"
        t.queueme("gate_x", participant=_Spy([{"body": {"accepted": True, "passed": False}}]))
        assert t._stands_raised(ident), "a reply that did not pass cleared the refusal"
        t.queueme("gate_y", participant=_Spy([{"body": {"accepted": True, "passed": True}}]))
        assert t._stands_raised(ident), "a pass at ANOTHER gate cleared gate_x's refusal"
        t.queueme("gate_x", participant=_Spy([{"body": {"accepted": True, "passed": True}}]))
        assert not t._stands_raised(ident), "a pass at the refusing gate left the refusal standing"
    print("ok test_a_pass_at_the_refusing_gate_clears_the_refused_trouble")


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
