"""Proof for the Probe primitive — "poke X when this trigger is true", immutable.

Teeth a hollow probe could not pass:
  - A TRIGGER IS ANY PREDICATE (the anti-reification). ``fires`` reflects an arbitrary
    callable — including one that CLOSES OVER owned data (Law 6): the data stays in the
    closure, only the true/false verdict comes out. A probe that only accepted a named
    "kind" (the deleted interval/date/quantity/state enum) could not do this.
  - IT IS IMMUTABLE (frozen) — a declaration, not a stateful worker.
  - CONSTRUCTION REFUSES A DEFECT LOUDLY (CP1/CP3): a non-callable trigger, a missing why,
    or a missing ``to`` is caught at n=1, not discovered when it silently never pokes.
  - A PROBE CARRIES NO AUTHORITY (Law 6, ticket ``watchme-emits-a-probe`` 2026-07-30): it
    CANNOT move a node's state, and that is structural rather than merely unexercised. The
    whole fire path — ``probe.py`` and the shim's ``_fire`` — reaches the emit chokepoint by
    no import and no call, so the capability is absent, not declined; and a body that spells
    out a state move rides as inert data into the poke and moves nothing.

Runnable bare (no DB, no framework):
    python3 cairn/base/proofs/test_probe.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.probe import Probe


def test_a_trigger_is_any_predicate_evaluated_where_owned():
    # Genuinely shared data (the moment) read from now/context.
    at_noon = Probe(why="lunch", trigger=lambda now, ctx: now == 12, to="cook/personal")
    assert at_noon.fires(12) and not at_noon.fires(11)

    # Device-LOCAL data: the predicate closes over an owned value; only the verdict escapes,
    # never the value itself (Law 6 for triggers). The reading stays home in the closure.
    owned = {"cpu": 95}  # stands in for a device's own, unexported metric
    over_80 = Probe(why="cpu is high", trigger=lambda now, ctx: owned["cpu"] >= 80,
                       to="ops/personal", body={"crossed": 80})
    assert over_80.fires(now=None) is True
    owned["cpu"] = 50
    assert over_80.fires(now=None) is False
    # The body carries only THAT the line was crossed — never the owned reading (95/50).
    assert "cpu" not in over_80.body and over_80.body == {"crossed": 80}


def test_it_is_immutable():
    cb = Probe(why="w", trigger=lambda n, c: True, to="x/personal")
    try:
        cb.to = "y/personal"  # type: ignore[misc]
        raise AssertionError("a probe is a declaration — it must be frozen")
    except FrozenInstanceError:
        pass


def test_construction_refuses_a_defect_loudly():
    try:
        Probe(why="w", trigger="not-callable", to="x/personal")  # type: ignore[arg-type]
        raise AssertionError("a non-callable trigger must be refused (a trigger is a predicate)")
    except TypeError:
        pass
    try:
        Probe(why="", trigger=lambda n, c: True, to="x/personal")
        raise AssertionError("a probe with no why must be refused (CP3)")
    except ValueError:
        pass
    try:
        Probe(why="w", trigger=lambda n, c: True, to="")
        raise AssertionError("a probe with no 'to' must be refused (CP1 — nothing to poke)")
    except ValueError:
        pass


def test_a_probe_cannot_move_a_nodes_state():
    """THE AUTHORITY TOOTH (Law 6). The ticket's falsifier clause (5) says a probe moving a
    node's state directly is an ambient authority leak and must be STRUCTURALLY IMPOSSIBLE,
    not merely avoided — so this asserts absence-of-capability over the fire path, not
    good behaviour in one scenario.

    Measured over the AST rather than the text, so a docstring naming the chokepoint cannot
    green it and a real import cannot hide in one. The fire path is exactly two files: the
    declaration (``probe.py``) and the one method that fires it (``BaseShim._fire``). If
    either could reach ``cairn.base.transitions``, a probe body would be one call away from
    moving the node that emitted it — and the back-edge is the OWNER's act."""
    import ast
    import inspect

    from cairn.base import shim as shim_module

    def _imported(path: Path) -> set[str]:
        """Every DOTTED NAME an import brings into scope — module AND the names taken from
        it. The first draft of this collected only ``ImportFrom.module``, and a hollowing
        run caught it: ``from cairn.base import transitions`` puts the chokepoint in scope
        under module ``cairn.base``, so the row passed against a probe that imported it."""
        names: set[str] = set()
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Import):
                names.update(a.name for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                names.add(n.module)
                names.update("%s.%s" % (n.module, a.name) for a in n.names)
        return names

    probe_src = Path(inspect.getsourcefile(Probe))
    leaked = {m for m in _imported(probe_src) if "transitions" in m}
    assert not leaked, f"the probe declaration imports the chokepoint: {sorted(leaked)}"

    fire = ast.parse(inspect.getsource(shim_module.BaseShim._fire).lstrip())
    called = {ast.unparse(n.func) for n in ast.walk(fire) if isinstance(n, ast.Call)}
    assert not any("emit" in c or "transition" in c for c in called), \
        f"the shim's fire path calls the chokepoint: {sorted(called)}"

    # And the positive half: a body that SPELLS a state move is inert data. The payload comes
    # back verbatim — the probe hands the receiver a description, never an act.
    pretender = Probe(why="tries to promote its own node", trigger=lambda n, c: True,
                      to="harbor_master",
                      body={"emit": "PROVED", "workflow": "code-seam@v2: ... -> PROVED"})
    assert pretender.payload({}) == {"emit": "PROVED",
                                     "workflow": "code-seam@v2: ... -> PROVED"}, \
        "the payload is the body, not an instruction the primitive interprets"
    assert not hasattr(pretender, "emit") and not hasattr(pretender, "cross"), \
        "a probe with a state-moving method is the authority leak this row exists to refuse"


def _main() -> int:
    for check in (test_a_trigger_is_any_predicate_evaluated_where_owned,
                  test_it_is_immutable, test_construction_refuses_a_defect_loudly,
                  test_a_probe_cannot_move_a_nodes_state):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — Probe: a trigger is any predicate (evaluated where its data is owned), "
          "the probe is immutable, a defect is refused at construction, and a probe carries "
          "NO AUTHORITY — the fire path reaches the emit chokepoint by no import and no "
          "call, so a probe cannot move a node's state (Law 6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
