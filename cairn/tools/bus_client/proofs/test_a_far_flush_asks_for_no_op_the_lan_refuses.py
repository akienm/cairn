"""Proof for ticket 3195b3b834bc "a far bus handle's flush answers without asking the LAN door for an
op it refuses".

MEASURED 2026-11-12 on akienasus, CAIRN_BUS_HOME on akiendelllinux: every `bin/cairn test --seal`
printed "'flush' is not open across the LAN" and "the crossings they would have fired did not",
yet all 12 tester->codemother sealed posts were in her channel and her sealed replies came back
accepted:true. A far post rides op call and her hook runs in the far bus process; the trailing
flush is an op the LAN door refuses by design (LAN_OPS, ticket 5183005fa134: the ring is its own
box's process to flush, Law 6), and that refusal alone made the tester report a failure that did
not happen. The ring a far handle posted into lives in a process that outlives this one, so there
is nothing here to flush.

  1. test_a_far_flush_sends_nothing: with a far home, flush() sends no request and answers
     flushed 0, far naming host:port, and a why;
  2. test_a_far_post_then_flush_sends_only_lan_ops: post then flush, far, sends only LAN ops;
  3. test_a_local_flush_still_sends_flush: with a home on this box, flush() sends one op flush.

The wire is replaced for the call: remote.exchange records each request and answers it, so
nothing dials. LAN_OPS is restated here, not imported (RULE 1: this proof measures only
bus_client).

    bin/cairn test cairn/tools/bus_client/proofs/test_a_far_flush_asks_for_no_op_the_lan_refuses.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"3195b3b834bc": {
    "1": "test_a_far_flush_sends_nothing",
    "2": "test_a_far_post_then_flush_sends_only_lan_ops",
    "3": "test_a_local_flush_still_sends_flush",
}}

_LAN_OPS = ("call", "stats", "verbs")   # server.py LAN_OPS, restated (RULE 1)
_FAR = "far-box.invalid:7419"


def _run(home: str, act):
    """Run ``act(RemoteBus(home))`` with the wire replaced; ``(requests sent, act's result)``."""
    from cairn.tools.bus_client import remote
    sent: list[dict] = []

    def exchange(req, h=None, timeout=None):
        sent.append(dict(req))
        op = req.get("op")
        if remote.remote_address(h) is not None and op not in _LAN_OPS:
            return {"ok": False, "error": f"{op!r} is not open across the LAN — one of {_LAN_OPS}"}
        if op == "flush":
            return {"ok": True, "json": {"flushed": 1, "receipts": 0}}
        return {"ok": True, "json": {"answered": True}}

    saved_env = os.environ.get("CAIRN_BUS_HOME")
    saved = remote.exchange
    os.environ["CAIRN_BUS_HOME"] = home
    remote.exchange = exchange
    try:
        result = act(remote.RemoteBus(home))
    finally:
        remote.exchange = saved
        if saved_env is None:
            os.environ.pop("CAIRN_BUS_HOME", None)
        else:
            os.environ["CAIRN_BUS_HOME"] = saved_env
    return sent, result


def _local_home() -> str:
    from cairn.tools.scratch.scratch import scratch_dir
    return str(scratch_dir("testing-far-flush-local-"))


def test_a_far_flush_sends_nothing():
    sent, got = _run(_FAR, lambda bus: bus.flush())
    assert sent == [], f"a far flush sent requests the far box owns: {sent!r}"
    assert isinstance(got, dict) and got.get("flushed") == 0, f"a far flush must answer flushed 0: {got!r}"
    assert got.get("far") == _FAR, f"a far flush must name the box whose process holds the ring: {got!r}"
    assert str(got.get("why") or "").strip(), f"a far flush must say why nothing was flushed: {got!r}"


def test_a_far_post_then_flush_sends_only_lan_ops():
    def act(bus):
        bus.post(sender="testing-3195", to="codemother", channel="personal", verb="sealed",
                 why="testing: 3195b3b834bc far post then flush", body={})
        return bus.flush()
    sent, _ = _run(_FAR, act)
    ops = [r.get("op") for r in sent]
    assert ops and all(op in _LAN_OPS for op in ops), f"a far post+flush sent ops outside LAN_OPS: {ops!r}"


def test_a_local_flush_still_sends_flush():
    sent, got = _run(_local_home(), lambda bus: bus.flush())
    flushes = [r for r in sent if r.get("op") == "flush"]
    assert len(flushes) == 1, f"a local flush must send op flush once: {sent!r}"
    assert got == {"flushed": 1, "receipts": 0}, f"a local flush must return the bus's answer: {got!r}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
