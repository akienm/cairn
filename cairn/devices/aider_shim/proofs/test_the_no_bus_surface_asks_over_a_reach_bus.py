#!/usr/bin/env python3
"""Proof that aider_shim's no-bus surface asks inference_domain over a reach bus (ticket 51fa6654ed3e).

aider runs in its own venv subprocess with NO bus and NO injected door. ``interceptor.build``
with neither must, on first need, build ONE bus through ``bus_client.inference_bus`` and ask
inference_domain ``get`` (the models stack) and then ``resolve`` on it, as sender aider_shim.
Until this ticket that was measured only from the cairn bus machine's proof
(test_inference_rides_the_bus.py), which imported aider_shim's interceptor and fence: a RULE 1
reach. The tooth berths here, with its owner.

bus_client.inference_bus is a published tool; it is swapped for a recording bus, so nothing
reaches the instance's bus or the inference host.

    bin/cairn test cairn/devices/aider_shim/proofs/test_the_no_bus_surface_asks_over_a_reach_bus.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"51fa6654ed3e": {
    "1": "test_the_no_bus_surface_builds_one_reach_bus_and_asks_get_then_resolve",
    "2": "test_the_reply_on_the_bus_is_the_reply_aider_reads",
}}


class _RecordingBus:
    """Answers ``get``/``what=models`` with a declared stack and ``resolve`` with a scripted
    reply; records every request so the tooth can say which door was knocked on."""

    def __init__(self, stack: dict, model: str, provider: str):
        self.stack, self.model, self.provider = stack, model, provider
        self.seen: list[dict] = []

    def request(self, **kw):
        self.seen.append(kw)
        assert kw["to"] == "inference_domain", kw
        if kw["verb"] == "get":
            assert kw["body"] == {"what": "models"}, kw
            return {"body": {"accepted": True, "verb": "get", "view": "models",
                             "device": "inference_domain", "data": self.stack}}
        if kw["verb"] == "resolve":
            return {"body": {"answer": {"text": "pong", "role": "assistant"}, "hit": False,
                             "canonical": "c", "cost": 1,
                             "provenance": {"provider": self.provider, "domain": "coding",
                                            "model": self.model}}}
        raise AssertionError(f"unexpected verb on the bus: {kw['verb']}")


def _drive():
    """Build the surface with no bus and no door, complete one message; return what happened."""
    from cairn.tools import bus_client as bc
    from cairn.devices.aider_shim import interceptor
    from cairn.devices.aider_shim.fence import Fence, SeenLog

    fence = Fence()
    model = fence.models[0]
    # the provider must sit inside the fence, or the fence (rightly) refuses the answer
    bus = _RecordingBus({"models": [{"name": model}]}, model, list(fence.providers)[0])
    built: list[int] = []

    def _fake_inference_bus():
        built.append(1)
        return bus

    saved = bc.inference_bus
    bc.inference_bus = _fake_inference_bus
    try:
        mod = interceptor.build(fence=fence, log=SeenLog(record_path=None))
        out = mod.completion(model=model, messages=[{"role": "user", "content": "ping"}])
    finally:
        bc.inference_bus = saved
    return built, bus, model, out


def test_the_no_bus_surface_builds_one_reach_bus_and_asks_get_then_resolve():
    built, bus, model, _ = _drive()
    assert built == [1], f"the surface builds ONE reach bus on first need, saw {len(built)}"
    verbs = [r["verb"] for r in bus.seen]
    assert verbs == ["get", "resolve"], f"the no-bus surface asks the stack then resolves: {verbs}"
    assert all(r["sender"] == "aider_shim" for r in bus.seen), bus.seen
    assert bus.seen[1]["body"]["model"] == model, bus.seen[1]


def test_the_reply_on_the_bus_is_the_reply_aider_reads():
    _, _, _, out = _drive()
    assert out.choices[0].message.content == "pong", out


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
