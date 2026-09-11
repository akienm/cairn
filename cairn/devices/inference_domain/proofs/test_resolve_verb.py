"""PROOF — the resolve verb: inference_domain answers on the bus.

The resolve verb is the bus-addressable face of domain.resolve. A caller posts
a request (kind, prompt, model), the handler builds the resolver, runs the domain
workflow, and posts the result back. The bus is the sole path for inter-device
inference (ticket 87a7f1c7ae21).

What a hollow build cannot pass (Law 8):
  - A device that declares no verbs passes shape tests and fails
    test_resolve_verb_is_declared — the verb must be in declared_verbs().
  - A handler that ignores the request and returns a canned answer passes
    declaration tests and fails test_resolve_returns_real_result — the result
    must carry the answer from the (injected) resolver.
  - A handler that resolves but never posts a reply passes resolve tests and fails
    test_reply_lands_in_ring — the reply must be in the bus ring with reply_to set.

Requires Postgres (domain.resolve writes to the cache). Self-cleaning.

    python3 cairn/devices/inference_domain/proofs/test_resolve_verb.py   # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.shim import BaseShim, ONLINE  # noqa: E402
from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.shim import BusShim  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402
from cairn.devices.inference_domain.device import InferenceDomainDevice  # noqa: E402
from cairn.devices.inference_domain.shim import InferenceDomainShim  # noqa: E402
from cairn.devices.db_domain import store  # noqa: E402

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLES: list[str] = []
NOW = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)

FAKE_VECTOR = [0.1, 0.2, 0.3]


def _fake_resolver(request):
    """A resolver that returns a canned answer — no host needed."""
    kind = request.get("kind", "")
    if kind == "embed":
        return {"answer": {"vector": FAKE_VECTOR, "dim": len(FAKE_VECTOR)},
                "cost": 10, "falsifier": "test", "horizon": "", "provenance": {}}
    if kind == "generate":
        return {"answer": {"text": "hello from the fake host"},
                "cost": 20, "falsifier": "test", "horizon": "", "provenance": {}}
    raise ValueError(f"unknown kind {kind!r}")


class CallerShim(BaseShim):
    def __init__(self, bus=None):
        super().__init__(bus=bus)
        self._presence = ONLINE

    @property
    def device_id(self):
        return "caller"

    def _start_device(self):
        dev = BaseDevice.__new__(BaseDevice)
        dev.__dict__["_device_id"] = "caller"
        dev.intention = lambda: {"what": "proof caller"}
        dev.state = lambda: {}
        dev.settings = lambda: {}
        dev.device_id = property(lambda s: "caller")
        return dev


def _fresh_bus():
    bus = BusDevice(table=f"_bus_resolve_{_NONCE}_{len(_TABLES)}")
    _TABLES.append(bus.table)
    return bus


def _rig_with_inference(bus):
    loop = GroundLoopDevice(bus=bus)
    bus_shim = BusShim(bus, loop)
    inf_shim = InferenceDomainShim(bus=bus)
    caller_shim = CallerShim(bus=bus)
    loop.subscribe(bus_shim)
    loop.subscribe(inf_shim)
    loop.subscribe(caller_shim)
    loop.beat(NOW)
    return loop


# --- teeth ------------------------------------------------------------------

# WHICH CLAUSE OF 548dd13fb4db'S FALSIFIER THIS PROOF COVERS. The ticket's clause (a) is about
# THE ONE INFERENCE DOOR carrying a tool-using conversation — and for every other device the one
# door is this verb, not the Python call. test_host.py proves the host end; this proves the bus
# end, and they are not the same seam: the verb copies the body key by key into the request, so a
# toolset can cross the host boundary perfectly and still never reach it.
PROVES = {"548dd13fb4db": {"a": "test_a_toolset_survives_the_bus_verb"}}


def test_resolve_verb_is_declared():
    """The inference_domain device declares a 'resolve' verb."""
    dev = InferenceDomainDevice()
    verbs = dev.declared_verbs()
    assert "resolve" in verbs, f"no resolve verb, available: {sorted(verbs)}"
    assert callable(verbs["resolve"])


def test_resolve_verb_includes_base_verbs():
    """The device extends, not replaces, base verbs."""
    dev = InferenceDomainDevice()
    verbs = dev.declared_verbs()
    assert "show" in verbs, "missing base verb: show"
    assert "get" in verbs, "missing base verb: get"


def test_resolve_returns_real_result():
    """The resolve verb calls domain.resolve with the body's request and returns the answer."""
    bus = _fresh_bus()
    _rig_with_inference(bus)
    with patch("cairn.devices.inference_domain.host.ollama_resolver",
               return_value=_fake_resolver):
        reply = bus.request(
            sender="caller", to="inference_domain", channel="personal",
            verb="resolve", why="proof: embed test",
            body={"kind": "embed", "prompt": "test text", "model": "nomic-embed-text"},
        )
    assert reply["body"]["answer"]["vector"] == FAKE_VECTOR, reply["body"]
    assert "hit" in reply["body"], "result must carry hit flag"


def test_reply_lands_in_ring():
    """The reply is posted back to the sender with reply_to set."""
    bus = _fresh_bus()
    _rig_with_inference(bus)
    with patch("cairn.devices.inference_domain.host.ollama_resolver",
               return_value=_fake_resolver):
        reply = bus.request(
            sender="caller", to="inference_domain", channel="personal",
            verb="resolve", why="proof: reply check",
            body={"kind": "embed", "prompt": "test", "model": "nomic-embed-text"},
        )
    assert reply["sender"] == "inference_domain"
    assert reply["addressee"] == "caller"
    assert reply["reply_to"] is not None, "reply must carry reply_to"


def test_generate_kind():
    """The resolve verb handles 'generate' kind requests."""
    bus = _fresh_bus()
    _rig_with_inference(bus)
    with patch("cairn.devices.inference_domain.host.ollama_resolver",
               return_value=_fake_resolver):
        reply = bus.request(
            sender="caller", to="inference_domain", channel="personal",
            verb="resolve", why="proof: generate test",
            body={"kind": "generate", "prompt": "say hello", "model": "qwen2.5:7b"},
        )
    assert reply["body"]["answer"]["text"] == "hello from the fake host"


def test_device_is_bus_unaware():
    """The device returns the result; the shim posts it. No bus on the device."""
    dev = InferenceDomainDevice()
    assert not hasattr(dev, "_bus"), "device must not hold a bus reference"
    with patch("cairn.devices.inference_domain.host.ollama_resolver",
               return_value=_fake_resolver):
        result = dev._handle_resolve({
            "id": "test", "sender": "cli", "to": "inference_domain",
            "verb": "resolve",
            "body": {"kind": "embed", "prompt": "test", "model": "nomic-embed-text"},
        })
    assert "answer" in result, "handler returns the domain.resolve result directly"
    assert "vector" in result["answer"], f"result must carry vector, got {sorted(result['answer'])}"


def test_yield_view_via_get_verb():
    """The yield view is reachable through the base get verb on the bus."""
    bus = _fresh_bus()
    _rig_with_inference(bus)
    with patch("cairn.devices.inference_domain.host.ollama_resolver",
               return_value=_fake_resolver):
        bus.request(
            sender="caller", to="inference_domain", channel="personal",
            verb="resolve", why="proof: warm the cache",
            body={"kind": "embed", "prompt": "test", "model": "nomic-embed-text"},
        )
    reply = bus.request(
        sender="caller", to="inference_domain", channel="personal",
        verb="get", why="proof: yield view",
        body={"what": "yield"},
    )
    data = reply["body"]["data"]
    assert "spent" in data, f"yield view must report spent, got {sorted(data)}"
    assert "avoided" in data, f"yield view must report avoided, got {sorted(data)}"


def test_a_toolset_survives_the_bus_verb():
    """A `tools` list posted over the bus REACHES the resolver — it is not dropped in the copy.

    THE HOLLOW SHAPE THIS BITES, and it was the live one when this tooth was written: the
    handler builds its request with a whitelist of body keys, so a caller posting a toolset
    over the bus got a perfectly ordinary toolless answer and NO error anywhere. Every seam
    below this one carried the toolset correctly — host.py sends `tools` on /api/chat,
    canonicalize() digests it, the cache forks on it — and none of that is reachable from the
    bus if the key never makes it into the request. A silent drop at a door is the reading
    Law 7 forbids: the answer is coherent, it is simply an answer to a different question.

    The control is the whole tooth: asserting the key is present would pass on a handler that
    forwarded the whole body unfiltered, so the toolless call must come back WITHOUT the key —
    the whitelist is doing its job in both directions or neither.
    """
    seen = []

    def _capturing(request):
        seen.append(dict(request))
        return {"answer": {"text": "ack", "role": "assistant"},
                "cost": 1, "falsifier": "test", "horizon": "", "provenance": {}}

    turns = [{"role": "user", "content": f"what time is it? {_NONCE}"},
             {"role": "assistant", "content": "",
              "tool_calls": [{"function": {"name": "clock", "arguments": {}}}]},
             {"role": "tool", "content": "12:00"}]
    toolset = [{"type": "function",
                "function": {"name": "clock", "description": "the time",
                             "parameters": {"type": "object", "properties": {}}}}]

    bus = _fresh_bus()
    _rig_with_inference(bus)
    with patch("cairn.devices.inference_domain.host.ollama_resolver",
               return_value=_capturing):
        bus.request(sender="caller", to="inference_domain", channel="personal",
                    verb="resolve", why="proof: a toolset crosses the bus",
                    body={"kind": "chat", "messages": turns, "model": "qwen2.5:7b",
                          "tools": toolset})
    assert seen, "the resolver was never called — the request never reached the domain"
    assert seen[-1].get("tools") == toolset, (
        "the bus verb DROPPED the toolset: the resolver saw "
        f"{sorted(seen[-1])} — a caller asking a tool-using question over the one door got "
        "a toolless answer with no error anywhere")
    assert seen[-1].get("messages") == turns, \
        "the agent-shaped turns must cross unchanged too — an assistant turn with empty " \
        "content and present tool_calls, and a tool-result turn"

    # THE CONTROL: no toolset in, no toolset key out. Without this the assertion above is
    # satisfied by a handler that copies the body wholesale, which is a different design.
    seen.clear()
    with patch("cairn.devices.inference_domain.host.ollama_resolver",
               return_value=_capturing):
        bus.request(sender="caller", to="inference_domain", channel="personal",
                    verb="resolve", why="proof: a toolless chat carries no toolset",
                    body={"kind": "chat",
                          "messages": [{"role": "user", "content": f"plain {_NONCE}"}],
                          "model": "qwen2.5:7b"})
    assert seen and "tools" not in seen[-1], \
        "a toolless chat must carry no `tools` key at all — an always-present key forks the " \
        "cache for every caller who never asked for one"


if __name__ == "__main__":
    checks = [
        test_resolve_verb_is_declared,
        test_resolve_verb_includes_base_verbs,
        test_resolve_returns_real_result,
        test_reply_lands_in_ring,
        test_generate_kind,
        test_device_is_bus_unaware,
        test_yield_view_via_get_verb,
        test_a_toolset_survives_the_bus_verb,
    ]
    failures = 0
    try:
        for check in checks:
            try:
                check()
                print(f"  PASS  {check.__name__}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
    finally:
        try:
            conn = store.connect()
            with conn.cursor() as cur:
                for base in _TABLES:
                    for table in (f"{base}_delivery", base):
                        cur.execute(f'DROP TABLE IF EXISTS "{table}"')
                        cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s',
                                    (table,))
            conn.close()
        except Exception as exc:  # noqa: BLE001
            print(f"  (cleanup refused: {type(exc).__name__}: {exc})")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — inference_domain answers on the bus, zero cross-device imports needed")
