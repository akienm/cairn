#!/usr/bin/env python3
"""Proof that db_domain's store creates an owned index, and only for the owner (ticket d494ff4ae955).

Measured 2026-11-10: the store had create_owned_table and add_owned_constraint and no index door;
outline 17.27.2 indexes the metrics table on name and source by time. Law 6: the owner alone gates
writes, and DDL is a write.

Teeth, one per falsifier clause (PROVES below):
  (1) the owner indexes named columns; pg_indexes shows one such index; a repeat is a no-op;
  (2) a non-owner, or a table db_domain never created, is refused and no index lands;
  (3) a column carrying SQL is quoted, raises, lands nothing, and the table stands; [] is refused.

    PYTHONPATH=. python3 cairn/devices/db_domain/proofs/test_an_owned_index_is_owner_gated.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.devices.db_domain.tools.client import store
from cairn.devices.db_domain.tools.client.store import OwnershipError

PROVES = {"d494ff4ae955": {
    "1": "test_the_owner_indexes_its_table_once",
    "2": "test_no_one_else_indexes_it",
    "3": "test_a_column_is_a_name_never_sql",
}}

_COLS = {"name": "text", "source": "text", "at": "timestamptz"}
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _indexes(table: str) -> dict[str, str]:
    rows = store.query("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' AND tablename = %s",
                       tables={}, params=(table,))
    return {r["indexname"]: r["indexdef"] for r in rows}


def test_the_owner_indexes_its_table_once() -> None:
    with store.scratch("tester", "idx", _COLS) as t:
        iname = t + "_name_at"
        store.add_owned_index(t, "tester", iname, ["name", "at"])
        store.add_owned_index(t, "tester", iname, ["name", "at"])
        got = _indexes(t)
        ok = iname in got and "(name, at)" in got[iname] and sum(1 for d in got.values() if "(name, at)" in d) == 1
        check("test_the_owner_indexes_its_table_once", ok, str(got))


def test_no_one_else_indexes_it() -> None:
    lacks = []
    with store.scratch("tester", "idx", _COLS) as t:
        try:
            store.add_owned_index(t, "impostor", t + "_imp", ["name"])
            lacks.append("a non-owner was not refused")
        except OwnershipError:
            pass
        ghost = f"_never_created_{uuid.uuid4().hex[:8]}"
        try:
            store.add_owned_index(ghost, "anyone", ghost + "_ix", ["name"])
            lacks.append("a table db_domain never created was not refused")
        except OwnershipError:
            pass
        if t + "_imp" in _indexes(t):
            lacks.append("the non-owner's index landed")
    check("test_no_one_else_indexes_it", not lacks, "; ".join(lacks))


def test_a_column_is_a_name_never_sql() -> None:
    lacks = []
    with store.scratch("tester", "idx", _COLS) as t:
        bad = t + "_bad"
        try:
            store.add_owned_index(t, "tester", bad, ["name) ; DELETE FROM " + t + " ; --"])
            lacks.append("a column carrying SQL did not raise")
        except (OwnershipError, ValueError) as exc:
            lacks.append(f"refused for the wrong reason: {exc}")
        except Exception:  # noqa: BLE001 — Postgres refuses the quoted name as an unknown column
            pass
        if bad in _indexes(t):
            lacks.append("an index landed from a column carrying SQL")
        if store.owner_of(t) != "tester":
            lacks.append("the table's owner record is gone")
        store.read(t)  # raises if the table was dropped
        try:
            store.add_owned_index(t, "tester", t + "_empty", [])
            lacks.append("an empty column list was not refused")
        except ValueError:
            pass
    check("test_a_column_is_a_name_never_sql", not lacks, "; ".join(lacks))


def main() -> int:
    for tooth in (test_the_owner_indexes_its_table_once, test_no_one_else_indexes_it, test_a_column_is_a_name_never_sql):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
