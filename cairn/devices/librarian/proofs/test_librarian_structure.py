"""Proof for librarian/trees.py — the structural features (paper §6). Teeth a hollow
build couldn't pass:

  - ATTRACTOR IS THE CENTROID: the attractor of a tree IS the mean of its embeddings,
    verified numerically; an empty tree has no attractor (None, not a zero vector).
  - CALVING SPLITS BY CLUSTERING: a tree above threshold calves into two child tables
    whose union covers every leaf of the parent, whose intersection is empty, and whose
    parent is left empty. Below threshold → None.
  - LINKS ARE BIDIRECTIONAL AND DETERMINISTIC: link(a, b) and link(b, a) create the same
    link_id; a link is readable from EITHER end via linked(); traversal increments count.
  - ROUTING RANKS BY ATTRACTOR PROXIMITY: route() returns tables sorted by the query's
    cosine to each tree's attractor; an empty tree is skipped.

Seams: the DB is the real one through db_domain (nonce tables, self-cleaning).

    python3 cairn/devices/librarian/proofs/test_librarian_structure.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.db_domain import store
from cairn.devices.librarian.trees import (
    EMBEDDINGS_TABLE, LINKS_TABLE, NODES_TABLE, OWNER,
    _LEAF_COLUMNS, _LINK_COLUMNS,
    attractor, calve, cosine, deposit, ensure_trees,
    link, link_id_for, link_neighbors, linked, nearest,
    node_id_for, route, traverse_link,
)

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"

_TABLES: list[str] = []


def _t(name: str) -> str:
    t = f"_struct_{name}_{_NONCE}"
    if t not in _TABLES:
        _TABLES.append(t)
    return t


def _node(node_id: str) -> dict:
    return store.read(NODES_TABLE, where="node_id = %s", params=(node_id,))[0]


def _deposit(content: str, vector, table: str):
    return deposit(
        content, vector,
        {"source": "test", "question": content},
        table=table,
    )


def teardown_module():
    conn = store.connect()
    try:
        nids = set()
        for t in _TABLES:
            if store.owner_of(t, conn=conn) is None:
                continue
            for r in store.read(t, conn=conn):
                nids.add(r["node_id"])
        for t in _TABLES:
            owner = store.owner_of(t, conn=conn)
            if owner is not None:
                store.drop_table(t, owner, conn=conn)
        if nids:
            store.delete(EMBEDDINGS_TABLE, OWNER,
                         where="node_id = ANY(%s)", params=(list(nids),), conn=conn)
            store.delete(NODES_TABLE, OWNER,
                         where="node_id = ANY(%s)", params=(list(nids),), conn=conn)
        if store.owner_of(LINKS_TABLE, conn=conn) is not None:
            store.delete(LINKS_TABLE, OWNER,
                         where="link_id LIKE %s", params=("%",), conn=conn)
    finally:
        conn.close()


# ── attractor ────────────────────────────────────────────────────────────────


def test_attractor_of_an_empty_tree_is_none():
    t = _t("attr_empty")
    ensure_trees(table=t)
    assert attractor(table=t) is None


def test_attractor_is_the_centroid():
    t = _t("attr_cent")
    _deposit(f"attractor centroid north {_NONCE}", [1.0, 0.0, 0.0], t)
    _deposit(f"attractor centroid south {_NONCE}", [-1.0, 0.0, 0.0], t)
    _deposit(f"attractor centroid east {_NONCE}", [0.0, 1.0, 0.0], t)
    a = attractor(table=t)
    assert a is not None
    assert len(a) == 3
    assert abs(a[0] - 0.0) < 1e-9
    assert abs(a[1] - 1.0 / 3.0) < 1e-9
    assert abs(a[2] - 0.0) < 1e-9


def test_attractor_of_one_node_is_that_node():
    t = _t("attr_one")
    _deposit(f"attractor single node {_NONCE}", [0.5, 0.3, 0.8], t)
    a = attractor(table=t)
    assert abs(a[0] - 0.5) < 1e-9
    assert abs(a[1] - 0.3) < 1e-9
    assert abs(a[2] - 0.8) < 1e-9


# ── calving ──────────────────────────────────────────────────────────────────


def test_calve_below_threshold_returns_none():
    t = _t("calve_small")
    _deposit(f"calve small node {_NONCE}", [1.0, 0.0, 0.0], t)
    assert calve(table=t, threshold=100) is None


def test_calve_splits_into_two_children():
    t = _t("calve_split")
    n_nodes = 20
    for i in range(n_nodes // 2):
        _deposit(f"calve north cluster {i} {_NONCE}", [1.0, 0.1 * i / n_nodes, 0.0], t)
    for i in range(n_nodes // 2):
        _deposit(f"calve south cluster {i} {_NONCE}", [-1.0, 0.1 * i / n_nodes, 0.0], t)

    result = calve(table=t, threshold=n_nodes)
    assert result is not None
    assert len(result["children"]) == 2
    assert result["sizes"][0] + result["sizes"][1] == n_nodes
    assert result["sizes"][0] > 0
    assert result["sizes"][1] > 0

    child_a, child_b = result["children"]
    _TABLES.append(child_a)
    _TABLES.append(child_b)

    from cairn.devices.librarian.trees import _leaf_rows
    conn = store.connect()
    try:
        parent_rows = _leaf_rows(table=t, conn=conn)
        assert len(parent_rows) == 0

        a_rows = _leaf_rows(table=child_a, conn=conn)
        b_rows = _leaf_rows(table=child_b, conn=conn)
        assert len(a_rows) == result["sizes"][0]
        assert len(b_rows) == result["sizes"][1]

        a_ids = {r["node_id"] for r in a_rows}
        b_ids = {r["node_id"] for r in b_rows}
        assert len(a_ids & b_ids) == 0
    finally:
        conn.close()


def test_calve_children_have_distinct_attractors():
    t = _t("calve_attr")
    for i in range(10):
        _deposit(f"calve attr east {i} {_NONCE}", [1.0, 0.0, 0.05 * i], t)
    for i in range(10):
        _deposit(f"calve attr west {i} {_NONCE}", [-1.0, 0.0, 0.05 * i], t)

    result = calve(table=t, threshold=20)
    assert result is not None

    child_a, child_b = result["children"]
    _TABLES.append(child_a)
    _TABLES.append(child_b)

    a_attr = attractor(table=child_a)
    b_attr = attractor(table=child_b)
    assert a_attr is not None
    assert b_attr is not None
    sim = cosine(a_attr, b_attr)
    assert sim < 0.5


def test_calve_links_survive_split():
    t = _t("calve_links")
    n_nodes = 20
    for i in range(n_nodes // 2):
        _deposit(f"calve link north {i} {_NONCE}", [1.0, 0.1 * i / n_nodes, 0.0], t)
    for i in range(n_nodes // 2):
        _deposit(f"calve link south {i} {_NONCE}", [-1.0, 0.1 * i / n_nodes, 0.0], t)

    nid_n0 = node_id_for(f"calve link north 0 {_NONCE}")
    nid_n1 = node_id_for(f"calve link north 1 {_NONCE}")
    nid_s0 = node_id_for(f"calve link south 0 {_NONCE}")

    link(nid_n0, nid_n1, 0.9)
    link(nid_n0, nid_s0, 0.3)
    traverse_link(nid_n0, nid_n1)
    traverse_link(nid_n0, nid_n1)

    pre_links = linked(nid_n0)
    pre_weights = {(l["source_id"], l["target_id"]): l["weight"] for l in pre_links}
    pre_traversals = {l["link_id"]: l["traversals"] for l in pre_links}
    assert len(pre_links) == 2

    result = calve(table=t, threshold=n_nodes)
    assert result is not None
    assert result["links_verified"] >= 2

    child_a, child_b = result["children"]
    _TABLES.append(child_a)
    _TABLES.append(child_b)

    post_links = linked(nid_n0)
    assert len(post_links) == 2
    for lnk in post_links:
        assert lnk["weight"] == pre_weights[(lnk["source_id"], lnk["target_id"])]
        assert lnk["traversals"] == pre_traversals[lnk["link_id"]]


# ── bidirectional links ──────────────────────────────────────────────────────


def test_link_id_is_direction_independent():
    assert link_id_for("aaa", "bbb") == link_id_for("bbb", "aaa")
    assert link_id_for("aaa", "bbb") != link_id_for("aaa", "ccc")


def test_link_creates_and_updates():
    t = _t("link_basic")
    _deposit(f"link node alpha {_NONCE}", [1.0, 0.0, 0.0], t)
    _deposit(f"link node beta {_NONCE}", [0.9, 0.1, 0.0], t)
    nid_a = node_id_for(f"link node alpha {_NONCE}")
    nid_b = node_id_for(f"link node beta {_NONCE}")

    r1 = link(nid_a, nid_b, 0.95)
    assert r1["updated"] is False

    r2 = link(nid_a, nid_b, 0.97)
    assert r2["updated"] is True
    assert r2["link_id"] == r1["link_id"]


def test_linked_returns_both_directions():
    t = _t("link_bidir")
    _deposit(f"linked bidir alpha {_NONCE}", [1.0, 0.0, 0.0], t)
    _deposit(f"linked bidir beta {_NONCE}", [0.0, 1.0, 0.0], t)
    nid_a = node_id_for(f"linked bidir alpha {_NONCE}")
    nid_b = node_id_for(f"linked bidir beta {_NONCE}")

    link(nid_a, nid_b, 0.80)

    from_a = linked(nid_a)
    from_b = linked(nid_b)
    assert len(from_a) == 1
    assert len(from_b) == 1
    assert from_a[0]["link_id"] == from_b[0]["link_id"]


def test_traverse_increments_count():
    t = _t("link_trav")
    _deposit(f"traverse node one {_NONCE}", [1.0, 0.0, 0.0], t)
    _deposit(f"traverse node two {_NONCE}", [0.0, 1.0, 0.0], t)
    nid_a = node_id_for(f"traverse node one {_NONCE}")
    nid_b = node_id_for(f"traverse node two {_NONCE}")

    link(nid_a, nid_b, 0.75)
    r1 = traverse_link(nid_a, nid_b)
    assert r1["traversals"] == 1
    r2 = traverse_link(nid_a, nid_b)
    assert r2["traversals"] == 2
    r3 = traverse_link(nid_b, nid_a)
    assert r3["traversals"] == 3


def test_traverse_nonexistent_returns_none():
    assert traverse_link("nonexistent_a", "nonexistent_b") is None


def test_link_neighbors_creates_links():
    t = _t("link_neigh")
    _deposit(f"link neighbor center {_NONCE}", [1.0, 0.0, 0.0], t)
    _deposit(f"link neighbor near {_NONCE}", [0.95, 0.05, 0.0], t)
    _deposit(f"link neighbor far {_NONCE}", [0.0, 0.0, 1.0], t)
    nid_center = node_id_for(f"link neighbor center {_NONCE}")

    results = link_neighbors(nid_center, k=2, table=t)
    assert len(results) == 2

    links = linked(nid_center)
    assert len(links) == 2


# ── multi-tree routing ───────────────────────────────────────────────────────


def test_route_ranks_by_attractor_proximity():
    t_north = _t("route_north")
    t_south = _t("route_south")
    for i in range(3):
        _deposit(f"route north node {i} {_NONCE}", [1.0, 0.1 * i, 0.0], t_north)
    for i in range(3):
        _deposit(f"route south node {i} {_NONCE}", [-1.0, 0.1 * i, 0.0], t_south)

    query_north = [0.9, 0.0, 0.0]
    ranked = route(query_north, tables=[t_north, t_south])
    assert len(ranked) == 2
    assert ranked[0]["table"] == t_north
    assert ranked[0]["similarity"] > ranked[1]["similarity"]

    query_south = [-0.9, 0.0, 0.0]
    ranked_s = route(query_south, tables=[t_north, t_south])
    assert ranked_s[0]["table"] == t_south


def test_route_skips_empty_trees():
    t_full = _t("route_full")
    t_empty = _t("route_empty")
    ensure_trees(table=t_empty)
    _deposit(f"route full node {_NONCE}", [1.0, 0.0, 0.0], t_full)

    ranked = route([1.0, 0.0, 0.0], tables=[t_full, t_empty])
    assert len(ranked) == 1
    assert ranked[0]["table"] == t_full


def test_route_respects_k():
    tables = []
    for i in range(4):
        t = _t(f"route_k_{i}")
        tables.append(t)
        _deposit(f"route k node {i} {_NONCE}", [1.0 - 0.2 * i, 0.2 * i, 0.0], t)

    ranked = route([1.0, 0.0, 0.0], tables=tables, k=2)
    assert len(ranked) == 2


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
