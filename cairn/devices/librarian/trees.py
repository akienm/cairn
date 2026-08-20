"""librarian/trees.py — the graph-tree store: the librarian's spine, db_domain's first tenant.

Three-table schema (paper §3.1, §6.4, ticket node-embedding-leaf-separation):
  - **cairn_nodes**: what is remembered, tree-free. node_id + content + provenance +
    standing + created. One shared set per database, owned by the librarian (Law 6).
  - **cairn_embeddings**: renderings as coordinates. embedding_id + node_id + vector +
    render_method. Many per node (one today), derived, owned by the librarian.
  - **per-tree leaf tables**: how a node is found. leaf_id + node_id + embedding_id.
    Each consumer keeps its own leaf table (the existing *_nodes tables become these).

Akien's founding facts (settled 2026-07-22): "the embedding IS the path through the graph
trees" — edges are DERIVED from vector proximity, never stored. The librarian OWNS the
nodes and embeddings; each consumer owns its leaf table through db_domain's owner-gate.

THE CONTRACT
  - A node is content + PROVENANCE + standing — no tree, no vector (those belong to
    embeddings and leaves). The deposit door refuses a node nobody can trace.
  - Every node is born ``standing = "hypothesis"`` (Law 3). Tenure is a MEASUREMENT.
  - Edges are NEVER stored. ``nearest`` walks a leaf table, joins through embeddings to
    get vectors, and computes cosine. Bounded weighted similarity links (§6.2) add a
    learned layer: stored associations populated on deposit and reinforced by traversal.
  - Dimensions are physics: the first embedding deposited sets the tree's dimension.
  - A duplicate deposit (same content, ANY tree) writes no new node row — the same claim
    IS the same node however many trees index it (§4.3, constraint 4).

This module is import-pure toward the network: vectors arrive as DATA, the database is
reached only through db_domain (the sole path; Law 4). The proof pins both by AST allowlist.
"""

from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone

from cairn.tools.base.device import BaseDevice
from cairn.devices.db_domain import store

NODES_TABLE = "cairn_nodes"
EMBEDDINGS_TABLE = "cairn_embeddings"
NODES = "librarian_nodes"
OWNER = "librarian"

_MIN_CONTENT_CHARS = 8

_NODE_COLUMNS = {
    "node_id": "text PRIMARY KEY",
    "content": "text NOT NULL",
    "provenance": "jsonb NOT NULL",
    "standing": "text NOT NULL",
    "created": "timestamptz NOT NULL DEFAULT now()",
}

_EMBEDDING_COLUMNS = {
    "embedding_id": "text PRIMARY KEY",
    "node_id": "text NOT NULL",
    "vector": "jsonb NOT NULL",
    "render_method": "text NOT NULL",
}

_LEAF_COLUMNS = {
    "leaf_id": "text PRIMARY KEY",
    "node_id": "text NOT NULL",
    "embedding_id": "text NOT NULL",
}

LINKS_TABLE = "cairn_links"

_LINK_COLUMNS = {
    "link_id": "text PRIMARY KEY",
    "source_id": "text NOT NULL",
    "target_id": "text NOT NULL",
    "weight": "real NOT NULL",
    "traversals": "integer NOT NULL DEFAULT 0",
    "created": "timestamptz NOT NULL DEFAULT now()",
}

CALVE_THRESHOLD = 5000


class DepositRefused(RuntimeError):
    """A deposit the door cannot honestly accept — refused loudly, nothing landed (Law 7)."""


class WalkRefused(RuntimeError):
    """A walk that would answer a different question than the one asked — refused, not guessed."""


class RefutationRefused(RuntimeError):
    """A retirement the door cannot honestly accept — every lack named in ONE pass, nothing landed.

    One pass rather than one-per-run is the point: a caller that fixes a lack and is
    refused for the next one learns the door's shape by attrition, and a human typing a
    correction gets told the whole truth once (Law 7 at a diagnostic surface)."""


# Who may retire an EARNED node. The borrow is cairn/machines/ruling's supersession rule —
# "an unconfirmed reading cannot retire a confirmed act; that would be my guess outvoting
# his signature" — cited in the charter's `entry`, never imported (charter falsifier 7).
# Read as an ALLOWLIST, not a denylist: an unrecognized source is refused against earned
# knowledge, because red is the default and an unknown hand is not a known-safe one (CP6).
_REFUTER_AUTHORITIES = frozenset({"correction"})


def node_id_for(content: str) -> str:
    """Deterministic identity: the same content IS the same node, regardless of tree."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def embedding_id_for(node_id: str, render_method: str) -> str:
    """Deterministic embedding identity: same node + same rendering = same embedding."""
    return hashlib.sha256(f"{node_id}\n{render_method}".encode("utf-8")).hexdigest()[:16]


def leaf_id_for(node_id: str, embedding_id: str) -> str:
    """Deterministic leaf identity within a leaf table."""
    return hashlib.sha256(f"{node_id}\n{embedding_id}".encode("utf-8")).hexdigest()[:16]


def link_id_for(a: str, b: str) -> str:
    """Deterministic, direction-independent link identity."""
    pair = "\n".join(sorted([a, b]))
    return hashlib.sha256(pair.encode("utf-8")).hexdigest()[:16]


def _norm(s: str) -> str:
    return " ".join(s.split())


def _check_vector(vector, *, who: str) -> list[float]:
    """A vector is a non-empty list of finite numbers with direction (nonzero magnitude).

    A zero vector has no direction, so proximity to it is undefined — cosine would divide
    by zero or, patched, silently rank everything equal. Refused, both doors."""
    if not isinstance(vector, (list, tuple)) or not vector:
        raise (DepositRefused if who == "deposit" else WalkRefused)(
            f"{who}: vector must be a non-empty list of numbers, got "
            f"{type(vector).__name__}{'' if vector else ' (empty)'}"
        )
    try:
        v = [float(x) for x in vector]
    except (TypeError, ValueError):
        raise (DepositRefused if who == "deposit" else WalkRefused)(
            f"{who}: vector carries a non-numeric entry — refusing to coerce"
        ) from None
    if not all(math.isfinite(x) for x in v):
        raise (DepositRefused if who == "deposit" else WalkRefused)(
            f"{who}: vector carries a non-finite entry (nan/inf) — that is not a direction"
        )
    if not any(x != 0.0 for x in v):
        raise (DepositRefused if who == "deposit" else WalkRefused)(
            f"{who}: zero vector — no direction, so proximity is undefined; refusing to "
            "rank everything as equally near"
        )
    return v


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity — the derived edge's weight. Callers guarantee nonzero vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def ensure_trees(*, table: str = NODES, owner: str = OWNER, conn=None) -> None:
    """The shared tables + the caller's leaf table, owner-gated into existence."""
    store.create_owned_table(NODES_TABLE, OWNER, _NODE_COLUMNS, conn=conn)
    store.create_owned_table(EMBEDDINGS_TABLE, OWNER, _EMBEDDING_COLUMNS, conn=conn)
    store.create_owned_table(table, owner, _LEAF_COLUMNS, conn=conn)


def _leaf_rows(*, table: str, conn) -> list[dict]:
    """All rows in a leaf table, joined through embedding->node."""
    from psycopg2 import sql as psql
    from psycopg2.extras import RealDictCursor
    stmt = psql.SQL(
        "SELECT l.leaf_id, n.node_id, n.content, e.vector, n.provenance, "
        "n.standing, n.created, e.embedding_id, e.render_method "
        "FROM {leaf} l "
        "JOIN {embed} e ON l.embedding_id = e.embedding_id "
        "JOIN {node} n ON l.node_id = n.node_id"
    ).format(
        leaf=psql.Identifier(table),
        embed=psql.Identifier(EMBEDDINGS_TABLE),
        node=psql.Identifier(NODES_TABLE),
    )
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(stmt)
        return [dict(r) for r in cur.fetchall()]


def deposit(content: str, vector, provenance: dict, *,
            tree: str = "commons", table: str = NODES, owner: str = OWNER,
            render_method: str = "embed:default",
            conn=None) -> dict:
    """The deposit door: one node in, judged before it lands.

    Three-table write: node -> cairn_nodes, embedding -> cairn_embeddings,
    leaf -> the caller's leaf table. A duplicate node (same content, ANY tree) appends
    provenance as an attestation; a new leaf is still written for this tree.
    """
    if not isinstance(content, str) or len(_norm(content)) < _MIN_CONTENT_CHARS:
        raise DepositRefused(
            f"deposit: content is "
            f"{len(_norm(content)) if isinstance(content, str) else 'not a string'} "
            f"normalized chars — floor is {_MIN_CONTENT_CHARS}. A node distilled from "
            "near-nothing is invention; nothing landed."
        )
    v = _check_vector(vector, who="deposit")
    if not isinstance(provenance, dict) or not str(provenance.get("source", "")).strip():
        raise DepositRefused(
            f"deposit: provenance must be a dict naming a non-empty 'source', got "
            f"{provenance!r}. A node nobody can trace is fabricated attribution as a "
            "permanent resident; nothing landed."
        )

    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        nid = node_id_for(content)
        eid = embedding_id_for(nid, render_method)
        lid = leaf_id_for(nid, eid)

        existing_node = store.read(NODES_TABLE, where="node_id = %s", params=(nid,), conn=own)
        node_is_dup = bool(existing_node)

        if node_is_dup:
            prior = existing_node[0]["provenance"] or {}
            attests = list(prior.get("attestations") or [])
            attests.append({**provenance, "at": datetime.now(timezone.utc).isoformat()})
            merged = {**prior, "attestations": attests}
            store.update(NODES_TABLE, OWNER, {"provenance": merged},
                         where="node_id = %s", params=(nid,), conn=own)
        else:
            store.write(NODES_TABLE, OWNER, {
                "node_id": nid,
                "content": content,
                "provenance": provenance,
                "standing": "hypothesis",
            }, conn=own)

        existing_emb = store.read(EMBEDDINGS_TABLE, where="embedding_id = %s", params=(eid,), conn=own)
        if not existing_emb:
            siblings = _leaf_rows(table=table, conn=own)
            if siblings:
                tree_dim = len(siblings[0]["vector"])
                if len(v) != tree_dim:
                    raise DepositRefused(
                        f"deposit: vector dim {len(v)} vs tree {tree!r} dim {tree_dim} — a "
                        "mixed-dimension tree cannot be walked; refusing (the first deposit "
                        "set the tree's dimension)."
                    )
            store.write(EMBEDDINGS_TABLE, OWNER, {
                "embedding_id": eid,
                "node_id": nid,
                "vector": v,
                "render_method": render_method,
            }, conn=own)

        existing_leaf = store.read(table, where="leaf_id = %s", params=(lid,), conn=own)
        leaf_is_dup = bool(existing_leaf)
        if not leaf_is_dup:
            store.write(table, owner, {
                "leaf_id": lid,
                "node_id": nid,
                "embedding_id": eid,
            }, conn=own)

        return {"node_id": nid, "duplicate": node_is_dup and leaf_is_dup,
                "dim": len(v), "provenance_appended": node_is_dup}
    finally:
        if conn is None:
            own.close()


def corroborate(node_id: str, question: str, *, promote_at: int,
                tree: str = "commons", table: str = NODES, owner: str = OWNER,
                conn=None) -> dict:
    """The earning write on the SHARED node (cairn_nodes), fired by the
    librarian's resolution event — never by a clock.

    The tree/table params kept for API compatibility but the attestation
    lands on the shared node.
    """
    own = conn or store.connect()
    try:
        rows = store.read(NODES_TABLE, where="node_id = %s",
                          params=(node_id,), conn=own)
        if not rows:
            raise DepositRefused(
                f"corroborate: no standing node {node_id!r} — nothing to attest")
        row = rows[0]
        prov = dict(row["provenance"] or {})
        birth_q = prov.get("question")
        attests = list(prov.get("attestations") or [])
        distinct = {a.get("question") for a in attests
                    if a.get("question") and a.get("question") != birth_q}
        changes: dict = {}
        corroborated = False
        if question != birth_q and question not in distinct:
            attests.append({"source": "corroboration", "question": question,
                            "at": datetime.now(timezone.utc).isoformat()})
            distinct.add(question)
            changes["provenance"] = {**prov, "attestations": attests}
            corroborated = True
        promoted = False
        if len(distinct) >= promote_at and row["standing"] != "earned":
            changes["standing"] = "earned"
            promoted = True
        if changes:
            store.update(NODES_TABLE, OWNER, changes, where="node_id = %s",
                         params=(node_id,), conn=own)
        return {"corroborated": corroborated, "promoted": promoted, "distinct": len(distinct)}
    finally:
        if conn is None:
            own.close()


def _may_retire_earned(refuter: dict) -> bool:
    """Is this refuter allowed to outvote corroborated knowledge?

    Yes if it has EARNED tenure itself, or if its provenance names it an authority — today
    that means a stated correction, which is an INPUT from outside and therefore not the
    system's own guess. Law 9 forces this second arm: "no past artifact outranks him now",
    and a node in this tree is a past artifact. A gate keyed on standing ALONE would make
    Akien's correction unable to retire an earned node, since every node is born a
    hypothesis (the deposit door's contract) — the gate would then be protecting the
    corpus from its own author.
    """
    if refuter.get("standing") == "earned":
        return True
    source = str((refuter.get("provenance") or {}).get("source", "")).strip()
    return source in _REFUTER_AUTHORITIES


def refute(node_id: str, refuter_id: str, evidence: str, *,
           tree: str = "commons", table: str = NODES, owner: str = OWNER,
           minted_this_crossing=(), conn=None) -> dict:
    """The retirement door on the SHARED node (cairn_nodes).

    tree/table params kept for API compatibility; reads/writes go to cairn_nodes.
    """
    lacks: list[str] = []
    ev = evidence.strip() if isinstance(evidence, str) else ""
    if not ev:
        lacks.append(
            f"evidence is {'empty' if isinstance(evidence, str) else f'{type(evidence).__name__}, not a string'} "
            "— a retirement nobody can read back is an unexplained hole in the record"
        )

    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        seen: dict[str, dict] = {}
        for wanted in (node_id, refuter_id):
            if wanted in seen:
                continue
            found = store.read(NODES_TABLE, where="node_id = %s",
                               params=(wanted,), conn=own)
            if found:
                seen[wanted] = found[0]
        target = seen.get(node_id)
        refuter = seen.get(refuter_id)

        if target is None:
            lacks.append(f"no standing node {node_id!r} — nothing to retire")
        if refuter is None:
            lacks.append(
                f"no standing node {refuter_id!r} — the refuter must itself "
                "be in the record, or the retirement cites nothing"
            )
        if node_id == refuter_id:
            lacks.append(
                f"{node_id!r} would refute itself — a node arguing itself down is not "
                "evidence, and the receipt would cite the thing it retired"
            )
        if refuter_id in set(minted_this_crossing):
            lacks.append(
                f"crossing honesty: {refuter_id!r} was minted during this crossing, so it "
                "may not retire anything in it — that is a manufactured revision"
            )
        if target is not None and target["standing"] == "refuted":
            lacks.append(
                f"{node_id!r} is already refuted — a second retirement would overwrite the "
                "first one's receipt, and the first refuter is who the record owes"
            )
        if refuter is not None and refuter["standing"] == "refuted":
            lacks.append(
                f"the refuter {refuter_id!r} is itself refuted — retired knowledge does not "
                "get to retire more"
            )
        if (target is not None and refuter is not None
                and target["standing"] == "earned" and not _may_retire_earned(refuter)):
            lacks.append(
                f"the standing gate: {node_id!r} is EARNED (corroborated across distinct "
                f"crossings) and the refuter {refuter_id!r} is standing "
                f"{refuter['standing']!r} from source "
                f"{str((refuter['provenance'] or {}).get('source', ''))!r} — a guess does not "
                f"outvote a signature. Authorities: {sorted(_REFUTER_AUTHORITIES)}"
            )

        if lacks:
            raise RefutationRefused(
                "refute: " + "; ".join(lacks) + ". Nothing landed."
            )

        prov = dict(target["provenance"] or {})
        attests = list(prov.get("attestations") or [])
        attests.append({"source": "refutation", "refuter": refuter_id, "evidence": ev,
                        "at": datetime.now(timezone.utc).isoformat()})
        store.update(NODES_TABLE, OWNER,
                     {"standing": "refuted", "provenance": {**prov, "attestations": attests}},
                     where="node_id = %s", params=(node_id,), conn=own)
        return {"refuted": True, "node_id": node_id, "refuter": refuter_id,
                "was": target["standing"], "attestations": len(attests)}
    finally:
        if conn is None:
            own.close()


def tree_state(tree: str, *, table: str = NODES, owner: str = OWNER, conn=None) -> dict:
    """The tree's fingerprint: ``{"digest", "nodes"}`` — same members, same digest.

    Reads the leaf table to enumerate what nodes this tree contains.
    """
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        ids = sorted(r["node_id"] for r in _leaf_rows(table=table, conn=own))
        digest = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()[:16] if ids else "empty"
        return {"digest": digest, "nodes": len(ids)}
    finally:
        if conn is None:
            own.close()


# ── attractor ────────────────────────────────────────────────────────────────


def attractor(*, table: str = NODES, owner: str = OWNER, conn=None) -> list[float] | None:
    """The tree's attractor: centroid of all embedding vectors in this leaf table.

    None for an empty tree (no leaves = no direction). The attractor IS the
    tree's identity in vector space — routing (ρ) compares queries to it, and
    calving triggers when the attractor stops representing its members.
    """
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        rows = _leaf_rows(table=table, conn=own)
        if not rows:
            return None
        dim = len(rows[0]["vector"])
        centroid = [0.0] * dim
        for r in rows:
            v = r["vector"]
            for i in range(dim):
                centroid[i] += float(v[i])
        n = len(rows)
        return [c / n for c in centroid]
    finally:
        if conn is None:
            own.close()


# ── calving ──────────────────────────────────────────────────────────────────


def _kmeans2(vectors: list[list[float]], max_iter: int = 20) -> tuple[list[int], list[list[float]]]:
    """2-means clustering. Returns (assignments, [centroid_0, centroid_1])."""
    n = len(vectors)
    if n < 2:
        return [0] * n, [list(vectors[0])] if vectors else []
    dim = len(vectors[0])
    centroid = [sum(v[d] for v in vectors) / n for d in range(dim)]
    s0 = max(range(n), key=lambda i: 1.0 - cosine(vectors[i], centroid))
    s1 = max(range(n), key=lambda i: 1.0 - cosine(vectors[i], vectors[s0]))
    if s0 == s1:
        return [0] * n, [centroid]
    centroids = [list(vectors[s0]), list(vectors[s1])]
    assignments = [0] * n
    for _ in range(max_iter):
        changed = False
        for i, v in enumerate(vectors):
            a = 0 if cosine(v, centroids[0]) >= cosine(v, centroids[1]) else 1
            if a != assignments[i]:
                assignments[i] = a
                changed = True
        if not changed:
            break
        for c in range(2):
            members = [vectors[i] for i, a in enumerate(assignments) if a == c]
            if members:
                centroids[c] = [sum(m[d] for m in members) / len(members) for d in range(dim)]
    return assignments, centroids


def calve(*, table: str = NODES, owner: str = OWNER,
          threshold: int = CALVE_THRESHOLD, conn=None) -> dict | None:
    """Split a leaf table into two child tables by 2-means clustering.

    Returns None if the table has fewer than ``threshold`` leaves (no split needed).
    On split: creates ``{table}_0`` and ``{table}_1``, moves every leaf into the
    nearer child, and empties the parent. The parent table stays (its name may be
    held by callers); the children are the new walk targets.
    """
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        rows = _leaf_rows(table=table, conn=own)
        if len(rows) < threshold:
            return None

        vectors = [[float(x) for x in r["vector"]] for r in rows]
        assignments, centroids = _kmeans2(vectors)

        if len(centroids) < 2 or all(a == 0 for a in assignments):
            return None

        child_a = f"{table}_0"
        child_b = f"{table}_1"
        store.create_owned_table(child_a, owner, _LEAF_COLUMNS, conn=own)
        store.create_owned_table(child_b, owner, _LEAF_COLUMNS, conn=own)

        sizes = [0, 0]
        for i, r in enumerate(rows):
            target = child_a if assignments[i] == 0 else child_b
            store.write(target, owner, {
                "leaf_id": r["leaf_id"],
                "node_id": r["node_id"],
                "embedding_id": r["embedding_id"],
            }, conn=own)
            sizes[assignments[i]] += 1

        from psycopg2 import sql as psql
        with own.cursor() as cur:
            cur.execute(psql.SQL("DELETE FROM {}").format(psql.Identifier(table)))

        return {
            "children": [child_a, child_b],
            "sizes": sizes,
            "attractors": centroids,
        }
    finally:
        if conn is None:
            own.close()


# ── bidirectional links (§6.2) ───────────────────────────────────────────────


def _ensure_links(conn) -> None:
    store.create_owned_table(LINKS_TABLE, OWNER, _LINK_COLUMNS, conn=conn)


def link(source_id: str, target_id: str, weight: float, *, conn=None) -> dict:
    """Create or update a bidirectional link between two nodes."""
    own = conn or store.connect()
    try:
        _ensure_links(own)
        lid = link_id_for(source_id, target_id)
        existing = store.read(LINKS_TABLE, where="link_id = %s", params=(lid,), conn=own)
        if existing:
            store.update(LINKS_TABLE, OWNER, {"weight": weight},
                         where="link_id = %s", params=(lid,), conn=own)
            return {"link_id": lid, "updated": True}
        store.write(LINKS_TABLE, OWNER, {
            "link_id": lid,
            "source_id": source_id,
            "target_id": target_id,
            "weight": weight,
        }, conn=own)
        return {"link_id": lid, "updated": False}
    finally:
        if conn is None:
            own.close()


def link_neighbors(node_id: str, *, k: int = 5, table: str = NODES,
                   owner: str = OWNER, conn=None) -> list[dict]:
    """Create links between a node and its k nearest neighbors in the tree."""
    own = conn or store.connect()
    try:
        _ensure_links(own)
        emb = store.read(EMBEDDINGS_TABLE, where="node_id = %s",
                         params=(node_id,), conn=own)
        if not emb:
            return []
        vector = [float(x) for x in emb[0]["vector"]]
        nears = nearest(vector, k=k + 1, table=table, conn=own)
        results = []
        for n in nears:
            if n["node_id"] != node_id:
                r = link(node_id, n["node_id"], n["similarity"], conn=own)
                results.append(r)
        if len(results) > k:
            results = results[:k]
        return results
    finally:
        if conn is None:
            own.close()


def traverse_link(source_id: str, target_id: str, *, conn=None) -> dict | None:
    """Record a link traversal — increment the use count."""
    own = conn or store.connect()
    try:
        _ensure_links(own)
        lid = link_id_for(source_id, target_id)
        existing = store.read(LINKS_TABLE, where="link_id = %s", params=(lid,), conn=own)
        if not existing:
            return None
        new_count = existing[0]["traversals"] + 1
        store.update(LINKS_TABLE, OWNER, {"traversals": new_count},
                     where="link_id = %s", params=(lid,), conn=own)
        return {"link_id": lid, "traversals": new_count}
    finally:
        if conn is None:
            own.close()


def linked(node_id: str, *, conn=None) -> list[dict]:
    """All stored links for a node, both directions, ordered by weight."""
    own = conn or store.connect()
    try:
        _ensure_links(own)
        from psycopg2 import sql as psql
        from psycopg2.extras import RealDictCursor
        with own.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                psql.SQL(
                    "SELECT l.link_id, l.source_id, l.target_id, l.weight, "
                    "l.traversals, l.created, n.content, n.standing "
                    "FROM {links} l "
                    "JOIN {nodes} n ON n.node_id = CASE "
                    "  WHEN l.source_id = %s THEN l.target_id "
                    "  ELSE l.source_id END "
                    "WHERE l.source_id = %s OR l.target_id = %s "
                    "ORDER BY l.weight DESC"
                ).format(
                    links=psql.Identifier(LINKS_TABLE),
                    nodes=psql.Identifier(NODES_TABLE),
                ),
                (node_id, node_id, node_id),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        if conn is None:
            own.close()


# ── multi-tree routing ρ(q) ─────────────────────────────────────────────────


def route(vector, *, tables: list[str], k: int = 3, conn=None) -> list[dict]:
    """Multi-tree routing: rank trees by attractor proximity to the query vector.

    Each tree's attractor (centroid) is compared to the query; the top k trees
    are returned. An empty tree (no attractor) is skipped.
    """
    v = _check_vector(vector, who="route")
    own = conn or store.connect()
    try:
        scored = []
        for t in tables:
            a = attractor(table=t, owner=OWNER, conn=own)
            if a is not None:
                scored.append({
                    "table": t,
                    "similarity": cosine(v, a),
                })
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:k]
    finally:
        if conn is None:
            own.close()


# ── walks ────────────────────────────────────────────────────────────────────


def nearest(vector, *, k: int = 5, tree: str = "commons",
            table: str = NODES, owner: str = OWNER, conn=None) -> list[dict]:
    """The walk: the k nodes nearest the query vector, by cosine.

    Reads the leaf table (three-table join) to get content + vector + provenance.
    """
    if not isinstance(k, int) or k < 1:
        raise WalkRefused(f"nearest: k must be a positive int, got {k!r}")
    v = _check_vector(vector, who="nearest")
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        rows = _leaf_rows(table=table, conn=own)
        if not rows:
            return []
        tree_dim = len(rows[0]["vector"])
        if len(v) != tree_dim:
            raise WalkRefused(
                f"nearest: query dim {len(v)} vs tree {tree!r} dim {tree_dim} — "
                "answering across dimensions would be a silent wrong answer; refused."
            )
        ranked = sorted(
            ({"node_id": r["node_id"], "content": r["content"],
              "similarity": cosine(v, [float(x) for x in r["vector"]]),
              "provenance": r["provenance"], "standing": r["standing"],
              "created": r["created"]}
             for r in rows),
            key=lambda n: n["similarity"], reverse=True)
        return ranked[:k]
    finally:
        if conn is None:
            own.close()


def neighbors(node_id: str, *, k: int = 5, tree: str = "commons",
              table: str = NODES, owner: str = OWNER, conn=None) -> list[dict]:
    """A node's derived edges: its k nearest siblings in this tree, itself excluded."""
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        emb = store.read(EMBEDDINGS_TABLE, where="node_id = %s",
                         params=(node_id,), conn=own)
        if not emb:
            raise WalkRefused(
                f"neighbors: node {node_id!r} has no embedding — a ghost has no "
                "neighborhood (an empty [] would claim 'isolated', which is a different fact)."
            )
        ranked = nearest([float(x) for x in emb[0]["vector"]], k=k + 1, tree=tree,
                         table=table, conn=own)
        return [n for n in ranked if n["node_id"] != node_id][:k]
    finally:
        if conn is None:
            own.close()


# ── the device ───────────────────────────────────────────────────────────────


class LibrarianDevice(BaseDevice):
    """The librarian (carries CP1-CP6; reports the Form v0 #2 surface).

    v0 surface = the graph-tree spine: ``deposit`` (a write-crossing — breadcrumbed,
    DEPOSITED and DUPLICATE alike) and the walks ``nearest`` / ``neighbors`` (reads —
    silent, per the extractor's reads-silent rule). The core resolve-or-generate loop,
    the summarizer, and the chat face land on this same device as later stones.
    """

    def __init__(self) -> None:
        super().__init__()
        self._deposits = 0
        self._verdicts = {"DEPOSITED": 0, "DUPLICATE": 0}
        self._last_node: str | None = None
        self._chat = None        # the conversational face — attached by the shim at wake

    @property
    def device_id(self) -> str:
        return "librarian"

    def deposit(self, content: str, vector, provenance: dict, *,
                tree: str = "commons", table: str = NODES,
                render_method: str = "embed:default", conn=None) -> dict:
        """One deposit crossing — judged at the door, breadcrumbed after it lands."""
        result = deposit(content, vector, provenance, tree=tree, table=table,
                         render_method=render_method, conn=conn)
        verdict = "DUPLICATE" if result["duplicate"] else "DEPOSITED"
        self._deposits += 1
        self._verdicts[verdict] += 1
        self._last_node = result["node_id"]
        # GATE CONTACT: a node crossed the deposit door (or was turned back as already
        # standing — that verdict breadcrumbs too; a write avoided is the cache's shape
        # and worth a trace). Thin: pointer is the node, values the verdict and where.
        self.emit("deposit", pointer=result["node_id"],
                  values={"verdict": verdict, "tree": tree, "dim": result["dim"]})
        return result

    def nearest(self, vector, *, k: int = 5, tree: str = "commons",
                table: str = NODES, conn=None) -> list[dict]:
        return nearest(vector, k=k, tree=tree, table=table, conn=conn)

    def neighbors(self, node_id: str, *, k: int = 5, tree: str = "commons",
                  table: str = NODES, conn=None) -> list[dict]:
        return neighbors(node_id, k=k, tree=tree, table=table, conn=conn)

    def attractor(self, *, table: str = NODES, conn=None) -> list[float] | None:
        return attractor(table=table, conn=conn)

    def calve(self, *, table: str = NODES, threshold: int = CALVE_THRESHOLD,
              conn=None) -> dict | None:
        result = calve(table=table, threshold=threshold, conn=conn)
        if result:
            self.emit("calve", pointer=table,
                      values={"children": result["children"],
                              "sizes": result["sizes"]})
        return result

    def route(self, vector, *, tables: list[str], k: int = 3,
              conn=None) -> list[dict]:
        return route(vector, tables=tables, k=k, conn=conn)

    def linked(self, node_id: str, *, conn=None) -> list[dict]:
        return linked(node_id, conn=conn)

    # --- the chat window: a surface the base shim class understands ---------

    def attach_chat(self, session) -> None:
        """Wire the conversational face (a ChatSession). Live composition happens in
        the SHIM at wake time — this device stays import-pure toward the host. The
        chat window is a declared PANE (below): the librarian owns a page the ONE web
        server displays through the standard shim machinery — never a server, a
        route, or a port of its own."""
        self._chat = session

    def declared_panes(self) -> list[dict]:
        """The chat window, offered as a pane. Unattached (nobody woke the face) it
        is honestly ABSENT-with-reason on the page, not a missing surface."""
        return [{"kind": "chat", "label": "Chat",
                 "handler": None if self._chat is None else self._chat.page}]

    def receive(self, envelope: dict) -> dict:
        """Incoming mail (web_server → shim → here: the designed path, in-process
        v0). Channel ``chat`` carries one utterance to the face. Anything this
        device cannot honestly process refuses loudly — mail never vanishes
        (Law 7)."""
        channel = envelope.get("channel")
        if channel != "chat":
            raise ValueError(
                f"librarian: no handler for channel {channel!r} — this device "
                "receives 'chat' (one utterance per envelope)")
        if self._chat is None:
            raise RuntimeError(
                "librarian: a chat envelope arrived but no face is attached — the "
                "shim wires the ChatSession at wake; an unwired face refuses, it "
                "does not pretend")
        return self._chat.turn(str((envelope.get("body") or {}).get("utterance", "")))

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The librarian: owner of the graph trees (db_domain's first tenant). "
            "v0 is the spine — a provenance-gated deposit door and proximity walks whose "
            "edges are derived from the vectors, never stored. The face it feeds: a "
            "chatbot, learning always, summarizing when asked.",
            "why": "A query answered from structure costs a walk; only the novel costs "
            "inference (Law 1 as runtime). The embedding IS the path — so the store "
            "holds O(n) vectors and the paths fall out. Every node is traceable at "
            "birth: an untraceable node would be fabricated attribution in permanent "
            "residence.",
        }

    def state(self) -> dict:
        return {
            "deposits": self._deposits,
            "verdicts": dict(self._verdicts),
            "last_node_id": self._last_node,
        }

    def settings(self) -> dict:
        return {
            "table": NODES,
            "owner": OWNER,
            "min_content_chars": _MIN_CONTENT_CHARS,
            "standing_at_birth": "hypothesis (Law 3; the tenure loop is a filed edge)",
            "edges": "derived from cosine proximity at walk time; stored links (cairn_links) "
                    "add a learned layer reinforced by traversal",
            "calve_threshold": CALVE_THRESHOLD,
            "seam": "vectors arrive as data; the embed call is the caller's, through "
                    "inference_domain (live wiring in live.py, never here)",
        }
