"""ONE SURVEY PER PULSE — the context convention that only ever READ, made to write.

Ticket ``9579a6f9cec6`` (2026-09-07). Every probe in the corpus is written
``s = context.get("survey") or survey()``, a line that reads as though the pulse hands the
survey down. NOTHING HAS EVER POPULATED THAT CONTEXT — ``beat`` does ``context = context or
{}`` and ``__main__`` passes none — so all 164 call sites took the ``or`` branch on every
beat, and a probe that FIRES took it three times over (``fires``, then ``payload`` -> carry,
then ``gathered_enough`` -> enough). Measured beat before this: 104.8s, of which trigger
57.5s, carry 24.0s, enough 22.6s, and 0.7s for everything the loop itself does.

WHAT THIS PROVES, and every tooth is pointed at a way a memo goes wrong rather than at the
speed — a fast wrong answer is the worse defect (Law 8):

  - IT COMPUTES ONCE PER CONTEXT. The whole point, and the only thing invisible in the
    answers: a memo that quietly recomputes returns exactly what a working one returns.
  - AN INJECTED VALUE STILL WINS. Hand-injection is a live seam — proofs and ``__main__``
    blocks pass a synthetic survey to drive a branch without building the world — so this is
    a strict superset of the line it replaces, not a replacement for it.
  - TWO PROBES SPELLING THEIR SLOT ``"survey"`` DO NOT GET EACH OTHER'S WORLD. 24 of them
    do spell it that way. A memo keyed on the caller's chosen word alone would serve the
    first probe's corpus to the second, and every answer downstream would be confidently
    wrong.
  - A FRESH CONTEXT RECOMPUTES. The memo must not outlive the pulse: ``beat`` builds a new
    dict each time, and a survey that persisted across beats would be a watch reporting on
    a world that has moved.
  - A RAISE IS NOT MEMOIZED. A survey that blew up is not an answer, and caching one would
    turn a transient read failure into a pulse-long lie.
  - THE THREE PREDICATES OF ONE FIRING PROBE SEE ONE WORLD — end to end through a real
    ``Probe``, because that is the claim that matters and it is not the same claim as
    "the helper memoizes". A carry reporting different numbers than the trigger tested is a
    defect in its own right, and this closes it as a side effect worth asserting.
  - THE CONTEXT IS NOT MUTATED WHERE A PROBE CAN SEE IT. The memo berths under one reserved
    key, so a probe reading ``context`` for its own injected values finds exactly what was
    put there.
"""
from __future__ import annotations

import sys

from cairn.tools.base.probe import Probe, once


class _Counted:
    """A survey that says how many times it has actually been derived."""

    def __init__(self, tag="s"):
        self.tag, self.calls = tag, 0

    def __call__(self):
        self.calls += 1
        return {"tag": self.tag, "derived": self.calls}


def test_computes_once_per_context():
    s, ctx = _Counted(), {}
    first = once(ctx, "survey", s)
    for _ in range(50):
        assert once(ctx, "survey", s) == first
    assert s.calls == 1, f"derived {s.calls} times over one pulse — that is not a memo"


def test_an_injected_value_still_wins():
    s = _Counted()
    got = once({"survey": {"tag": "INJECTED"}}, "survey", s)
    assert got == {"tag": "INJECTED"}, got
    assert s.calls == 0, "the seam is gone: an injected survey was ignored and rebuilt"


def test_two_computes_sharing_a_key_do_not_collide():
    """24 probes spell their slot ``"survey"``. Keyed on that word alone, the second would
    be served the first one's world."""
    a, b, ctx = _Counted("probe-a"), _Counted("probe-b"), {}
    assert once(ctx, "survey", a)["tag"] == "probe-a"
    assert once(ctx, "survey", b)["tag"] == "probe-b", "one probe was served another's world"
    assert (a.calls, b.calls) == (1, 1)


def test_a_fresh_context_recomputes():
    s = _Counted()
    once({}, "survey", s)
    once({}, "survey", s)
    once(None, "survey", s)
    assert s.calls == 3, (
        f"derived {s.calls} times over three separate pulses — the memo outlived its beat, "
        "and a watch reading a stale world is worse than a slow one")


def test_a_raise_is_not_memoized():
    calls = []

    def boom():
        calls.append(1)
        raise RuntimeError("the corpus went away")

    ctx = {}
    for _ in range(3):
        try:
            once(ctx, "survey", boom)
        except RuntimeError:
            pass
        else:
            raise AssertionError("the raise was swallowed — a broken survey must be loud")
    assert len(calls) == 3, "a failed survey was cached as though it were an answer"


def test_one_firing_probe_sees_ONE_world_across_all_three_predicates():
    """End to end through a real Probe: trigger, carry and enough must agree, because a
    carry reporting numbers the trigger never tested is its own defect."""
    s = _Counted()
    seen = {}

    def trigger(now, context):
        seen["trigger"] = once(context, "survey", s)
        return True

    def carry(context):
        seen["carry"] = once(context, "survey", s)
        return {"n": seen["carry"]["derived"]}

    def enough(context):
        seen["enough"] = once(context, "survey", s)
        return False

    p = Probe(why="one world per pulse", trigger=trigger, to="nobody",
              body={}, carry=carry, enough=enough)
    ctx = {}
    assert p.fires(None, ctx) is True
    payload = p.payload(ctx)
    assert p.gathered_enough(ctx) is False
    assert s.calls == 1, f"one firing probe derived its survey {s.calls} times"
    assert seen["trigger"] is seen["carry"] is seen["enough"], seen
    assert payload["n"] == 1, payload


def test_the_memo_does_not_shadow_a_probes_own_context_keys():
    ctx = {"root": "/somewhere", "seen": 4}
    once(ctx, "survey", _Counted())
    assert ctx["root"] == "/somewhere" and ctx["seen"] == 4, ctx
    assert set(ctx) == {"root", "seen", "_once"}, (
        f"the memo scattered keys a probe could mistake for its own: {sorted(ctx)}")


def test_the_pulse_context_survives_the_shim_that_was_handed_it():
    """TWO PROBES IN DIFFERENT SHIMS SEE ONE WORLD — the claim that was silently false.

    ``beat`` builds ONE context and hands the same object to every shim, so a survey
    derived under shim A must be visible to a probe under shim B. Until 2026-09-07 it was
    not: ``on_pulse`` spelled ``context or {}``, the shared dict is empty and therefore
    falsy, and every shim quietly swapped in its own. Nothing could see it, because the
    convention only ever READ the context — the memo counter climbing and resetting once
    per shim across a live beat is what exposed it.

    This asserts the OWNERSHIP (Law 6), not the saving: the dict a caller passes is the
    dict the probes get. The saving follows from it and is measured elsewhere."""
    from cairn.tools.base.shim import BaseShim

    s = _Counted()
    seen = {}

    class _Shim(BaseShim):
        """A shim with one probe that memoizes into whatever context it is handed. Fired
        through the REAL ``on_pulse`` — calling ``Probe.fires`` directly would only re-prove
        ``_pulse``, which is the tooth above, and would leave the line under test untouched."""

        def __init__(self, tag):
            super().__init__(bus=None)
            self._tag = tag

        @property
        def device_id(self):
            return self._tag

        def probes(self):
            tag = self._tag

            def trigger(now, context):
                seen[tag] = once(context, "survey", s)
                return False        # never fires, so no bus poke is attempted

            return [Probe(why=f"probe under {tag}", trigger=trigger, to="nobody", body={})]

    shared = {}                     # EMPTY AND REAL — the exact shape that used to be lost
    for tag in ("shim-a", "shim-b"):
        _Shim(tag).on_pulse(None, shared)

    assert seen.keys() == {"shim-a", "shim-b"}, f"a probe never ran: {sorted(seen)}"
    assert seen["shim-a"] is seen["shim-b"], (
        "two shims in one beat derived the survey separately — the beat's context did not "
        "survive being handed to the shim")
    assert s.calls == 1, f"the survey was derived {s.calls} times across two shims"
    assert "_once" in shared, (
        "on_pulse wrote the memo into a dict the caller never sees — the context was "
        "substituted, which is the defect this tooth exists for")


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
