"""One-shot migration: flat *_nodes → three-table schema.

Reads every *_nodes table (except cairn_nodes/cairn_embeddings), extracts
node+embedding into the shared tables, then rebuilds each as a leaf table.

Safe to re-run: idempotent on all three tables (PK-based dedup).
"""
import sys
from cairn.devices.db_domain import store
from cairn.devices.librarian.trees import (
    NODES_TABLE, EMBEDDINGS_TABLE, OWNER,
    _NODE_COLUMNS, _EMBEDDING_COLUMNS, _LEAF_COLUMNS,
    node_id_for, embedding_id_for, leaf_id_for,
)

SKIP = {NODES_TABLE, EMBEDDINGS_TABLE, "cairn_owned"}
RENDER_METHOD = "embed:default"


def migrate():
    conn = store.connect()

    rows = store.query(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name LIKE '%_nodes' ORDER BY 1",
        tables={}, conn=conn,
    )
    tables = [r["table_name"] for r in rows if r["table_name"] not in SKIP]
    print(f"tables to migrate: {tables}")

    store.create_owned_table(NODES_TABLE, OWNER, _NODE_COLUMNS, conn=conn)
    store.create_owned_table(EMBEDDINGS_TABLE, OWNER, _EMBEDDING_COLUMNS, conn=conn)

    total_nodes = 0
    total_embeddings = 0
    total_leaves = 0

    for table in tables:
        owner = store.owner_of(table, conn=conn)
        if owner is None:
            print(f"  {table}: no owner, skipping")
            continue

        cols = store.query(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = 'leaf_id'",
            tables={}, params=(table,), conn=conn,
        )
        if cols:
            print(f"  {table}: already migrated (has leaf_id), skipping")
            continue

        cols = store.query(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = 'content'",
            tables={}, params=(table,), conn=conn,
        )
        if not cols:
            print(f"  {table}: no content column, skipping")
            continue

        old_rows = store.read(table, conn=conn)
        print(f"  {table}: {len(old_rows)} rows, owner={owner}")

        leaves = []
        for row in old_rows:
            content = row["content"]
            vector = row["vector"]
            provenance = row["provenance"]
            standing = row["standing"]
            nid = node_id_for(content)
            eid = embedding_id_for(nid, RENDER_METHOD)
            lid = leaf_id_for(nid, eid)

            existing = store.read(NODES_TABLE, where="node_id = %s",
                                  params=(nid,), conn=conn)
            if not existing:
                store.write(NODES_TABLE, OWNER, {
                    "node_id": nid, "content": content,
                    "provenance": provenance, "standing": standing,
                }, conn=conn)
                total_nodes += 1

            existing = store.read(EMBEDDINGS_TABLE, where="embedding_id = %s",
                                  params=(eid,), conn=conn)
            if not existing:
                store.write(EMBEDDINGS_TABLE, OWNER, {
                    "embedding_id": eid, "node_id": nid,
                    "vector": vector, "render_method": RENDER_METHOD,
                }, conn=conn)
                total_embeddings += 1

            leaves.append((lid, nid, eid))

        store.drop_table(table, owner, conn=conn)
        store.create_owned_table(table, owner, _LEAF_COLUMNS, conn=conn)
        for lid, nid, eid in leaves:
            existing = store.read(table, where="leaf_id = %s",
                                  params=(lid,), conn=conn)
            if not existing:
                store.write(table, owner, {
                    "leaf_id": lid, "node_id": nid, "embedding_id": eid,
                }, conn=conn)
                total_leaves += 1

    node_count = len(store.read(NODES_TABLE, conn=conn))
    emb_count = len(store.read(EMBEDDINGS_TABLE, conn=conn))

    print(f"\n--- migration complete ---")
    print(f"cairn_nodes: {node_count} ({total_nodes} new)")
    print(f"cairn_embeddings: {emb_count} ({total_embeddings} new)")
    print(f"leaf rows written: {total_leaves}")

    for table in tables:
        try:
            cols = store.query(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = %s ORDER BY ordinal_position",
                tables={}, params=(table,), conn=conn,
            )
            col_names = [r["column_name"] for r in cols]
            n = len(store.read(table, conn=conn))
            print(f"  {table}: {n} leaves, cols={col_names}")
        except Exception as e:
            print(f"  {table}: error: {e}")

    orphans = store.query(
        "SELECT count(*) as cnt FROM {embed} e "
        "WHERE NOT EXISTS (SELECT 1 FROM {nodes} n WHERE n.node_id = e.node_id)",
        tables={"embed": EMBEDDINGS_TABLE, "nodes": NODES_TABLE},
        conn=conn,
    )
    print(f"\norphaned embeddings (no node): {orphans[0]['cnt']}")

    conn.close()
    return node_count, emb_count


if __name__ == "__main__":
    nodes, embs = migrate()
    if nodes == 0:
        print("WARNING: cairn_nodes is empty after migration", file=sys.stderr)
        sys.exit(1)
