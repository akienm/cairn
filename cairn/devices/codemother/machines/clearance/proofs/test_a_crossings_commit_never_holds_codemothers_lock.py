"""Proof for ticket 7c4138f7fa33 — a crossing's commit never holds codemother's lock.

Measured 2026-11-24 on akiendelllinux: b03dce633aa8's PROVEME ``queueme`` ran ``Ticket.passed``
inline, and its records' ``git commit`` (pid 84628) ran 7m56s and counting under the pre-commit
reseal. Every other ask to codemother waited behind her one shim lock: the asker's reach timed out
at 120 s, a hollow's ``resolves_to`` ask at 300 s. e4714e460e32 took the chart and verdict stages
off that lock; clearance was not among them. The fix: the clearance gate queues the ticket on its
own FIFO, returns at once, and its one worker posts today's answer to the asker by ``reply_to``.

The world. The gate is the real ``ClearanceGate``, and today's body runs unchanged (the crossing
it derives, the hand, the answer it builds). The ticket is a stand-in whose ``passed`` makes the
CROSSING'S COMMIT for real: it writes the component's ``history.json`` in a scratch git repo and
commits it through the ticket machine's published ``commit_crossing_records``, and that repo's
pre-commit hook sleeps, so "a slow commit" is a git fact, not a mock. The Ticket class is proved
where it lives. Tooth 1 runs the real codemother shim on a scratch bus whose delivery is wrapped
in one lock per device, the shape the bus process installs (``server.py`` ``_locked_hook``), as
e4714e460e32's proof does.

    bin/cairn test cairn/devices/codemother/machines/clearance/proofs/test_a_crossings_commit_never_holds_codemothers_lock.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"7c4138f7fa33": {
    "1": "test_a_second_ask_is_answered_while_a_crossings_commit_runs",
    "2": "test_the_asker_hears_the_crossings_answer_by_reply_to_once_the_commit_lands",
    "3": "test_two_queuemes_for_one_ticket_cross_in_the_order_sent",
}}

_SLOW_S = 30.0   # clause 1: the commit's hook sleeps this long
_QUICK_S = 2.0   # clauses 2 and 3: long enough to see the order, short enough to run
_ANSWER_S = 5.0  # clause 1's bound
_WF = "code-seam@v2: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> PROVED"
_CROSSED = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"


def _git(cwd, *args) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    out = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=env)
    assert out.returncode == 0, f"git {args}: {out.stderr}"
    return out.stdout


class _Ticket:
    """A stand-in for the ticket the gate instantiates. Its ``passed`` makes the crossing's
    commit in the scratch repo (the hook sleeps), records when each crossing entered and left,
    and returns the crossed workflow, or raises ``refuse`` when one is set."""

    def __init__(self, tid: str, comp: Path, log: list, guard: threading.Lock,
                 refuse: Exception | None = None) -> None:
        self.id = tid
        self.fileref = f"/scratch/{tid}.json"
        self.workflow = _WF
        self._comp, self._log, self._guard, self._refuse = comp, log, guard, refuse

    def doc(self) -> dict:
        return {"id": self.id, "workflow_and_state": _WF,
                "owning_intention": str(self._comp / "intention+why.json")}

    def passed(self, target, *, participant, history_path, state_path, actor, why, cross=None,
               **extra):
        from cairn.machines.ticket.ticket import commit_crossing_records
        n = extra.get("asked_by")
        with self._guard:
            self._log.append(("in", n, time.monotonic()))
        try:
            if self._refuse is not None:
                raise self._refuse
            hist = Path(history_path)
            rows = json.loads(hist.read_text(encoding="utf-8"))
            rows.append({"crossed": target, "asked_by": n})
            hist.write_text(json.dumps(rows) + "\n", encoding="utf-8", newline="\n")
            commit_crossing_records(history_path, state_path, f"{self.id} passed into {target}")
            return _CROSSED
        finally:
            with self._guard:
                self._log.append(("out", n, time.monotonic()))


class _Spy:
    """The gate's participant: every post recorded, and a wait for the reply to one envelope."""

    def __init__(self) -> None:
        self.posts: list[dict] = []
        self._cv = threading.Condition()

    def post(self, **kw):
        with self._cv:
            self.posts.append(kw)
            self._cv.notify_all()
        return {"id": "spy"}

    def request(self, **kw):
        return {"accepted": True}

    def reply_to(self, envelope_id: str, timeout: float) -> dict | None:
        end = time.monotonic() + timeout
        with self._cv:
            while True:
                for p in self.posts:
                    if p.get("reply_to") == envelope_id:
                        return p
                left = end - time.monotonic()
                if left <= 0:
                    return None
                self._cv.wait(left)


@contextmanager
def _world(tid: str, hook_s: float, refuse: Exception | None = None):
    """A scratch git repo holding the boat's component (its pre-commit hook writes a marker and
    sleeps ``hook_s``), and ``Ticket.at`` answering the stand-in by ``tid``; restored on exit."""
    from cairn.machines.ticket.ticket import Ticket
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("t7c41-clearance-")
    repo = tmp / "repo"
    comp = repo / "comp"
    comp.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "proof@example.invalid")
    _git(repo, "config", "user.name", "proof")
    (comp / "intention+why.json").write_text('{"intention": "a fixture boat"}\n')
    (comp / "history.json").write_text("[]\n")
    (comp / "state.json").write_text("{}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "baseline")
    entered = tmp / "commit-entered"
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text(f"#!/bin/sh\ntouch '{entered}'\nsleep {hook_s}\n", newline="\n")
    hook.chmod(0o755)
    log: list = []
    ticket = _Ticket(tid, comp, log, threading.Lock(), refuse)
    saved = Ticket.__dict__["at"]
    Ticket.at = classmethod(lambda cls, fileref, **kw: ticket)
    try:
        yield {"repo": repo, "ticket": ticket, "log": log, "entered": entered}
    finally:
        Ticket.at = saved
        _settle()
        shutil.rmtree(tmp, ignore_errors=True)


def _settle(timeout: float = 120.0) -> None:
    """Wait until the gate's worker (if it has one) has drained, so no crossing outlives its world."""
    from cairn.devices.codemother.machines.clearance import gate as C
    end = time.monotonic() + timeout
    fifo = getattr(C, "_QUEUES", {}).get("clearance") if hasattr(C, "_QUEUES") else None
    while fifo is not None and fifo.unfinished_tasks and time.monotonic() < end:
        time.sleep(0.1)


def _wait_for(path: Path, timeout: float) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if path.exists():
            return True
        time.sleep(0.05)
    return False


def _envelope(tid: str, n: str) -> dict:
    return {"id": f"env-{tid}-{n}", "sender": n, "verb": "queueme", "body": {"fileref": tid}}


def _queue_on_a_thread(gate, envelope) -> dict:
    """``queueme`` on its own thread, so a gate that holds the call cannot hang the proof."""
    out: dict = {}

    def call():
        t0 = time.monotonic()
        out["got"] = gate.queueme(envelope)
        out["s"] = time.monotonic() - t0
    th = threading.Thread(target=call, daemon=True)
    th.start()
    out["thread"] = th
    return out


def test_a_second_ask_is_answered_while_a_crossings_commit_runs():
    """Clause 1: while a crossing's commit takes 30 s, a second ask to the clearance gate is
    answered within 5 s, through the real shim behind one lock per device."""
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import scratch_bus
    from cairn.tools.bus_client import _load_device_shim
    tid = "7c4138f700a1"
    locks: dict[str, threading.RLock] = {}

    def one_lock_per_device(device_id, hook):  # server.py _locked_hook's shape
        lock = locks.setdefault(device_id, threading.RLock())

        def locked(envelope):
            with lock:
                return hook(envelope)
        return locked

    got: dict = {}
    with _world(tid, _SLOW_S) as w, scratch_bus("t7c41_slow_commit") as bus:
        bus.set_delivery_wrapper(one_lock_per_device)
        shim = _load_device_shim("codemother", bus)
        shim._wire_delivery()
        asker = threading.Thread(target=lambda: bus.post(
            sender="proof_asker", to="codemother", channel="personal",
            verb="machines/clearance/queueme", body={"fileref": tid},
            why="7c4138f7fa33 clause 1: a crossing whose commit sleeps"), daemon=True)
        asker.start()
        assert _wait_for(w["entered"], 20.0), "the crossing's commit never started"

        def ask():
            t0 = time.monotonic()
            got["reply"] = bus.request(sender="proof_asker", to="codemother",
                                       channel="personal", verb="machines/clearance/queueme",
                                       body={"fileref": ""}, timeout=_ANSWER_S,
                                       why="7c4138f7fa33 clause 1: a second ask mid-commit")
            got["s"] = time.monotonic() - t0
        th = threading.Thread(target=ask, daemon=True)
        th.start()
        th.join(_ANSWER_S + 1)
        commit_still_running = not [e for e in w["log"] if e[0] == "out"]
        asker.join(_SLOW_S + 30)
    assert commit_still_running, "the commit ended before the second ask was measured"
    assert "reply" in got, (f"the second ask to clearance was not answered within "
                            f"{_ANSWER_S:.0f} s while a crossing's commit ran")
    assert got["s"] <= _ANSWER_S, got
    body = got["reply"].get("body") or got["reply"]
    assert body.get("accepted") is False and "fileref" in str(body.get("reason")), got["reply"]
    print(f"ok test_a_second_ask_is_answered_while_a_crossings_commit_runs ({got['s']:.2f} s)")


def test_the_asker_hears_the_crossings_answer_by_reply_to_once_the_commit_lands():
    """Clause 2: queueme lets go at once; the asker's answer (the workflow, or the refusal)
    arrives by reply_to only after the commit lands, carrying the dict queueme returned before."""
    from cairn.devices.codemother.machines.clearance.gate import ClearanceGate
    tid = "7c4138f700a2"
    spy = _Spy()
    with _world(tid, _QUICK_S) as w:
        env = _envelope(tid, "proof_asker")
        call = _queue_on_a_thread(ClearanceGate(participant=spy), env)
        call["thread"].join(_QUICK_S / 2)
        assert call.get("got", "still running") is None and call["s"] < 1.0, (
            f"queueme held the call while the crossing ran: {call.get('got', 'still running')!r}")
        assert spy.reply_to(env["id"], timeout=0.2) is None, "replied before the commit landed"
        reply = spy.reply_to(env["id"], timeout=_QUICK_S + 30)
        landed = [e for e in w["log"] if e[0] == "out"]
        head = _git(w["repo"], "log", "-1", "--format=%s")
    assert reply is not None, "the crossing posted no answer by reply_to"
    assert landed, "the crossing never ended"
    assert reply["to"] == "proof_asker", reply
    body = reply["body"]
    want = {"accepted": True, "verb": "queueme", "device": "codemother", "door": "clearance",
            "ticket": tid, "fileref": f"/scratch/{tid}.json", "target": "BUILDME",
            "proven_by": [], "asked_by": "proof_asker", "workflow": _CROSSED}
    assert body == want, body
    assert head.strip() == f"crossing records: {tid} passed into BUILDME", head

    tid = "7c4138f700a3"
    spy = _Spy()
    with _world(tid, _QUICK_S, refuse=RuntimeError("the harbor refused: no proof")):
        env = _envelope(tid, "proof_asker")
        call = _queue_on_a_thread(ClearanceGate(participant=spy), env)
        call["thread"].join(_QUICK_S / 2)
        assert call.get("got", "still running") is None, call.get("got")
        reply = spy.reply_to(env["id"], timeout=30)
    assert reply is not None, "a refused crossing left the asker unanswered"
    body = reply["body"]
    assert body.get("accepted") is False and body.get("refusal") == "RuntimeError", body
    assert body.get("reason") == "the harbor refused: no proof" and body.get("ticket") == tid, body
    print("ok test_the_asker_hears_the_crossings_answer_by_reply_to_once_the_commit_lands")


def test_two_queuemes_for_one_ticket_cross_in_the_order_sent():
    """Clause 3: two queuemes for one ticket, through two gate objects (her device builds its
    gates afresh at each lookup), cross in the order sent, the second only after the first's
    commit lands."""
    from cairn.devices.codemother.machines.clearance.gate import ClearanceGate
    tid = "7c4138f700a4"
    spy = _Spy()
    with _world(tid, _QUICK_S) as w:
        ea, eb = _envelope(tid, "first"), _envelope(tid, "second")
        ca = _queue_on_a_thread(ClearanceGate(participant=spy), ea)
        assert _wait_for(w["entered"], 20.0), "the first crossing's commit never started"
        cb = _queue_on_a_thread(ClearanceGate(participant=spy), eb)
        ra = spy.reply_to(ea["id"], timeout=_QUICK_S * 2 + 30)
        rb = spy.reply_to(eb["id"], timeout=_QUICK_S * 2 + 30)
        ca["thread"].join(_QUICK_S * 2 + 30)
        cb["thread"].join(_QUICK_S * 2 + 30)
        log = list(w["log"])
        commits = _git(w["repo"], "rev-list", "--count", "HEAD").strip()
    assert ca.get("got") is None and cb.get("got") is None, (ca.get("got"), cb.get("got"))
    assert ra and rb, (ra, rb)
    assert ra["body"].get("accepted") and rb["body"].get("accepted"), (ra, rb)
    order = [(e[0], e[1]) for e in log]
    assert order == [("in", "first"), ("out", "first"), ("in", "second"), ("out", "second")], order
    assert commits == "3", f"{commits} commits: two crossings should each have committed once"
    print("ok test_two_queuemes_for_one_ticket_cross_in_the_order_sent")


def main() -> int:
    failed = 0
    for name in PROVES["7c4138f7fa33"].values():
        try:
            globals()[name]()
        except Exception as exc:  # noqa: BLE001 — every tooth runs; each red is named
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
