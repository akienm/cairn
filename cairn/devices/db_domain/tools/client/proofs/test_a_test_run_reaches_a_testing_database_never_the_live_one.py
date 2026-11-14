"""Proof: a test run reaches a TESTING database, never the live one.

Akien 2026-11-14 (relayed, answering Q#104): "we need a TESTING database." The lived symptom: tests and
scratch tables shared the live ``cairn`` database, so a sweep bug (5b940b1c4fbe) dropped live-process tables
and 36 orphan ``seal_ann_*_delivery`` tables stood in it. A process the tester marked (CAIRN_TESTER_TEST_ID)
now dials ``cairn_testing``; one that is not dials ``cairn``.

THE PROOF NEVER TOUCHES THE REAL DATABASES. It points the store's two names at stand-ins minted and dropped
here (``cairn_td_live_<tag>`` as the "live" name, ``cairn_td_testing_<tag>`` as the testing one), which is
what a module constant a caller can bend is for, and it sets and clears the run marker in the environment it
runs in.

  1. With the marker set, ``connect()`` answers current_database() = the testing name (created on demand);
     with it unset, the live name.
  2. A scratch table minted under the marker exists in the testing database and NOT in the live one; and a
     sweep run under the marker leaves a SWEEPABLE (dead-minter) scratch table standing in the live one.
  3. A table written through store.write under the marker lands in the testing database, owner registry
     included, and the live database's owner registry is unchanged.

    python3 cairn/devices/db_domain/tools/client/proofs/test_a_test_run_reaches_a_testing_database_never_the_live_one.py
"""
from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"testing-db": {
    "1": "test_the_run_marker_picks_the_testing_database",
    "2": "test_a_test_run_scratch_table_and_sweep_never_reach_the_live_database",
    "3": "test_a_write_under_the_marker_lands_in_the_testing_database_registry_included",
}}

MARK = "CAIRN_TESTER_TEST_ID"


@contextlib.contextmanager
def _two_databases(marked: bool):
    """Stand-in live and testing databases bent into the store, the marker set or cleared for the block."""
    import psycopg2
    from cairn.devices.db_domain.tools.client import store
    tag = uuid.uuid4().hex[:8]
    live, testing = f"cairn_td_live_{tag}", f"cairn_td_testing_{tag}"
    saved = (store.DB_NAME, getattr(store, "TESTING_DB_NAME", None), os.environ.get(MARK))   # getattr: an unfixed store reds on behaviour, not on a missing name
    boot = psycopg2.connect(dbname="postgres", **store._conn_args())
    boot.autocommit = True
    try:
        with boot.cursor() as cur:
            cur.execute(f'CREATE DATABASE "{live}"')   # the testing one is created ON DEMAND, by the store
        store.DB_NAME, store.TESTING_DB_NAME = live, testing
        if marked:
            os.environ[MARK] = "test-proof-td"
        else:
            os.environ.pop(MARK, None)
        yield live, testing, store
    finally:
        store.DB_NAME = saved[0]
        if saved[1] is None:
            with contextlib.suppress(AttributeError):
                del store.TESTING_DB_NAME
        else:
            store.TESTING_DB_NAME = saved[1]
        if saved[2] is None:
            os.environ.pop(MARK, None)
        else:
            os.environ[MARK] = saved[2]
        with boot.cursor() as cur:
            for n in (live, testing):
                with contextlib.suppress(Exception):
                    cur.execute(f'DROP DATABASE IF EXISTS "{n}" WITH (FORCE)')
        boot.close()


def _current(store) -> str:
    conn = store.connect()
    try:
        return store.query("select current_database() as d", tables={}, conn=conn)[0]["d"]
    finally:
        conn.close()


def _dbs_with(table: str, live: str, testing: str, store) -> set[str]:
    import psycopg2
    found = set()
    for name in (live, testing):
        try:
            c = psycopg2.connect(dbname=name, **store._conn_args())
        except Exception:  # noqa: BLE001 - a database that does not exist holds nothing
            continue
        try:
            with c.cursor() as cur:
                cur.execute("select 1 from pg_tables where tablename = %s", (table,))
                if cur.fetchone():
                    found.add(name)
        finally:
            c.close()
    return found


def test_the_run_marker_picks_the_testing_database():
    with _two_databases(marked=True) as (live, testing, store):
        assert _current(store) == testing, "a marked run did not reach the testing database"
    with _two_databases(marked=False) as (live, testing, store):
        assert _current(store) == live, "an unmarked process did not reach the live database"


def test_a_test_run_scratch_table_and_sweep_never_reach_the_live_database():
    import psycopg2
    with _two_databases(marked=False) as (live, testing, store):
        # a sweepable family in the LIVE database: a scratch row whose minter is a pid that has exited
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait()
        conn = store.connect()
        store.create_owned_table("td_live_orphan", "db_domain", {"k": "text PRIMARY KEY"}, conn=conn)
        store._ensure_scratch_registry(conn)
        with conn.cursor() as cur:
            cur.execute(f'INSERT INTO "{store._SCRATCH}" (table_name, pid) VALUES (%s, %s)', ("td_live_orphan", child.pid))
        conn.close()
        os.environ[MARK] = "test-proof-td"
        with store.scratch("db_domain", "td_probe", {"k": "text PRIMARY KEY"}) as table:
            assert _dbs_with(table, live, testing, store) == {testing}, "the scratch table is not only in the testing database"
            store.sweep_scratch()
        os.environ.pop(MARK, None)
        assert "td_live_orphan" in {r["table_name"] for r in store.read(store._SCRATCH, conn=store.connect())}, \
            "a sweep run under the marker reached the live database's registry"
        assert _dbs_with("td_live_orphan", live, testing, store) == {live}, "a sweep under the marker dropped a live table"
        # the control: the same sweep UNMARKED does reach it, so the tooth above measures separation, not an inert sweep
        assert store.sweep_scratch() >= 1, "the unmarked sweep did not drop the dead minter's table: the control is inert"
        assert _dbs_with("td_live_orphan", live, testing, store) == set()


def test_a_write_under_the_marker_lands_in_the_testing_database_registry_included():
    with _two_databases(marked=True) as (live, testing, store):
        conn = store.connect()
        store.create_owned_table("td_marked_table", "librarian", {"k": "text PRIMARY KEY"}, conn=conn)
        store.write("td_marked_table", "librarian", {"k": "a"}, conn=conn)
        conn.close()
        assert _dbs_with("td_marked_table", live, testing, store) == {testing}
        os.environ.pop(MARK, None)
        live_conn = store.connect()
        owned = {r["table_name"] for r in store.read("cairn_owned", conn=live_conn)}
        live_conn.close()
        assert "td_marked_table" not in owned, "the live owner registry learned a table a test run made"


TEETH = [test_the_run_marker_picks_the_testing_database,
         test_a_test_run_scratch_table_and_sweep_never_reach_the_live_database,
         test_a_write_under_the_marker_lands_in_the_testing_database_registry_included]


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
