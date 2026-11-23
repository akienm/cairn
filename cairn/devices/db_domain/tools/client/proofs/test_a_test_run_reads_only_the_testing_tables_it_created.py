"""Proof for ticket b7b90c36cb37: a test run reads from cairn_testing only the tables it created.

e4fd7f28faaf's intention says a test run reads live "except a table the run itself created". Its
router read any table cairn_testing held, whichever run left it there. Measured 2026-11-23
(a4c8bf408dc2): inferenceproxy's LIVE tooth read 224 rows that earlier runs wrote, not live's
20216. Here the scope is a set on each cairn_testing registry row, ``cairn_owned.test_ids``.
create_owned_table appends the creating run's id to it, and the router reads testing only when
the reading run's id is in the set. One tooth per falsifier clause:

  1. under test id A, a table A created reads from cairn_testing (its rows, not live's);
  2. under test id B, the table A created reads LIVE: the count equals the count with no id,
     and an INSERT sent down that read path raises a read-only error;
  3. a cairn_testing table whose registry row names no run (one born before the set, like the
     224 stale answer rows' table) routes no run to testing;
  4. after B also creates the table, A and B both read it from testing, and C reads it live.

Every tooth borrows a live owned table with more than one row that cairn_testing does not hold.
It only reads that table, and makes a one-row testing copy of the same name, so "read live" (N)
and "read testing" (1) give different answers. Nothing is written live. Each tooth drops the
testing copy and its testing registry row at the end.

    PYTHONPATH=. python3 cairn/devices/db_domain/tools/client/proofs/test_a_test_run_reads_only_the_testing_tables_it_created.py
"""
from __future__ import annotations

import contextlib
import os
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import psycopg2  # noqa: E402 - db_domain's own proof: the store's driver, never a dial of its own

from cairn.devices.db_domain.tools.client import store  # noqa: E402

PROVES = {"b7b90c36cb37": {
    "1": "test_a_run_reads_its_own_table_from_testing",
    "2": "test_another_run_reads_that_table_live_and_cannot_write_it",
    "3": "test_a_table_no_run_created_routes_no_run_to_testing",
    "4": "test_two_creators_both_read_testing_and_a_third_reads_live",
}}

_VAR = "CAIRN_TESTER_TEST_ID"
_OWNER = "tester"
_RUN = uuid.uuid4().hex[:8]
_A, _B, _C = (f"test-b7b9{_RUN}{x}" for x in "abc")


@contextlib.contextmanager
def _as(test_id: str | None):
    """This process carries ``test_id`` for the body (None: no test run at all)."""
    was = os.environ.get(_VAR)
    if test_id is None:
        os.environ.pop(_VAR, None)
    else:
        os.environ[_VAR] = test_id
    try:
        yield
    finally:
        if was is None:
            os.environ.pop(_VAR, None)
        else:
            os.environ[_VAR] = was


def _count(name: str, test_id: str | None) -> int:
    with _as(test_id):
        return store.query("SELECT count(*) AS n FROM {t}", tables={"t": name})[0]["n"]


def _a_live_table() -> str:
    """A live owned table with more than one row that cairn_testing does not hold. The proof only
    reads it; reading live gives its count and reading the one-row testing copy gives 1."""
    with _as(_A):
        held = {r["table_name"] for r in store.query("SELECT table_name FROM {r}", tables={"r": "cairn_owned"})}
    with _as(None):
        live = store.connect()
    try:
        for r in store.query("SELECT o.table_name FROM {r} o JOIN pg_tables p ON p.tablename = o.table_name "
                             "WHERE p.schemaname = 'public' ORDER BY o.created",
                             tables={"r": "cairn_owned"}, conn=live):
            name = r["table_name"]
            if name in held or name.startswith("cairn_") or store.is_scratch(name):
                continue
            if store.query("SELECT count(*) AS n FROM {t}", tables={"t": name}, conn=live)[0]["n"] > 1:
                return name
    finally:
        live.close()
    raise AssertionError("live holds no owned table with more than one row outside cairn_testing")


def _testing_copy(name: str, creator: str) -> None:
    """A one-row cairn_testing table of that name, created through the store door under ``creator``."""
    with _as(creator):
        store.create_owned_table(name, _OWNER, {"k": "text"})
        conn = store.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f'SELECT count(*) FROM "{name}"')
                if cur.fetchone()[0] == 0:
                    cur.execute(f'INSERT INTO "{name}" DEFAULT VALUES')
        finally:
            conn.close()


def _drop_testing(name: str) -> None:
    """Drop the testing copy and its testing registry row only; live is never touched."""
    with _as(_A):
        conn = store.connect()
        try:
            with conn.cursor() as cur:
                assert _dbname(conn) == store.TESTING_DB_NAME
                cur.execute(f'DROP TABLE IF EXISTS "{name}"')
                cur.execute("DELETE FROM cairn_owned WHERE table_name = %s", (name,))
        finally:
            conn.close()


def _dbname(conn) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        return cur.fetchone()[0]


def test_a_run_reads_its_own_table_from_testing():
    name = _a_live_table()
    try:
        _testing_copy(name, _A)
        got = _count(name, _A)
        assert got == 1, f"run A read {got} rows of {name}, the table it created; want testing's 1"
    finally:
        _drop_testing(name)


def test_another_run_reads_that_table_live_and_cannot_write_it():
    name = _a_live_table()
    try:
        bare = _count(name, None)
        _testing_copy(name, _A)
        got = _count(name, _B)
        with _as(_B):
            try:
                store.query("INSERT INTO {t} SELECT * FROM {t} WHERE false", tables={"t": name})
            except psycopg2.Error as exc:
                refused = exc
            else:
                refused = None
        assert got == bare, f"run B read {got} rows of {name}, which run A created; live holds {bare}"
        assert isinstance(refused, psycopg2.errors.ReadOnlySqlTransaction), \
            f"run B's INSERT down the read path was not refused read-only: {type(refused).__name__}: {refused}"
        assert _count(name, None) == bare, f"live's {name} changed across the tooth"
    finally:
        _drop_testing(name)


def test_a_table_no_run_created_routes_no_run_to_testing():
    """A registry row naming no creating run: the table a pre-fix run left behind."""
    name = _a_live_table()
    try:
        bare = _count(name, None)
        _testing_copy(name, _A)
        with _as(_A):
            conn = store.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM information_schema.columns "
                            "WHERE table_name = 'cairn_owned' AND column_name = 'test_ids'")
                if cur.fetchone() is not None:
                    cur.execute("UPDATE cairn_owned SET test_ids = '{}' WHERE table_name = %s", (name,))
        finally:
            conn.close()
        seen = {who: _count(name, who) for who in (_A, _B)}
        assert all(v == bare for v in seen.values()), \
            f"a testing table no run created routed a read to testing: {seen}; live holds {bare}"
    finally:
        _drop_testing(name)


def test_two_creators_both_read_testing_and_a_third_reads_live():
    name = _a_live_table()
    try:
        bare = _count(name, None)
        _testing_copy(name, _A)
        _testing_copy(name, _B)
        seen = {who: _count(name, who) for who in (_A, _B, _C)}
        assert seen[_A] == 1 and seen[_B] == 1, \
            f"after A and B both created {name}, they read {seen[_A]} and {seen[_B]} rows; want testing's 1"
        assert seen[_C] == bare, f"run C, which created nothing, read {seen[_C]} rows; live holds {bare}"
    finally:
        _drop_testing(name)


TEETH = [test_a_run_reads_its_own_table_from_testing,
         test_another_run_reads_that_table_live_and_cannot_write_it,
         test_a_table_no_run_created_routes_no_run_to_testing,
         test_two_creators_both_read_testing_and_a_third_reads_live]


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
