"""One shot (ticket 98ab0e9db57f, outline 11.4.4): carry the proxy's old append-only table into
its two new homes, then drop it.

The table was both the compiled answers and the meter. The answers go to the proxy's keyed
answer tree (``domain.ANSWERS``): each distinct request's newest still-valid answer, deposited
under its digest exactly as ``resolve`` deposits a new one. The meter goes to metrics: every row
written before the live meter began (ticket 0615d8cdc998) records its spent, saved and latency
rows, ``info.migrated`` true and ``at`` the row's own time, so the all-time total is one sum
over the metrics table (Q#78, answered 2026-11-09). A call the live meter already recorded is
never counted twice.

THE DROP IS THE LAST THING AND IT IS EARNED. Nothing is dropped without a dump that exists and
names the table (taken by hand first: ``pg_dump -t inference_calls`` into
``~/.cairn/devices/inference_domain/0/temp/``), and nothing is dropped unless every expected
request is found in the tree afterwards. Any mismatch exits non-zero and drops nothing; a second
run over an already-dropped table writes nothing.

    python3 -m cairn.devices.inference_domain.migrate_answers_to_their_tree --dump <file>
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from cairn.devices.db_domain.tools.client import store
from cairn.devices.inference_domain import domain

SOURCE = "inference_calls"
SOURCE_COLUMNS = {
    "canonical": "text NOT NULL",
    "verdict": "text NOT NULL",
    "answer": "jsonb",
    "falsifier": "text",
    "horizon": "text",
    "provenance": "jsonb",
    "cost": "numeric",
    "created": "timestamptz NOT NULL DEFAULT now()",
}
BATCH = 1000


def carry(canonical: str, answer, *, table: str, meta: dict, domain_name: str | None = None,
          conn=None) -> dict:
    """One answer into the tree, through the same door ``resolve`` uses."""
    return domain.store_answer(canonical, answer, table=table, meta=meta, domain=domain_name,
                               conn=conn)


def _record(name: str, value, **kw) -> None:
    from cairn.tools.metric import metric
    metric.Metric(domain.metrics_holder(), domain._CHARTER,
                  source=domain.METRIC_SOURCE).record(name, value, **kw)


def _dump_names(dump, source: str) -> bool:
    if dump is None:
        return False
    p = Path(dump)
    if not p.is_file() or p.stat().st_size == 0:
        return False
    with open(p, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith(f"COPY public.{source} "):
                return True
    return False


def _key(canonical: str) -> str:
    """The request as resolve canonicalizes it today, so a carried answer sits under the digest
    resolve will ask for (a row stored under an older spelling would otherwise be unreachable)."""
    try:
        return domain.canonicalize(json.loads(canonical))
    except (json.JSONDecodeError, TypeError, AttributeError):
        return canonical


def _utc(when) -> datetime:
    if isinstance(when, str):
        when = datetime.fromisoformat(when)
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def _batches(template: str, source: str, conn):
    """Rows in created order, BATCH at a time, so 235 MB never sits in memory at once."""
    offset = 0
    while True:
        rows = store.query(template + " ORDER BY created, canonical LIMIT %s OFFSET %s",
                           tables={"t": source}, params=(BATCH, offset), conn=conn)
        if not rows:
            return
        yield from rows
        offset += len(rows)


def migrate(*, source: str = SOURCE, table: str = domain.ANSWERS, ask=None, record=None,
            dump=None, carry=carry, now: datetime | None = None) -> dict:
    """Carry, verify, meter, drop. Returns ``{"exit": 0|1|2, ...}``; only exit 0 dropped."""
    ask = ask or domain._ask_metrics
    record = record or _record
    now = now or datetime.now(timezone.utc)
    if store.owner_of(source) is None:
        return {"exit": 0, "source": "absent", "carried": 0, "metered": 0, "dropped": False}
    if not _dump_names(dump, source):
        return {"exit": 2, "refused": f"no dump naming {source} at {dump!r}: nothing written, "
                                      "nothing dropped", "dropped": False}
    conn = store.connect()
    try:
        domain.ensure_answers(table=table, conn=conn)
        # 1. which miss row is each request's newest still-valid answer (metadata only)
        newest: dict[str, tuple] = {}
        for r in _batches("SELECT canonical, horizon, created FROM {t} WHERE verdict = 'miss'",
                          source, conn):
            if not domain._valid(r.get("horizon") or "", now):
                continue
            k = _key(r["canonical"])
            if k not in newest or _utc(r["created"]) >= newest[k]:
                newest[k] = _utc(r["created"])
        # 2. carry those answers, skipping a request the tree already answers
        carried = skipped = 0
        for r in _batches("SELECT canonical, answer, horizon, falsifier, provenance, cost, created "
                          "FROM {t} WHERE verdict = 'miss'", source, conn):
            k = _key(r["canonical"])
            if newest.get(k) != _utc(r["created"]):
                continue
            newest[k] = None          # one carry per request, even if two rows share a time
            if domain._trees().find(domain.canonical_digest(k), table=table, conn=conn):
                skipped += 1
                continue
            prov = dict(r.get("provenance") or {})
            carry(k, r["answer"], table=table, conn=conn, domain_name=prov.get("domain"),
                  meta={"horizon": r.get("horizon") or "", "falsifier": r.get("falsifier") or "",
                        "cost": float(r.get("cost") or 0), "provenance": prov})
            carried += 1
        # 3. verify: every expected request is found in the tree
        missing = [k for k in newest
                   if not domain._trees().find(domain.canonical_digest(k), table=table, conn=conn)]
        if missing:
            return {"exit": 1, "expected": len(newest), "carried": carried, "skipped": skipped,
                    "missing": len(missing), "missing_sample": missing[:5], "dropped": False}
        # 4. meter the rows the live meter never saw, once
        rows = (ask({"source": domain.METRIC_SOURCE}) or {}).get("rows") or []
        mine = [m for m in rows if str(m.get("name") or "").startswith("inference.")]
        metered = 0
        if any((m.get("info") or {}).get("migrated") for m in mine):
            meter_note = "already metered"
        else:
            live = [_utc(m["at"]) for m in mine if m.get("at")]
            cutoff = min(live) if live else None
            for r in _batches("SELECT canonical, verdict, cost, created FROM {t}", source, conn):
                at = _utc(r["created"])
                if cutoff is not None and at >= cutoff:
                    continue
                v, cost = r["verdict"], float(r.get("cost") or 0)
                stamp = at.astimezone(timezone.utc).isoformat()
                kw = {"subject": f"migrated-{domain.canonical_digest(r['canonical'])[:12]}-{stamp}",
                      "start": stamp, "end": stamp, "at": stamp,
                      "info": {"verdict": v, "migrated": True}}
                record(domain.SPENT, cost if v == "miss" else 0.0, **kw)
                record(domain.SAVED, cost if v == "hit" else 0.0, **kw)
                record(domain.LATENCY, None, **kw)
                metered += 1
            meter_note = f"metered before {cutoff.isoformat() if cutoff else 'the end'}"
        # 5. drop, earned
        dropped = store.drop_table(source, domain.OWNER, conn=conn)
        return {"exit": 0 if dropped else 1, "expected": len(newest), "carried": carried,
                "skipped": skipped, "metered": metered, "meter": meter_note, "dropped": dropped}
    finally:
        conn.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dump", required=True, help="the pg_dump file of the old table")
    args = ap.parse_args(argv)
    report = migrate(dump=args.dump)
    print(json.dumps(report, indent=1, default=str))
    return int(report.get("exit") or 0)


if __name__ == "__main__":
    sys.exit(main())
