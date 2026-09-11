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

from cairn.devices.inference_domain.probes import an_agent_retry_gets_a_fresh_sample as watch

_ERA = watch._ERA
_AFTER = _ERA + timedelta(hours=1)
_BEFORE = _ERA - timedelta(hours=1)

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
    p = watch.PROBE
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
    rows = [_row(_TOOLED, "miss", _AFTER)] * 3 + [_row(_TOOLED, "hit", _AFTER)]
    s = watch.judge(rows)
    assert s["tool_carrying_hits"] == 1, s
    assert s["replayed_to_an_agent"], "the finding must NAME the question that was replayed"

    # The control that makes the line above a measurement rather than a tautology: the same
    # store with the hit removed must NOT fire. Without this, a trigger hard-wired to True
    # would pass the assertion above.
    clean = watch.judge([_row(_TOOLED, "miss", _AFTER)] * 4)
    assert clean["tool_carrying_hits"] == 0 and not clean["replayed_to_an_agent"], clean

    ctx.clear()
    assert watch._trigger(None, {"corpus": s}) is True
    assert watch._trigger(None, {"corpus": clean}) is False


def test_a_bare_chat_hit_is_not_the_finding():
    """The toolset is read off the CANONICAL TEXT. A cached ordinary chat is the cache WORKING,
    and counting it would make the watch fire on its own device's whole reason for existing."""
    s = watch.judge([_row(_BARE, "hit", _AFTER)] * 9)
    assert s["tool_carrying_calls"] == 0 and s["tool_carrying_hits"] == 0, s


def test_the_era_floor_refuses_to_count_an_impossibility():
    """Before this build the chat branch sent no `tools` key, so a pre-era toolset row cannot
    exist. Counting one would mean the era floor had stopped floor-ing."""
    s = watch.judge([_row(_TOOLED, "hit", _BEFORE)] * 5)
    assert s["post_era_rows"] == 0 and s["tool_carrying_hits"] == 0, s


def test_the_clear_needs_the_floor_and_the_floor_is_the_TICKETS_number():
    """A watch that can clear before it can fire is not a watch. An empty store must NOT clear."""
    assert watch._enough({"corpus": watch.judge([])}) is False, \
        "an empty store must not clear — 0 hits out of 0 calls certifies nothing"

    just_under = watch.judge([_row(_TOOLED, "miss", _AFTER)] * (watch._ENOUGH - 1))
    assert watch._enough({"corpus": just_under}) is False, "one short of the floor is not enough"

    at_floor = watch.judge([_row(_TOOLED, "miss", _AFTER)] * watch._ENOUGH)
    assert watch._enough({"corpus": at_floor}) is True, "at the floor with no hits, it clears"

    with_hit = watch.judge([_row(_TOOLED, "miss", _AFTER)] * watch._ENOUGH
                           + [_row(_TOOLED, "hit", _AFTER)])
    assert watch._enough({"corpus": with_hit}) is False, \
        "traffic past the floor does NOT clear a watch that has a live finding"

    # THE NUMBER IS THE TICKET'S, NOT THE PROBE'S. It read 20 against a spec demanding 50 — a
    # probe grading itself easier than the spec it was compiled from. Pinned so lowering it is
    # a red here rather than a quiet edit.
    assert watch._ENOUGH == 50, \
        "548dd13fb4db's watchme spec says 50 toolset-carrying calls; the number moves in the " \
        "TICKET first and follows here, never the reverse"


def test_the_carry_reports_the_three_states_apart():
    """not-yet-judgeable, found, and clean must read DIFFERENTLY — Law 7 at a diagnostic surface."""
    thin = watch._carry({"corpus": watch.judge([_row(_TOOLED, "miss", _AFTER)])})
    found = watch._carry({"corpus": watch.judge([_row(_TOOLED, "hit", _AFTER)])})
    clean = watch._carry({"corpus": watch.judge([_row(_TOOLED, "miss", _AFTER)] * watch._ENOUGH)})
    texts = {thin["finding"], found["finding"], clean["finding"]}
    assert len(texts) == 3, "three states, three readings — a surface that collapses them lies"
    assert "not yet judgeable" in thin["finding"]
    assert "SERVED FROM THE STORE" in found["finding"]
    assert "none replayed" in clean["finding"]
    assert found["owning_ticket"], "the carry must name the ticket it answers to"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print("  ok  ", t.__name__)
    print(f"green: {len(tests)} teeth")


if __name__ == "__main__":
    main()
