#!/usr/bin/env python3
"""Proof: a metric records into its holder's recorder, refuses an undeclared name, and hands
rows in the one table's shape to whoever asks (ticket 75de6bafbd95, outline 17.27).

Measured 2026-11-10: no metric tool existed; outline 17.27 defines one, and Akien's answer to
Q#78 makes the inference proxy's spent, saved and latency metrics. Every tooth runs over a
scratch holder directory and a scratch charter; nothing in ~/.cairn is touched.

  1. a declared name lands in <holder>/tools/data_recorder/metrics/ with its name, source,
     value, subject, info and the charter's unit; metric.py imports no bus and no database.
  2. an undeclared name, and one declared with a blank consumer, raise UndeclaredMetric naming
     the name, and nothing is written.
  3. take hands the sink rows with exactly the COLUMNS keys, then clears them; a sink that
     raises leaves every record in place.
  4. after a write, the recorder's reading.json declares the read frequency and on_read drain.

    python3 cairn/tools/metric/proofs/test_metric.py
"""
from __future__ import annotations

import ast
import json
import sys
from cairn.tools.scratch.scratch import scratch_dir
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"75de6bafbd95": {
    "1": "test_a_declared_name_lands_in_the_holders_recorder",
    "2": "test_an_undeclared_name_writes_nothing",
    "3": "test_take_hands_rows_and_clears_only_after",
    "4": "test_the_read_frequency_is_declared",
}}

FAILURES: list[str] = []
_TOOL = _REPO / "cairn" / "tools" / "metric" / "metric.py"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _scratch():
    tmp = scratch_dir("metric_proof_")
    charter = tmp / "intention+why.json"
    charter.write_text(json.dumps({"metrics": {
        "spent": {"consumer": "the yield report (outline 11.4.4.2)", "unit": "tokens"},
        "orphan": {"consumer": "  ", "unit": "s"},
    }}), encoding="utf-8")
    return tmp / "holder", charter


def _records(holder: Path) -> list[dict]:
    f = holder / "tools" / "data_recorder" / "metrics" / "records.jsonl"
    if not f.is_file():
        return []
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_a_declared_name_lands_in_the_holders_recorder() -> None:
    from cairn.tools.metric import metric
    holder, charter = _scratch()
    m = metric.Metric(holder, charter, source="inference_domain")
    m.record("spent", 412.0, subject="call-7", info={"model": "m"})
    recs = _records(holder)
    lacks = []
    if len(recs) != 1:
        lacks.append(f"{len(recs)} records, wanted 1")
    else:
        r = recs[0]
        want = {"finding": "spent", "probe_source": "inference_domain", "value": 412.0,
                "unit": "tokens", "subject": "call-7", "info": {"model": "m"}}
        lacks += [f"{k}={r.get(k)!r}, wanted {v!r}" for k, v in want.items() if r.get(k) != v]
    tree = ast.parse(_TOOL.read_text(encoding="utf-8"))
    mods = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    mods += [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    lacks += [f"metric.py imports {x}" for x in mods
              if x.startswith(("cairn.devices", "psycopg2")) or "bus" in x.split(".")]
    check("test_a_declared_name_lands_in_the_holders_recorder", not lacks, "; ".join(lacks))


def test_an_undeclared_name_writes_nothing() -> None:
    from cairn.tools.metric import metric
    holder, charter = _scratch()
    m = metric.Metric(holder, charter, source="x")
    lacks = []
    for name in ("never_declared", "orphan"):
        try:
            m.record(name, 1.0)
            lacks.append(f"{name} was recorded")
        except metric.UndeclaredMetric as exc:
            if name not in str(exc):
                lacks.append(f"the refusal does not name {name}: {exc}")
    if _records(holder):
        lacks.append("a refused name left a record")
    check("test_an_undeclared_name_writes_nothing", not lacks, "; ".join(lacks))


def test_take_hands_rows_and_clears_only_after() -> None:
    from cairn.tools.metric import metric
    holder, charter = _scratch()
    m = metric.Metric(holder, charter, source="s")
    m.record("spent", 1.0)
    m.record("spent", 2.0, subject="b")
    lacks = []

    def boom(rows):
        raise RuntimeError("the table is down")
    try:
        metric.take(holder, boom)
        lacks.append("a raising sink did not propagate")
    except RuntimeError:
        pass
    if len(_records(holder)) != 2:
        lacks.append(f"a raising sink cleared records ({len(_records(holder))} left of 2)")

    got: list[dict] = []
    seen_before_clear: list[int] = []

    def sink(rows):
        seen_before_clear.append(len(_records(holder)))
        got.extend(rows)
    n = metric.take(holder, sink)
    if n != 2 or len(got) != 2:
        lacks.append(f"take handed {n} / {len(got)} rows, wanted 2")
    if seen_before_clear != [2]:
        lacks.append(f"records were cleared before the sink returned: {seen_before_clear}")
    keys = {tuple(sorted(r)) for r in got}
    if keys != {tuple(sorted(metric.COLUMNS))}:
        lacks.append(f"row keys {keys} are not COLUMNS {sorted(metric.COLUMNS)}")
    if got and [r["value"] for r in got] != [1.0, 2.0]:
        lacks.append(f"values {[r['value'] for r in got]}")
    if _records(holder):
        lacks.append("records left after a sink that returned")
    check("test_take_hands_rows_and_clears_only_after", not lacks, "; ".join(lacks))


def test_the_read_frequency_is_declared() -> None:
    from cairn.tools.metric import metric
    holder, charter = _scratch()
    metric.Metric(holder, charter, source="s").record("spent", 1.0)
    f = holder / "tools" / "data_recorder" / "metrics" / "reading.json"
    reading = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    ok = isinstance(reading.get("expected_read_frequency_seconds"), int) and reading.get("on_read") == "drain"
    check("test_the_read_frequency_is_declared", ok, json.dumps(reading))


def main() -> int:
    for tooth in (test_a_declared_name_lands_in_the_holders_recorder, test_an_undeclared_name_writes_nothing,
                  test_take_hands_rows_and_clears_only_after, test_the_read_frequency_is_declared):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
