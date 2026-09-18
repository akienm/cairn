"""Proof for ticket ``ea4a6151300f`` — every inference call produces a complete TASK TICKET.

The falsifier is unnumbered, so ``proof_coverage.clauses`` reads it as the single clause
``all`` and this file declares ONE composite tooth for it, which runs the narrow teeth end to
end (each still prints on its own so a red names which half fell). Reverting any build file
— ``domain.py`` (the ticket writer, the caller measurement, the trouble raise), ``device.py``
(the envelope sender carried through, the refusal returned as a value) or the probe — reds
the composite.

WHAT THE NARROW TEETH ASK, and why each is one a hollow build could not pass:

  - ONE CALL, ONE FILE, AND THE FILE NAMES THE CANONICAL. Read back off disk under an isolated
    instance root, never off ``resolve``'s return value.
  - THE CALLER RIDES THE ENVELOPE. A fake envelope with a ``sender`` goes through the shim's
    real ``_handle_resolve`` and the ticket's caller IS that sender, measured ``declared``.
  - A DIRECT CALL IS NAMED OFF THE CALL CHAIN; a call that leaves no trace records
    ``unknown`` — never a blank (the ticket's third green clause).
  - SPECIFIED AND SELECTED ARE BOTH THERE AND CAN DISAGREE. The request asks for one model,
    the route reports another, and the ticket shows both — the escalation the ticket exists
    to make visible.
  - A REFUSAL RAISES A TROUBLE INTO THE DEVICE'S OWN LOG HOME naming the ticket, and the
    caller still receives the very exception the resolver raised — over the bus, the shim
    turns it into an intelligible VALUE naming the refusal and the ticket path.
  - THE TICKET IS NOT A PARALLEL STORE: a hit is still served from the cache with one host
    call across two asks, and the ticket write is bounded (the latency clause).
  - THE PROBE AND THE PROOF SHARE ONE PREDICATE: ``ticket_lacks`` reads ``[]`` over every
    ticket this file wrote, and the probe fires on a fixture ticket that lacks.

Requires the db_domain provisioning; uses an ephemeral cache table dropped on the way out and
a fresh temp instance-root per tooth, so neither the live cache nor the live tickets folder is
touched.

    python3 cairn/devices/inference_domain/proofs/test_task_ticket.py
"""

from __future__ import annotations

import contextlib
import json
import sys
import uuid
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.inference_domain import domain
from cairn.devices.inference_domain.probes import are_inference_task_tickets_complete as probe
from cairn.devices.tester.scratch import scratch_dir
from cairn.tools.base import address

_RUN = uuid.uuid4().hex[:8]     # names this run in row text; never a table name
_SCRATCH = contextlib.ExitStack()   # the one table this proof owns rides store.scratch(): dropped at close, swept by pid if not
_HELD: list[str] = []


def _table() -> str:
    """The proof's one table, minted on first use as scratch."""
    if not _HELD:
        _HELD.append(_SCRATCH.enter_context(domain.scratch_cache("probe_infer")))
    return _HELD[0]

PROVES = {
    "ea4a6151300f": {
        "all": "test_every_inference_call_produces_a_complete_task_ticket",
    },
}


class _Resolver:
    def __init__(self, provenance: dict | None = None, cost: float = 7.0):
        self.calls = 0
        self._cost = cost
        self._provenance = provenance if provenance is not None else {
            "host": "http://hex.local:11434", "path": "/api/generate",
            "model": "qwen2.5:7b", "provider": "ollama", "route_walked": ["local", "hex"]}

    def __call__(self, request: dict) -> dict:
        self.calls += 1
        return {"answer": {"text": f"answer {self.calls}"}, "cost": self._cost,
                "provenance": dict(self._provenance)}


class _Refusing(_Resolver):
    def __init__(self, error: Exception, **kw):
        super().__init__(**kw)
        self._error = error

    def __call__(self, request: dict) -> dict:
        self.calls += 1
        raise self._error


class _Unreachable(Exception):
    pass


@contextlib.contextmanager
def _isolated():
    tmp = scratch_dir("cairn_task_ticket_")
    domain.set_diagnostic_roots({**address.ROOTS, "instance": tmp})
    try:
        yield tmp
    finally:
        domain.set_diagnostic_roots(None)


def _tickets(tmp: Path) -> list[dict]:
    folder = tmp / "devices" / "inference_domain" / "0" / "tickets"
    if not folder.is_dir():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))]


def _trail_lines(tmp: Path) -> list[dict]:
    trail = tmp / "logs" / "inference_domain" / "0"
    if not trail.exists():
        return []
    from cairn.tools.base.breadcrumb_log import RECORD_NAME
    out = []
    jsonl = trail / RECORD_NAME
    if jsonl.is_file():
        out.extend(json.loads(l) for l in jsonl.read_text(encoding="utf-8").splitlines() if l.strip())
    for p in sorted(trail.glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def test_one_call_writes_one_ticket_naming_the_canonical():
    with _isolated() as tmp:
        assert _tickets(tmp) == [], "the isolated root starts with no tickets"
        out = domain.resolve({"q": f"one_{_RUN}", "model": "qwen2.5:7b"},
                             resolver=_Resolver(), table=_table())
        tickets = _tickets(tmp)
        assert len(tickets) == 1, f"one call must write exactly one ticket, found {len(tickets)}"
        t = tickets[0]
        assert t["canonical"] == out["canonical"], "the ticket names the canonical request"
        assert out["ticket"] and Path(out["ticket"]).is_file(), "the result carries the ticket path"
        assert Path(out["ticket"]).parent == tmp / "devices" / "inference_domain" / "0" / "tickets", (
            f"the ticket berths in the device's own instance-space, got {out['ticket']}")
        assert t["verdict"] == "miss" and t["outcome"]["kind"] == "answered"
        assert t["response"] == out["answer"], "the ticket carries the response"
        assert domain.ticket_lacks(t) == [], f"a fresh ticket is complete, lacks {domain.ticket_lacks(t)}"
        assert t["cache"]["table"] == _table()


def test_the_caller_rides_the_bus_envelope_through_the_shim():
    from cairn.devices.inference_domain.device import InferenceDomainDevice
    with _isolated() as tmp:
        dev = InferenceDomainDevice.__new__(InferenceDomainDevice)

        class _Sink:
            def __init__(self):
                self.emitted = []

            def emit(self, *a, **k):
                self.emitted.append((a, k))
                return {}

            def raise_trouble(self, identity, *, why, detail=None, now=None):
                return domain._trail.raise_trouble(identity, why=why, detail=detail, now=now)

        dev.debug_sink = _Sink()
        r = _Resolver()
        real = domain.resolve
        # The shim builds the host resolver itself; hand it the stub through the seam it
        # already uses so no host is dialled, and pin the cache table to this run's own.
        import cairn.devices.inference_domain.host as host
        kept = host.ollama_resolver
        host.ollama_resolver = lambda **kw: r
        domain.resolve = lambda request, **kw: real(request, table=_table(), **kw)
        try:
            result = dev._handle_resolve({"sender": f"probe-sender-{_RUN}",
                                          "body": {"kind": "generate",
                                                   "prompt": f"bus_{_RUN}",
                                                   "model": "qwen2.5:7b"}})
        finally:
            host.ollama_resolver = kept
            domain.resolve = real
        tickets = _tickets(tmp)
        assert len(tickets) == 1
        t = tickets[0]
        assert t["caller"] == {"identity": f"probe-sender-{_RUN}", "how": "declared"}, (
            f"the ticket's caller is the envelope sender, got {t['caller']}")
        assert result["ticket"] and Path(result["ticket"]).is_file(), result
        assert json.loads(Path(result["ticket"]).read_text())["id"] == t["id"]
        assert result["hit"] is False and result["answer"] == {"text": "answer 1"}


def test_a_direct_call_is_named_off_the_call_chain_and_nothing_records_unknown():
    with _isolated() as tmp:
        domain.resolve({"q": f"direct_{_RUN}"}, resolver=_Resolver(), table=_table())
        t = _tickets(tmp)[0]
        assert t["caller"]["how"] == "call_chain", t["caller"]
        assert t["caller"]["identity"].startswith("cairn/devices/inference_domain/proofs/test_task_ticket.py"), (
            f"a direct caller inside class-space is named by its address, got {t['caller']}")
        # No frame in class-space at all → unknown, never a blank.
        who = domain.caller_identity(None, frames=[])
        assert who == {"identity": "unknown", "how": "none"}, who
        who = domain.caller_identity(None, frames=[("", "/nowhere/outside/repo.py", 1, "f")])
        assert who == {"identity": "unknown", "how": "none"}, who
        assert domain.caller_identity("x-shim") == {"identity": "x-shim", "how": "declared"}


def test_specified_and_selected_are_both_carried_and_may_disagree():
    with _isolated() as tmp:
        r = _Resolver(provenance={"host": "http://hex.local:11434", "path": "/api/generate",
                                  "model": "qwen2.5:14b", "provider": "ollama",
                                  "route_walked": ["local", "hex"]})
        domain.resolve({"q": f"esc_{_RUN}", "model": "qwen2.5:7b", "provider": "ollama"},
                       resolver=r, table=_table())
        t = _tickets(tmp)[0]
        assert t["specified"]["model"] == "qwen2.5:7b", t["specified"]
        assert t["selected"]["model"] == "qwen2.5:14b", t["selected"]
        assert t["selected"]["host"] == "http://hex.local:11434"
        assert t["selected"]["route_walked"] == ["local", "hex"]
        assert t["specified"]["provider"] == t["selected"]["provider"] == "ollama"
        assert t["specified"]["domain"], "the specified block names the domain the request dressed into"


def test_a_refusal_raises_a_trouble_naming_the_ticket_and_the_shim_returns_a_value():
    with _isolated() as tmp:
        err = _Unreachable(f"dial 127.0.0.1:1 refused {_RUN}")
        try:
            domain.resolve({"q": f"refused_{_RUN}"}, resolver=_Refusing(err), table=_table())
        except _Unreachable as caught:
            assert caught is err, "the very instance the resolver raised reaches the caller"
        else:
            raise AssertionError("a refusal must still raise to a direct caller")
        tickets = _tickets(tmp)
        assert len(tickets) == 1
        t = tickets[0]
        assert t["outcome"] == {"kind": "refused", "refused": "_Unreachable",
                                "detail": str(err)}, t["outcome"]
        assert t["verdict"] == "refused" and t["response"] is None and t["cost"] == 0
        assert t["trouble"] and t["trouble"]["identity"].startswith("inference-refused-"), t["trouble"]
        assert domain.ticket_lacks(t) == [], domain.ticket_lacks(t)
        assert getattr(err, "task_ticket", None) and Path(err.task_ticket).is_file()
        raised = [l for l in _trail_lines(tmp) if l.get("crossing") == "raise_trouble"
                  or l.get("gate") == "raise_trouble" or "raise_trouble" in json.dumps(l)]
        assert raised, f"the refusal must land a raise_trouble emission in the device's own log home: {_trail_lines(tmp)}"
        body = json.dumps(raised[-1])
        assert t["trouble"]["identity"] in body and "_Unreachable" in body, raised[-1]
        assert t["canonical_digest"] in body, "the trouble names the refused ask"
        assert err.task_ticket in body, "the trouble names the task-ticket path (chart criterion 4)"

        # Over the bus: the shim returns an intelligible VALUE rather than a traceback.
        from cairn.devices.inference_domain.device import InferenceDomainDevice
        import cairn.devices.inference_domain.host as host
        dev = InferenceDomainDevice.__new__(InferenceDomainDevice)

        class _Sink:
            def emit(self, *a, **k):
                return {}

            def raise_trouble(self, identity, *, why, detail=None, now=None):
                return domain._trail.raise_trouble(identity, why=why, detail=detail, now=now)

        dev.debug_sink = _Sink()
        real = domain.resolve
        kept = host.ollama_resolver
        host.ollama_resolver = lambda **kw: _Refusing(_Unreachable("bus dial refused"))
        domain.resolve = lambda request, **kw: real(request, table=_table(), **kw)
        try:
            value = dev._handle_resolve({"sender": "some-device", "body": {"kind": "generate",
                                                                            "prompt": f"busref_{_RUN}"}})
        finally:
            host.ollama_resolver = kept
            domain.resolve = real
        assert value["outcome"] == "refused" and value["refused"] == "_Unreachable", value
        assert "bus dial refused" in value["detail"]
        assert value["ticket"] and Path(value["ticket"]).is_file(), value
        assert json.loads(Path(value["ticket"]).read_text())["caller"]["identity"] == "some-device"


def test_the_ticket_is_not_a_parallel_store_and_costs_bounded_latency():
    with _isolated() as tmp:
        r = _Resolver()
        ask = {"q": f"hit_{_RUN}"}
        domain.resolve(dict(ask), resolver=r, table=_table())
        t0 = time.perf_counter()
        hit = domain.resolve(dict(ask), resolver=r, table=_table())
        elapsed = time.perf_counter() - t0
        assert hit["hit"] is True and r.calls == 1, "the answer still comes from the cache, one host call"
        tickets = _tickets(tmp)
        assert len(tickets) == 2 and tickets[-1]["verdict"] == "hit"
        assert tickets[-1]["selected"].get("model") == "qwen2.5:7b", (
            "a hit's selected block is read off the cached provenance")
        assert elapsed < 2.0, f"a cached resolve with a ticket took {elapsed:.3f}s"
        t0 = time.perf_counter()
        domain._write_task_ticket(dict(tickets[-1]))
        w = (time.perf_counter() - t0) * 1000
        assert w < 50, f"the ticket write must be negligible, took {w:.1f}ms"
        assert len(_tickets(tmp)) == 3


def test_the_probe_shares_the_predicate_and_fires_on_a_lacking_ticket():
    with _isolated() as tmp:
        for n in range(3):
            domain.resolve({"q": f"probe_{n}_{_RUN}"}, resolver=_Resolver(), table=_table())
        good = domain.read_task_tickets()
        assert len(good) == 3 and all(domain.ticket_lacks(t) == [] for t in good)
        s = probe.judge_tickets(good)
        assert s["incomplete"] == [] and s["named"] == 3
        lacking = [dict(t) for t in good]
        del lacking[0]["caller"]
        lacking[1]["outcome"] = {"kind": "refused"}       # a refusal with no trouble beside it
        s = probe.judge_tickets(lacking * 7)              # past the trigger floor of 20
        assert s["tickets"] == 21 and len(s["incomplete"]) == 14, s
        assert probe._trigger(None, {"corpus": s}) is True
        assert probe._enough({"corpus": s}) is False
        assert probe._trigger(None, {"corpus": probe.judge_tickets(lacking)}) is False, (
            "below the floor the probe waits")
        # The clear: ten named callers beside one real trouble.
        refused = dict(good[0], outcome={"kind": "refused", "refused": "X"},
                       trouble={"identity": "inference-refused-x"})
        s = probe.judge_tickets(good * 4 + [refused])
        assert probe._enough({"corpus": s}) is True, s
        assert probe._carry({"corpus": s})["cleared_by"] == "named-and-troubled"
        assert probe.PROBE.to == "harbor_master"


_NARROW = [
    test_one_call_writes_one_ticket_naming_the_canonical,
    test_the_caller_rides_the_bus_envelope_through_the_shim,
    test_a_direct_call_is_named_off_the_call_chain_and_nothing_records_unknown,
    test_specified_and_selected_are_both_carried_and_may_disagree,
    test_a_refusal_raises_a_trouble_naming_the_ticket_and_the_shim_returns_a_value,
    test_the_ticket_is_not_a_parallel_store_and_costs_bounded_latency,
    test_the_probe_shares_the_predicate_and_fires_on_a_lacking_ticket,
]


def test_every_inference_call_produces_a_complete_task_ticket():
    """THE ONE DECLARED TOOTH for the falsifier's one clause: the narrow teeth end to end."""
    for check in _NARROW:
        check()
        print(f"    PASS  {check.__name__}")


def _main() -> int:
    try:
        test_every_inference_call_produces_a_complete_task_ticket()
        print("  PASS  test_every_inference_call_produces_a_complete_task_ticket")
    finally:
        domain.set_diagnostic_roots(None)
        _SCRATCH.close()
    print("green — every inference call produces a complete task ticket, and a refusal raises a trouble")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
