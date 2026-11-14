"""Move the hash-keyed librarian memory onto rows, dropping nothing (ticket 26acbf5314a5).

Akien, Q#104 (outline 4.3.1.5.1.2): a node id is its master row number only. Until T2
(06db586bedfd) the librarian keyed ``cairn_nodes`` by sha256(content)[:16]. This pass lays every
such node as a DATA row in T2's nodes table (``trees.NODES_TABLE``) at a row ``trees.reserve()``
hands out, meta carrying the legacy provenance and standing verbatim plus the old hash as
``legacy_id`` and NO confidence key (Q#108: confidence is absent until something scores it).
Embeddings and links follow onto the addresses, and every standing leaf table (vector or keyed)
gains its ``row`` column, filled 1..n in leaf_id order and held by a UNIQUE index, its node_id
rewritten to the node's address, the old hash and the old leaf_id kept in additive
``legacy_node_id`` / ``legacy_leaf_id`` columns, and the node's in_list holding the leaf back.

The new ids are the ones a deposit would compute from the address: an embedding lands at
``trees.embedding_id_for(address, render_method)``, a leaf is re-keyed to
``trees.leaf_id_for(address, embedding_id | key)``. A legacy id is a hash of the old text id, so
keeping it would let a later deposit of the same content lay a second embedding and a second
leaf beside the migrated one (measured 2026-11-14, trees.deposit's duplicate test is on those
two ids).

It NEVER drops, deletes or alters a legacy nodes/embeddings/links row; a leaf table keeps every
row (its columns are only added to, through store's owner-gated doors, under the table's own
owner). Idempotent: a node already mapped (its meta.legacy_id, or an attestation carrying the
hash) is not laid again, a leaf already carrying legacy_node_id is not rewritten, and the column,
index and tag doors are additive and idempotent, so a second --write lays nothing.

    python3 -m cairn.devices.librarian.tools.trees.migrate_to_row_ids            # dry run
    python3 -m cairn.devices.librarian.tools.trees.migrate_to_row_ids --write    # applies
    ... --legacy '{"nodes": "...", "embeddings": "...", "links": "...", "leaves": ["..."]}'

Prints the report as JSON. Exits 1 when a legacy table's row count (or a leaf table's) moved
during the run, or a node it mapped did not land. Ids that map to no node are named in the
report and left untouched; they do not fail the run.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone

from cairn.devices.db_domain.tools.client import store
from cairn.devices.librarian.tools.trees import trees as t
from cairn.tools.node_address import node_address as A

LEGACY = {"nodes": "cairn_nodes", "embeddings": "cairn_embeddings", "links": "cairn_links"}

# The shapes the hash-keyed tables were made with (trees.py before 06db586bedfd). The proof
# builds its scratch legacy world from these.
LEGACY_NODE_COLUMNS = {
    "node_id": "text PRIMARY KEY",
    "content": "text NOT NULL",
    "provenance": "jsonb NOT NULL",
    "standing": "text NOT NULL",
    "created": "timestamptz NOT NULL DEFAULT now()",
}
LEGACY_EMBEDDING_COLUMNS = {
    "embedding_id": "text PRIMARY KEY",
    "node_id": "text NOT NULL",
    "vector": "jsonb NOT NULL",
    "render_method": "text NOT NULL",
}
LEGACY_LINK_COLUMNS = {
    "link_id": "text PRIMARY KEY",
    "source_id": "text NOT NULL",
    "target_id": "text NOT NULL",
    "weight": "real NOT NULL",
    "traversals": "integer NOT NULL DEFAULT 0",
    "created": "timestamptz NOT NULL DEFAULT now()",
}
LEGACY_LEAF_COLUMNS = {
    "leaf_id": "text PRIMARY KEY",
    "node_id": "text NOT NULL",
    "embedding_id": "text NOT NULL",
}
LEGACY_KEYED_LEAF_COLUMNS = {
    "leaf_id": "text PRIMARY KEY",
    "key": "text NOT NULL",
    "node_id": "text NOT NULL",
    "meta": "jsonb NOT NULL DEFAULT '{}'",
    "created": "timestamptz NOT NULL DEFAULT now()",
}

# The columns a leaf table gains (additive, nullable, through store.add_owned_column).
LEAF_ADDED = (("row", "bigint"), ("legacy_node_id", "text"), ("legacy_leaf_id", "text"))

# store.scratch_name's shape (<prefix>_<pid>_<HHMMSSffff>[_<suffix>]): such a table is a run's,
# not standing, and ensure_trees refuses one since 1a3a55a314eb.
_SCRATCH = getattr(t, "_SCRATCH_SHAPE", None) or re.compile(r"_[0-9]+_[0-9]{10}(?:_\w+)?$")


def _exists(table: str, *, conn) -> bool:
    return store.owner_of(table, conn=conn) is not None


def _read(table: str, *, conn, order: str = "") -> list[dict]:
    if not _exists(table, conn=conn):
        return []
    return store.query("SELECT * FROM {t}" + (f" ORDER BY {order}" if order else ""),
                       tables={"t": table}, conn=conn)


def _count(table: str, *, conn) -> int | None:
    if not _exists(table, conn=conn):
        return None
    return int(store.query("SELECT count(*) AS n FROM {t}", tables={"t": table},
                           conn=conn)[0]["n"])


def _columns(table: str, *, conn) -> set[str]:
    return {r["column_name"] for r in store.query(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
        tables={}, params=(table,), conn=conn)}


def _new_tables() -> set[str]:
    return {t.NODES_TABLE, t.LISTS_TABLE, t.LINKS_TABLE, t.BLOBS_TABLE, t.TAGS_TABLE,
            t.EMBEDDINGS_TABLE, t.CONTENT_INDEX}


def standing_leaves(*, legacy: dict, conn) -> tuple[list[str], list[str]]:
    """(the standing leaf tables, the scratch-shaped ones skipped): every owned table carrying
    leaf_id and node_id and either embedding_id (a vector leaf) or key (a keyed leaf)."""
    rows = store.query(
        "SELECT table_name, array_agg(column_name::text) AS cols FROM information_schema.columns "
        "WHERE table_schema = current_schema() GROUP BY table_name", tables={}, conn=conn)
    skip = _new_tables() | {v for k, v in legacy.items() if k != "leaves"}
    found, scratch = [], []
    for r in sorted(rows, key=lambda r: r["table_name"]):
        name, cols = r["table_name"], set(r["cols"] or [])
        if name in skip or not {"leaf_id", "node_id"} <= cols:
            continue
        if "embedding_id" not in cols and "key" not in cols:
            continue
        if not _exists(name, conn=conn):
            continue
        if _SCRATCH.search(name) or store.is_scratch(name, conn=conn):
            scratch.append(name)
            continue
        found.append(name)
    return found, scratch


def _is_address(value) -> bool:
    return isinstance(value, str) and value.strip().lstrip("-").isdigit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _node(r: dict, *, write: bool, index_exists: bool, conn) -> tuple[str, int | None]:
    """One legacy node: ("laid" | "mapped_onto_held" | "already" | "index_disagrees", address).
    In a dry run a node that would be laid has no address yet (None)."""
    h, content = r["node_id"], r["content"]
    held = t.already_held(content, conn=conn) if index_exists else None
    if held is not None:
        view = t._get(held, conn=conn)
        if view is None:
            return "index_disagrees", None
        if (view.get("meta") or {}).get("legacy_id") == h:
            return "already", held
        prov = dict(view["provenance"] or {})
        attests = list(prov.get("attestations") or [])
        if any(isinstance(a, dict) and a.get("legacy_id") == h for a in attests):
            return "already", held
        if write:
            attests.append({**(r["provenance"] or {}), "legacy_id": h,
                            "legacy_standing": r["standing"], "at": _now()})
            t._put_meta(held, {"provenance": {**prov, "attestations": attests}}, conn=conn)
        return "mapped_onto_held", held
    if not write:
        return "laid", None
    row = t.reserve(conn=conn)
    addr = t._addr("nodes", row)
    if t._hold_content(content, addr, conn=conn) is not None:
        t.void(row, conn=conn)   # a concurrent deposit filed the same content first
        return _node(r, write=write, index_exists=True, conn=conn)
    t.write_node(row, content, r["provenance"], standing=r["standing"] or "hypothesis", conn=conn)
    t._put_meta(addr, {"legacy_id": h}, conn=conn)
    if r.get("created") is not None:
        t._update(t.NODES_TABLE, t.OWNER, {"created": r["created"]}, where="row = %s",
                  params=(row,), conn=conn)
    return "laid", addr


def _leaf(table: str, addr: dict, emb_map: dict, *, write: bool, conn) -> dict:
    """One leaf table: its row column filled 1..n and indexed UNIQUE, each mapped leaf re-keyed
    onto its node's address and held back in the node's in_list."""
    owner = store.owner_of(table, conn=conn)
    cols = _columns(table, conn=conn)
    keyed = "key" in cols and "embedding_id" not in cols
    rows = _read(table, conn=conn, order="leaf_id")
    out = {"table": table, "owner": owner, "keyed": keyed, "rows": len(rows),
           "columns_added": [], "rows_filled": 0, "rewritten": 0, "already": 0,
           "unmapped": []}
    if write:
        for name, ctype in LEAF_ADDED:
            if store.add_owned_column(table, owner, name, ctype, conn=conn):
                out["columns_added"].append(name)
        empty = store.query("SELECT leaf_id FROM {t} WHERE row IS NULL ORDER BY leaf_id",
                            tables={"t": table}, conn=conn)
        top = int(store.query("SELECT max(row) AS m FROM {t}", tables={"t": table},
                              conn=conn)[0]["m"] or 0)
        for i, r in enumerate(empty, 1):
            store.update(table, owner, {"row": top + i}, where="leaf_id = %s",
                         params=(r["leaf_id"],), conn=conn)
        out["rows_filled"] = len(empty)
        store.add_owned_index(table, owner, f"{table}_row_key", ["row"], unique=True, conn=conn)
        rows = _read(table, conn=conn, order="leaf_id")
        tag = t.leaf_tag(table, conn=conn)
        out["tag"] = tag
    else:
        out["columns_added"] = [n for n, _ in LEAF_ADDED if n not in cols]
        out["rows_filled"] = sum(1 for r in rows if r.get("row") is None)
    for r in rows:
        if r.get("legacy_node_id") is not None or _is_address(r["node_id"]):
            out["already"] += 1
            continue
        h = r["node_id"]
        if h not in addr:
            out["unmapped"].append(r["leaf_id"])
            continue
        if keyed:
            new_eid = None
        else:
            new_eid = emb_map.get(r["embedding_id"])
            if new_eid is None:
                out["unmapped"].append(r["leaf_id"])
                continue
        if not write:
            out["rewritten"] += 1
            continue
        a = addr[h]
        changes = {"node_id": str(a), "legacy_node_id": h, "legacy_leaf_id": r["leaf_id"],
                   "leaf_id": t.leaf_id_for(a, r["key"] if keyed else new_eid)}
        if not keyed:
            changes["embedding_id"] = new_eid
        store.update(table, owner, changes, where="leaf_id = %s", params=(r["leaf_id"],),
                     conn=conn)
        t._list_append(A.row_of(a), "in_list", A.pack(tag, int(r["row"])), conn=conn)
        out["rewritten"] += 1
    return out


def migrate(*, legacy: dict | None = None, write: bool = False, conn=None) -> dict:
    """One pass. ``write=False`` reads only and reports what a write would do. ``legacy`` names
    the legacy tables (nodes, embeddings, links) and, under "leaves", the leaf tables to move;
    without "leaves" every standing leaf table is found by its columns."""
    names = {**LEGACY, **{k: v for k, v in (legacy or {}).items() if k != "leaves"}}
    own = conn or store.connect()
    try:
        if legacy and "leaves" in legacy:
            leaves, scratch = list(legacy["leaves"]), []
        else:
            leaves, scratch = standing_leaves(legacy=names, conn=own)
        before = {k: _count(v, conn=own) for k, v in names.items()}
        leaves_before = {lt: _count(lt, conn=own) for lt in leaves}
        if write:
            t.ensure_nodes(conn=own)
        index_exists = _exists(t.CONTENT_INDEX, conn=own)
        report: dict = {"write": write, "legacy": names, "before": before,
                        "skipped_scratch_leaves": scratch,
                        "nodes": {"laid": 0, "mapped_onto_held": 0, "already": 0,
                                  "index_disagrees": [], "not_landed": []},
                        "embeddings": {"laid": 0, "already": 0, "unmapped": []},
                        "links": {"laid": 0, "already": 0, "unmapped": []}}

        addr: dict[str, int | None] = {}
        legacy_nodes = _read(names["nodes"], conn=own, order="node_id")
        for r in legacy_nodes:
            how, a = _node(r, write=write, index_exists=index_exists, conn=own)
            if how == "index_disagrees":
                report["nodes"]["index_disagrees"].append(r["node_id"])
                continue
            report["nodes"][how] += 1
            addr[r["node_id"]] = a

        emb_map: dict[str, str | None] = {}
        for e in _read(names["embeddings"], conn=own, order="embedding_id"):
            if e["node_id"] not in addr:
                report["embeddings"]["unmapped"].append(e["embedding_id"])
                continue
            a = addr[e["node_id"]]
            if a is None:   # a dry run: the node has no address yet
                report["embeddings"]["laid"] += 1
                emb_map[e["embedding_id"]] = "planned"
                continue
            eid = t.embedding_id_for(a, e["render_method"])
            emb_map[e["embedding_id"]] = eid
            if store.read(t.EMBEDDINGS_TABLE, where="embedding_id = %s", params=(eid,), conn=own) \
                    if _exists(t.EMBEDDINGS_TABLE, conn=own) else False:
                report["embeddings"]["already"] += 1
                continue
            if write:
                store.write(t.EMBEDDINGS_TABLE, t.OWNER, {
                    "embedding_id": eid, "node_id": a, "vector": e["vector"],
                    "render_method": e["render_method"]}, conn=own)
            report["embeddings"]["laid"] += 1

        for lk in _read(names["links"], conn=own, order="link_id"):
            src, tgt = lk["source_id"], lk["target_id"]
            if src not in addr or tgt not in addr:
                report["links"]["unmapped"].append(lk["link_id"])
                continue
            if not write:
                report["links"]["laid"] += 1
                continue
            got = t.link(addr[src], addr[tgt], float(lk["weight"]), conn=own)
            t._update(t.LINKS_TABLE, t.OWNER, {"traversals": int(lk["traversals"] or 0)},
                      where="row = %s", params=(A.row_of(got["link"]),), conn=own)
            report["links"]["already" if got["updated"] else "laid"] += 1

        report["leaves"] = [_leaf(lt, addr, emb_map, write=write, conn=own) for lt in leaves]

        if write:
            for r in legacy_nodes:
                a = addr.get(r["node_id"])
                got = t._get(a, conn=own) if a is not None else None
                if r["node_id"] in addr and (got is None or got["content"] != r["content"]):
                    report["nodes"]["not_landed"].append(r["node_id"])

        after = {k: _count(v, conn=own) for k, v in names.items()}
        leaves_after = {lt: _count(lt, conn=own) for lt in leaves}
        report["after"] = after
        report["legacy_unchanged"] = before == after and leaves_before == leaves_after
        report["leaf_counts"] = {"before": leaves_before, "after": leaves_after}
        return report
    finally:
        if conn is None:
            own.close()


def failed(report: dict) -> bool:
    return not report["legacy_unchanged"] or bool(report["nodes"]["not_landed"])


def main(argv: list[str]) -> int:
    legacy = None
    if "--legacy" in argv:
        legacy = json.loads(argv[argv.index("--legacy") + 1])
    report = migrate(legacy=legacy, write="--write" in argv)
    print(json.dumps(report, indent=2, default=str))
    return 1 if failed(report) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
