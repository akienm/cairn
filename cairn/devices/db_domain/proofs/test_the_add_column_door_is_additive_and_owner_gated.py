"""Proof: db_domain's ADD-COLUMN door is additive only and owner-gated (Law 6).

The librarian's row-id migration (T5) needs 39 live leaf tables to gain a ``row bigint`` column, and the
store has a door for a constraint and a door for an index but none for a column, so the only way was raw
ALTER TABLE outside db_domain, which the_constraint_door_is_the_only_alter probe reds. ``add_owned_column``
is that door: the owner adds ONE nullable column (or one with a literal default), rows survive, and the
door never drops a column, never retypes one and takes a bare type name and nothing else.

  1. The owner adds a column: it returns True, every existing row survives unchanged and reads NULL in the
     new column (or the default when one is given), and adding it again returns False (idempotent).
  2. A non-owner is refused with OwnershipError and the column is not added; a table db_domain never created
     is refused too.
  3. A retype (the same column, another base type) is refused and leaves type and rows as they were; a type
     string that carries a statement, a key, a default or NOT NULL is refused and the table stands; across all
     the refusals the column list never shrinks.

Each tooth works in a scratch table the store drops at exit (it runs against the TESTING database when the
tester marked the run). Run: python3 cairn/devices/db_domain/proofs/test_the_add_column_door_is_additive_and_owner_gated.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"add-column": {
    "1": "test_the_owner_adds_a_column_and_the_rows_survive",
    "2": "test_a_non_owner_is_refused_and_adds_nothing",
    "3": "test_a_retype_or_a_drop_or_more_than_a_type_is_refused",
}}

OWNER = "librarian"
COLUMNS = {"leaf_id": "text PRIMARY KEY", "weight": "double precision"}


def _columns(store, conn, table: str) -> dict[str, str]:
    rows = store.query("select column_name as n, data_type as t from information_schema.columns "
                       "where table_schema = 'public' and table_name = %s order by ordinal_position",
                       tables={}, params=(table,), conn=conn)
    return {r["n"]: r["t"] for r in rows}


def _stock(store, conn, table: str) -> None:
    for i in range(3):
        store.write(table, OWNER, {"leaf_id": f"l{i}", "weight": 0.5 + i}, conn=conn)


def test_the_owner_adds_a_column_and_the_rows_survive():
    from cairn.devices.db_domain.tools.client import store
    conn = store.connect()
    with store.scratch(OWNER, "add_col_a", COLUMNS, conn=conn) as table:
        _stock(store, conn, table)
        before = store.read(table, conn=conn)
        assert store.add_owned_column(table, OWNER, "row", "bigint", conn=conn) is True
        after = store.read(table, conn=conn)
        assert len(after) == 3, f"rows were lost: {after}"
        assert [{k: v for k, v in r.items() if k != "row"} for r in after] == [{k: v for k, v in r.items()} for r in before]
        assert all(r["row"] is None for r in after), after
        assert _columns(store, conn, table)["row"] == "bigint"
        assert store.add_owned_column(table, OWNER, "row", "bigint", conn=conn) is False, "a second add was not idempotent"
        assert store.add_owned_column(table, OWNER, "tag", "text", default="unset", conn=conn) is True
        assert {r["tag"] for r in store.read(table, conn=conn)} == {"unset"}, "a default did not fill the existing rows"
    conn.close()


def test_a_non_owner_is_refused_and_adds_nothing():
    from cairn.devices.db_domain.tools.client import store
    conn = store.connect()
    with store.scratch(OWNER, "add_col_b", COLUMNS, conn=conn) as table:
        _stock(store, conn, table)
        try:
            store.add_owned_column(table, "stranger", "row", "bigint", conn=conn)
        except store.OwnershipError:
            pass
        else:
            raise AssertionError("a non-owner added a column")
        assert "row" not in _columns(store, conn, table), "the refused column was added anyway"
        assert len(store.read(table, conn=conn)) == 3
        try:
            store.add_owned_column("a_table_db_domain_never_made", OWNER, "row", "bigint", conn=conn)
        except store.OwnershipError:
            pass
        else:
            raise AssertionError("a column was added to a table with no owner")
    conn.close()


def test_a_retype_or_a_drop_or_more_than_a_type_is_refused():
    from cairn.devices.db_domain.tools.client import store
    conn = store.connect()
    with store.scratch(OWNER, "add_col_c", COLUMNS, conn=conn) as table:
        _stock(store, conn, table)
        store.add_owned_column(table, OWNER, "row", "bigint", conn=conn)
        start = _columns(store, conn, table)
        rows = store.read(table, conn=conn)
        # a retype of an existing column, and of a column the table was born with
        for name, wanted, held in (("row", "text", "bigint"), ("weight", "text", "double precision")):
            try:
                store.add_owned_column(table, OWNER, name, wanted, conn=conn)
            except store.SchemaChangeRefused as exc:
                assert held in str(exc), exc
            else:
                raise AssertionError(f"{name} was retyped to {wanted}")
        # more than a bare type: a statement, a key, a default, NOT NULL, an unknown type
        for bad in ("bigint; DROP TABLE " + table, "bigint PRIMARY KEY", "bigint NOT NULL", "bigint DEFAULT 1",
                    "text) ; DROP TABLE x --", "no_such_type_at_all"):
            try:
                store.add_owned_column(table, OWNER, "extra", bad, conn=conn)
            except store.SchemaChangeRefused:
                pass
            else:
                raise AssertionError(f"{bad!r} was accepted as a column type")
        try:
            store.add_owned_column(table, OWNER, "bad name; drop", "bigint", conn=conn)
        except store.SchemaChangeRefused:
            pass
        else:
            raise AssertionError("a name that is not a plain identifier was accepted")
        end = _columns(store, conn, table)
        assert end == start, f"the column list moved through refusals: {start} -> {end}"
        assert store.read(table, conn=conn) == rows, "rows changed through refusals"
        assert not hasattr(store, "drop_owned_column") and not hasattr(store, "retype_owned_column"), \
            "a door that drops or retypes a column exists"
    conn.close()


TEETH = [test_the_owner_adds_a_column_and_the_rows_survive,
         test_a_non_owner_is_refused_and_adds_nothing,
         test_a_retype_or_a_drop_or_more_than_a_type_is_refused]


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
