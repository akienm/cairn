"""Proof for ticket bc0bbfd33a71 "a non-home box cannot drive the ticket machine": a client whose home is
another box's bus reaches a device without asking for hold.

MEASURED 2026-11-12 on akienasus, CAIRN_BUS_HOME=akiendelllinux.local:7419, running
`sail.py chart 1029d5146152`:
    RuntimeError: bus process: 'hold' is not open across the LAN — one of ('call', 'stats', 'verbs')
reach(HOLDER) goes through _wire, and _wire calls bus.hold(*devices). The LAN door answers only
LAN_OPS (cairn/devices/cairn/machines/bus/server.py, ticket 5183005fa134). Holding is not needed
across the LAN: mail to a device no hook answers takes the home bus's no_receiver, which wakes
the addressee's shim with hold_name(wire=True) (ticket 7cb1989e7825).

  1. test_a_far_reach_sends_only_lan_ops: with a remote home, reach("codemother") sends only
     ops the LAN door answers, and no hold;
  2. test_a_local_reach_still_holds: with a home on this box, reach("codemother") still sends
     hold naming the device, as before;
  3. test_a_far_request_goes_over_call: a request through a far reach is sent as op 'call',
     method 'request'.

The wire is replaced for the call: remote.exchange records each request and answers it, so
nothing dials. LAN_OPS is restated here, not imported (RULE 1: this proof measures only
bus_client).

    bin/cairn test cairn/tools/bus_client/proofs/test_a_far_client_reaches_without_hold.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"bc0bbfd33a71": {
    "1": "test_a_far_reach_sends_only_lan_ops",
    "2": "test_a_local_reach_still_holds",
    "3": "test_a_far_request_goes_over_call",
}}

_LAN_OPS = ("call", "stats", "verbs")   # server.py LAN_OPS, restated (RULE 1)
_FAR = "far-box.invalid:7419"


def _sent(home: str, act) -> list[dict]:
    """Run ``act(reach)`` with CAIRN_BUS_HOME=home and the wire replaced; the requests sent."""
    from cairn.tools import bus_client
    from cairn.tools.bus_client import remote
    sent: list[dict] = []

    def exchange(req, h=None, timeout=None):
        sent.append(dict(req))
        if req.get("op") == "stats":
            return {"ok": True, "json": {"pid": 1}}
        if req.get("op") == "hold":
            return {"ok": True, "held": list(req.get("devices") or [])}
        return {"ok": True, "json": {"answered": True}}

    saved_env = os.environ.get("CAIRN_BUS_HOME")
    saved = remote.exchange
    os.environ["CAIRN_BUS_HOME"] = home
    remote.exchange = exchange
    try:
        act(bus_client.reach)
    finally:
        remote.exchange = saved
        if saved_env is None:
            os.environ.pop("CAIRN_BUS_HOME", None)
        else:
            os.environ["CAIRN_BUS_HOME"] = saved_env
    return sent


def _local_home() -> str:
    from cairn.tools.scratch.scratch import scratch_dir
    return str(scratch_dir("testing-far-reach-local-"))


def test_a_far_reach_sends_only_lan_ops():
    sent = _sent(_FAR, lambda reach: reach("codemother"))
    ops = [r.get("op") for r in sent]
    assert "hold" not in ops, f"a far reach asked for hold, which the LAN door refuses: {sent!r}"
    assert all(op in _LAN_OPS for op in ops), f"a far reach sent ops outside LAN_OPS: {ops!r}"


def test_a_local_reach_still_holds():
    sent = _sent(_local_home(), lambda reach: reach("codemother"))
    holds = [r for r in sent if r.get("op") == "hold"]
    assert len(holds) == 1 and holds[0].get("devices") == ["codemother"], (
        f"a local reach must hold the device it names, once: {sent!r}")


def test_a_far_request_goes_over_call():
    sent = _sent(_FAR, lambda reach: reach("codemother").request(
        sender="cc", to="codemother", verb="show", body={}))
    calls = [r for r in sent if r.get("op") == "call" and r.get("method") == "request"]
    assert len(calls) == 1, f"a far request must go as one call/request: {sent!r}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
