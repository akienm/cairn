#!/usr/bin/env python3
"""Proof for ticket a0016627c71e — concurrent collects land each record once.

Measured 2026-11-10: eight threads calling metrics.collect over one holder with 200 waiting
records landed 1600 rows, three trials of three; the live metrics table held 519 inference rows
for 66 calls. Each collect read the whole recorder before any cleared it. collect is now
single-flight, across threads and processes, and a one-shot dedupe removes the copies the race
already wrote.

One tooth per numbered falsifier clause:

  1. eight threads collecting one holder's 200 waiting records into a fresh table land exactly
     200 rows, none raising, and leave the recorder empty.
  2. two processes collecting one holder's 300 waiting records at once land exactly 300 rows.
  3. dedupe deletes all but one of each set of rows equal in every column, leaves rows that
     differ in any column, and a second run deletes nothing.
  4. the cairn device's charter says collect is single-flight.

The worlds are temp roots; every table is a store.scratch table owned by 'cairn', dropped at exit.
The live metrics table is not touched.

    python3 cairn/devices/cairn/proofs/test_concurrent_collects_land_each_record_once.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from cairn.tools.scratch.scratch import scratch_dir
import threading
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.devices.db_domain.tools.client import store

PROVES = {"a0016627c71e": {
    "1": "eight_threads_land_each_record_once",
    "2": "two_processes_land_each_record_once",
    "3": "dedupe_keeps_one_of_each",
    "4": "the_charter_says_collect_is_single_flight",
}}

CHARTER = _REPO / "cairn" / "devices" / "cairn" / "intention+why.json"
PASS = 0
FAIL = 0


def _world(n: int):
    """A temp roots with one holder whose recorder waits with n spent records."""
    from cairn.tools.metric import metric
    tmp = scratch_dir("metrics_single_flight_proof_")
    roots = {"repo": _REPO, "commons": tmp / "commons", "instance": tmp / "instance"}
    charter = tmp / "charter.json"
    charter.write_text(json.dumps({"metrics": {"spent": {
        "consumer": "testing: the single-flight proof", "unit": "tokens"}}}), encoding="utf-8")
    holder = roots["instance"] / "devices" / "inference_domain" / "0"
    m = metric.Metric(holder, charter, source="inference_domain")
    for i in range(n):
        m.record("spent", float(i), at="2026-01-01T00:00:00+00:00", subject=f"testing-{i}")
    return roots, holder, tmp


def _count(table: str) -> int:
    return store.query("SELECT count(*) AS n FROM {t}", tables={"t": table}, params=())[0]["n"]


def eight_threads_land_each_record_once():
    from cairn.devices.cairn import metrics
    from cairn.tools.metric import metric
    roots, holder, _ = _world(200)
    errors: list[str] = []

    def run(table):
        try:
            metrics.collect(table, roots)
        except Exception as exc:  # noqa: BLE001 — counted, then asserted
            errors.append(f"{type(exc).__name__}: {exc}")
    with store.scratch("cairn", "mcthreads", metric.COLUMNS) as table:
        ths = [threading.Thread(target=run, args=(table,)) for _ in range(8)]
        for t in ths:
            t.start()
        for t in ths:
            t.join()
        n = _count(table)
    assert not errors, f"{len(errors)} collects raised, first: {errors[0]}"
    assert n == 200, f"{n} rows landed for 200 records"
    assert metric.recorder(holder).read() == [], "the recorder still holds records"


_CHILD = """
import json, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from cairn.devices.cairn import metrics
roots = {k: Path(v) for k, v in json.loads(sys.argv[2]).items()}
go = Path(sys.argv[4])
while not go.exists():
    time.sleep(0.001)
print(metrics.collect(sys.argv[3], roots))
"""


def two_processes_land_each_record_once():
    from cairn.devices.cairn import metrics
    from cairn.tools.metric import metric
    roots, _, tmp = _world(300)
    go = tmp / "go"
    with store.scratch("cairn", "mcprocs", metric.COLUMNS) as table:
        metrics.ensure_table(table)
        args = [str(_REPO), json.dumps({k: str(v) for k, v in roots.items()}), table, str(go)]
        kids = [subprocess.Popen([sys.executable, "-c", _CHILD, *args], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True) for _ in range(2)]
        time.sleep(3)  # both children imported and waiting on the go file
        go.write_text("go")
        outs = [k.communicate(timeout=120) for k in kids]
        n = _count(table)
    for k, (out, err) in zip(kids, outs):
        assert k.returncode == 0, f"a collecting process failed: {err[-400:]}"
    assert n == 300, f"{n} rows landed for 300 records (each process said {[o.strip() for o, _ in outs]})"


def dedupe_keeps_one_of_each():
    from cairn.devices.cairn import metrics
    from cairn.tools.metric import metric
    base = {"at": "2026-01-01T00:00:00+00:00", "name": "inference.spent", "source": "testing",
            "start": None, "end": None, "unit": "tokens", "subject": "testing-a", "value": 3.0,
            "info": {"verdict": "miss"}}
    rows = [dict(base), dict(base), dict(base),                       # three copies of one row
            dict(base, subject="testing-b"),                           # differs by subject
            dict(base, info={"verdict": "hit"}),           # differs by info
            dict(base, info={"verdict": "hit"}),           # ... and its one copy
            dict(base, value=4.0)]                                     # differs by value
    with store.scratch("cairn", "mcdedupe", metric.COLUMNS) as table:
        for r in rows:
            store.write(table, "cairn", r)
        first = metrics.dedupe(table)
        left = _count(table)
        second = metrics.dedupe(table)
    assert first == 3, f"the first dedupe deleted {first}, not 3"
    assert left == 4, f"{left} rows left, not 4"
    assert second == 0, f"the second dedupe deleted {second}"


def the_charter_says_collect_is_single_flight():
    what = json.loads(CHARTER.read_text())["what"]
    assert "single-flight" in what, "the cairn charter's what does not say collect is single-flight"


TEETH = [eight_threads_land_each_record_once,
         two_processes_land_each_record_once,
         dedupe_keeps_one_of_each,
         the_charter_says_collect_is_single_flight]

if __name__ == "__main__":
    for fn in TEETH:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
            FAIL += 1
            print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
        else:
            PASS += 1
            print(f"  green {fn.__name__}")
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
