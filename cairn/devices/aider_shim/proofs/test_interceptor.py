#!/usr/bin/env python3
"""Teeth on the interceptor: the surface is complete, and the door is the only road.

A HOLLOW BUILD COULD NOT PASS THESE. The one that matters most is
``test_touched_is_not_empty``: every other assertion here about "no host was touched" is
satisfiable by a run in which nothing happened at all, and a green earned that way is
worse than a red because a peer leans on it (Law 8's why). So the touched-attribute set
is asserted NON-EMPTY before it is asserted to be a subset.

No network, by construction: the ``resolve`` and ``resolver`` seams are injected, so this
file passes identically inside and outside a netns. That equality is itself checked by the
voyage's close, not here.
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.aider_shim import interceptor  # noqa: E402
from cairn.devices.aider_shim.fence import AskWidened, Fence, SeenLog  # noqa: E402

FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"  ok   {name}")
    except Exception:
        FAILURES.append(name)
        print(f"  FAIL {name}")
        traceback.print_exc()


def fake_door(answer_text="ok", counters=None, provider="hex", hit=False):
    """A stand-in for ``domain.resolve`` that records what it was handed."""
    seen = []

    def resolve(request, *, resolver, **_kw):
        seen.append(request)
        prov = {"provider": provider, "domain": "coding", "model": request.get("model")}
        if counters:
            prov["counters"] = counters
        return {"answer": {"text": answer_text, "role": "assistant"}, "hit": hit,
                "canonical": "c", "cost": 17, "provenance": prov}

    resolve.seen = seen
    return resolve


def fresh(**kw):
    kw.setdefault("resolve", fake_door())
    kw.setdefault("resolver", object())
    kw.setdefault("log", SeenLog())
    return interceptor.build(**kw)


# --------------------------------------------------------------- the surface is whole

def test_surface_is_complete():
    mod = fresh()
    missing = [n for n in interceptor.SURFACE if not hasattr(mod, n)]
    assert not missing, f"surface incomplete: {missing}"


def test_every_exception_name_is_a_catchable_class():
    mod = fresh()
    names, _ = interceptor._exception_names()
    assert names, "no exception names resolved at all"
    for n in names:
        cls = getattr(mod, n, None)
        assert isinstance(cls, type) and issubclass(cls, BaseException), \
            f"{n} is not a catchable exception class"


def test_no_stray_Error_attribute():
    """``LiteLLMExceptions._load`` raises ValueError on any ``*Error`` it does not know.

    It also calls ``issubclass`` on it unguarded, so a NON-class attribute ending in
    ``Error`` would raise TypeError instead. Both break aider at first use, so the surface
    must carry no ``*Error`` name outside the declared list.
    """
    mod = fresh()
    names, _ = interceptor._exception_names()
    strays = [n for n in dir(mod) if n.endswith("Error") and n not in names]
    assert not strays, f"stray *Error attributes would break aider's exception load: {strays}"


def test_the_refusal_is_outside_aiders_retry_tuple():
    """``AskWidened`` must not be catchable as a litellm exception, or it gets retried."""
    mod = fresh()
    names, _ = interceptor._exception_names()
    tup = tuple(getattr(mod, n) for n in names)
    assert not issubclass(AskWidened, tup), \
        "AskWidened is inside aider's exceptions_tuple — a refusal would be retried to timeout"
    assert not AskWidened.__name__.endswith("Error"), \
        "the refusal's name ends in Error, which aider's dir(litellm) walk would reject"


# --------------------------------------------------------------- the door is the road

def test_completion_goes_through_the_resolve_door():
    door = fake_door(answer_text="hello")
    mod = fresh(resolve=door)
    res = mod.completion(model="qwen3-coder:30b",
                         messages=[{"role": "user", "content": "hi"}])
    assert len(door.seen) == 1, "the door was not called exactly once"
    req = door.seen[0]
    assert req["kind"] == "chat", f"wrong verb: {req['kind']!r}"
    assert req["messages"] == [{"role": "user", "content": "hi"}]
    assert res.choices[0].message.content == "hello"


def test_usage_is_none_when_the_door_reports_no_counters():
    """A cache hit carries no counters. Inventing them would be a Law 7 breach."""
    mod = fresh(resolve=fake_door(hit=True))
    res = mod.completion(model="qwen3-coder:30b", messages=[{"role": "user", "content": "x"}])
    assert res.usage is None, "usage was fabricated for a call that never touched the host"


def test_usage_is_the_hosts_real_counters_when_reported():
    mod = fresh(resolve=fake_door(counters={"prompt_eval_count": 15, "eval_count": 2}))
    res = mod.completion(model="qwen3-coder:30b", messages=[{"role": "user", "content": "x"}])
    assert res.usage.prompt_tokens == 15 and res.usage.completion_tokens == 2, \
        f"counters did not ride through: {res.usage.prompt_tokens}/{res.usage.completion_tokens}"


def test_streaming_is_refused_not_silently_downgraded():
    mod = fresh()
    try:
        mod.completion(model="qwen3-coder:30b", messages=[{"role": "user", "content": "x"}],
                       stream=True)
    except AskWidened:
        return
    raise AssertionError("a streaming request was served — it must be refused loudly")


# --------------------------------------------------------------- the anti-hollow tooth

def test_touched_is_not_empty():
    """THE ANTI-HOLLOW TOOTH. Every 'no host was touched' claim passes when nothing ran."""
    mod = fresh()
    mod.completion(model="qwen3-coder:30b", messages=[{"role": "user", "content": "x"}])
    assert mod._cairn_touched, \
        "the touched-attribute set is EMPTY — nothing exercised the surface, so every " \
        "other green in this file was earned by inactivity"
    assert "completion" in mod._cairn_touched


def test_touched_stays_inside_the_declared_surface():
    mod = fresh()
    mod.completion(model="qwen3-coder:30b", messages=[{"role": "user", "content": "x"}])
    mod.get_model_info("qwen3-coder:30b")
    mod.validate_environment("qwen3-coder:30b")
    mod.token_counter(model="qwen3-coder:30b", messages=[{"role": "user", "content": "x"}])
    names, _ = interceptor._exception_names()
    allowed = set(interceptor.SURFACE) | set(names) | {
        "model_cost", "suppress_debug_info", "set_verbose", "drop_params"}
    stray = mod._cairn_touched - allowed
    assert not stray, f"aider-facing code reached attributes outside the declared surface: {stray}"


# --------------------------------------------------------------- the constants surface

def test_model_info_answers_from_the_stack_and_refuses_otherwise():
    mod = fresh()
    info = mod.get_model_info("qwen3-coder:30b")
    assert info["input_cost_per_token"] == 0.0
    try:
        mod.get_model_info("gpt-4o")
    except KeyError:
        return
    raise AssertionError("a model absent from the stack was answered for")


def test_model_cost_is_a_mapping_aider_can_walk():
    mod = fresh()
    assert "qwen3-coder:30b" in mod.model_cost.keys()
    assert dict(mod.model_cost.items())["qwen3-coder:30b"]["mode"] == "chat"


def test_fallback_exception_list_matches_the_foreign_programs_own():
    """The fallback is a COPY of aider's list, and a copy drifts silently.

    Read by AST rather than by import, deliberately: aider is not importable until the
    venv exists (piece 4, which needs Akien's answer), and a check that only runs after
    that is a check that never guarded the window it was written for. Reading aider's
    bytes is inside constrain's bounds; writing them is not.
    """
    import ast
    src = Path.home() / "dev" / "src" / "aider" / "aider" / "exceptions.py"
    assert src.exists(), \
        f"the held foreign program is not at its declared address: {src} — this device " \
        "is defined against a checkout that is no longer there"
    for node in ast.walk(ast.parse(src.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", None) == "EXCEPTIONS" for t in node.targets):
            theirs = tuple(el.args[0].value for el in node.value.elts)
            break
    else:
        raise AssertionError("aider/exceptions.py no longer declares EXCEPTIONS")
    assert interceptor.EXCEPTION_NAMES == theirs, \
        f"the fallback list has drifted from aider's.\n  ours only: " \
        f"{sorted(set(interceptor.EXCEPTION_NAMES) - set(theirs))}\n  theirs only: " \
        f"{sorted(set(theirs) - set(interceptor.EXCEPTION_NAMES))}"


def test_install_puts_us_at_the_import_name():
    """The correction this build measured: the slot is not enough, sys.modules is."""
    before = sys.modules.get("litellm")
    try:
        mod = interceptor.install(resolve=fake_door(), resolver=object(), log=SeenLog())
        assert sys.modules["litellm"] is mod
        assert interceptor.installed(), "installed() cannot see its own installation"
    finally:
        if before is None:
            sys.modules.pop("litellm", None)
        else:
            sys.modules["litellm"] = before


def test_installed_is_FALSE_when_the_module_there_is_not_OURS():
    """THE NEGATIVE HALF, and it is the half that carries the falsifier.

    ``installed()`` is the instrument for falsifier clause (1) — 'the real litellm appears
    in sys.modules after a driven run'. An instrument that only ever reports success is not
    an instrument, and this device would have shipped one: a mutation reducing ``installed``
    from an identity check to ``'litellm' in sys.modules`` survived the whole proof file,
    because nothing here had ever put a foreign module at that name and demanded a False.
    So this test does exactly that. If the real litellm ever loads, the shim must be able
    to SAY so — that is the entire value of the check.
    """
    import types as _types
    before = sys.modules.get("litellm")
    try:
        sys.modules["litellm"] = _types.ModuleType("litellm")  # a stand-in for the real one
        assert not interceptor.installed(), \
            "installed() reports True for a module that is NOT ours — it is a presence " \
            "check wearing an identity check's name, and falsifier clause (1) is blind"
        sys.modules.pop("litellm", None)
        assert not interceptor.installed(), "installed() reports True for nothing at all"
    finally:
        if before is None:
            sys.modules.pop("litellm", None)
        else:
            sys.modules["litellm"] = before


def main():
    print("aider_shim :: interceptor")
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            check(name, fn)
    if FAILURES:
        print(f"\nRED — {len(FAILURES)} failure(s): {FAILURES}")
        return 1
    print("\nGREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
