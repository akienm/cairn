"""One-shot migration: flat *_nodes → three-table schema.

Reads every *_nodes table (except cairn_nodes/cairn_embeddings), extracts
node+embedding into the shared tables, then rebuilds each as a leaf table.

Safe to re-run: idempotent on all three tables (PK-based dedup).
"""
import sys
from psycopg2.extras import Json
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
    cur = conn.cursor()

    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name LIKE '%_nodes' ORDER BY 1"
    )
    tables = [r[0] for r in cur.fetchall() if r[0] not in SKIP]
    print(f"tables to migrate: {tables}")

    # ensure shared tables exist
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

        # check if already migrated (leaf schema has leaf_id column)
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = 'leaf_id'", (table,)
        )
        if cur.fetchone():
            print(f"  {table}: already migrated (has leaf_id), skipping")
            continue

        # check it has the old schema
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = 'content'", (table,)
        )
        if not cur.fetchone():
            print(f"  {table}: no content column, skipping")
            continue

        # read all old rows
        cur.execute(f"SELECT node_id, content, vector, provenance, standing, created FROM {table}")
        old_rows = cur.fetchall()
        print(f"  {table}: {len(old_rows)} rows, owner={owner}")

        leaves = []
        for old_nid, content, vector, provenance, standing, created in old_rows:
            nid = node_id_for(content)
            eid = embedding_id_for(nid, RENDER_METHOD)
            lid = leaf_id_for(nid, eid)

            # insert node (dedup by PK)
            cur.execute(
                "INSERT INTO cairn_nodes (node_id, content, provenance, standing, created) "
                "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (node_id) DO NOTHING",
                (nid, content, Json(provenance), standing, created)
            )
            if cur.rowcount:
                total_nodes += 1

            # insert embedding (dedup by PK)
            cur.execute(
                "INSERT INTO cairn_embeddings (embedding_id, node_id, vector, render_method) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT (embedding_id) DO NOTHING",
                (eid, nid, Json(vector), RENDER_METHOD)
            )
            if cur.rowcount:
                total_embeddings += 1

            leaves.append((lid, nid, eid))

        # rebuild the table as a leaf table:
        # 1. drop old table
        cur.execute(f"DROP TABLE {table}")
        # 2. create with leaf schema
        store.create_owned_table(table, owner, _LEAF_COLUMNS, conn=conn)
        # 3. insert leaf rows
        for lid, nid, eid in leaves:
            cur.execute(
                f"INSERT INTO {table} (leaf_id, node_id, embedding_id) "
                "VALUES (%s, %s, %s) ON CONFLICT (leaf_id) DO NOTHING",
                (lid, nid, eid)
            )
            if cur.rowcount:
                total_leaves += 1

    conn.commit()

    # verify
    cur.execute("SELECT count(*) FROM cairn_nodes")
    node_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM cairn_embeddings")
    emb_count = cur.fetchone()[0]

    print(f"\n--- migration complete ---")
    print(f"cairn_nodes: {node_count} ({total_nodes} new)")
    print(f"cairn_embeddings: {emb_count} ({total_embeddings} new)")
    print(f"leaf rows written: {total_leaves}")

    # verify each leaf table
    for table in tables:
        try:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = %s ORDER BY ordinal_position", (table,)
            )
            cols = [r[0] for r in cur.fetchall()]
            cur.execute(f"SELECT count(*) FROM {table}")
            n = cur.fetchone()[0]
            print(f"  {table}: {n} leaves, cols={cols}")
        except Exception as e:
            print(f"  {table}: error: {e}")
            conn.rollback()

    # verify no orphaned references
    cur.execute(
        "SELECT count(*) FROM cairn_embeddings e "
        "WHERE NOT EXISTS (SELECT 1 FROM cairn_nodes n WHERE n.node_id = e.node_id)"
    )
    orphan_emb = cur.fetchone()[0]
    print(f"\norphaned embeddings (no node): {orphan_emb}")

    conn.close()
    return node_count, emb_count


if __name__ == "__main__":
    nodes, embs = migrate()
    if nodes == 0:
        print("WARNING: cairn_nodes is empty after migration", file=sys.stderr)
        sys.exit(1)
