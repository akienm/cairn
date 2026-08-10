"""Proof for librarian/trees.py — the graph-tree spine. Teeth a hollow store could not pass:

  - THE DOOR REFUSES THE UNTRACEABLE: a deposit without provenance (or with a sourceless
    one) never lands — fabricated attribution cannot take up permanent residence.
  - VECTORS ARE PHYSICS: empty, non-numeric, non-finite, and zero vectors are refused at
    both doors; a dimension mismatch (deposit or query) is refused, not answered.
  - BORN A HYPOTHESIS: a landed node reads back with its content, structured provenance,
    and standing = "hypothesis" (Law 3 — tenure is a later measurement, not a birthright).
  - A DUPLICATE GROWS NOTHING, BUT ITS PROVENANCE LANDS: same tree + content returns the
    standing node, flagged, row count unmoved (Law 1 stops redundant STRUCTURE) — and the
    incoming provenance appends as a timestamped attestation (ticket the-tenure-loop:
    redundant ARRIVAL is evidence). The shared walk never decays a tenant's node.
  - THE EMBEDDING IS THE PATH: nearest ranks by cosine, provably in proximity order;
    neighbors derives a node's edges and excludes the node itself; NO edge table exists —
    nothing edge-named is ever registered with db_domain.
  - TREES DO NOT CROSS: a walk of one tree never surfaces another tree's nodes.
  - THE OWNER-GATE HOLDS THROUGH THE STACK: a non-librarian write to the nodes table is
    refused by db_domain's physics, not by this module's manners.
  - CROSSINGS BREADCRUMB, READS STAY SILENT: every deposit emits (DEPOSITED and DUPLICATE
    alike); walks emit nothing.
  - DEVICE-HOOD: BaseDevice + CP1-CP6 + the ordered Form v0 #2 surface.
  - IMPORT PURITY BY AST ALLOWLIST: trees.py reaches the DB only through db_domain and
    the network not at all — psycopg2, urllib, socket and friends cannot appear.

Requires the one-time DB provisioning (as db_domain's proof does). Self-cleaning: the
nonce table and its registry row are dropped. The netns seal does not sever the DB — the
Unix socket is a file (db_domain's documented asymmetry, exercised for real here).

    python3 cairn/librarian/proofs/test_librarian_trees.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.device import BaseDevice
from cairn.db_domain import store
from cairn.db_domain.store import OwnershipError
from cairn.librarian import trees
from cairn.librarian.trees import (
    DepositRefused, LibrarianDevice, WalkRefused, deposit, nearest, neighbors,
)

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_trees_{_NONCE}"

_PROV = {"source": "proofs/test_librarian_trees.py", "ground": "fixture"}


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def test_the_door_refuses_the_untraceable():
    # No provenance at all, a non-dict, and a sourceless dict: none may land.
    _refuses(DepositRefused, deposit, "a perfectly good sentence", [1.0, 0.0], None, table=_TABLE)
    _refuses(DepositRefused, deposit, "a perfectly good sentence", [1.0, 0.0], "held-librarian", table=_TABLE)
    msg = _refuses(DepositRefused, deposit, "a perfectly good sentence", [1.0, 0.0],
                   {"source": "  "}, table=_TABLE)
    assert "provenance" in msg and "source" in msg, "the refusal must name what was missing"
    # And content under the floor is invention, refused before any write.
    _refuses(DepositRefused, deposit, "tiny", [1.0, 0.0], _PROV, table=_TABLE)


def test_vectors_are_physics_at_both_doors():
    for bad in ([], ["a", "b"], [float("nan"), 1.0], [0.0, 0.0]):
        _refuses(DepositRefused, deposit, "content long enough to land", bad, _PROV, table=_TABLE)
        _refuses(WalkRefused, nearest, bad, tree="commons", table=_TABLE)
    _refuses(WalkRefused, nearest, [1.0, 0.0], k=0, table=_TABLE)


def test_a_node_lands_and_is_born_a_hypothesis():
    r = deposit("the embedding is the path through the graph trees",
                [1.0, 0.0, 0.0], _PROV, tree="t1", table=_TABLE)
    assert r["duplicate"] is False and r["dim"] == 3
    rows = store.read(_TABLE, where="node_id = %s", params=(r["node_id"],))
    assert len(rows) == 1, "the node must be durably readable"
    row = rows[0]
    assert row["standing"] == "hypothesis", "every node is born a hypothesis (Law 3)"
    assert row["provenance"]["source"] == _PROV["source"], "provenance must round-trip as structure"
    assert row["vector"] == [1.0, 0.0, 0.0], "the vector must round-trip exactly"


def test_a_duplicate_grows_nothing_but_its_provenance_lands():
    # Edge (b)'s switch, flipped by ticket the-tenure-loop: Law 1 still refuses the
    # redundant ROW; the redundant ARRIVAL now lands as an attestation on the standing
    # row — independent reach is evidence the tenure loop counts, not litter to drop.
    content = "the embedding is the path through the graph trees"
    before = len(store.read(_TABLE, where="tree = %s", params=("t1",)))
    r = deposit(content, [1.0, 0.0, 0.0], {"source": "a-second-witness"}, tree="t1", table=_TABLE)
    after = len(store.read(_TABLE, where="tree = %s", params=("t1",)))
    assert r["duplicate"] is True, "the standing node must come back flagged"
    assert r["provenance_appended"] is True
    assert before == after, "a duplicate deposit must grow the table by NOTHING (Law 1)"
    row = store.read(_TABLE, where="node_id = %s", params=(r["node_id"],))[0]
    attests = row["provenance"].get("attestations") or []
    assert len(attests) == 1 and attests[0]["source"] == "a-second-witness" and attests[0]["at"], \
        "the incoming provenance must land WHOLE as an attestation, timestamped"
    assert row["provenance"]["source"] == _PROV["source"], "the birth provenance survives untouched"


def test_dimension_mismatch_is_refused_not_answered():
    _refuses(DepositRefused, deposit, "a node of the wrong dimension",
             [1.0, 0.0], _PROV, tree="t1", table=_TABLE)
    _refuses(WalkRefused, nearest, [1.0, 0.0], tree="t1", table=_TABLE)


def test_nearest_ranks_by_proximity_and_derives_the_path():
    # Three known directions: the query points almost exactly at `east`.
    deposit("east-pointing node, the close one", [1.0, 0.1, 0.0], _PROV, tree="t1", table=_TABLE)
    deposit("up-pointing node, the far one", [0.0, 0.0, 1.0], _PROV, tree="t1", table=_TABLE)
    got = nearest([1.0, 0.05, 0.0], k=2, tree="t1", table=_TABLE)
    assert [n["content"] for n in got][0] == "east-pointing node, the close one"
    assert got[0]["similarity"] > got[1]["similarity"], "ranked by cosine, descending"
    assert all(-1.0 <= n["similarity"] <= 1.0 for n in got), "cosine stays in [-1, 1]"
    # An empty tree is an honest [] — absence is not an error.
    assert nearest([1.0], k=3, tree="empty-tree", table=_TABLE) == []


def test_the_walk_itself_never_decays_a_tenant():
    # MULTI-TENANT NEUTRALITY (ticket the-tenure-loop, out-of-bounds clause): the chart's
    # nexi walk these same tools with their own tables. Tenure's decay lives in the
    # LIBRARIAN'S answer path (loop.py), never here — an aged, uncorroborated node still
    # ranks at full raw cosine in nearest, and created merely RIDES the walk for readers
    # who weigh it.
    aged = "an old resident a tenant's walk must still surface first"
    r = deposit(aged, [1.0, 0.02, 0.0], _PROV, tree="tenant", table=_TABLE)
    deposit("a nearer-in-time but farther-in-space node", [0.3, 0.9, 0.0], _PROV,
            tree="tenant", table=_TABLE)
    store.update(_TABLE, trees.OWNER,
                 {"created": datetime.now(timezone.utc) - timedelta(days=365)},
                 where="node_id = %s", params=(r["node_id"],))
    got = nearest([1.0, 0.0, 0.0], k=2, tree="tenant", table=_TABLE)
    assert got[0]["node_id"] == r["node_id"], \
        "a year-old node still ranks FIRST by raw cosine — no decay at the shared walk"
    assert got[0]["created"] is not None, "created rides the walk as data for the reader"


def test_trees_do_not_cross():
    deposit("a node that lives in another tree entirely", [1.0, 0.09, 0.0],
            _PROV, tree="t2", table=_TABLE)
    surfaced = nearest([1.0, 0.09, 0.0], k=50, tree="t1", table=_TABLE)
    assert all("another tree" not in n["content"] for n in surfaced), \
        "a walk of t1 must never surface a t2 node — trees do not cross"


def test_neighbors_are_derived_and_exclude_self():
    nid = trees.node_id_for("t1", "east-pointing node, the close one")
    got = neighbors(nid, k=2, tree="t1", table=_TABLE)
    assert got, "a node among siblings has derived neighbors"
    assert all(n["node_id"] != nid for n in got), "a node is not its own neighbor"
    # A ghost has no neighborhood — refused, not an empty list wearing 'isolated'.
    _refuses(WalkRefused, neighbors, "no-such-node", tree="t1", table=_TABLE)


def test_tree_state_moves_with_the_tree_and_only_with_it():
    # The livelock-fix primitive: same members -> same digest; a deposit moves it; a
    # DUPLICATE deposit (nothing written) leaves it exactly where it stood.
    before = trees.tree_state("t1", table=_TABLE)
    again = trees.tree_state("t1", table=_TABLE)
    assert before == again, "the fingerprint is a pure function of the tree's members"
    assert before["nodes"] > 0 and before["digest"] != "empty"
    deposit("a node that moves the fingerprint", [0.2, 0.9, 0.0], _PROV, tree="t1", table=_TABLE)
    moved = trees.tree_state("t1", table=_TABLE)
    assert moved["digest"] != before["digest"] and moved["nodes"] == before["nodes"] + 1
    deposit("a node that moves the fingerprint", [0.2, 0.9, 0.0], _PROV, tree="t1", table=_TABLE)
    assert trees.tree_state("t1", table=_TABLE) == moved, \
        "a duplicate writes nothing, so the fingerprint must not move"
    assert trees.tree_state("never-touched", table=_TABLE) == {"digest": "empty", "nodes": 0}


def test_no_edge_table_exists():
    # The derived-edges claim, pinned in the registry: nothing edge-named was ever
    # registered by this build (a hollow store quietly persisting adjacency trips this).
    for name in ("librarian_edges", f"{_TABLE}_edges"):
        assert store.owner_of(name) is None, f"an edge table {name!r} must NOT exist — edges are derived"


def test_the_owner_gate_holds_through_the_stack():
    try:
        store.write(_TABLE, "impostor", {
            "node_id": "forced", "tree": "t1", "content": "should never land",
            "vector": [1.0], "provenance": {"source": "x"}, "standing": "hypothesis"})
        raise AssertionError("a non-librarian write must be REFUSED by db_domain (Law 6)")
    except OwnershipError:
        pass


def test_crossings_breadcrumb_and_reads_stay_silent():
    dev = LibrarianDevice()
    r1 = dev.deposit("a breadcrumbed crossing, observed end to end",
                     [0.5, 0.5, 0.0], _PROV, tree="t1", table=_TABLE)
    dev.deposit("a breadcrumbed crossing, observed end to end",
                [0.5, 0.5, 0.0], _PROV, tree="t1", table=_TABLE)
    crumbs = dev.held_diagnostics()
    assert len(crumbs) == 2, "every deposit crossing breadcrumbs — DEPOSITED and DUPLICATE alike"
    assert [c["values"]["verdict"] for c in crumbs] == ["DEPOSITED", "DUPLICATE"]
    assert crumbs[0]["pointer"] == r1["node_id"], "the pointer is the node that crossed"
    assert crumbs[0]["gate"] == "deposit" and crumbs[0]["source"] == "LibrarianDevice"

    dev.nearest([1.0, 0.0, 0.0], tree="t1", table=_TABLE)
    dev.neighbors(r1["node_id"], tree="t1", table=_TABLE)
    assert len(dev.held_diagnostics()) == 2, "walks are reads — silent, no breadcrumb"
    assert dev.state()["deposits"] == 2 and dev.state()["verdicts"]["DUPLICATE"] == 1


def test_device_hood_and_the_ordered_surface():
    dev = LibrarianDevice()
    assert isinstance(dev, BaseDevice) and dev.device_id == "librarian"
    surface = dev.introspect()
    assert list(surface) == ["intention", "state", "settings", "other"], "Form v0 #2 order is the contract"
    assert "chatbot" in surface["intention"]["what"], "the reported intention names the face"
    from cairn.base.core_values import CoreValuesMixin
    assert isinstance(dev, CoreValuesMixin), "a device carries CP1-CP6 structurally (Law 2)"


def test_trees_opens_no_door_of_its_own():
    # Allowlist, not blocklist: an import outside these prefixes is a second door and reds.
    allowed = ("__future__", "hashlib", "math", "datetime", "cairn.base", "cairn.db_domain")
    src = Path(trees.__file__).read_text(encoding="utf-8")
    seen = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            seen.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            seen.append(node.module or "")
    offenders = [m for m in seen if not any(m == p or m.startswith(p + ".") for p in allowed)]
    assert not offenders, (
        f"trees.py imports outside its allowlist: {offenders} — the DB is reached only "
        "through db_domain and the network not at all (Law 4; sole-path)")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_the_door_refuses_the_untraceable,
        test_vectors_are_physics_at_both_doors,
        test_a_node_lands_and_is_born_a_hypothesis,
        test_a_duplicate_grows_nothing_but_its_provenance_lands,
        test_the_walk_itself_never_decays_a_tenant,
        test_dimension_mismatch_is_refused_not_answered,
        test_nearest_ranks_by_proximity_and_derives_the_path,
        test_trees_do_not_cross,
        test_neighbors_are_derived_and_exclude_self,
        test_tree_state_moves_with_the_tree_and_only_with_it,
        test_no_edge_table_exists,
        test_the_owner_gate_holds_through_the_stack,
        test_crossings_breadcrumb_and_reads_stay_silent,
        test_device_hood_and_the_ordered_surface,
        test_trees_opens_no_door_of_its_own,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — librarian/trees: the untraceable never lands, vectors are physics, "
          "nodes are born hypotheses, a duplicate grows nothing but its provenance lands "
          "as an attestation, the embedding is the path "
          "(edges derived, never stored), trees do not cross, the owner-gate holds, "
          "crossings breadcrumb, and the module opens no door of its own")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
