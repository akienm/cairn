#!/usr/bin/env python3
"""Proof: the cairn device holds the one metrics table and fills it when a consumer asks
(ticket 3721d82be75c, outline 17.27.2, 17.27.3, 17.27.5, 5.3.6).

Measured 2026-11-10: no metrics table existed; cairn.tools.metric (ticket 75de6bafbd95) records into
each holder's recorder and hands rows to whoever asks. The world is a temp roots table (two
holders' recorders), and the table is a store.scratch table owned by 'cairn', dropped at exit;
the live 'metrics' table is not touched.

  1. ensure_table gives the table every metric.COLUMNS column and two indexes, on (name, at) and
     (source, at), owned by 'cairn'; a second call changes nothing.
  2. records waiting under two holders stay out of the table until a report is asked for; the
     report moves every one in, with its name, source and value, and empties the recorders.
  3. a report filters by name and by source.
  4. a second report keeps the first report's rows (rows are kept forever).
  5. the cairn device's ``metrics`` verb answers a json-serialisable report.

    python3 cairn/devices/cairn/proofs/test_the_metrics_table_fills_when_asked.py
"""
from __future__ import annotations

import json
import sys
from cairn.tools.scratch.scratch import scratch_dir
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.devices.db_domain.tools.client import store

PROVES = {"3721d82be75c": {
    "1": "test_the_table_has_its_columns_and_indexes",
    "2": "test_a_report_picks_up_what_waits",
    "3": "test_a_report_filters",
    "4": "test_rows_are_kept",
    "5": "test_the_device_answers_the_verb",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _world():
    from cairn.tools.metric import metric
    tmp = scratch_dir("metrics_table_proof_")
    roots = {"repo": _REPO, "commons": tmp / "commons", "instance": tmp / "instance"}
    charter = tmp / "charter.json"
    charter.write_text(json.dumps({"metrics": {
        "spent": {"consumer": "the yield report (outline 11.4.4.2)", "unit": "tokens"},
        "latency": {"consumer": "the yield report (outline 11.4.4.2)", "unit": "s"}}}), encoding="utf-8")
    a = roots["instance"] / "devices" / "inference_domain" / "0"
    b = roots["instance"] / "devices" / "librarian" / "0"
    metric.Metric(a, charter, source="inference_domain").record("spent", 10.0, subject="call-1")
    metric.Metric(a, charter, source="inference_domain").record("latency", 0.5, subject="call-1")
    metric.Metric(b, charter, source="librarian").record("spent", 7.0)
    return roots, (a, b)


def _COLUMNS() -> dict:
    from cairn.tools.metric import metric
    return dict(metric.COLUMNS)


def _waiting(holders) -> int:
    from cairn.tools.metric import metric
    return sum(len(metric.recorder(h).read()) for h in holders)


def _cols(table):
    return {r["column_name"] for r in store.query(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %s",
        tables={}, params=(table,))}


def _indexdefs(table):
    return [r["indexdef"] for r in store.query(
        "SELECT indexdef FROM pg_indexes WHERE schemaname = 'public' AND tablename = %s",
        tables={}, params=(table,))]


def test_the_table_has_its_columns_and_indexes() -> None:
    from cairn.devices.cairn import metrics
    from cairn.tools.metric import metric
    t = store.scratch_name("mtab")
    try:
        metrics.ensure_table(t)
        metrics.ensure_table(t)
        lacks = [f"no column {c}" for c in metric.COLUMNS if c not in _cols(t)]
        defs = _indexdefs(t)
        for cols in ("(name, at)", "(source, at)"):
            if sum(1 for d in defs if cols in d) != 1:
                lacks.append(f"not exactly one index on {cols}: {defs}")
        if store.owner_of(t) != "cairn":
            lacks.append(f"owner {store.owner_of(t)!r}")
    finally:
        store.drop_table(t, "cairn")
    check("test_the_table_has_its_columns_and_indexes", not lacks, "; ".join(lacks))


def test_a_report_picks_up_what_waits() -> None:
    from cairn.devices.cairn import metrics
    roots, holders = _world()
    with store.scratch("cairn", "mtab", _COLUMNS()) as t:
        metrics.ensure_table(t)
        lacks = []
        if store.read(t):
            lacks.append("rows were in the table before anyone asked")
        out = metrics.report(t, roots=roots)
        got = sorted((r["name"], r["source"], r["value"]) for r in out["rows"])
        want = sorted([("spent", "inference_domain", 10.0), ("latency", "inference_domain", 0.5),
                       ("spent", "librarian", 7.0)])
        if got != want or out["collected"] != 3:
            lacks.append(f"report {got} collected {out['collected']}, wanted {want} / 3")
        if _waiting(holders):
            lacks.append(f"{_waiting(holders)} records still wait in the recorders")
    check("test_a_report_picks_up_what_waits", not lacks, "; ".join(lacks))


def test_a_report_filters() -> None:
    from cairn.devices.cairn import metrics
    roots, _ = _world()
    with store.scratch("cairn", "mtab", _COLUMNS()) as t:
        metrics.ensure_table(t)
        by_name = metrics.report(t, name="spent", roots=roots)["rows"]
        by_source = metrics.report(t, source="librarian", roots=roots)["rows"]
        lacks = []
        if sorted(r["source"] for r in by_name) != ["inference_domain", "librarian"] or any(r["name"] != "spent" for r in by_name):
            lacks.append(f"name filter: {by_name}")
        if [(r["name"], r["value"]) for r in by_source] != [("spent", 7.0)]:
            lacks.append(f"source filter: {by_source}")
    check("test_a_report_filters", not lacks, "; ".join(lacks))


def test_rows_are_kept() -> None:
    from cairn.devices.cairn import metrics
    roots, _ = _world()
    with store.scratch("cairn", "mtab", _COLUMNS()) as t:
        metrics.ensure_table(t)
        first = metrics.report(t, roots=roots)
        second = metrics.report(t, roots=roots)
        ok = len(first["rows"]) == 3 and len(second["rows"]) == 3 and second["collected"] == 0
        check("test_rows_are_kept", ok, f"first {len(first['rows'])}, second {len(second['rows'])} (collected {second['collected']})")


def test_the_device_answers_the_verb() -> None:
    from cairn.devices.cairn.device import CairnDevice
    roots, _ = _world()
    with store.scratch("cairn", "mtab", _COLUMNS()) as t:
        dev = CairnDevice(roots=roots, metrics_table=t)
        out = dev.declared_verbs()["metrics"]({"body": {"name": "latency"}})
        text = json.dumps(out)
        ok = [(r["name"], r["value"]) for r in out.get("rows", [])] == [("latency", 0.5)]
        check("test_the_device_answers_the_verb", ok, text[:300])


def main() -> int:
    for tooth in (test_the_table_has_its_columns_and_indexes, test_a_report_picks_up_what_waits,
                  test_a_report_filters, test_rows_are_kept, test_the_device_answers_the_verb):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
