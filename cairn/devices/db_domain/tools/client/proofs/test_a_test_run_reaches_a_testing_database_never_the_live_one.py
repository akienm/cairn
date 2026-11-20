"""Proof for ticket e4fd7f28faaf: a test run reaches a TESTING database, never the live one.

Under a test run (the process carries CAIRN_TESTER_TEST_ID) every write the store door makes lands
in ``cairn_testing``; reads of a table the run did not create read live through a read-only
connection; a table the run created reads from ``cairn_testing``. Without a test id, ``cairn``.
One tooth per falsifier clause:

  1. with the id set, the store door's connection answers current_database() = cairn_testing
     (created on demand); unset, ``cairn``.
  2. a scratch table minted under the id is in cairn_testing and not live; sweep_scratch() under
     the id leaves a live scratch table of a killed minter (and its registry row) standing.
  3. a table written through store.write under the id lands in cairn_testing with its owner row;
     the live owner registry has no row of it.
  4. under the id, store.query of a live table the run did not create returns the live count, and
     an INSERT sent through that read path raises a read-only error; live's count is unchanged.
  5. under the id, a table the run created is read by store.query from cairn_testing (its rows),
     and live holds no table of that name.

The proof sets and clears the id in its own environment to ask each database by name; every name
it mints carries this run's marker and is dropped in both databases at the end of its tooth.

    PYTHONPATH=. python3 cairn/devices/db_domain/tools/client/proofs/test_a_test_run_reaches_a_testing_database_never_the_live_one.py
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

import psycopg2  # noqa: E402 - db_domain's own proof: the store's driver, never a dial of its own

from cairn.devices.db_domain.tools.client import store  # noqa: E402

PROVES = {"e4fd7f28faaf": {
    "1": "test_the_store_door_connects_to_cairn_testing_under_a_test_id",
    "2": "test_scratch_under_a_test_id_lives_in_testing_and_the_sweep_leaves_live_standing",
    "3": "test_a_write_under_a_test_id_lands_in_testing_with_its_owner_row",
    "4": "test_a_live_table_reads_live_and_the_read_path_cannot_write",
    "5": "test_a_table_the_run_created_reads_from_testing",
}}

_VAR = "CAIRN_TESTER_TEST_ID"
_TESTING = "cairn_testing"
_OWNER = "tester"
_RUN = uuid.uuid4().hex[:8]
_ID = os.environ.get(_VAR) or f"test-e4fd{_RUN}"


@contextlib.contextmanager
def _marked(on: bool):
    """This process carries the test id (on) or carries none (off) for the body."""
    was = os.environ.get(_VAR)
    if on:
        os.environ[_VAR] = _ID
    else:
        os.environ.pop(_VAR, None)
    try:
        yield
    finally:
        if was is None:
            os.environ.pop(_VAR, None)
        else:
            os.environ[_VAR] = was


def _dbname(conn) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        return cur.fetchone()[0]


def _has_table(conn, name: str) -> bool:
    return bool(store.query("SELECT 1 AS x FROM pg_tables WHERE tablename = %s",
                            tables={}, params=(name,), conn=conn))


def _owner_row(conn, name: str) -> bool:
    return bool(store.query("SELECT 1 AS x FROM {r} WHERE table_name = %s",
                            tables={"r": "cairn_owned"}, params=(name,), conn=conn))


def _live():
    """A connection to the live database, opened with no test id in this process."""
    with _marked(False):
        conn = store.connect()
    assert _dbname(conn) == store.DB_NAME, _dbname(conn)
    return conn


def _testing():
    """The store door's connection under the test id: the database a test run writes."""
    with _marked(True):
        return store.connect()


def _drop_everywhere(name: str) -> None:
    for on in (True, False):
        with _marked(on):
            store.drop_table(name, _OWNER)


def test_the_store_door_connects_to_cairn_testing_under_a_test_id():
    conn = _testing()
    try:
        assert _dbname(conn) == _TESTING, f"under a test id the store door reached {_dbname(conn)!r}"
        assert store.query("SELECT 1 AS x FROM pg_database WHERE datname = %s",
                           tables={}, params=(_TESTING,), conn=conn), "cairn_testing was not created"
    finally:
        conn.close()
    with _marked(False):
        conn = store.connect()
    try:
        assert _dbname(conn) == store.DB_NAME == "cairn", f"with no test id the store door reached {_dbname(conn)!r}"
    finally:
        conn.close()


def _killed_live_minter() -> str:
    """A child with no test id mints a live scratch table and is killed before its finally."""
    env = {k: v for k, v in os.environ.items() if k != _VAR}
    env["PYTHONPATH"] = str(REPO) + os.pathsep + env.get("PYTHONPATH", "")
    code = ("import sys, time\n"
            "from cairn.devices.db_domain.tools.client import store\n"
            f"with store.scratch({_OWNER!r}, 'e4fd_dead_{_RUN}', {{'k': 'text'}}) as t:\n"
            "    print(t, flush=True)\n"
            "    time.sleep(120)\n")
    child = subprocess.Popen([sys.executable, "-c", code], env=env, cwd=str(REPO),
                             stdout=subprocess.PIPE, text=True)
    try:
        name = child.stdout.readline().strip()
    finally:
        child.kill()
        child.wait()
    assert name, "the live minter printed no table"
    return name


def test_scratch_under_a_test_id_lives_in_testing_and_the_sweep_leaves_live_standing():
    live = _live()
    dead = None
    try:
        with _marked(True):
            with store.scratch(_OWNER, f"e4fd_scr_{_RUN}", {"k": "text"}) as name:
                t = store.connect()
                try:
                    assert _dbname(t) == _TESTING, _dbname(t)
                    assert _has_table(t, name), f"{name} is not in cairn_testing"
                finally:
                    t.close()
                assert not _has_table(live, name), f"a scratch table minted under a test id is in live: {name}"
        dead = _killed_live_minter()
        assert _has_table(live, dead) and store.is_scratch(dead, conn=live), "the killed minter's live table is missing"
        with _marked(True):
            store.sweep_scratch()
        assert _has_table(live, dead), "sweep_scratch under a test id dropped a live scratch table"
        assert store.is_scratch(dead, conn=live), "sweep_scratch under a test id removed a live registry row"
    finally:
        if dead:
            with _marked(False):
                store.sweep_scratch()
            assert not _has_table(live, dead), "the live sweep left the killed minter's table"
        live.close()


def test_a_write_under_a_test_id_lands_in_testing_with_its_owner_row():
    name = f"e4fd_w_{_RUN}"
    live = _live()
    try:
        with _marked(True):
            store.create_owned_table(name, _OWNER, {"k": "text"})
            store.write(name, _OWNER, {"k": "testing-row"})
        t = _testing()
        try:
            assert _has_table(t, name), f"{name} is not in cairn_testing"
            assert _owner_row(t, name), f"cairn_testing's owner registry has no row for {name}"
            assert store.query("SELECT k FROM {t}", tables={"t": name}, conn=t) == [{"k": "testing-row"}]
        finally:
            t.close()
        assert not _has_table(live, name), f"a write under a test id created {name} in live"
        assert not _owner_row(live, name), f"a write under a test id registered {name} in live's owner registry"
    finally:
        live.close()
        _drop_everywhere(name)


def _a_live_table(live) -> str:
    """A live, owned table with rows that cairn_testing does not hold."""
    t = _testing()
    try:
        testing = {r["table_name"] for r in store.query("SELECT table_name FROM {r}", tables={"r": "cairn_owned"}, conn=t)}
    finally:
        t.close()
    for r in store.query("SELECT o.table_name FROM {r} o JOIN pg_tables p ON p.tablename = o.table_name "
                         "WHERE p.schemaname = 'public' ORDER BY o.created",
                         tables={"r": "cairn_owned"}, conn=live):
        name = r["table_name"]
        if name in testing or name.startswith("cairn_"):
            continue
        if store.query("SELECT count(*) AS n FROM {t}", tables={"t": name}, conn=live)[0]["n"]:
            return name
    raise AssertionError("live holds no owned table with rows outside cairn_testing")


def test_a_live_table_reads_live_and_the_read_path_cannot_write():
    live = _live()
    try:
        table = _a_live_table(live)
        count = "SELECT count(*) AS n FROM {t}"
        before = store.query(count, tables={"t": table}, conn=live)[0]["n"]
        with _marked(True):
            seen = store.query(count, tables={"t": table})[0]["n"]
            try:
                store.query("INSERT INTO {t} SELECT * FROM {t} WHERE false", tables={"t": table})
            except psycopg2.Error as exc:
                refused = exc
            else:
                refused = None
        assert seen == before, f"under a test id {table} read {seen} rows; live holds {before}"
        assert isinstance(refused, psycopg2.errors.ReadOnlySqlTransaction), \
            f"an INSERT through the read path was not refused read-only: {type(refused).__name__}: {refused}"
        after = store.query(count, tables={"t": table}, conn=live)[0]["n"]
        assert after == before, f"{table} went from {before} to {after} rows across the tooth"
    finally:
        live.close()


def test_a_table_the_run_created_reads_from_testing():
    name = f"e4fd_r_{_RUN}"
    live = _live()
    try:
        with _marked(True):
            store.create_owned_table(name, _OWNER, {"k": "text"})
            store.write(name, _OWNER, {"k": "only-in-testing"})
            rows = store.query("SELECT k FROM {t}", tables={"t": name})
        assert rows == [{"k": "only-in-testing"}], f"store.query under a test id read {rows}"
        assert not _has_table(live, name), f"live holds a table named {name}"
    finally:
        live.close()
        _drop_everywhere(name)


TEETH = [test_the_store_door_connects_to_cairn_testing_under_a_test_id,
         test_scratch_under_a_test_id_lives_in_testing_and_the_sweep_leaves_live_standing,
         test_a_write_under_a_test_id_lands_in_testing_with_its_owner_row,
         test_a_live_table_reads_live_and_the_read_path_cannot_write,
         test_a_table_the_run_created_reads_from_testing]


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
