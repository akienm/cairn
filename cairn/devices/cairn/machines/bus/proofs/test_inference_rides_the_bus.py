#!/usr/bin/env python3
"""Everybody talks to inference_domain over the bus — ticket 87a7f1c7ae21.

The falsifier numbers no clauses, so ONE composite tooth carries the ticket's whole
claim (PROVES keys follow the falsifier markers): (a) no source outside
``cairn/devices/inference_domain/`` imports ``cairn.devices.inference_domain`` — an AST
walk over every .py under ``cairn/`` that is not a proof or a probe (instruments may read
what they measure; ``device_isolation_holds`` draws the same line), which is the
falsifier's ``grep`` taken the way the sieve takes it and widened from the devices to the
TOOL that used to hold the door; (b) the path that used to go around the bus now rides
it: a surface built with NO bus and NO injected door (aider's venv subprocess) asks
``resolve`` and ``get`` of ``inference_domain`` on the bus ``bus_client.inference_bus``
hands it, and ``bus_client.models_stack()`` is a ``get`` on that same bus, never a call
into the domain; (c) that bus is real — ``inference_bus()`` wires inference_domain's shim
in-process and answers ``get``/``what=models`` with a non-empty stack, so the door the
no-bus path leans on exists.

A HOLLOW BUILD COULD NOT PASS THIS: reverting bus_client restores ``inference_seam`` (the
import walk reds, and ``inference_bus`` is gone); reverting interceptor.py makes the no-bus
surface reach for ``inference_seam`` instead of the bus (the fake bus sees no ``resolve``).
Measured 2026-09-18 before the build: the walk found two imports, both in
``cairn/tools/bus_client/bus_client.py`` (``inference_seam``, ``models_stack``), and the
no-bus surface called ``domain.resolve`` in-process.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

PROVES = {
    "87a7f1c7ae21": {
        "all": "test_every_inference_call_rides_the_bus",
    },
}

_REPO = Path(__file__).resolve().parents[6]
_CAIRN = _REPO / "cairn"
_OWNER = _CAIRN / "devices" / "inference_domain"
_FORBIDDEN = "cairn.devices.inference_domain"
_INSTRUMENT_DIRS = {"proofs", "probes", "proofs_disabled"}


def _source_modules() -> list[Path]:
    """Every .py under cairn/ that is neither the owner's nor an instrument."""
    out = []
    for p in _CAIRN.rglob("*.py"):
        if _OWNER in p.parents:
            continue
        if _INSTRUMENT_DIRS & set(p.relative_to(_CAIRN).parts[:-1]):
            continue
        out.append(p)
    return sorted(out)


def _imports_of(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""


def test_no_source_outside_the_owner_imports_inference_domain():
    mods = _source_modules()
    assert len(mods) > 100, f"the walk read {len(mods)} modules — a clean result over so few is a hollow scan"
    assert any(p.name == "bus_client.py" for p in mods), "the walk must reach the tool that held the door"
    assert any(p.name == "interceptor.py" for p in mods), "the walk must reach aider_shim's surface"
    offenders = [
        f"{m.relative_to(_REPO)}: {imp}"
        for m in mods
        for imp in _imports_of(m)
        if imp == _FORBIDDEN or imp.startswith(_FORBIDDEN + ".")
    ]
    assert not offenders, "source outside inference_domain imports it directly:\n  " + "\n  ".join(offenders)


def fence_provider() -> str:
    """The provider the device's own fence allows — the scripted reply must sit inside it,
    or the fence (rightly) refuses the answer before this tooth can read the route."""
    from cairn.devices.aider_shim.fence import Fence
    return list(Fence().providers)[0]


class _RecordingBus:
    """Answers ``get``/``what=models`` with a declared stack and ``resolve`` with a scripted
    reply; records every request so the tooth can say which door was knocked on."""

    def __init__(self, stack: dict, model: str):
        self.stack = stack
        self.model = model
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
                             "provenance": {"provider": fence_provider(), "domain": "coding",
                                            "model": self.model}}}
        raise AssertionError(f"unexpected verb on the bus: {kw['verb']}")


def test_a_surface_with_no_bus_asks_inference_domain_over_a_reach_bus():
    from cairn.tools import bus_client as bc
    from cairn.devices.aider_shim import interceptor
    from cairn.devices.aider_shim.fence import Fence, SeenLog

    fence = Fence()
    model = fence.models[0]
    bus = _RecordingBus({"models": [{"name": model}]}, model)
    built = []

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
    assert built == [1], f"the surface builds ONE reach bus on first need, saw {len(built)}"
    verbs = [r["verb"] for r in bus.seen]
    assert verbs == ["get", "resolve"], f"the no-bus surface asks the stack then resolves, over the bus: {verbs}"
    assert all(r["sender"] == "aider_shim" for r in bus.seen), bus.seen
    assert bus.seen[1]["body"]["model"] == model, bus.seen[1]
    assert out.choices[0].message.content == "pong", out


def test_the_tools_models_stack_is_a_get_on_the_bus():
    from cairn.tools.bus_client import bus_client as bcm

    stack = {"models": [{"name": "fixture-model:1b"}]}
    bus = _RecordingBus(stack, "fixture-model:1b")
    saved = bcm.reach
    bcm.reach = lambda *devices: (bus if devices == ("inference_domain",) else (_ for _ in ()).throw(AssertionError(devices)))
    try:
        got = bcm.models_stack()
    finally:
        bcm.reach = saved
    assert got == stack, got
    assert [r["verb"] for r in bus.seen] == ["get"], bus.seen
    assert not hasattr(bcm, "inference_seam"), "the in-process seam is gone; the bus is the one path"


def test_the_reach_bus_is_real_and_inference_domain_answers_on_it():
    from cairn.tools.bus_client import inference_bus

    bus = inference_bus()
    reply = bus.request(sender="proof", to="inference_domain", verb="get",
                        why="87a7f1c7ae21: the door the no-bus path leans on exists",
                        body={"what": "models"})
    body = reply["body"]
    assert body["accepted"] is True and body["view"] == "models", body
    names = {m["name"] for m in body["data"]["models"]}
    assert names, "the owner answered an empty stack"


def test_every_inference_call_rides_the_bus():
    """The declared tooth: the falsifier whole — zero direct imports outside the owner,
    the no-bus surface on the bus, the tool's stack seam on the bus, and the bus real."""
    test_no_source_outside_the_owner_imports_inference_domain()
    test_a_surface_with_no_bus_asks_inference_domain_over_a_reach_bus()
    test_the_tools_models_stack_is_a_get_on_the_bus()
    test_the_reach_bus_is_real_and_inference_domain_answers_on_it()


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
