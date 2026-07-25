"""WHAT RIDES ALONG is a carrier — a callable, not a named kind.

Akien, 2026-07-25: "a gate watching callback will send a copy of it's ticket thru... but
something inside of the inference proxy may send back a loop count over n or something. they
are designed to be that flexible. so a gate callback can say 'call dave back with "ticket
detected at {gatename} as {ticket}"' whatever the callback can process in that location."

WHAT THIS PROVES:
  - CARRIAGE IS OPEN, NOT AN ENUM. Any ``(context) -> dict`` is a carrier; the shipped three
    are ordinary functions, and a fourth needs no schema change. Same anti-reification the
    trigger already got — one idea, one spelling.
  - THE THREE RIDES ARE REAL AND DIFFERENT. pointer (Law 6 default: only the address leaves),
    deep copy (the receiver cannot reach back and mutate the original), text (a receiver whose
    only vocabulary is a string).
  - THE MOMENT BEATS THE DECLARATION. The carrier runs at FIRE time against the context the
    trigger just saw, and its fragment merges OVER the static body.
  - THE DECLARATION NEVER DRIFTS. The callback is frozen; firing it twice against different
    contexts leaves ``body`` untouched.
  - A BROKEN CARRIER DOES NOT SWALLOW THE POKE (Law 7 / no silent failure). The poke lands
    carrying ``carry_failed``, and a template hole renders visibly rather than raising.

    python3 cairn/base/proofs/test_callback_carry.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cairn.base.callback import Callback, by_copy, by_pointer, by_text

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_bus_traffic_{_NONCE}"     # the ephemeral transit table this proof owns


def _cleanup() -> None:
    from cairn.db_domain import store
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()

ALWAYS = lambda now, ctx: True   # noqa: E731 — a trigger is a predicate, not a kind


def _cb(**kw):
    return Callback(why="a gate was crossed", trigger=ALWAYS, to="dave", **kw)


def test_no_carrier_says_only_that_the_line_was_crossed():
    cb = _cb(body={"gate": "PROVEME"})
    assert cb.payload({"ticket": {"id": "T-1", "secret": "owned"}}) == {"gate": "PROVEME"}, \
        "absent a carrier, nothing rides along — the poke is bare by default"


def test_by_pointer_sends_the_address_and_nothing_else():
    cb = _cb(carry=by_pointer("ticket"))
    out = cb.payload({"ticket": {"id": "T-1", "secret": "owned data that stays home"}})
    assert out == {"pointer": "T-1"}
    assert "secret" not in str(out), "the cheap, safe ride: owned data does not leave (Law 6)"


def test_by_pointer_passes_a_bare_id_through():
    assert _cb(carry=by_pointer("ticket")).payload({"ticket": "T-9"}) == {"pointer": "T-9"}


def test_by_copy_sends_the_artifact_and_it_is_deep():
    ticket = {"id": "T-2", "gates": ["BUILDME"]}
    out = _cb(carry=by_copy("ticket")).payload({"ticket": ticket})
    assert out["ticket"] == ticket, "the whole artifact rides — the deliberate Law 6 choice"
    out["ticket"]["gates"].append("MUTATED")
    assert ticket["gates"] == ["BUILDME"], \
        "DEEP — the receiver can never reach back through the payload and change the original"


def test_by_text_renders_the_artifact_in_motion():
    cb = _cb(carry=by_text("ticket detected at {gate} as {ticket}"))
    out = cb.payload({"gate": "PROVEME", "ticket": "T-3"})
    assert out == {"text": "ticket detected at PROVEME as T-3"}, "Akien's example, literally"


def test_a_template_hole_is_visible_not_fatal():
    out = _cb(carry=by_text("at {gate} as {ticket}")).payload({"gate": "PROVEME"})
    assert out["text"] == "at PROVEME as {missing:ticket}", \
        "a typo must not lose the poke; the hole shows in the text instead (Law 7)"


def test_the_carrier_runs_at_fire_time_and_wins_over_the_static_body():
    cb = _cb(body={"gate": "declared-long-ago", "why_static": "kept"},
             carry=by_pointer("ticket", as_="gate"))
    out = cb.payload({"ticket": "measured-at-the-gate"})
    assert out["gate"] == "measured-at-the-gate", \
        "the moment beats the declaration — a stale static value never masks what was measured"
    assert out["why_static"] == "kept", "the rest of the static body survives"


def test_the_frozen_declaration_does_not_drift_across_firings():
    body = {"gate": "PROVEME"}
    cb = _cb(body=body, carry=by_copy("ticket"))
    cb.payload({"ticket": {"id": "A"}})
    cb.payload({"ticket": {"id": "B"}})
    assert cb.body == {"gate": "PROVEME"} and body == {"gate": "PROVEME"}, \
        "a declaration that mutated per firing would stop being a declaration"


def test_any_callable_is_a_carrier_not_a_named_kind():
    """The loop-count case: what rides back is not an artifact at all."""
    out = _cb(carry=lambda ctx: {"loops": ctx["n"], "over": ctx["n"] > 5}).payload({"n": 9})
    assert out == {"loops": 9, "over": True}, "a fourth carriage is a fourth function"


def test_a_broken_carrier_still_lands_the_poke_and_says_so():
    def boom(context):
        raise RuntimeError("the artifact was gone")
    out = _cb(body={"gate": "PROVEME"}, carry=boom).payload({})
    assert out["gate"] == "PROVEME", "the poke LANDS — a broken carrier is not a lost message"
    assert out["carry_failed"] == "RuntimeError: the artifact was gone", "and it lands LOUD"


def test_a_carrier_returning_a_non_dict_is_caught_the_same_way():
    out = _cb(carry=lambda ctx: "just a string").payload({})
    assert "carry_failed" in out and "str" in out["carry_failed"]


def test_a_non_callable_carry_is_refused_at_construction():
    try:
        _cb(carry={"ticket": "T-1"})
    except TypeError as e:
        assert "callable" in str(e), e
    else:
        raise AssertionError("a named-kind carry must be refused at n=1, not discovered at fire")


def test_the_shim_fires_the_carrier_against_the_pulse_context():
    """End to end: the poke that reaches the bus carries what the trigger just saw."""
    from cairn.base.shim import BaseShim
    from cairn.bus.bus import BusDevice

    seen = {"ticket": {"id": "T-7", "gate": "PROVEME"}}

    class _Shim(BaseShim):
        @property
        def device_id(self) -> str:
            return "watcher"

        def callbacks(self):
            return [Callback(why="gate watch", trigger=lambda now, ctx: "ticket" in ctx,
                             to="dave", carry=by_text("ticket detected at {gate} as {ticket}"))]

    # An EPHEMERAL transit table this proof owns — the durable bus is shared, so counting a
    # live channel would pin a legitimately-moving value and go red on the second run.
    bus = BusDevice(table=_TABLE)
    try:
        shim = _Shim(bus=bus)
        shim.on_pulse(now="2026-07-25", context={**seen, "gate": "PROVEME"})
        posted = bus.read(to="dave", channel="personal")
        assert len(posted) == 1, f"one fire, one poke — got {len(posted)}"
        assert posted[0]["body"]["text"] == \
            "ticket detected at PROVEME as {'id': 'T-7', 'gate': 'PROVEME'}", posted[0]["body"]
    finally:
        _cleanup()


TESTS = [
    test_no_carrier_says_only_that_the_line_was_crossed,
    test_by_pointer_sends_the_address_and_nothing_else,
    test_by_pointer_passes_a_bare_id_through,
    test_by_copy_sends_the_artifact_and_it_is_deep,
    test_by_text_renders_the_artifact_in_motion,
    test_a_template_hole_is_visible_not_fatal,
    test_the_carrier_runs_at_fire_time_and_wins_over_the_static_body,
    test_the_frozen_declaration_does_not_drift_across_firings,
    test_any_callable_is_a_carrier_not_a_named_kind,
    test_a_broken_carrier_still_lands_the_poke_and_says_so,
    test_a_carrier_returning_a_non_dict_is_caught_the_same_way,
    test_a_non_callable_carry_is_refused_at_construction,
    test_the_shim_fires_the_carrier_against_the_pulse_context,
]

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
