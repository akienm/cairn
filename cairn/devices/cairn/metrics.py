"""cairn/devices/cairn/metrics.py — the one metrics table, held by the cairn device (outline 17.27).

The cairn device holds the metrics table until Recovery exists (5.3.6, 6.6.3.4). Every source
records into its own holder's recorder through cairn.tools.metric (17.27.1); this module is the
table's side: it creates the table through db_domain's store, owned by 'cairn', indexed on name
and source by time (17.27.2), and when a consumer asks for a report it first picks up what waits
in every holder's recorder (17.27.3 — the read is the event; nothing polls). Rows are never
deleted here (17.27.5): the table is the history.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from cairn.devices.db_domain.tools.client import store
from cairn.tools.base.address import resolve
from cairn.tools.metric import metric

TABLE = "metrics"
OWNER = "cairn"
INDEXES = {"name_at": ["name", "at"], "source_at": ["source", "at"]}


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


def collect(table: str = TABLE, roots: dict | None = None) -> int:
    """Move what waits in every holder's recorder into the table. Returns the rows added."""
    ensure_table(table)
    conn = store.connect()
    try:
        def sink(rows: list[dict]) -> None:
            for row in rows:
                store.write(table, OWNER, row, conn=conn)
        return sum(metric.take(h, sink) for h in holders(roots))
    finally:
        conn.close()


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
