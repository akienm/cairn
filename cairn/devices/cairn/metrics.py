"""cairn/devices/cairn/metrics.py — the one metrics table, held by the cairn device (outline 17.27).

The cairn device holds the metrics table until Recovery exists (5.3.6, 6.6.3.4). Every source
records into its own holder's recorder through cairn.tools.metric (17.27.1); this module is the
table's side: it creates the table through db_domain's store, owned by 'cairn', indexed on name
and source by time (17.27.2), and when a consumer asks for a report it first picks up what waits
in every holder's recorder (17.27.3 — the read is the event; nothing polls). Rows are never
deleted here (17.27.5): the table is the history.
"""
from __future__ import annotations

import re
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from cairn.devices.db_domain.tools.client import store
from cairn.tools.base import flock
from cairn.tools.base.address import resolve
from cairn.tools.metric import metric

TABLE = "metrics"
OWNER = "cairn"
INDEXES = {"name_at": ["name", "at"], "source_at": ["source", "at"]}
LOCK = "instance/devices/cairn/0/metrics.lock"
_FLIGHT = threading.Lock()


def ensure_table(table: str = TABLE) -> None:
    """Create the table (idempotent) with metric.COLUMNS, and its two indexes."""
    store.create_owned_table(table, OWNER, metric.COLUMNS)
    for suffix, cols in INDEXES.items():
        store.add_owned_index(table, OWNER, f"{table}_{suffix}", cols)


def holders(roots: dict | None = None) -> list[Path]:
    """Every <instance root>/devices/<device>/<n>/ with metrics waiting in its recorder."""
    base = resolve("instance/devices", roots)
    if not base.is_dir():
        return []
    return [h for h in sorted(base.glob("*/*"))
            if (h / "tools" / "data_recorder" / metric.RECORDER / "records.jsonl").is_file()]


@contextmanager
def _single_flight(roots: dict | None):
    """One collector at a time (ticket a0016627c71e): a thread lock within the process and an
    exclusive flock on the cairn instance's lock file across processes. take reads a recorder
    whole and clears it only after the sink returns, so two collectors at once each land every
    record (measured 2026-11-10: eight threads landed 1600 rows for 200 records)."""
    path = resolve(LOCK, roots)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _FLIGHT, open(path, "a") as fh:
        flock.lock(fh)
        try:
            yield
        finally:
            flock.unlock(fh)


def collect(table: str = TABLE, roots: dict | None = None) -> int:
    """Move what waits in every holder's recorder into the table. Returns the rows added.
    Single-flight: a second collector waits, then finds the recorders already drained."""
    with _single_flight(roots):
        ensure_table(table)
        conn = store.connect()
        try:
            def sink(rows: list[dict]) -> None:
                for row in rows:
                    store.write(table, OWNER, row, conn=conn)
            return sum(metric.take(h, sink) for h in holders(roots))
        finally:
            conn.close()


def dedupe(table: str = TABLE) -> int:
    """Delete all but one of each set of rows equal in every column: the copies concurrent
    collects wrote before collect was single-flight (ticket a0016627c71e). A copy is not a
    measurement, so no history is lost (17.27.5). Returns the rows deleted."""
    if not re.fullmatch(r"[a-z0-9_]+", table):
        raise ValueError(f"not a table name: {table!r}")
    cols = ", ".join(f'"{c}"' for c in metric.COLUMNS)
    return store.delete(table, OWNER, where=(
        f'ctid IN (SELECT ctid FROM (SELECT ctid, row_number() OVER (PARTITION BY {cols} '
        f'ORDER BY ctid) AS rn FROM "{table}") d WHERE rn > 1)'))


def _where(name, source, since, until) -> tuple[list[str], list]:
    where, params = [], []
    for col, val in (("name", name), ("source", source)):
        if val:
            where.append(f"{col} = %s")
            params.append(val)
    if since:
        where.append("at >= %s")
        params.append(since)
    if until:
        where.append("at <= %s")
        params.append(until)
    return where, params


def report(table: str = TABLE, *, name: str | None = None, source: str | None = None,
           since: str | None = None, until: str | None = None, roots: dict | None = None) -> dict:
    """Collect, then answer the rows matching name / source / since / until, oldest first."""
    collected = collect(table, roots)
    where, params = _where(name, source, since, until)
    rows = store.read(table, where=(" AND ".join(where) + " ORDER BY at") if where else "true ORDER BY at",
                      params=tuple(params))
    return {"collected": collected,
            "rows": [{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in r.items()} for r in rows]}


def totals(table: str = TABLE, *, name: str | None = None, source: str | None = None,
           since: str | None = None, until: str | None = None, by: str | None = None,
           roots: dict | None = None) -> dict:
    """Collect, then answer one total per metric name (and per ``info[by]`` when ``by`` is given):
    ``count`` every matching row, ``sum`` their values (a row with no value counts but adds
    nothing). The table answers the sum, so a report over every call ever made stays small
    (outline 17.27.2: "so any metric can be reported fast")."""
    collected = collect(table, roots)
    where, params = _where(name, source, since, until)
    group, cols = "1", "name"
    if by:
        group, cols = "1, 2", 'name, info ->> %s AS "by"'
        params = [by] + params
    stmt = (f"SELECT {cols}, count(*) AS count, coalesce(sum(value), 0) AS sum FROM {{t}}"
            + (" WHERE " + " AND ".join(where) if where else "")
            + f" GROUP BY {group} ORDER BY {group}")
    rows = store.query(stmt, tables={"t": table}, params=tuple(params))
    return {"collected": collected,
            "totals": [dict(r, count=int(r["count"]), sum=float(r["sum"])) for r in rows]}
