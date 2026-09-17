#!/usr/bin/env python3
"""aider_shim reaches inference_domain only through a door — never by import, never by path.

TICKET 50ad391f4e95. The falsifier: done when aider_shim contains zero imports from
``cairn.devices.inference_domain`` and zero hardcoded paths into inference_domain's file
tree; wrong intent if the fix just updates the path to the new location. So the teeth
here are two measurements over the device's OWN SOURCE (an ast walk for the import, a
literal scan for the path — the same instrument would red a "moved" path exactly as it
reds the old one, which is what makes the wrong-intent clause falsifiable) and two over
the door that replaced the reach: the surface asks the bus ``get`` / ``what=models`` and
sizes its model table off the answer, and inference_domain actually declares that view
and answers it with the parsed stack.

A HOLLOW BUILD COULD NOT PASS THESE: the source teeth are satisfied by deleting the reach,
but the door teeth are satisfied only by a surface that still gets a stack from somewhere
— the fake bus counts the ask, and the model table it produces must carry a model the
stack declares.
"""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

DEVICE = Path(__file__).resolve().parents[1]
FORBIDDEN_MODULE = "cairn.devices.inference_domain"
FORBIDDEN_PATH_PARTS = ("inference_domain",)

# 50ad391f4e95's falsifier numbers no clauses — proof_coverage.clauses() reads it as the one
# clause ``all`` — so ONE tooth is declared for it, and that tooth is the ticket's whole claim
# run end to end: zero imports, zero paths, the owner declares the view, the surface asks the
# bus. It is composed from the narrow teeth below (each of which still prints on its own so a
# red names WHICH half fell), and it reds when ANY of the build's three files is reverted —
# measured 2026-09-17: with the first draft's three narrow declarations, the hollow reading
# reverted inference_domain/device.py and no declared tooth redded, because the view tooth
# was not among them.
PROVES = {
    "50ad391f4e95": {
        "all": "test_aider_shim_reaches_inference_domain_only_through_a_door",
    },
}


def _device_modules():
    """Every .py under the device that is NOT a proof — the proofs may name the forbidden
    module (this file does, as a string) and are not the device's runtime."""
    return sorted(p for p in DEVICE.rglob("*.py") if "proofs" not in p.relative_to(DEVICE).parts)


def _imports_of(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""


def _path_literals_of(path: Path):
    """String constants that spell a path into inference_domain's tree.

    Two shapes, and only these two: ``"inference_domain"`` as an operand of ``/`` (the
    ``Path(...) / "devices" / "inference_domain" / ...`` walk the old code did), or any
    string carrying ``inference_domain/`` (a joined path). A bare ``"inference_domain"``
    elsewhere is NOT a path — it is the device's bus address, and ``to="inference_domain"``
    is exactly the door this ticket wants the reach replaced with.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    div_operands = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            for side in (node.left, node.right):
                if isinstance(side, ast.Constant):
                    div_operands.add(id(side))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if any(f"{p}/" in v for p in FORBIDDEN_PATH_PARTS):
                yield v
            elif v in FORBIDDEN_PATH_PARTS and id(node) in div_operands:
                yield v


def test_the_device_has_modules_to_measure():
    mods = _device_modules()
    assert mods, f"no modules under {DEVICE} — the census below would be vacuous"
    assert any(m.name == "interceptor.py" for m in mods)


def test_no_module_in_aider_shim_imports_inference_domain():
    offenders = []
    for m in _device_modules():
        for name in _imports_of(m):
            if name == FORBIDDEN_MODULE or name.startswith(FORBIDDEN_MODULE + "."):
                offenders.append(f"{m.relative_to(DEVICE)}: {name}")
    assert not offenders, "aider_shim imports inference_domain directly:\n  " + "\n  ".join(offenders)


def test_no_module_in_aider_shim_spells_a_path_into_inference_domain():
    offenders = []
    for m in _device_modules():
        for lit in _path_literals_of(m):
            offenders.append(f"{m.relative_to(DEVICE)}: {lit!r}")
    assert not offenders, "aider_shim names a path into inference_domain's tree:\n  " + "\n  ".join(offenders)


def test_the_instrument_would_catch_a_repointed_path(tmp_path):
    """The wrong-intent clause: 'the fix just updates the path to the new location'. The
    literal scan must red a path into inference_domain wherever it points."""
    bad = tmp_path / "repointed.py"
    bad.write_text(
        'from pathlib import Path\n'
        'HERE = Path(__file__).parents[3] / "somewhere_else" / "inference_domain" / "stacks"\n',
        encoding="utf-8",
    )
    assert list(_path_literals_of(bad)) == ["inference_domain"]
    bad2 = tmp_path / "joined.py"
    bad2.write_text('P = "cairn/devices/inference_domain/machines/route/stacks/models.json"\n',
                    encoding="utf-8")
    assert list(_path_literals_of(bad2))
    fine = tmp_path / "address.py"
    fine.write_text('bus.request(sender="aider_shim", to="inference_domain", verb="get")\n',
                    encoding="utf-8")
    assert list(_path_literals_of(fine)) == [], "a bus address is not a path"


class _FakeBus:
    """Records every request; answers ``get``/``what=models`` with a declared stack."""

    def __init__(self, stack):
        self.stack = stack
        self.seen = []

    def request(self, **kw):
        self.seen.append(kw)
        assert kw["to"] == "inference_domain"
        assert kw["verb"] == "get"
        assert kw["body"] == {"what": "models"}
        return {"body": {"accepted": True, "verb": "get", "view": "models",
                         "device": "inference_domain", "data": self.stack}}


def test_the_surface_asks_the_bus_for_the_models_stack():
    from cairn.devices.aider_shim import interceptor
    from cairn.devices.aider_shim.fence import Fence, SeenLog

    stack = {"models": [{"name": "fixture-model:1b"}, {"name": "other-model:7b"}]}
    bus = _FakeBus(stack)
    mod = interceptor.build(bus=bus, fence=Fence(), log=SeenLog(), resolver=object())
    assert len(bus.seen) == 1, f"expected one ask for the stack, saw {len(bus.seen)}"
    assert bus.seen[0]["sender"] == "aider_shim"
    assert set(mod.model_cost) == {"fixture-model:1b", "other-model:7b"}
    assert mod.get_model_info("fixture-model:1b")["max_output_tokens"] == Fence().reply_headroom
    try:
        mod.get_model_info("gpt-4o")
    except KeyError:
        pass
    else:
        raise AssertionError("a model the stack does not declare was answered")


def test_an_injected_stack_never_touches_the_bus():
    from cairn.devices.aider_shim import interceptor
    from cairn.devices.aider_shim.fence import Fence, SeenLog

    class _Never:
        def request(self, **kw):
            raise AssertionError(f"bus asked with an injected stack: {kw}")

    stack = {"models": [{"name": "fixture-model:1b"}]}
    mod = interceptor.build(bus=_Never(), models_stack=stack, fence=Fence(), log=SeenLog(),
                            resolver=object())
    assert set(mod.model_cost) == {"fixture-model:1b"}


def test_inference_domain_declares_a_models_view_that_returns_the_stack():
    from cairn.devices.inference_domain.device import InferenceDomainDevice

    dev = InferenceDomainDevice()
    views = dev.declared_views()
    assert "models" in views, f"no models view, available: {sorted(views)}"
    reply = dev.declared_verbs()["get"]({"body": {"what": "models"}})
    assert reply["accepted"] is True and reply["view"] == "models"
    stack = reply["data"]
    names = {m["name"] for m in stack["models"]}
    assert names, "the models stack declares no models"
    assert "qwen3-coder:30b" in names, f"the declared stack lost the coder model: {sorted(names)}"


def test_the_seam_answers_the_same_stack_as_the_view():
    from cairn.tools.bus_client import models_stack
    from cairn.devices.inference_domain.device import InferenceDomainDevice

    assert models_stack() == InferenceDomainDevice().declared_views()["models"]()


def test_aider_shim_reaches_inference_domain_only_through_a_door():
    """The declared tooth: the falsifier whole. Reverting interceptor.py restores the path walk
    (the scan reds) and stops the bus ask (the fake bus sees zero asks); reverting
    inference_domain/device.py removes the view (the get verb refuses); reverting bus_client
    removes the seam (the import fails)."""
    test_the_device_has_modules_to_measure()
    test_no_module_in_aider_shim_imports_inference_domain()
    test_no_module_in_aider_shim_spells_a_path_into_inference_domain()
    test_the_surface_asks_the_bus_for_the_models_stack()
    test_inference_domain_declares_a_models_view_that_returns_the_stack()
    test_the_seam_answers_the_same_stack_as_the_view()


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
