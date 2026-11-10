"""Proof for ticket fe263b21cece — a keyed find asks the table's shape once.

Measured 2026-11-10 while building ticket 98ab0e9db57f: trees.find over a keyed leaf took 2.0 ms
against 0.28 ms for a table read, 1.69 ms of it in _is_keyed's information_schema query, which ran
on every call. A leaf's shape is fixed when ensure_trees makes it, so find remembers a keyed
table's shape for the process, and a scratch leaf takes its memory with it when it drops.

One tooth per numbered falsifier clause:

  1. fifty finds over one keyed leaf ask the catalog for its columns at most once.
  2. find's median over a 300-node keyed leaf is at most 4x a store.read of the same leaf by key.
  3. a name a scratch keyed leaf held, reused by a vectored scratch leaf after the first drops, is
     refused by find with WalkRefused.
  4. the charter beside trees.py says find remembers a keyed table's shape.

Requires the db_domain provisioning; every leaf is scratch, and its nodes are forgotten before it
drops.

    bin/cairn test cairn/devices/librarian/tools/trees/proofs/test_a_keyed_find_asks_the_tables_shape_once.py
"""

from __future__ import annotations

import contextlib
import json
import statistics
import sys
import time
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"fe263b21cece": {
    "1": "fifty_finds_ask_the_shape_at_most_once",
    "2": "a_keyed_find_is_within_four_reads",
    "3": "a_reused_name_is_judged_by_its_new_shape",
    "4": "the_charter_names_the_remembered_shape",
}}

CHARTER = _REPO_ROOT / "cairn" / "devices" / "librarian" / "tools" / "trees" / "intention+why.json"
_RUN = uuid.uuid4().hex[:8]
_SCRATCH = contextlib.ExitStack()
_TABLES: list[str] = []
PROV = {"source": "testing: fe263b21cece proof"}

PASS = 0
FAIL = 0


def _trees():
    from cairn.devices.librarian.tools.trees import trees
    return trees


def _store():
    from cairn.devices.db_domain.tools.client import store
    return store


def _keyed(n: int) -> str:
    t = _trees()
    table = _SCRATCH.enter_context(t.scratch_leaf("kfproof", keyed=True))
    _TABLES.append(table)
    for i in range(n):
        t.deposit_keyed(f"testing {_RUN}: answer {i}, a stored answer found by its key",
                        f"k{i}-{_RUN}", PROV, table=table, owner=t.OWNER)
    return table


def _median_ms(fn, n: int = 200) -> float:
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts) * 1000


def fifty_finds_ask_the_shape_at_most_once():
    t, store = _trees(), _store()
    table = _keyed(3)
    asked: list[str] = []
    real = store.query

    def counting(sql, *a, **kw):
        low = sql.lower()
        if "information_schema" in low or "pg_attribute" in low:
            asked.append(sql)
        return real(sql, *a, **kw)
    store.query = counting
    try:
        for _ in range(50):
            got = t.find(f"k1-{_RUN}", table=table)
            assert len(got) == 1, got
    finally:
        store.query = real
    assert len(asked) <= 1, f"{len(asked)} shape queries over 50 finds"


def a_keyed_find_is_within_four_reads():
    t, store = _trees(), _store()
    table = _keyed(300)
    conn = store.connect()
    try:
        key = f"k17-{_RUN}"
        assert len(t.find(key, table=table, conn=conn)) == 1
        read = _median_ms(lambda: store.read(table, where="key = %s", params=(key,), conn=conn))
        find = _median_ms(lambda: t.find(key, table=table, conn=conn))
    finally:
        conn.close()
    assert find <= 4 * read, f"find {find:.3f} ms is more than 4x the read {read:.3f} ms"


def a_reused_name_is_judged_by_its_new_shape():
    t, store = _trees(), _store()
    name = f"kfreuse_{_RUN}"
    real = store.scratch_name
    store.scratch_name = lambda prefix, suffix="": name
    try:
        with t.scratch_leaf("kfreuse", keyed=True) as table:
            assert table == name, table
            t.deposit_keyed(f"testing {_RUN}: the keyed tenant of a reused name", f"r-{_RUN}",
                            PROV, table=table, owner=t.OWNER)
            assert len(t.find(f"r-{_RUN}", table=table)) == 1
            t.forget_leaf(table)
        with t.scratch_leaf("kfreuse") as table:
            assert table == name, table
            try:
                t.find(f"r-{_RUN}", table=table)
            except t.WalkRefused:
                pass
            else:
                raise AssertionError("find over the vectored tenant of a reused name was not refused")
    finally:
        store.scratch_name = real


def the_charter_names_the_remembered_shape():
    what = json.loads(CHARTER.read_text())["what"]
    assert "remembers a keyed table's shape" in what, "the charter's what does not say find remembers a keyed table's shape"


TEETH = [fifty_finds_ask_the_shape_at_most_once,
         a_keyed_find_is_within_four_reads,
         a_reused_name_is_judged_by_its_new_shape,
         the_charter_names_the_remembered_shape]


def _forget() -> None:
    for table in _TABLES:
        try:
            _trees().forget_leaf(table)
        except Exception as exc:  # noqa: BLE001 — loud, never hidden
            print(f"  cleanup: forget_leaf({table}) failed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    try:
        for fn in TEETH:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
                FAIL += 1
                print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
            else:
                PASS += 1
                print(f"  green {fn.__name__}")
    finally:
        _forget()
        _SCRATCH.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
