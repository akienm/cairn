#!/usr/bin/env python3
"""The money-fence's tooth: a widened ask is refused, recorded, and not retried.

THIS IS THE GATE THE CHARTER CALLS THE MONEY GATE, and the reason it is a separate file
from the interceptor's proof is that its failure mode is different in kind. The
interceptor's proof asks 'does the surface work'; a wrong answer there is a broken build.
This one asks 'can this device spend money it was not allowed to spend'; a wrong answer
here is a bill.

THE HOLLOW GREEN THIS FILE IS BUILT AGAINST. 'No widened ask was served' is satisfied
perfectly by a run in which no ask was made at all — the empty set has no
counterexamples. So every refusal case below ALSO asserts that the seen-log is non-empty
and that the widened name appears in it verbatim: the fence must be shown to have been
REACHED and to have REDDENED, never merely to have not-fired.

No network: the door is injected, and in the refusal cases the door is a tripwire that
raises if it is ever called — which is the assertion that the fence fires BEFORE the host,
not after.
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


class DoorNeverReached(AssertionError):
    """Raised BY the tripwire door. If a test sees this, the fence let an ask through."""


def tripwire(_request, *, resolver=None, **_kw):
    raise DoorNeverReached(
        "the inference door was called for an ask the fence should have refused — "
        "the fence fired late, or not at all"
    )


def serving_door(provider="hex"):
    def resolve(request, *, resolver=None, **_kw):
        return {"answer": {"text": "ok", "role": "assistant"}, "hit": False, "canonical": "c",
                "cost": 1, "provenance": {"provider": provider, "counters": {}}}
    return resolve


# --------------------------------------------------------- refused before the host

def test_a_widened_model_is_refused_before_the_door():
    log = SeenLog()
    mod = interceptor.build(resolve=tripwire, resolver=object(), log=log,
                            fence=Fence(models=("qwen3-coder:30b",)))
    try:
        mod.completion(model="gpt-4o", messages=[{"role": "user", "content": "x"}])
    except DoorNeverReached:
        raise AssertionError("THE FENCE WAS BYPASSED — a widened ask reached the door")
    except AskWidened as widened:
        assert "gpt-4o" in str(widened), \
            f"the refusal does not name what was refused: {widened}"
    else:
        raise AssertionError("a widened ask was SERVED — this is the money failure")

    # THE ANTI-HOLLOW HALF: the fence must be shown to have been reached, not merely
    # to have not-fired. An empty log here means nothing was asked and the green above
    # was earned by inactivity.
    assert log.entries, \
        "the seen-log is EMPTY — nothing reached the fence, so the refusal above proves nothing"
    assert "gpt-4o" in log.names(), \
        f"the widened name is not in the record: {log.names()}"
    assert log.refused(), "the ask was recorded, but not as a refusal"
    assert log.refused()[-1]["model"] == "gpt-4o"


def test_the_refusal_names_the_widened_model_verbatim_in_the_record():
    """Law 7 at a record of truth: the record may not smooth the refusal into a shape."""
    log = SeenLog()
    mod = interceptor.build(resolve=tripwire, resolver=object(), log=log)
    for name in ("gpt-4o", "claude-opus-5", "qwen3-coder:480b"):
        try:
            mod.completion(model=name, messages=[{"role": "user", "content": "x"}])
        except AskWidened:
            pass
    assert log.names() == ["gpt-4o", "claude-opus-5", "qwen3-coder:480b"], \
        f"the record does not carry each ask verbatim and in order: {log.names()}"
    for row in log.refused():
        assert row["model"] in row["detail"], \
            f"the recorded detail does not name the model it refused: {row}"


def test_a_widened_PROVIDER_is_refused_even_though_the_name_passed():
    """The route chooses a provider the name-check cannot see. That is the second half."""
    log = SeenLog()
    mod = interceptor.build(resolve=serving_door(provider="openai"), resolver=object(),
                            log=log, fence=Fence(providers=("hex",)))
    try:
        mod.completion(model="qwen3-coder:30b", messages=[{"role": "user", "content": "x"}])
    except AskWidened as widened:
        assert "openai" in str(widened)
    else:
        raise AssertionError("an off-fence provider served this device and was accepted")
    assert log.refused(), "the provider refusal was not recorded"
    assert log.refused()[-1]["provider"] == "openai"


def test_an_on_fence_ask_is_allowed_and_recorded_as_allowed():
    """The fence must not be a wall. A green that refuses everything is not a fence."""
    log = SeenLog()
    mod = interceptor.build(resolve=serving_door(), resolver=object(), log=log)
    mod.completion(model="qwen3-coder:30b", messages=[{"role": "user", "content": "x"}])
    assert log.entries and log.entries[-1]["verdict"] == "allowed", \
        f"an on-fence ask was not allowed: {log.entries}"
    assert not log.refused(), "an on-fence ask was refused — the fence is a wall"


# --------------------------------------------------------- not absorbed by the retry

def test_the_refusal_survives_aiders_retry_loop_unretried():
    """aider retries ``exceptions_tuple()`` with backoff to RETRY_TIMEOUT (60s).

    This drives the ACTUAL loop shape from aider's ``simple_send_with_retries``: catch the
    litellm exception tuple, sleep, retry. ``AskWidened`` must fall straight through it, so
    the ask is attempted exactly ONCE and the refusal reaches the caller intact.
    """
    log = SeenLog()
    mod = interceptor.build(resolve=tripwire, resolver=object(), log=log)
    names, _ = interceptor._exception_names()
    retryable = tuple(getattr(mod, n) for n in names)

    attempts = []

    def aiders_loop():
        while True:
            try:
                attempts.append(1)
                return mod.completion(model="gpt-4o",
                                      messages=[{"role": "user", "content": "x"}])
            except retryable:
                if len(attempts) > 3:
                    raise AssertionError("retried — the refusal was absorbed by the loop")
                continue

    try:
        aiders_loop()
    except AskWidened:
        pass
    else:
        raise AssertionError("the refusal did not propagate out of aider's retry loop")

    assert len(attempts) == 1, \
        f"the ask was attempted {len(attempts)} times — a refusal must not be retried"
    assert len(log.refused()) == 1, \
        f"the record shows {len(log.refused())} refusals for one ask — the loop re-asked"


def test_the_refusal_escapes_every_handler_on_aiders_actual_call_path():
    """THE INSTRUMENT FOR THE CHARTER'S PROSE CLAIM, derived rather than transcribed.

    The charter says the refusal "propagates out of aider untouched". That is a claim about
    aider's code, so the check reads aider's code: it parses the except-handlers inside
    ``simple_send_with_retries`` — the function that wraps every completion — and requires
    ``AskWidened`` to be caught by NONE of them.

    Deriving beats listing, and this build is why. The handler that matters was not the one
    the design was worried about: beside the retry tuple sits a bare ``except AttributeError:
    return None``, which would turn a refusal into "the model returned nothing" — silently,
    with no record and no red. That is falsifier clause (4), it is worse than the retry the
    fence was designed against, and a hand-written list of forbidden base classes would not
    have contained it because nobody knew to write it down. Re-derived each run, this tooth
    also survives aider changing its handlers under us.
    """
    import ast
    src = Path.home() / "dev" / "src" / "aider" / "aider" / "models.py"
    assert src.exists(), f"the held foreign program is not at its declared address: {src}"

    handlers = []
    for node in ast.walk(ast.parse(src.read_text(encoding="utf-8"))):
        if isinstance(node, ast.FunctionDef) and node.name == "simple_send_with_retries":
            for h in ast.walk(node):
                if isinstance(h, ast.ExceptHandler):
                    handlers.append(h)
    assert handlers, \
        "no except-handlers found in aider's simple_send_with_retries — the function was " \
        "renamed or restructured, and this tooth is measuring nothing"

    mod = interceptor.build(resolve=tripwire, resolver=object(), log=SeenLog())
    names, _ = interceptor._exception_names()

    caught_by = []
    for h in handlers:
        if h.type is None:
            caught_by.append(("bare except", (BaseException,)))
            continue
        expr = ast.unparse(h.type)
        if "exceptions_tuple" in expr:
            # Resolves off the litellm module — which is OURS once installed.
            caught_by.append((expr, tuple(getattr(mod, n) for n in names)))
        else:
            builtin = getattr(__builtins__, expr, None) if not isinstance(__builtins__, dict) \
                else __builtins__.get(expr)
            assert builtin is not None and isinstance(builtin, type), \
                f"aider catches {expr!r} on this path and this proof cannot resolve it — " \
                "the tooth cannot claim the refusal escapes what it cannot name"
            caught_by.append((expr, (builtin,)))

    swallowed = [expr for expr, tup in caught_by if issubclass(AskWidened, tup)]
    assert not swallowed, (
        f"AskWidened is caught by aider's own handler(s) {swallowed} — the refusal would be "
        "absorbed on the real call path, not raised to the caller"
    )
    print(f"       (checked against {len(caught_by)} handler(s): "
          f"{[e for e, _ in caught_by]})")


def test_streaming_is_refused_and_recorded():
    log = SeenLog()
    mod = interceptor.build(resolve=tripwire, resolver=object(), log=log)
    try:
        mod.completion(model="qwen3-coder:30b", messages=[{"role": "user", "content": "x"}],
                       stream=True)
    except DoorNeverReached:
        raise AssertionError("a streaming ask reached the door before being refused")
    except AskWidened:
        pass
    else:
        raise AssertionError("a streaming ask was served")
    assert log.refused(), "the streaming refusal left no record"


# --------------------------------------------------------- the fence itself

def test_the_fence_is_exact_match_never_a_prefix_or_pattern():
    """A pattern is how an allow-list widens without anyone deciding to widen it."""
    f = Fence(models=("qwen3-coder:30b",))
    for near in ("qwen3-coder", "qwen3-coder:30b-instruct", "Qwen3-Coder:30B",
                 "qwen3-coder:30b ", "openai/qwen3-coder:30b"):
        try:
            f.check_model(near)
        except AskWidened:
            continue
        raise AssertionError(f"{near!r} passed a fence pinned to 'qwen3-coder:30b'")
    f.check_model("qwen3-coder:30b")  # the exact name must still pass


def test_the_record_is_appended_to_disk_when_a_path_is_given():
    """The in-memory log is the proof's instrument; the FILE is the device's record."""
    import json
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "asks.jsonl"
        log = SeenLog(record_path=path)
        mod = interceptor.build(resolve=tripwire, resolver=object(), log=log)
        for name in ("gpt-4o", "claude-opus-5"):
            try:
                mod.completion(model=name, messages=[{"role": "user", "content": "x"}])
            except AskWidened:
                pass
        lines = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
        assert [r["model"] for r in lines] == ["gpt-4o", "claude-opus-5"], \
            f"the on-disk record does not match what was asked: {lines}"
        assert all(r["verdict"] == "refused" for r in lines)


def test_the_default_record_path_is_instance_space():
    """Law 6 and the three roots: no runtime state in class-space, ever."""
    from cairn.devices.aider_shim.fence import DEFAULT_RECORD
    assert str(DEFAULT_RECORD).startswith(str(Path.home() / ".cairn")), \
        f"the device's record berths outside instance-space: {DEFAULT_RECORD}"
    assert "dev/src/cairn" not in str(DEFAULT_RECORD), \
        "the device's record berths in class-space — no runtime state here, ever"


def main():
    print("aider_shim :: fence")
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
