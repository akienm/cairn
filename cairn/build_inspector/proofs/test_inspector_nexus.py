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

    python3 cairn/build_inspector/proofs/test_inspector_nexus.py     # exit 0 = green
"""
from __future__ import annotations

import ast
import os
import re
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.build_inspector import inspector
from cairn.build_inspector import nexus
from cairn.build_inspector.nexus import (
    FOUNDING_QUESTIONS, GraftRefused, counsel_failures, deposit_failure,
    propose_sieve,
)
from cairn.chart.tree import nexus_table
from cairn.db_domain import store
from cairn.db_domain.store import OwnershipError
from cairn.librarian import trees

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
    # cairn.chart.orient joined 2026-07-28 (packet-inspector-wire): the packet
    # jurisdiction composes the berth gate's own ref semantics. It is a TREE-FREE
    # module (its own allowlist tooth pins stdlib + cairn.orient.orient only), so
    # the verdict path stays structurally unable to reach tree machinery —
    # transitively, which the assert below the loop pins.
    allowed = {
        # cairn.chart.verdict joined 2026-07-29 (proved-answers-the-chart): the
        # exit gate composes the ONE verdict-artifact validator — tree-free like
        # chart.orient, pinned transitively below.
        # re joined 2026-08-01 (intent-becomes-a-learning-block): the intent gate
        # matches the "none, because <why>" exemption on the RAW field, and a
        # hand-rolled prefix test on a stripped string is exactly how the blank
        # exemption slipped into the wrong branch. stdlib, tree-free by definition.
        # cairn.skill_block joined 2026-08-01 (same ticket): the intent gate reads a
        # skill firing's berth through the seam's OWN reader rather than re-deriving
        # the berth layout here — one address rule, two mouths that cannot disagree.
        # It is tree-free, and so is the learning_block primitive beneath it; both
        # are pinned transitively below.
        inspector.__file__: ("__future__", "json", "os", "re", "sys", "pathlib",
                             "cairn.charter", "cairn.chart.orient",
                             "cairn.chart.verdict", "cairn.orient.orient",
                             "cairn.skill_block", "cairn.import_sieve"),
        # cairn.import_sieve joined 2026-08-06 (the-questions-are-the-sieve): the nest
        # DERIVES each sieve's band from what that sieve's own body reaches, so the
        # verdict path now reads its own source through the same AST primitive that
        # seals the inference and 5432 doors. It is the strictest kind of addition to
        # this list — a pure-AST module with no cairn imports at all — and it is pinned
        # tree-free transitively below like every other composed module.
        # os joined 2026-07-28 (decompose-filters): judge_decompose reads the
        # packet's survey_ref berth with its OWN minimal open — importing chart's
        # chain reader back would let the judged family shape the judge.
        nexus.__file__: ("__future__", "cairn.chart.tree"),
    }
    # Composed over orient's import_map (installed 2026-07-28 through the brick
    # loop): the allowlist matches the module that ACTUALLY ENTERS, not the
    # spelling — the loose package form resolves before matching.
    from cairn.orient.orient import import_map
    for path, allow in allowed.items():
        seen = import_map(path)["measured"]["imports"]
        offenders = [m for m in seen
                     if not any(m == p or m.startswith(p + ".") for p in allow)]
        assert not offenders, (
            f"{Path(path).name} imports outside its allowlist: {offenders} — the "
            "verdict path may never reach the tree (a verdict is always hardware), and "
            "the graft's only cairn door is chart's nexus verbs")
    # The transitive half: the chart modules the verdict path composes must
    # themselves be tree-free — if chart/orient.py (or chart/verdict.py, joined
    # 2026-07-29) ever imports tree machinery, the separation breaks one hop
    # away and THIS tooth is the one that says so.
    import cairn.chart.orient as chart_orient
    import cairn.chart.verdict as chart_verdict
    import cairn.learning_block.learning_block as lb
    import cairn.skill_block.skill_block as skill_block
    import cairn.import_sieve.sieve as import_sieve_mod
    # Sharpened 2026-08-06: this check used to scan the raw source for the door's NAME,
    # and import_sieve is the module that proves why that is a coin-toss — it NAMES
    # cairn.chart.tree as data (an entry in the reach ladder) while importing nothing.
    # Mention is not capability, which is the same lesson silent_device learned from
    # emit-homonyms, arriving here in the guard rather than in the thing guarded. So the
    # question is asked of the IMPORTS, with the text scan kept for exactly the hole an
    # AST cannot see: a module that never reaches for importlib/__import__ cannot open a
    # door dynamically, so for those the AST answer is complete.
    TREE_DOORS = ("cairn.chart.tree", "cairn.librarian", "cairn.db_domain")
    for mod in (chart_orient, chart_verdict, skill_block, lb, import_sieve_mod):
        seen = import_map(mod.__file__)["measured"]["imports"]
        reached = [m for m in seen
                   if any(m == d or m.startswith(d + ".") for d in TREE_DOORS)]
        assert not reached, (
            f"{mod.__name__} imports {reached} — the verdict path's composed module "
            "must stay tree-free (the wire's standing condition)")
        # ...and the dynamic-capability question is asked the same way, for the same
        # reason: import_sieve NAMES importlib (it is a thing the hollow scan looks for)
        # while never importing it. Asking by substring here would have re-created the
        # exact defect one line below the comment explaining it.
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
