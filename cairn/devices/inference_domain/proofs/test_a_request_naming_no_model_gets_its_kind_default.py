"""A request that names no model gets the default its kind declares (ticket 959bb65192a1).

Measured 2026-10-14 at ticket e194f4b4cb3e: a bus generate request naming no model was sent to
nomic-embed-text and refused as if the route had failed — the asker was told the wrong cause.
The default was a code literal in _handle_resolve, valid for one kind only (nomic's duty is
embed only, Akien 2026-08-08). The default is now data — ``kind_defaults`` in the route's
models stack — and a kind that declares none is refused by name before any host is dialed.

Teeth a hollow build could not pass (no network: the resolver factory and the domain are
replaced at call time, and the factory fails the tooth if it is built when it must not be):
  1. AN EMBED REQUEST NAMING NO MODEL RESOLVES WITH nomic-embed-text, READ FROM THE STACKS:
     the model handed to the resolver equals load_stacks()'s kind_defaults['embed'], and
     device.py carries no 'nomic-embed-text' literal.
  2. A GENERATE REQUEST NAMING NO MODEL IS REFUSED BEFORE ANY DIAL: no resolver is built, and
     the refusal names the missing model, the kind 'generate', and the kinds that declare a
     default.
  3. A REQUEST NAMING A MODEL IS UNCHANGED: the named model passes through to the resolver.
  4. THE DECLARED DEFAULTS ARE VALIDATED AT LOAD: a fixture stack whose default names a model
     that does not serve that kind is refused by load_stacks, naming the kind and the model.
  5. THE EXISTING inference_domain PROOFS STAY GREEN: test_resolve_verb.py and
     test_route.py run whole, exit 0.

Run: python3 cairn/devices/inference_domain/proofs/test_a_request_naming_no_model_gets_its_kind_default.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "959bb65192a1": {
        "1": "test_an_embed_request_naming_no_model_gets_the_stacks_default",
        "2": "test_a_generate_request_naming_no_model_is_refused_before_any_dial",
        "3": "test_a_request_naming_a_model_passes_it_through",
        "4": "test_a_default_that_does_not_serve_its_kind_is_refused_at_load",
        "5": "test_the_existing_inference_domain_proofs_stay_green",
    },
}

_DEVICE_PY = _REPO_ROOT / "cairn/devices/inference_domain/device.py"
_STACKS = _REPO_ROOT / "cairn/devices/inference_domain/machines/route/stacks"


def _resolve(body: dict, *, may_dial: bool = True) -> tuple[dict, list]:
    """Run the resolve handler with the resolver factory and the domain replaced. Returns
    (the handler's answer, the models the factory was asked to build a resolver for)."""
    from cairn.devices.inference_domain.device import InferenceDomainDevice

    built: list = []

    def _factory(*, model, temperature=0.0, **kw):
        if not may_dial:
            raise AssertionError(f"a resolver was built for model {model!r} — that is a dial")
        built.append(model)
        return lambda request: None

    def _domain_resolve(request, *, resolver, sink=None, caller=None):
        return {"hit": False, "answer": {"text": "fixture"}, "ticket": None}

    with patch("cairn.devices.inference_domain.host.ollama_resolver", side_effect=_factory), \
         patch("cairn.devices.inference_domain.domain.resolve", side_effect=_domain_resolve):
        out = InferenceDomainDevice()._handle_resolve(
            {"id": "env-959b", "sender": "proof_959b", "body": body})
    return out, built


def test_an_embed_request_naming_no_model_gets_the_stacks_default():
    from cairn.devices.inference_domain.machines.route.route import load_stacks
    declared = (load_stacks()["models"].get("kind_defaults") or {}).get("embed")
    assert declared == "nomic-embed-text", f"the stacks declare embed's default as {declared!r}"
    out, built = _resolve({"kind": "embed", "prompt": "a"})
    assert built == [declared], f"the resolver was built for {built}, not the stacks' {declared!r}"
    assert "nomic-embed-text" not in _DEVICE_PY.read_text(), (
        "device.py still carries the literal 'nomic-embed-text' — the default is decided in code")
    print("ok test_an_embed_request_naming_no_model_gets_the_stacks_default")


def test_a_generate_request_naming_no_model_is_refused_before_any_dial():
    out, built = _resolve({"kind": "generate", "prompt": "a"}, may_dial=False)
    assert out.get("outcome") == "refused", f"a model-less generate was not refused: {out}"
    detail = str(out.get("detail", ""))
    assert "model" in detail and "'generate'" in detail and "'embed'" in detail, (
        f"the refusal must name the missing model, the kind and the kinds with a default: {detail!r}")
    assert out.get("answer") is None and not built, f"something was dialed: {built} {out}"
    print("ok test_a_generate_request_naming_no_model_is_refused_before_any_dial")


def test_a_request_naming_a_model_passes_it_through():
    out, built = _resolve({"kind": "generate", "prompt": "a", "model": "qwen2.5:7b"})
    assert built == ["qwen2.5:7b"], f"the named model did not pass through: {built}"
    assert out.get("outcome") != "refused", f"a named-model request was refused: {out}"
    print("ok test_a_request_naming_a_model_passes_it_through")


def test_a_default_that_does_not_serve_its_kind_is_refused_at_load():
    from cairn.devices.inference_domain.machines.route.route import RouteRefused, load_stacks
    d = Path(tempfile.mkdtemp(prefix="proof-959b-stacks-"))
    try:
        for f in _STACKS.glob("*.json"):
            shutil.copy(f, d / f.name)
        models = json.loads((d / "models.json").read_text())
        models["kind_defaults"] = {"generate": "nomic-embed-text"}
        (d / "models.json").write_text(json.dumps(models))
        try:
            load_stacks(d)
        except RouteRefused as exc:
            msg = str(exc)
            assert "generate" in msg and "nomic-embed-text" in msg, f"refusal names neither: {msg!r}"
        else:
            raise AssertionError("a default whose model does not serve its kind loaded cleanly")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("ok test_a_default_that_does_not_serve_its_kind_is_refused_at_load")


def test_the_existing_inference_domain_proofs_stay_green():
    for rel in ("cairn/devices/inference_domain/proofs/test_resolve_verb.py",
                "cairn/devices/inference_domain/machines/route/proofs/test_route.py"):
        r = subprocess.run([sys.executable, str(_REPO_ROOT / rel)], cwd=_REPO_ROOT,
                           capture_output=True, text=True, timeout=600)
        assert r.returncode == 0, f"{rel} reds: rc={r.returncode}\n{r.stdout[-800:]}{r.stderr[-800:]}"
    print("ok test_the_existing_inference_domain_proofs_stay_green")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
