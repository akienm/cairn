"""Proof: the agent-retry probe JUDGES fixture rows, and is armed in the gate's shape.

WHY THIS FILE EXISTS, and it is a hollow finding rather than a tidy-up. `cairn test --hollow
548dd13fb4db` reverted the build file by file and reported:

    HOLLOW cairn/devices/inference_domain/probes/an_agent_retry_gets_a_fresh_sample.py
           (removed (absent before the build)) -> no declared tooth redded

The probe could be deleted whole and every declared tooth of this ticket stayed green. That is
exactly the state Law 8 names: a file the build ships, that nothing can distinguish from its own
absence. The honest answer is a tooth, not an exemption — so the probe is measured here the way
does_the_route_leave_loopback is measured beside it: FIXTURE rows through `judge`, and the
emission gate's ARMED shape asserted directly.

The hollow build this proof is aimed at is a probe that exists, satisfies the ARMED shape, and
then judges nothing — a trigger that never fires on a real replayed call, a clear that fires on
an empty store, an era floor that counts a world where a toolset could not yet cross.

    python3 cairn/devices/inference_domain/proofs/test_the_agent_retry_probe_judges.py
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# THE SUBJECT IS RESOLVED AT CALL TIME, NEVER BOUND AT IMPORT — and that is a hollow finding
# about THIS FILE, made by the same instrument that made the one in the docstring. The first cut
# did `from ... import an_agent_retry_gets_a_fresh_sample as watch` at module level, so when the
# hollow check took the probe away the proof died at import and printed no teeth at all:
#
#     UNRAN ... probes/an_agent_retry_gets_a_fresh_sample.py (removed (absent before the build))
#           [1 proof(s) printed no teeth at all — did not reach a check]
#
# A crash before the first check says NOTHING about whether a tooth covers the file — it is
# indistinguishable from a timeout or a typo, which is exactly the reading Law 7 forbids a
# diagnostic surface to collapse. Resolved here instead, so a missing probe REDS the named teeth
# by name rather than silencing them.
def _w():
    """The probe module, imported on each call. A missing subject raises INSIDE a tooth."""
    import importlib
    return importlib.import_module(
        "cairn.devices.inference_domain.probes.an_agent_retry_gets_a_fresh_sample")


def _after():
    return _w()._ERA + timedelta(hours=1)


def _before():
    return _w()._ERA - timedelta(hours=1)

_TOOLED = '{"kind":"chat","messages":[{"content":"go","role":"user"}],"tools":[{"function":{"name":"terminal"}}]}'
_BARE = '{"kind":"chat","messages":[{"content":"go","role":"user"}]}'


# WHICH CLAUSE OF 548dd13fb4db'S FALSIFIER EACH TOOTH PROVES. The ticket's WATCHME is what
# carries clause (e) out of the fixture world and into live traffic, so the clause this proof
# owns is the watch's own arming: the instrument that will answer "did a byte-identical agent
# retry get a fresh sample in the wild" must itself be capable of saying no.
PROVES = {
    "548dd13fb4db": {
        "the_watch_can_say_no": "test_a_replayed_tool_carrying_call_is_the_finding",
        "the_watch_is_armed": "test_the_probe_is_armed_in_the_emission_gates_shape",
    }
}


def _row(canonical, verdict, created):
    return {"canonical": canonical, "verdict": verdict, "created": created}


def test_the_probe_is_armed_in_the_emission_gates_shape():
    """The gate resolves ARMED from a module-level frozen Probe carrying a carry AND an enough."""
    p = _w().PROBE
    assert dataclasses.is_dataclass(p) and getattr(type(p), "__dataclass_params__").frozen, \
        "PROBE must be a FROZEN dataclass — a probe whose trigger can be reassigned at runtime " \
        "is a watch that can be disarmed without a record"
    assert callable(p.trigger) and callable(p.carry) and callable(p.enough), \
        "trigger, carry and enough are all required — a probe that fires and reports nothing " \
        "teaches nobody, and one that cannot clear watches forever"
    assert p.to == "inference_domain", "a probe berths with WHAT IT WATCHES"


def test_a_replayed_tool_carrying_call_is_the_finding():
    """ONE post-era hit on a toolset-carrying call fires the trigger. There is no rate to be
    patient about: a replayed tool_call is the hang, and it surfaces as no error anywhere."""
    ctx = {}
    rows = [_row(_TOOLED, "miss", _after())] * 3 + [_row(_TOOLED, "hit", _after())]
    s = _w().judge(rows)
    assert s["tool_carrying_hits"] == 1, s
    assert s["replayed_to_an_agent"], "the finding must NAME the question that was replayed"

    # The control that makes the line above a measurement rather than a tautology: the same
    # store with the hit removed must NOT fire. Without this, a trigger hard-wired to True
    # would pass the assertion above.
    clean = _w().judge([_row(_TOOLED, "miss", _after())] * 4)
    assert clean["tool_carrying_hits"] == 0 and not clean["replayed_to_an_agent"], clean

    ctx.clear()
    assert _w()._trigger(None, {"corpus": s}) is True
    assert _w()._trigger(None, {"corpus": clean}) is False


def test_a_bare_chat_hit_is_not_the_finding():
    """The toolset is read off the CANONICAL TEXT. A cached ordinary chat is the cache WORKING,
    and counting it would make the watch fire on its own device's whole reason for existing."""
    s = _w().judge([_row(_BARE, "hit", _after())] * 9)
    assert s["tool_carrying_calls"] == 0 and s["tool_carrying_hits"] == 0, s


def test_the_era_floor_refuses_to_count_an_impossibility():
    """Before this build the chat branch sent no `tools` key, so a pre-era toolset row cannot
    exist. Counting one would mean the era floor had stopped floor-ing."""
    s = _w().judge([_row(_TOOLED, "hit", _before())] * 5)
    assert s["post_era_rows"] == 0 and s["tool_carrying_hits"] == 0, s


def test_the_clear_needs_the_floor_and_the_floor_is_the_TICKETS_number():
    """A watch that can clear before it can fire is not a watch. An empty store must NOT clear."""
    assert _w()._enough({"corpus": _w().judge([])}) is False, \
        "an empty store must not clear — 0 hits out of 0 calls certifies nothing"

    just_under = _w().judge([_row(_TOOLED, "miss", _after())] * (_w()._ENOUGH - 1))
    assert _w()._enough({"corpus": just_under}) is False, "one short of the floor is not enough"

    at_floor = _w().judge([_row(_TOOLED, "miss", _after())] * _w()._ENOUGH)
    assert _w()._enough({"corpus": at_floor}) is True, "at the floor with no hits, it clears"

    with_hit = _w().judge([_row(_TOOLED, "miss", _after())] * _w()._ENOUGH
                           + [_row(_TOOLED, "hit", _after())])
    assert _w()._enough({"corpus": with_hit}) is False, \
        "traffic past the floor does NOT clear a watch that has a live finding"

    # THE NUMBER IS THE TICKET'S, NOT THE PROBE'S. It read 20 against a spec demanding 50 — a
    # probe grading itself easier than the spec it was compiled from. Pinned so lowering it is
    # a red here rather than a quiet edit.
    assert _w()._ENOUGH == 50, \
        "548dd13fb4db's watchme spec says 50 toolset-carrying calls; the number moves in the " \
        "TICKET first and follows here, never the reverse"


def test_the_carry_reports_the_three_states_apart():
    """not-yet-judgeable, found, and clean must read DIFFERENTLY — Law 7 at a diagnostic surface."""
    thin = _w()._carry({"corpus": _w().judge([_row(_TOOLED, "miss", _after())])})
    found = _w()._carry({"corpus": _w().judge([_row(_TOOLED, "hit", _after())])})
    clean = _w()._carry({"corpus": _w().judge([_row(_TOOLED, "miss", _after())] * _w()._ENOUGH)})
    texts = {thin["finding"], found["finding"], clean["finding"]}
    assert len(texts) == 3, "three states, three readings — a surface that collapses them lies"
    assert "not yet judgeable" in thin["finding"]
    assert "SERVED FROM THE STORE" in found["finding"]
    assert "none replayed" in clean["finding"]
    assert found["owning_ticket"], "the carry must name the ticket it answers to"


def main():
    """EVERY TOOTH RUNS, AND A FAILURE PRINTS ITS NAME BESIDE A RED MARKER.

    A runner that stops at the first raise prints nothing for the teeth behind it, and the
    reader — here, cairn test --hollow's teeth_printed — cannot tell "this tooth failed" from
    "this proof never ran". Measured: with the probe reverted away, the stop-at-first shape
    reported `1 proof(s) printed no teeth at all`, which is the diagnostic collapse Law 7
    forbids. Printing FAIL per tooth is what makes a reverted subject a READING.
    """
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    red = []
    for t in tests:
        try:
            t()
        except BaseException as exc:                       # noqa: BLE001 — a crash is a red
            red.append(t.__name__)
            print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}")
        else:
            print("  ok   ", t.__name__)
    if red:
        print(f"red: {len(red)} of {len(tests)} teeth — {', '.join(red)}")
        return 1
    print(f"green: {len(tests)} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
