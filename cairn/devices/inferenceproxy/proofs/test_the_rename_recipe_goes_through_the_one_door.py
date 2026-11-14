"""Proof for ticket 1468fcdb10ab: the inference proxy's rename recipe reaches 5432 only through db_domain.

Measured 2026-11-13 on akienyoga9i at origin/main c3d8c3593: tools/import_sieve's
test_sole_path_is_clean_on_the_real_corpus_for_both_domains reds with
    cairn/devices/inferenceproxy/rename_instance.py imports ['psycopg2', 'psycopg2.sql'] — a SECOND door to 5432
The import came in with 60e1dd170 (ticket f942a413f26d): ``apply_tables`` composed its DDL with
``psycopg2.sql``. The recipe now quotes its identifiers itself (``_ident``) and runs on the store's
connection, so the only file importing a Postgres driver is db_domain's store.

  1. the 5432 sole-path rule, over the real corpus, catches nothing under cairn/devices/inferenceproxy/,
     and the recipe's own imports (read, not grepped) hold no driver;
  2. the DDL the recipe composes quotes every identifier the way sql.Identifier does (a quote inside
     a name doubled), for the fold, the table rename and the index rename, driven over a recording
     connection: no database needed, so this tooth runs on every box. The live-table behaviour stays
     with test_the_proxy_stands_at_its_outline_address.py's tooth 4.

    bin/cairn test cairn/devices/inferenceproxy/proofs/test_the_rename_recipe_goes_through_the_one_door.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"1468fcdb10ab": {
    "1": "test_the_recipe_imports_no_driver",
    "2": "test_the_ddl_quotes_every_identifier"}}

RECIPE = _REPO / "cairn" / "devices" / "inferenceproxy" / "rename_instance.py"
DRIVERS = ("psycopg2", "psycopg", "asyncpg", "pg8000", "sqlalchemy")


def test_the_recipe_imports_no_driver():
    from cairn.tools.import_sieve import sieve
    own = sieve.imports_in(RECIPE.read_text(encoding="utf-8"))
    assert {"json", "shutil"} <= own, f"the recipe's imports did not parse: {own}"
    assert not [m for m in own if m.split(".")[0] in DRIVERS], f"the recipe imports a driver: {own}"
    graph = sieve.import_graph(str(_REPO))
    caught = sieve.catches(graph, {"kind": "sole_path", "capability": "port 5432", "modules": DRIVERS,
                                   "only": "cairn/devices/db_domain/"}, floor=1)
    mine = [c for c in caught if c.startswith("cairn/devices/inferenceproxy/")]
    assert mine == [], f"a second door to 5432 under inferenceproxy: {mine}"


class _Cursor:
    def __init__(self, log: list[str], stands: set[str]):
        self.log, self.stands, self._one, self._all, self.rowcount = log, stands, None, [], 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, stmt, params=()):
        self.log.append(stmt)
        if "information_schema.tables" in stmt:
            self._one = (1,) if params[0] in self.stands else None
        elif "information_schema.columns" in stmt:
            self._all = [("leaf_id",), ('ke"y',)]
        elif "pg_indexes" in stmt:
            self._one = (1,) if params[0].endswith("_pkey") else None
        else:
            self.rowcount = 2

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


class _Conn:
    def __init__(self, stands: set[str]):
        self.log: list[str] = []
        self.stands = stands

    def cursor(self):
        return _Cursor(self.log, self.stands)


class _Store:
    """The store's surface the recipe calls; owner_of answers from the tables that stand."""
    _REGISTRY = "registry"

    def __init__(self, owners: dict[str, str]):
        self.owners, self.calls = dict(owners), []

    def owner_of(self, table, *, conn=None):
        return self.owners.get(table)

    def drop_table(self, table, owner, *, conn=None):
        self.calls.append(("drop_table", table, owner))
        self.owners.pop(table, None)
        return True

    def update(self, table, owner, changes, *, where, params=(), conn=None):
        self.calls.append(("update", table, owner, changes))
        self.owners[changes["table_name"]] = changes["owner"]
        self.owners.pop(params[0], None)
        return 1

    def delete(self, table, owner, *, where=None, params=(), conn=None):
        self.calls.append(("delete", table, owner, params))
        return 1


def test_the_ddl_quotes_every_identifier(monkeypatch):
    from cairn.devices.inferenceproxy import rename_instance as rec
    old, new = 'old"nodes', "new_nodes"
    store = _Store({old: "o", new: "n"})
    monkeypatch.setattr(rec, "_store", lambda: store)
    conn = _Conn({old, new})
    done = rec.apply_tables(((old, new),), old_owner="o", new_owner="n", conn=conn)
    ddl = [s for s in conn.log if not s.lstrip().upper().startswith("SELECT")]
    assert ddl == [
        'INSERT INTO "old""nodes" ("leaf_id", "ke""y") SELECT "leaf_id", "ke""y" FROM "new_nodes" '
        "ON CONFLICT DO NOTHING",
        'ALTER TABLE IF EXISTS "old""nodes" RENAME TO "new_nodes"',
        'ALTER INDEX "old""nodes_pkey" RENAME TO "new_nodes_pkey"',
    ], ddl
    assert ("drop_table", new, "n") in store.calls, store.calls
    assert ("update", "registry", "db_domain", {"table_name": new, "owner": "n"}) in store.calls, store.calls
    assert done[:2] == [f"folded 2 row(s) of {new} into {old}", f"dropped {new}"], done


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
