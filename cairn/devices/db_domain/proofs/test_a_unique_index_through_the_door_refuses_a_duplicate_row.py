"""Proof: db_domain's index door can declare a UNIQUE index, additive and owner-gated.

The librarian row-id migration (T5, Q#104): a node's master row number is its identity, so the migrated
``row bigint`` column on a leaf table must refuse a duplicate; a duplicate row is a wrong-data read. The
ADD-COLUMN door takes bare types only (no UNIQUE), so the guarantee rides the index door:
``add_owned_index(table, owner, name, columns, unique=True)``.

  1. The owner's unique index refuses a second row holding the same value, accepts distinct values, and
     asking for it again is a no-op (idempotent). NULLs stay distinct, so a column still being filled is
     unconstrained until it is.
  2. A non-owner is refused with OwnershipError and no index exists afterwards.
  3. The door never converts: a name that already stands as a non-unique index asked for as unique raises
     SchemaChangeRefused and stays non-unique; building a unique index over rows that already hold a
     duplicate raises and leaves no index behind.

Scratch tables the store drops at exit (the TESTING database when the tester marked the run).
Run: python3 cairn/devices/db_domain/proofs/test_a_unique_index_through_the_door_refuses_a_duplicate_row.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"add-unique-index": {
    "1": "test_the_owner_builds_a_unique_index_that_refuses_a_duplicate_row",
    "2": "test_a_non_owner_builds_no_unique_index",
    "3": "test_the_door_never_converts_an_index_and_a_duplicate_leaves_none",
}}

OWNER = "librarian"
COLUMNS = {"leaf_id": "text PRIMARY KEY", "row": "bigint"}


def _index(store, conn, name: str):
    rows = store.query("select i.indisunique as u from pg_class c join pg_index i on i.indexrelid = c.oid "
                       "where c.relname = %s and c.relkind = 'i'", tables={}, params=(name,), conn=conn)
    return rows[0]["u"] if rows else None


def test_the_owner_builds_a_unique_index_that_refuses_a_duplicate_row():
    from cairn.devices.db_domain.tools.client import store
    conn = store.connect()
    with store.scratch(OWNER, "uniq_a", COLUMNS, conn=conn) as table:
        store.add_owned_index(table, OWNER, f"{table}_row_uq", ["row"], unique=True, conn=conn)
        store.add_owned_index(table, OWNER, f"{table}_row_uq", ["row"], unique=True, conn=conn)   # idempotent
        assert _index(store, conn, f"{table}_row_uq") is True
        store.write(table, OWNER, {"leaf_id": "a", "row": 1}, conn=conn)
        store.write(table, OWNER, {"leaf_id": "b", "row": 2}, conn=conn)
        try:
            store.write(table, OWNER, {"leaf_id": "c", "row": 1}, conn=conn)
        except Exception as exc:  # noqa: BLE001 - the driver's own UniqueViolation
            assert "unique" in str(exc).lower() or "duplicate" in str(exc).lower(), exc
        else:
            raise AssertionError("a duplicate row was accepted under a unique index")
        store.write(table, OWNER, {"leaf_id": "d", "row": None}, conn=conn)
        store.write(table, OWNER, {"leaf_id": "e", "row": None}, conn=conn)   # NULLs are distinct
        assert len(store.read(table, conn=conn)) == 4
    conn.close()


def test_a_non_owner_builds_no_unique_index():
    from cairn.devices.db_domain.tools.client import store
    conn = store.connect()
    with store.scratch(OWNER, "uniq_b", COLUMNS, conn=conn) as table:
        try:
            store.add_owned_index(table, "stranger", f"{table}_row_uq", ["row"], unique=True, conn=conn)
        except store.OwnershipError:
            pass
        else:
            raise AssertionError("a non-owner built a unique index")
        assert _index(store, conn, f"{table}_row_uq") is None, "the refused index exists anyway"
    conn.close()


def test_the_door_never_converts_an_index_and_a_duplicate_leaves_none():
    from cairn.devices.db_domain.tools.client import store
    conn = store.connect()
    with store.scratch(OWNER, "uniq_c", COLUMNS, conn=conn) as table:
        plain = f"{table}_plain"
        store.add_owned_index(table, OWNER, plain, ["row"], conn=conn)
        try:
            store.add_owned_index(table, OWNER, plain, ["row"], unique=True, conn=conn)
        except store.SchemaChangeRefused:
            pass
        else:
            raise AssertionError("a non-unique index was turned into a unique one")
        assert _index(store, conn, plain) is False, "the index was converted"
        store.write(table, OWNER, {"leaf_id": "a", "row": 7}, conn=conn)
        store.write(table, OWNER, {"leaf_id": "b", "row": 7}, conn=conn)
        dup = f"{table}_dup_uq"
        try:
            store.add_owned_index(table, OWNER, dup, ["row"], unique=True, conn=conn)
        except Exception as exc:  # noqa: BLE001 - Postgres's own refusal, loud
            assert "duplicate" in str(exc).lower() or "unique" in str(exc).lower(), exc
        else:
            raise AssertionError("a unique index was built over rows that hold a duplicate")
        assert _index(store, conn, dup) is None, "a failed unique build left an index behind"
        assert len(store.read(table, conn=conn)) == 2
    conn.close()


TEETH = [test_the_owner_builds_a_unique_index_that_refuses_a_duplicate_row,
         test_a_non_owner_builds_no_unique_index,
         test_the_door_never_converts_an_index_and_a_duplicate_leaves_none]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except BaseException as e:  # noqa: BLE001 - a proof reports, never hides
            failed += 1
            print(f"  RED  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"{'GREEN' if not failed else 'RED'} - {len(TEETH) - failed}/{len(TEETH)} teeth")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
