"""Proof for orient/nexus.py — the graft, additive or it is not a graft. Teeth a hollow
build could not pass:

  - THE CORPUS TABLE IS BORN OWNED BY ORIENT: ``orient_corrections_nodes`` registers
    under owner 'orient', and a write wearing any other name is refused by db_domain's
    physics, not manners (Law 6 — the falsifier's own words).
  - AN UNDATED CORRECTION MAY NOT TAKE RESIDENCE: the deposit door demands a dated
    provenance (tooth 12's requirement, honored one layer early); a refused deposit
    leaves the tree exactly where it stood.
  - THE FOUNDING CORRECTIONS CARRY THEIR SCARS: every seed names a dated source and the
    scan it seeded — and that scan EXISTS in the registry (the corpus starts with the
    scars that built the instrument, edge (a)).
  - COUNSEL WALKS WITH ITS FLOOR VISIBLE: the labeled n=1 floor rides every answer
    (inherited fences, unforked).
  - A PROPOSAL NEVER TOUCHES THE REGISTRY: propose_scan assembles — corpus walk, ceiling
    draft, admission gate named in the artifact — and SCANS is bit-identical after (the
    hardware ruling's sharpest line: admission only by installation).
  - THE FIRE-PATH NEVER REACHES THE TREE, BY CONSTRUCTION: AST allowlists both ways —
    orient.py imports no tree machinery (a measurement is replayable; a live tree-walk
    verdict is not), and nexus.py's only cairn door is chart's nexus verbs.

Requires the one-time DB provisioning. Self-cleaning: the nonce corpus's table and
registry row are dropped. Under the tester's netns seal the DB rides the Unix socket.

    python3 cairn/orient/proofs/test_orient_nexus.py     # exit 0 = green
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

from cairn.chart.tree import nexus_table
from cairn.db_domain import store
from cairn.db_domain.store import OwnershipError
from cairn.librarian import trees
from cairn.orient import nexus
from cairn.orient import orient
from cairn.orient.nexus import (
    FOUNDING_CORRECTIONS, GraftRefused, counsel_corrections, deposit_correction,
    propose_scan,
)

_NONCE = f"corrections_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"
_TABLE = nexus_table(_NONCE, owner="orient")
_PROV = {"source": "proofs/test_orient_nexus.py", "date": "2026-07-28"}


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def test_the_corpus_table_is_born_owned_by_orient():
    r = deposit_correction("the first correction of an orient-owned corpus",
                           [1.0, 0.0, 0.0], _PROV)
    assert r["duplicate"] is False
    assert store.owner_of(_TABLE) == "orient", \
        "the corpus table must register under owner 'orient' at birth (Law 6)"
    try:
        store.write(_TABLE, "chart", {
            "node_id": "forced", "tree": _NONCE, "content": "should never land",
            "vector": [1.0], "provenance": {"source": "x"}, "standing": "hypothesis"})
        raise AssertionError("a non-orient write must be REFUSED by db_domain (Law 6)")
    except OwnershipError:
        pass


def test_an_undated_correction_may_not_take_residence():
    before = trees.tree_state(_NONCE, table=_TABLE, owner="orient")
    msg = _refuses(GraftRefused, deposit_correction,
                   "a correction arriving with no date on it",
                   [1.0, 0.0, 0.0], {"source": "somewhere real"})
    assert "date" in msg and "tooth 12" in msg
    # And the librarian's own refusals stay inherited under the date gate:
    _refuses(trees.DepositRefused, deposit_correction,
             "a dated correction with an empty source",
             [1.0, 0.0, 0.0], {"date": "2026-07-28", "source": ""})
    assert trees.tree_state(_NONCE, table=_TABLE, owner="orient") == before, \
        "a refused deposit must leave the corpus exactly where it stood"


def test_the_founding_corrections_carry_their_scars():
    assert FOUNDING_CORRECTIONS, "an empty founding set is a corpus with no scars"
    for c in FOUNDING_CORRECTIONS:
        prov = c["provenance"]
        assert str(prov.get("source", "")).strip(), "every scar names its source"
        assert re.match(r"^2026-07-2[5-8]$", prov.get("date", "")), \
            f"every scar is dated to the correction that made it: {prov.get('date')!r}"
        assert prov.get("scan") in orient.SCANS, \
            f"the scan a scar seeded must exist in the registry: {prov.get('scan')!r}"
        assert len(" ".join(c["content"].split())) >= 8, "a scar is not near-nothing"


def test_counsel_walks_with_its_floor_visible():
    deposit_correction("a second correction, far from the first",
                       [0.0, 0.0, 1.0], _PROV)
    got = counsel_corrections([0.9, 0.1, 0.0], k=10)
    assert got["walk"], "the walk sees the corpus"
    assert "guess" in got["floor_is"] and "n=1" in got["floor_is"], \
        "the floor's label travels through the graft unstripped"
    assert all(n["similarity"] >= got["floor"] for n in got["above_floor"])
    assert all(n["standing"] == "hypothesis" for n in got["walk"]), \
        "corpus nodes are born hypotheses (inherited physics)"


def test_a_proposal_never_touches_the_registry():
    registry_before = dict(orient.SCANS)
    p = propose_scan("CC read a summary of a proof instead of running it", [1.0, 0.0, 0.0])
    assert orient.SCANS == registry_before and all(
        orient.SCANS[k] is registry_before[k] for k in registry_before), \
        "propose_scan must not touch SCANS — admission is installation, never assembly"
    assert p["proposal_for"] == "scan" and p["counsel"]["walk"], \
        "the proposal carries the corpus walk the ceiling drafts from"
    assert "tooth 12" in p["admission"] and "ratified" in p["admission"], \
        "the admission gate travels in the artifact itself"
    assert "ceiling" in p["draft_is"], "the draft is the ceiling's, and says so"


def test_the_fire_path_never_reaches_the_tree():
    # Composed over orient's own import_map scan (installed 2026-07-28 through this
    # very brick's loop): the allowlist matches the module that ACTUALLY ENTERS,
    # not the spelling — the loose package form resolves before matching, so a
    # respelling can neither cause nor dodge a red.
    allowed = {
        orient.__file__: ("__future__", "ast", "json", "subprocess", "sys", "pathlib"),
        nexus.__file__: ("__future__", "cairn.chart.tree"),
    }
    for path, allow in allowed.items():
        seen = orient.import_map(path)["measured"]["imports"]
        offenders = [m for m in seen
                     if not any(m == p or m.startswith(p + ".") for p in allow)]
        assert not offenders, (
            f"{Path(path).name} imports outside its allowlist: {offenders} — the "
            "fire-path may never reach the tree (a measurement is replayable), and the "
            "graft's only cairn door is chart's nexus verbs")


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
        test_the_corpus_table_is_born_owned_by_orient,
        test_an_undated_correction_may_not_take_residence,
        test_the_founding_corrections_carry_their_scars,
        test_counsel_walks_with_its_floor_visible,
        test_a_proposal_never_touches_the_registry,
        test_the_fire_path_never_reaches_the_tree,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        nexus.CORPUS = "corrections"
        _cleanup()
    print("green — orient/nexus: the corpus is born orient's, undated corrections are "
          "turned away, the founding scars trace to real scans, counsel keeps its "
          "labeled floor, a proposal cannot touch the registry, and the fire-path "
          "cannot reach the tree — the graft is additive, by construction")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
