"""Proof for build_inspector/nexus.py — the graft, additive or it is not a graft. Teeth
a hollow build could not pass:

  - THE CORPUS TABLE IS BORN OWNED BY THE INSPECTOR: ``build_inspector_failures_nodes``
    registers under owner 'build_inspector'; a write wearing any other name is refused
    by db_domain's physics, not manners (Law 6 — the falsifier's own words).
  - AN UNDATED FAILURE MAY NOT TAKE RESIDENCE: the deposit door demands a dated
    provenance (tooth 10's requirement, honored one layer early); a refused deposit
    leaves the tree exactly where it stood.
  - THE FOUNDING QUESTIONS ARE SEEDED-BUT-UNBUILT: every candidate names a legal sieve
    name that is NOT yet in SIEVES (a question nexus holds the unbuilt well; when one
    lands by installation, this tooth demands its entry record that) and carries a dated
    source.
  - COUNSEL WALKS WITH ITS FLOOR VISIBLE: the labeled n=1 floor rides every answer.
  - A PROPOSAL NEVER TOUCHES THE REGISTRY: propose_sieve assembles — corpus walk,
    ceiling draft, admission gate named in the artifact — and SIEVES is bit-identical
    after (a gate that could learn its own leniency is the measured home-field risk).
  - THE FIRE-PATH NEVER REACHES THE TREE, BY CONSTRUCTION: AST allowlists both ways —
    inspector.py imports no tree machinery (a verdict is always hardware, replayable),
    and nexus.py's only cairn door is chart's nexus verbs. The chokepoint wiring
    (transitions.py) is untouched by this graft; its own five gate teeth are the
    falsifier there.

Requires the one-time DB provisioning. Self-cleaning: the nonce corpus's table and
registry row are dropped. Under the tester's netns seal the DB rides the Unix socket.

    python3 cairn/machines/build_inspector/proofs/test_inspector_nexus.py     # exit 0 = green
"""
from __future__ import annotations

import ast
import os
import re
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector import inspector
from cairn.machines.build_inspector import nexus
from cairn.machines.build_inspector.nexus import (
    FOUNDING_QUESTIONS, GraftRefused, counsel_failures, deposit_failure,
    propose_sieve,
)
from cairn.machines.chart.tree import nexus_table
from cairn.devices.db_domain import store
from cairn.devices.db_domain.store import OwnershipError
from cairn.devices.librarian import trees

_NONCE = f"failures_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"
_TABLE = nexus_table(_NONCE, owner="build_inspector")
_PROV = {"source": "proofs/test_inspector_nexus.py", "date": "2026-07-28"}


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def test_the_corpus_table_is_born_owned_by_the_inspector():
    r = deposit_failure("the first failure of an inspector-owned corpus",
                        [1.0, 0.0, 0.0], _PROV)
    assert r["duplicate"] is False
    assert store.owner_of(_TABLE) == "build_inspector", \
        "the corpus table must register under owner 'build_inspector' at birth (Law 6)"
    try:
        store.write(_TABLE, "orient", {
            "node_id": "forced", "tree": _NONCE, "content": "should never land",
            "vector": [1.0], "provenance": {"source": "x"}, "standing": "hypothesis"})
        raise AssertionError("a non-inspector write must be REFUSED by db_domain (Law 6)")
    except OwnershipError:
        pass


def test_an_undated_failure_may_not_take_residence():
    before = trees.tree_state(_NONCE, table=_TABLE, owner="build_inspector")
    msg = _refuses(GraftRefused, deposit_failure,
                   "a failure arriving with no date on it",
                   [1.0, 0.0, 0.0], {"source": "somewhere real"})
    assert "date" in msg and "tooth 10" in msg
    _refuses(trees.DepositRefused, deposit_failure,
             "a dated failure with an empty source",
             [1.0, 0.0, 0.0], {"date": "2026-07-28", "source": ""})
    assert trees.tree_state(_NONCE, table=_TABLE, owner="build_inspector") == before, \
        "a refused deposit must leave the corpus exactly where it stood"


def test_the_founding_questions_are_seeded_but_unbuilt():
    assert FOUNDING_QUESTIONS, "an empty founding set is a corpus with no questions"
    for q in FOUNDING_QUESTIONS:
        name = q["candidate_sieve"]
        assert re.match(r"^[a-z][a-z0-9_]*$", name), \
            f"a candidate names the sieve it would become: {name!r}"
        assert name not in inspector.SIEVES, (
            f"candidate {name!r} is already in SIEVES — seeded-but-unbuilt is the "
            "contract; a landed candidate updates its founding entry to say it landed")
        prov = q["provenance"]
        assert str(prov.get("source", "")).strip(), "every question names its source"
        assert re.match(r"^2026-07-2[5-8]$", prov.get("date", "")), \
            f"every question is dated: {prov.get('date')!r}"
        assert len(" ".join(q["content"].split())) >= 8, "a question is not near-nothing"


def test_counsel_walks_with_its_floor_visible():
    deposit_failure("a second failure, far from the first", [0.0, 0.0, 1.0], _PROV)
    got = counsel_failures([0.9, 0.1, 0.0], k=10)
    assert got["walk"], "the walk sees the corpus"
    assert "guess" in got["floor_is"] and "n=1" in got["floor_is"], \
        "the floor's label travels through the graft unstripped"
    assert all(n["similarity"] >= got["floor"] for n in got["above_floor"])
    assert all(n["standing"] == "hypothesis" for n in got["walk"]), \
        "corpus nodes are born hypotheses (inherited physics)"


def test_a_proposal_never_touches_the_registry():
    registry_before = dict(inspector.SIEVES)
    p = propose_sieve("a component's validations went stale against its code",
                       [1.0, 0.0, 0.0])
    assert inspector.SIEVES == registry_before and all(
        inspector.SIEVES[k] is registry_before[k] for k in registry_before), \
        "propose_sieve must not touch SIEVES — admission is installation, never assembly"
    assert p["proposal_for"] == "sieve" and p["counsel"]["walk"], \
        "the proposal carries the corpus walk the ceiling drafts from"
    assert "tooth 10" in p["admission"] and "ratified" in p["admission"], \
        "the admission gate travels in the artifact itself"
    assert "ceiling" in p["draft_is"], "the draft is the ceiling's, and says so"


def test_the_fire_path_never_reaches_the_tree():
    """The verdict path may never reach the tree — a verdict is always hardware.

    REPLACED 2026-08-12 (ticket reachability-replaces-the-allowlist). What stood here was
    a literal tuple of the modules inspector.py was ALLOWED to import, widened by hand
    with a dated comment every time the corpus grew a legitimate dependency — until one
    arrived without the widening (cairn.tools.base.nest, 047d633) and the tooth read as holding
    while it was red. The question is now asked the other way round and one address up:
    inspector._FIRE_PATH names the DENIED capability, the walk follows every import hop
    from inspector.py, and the innocent never need a signature. Both halves this tooth
    used to do by hand are strictly inside that: the direct-import half is the walk's
    first link, and the five hand-named composed modules are five of the seventeen files
    the closure actually holds.
    """
    from cairn.tools.orient.orient import import_map
    import cairn.tools.import_sieve.sieve as import_sieve_mod
    # The nexus keeps its allowlist, and that is not an oversight. It is the GRAFT — the
    # one file whose whole point is that its only cairn door is chart's nexus verbs — so
    # the question there really is "what may this file import", which is what an allowlist
    # asks. A two-entry list on a file that must stay two entries wide does not have the
    # maintenance failure above; a list that grows with the corpus does.
    allow = ("__future__", "cairn.machines.chart.tree")
    offenders = [m for m in import_map(nexus.__file__)["measured"]["imports"]
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"{Path(nexus.__file__).name} imports outside its allowlist: {offenders} — the "
        "graft's only cairn door is chart's nexus verbs")

    # The fire path itself, shaken through the rule at the address that owns it. This is
    # ONE call where twelve hand-maintained names and a five-module loop used to be, and
    # it is strictly wider than both: measured 2026-08-12, the closure from inspector.py
    # is 17 files, and the old loop named 5 of them. A breach in cairn/tools/base/address.py —
    # two hops out, a file the old list never mentioned — is caught by this and invisible
    # to what it replaced.
    graph = import_sieve_mod.import_graph(str(_REPO_ROOT))
    caught = import_sieve_mod.catches(graph, inspector._FIRE_PATH)
    assert caught == [], (
        f"the verdict path can reach a door it may not: {caught} — a verdict that can "
        "consult a tree, a database or a host returns an opinion wearing a "
        "measurement's clothes")
    reached = import_sieve_mod.reaches(graph, inspector._FIRE_PATH["start"])
    assert len(reached) > 5, (
        f"the closure from the fire path came back at {len(reached)} files — the assert "
        "above would be green because nothing was walked, which is the green-by-removal "
        "this replacement exists to avoid")

    # The dynamic-capability question, kept whole and asked of the same five modules it
    # was asked of before. The AST above cannot see a computed import, so this is the one
    # hand-written extent left in this tooth — deliberately not widened to the closure in
    # the same pass that removed the other two, because the ticket's bounds put it out.
    # Named here rather than left as a silent leftover: the residue is the 12 closure
    # members nobody asks the dynamic question of.
    import cairn.machines.chart.orient as chart_orient
    import cairn.machines.chart.verdict as chart_verdict
    import cairn.machines.learning_block.learning_block as lb
    import cairn.machines.skill_block.skill_block as skill_block
    # DERIVED from the one declaration, never restated: a second literal here is two
    # lists that drift, which is the defect one layer up from the one this ticket closed.
    # Scoped to the in-tree names because this check is a SUBSTRING scan — "socket" and
    # "requests" appear in honest prose all over the corpus, and asking by substring for
    # those would be the coin-toss red the comment above is about.
    TREE_DOORS = tuple(m for m in inspector._FIRE_PATH["modules"] if m.startswith("cairn."))
    for mod in (chart_orient, chart_verdict, skill_block, lb, import_sieve_mod):
        seen = import_map(mod.__file__)["measured"]["imports"]
        # Sharpened 2026-08-06: the dynamic question is asked of the IMPORTS, with the
        # text scan kept for exactly the hole an AST cannot see. import_sieve NAMES
        # importlib (a thing the hollow scan looks for) while never importing it, and
        # asking by substring would re-create the exact defect this comment explains.
        mod_src = Path(mod.__file__).read_text(encoding="utf-8")
        dyn = any(m == "importlib" or m.startswith("importlib.") for m in seen) or any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "__import__"
            for n in ast.walk(ast.parse(mod_src)))
        if dyn:
            # This module CAN open a door the AST cannot see (skill_block resolves a
            # skill's judge dynamically), so the coarse name-scan is still the only
            # instrument that reaches it, false positives and all. A module without
            # that capability does not pay the coin-toss — which is the whole
            # distinction, and it is measured per module rather than assumed for all.
            for tree_door in TREE_DOORS:
                assert tree_door not in mod_src, (
                    f"{mod.__name__} names {tree_door} AND imports dynamically — the "
                    "AST cannot clear it, so the name stands as a reach until the "
                    "dynamic door is closed or the name goes")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


def _main() -> int:
    nexus.CORPUS = _NONCE      # the proof runs in a nonce corpus; the live one is Akien's
    checks = [
        test_the_corpus_table_is_born_owned_by_the_inspector,
        test_an_undated_failure_may_not_take_residence,
        test_the_founding_questions_are_seeded_but_unbuilt,
        test_counsel_walks_with_its_floor_visible,
        test_a_proposal_never_touches_the_registry,
        test_the_fire_path_never_reaches_the_tree,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        nexus.CORPUS = "failures"
        _cleanup()
    print("green — build_inspector/nexus: the corpus is born the inspector's, undated "
          "failures are turned away, the founding questions are seeded-but-unbuilt, "
          "counsel keeps its labeled floor, a proposal cannot touch the registry, and "
          "the verdict path cannot reach the tree — the graft is additive, by "
          "construction")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
