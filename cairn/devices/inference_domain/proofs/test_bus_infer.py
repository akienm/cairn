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

import contextlib
import sys
import uuid
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

_RUN = uuid.uuid4().hex[:8]     # names this run in message text; never a table name
_SCRATCH = contextlib.ExitStack()   # every bus this run minted rides store.scratch(): dropped at close, swept by pid if not
NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
FAKE_VECTOR = [0.5, 0.25, 0.125]
SEEN: list[dict] = []


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
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_infer"))
    loop = GroundLoopDevice(bus=bus)
    loop.subscribe(BusShim(bus, loop))
    loop.subscribe(InferenceDomainShim(bus=bus))
    loop.subscribe(CallerShim(bus=bus))
    loop.beat(NOW)
    return bus


def _ask(bus, verb, body):
    with patch("cairn.devices.inference_domain.host.ollama_resolver",
               return_value=_stub_resolver):
        return bus.request(sender="caller", to="inference_domain", channel="personal",
                           verb=verb, why=f"proof: {verb} over the bus", body=body)


# --- teeth ------------------------------------------------------------------

def test_embed_and_infer_are_declared_beside_resolve():
    verbs = InferenceDomainDevice().declared_verbs()
    assert {"embed", "infer", "resolve"} <= set(verbs), sorted(verbs)
    assert all(callable(verbs[v]) for v in ("embed", "infer", "resolve"))


def test_infer_over_the_bus_answers_a_completion():
    bus = _fresh_bus()
    SEEN.clear()
    nonce = f"say the nonce {_RUN}"
    reply = _ask(bus, "infer", {"prompt": nonce, "model": "qwen2.5:7b"})
    assert reply["sender"] == "inference_domain" and reply["addressee"] == "caller", reply
    assert reply["body"]["answer"]["text"] == f"stub says: {nonce}", reply["body"]
    assert reply["body"].get("hit") is False, reply["body"]
    assert SEEN and SEEN[-1]["kind"] == "generate" and SEEN[-1]["prompt"] == nonce, SEEN


def test_embed_over_the_bus_answers_a_vector():
    bus = _fresh_bus()
    SEEN.clear()
    reply = _ask(bus, "embed", {"prompt": f"embed me {_RUN}", "model": "nomic-embed-text"})
    assert reply["body"]["answer"]["vector"] == FAKE_VECTOR, reply["body"]
    assert SEEN and SEEN[-1]["kind"] == "embed", SEEN


def test_the_verb_fixes_the_kind_over_a_callers_own():
    """embed means embed: a body that says kind=generate still gets a vector from ``embed``."""
    bus = _fresh_bus()
    SEEN.clear()
    reply = _ask(bus, "embed", {"kind": "generate", "prompt": f"contrary {_RUN}",
                                "model": "nomic-embed-text"})
    assert "vector" in reply["body"]["answer"], reply["body"]
    assert SEEN[-1]["kind"] == "embed", SEEN


def test_no_host_is_dialed():
    """Every ask above went to the stub — the recorder saw every request the domain made."""
    bus = _fresh_bus()
    SEEN.clear()
    _ask(bus, "infer", {"prompt": f"one {_RUN}", "model": "qwen2.5:7b"})
    _ask(bus, "embed", {"prompt": f"two {_RUN}", "model": "nomic-embed-text"})
    assert [r["kind"] for r in SEEN] == ["generate", "embed"], SEEN


if __name__ == "__main__":
    teeth = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    # The device's trail and task tickets ride the roots (ticket ea4a6151300f): moved into a
    # fixture world for the run so a bus proof leaves nothing in the live tickets folder.
    from cairn.devices.inference_domain import domain as _domain
    from cairn.devices.tester.scratch import scratch_dir
    from cairn.tools.base import address as _address
    _domain.set_diagnostic_roots({**_address.ROOTS, "instance": scratch_dir("cairn_bus_infer_")})
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
        _domain.set_diagnostic_roots(None)
        _SCRATCH.close()
    print("green — infer and embed answer over the bus, no host dialed" if rc == 0 else "RED")
    sys.exit(rc)
