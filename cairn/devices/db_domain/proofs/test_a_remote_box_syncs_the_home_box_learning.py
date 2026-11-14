"""Proof (ticket 3ef8654a8027, outline 11.3.5.1): a remote box's database syncs the home box's learning.

Measured 2026-11-12: akienasus's local db held none of codemother's trees while akiendelllinux's
held 688 rows, so 2b3d842bc118's clause_4 reds on akienasus. The unit (open-675330928c01, answered
by the outline) is the memory model's learning tables: the one node list, its embeddings and links,
and the trees that index it, each owned by one device.

Two real databases on the local Postgres (a HOME and a REMOTE, minted and dropped here), the sync
moving rows through the owner-gated store door. The cross-box transport (the bus, CAIRN_HOME_HOST)
is not this module's concern and not measured here.

  1. After ``sync_from_home``, every learning table the home holds for the named owners exists on the
     remote under the SAME owner and holds at least the home's node ids.
  2. A node row read on both boxes is identical.
  1b. The sync inserts and never updates or deletes: a second run copies nothing, a row only the
      remote holds stays, and a row both hold that differs is left as the remote has it and counted.
  1c. A table whose owner is not named is skipped (not created), a table without a single-column
      primary key is refused by name, and no owners at all raises.

    python3 cairn/devices/db_domain/proofs/test_a_remote_box_syncs_the_home_box_learning.py
"""
from __future__ import annotations

import contextlib
import json
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"3ef8654a8027": {
    "1": "test_every_learning_table_arrives_under_the_same_owner_with_the_home_node_ids",
    "2": "test_a_node_row_read_on_both_boxes_is_identical",
    "1b": "test_the_sync_inserts_and_never_updates_or_deletes",
    "1c": "test_an_unnamed_owner_is_skipped_a_keyless_table_refused_and_no_owners_raises",
}}

NODES = {"node_id": "text PRIMARY KEY", "content": "text NOT NULL", "provenance": "jsonb NOT NULL"}
LEAVES = {"leaf_id": "text PRIMARY KEY", "node_id": "text NOT NULL", "weight": "double precision NOT NULL"}
KEYLESS = {"k": "text", "v": "text"}
HOME_NODES = [("n1", "one", {"src": "a"}), ("n2", "two", {"src": "b"}), ("n3", "three", {"src": "c"})]


@contextlib.contextmanager
def _boxes():
    """A home and a remote database, each with the owner registry, dropped on the way out."""
    import psycopg2
    from cairn.devices.db_domain.tools.client import store
    tag = uuid.uuid4().hex[:8]
    names = {"home": f"cairn_sync_home_{tag}", "remote": f"cairn_sync_remote_{tag}"}
    boot = psycopg2.connect(dbname="postgres", **store._conn_args())
    boot.autocommit = True
    conns = {}
    try:
        with boot.cursor() as cur:
            for n in names.values():
                cur.execute(f'CREATE DATABASE "{n}"')
        for role, n in names.items():
            c = psycopg2.connect(dbname=n, **store._conn_args())
            c.autocommit = True
            store._ensure_registry(c)
            conns[role] = c
        yield conns["home"], conns["remote"]
    finally:
        for c in conns.values():
            with contextlib.suppress(Exception):
                c.close()
        with boot.cursor() as cur:
            for n in names.values():
                with contextlib.suppress(Exception):
                    cur.execute(f'DROP DATABASE IF EXISTS "{n}" WITH (FORCE)')
        boot.close()


def _stock_home(home) -> None:
    from cairn.devices.db_domain.tools.client import store
    store.create_owned_table("cairn_nodes", "librarian", NODES, conn=home)
    store.create_owned_table("codemother_orient_leaves", "codemother", LEAVES, conn=home)
    store.create_owned_table("stranger_things", "stranger", NODES, conn=home)
    store.create_owned_table("librarian_keyless", "librarian", KEYLESS, conn=home)
    for nid, content, prov in HOME_NODES:
        store.write("cairn_nodes", "librarian", {"node_id": nid, "content": content, "provenance": prov}, conn=home)
    for i in range(3):
        store.write("codemother_orient_leaves", "codemother",
                    {"leaf_id": f"l{i}", "node_id": HOME_NODES[i][0], "weight": 0.5 + i}, conn=home)
    store.write("stranger_things", "stranger", {"node_id": "s1", "content": "x", "provenance": {}}, conn=home)
    store.write("librarian_keyless", "librarian", {"k": "a", "v": "b"}, conn=home)


OWNERS = {"librarian", "codemother"}


def test_every_learning_table_arrives_under_the_same_owner_with_the_home_node_ids():
    from cairn.devices.db_domain.sync import sync_from_home
    from cairn.devices.db_domain.tools.client import store
    with _boxes() as (home, remote):
        _stock_home(home)
        got = sync_from_home(home, remote, owners=OWNERS)
        for table, owner in (("cairn_nodes", "librarian"), ("codemother_orient_leaves", "codemother")):
            assert store.owner_of(table, conn=remote) == owner, (table, got.get(table))
            assert got[table]["created"] is True, got[table]
        home_ids = {r["node_id"] for r in store.read("cairn_nodes", conn=home)}
        remote_ids = {r["node_id"] for r in store.read("cairn_nodes", conn=remote)}
        assert home_ids <= remote_ids and home_ids == {"n1", "n2", "n3"}, (home_ids, remote_ids)
        assert len(store.read("codemother_orient_leaves", conn=remote)) == 3


def test_a_node_row_read_on_both_boxes_is_identical():
    from cairn.devices.db_domain.sync import sync_from_home
    from cairn.devices.db_domain.tools.client import store
    with _boxes() as (home, remote):
        _stock_home(home)
        sync_from_home(home, remote, owners=OWNERS)
        for table in ("cairn_nodes", "codemother_orient_leaves"):
            key = "node_id" if table == "cairn_nodes" else "leaf_id"
            a = {r[key]: r for r in store.read(table, conn=home)}
            b = {r[key]: r for r in store.read(table, conn=remote)}
            assert a and a == b, (table, a, b)


def test_the_sync_inserts_and_never_updates_or_deletes():
    from cairn.devices.db_domain.sync import sync_from_home
    from cairn.devices.db_domain.tools.client import store
    with _boxes() as (home, remote):
        _stock_home(home)
        store.create_owned_table("cairn_nodes", "librarian", NODES, conn=remote)
        store.write("cairn_nodes", "librarian", {"node_id": "n1", "content": "one", "provenance": {"src": "a"}}, conn=remote)   # identical
        store.write("cairn_nodes", "librarian", {"node_id": "n2", "content": "REMOTE two", "provenance": {}}, conn=remote)     # differs
        store.write("cairn_nodes", "librarian", {"node_id": "r9", "content": "only here", "provenance": {}}, conn=remote)       # remote-only
        first = sync_from_home(home, remote, owners=OWNERS)["cairn_nodes"]
        assert (first["copied"], first["present"], first["differing"], first["created"]) == (1, 1, 1, False), first
        rows = {r["node_id"]: r for r in store.read("cairn_nodes", conn=remote)}
        assert rows["n2"]["content"] == "REMOTE two", "the sync overwrote a row the remote held"
        assert "r9" in rows and set(rows) == {"n1", "n2", "n3", "r9"}, sorted(rows)
        second = sync_from_home(home, remote, owners=OWNERS)["cairn_nodes"]
        assert (second["copied"], second["present"], second["differing"]) == (0, 2, 1), second


def test_an_unnamed_owner_is_skipped_a_keyless_table_refused_and_no_owners_raises():
    from cairn.devices.db_domain.sync import sync_from_home
    from cairn.devices.db_domain.tools.client import store
    with _boxes() as (home, remote):
        _stock_home(home)
        got = sync_from_home(home, remote, owners=OWNERS)
        assert got["stranger_things"] == {"skipped": "stranger"}, got["stranger_things"]
        assert store.owner_of("stranger_things", conn=remote) is None, "a table whose owner was not named was created"
        assert "single" in got["librarian_keyless"].get("refused", "") or "primary" in got["librarian_keyless"].get("refused", ""), got["librarian_keyless"]
        assert store.owner_of("librarian_keyless", conn=remote) is None, "a keyless table was copied blind"
        try:
            sync_from_home(home, remote, owners=set())
        except ValueError:
            return
        raise AssertionError("an empty owners set did not raise")


TEETH = [test_every_learning_table_arrives_under_the_same_owner_with_the_home_node_ids,
         test_a_node_row_read_on_both_boxes_is_identical,
         test_the_sync_inserts_and_never_updates_or_deletes,
         test_an_unnamed_owner_is_skipped_a_keyless_table_refused_and_no_owners_raises]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except BaseException as e:  # noqa: BLE001 — a proof reports, never hides
            failed += 1
            print(f"  RED  {t.__name__}: {type(e).__name__}: {str(e)[:500]}")
    print(f"{'GREEN' if not failed else 'RED'} - {len(TEETH) - failed}/{len(TEETH)} teeth")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
