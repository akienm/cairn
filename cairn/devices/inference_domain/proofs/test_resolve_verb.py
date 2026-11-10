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

The rig reaches the bus through bus_client and hands inference_domain's own shim a
perform-marked request (ticket 12e6ecd87700, RULE 1; the d0c8c4b4283e pattern): the caller is a
testing name, the reply rides the test's mark, and the caller takes it.

    python3 cairn/devices/inference_domain/proofs/test_resolve_verb.py   # exit 0 = green
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.inference_domain.device import InferenceDomainDevice  # noqa: E402
from cairn.devices.inference_domain.shim import InferenceDomainShim  # noqa: E402

_RUN = uuid.uuid4().hex[:8]     # names this run in message text; never a table name
_TICKET = "12e6ecd87700"        # the ticket that moved this rig onto bus_client; the perform mark's test id

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


class _TestingBus:
    """The bus, reached through bus_client, with one decline: a testing shim never asks the bus
    to hold it (the d0c8c4b4283e rig)."""

    def __init__(self, bus):
        self._bus = bus

    def wire_delivery(self, *args, **kwargs):
        return None

    def __getattr__(self, name):
        return getattr(self._bus, name)


class _Rig:
    """inference_domain's own shim on the bus, and a testing-named caller (ticket 12e6ecd87700).

    RULE 1: the bus is reached through bus_client, never by importing the cairn device's bus
    machine. A request is handed to the shim as a perform-marked envelope (d0c8c4b4283e): the
    shim runs the verb and posts the reply, carrying the mark, on the bus for the caller, who
    reads it by reply_to and takes it."""

    def __init__(self) -> None:
        from cairn.tools.bus_client import bus_client
        self.bus = _TestingBus(bus_client.reach())
        self.caller = f"testing-{_TICKET}-caller-{uuid.uuid4().hex[:8]}"
        self.shim = InferenceDomainShim(bus=self.bus)

    def ask(self, verb: str, body: dict, resolver=_fake_resolver) -> dict:
        from cairn.tools.base import testing_mark
        envelope_id = f"testing-{_TICKET}-{uuid.uuid4().hex}"
        with patch("cairn.devices.inference_domain.host.ollama_resolver",
                   return_value=resolver):
            self.shim.deliver({
                "id": envelope_id, "sender": self.caller, "addressee": "inference_domain",
                "channel": "personal", "verb": verb,
                "body": {**body, testing_mark.FIELD: testing_mark.mark(_TICKET, testing_mark.PERFORM)}})
        replies = [e for e in self.bus.read(to=self.caller, channel="personal")
                   if e.get("reply_to") == envelope_id]
        assert len(replies) == 1, f"{len(replies)} replies to {verb!r} on the bus, want 1"
        self.bus.record_delivery(replies[0]["id"], to=self.caller, by=self.caller)
        return replies[0]


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
    rig = _Rig()
    reply = rig.ask("resolve", {"kind": "embed", "prompt": "test text", "model": "nomic-embed-text"})
    assert reply["body"]["answer"]["vector"] == FAKE_VECTOR, reply["body"]
    assert "hit" in reply["body"], "result must carry hit flag"


def test_reply_lands_in_ring():
    """The reply is posted back to the sender with reply_to set."""
    rig = _Rig()
    reply = rig.ask("resolve", {"kind": "embed", "prompt": "test", "model": "nomic-embed-text"})
    assert reply["sender"] == "inference_domain"
    assert reply["addressee"] == rig.caller
    assert reply["reply_to"] is not None, "reply must carry reply_to"


def test_generate_kind():
    """The resolve verb handles 'generate' kind requests."""
    rig = _Rig()
    reply = rig.ask("resolve", {"kind": "generate", "prompt": "say hello", "model": "qwen2.5:7b"})
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
    rig = _Rig()
    rig.ask("resolve", {"kind": "embed", "prompt": "test", "model": "nomic-embed-text"})
    # the yield is the cairn device's metrics totals (ticket 98ab0e9db57f); a fake reply keeps
    # this tooth on the get verb's wiring, off the live bus
    fake = {"totals": [{"name": "inference.spent", "by": "miss", "count": 1, "sum": 3.0},
                       {"name": "inference.latency", "by": "miss", "count": 1, "sum": 0.1}]}
    with patch("cairn.devices.inference_domain.domain._ask_metrics", return_value=fake):
        reply = rig.ask("get", {"what": "yield"})
    data = reply["body"]["data"]
    assert data.get("spent") == 3.0 and data.get("misses") == 1, f"yield view must read the totals, got {data}"
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

    turns = [{"role": "user", "content": f"what time is it? {_RUN}"},
             {"role": "assistant", "content": "",
              "tool_calls": [{"function": {"name": "clock", "arguments": {}}}]},
             {"role": "tool", "content": "12:00"}]
    toolset = [{"type": "function",
                "function": {"name": "clock", "description": "the time",
                             "parameters": {"type": "object", "properties": {}}}}]

    rig = _Rig()
    rig.ask("resolve", {"kind": "chat", "messages": turns, "model": "qwen2.5:7b",
                        "tools": toolset}, _capturing)
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
    rig.ask("resolve", {"kind": "chat",
                        "messages": [{"role": "user", "content": f"plain {_RUN}"}],
                        "model": "qwen2.5:7b"}, _capturing)
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
    # The device's trail and task tickets (ticket ea4a6151300f) ride the roots: moved into a
    # fixture world for the run so a bus proof leaves nothing in the live tickets folder.
    from cairn.devices.inference_domain import domain as _domain
    from cairn.tools.scratch.scratch import scratch_dir
    from cairn.tools.base import address as _address
    _domain.set_diagnostic_roots({**_address.ROOTS, "instance": scratch_dir("cairn_resolve_verb_")})
    try:
        for check in checks:
            try:
                check()
                print(f"  PASS  {check.__name__}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
    finally:
        _domain.set_diagnostic_roots(None)
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — inference_domain answers on the bus, zero cross-device imports needed")
