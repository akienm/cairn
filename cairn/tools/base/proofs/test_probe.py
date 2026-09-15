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
    python3 cairn/tools/base/proofs/test_probe.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.probe import Probe


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
    either could reach ``cairn.tools.base.transitions``, a probe body would be one call away from
    moving the node that emitted it — and the back-edge is the OWNER's act."""
    import ast
    import inspect

    from cairn.tools.base import shim as shim_module

    def _imported(path: Path) -> set[str]:
        """Every DOTTED NAME an import brings into scope — module AND the names taken from
        it. The first draft of this collected only ``ImportFrom.module``, and a hollowing
        run caught it: ``from cairn.tools.base import transitions`` puts the chokepoint in scope
        under module ``cairn.tools.base``, so the row passed against a probe that imported it."""
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


def test_owning_ticket_answers_to_every_spelling_and_holes_with_the_path():
    """THE THREE SPELLINGS AND THE HOLE (ticket 2516e958a6dd, 2026-09-15). A probe author
    names the owning ticket by hex id, by slug, or by the full ``<hex>-<slug>`` stem, and
    all three are the same file. Until this ticket ``owning_ticket`` re-derived the lookup
    with a reversed glob (``*-<name>.json``, the id on the wrong side) and holed every
    hex-id name — 9 of 84 arguments across ``probes/*.py`` the day it was measured. It now
    rides the one locator, ``cairn.tools.chain.grammar.ticket_path``.

    Against a synthetic root, so the tooth measures the RULE and not whichever live tickets
    happen to be filed today. The hole is Law 7: a string naming the path looked at, never
    None — the receiver prints what it was handed and a hole is loud there."""
    import tempfile

    from cairn.tools.base.probe import owning_ticket

    with tempfile.TemporaryDirectory(prefix="owning-ticket-scratch-root-") as d:
        filed = Path(d) / "abcdef012345-a-probe-under-test.json"
        filed.write_text("{}")
        for spelling in ("abcdef012345", "a-probe-under-test", "abcdef012345-a-probe-under-test"):
            got = owning_ticket(spelling, tickets_root=d)
            assert got == str(filed), f"{spelling!r} -> {got!r}; every spelling is the one file"
        hole = owning_ticket("nowhere", tickets_root=d)
        assert hole.startswith("{unresolvable:") and str(Path(d) / "nowhere.json") in hole, hole
        assert owning_ticket("under-test", tickets_root=d).startswith("{unresolvable:"), \
            "a TAIL of the slug resolved — the locator's narrowing (voyage 8754ae677af6) is gone"


def test_owning_ticket_agrees_with_the_one_locator_over_every_probe():
    """THE CENSUS (the ticket's falsifier). Every ``owning_ticket("...")`` and
    ``_OWNING_TICKET = "..."`` argument under the repo's ``probes/*.py`` resolves the same
    way through both names: a hole exactly where ``ticket_path`` answers None, and never a
    hole for a 12-hex id. Measured before the build: names=84, holes=9, disagree=10. A
    proof over live data asserts the invariant, never the snapshot — a new probe naming its
    ticket in any spelling is covered the day it lands.

    The lazy import is part of the contract: chain imports base at module top, so base may
    reach chain only inside a body. Importing the probe module must load no chain module."""
    import re
    import subprocess

    from cairn.tools.base.probe import owning_ticket
    from cairn.tools.chain.grammar import ticket_path

    probe = subprocess.run(
        [sys.executable, "-c", "import sys, cairn.tools.base.probe; "
         "print(sorted(m for m in sys.modules if m.startswith('cairn.tools.chain')))"],
        cwd=_REPO_ROOT, capture_output=True, text=True, env={"PYTHONPATH": str(_REPO_ROOT)})
    assert probe.returncode == 0 and probe.stdout.strip() == "[]", \
        f"importing the probe module loaded the chain package: {probe.stdout} {probe.stderr[-200:]}"

    names: dict[str, set[str]] = {}
    for f in _REPO_ROOT.glob("**/probes/*.py"):
        src = f.read_text(encoding="utf-8")
        for m in re.finditer(r'owning_ticket\(\s*"([^"]+)"', src):
            names.setdefault(m.group(1), set()).add(str(f.relative_to(_REPO_ROOT)))
        if "owning_ticket(" in src:
            for m in re.finditer(r'_(?:OWNING_)?TICKET\s*=\s*"([^"]+)"', src):
                names.setdefault(m.group(1), set()).add(str(f.relative_to(_REPO_ROOT)))
    assert names, "no probe names its owning ticket — the census scanned nothing"

    disagree, hex_holes = [], []
    for name in sorted(names):
        hole = owning_ticket(name).startswith("{unresolvable:")
        located = ticket_path(name)
        if hole != (located is None) or (not hole and owning_ticket(name) != located):
            disagree.append((name, sorted(names[name])))
        if hole and re.fullmatch(r"[0-9a-f]{12}", name):
            hex_holes.append((name, sorted(names[name])))
    print(f"  census: names={len(names)} hex-holes={len(hex_holes)} disagree={len(disagree)}")
    assert not hex_holes, f"a hex-id probe still holes: {hex_holes}"
    assert not disagree, f"the two locators disagree: {disagree}"


def _main() -> int:
    for check in (test_a_trigger_is_any_predicate_evaluated_where_owned,
                  test_it_is_immutable, test_construction_refuses_a_defect_loudly,
                  test_a_probe_cannot_move_a_nodes_state,
                  test_owning_ticket_answers_to_every_spelling_and_holes_with_the_path,
                  test_owning_ticket_agrees_with_the_one_locator_over_every_probe):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — Probe: a trigger is any predicate (evaluated where its data is owned), "
          "the probe is immutable, a defect is refused at construction, and a probe carries "
          "NO AUTHORITY — the fire path reaches the emit chokepoint by no import and no "
          "call, so a probe cannot move a node's state (Law 6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
