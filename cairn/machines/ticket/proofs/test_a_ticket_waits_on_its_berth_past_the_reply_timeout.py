"""Proof for ticket 0bcb816d6e9c — a ticket waits on its own berth past a stage's reply timeout.

After e4714e460e32 a deferred chart gate queues the ticket at once and answers by ``reply_to``
when the stage ends, so a stage slower than its asker's timeout replies after the asker gave up.
Measured 2026-11-12: b0e65cf8a77e's constrain ran 1858 s, against live.py queue's 120 s and
sail.py chart's and verdict's 890 s. Each asker raised ``ticket-unqueued`` while the gate still
berthed the stage. Outline 3.3.4.3 has the ticket's life as data on disk, so the asker now reads
its own record (the berth the gate writes, or the refusal it raises) up to the stage's budget.

The world. A scratch tickets store (the live store charter copied in, one fixture plan and
state), ``ticket_file._TICKETS`` pointed at it, and every ``Ticket.at`` given the scratch roots,
so each trouble lands and is read in the scratch tree, never in ~/.cairn. The gate is a
participant whose ``request`` waits out its timeout and raises TimeoutError for the slow stage,
while a thread acting as the gate writes the berth (``Ticket.berthed``) or the refusal
(``Ticket.failed``) on a ticket instance of its own, only after the timeout has fired. The
reply timeouts are patched to 0.3 s and ``STAGE_BUDGET_S`` to 5 s; nothing else is patched.
One tooth per asker; tooth 1 also carries the refusal.

    bin/cairn test cairn/machines/ticket/proofs/test_a_ticket_waits_on_its_berth_past_the_reply_timeout.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "0bcb816d6e9c": {
        "1": "test_live_queue_reads_the_berth_that_lands_after_the_timeout",
        "2": "test_sail_chart_goes_on_to_survey_after_a_slow_constrain",
        "3": "test_sail_verdict_reads_the_berth_that_lands_after_the_timeout",
    },
}

_TID = "fixture0bcb1"
_REPLY_S = 0.3   # every asker's reply timeout, patched down
_BUDGET_S = 5.0  # STAGE_BUDGET_S, patched down
_LATE_S = 0.4    # the gate writes this long after the asker's timeout fired
_WF = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
_SAIL = _REPO_ROOT / "cairn" / "devices" / "cc" / "scripts" / "sail.py"
_LIVE_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"


@contextmanager
def _world():
    """The scratch store and roots; ``Ticket.at`` pinned to the roots and ``STAGE_BUDGET_S``
    patched, each restored on exit."""
    import cairn.machines.ticket.ticket as T
    import cairn.tools.base.ticket_file as tf
    tmp = scratch_dir("t0bcb-berth-")
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
    saved_at, saved_tickets = T.Ticket.__dict__["at"], tf._TICKETS
    had_budget, budget = hasattr(T, "STAGE_BUDGET_S"), getattr(T, "STAGE_BUDGET_S", None)
    orig_at = saved_at.__func__

    def pinned(cls, ref, **kw):
        kw["roots"] = roots
        kw.setdefault("tickets_dir", store)
        return orig_at(cls, ref, **kw)
    T.Ticket.at = classmethod(pinned)
    T.STAGE_BUDGET_S = _BUDGET_S
    tf._TICKETS = store
    try:
        yield {"tmp": tmp, "store": store, "plan": plan, "roots": roots}
    finally:
        T.Ticket.at, tf._TICKETS = saved_at, saved_tickets
        if had_budget:
            T.STAGE_BUDGET_S = budget
        else:
            del T.STAGE_BUDGET_S
        shutil.rmtree(tmp, ignore_errors=True)


def _gate_side():
    """The ticket as the gate instantiates it on its own side."""
    from cairn.machines.ticket.ticket import Ticket
    return Ticket.at(_TID)


class _SlowGate:
    """A participant standing in for codemother. ``slow`` is the stage whose reply never comes
    inside the asker's timeout: its ``request`` waits the timeout out and raises TimeoutError,
    and a thread writes ``late(stage)`` on the gate's own ticket ``_LATE_S`` after that. Every
    other stage is answered at once, passed, with a berth the gate also records."""

    def __init__(self, slow: str, late) -> None:
        self.slow, self._late = slow, late
        self.asked: list[str] = []
        self.timeouts: list[float] = []
        self._threads: list[threading.Thread] = []

    def request(self, *, to, verb="", body=None, timeout=30.0, **kw):
        stage = verb.split("/")[1]
        self.asked.append(stage)
        self.timeouts.append(timeout)
        if stage != self.slow:
            berth = f"/scratch/berths/{stage}-{_TID}.json"
            _gate_side().berthed(stage, berth, why=f"proof gate berths {stage}")
            return {"body": {"accepted": True, "passed": True, "berth": berth, "stage": stage,
                             "ticket": _TID}}
        fired = threading.Event()

        def gate():
            fired.wait(10)
            time.sleep(_LATE_S)
            self._late(stage)
        th = threading.Thread(target=gate, daemon=True)
        th.start()
        self._threads.append(th)
        time.sleep(timeout)
        fired.set()
        raise TimeoutError(f"no reply to {verb} within {timeout} s")

    def post(self, **kw):
        return {"id": "post"}

    def join(self) -> None:
        for th in self._threads:
            th.join(10)


def _berth_late(path: str):
    def late(stage):
        _gate_side().berthed(stage, path, why=f"proof gate berths {stage} after the timeout")
    return late


def _refuse_late(why: str):
    def late(stage):
        w = _gate_side()
        w.failed([{"kind": "bounds", "why": why}], participant=_SlowGate("", None),
                 history_path=None, state_path=None, actor="codemother",
                 why=f"proof gate refuses {stage} after the timeout", gate=stage)
    return late


def _unqueued(stage: str) -> bool:
    return _gate_side()._stands_raised(f"ticket-unqueued-{_TID}-at-{stage}")


def _live():
    import skills.chart.live as live
    return live


def _sail():
    spec = importlib.util.spec_from_file_location("cc_sail_0bcb_proof", _SAIL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_live(gate) -> tuple[int, str, str]:
    live = _live()
    saved = (live._gates, live._GATE_TIMEOUT_S)
    live._gates, live._GATE_TIMEOUT_S = (lambda: gate), _REPLY_S
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = live._queue([_TID, "constrain"])
    finally:
        live._gates, live._GATE_TIMEOUT_S = saved
        gate.join()
    return rc, out.getvalue(), err.getvalue()


def test_live_queue_reads_the_berth_that_lands_after_the_timeout():
    berth = f"/scratch/berths/constrain-{_TID}-late.json"
    with _world():
        gate = _SlowGate("constrain", _berth_late(berth))
        rc, out, err = _run_live(gate)
        assert gate.timeouts == [_REPLY_S], f"the reply was waited on for {gate.timeouts}"
        assert _gate_side().berth("constrain") == berth, "the gate's late berth never landed"
        assert rc == 0 and f"constrain: {berth}" in out, (
            f"constrain berthed {berth} {_LATE_S} s after the {_REPLY_S} s reply timeout, and "
            f"live queue said rc={rc} out={out!r} err={err!r}")
        assert not _unqueued("constrain"), "ticket-unqueued raised though the gate berthed it"
    with _world():
        why = "no bounds named in the constrain draft"
        gate = _SlowGate("constrain", _refuse_late(why))
        rc, out, err = _run_live(gate)
        assert rc == 1 and why in err, (rc, out, err)
        assert not _unqueued("constrain"), "ticket-unqueued raised though the gate refused it"
    print("ok test_live_queue_reads_the_berth_that_lands_after_the_timeout")


def test_sail_chart_goes_on_to_survey_after_a_slow_constrain():
    from cairn.machines.ticket.ticket import CHART
    berth = f"/scratch/berths/constrain-{_TID}-late.json"
    with _world() as w:
        sail = _sail()
        sail.CHART_TIMEOUT_S = _REPLY_S
        gate = _SlowGate("constrain", _berth_late(berth))
        out, err = [], []
        try:
            rc = sail.chart(_TID, participant=gate, tickets_dir=w["store"], out=out.append,
                            err=err.append)
        finally:
            gate.join()
        assert _gate_side().berth("constrain") == berth, "the gate's late berth never landed"
        assert gate.asked == list(CHART), (
            f"constrain berthed {berth} {_LATE_S} s after the {_REPLY_S} s reply timeout, and "
            f"the chart asked only {gate.asked}: {err}")
        assert rc == 0 and f"constrain: {berth}" in out, (rc, out, err)
        assert _gate_side().berth("validate") == f"/scratch/berths/validate-{_TID}.json"
        assert not _unqueued("constrain"), "ticket-unqueued raised though constrain berthed"
    print("ok test_sail_chart_goes_on_to_survey_after_a_slow_constrain")


def test_sail_verdict_reads_the_berth_that_lands_after_the_timeout():
    berth = f"/scratch/berths/verdict-{_TID}-late.json"
    with _world() as w:
        validate = w["tmp"] / "validate.json"
        validate.write_text(json.dumps({"criteria": [
            {"claim": "the fixture holds", "instrument": "true"}]}) + "\n")
        _gate_side().berthed("validate", str(validate), why="proof: the chart's validate berth")
        sail = _sail()
        sail.VERDICT_TIMEOUT_S = _REPLY_S
        gate = _SlowGate("verdict", _berth_late(berth))
        out, err = [], []
        try:
            rc = sail.verdict(_TID, "the fixture instrument can fail", participant=gate,
                              tickets_dir=w["store"], out=out.append, err=err.append)
        finally:
            gate.join()
        assert _gate_side().berth("verdict") == berth, "the gate's late berth never landed"
        assert rc == 0 and out == [berth], (
            f"the verdict berthed {berth} {_LATE_S} s after the {_REPLY_S} s reply timeout, and "
            f"sail verdict said rc={rc} out={out} err={err}")
        assert not _unqueued("verdict"), "ticket-unqueued raised though the verdict berthed"
    print("ok test_sail_verdict_reads_the_berth_that_lands_after_the_timeout")


def main() -> int:
    failed = 0
    for name in PROVES["0bcb816d6e9c"].values():
        try:
            globals()[name]()
        except Exception as exc:  # noqa: BLE001 — every tooth runs; each red is named
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
