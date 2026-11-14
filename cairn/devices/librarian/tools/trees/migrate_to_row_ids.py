"""Move the hash-keyed librarian nodes to row numbers, dropping nothing (ticket 06db586bedfd, D4).

Akien, Q#104 (outline 4.3.1.5.1.2): a node id is its master row number only. Until 06db the
librarian keyed ``cairn_nodes`` by sha256(content)[:16]. This lays every such node as a data row
in ``cairn_node_rows`` with the old hash kept as ``legacy_id``, copies its embeddings and links
onto the row, and files it in the content index. It NEVER drops, deletes or alters an old row:
the old tables stand beside the new ones, and a legacy leaf (a leaf table another owner holds,
still naming the hash) resolves through ``legacy_id`` until its owner rewrites it (Law 6).

Order-independent and idempotent: a legacy node already mapped is skipped; content the index
already holds (a deposit made after 06db landed) is merged as an attestation and the hash is
mapped onto that row; new rows take the numbers after this box's end. So it runs before the
merge and again right after, and the second run lays only what arrived between.

    python3 -m cairn.devices.librarian.tools.trees.migrate_to_row_ids            # dry run
    python3 -m cairn.devices.librarian.tools.trees.migrate_to_row_ids --write    # applies

Prints the report as JSON. Exits 1 when any embedding or link names a node that maps to no row,
or when an old table's row count moved.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from cairn.devices.db_domain.tools.client import store
from cairn.devices.librarian.tools.trees import trees as t

LEGACY = {"nodes": "cairn_nodes", "embeddings": "cairn_embeddings", "links": "cairn_links"}

# The shapes the hash-keyed tables were made with (trees.py before 06db586bedfd).
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


def _read(table: str, *, conn, order: str = "") -> list[dict]:
    if store.owner_of(table, conn=conn) is None:
        return []
    return store.query("SELECT * FROM {t}" + (f" ORDER BY {order}" if order else ""),
                       tables={"t": table}, conn=conn)


def _counts(legacy: dict, *, conn) -> dict:
    return {k: len(_read(v, conn=conn)) for k, v in legacy.items()}


def migrate(*, legacy: dict | None = None, write: bool = False, conn=None) -> dict:
    """One pass. ``write=False`` reads only and reports what a write would lay."""
    legacy = dict(legacy or LEGACY)
    own = conn or store.connect()
    try:
        before = _counts(legacy, conn=own)
        if write:
            t.ensure_nodes(conn=own)
        mapped = {r["legacy_id"]: int(r["node_id"]) for r in _read(t.NODES_TABLE, conn=own)
                  if r.get("legacy_id")}
        index = {r["key"]: int(r["node_id"]) for r in _read(t.CONTENT_INDEX, conn=own)}
        report = {"write": write, "would_lay": 0, "laid": 0, "merged": 0,
                  "embeddings_copied": 0, "links_copied": 0, "unmapped": 0,
                  "unmapped_ids": [], "old_counts": before}

        top = max([int(r["node_id"]) for r in _read(t.NODES_TABLE, conn=own)] or [0])
        for old in _read(legacy["nodes"], conn=own, order="created, node_id"):
            h = old["node_id"]
            if h in mapped:
                continue
            key = t.content_key(old["content"])
            if key in index:
                row = index[key]
                report["merged"] += 1
                if write:
                    held = store.read(t.NODES_TABLE, where="node_id = %s", params=(row,), conn=own)[0]
                    prov = dict(held["provenance"] or {})
                    attests = list(prov.get("attestations") or [])
                    attests.append({**(old["provenance"] or {}), "legacy_id": h,
                                    "at": datetime.now(timezone.utc).isoformat()})
                    changes = {"provenance": {**prov, "attestations": attests}}
                    if not held.get("legacy_id"):
                        changes["legacy_id"] = h
                    store.update(t.NODES_TABLE, t.OWNER, changes, where="node_id = %s",
                                 params=(row,), conn=own)
                mapped[h] = row
                continue
            report["would_lay"] += 1
            top += 1
            if write:
                store.write(t.NODES_TABLE, t.OWNER, {
                    "node_id": top, "state": t.DATA, "content": old["content"],
                    "provenance": old["provenance"], "standing": old["standing"],
                    "created": old["created"], "legacy_id": h}, conn=own)
                store.write(t.CONTENT_INDEX, t.OWNER, {"key": key, "node_id": top}, conn=own)
                report["laid"] += 1
            mapped[h] = top
            index[key] = top

        have_emb = {r["embedding_id"] for r in _read(t.EMBEDDINGS_TABLE, conn=own)}
        for e in _read(legacy["embeddings"], conn=own):
            if e["embedding_id"] in have_emb:
                continue
            row = mapped.get(e["node_id"])
            if row is None:
                report["unmapped"] += 1
                report["unmapped_ids"].append(e["node_id"])
                continue
            if write:
                store.write(t.EMBEDDINGS_TABLE, t.OWNER, {
                    "embedding_id": e["embedding_id"], "node_id": row, "vector": e["vector"],
                    "render_method": e["render_method"]}, conn=own)
            report["embeddings_copied"] += 1

        have_links = {r["link_id"] for r in _read(t.LINKS_TABLE, conn=own)}
        for lk in _read(legacy["links"], conn=own):
            src, tgt = mapped.get(lk["source_id"]), mapped.get(lk["target_id"])
            if src is None or tgt is None:
                report["unmapped"] += 1
                report["unmapped_ids"].append(lk["link_id"])
                continue
            lid = t.link_id_for(src, tgt)
            if lid in have_links:
                continue
            if write:
                store.write(t.LINKS_TABLE, t.OWNER, {
                    "link_id": lid, "source_id": src, "target_id": tgt, "weight": lk["weight"],
                    "traversals": lk["traversals"], "created": lk["created"]}, conn=own)
            have_links.add(lid)
            report["links_copied"] += 1

        report["old_counts_after"] = _counts(legacy, conn=own)
        report["old_tables_unchanged"] = report["old_counts_after"] == before
        report["unmapped_ids"] = report["unmapped_ids"][:50]
        return report
    finally:
        if conn is None:
            own.close()


def main(argv: list[str]) -> int:
    report = migrate(write="--write" in argv)
    print(json.dumps(report, indent=2, default=str))
    return 1 if report["unmapped"] or not report["old_tables_unchanged"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
