"""Proof for the Callback primitive — "poke X when this trigger is true", immutable.

Teeth a hollow callback could not pass:
  - A TRIGGER IS ANY PREDICATE (the anti-reification). ``fires`` reflects an arbitrary
    callable — including one that CLOSES OVER owned data (Law 6): the data stays in the
    closure, only the true/false verdict comes out. A callback that only accepted a named
    "kind" (the deleted interval/date/quantity/state enum) could not do this.
  - IT IS IMMUTABLE (frozen) — a declaration, not a stateful worker.
  - CONSTRUCTION REFUSES A DEFECT LOUDLY (CP1/CP3): a non-callable trigger, a missing why,
    or a missing ``to`` is caught at n=1, not discovered when it silently never pokes.

Runnable bare (no DB, no framework):
    python3 cairn/base/proofs/test_callback.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.callback import Callback


def test_a_trigger_is_any_predicate_evaluated_where_owned():
    # Genuinely shared data (the moment) read from now/context.
    at_noon = Callback(why="lunch", trigger=lambda now, ctx: now == 12, to="cook/personal")
    assert at_noon.fires(12) and not at_noon.fires(11)

    # Device-LOCAL data: the predicate closes over an owned value; only the verdict escapes,
    # never the value itself (Law 6 for triggers). The reading stays home in the closure.
    owned = {"cpu": 95}  # stands in for a device's own, unexported metric
    over_80 = Callback(why="cpu is high", trigger=lambda now, ctx: owned["cpu"] >= 80,
                       to="ops/personal", body={"crossed": 80})
    assert over_80.fires(now=None) is True
    owned["cpu"] = 50
    assert over_80.fires(now=None) is False
    # The body carries only THAT the line was crossed — never the owned reading (95/50).
    assert "cpu" not in over_80.body and over_80.body == {"crossed": 80}


def test_it_is_immutable():
    cb = Callback(why="w", trigger=lambda n, c: True, to="x/personal")
    try:
        cb.to = "y/personal"  # type: ignore[misc]
        raise AssertionError("a callback is a declaration — it must be frozen")
    except FrozenInstanceError:
        pass


def test_construction_refuses_a_defect_loudly():
    try:
        Callback(why="w", trigger="not-callable", to="x/personal")  # type: ignore[arg-type]
        raise AssertionError("a non-callable trigger must be refused (a trigger is a predicate)")
    except TypeError:
        pass
    try:
        Callback(why="", trigger=lambda n, c: True, to="x/personal")
        raise AssertionError("a callback with no why must be refused (CP3)")
    except ValueError:
        pass
    try:
        Callback(why="w", trigger=lambda n, c: True, to="")
        raise AssertionError("a callback with no 'to' must be refused (CP1 — nothing to poke)")
    except ValueError:
        pass


def _main() -> int:
    for check in (test_a_trigger_is_any_predicate_evaluated_where_owned,
                  test_it_is_immutable, test_construction_refuses_a_defect_loudly):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — Callback: a trigger is any predicate (evaluated where its data is owned), "
          "the callback is immutable, and a defect is refused at construction")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
