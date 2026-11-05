"""PROOF — a device asking over the bus gets an inference answer (ticket 87a7f1c7ae21).

The chart's second criterion (validate-20260906T111940-63fc41318d0d): a device that asks
``infer`` and then ``embed`` over the bus gets an inference answer, with a STUB resolver so
no host is dialed. The two verbs are ``resolve`` with the kind fixed — a caller asks for a
completion or a vector by name and never needs the domain's request vocabulary, or its
module, to ask. This proof is the bus end of that promise; the sole-path half (nobody
outside the owner imports it) is test_inference_rides_the_bus beside the bus machine.

What a hollow build cannot pass (Law 8):
  - a device that drops ``embed``/``infer`` from declared_verbs() fails the declaration tooth;
  - a verb that does not fix the kind fails the kind teeth — the stub resolver answers by
    kind and the answer shape (``text`` vs ``vector``) is asserted per verb;
  - a verb that ignores the caller's body fails the prompt tooth — the stub records the
    request it was handed and the prompt must be the one posted.

Requires Postgres (domain.resolve writes to the cache). Self-cleaning.

    python3 cairn/devices/inference_domain/proofs/test_bus_infer.py   # exit 0 = green
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# THE SUBJECT IS BOUND AT CALL TIME, never at import (ticket 87a7f1c7ae21's FIXME 1-2): the
# bus, the roster and the domain all import cairn.tools.bus_client, whose package __init__
# names inference_bus — the name this build ADDED. A hollow reading that takes the build's
# hunks out of bus_client.py breaks that import, and bound here it crashed the file before
# the first tooth (UNREAD). Bound in the teeth, each tooth FAILS by name instead.


#
# THE BUS IS REACHED THROUGH bus_client (ticket 12e6ecd87700, RULE 1): never by importing the
# cairn device's bus machine. A request is handed to inference_domain's own shim as a
# perform-marked envelope (the d0c8c4b4283e pattern); the shim runs the verb and posts the
# reply, carrying the mark, on the bus for a testing-named caller, who reads it and takes it.


def _subject():
    from cairn.tools.bus_client import bus_client
    from cairn.devices.inference_domain.device import InferenceDomainDevice
    from cairn.devices.inference_domain.shim import InferenceDomainShim
    return bus_client, InferenceDomainDevice, InferenceDomainShim

_RUN = uuid.uuid4().hex[:8]     # names this run in message text; never a table name
_TICKET = "12e6ecd87700"        # the perform mark's test id
FAKE_VECTOR = [0.5, 0.25, 0.125]
SEEN: list[dict] = []

PROVES = {
    # A device asks infer then embed over the bus and gets an answer, kind fixed by the verb.
    "87a7f1c7ae21": {
        "all": "test_infer_over_the_bus_answers_a_completion",
    },
}


def _stub_resolver(request):
    """Answers by kind and records what it was asked — no host anywhere near it."""
    SEEN.append(dict(request))
    kind = request.get("kind", "")
    if kind == "embed":
        return {"answer": {"vector": FAKE_VECTOR, "dim": len(FAKE_VECTOR)},
                "cost": 1, "falsifier": "proof", "horizon": "", "provenance": {}}
    if kind == "generate":
        return {"answer": {"text": f"stub says: {request.get('prompt', '')}"},
                "cost": 1, "falsifier": "proof", "horizon": "", "provenance": {}}
    raise ValueError(f"unknown kind {kind!r}")


class _TestingBus:
    """The bus with one decline: a testing shim never asks the bus to hold it."""

    def __init__(self, bus):
        self._bus = bus

    def wire_delivery(self, *args, **kwargs):
        return None

    def __getattr__(self, name):
        return getattr(self._bus, name)


def _fresh_bus():
    """inference_domain's own shim on the bus and a fresh testing-named caller."""
    bus_client, _, InferenceDomainShim = _subject()
    bus = _TestingBus(bus_client.reach())
    caller = f"testing-{_TICKET}-caller-{uuid.uuid4().hex[:8]}"
    return {"bus": bus, "caller": caller, "shim": InferenceDomainShim(bus=bus)}


def _ask(rig, verb, body):
    from cairn.tools.base import testing_mark
    envelope_id = f"testing-{_TICKET}-{uuid.uuid4().hex}"
    with patch("cairn.devices.inference_domain.host.ollama_resolver",
               return_value=_stub_resolver):
        rig["shim"].deliver({
            "id": envelope_id, "sender": rig["caller"], "addressee": "inference_domain",
            "channel": "personal", "verb": verb,
            "body": {**body, testing_mark.FIELD: testing_mark.mark(_TICKET, testing_mark.PERFORM)}})
    replies = [e for e in rig["bus"].read(to=rig["caller"], channel="personal")
               if e.get("reply_to") == envelope_id]
    assert len(replies) == 1, f"{len(replies)} replies to {verb!r} on the bus, want 1"
    rig["bus"].record_delivery(replies[0]["id"], to=rig["caller"], by=rig["caller"])
    return replies[0]


# --- teeth ------------------------------------------------------------------

def test_embed_and_infer_are_declared_beside_resolve():
    InferenceDomainDevice = _subject()[1]
    verbs = InferenceDomainDevice().declared_verbs()
    assert {"embed", "infer", "resolve"} <= set(verbs), sorted(verbs)
    assert all(callable(verbs[v]) for v in ("embed", "infer", "resolve"))


def test_infer_over_the_bus_answers_a_completion():
    rig = _fresh_bus()
    SEEN.clear()
    nonce = f"say the nonce {_RUN}"
    reply = _ask(rig, "infer", {"prompt": nonce, "model": "qwen2.5:7b"})
    assert reply["sender"] == "inference_domain" and reply["addressee"] == rig["caller"], reply
    assert reply["body"]["answer"]["text"] == f"stub says: {nonce}", reply["body"]
    assert reply["body"].get("hit") is False, reply["body"]
    assert SEEN and SEEN[-1]["kind"] == "generate" and SEEN[-1]["prompt"] == nonce, SEEN


def test_embed_over_the_bus_answers_a_vector():
    rig = _fresh_bus()
    SEEN.clear()
    reply = _ask(rig, "embed", {"prompt": f"embed me {_RUN}", "model": "nomic-embed-text"})
    assert reply["body"]["answer"]["vector"] == FAKE_VECTOR, reply["body"]
    assert SEEN and SEEN[-1]["kind"] == "embed", SEEN


def test_the_verb_fixes_the_kind_over_a_callers_own():
    """embed means embed: a body that says kind=generate still gets a vector from ``embed``."""
    rig = _fresh_bus()
    SEEN.clear()
    reply = _ask(rig, "embed", {"kind": "generate", "prompt": f"contrary {_RUN}",
                                "model": "nomic-embed-text"})
    assert "vector" in reply["body"]["answer"], reply["body"]
    assert SEEN[-1]["kind"] == "embed", SEEN


def test_no_host_is_dialed():
    """Every ask above went to the stub — the recorder saw every request the domain made."""
    rig = _fresh_bus()
    SEEN.clear()
    _ask(rig, "infer", {"prompt": f"one {_RUN}", "model": "qwen2.5:7b"})
    _ask(rig, "embed", {"prompt": f"two {_RUN}", "model": "nomic-embed-text"})
    assert [r["kind"] for r in SEEN] == ["generate", "embed"], SEEN


if __name__ == "__main__":
    teeth = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    # The device's trail and task tickets ride the roots (ticket ea4a6151300f): moved into a
    # fixture world for the run so a bus proof leaves nothing in the live tickets folder.
    from cairn.tools.scratch.scratch import scratch_dir
    from cairn.tools.base import address as _address
    try:
        from cairn.devices.inference_domain import domain as _domain
        _domain.set_diagnostic_roots({**_address.ROOTS, "instance": scratch_dir("cairn_bus_infer_")})
    except Exception as exc:  # noqa: BLE001 — the subject is gone; every tooth below FAILS by name
        _domain = None
        print(f"  (the domain did not import: {type(exc).__name__}: {exc})")
    rc = 0
    try:
        for t in teeth:
            try:
                t()
                print(f"  PASS  {t.__name__}")
            except Exception as exc:  # noqa: BLE001
                rc = 1
                print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}")
    finally:
        if _domain is not None:
            _domain.set_diagnostic_roots(None)
    print("green — infer and embed answer over the bus, no host dialed" if rc == 0 else "RED")
    sys.exit(rc)
