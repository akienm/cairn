#!/usr/bin/env python3
"""Proof: the cairn device's metrics verb answers totals (ticket f4dbcea5a117, outline 17.27.2:
"so any metric can be reported fast"; 11.4.4.2: "the all-time total is a sum").

Measured 2026-11-10: the metrics verb (ticket 3721d82be75c) answers only raw rows, and the proxy's
22,156 migrated calls would make every yield report carry ~66k rows (~23 MB). The world is a
temp roots table (one holder's recorder), and the table is a store.scratch table owned by
'cairn', dropped at exit; the live 'metrics' table is not touched.

  1. totals answers one total per name: count is every matching row, a row with no value
     included; sum adds the values, a valueless row adding nothing.
  2. totals with by="verdict" answers one total per name and info.verdict.
  3. since and until bound the totals, and report honors until.
  4. the cairn device's metrics verb, with totals true in its body, answers json-serialisable
     totals grouped by the body's by.

    python3 cairn/devices/cairn/proofs/test_the_metrics_verb_answers_totals.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.devices.db_domain.tools.client import store

PROVES = {"f4dbcea5a117": {
    "1": "test_totals_count_and_sum_per_name",
    "2": "test_totals_split_by_an_info_key",
    "3": "test_since_and_until_bound_the_answer",
    "4": "test_the_device_answers_totals",
}}

FAILURES: list[str] = []
T1, T2, T3 = "2026-01-01T00:00:00+00:00", "2026-02-01T00:00:00+00:00", "2026-03-01T00:00:00+00:00"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _world():
    """Three calls at three times: a miss (spent 10), a hit (saved 4), a miss (spent 6); each
    with a valueless latency row carrying its verdict."""
    from cairn.tools.metric import metric
    tmp = Path(tempfile.mkdtemp(prefix="metrics_totals_proof_"))
    roots = {"repo": _REPO, "commons": tmp / "commons", "instance": tmp / "instance"}
    charter = tmp / "charter.json"
    charter.write_text(json.dumps({"metrics": {
        n: {"consumer": "the yield report (outline 11.4.4.2)", "unit": "tokens"}
        for n in ("spent", "saved", "latency")}}), encoding="utf-8")
    m = metric.Metric(roots["instance"] / "devices" / "inference_domain" / "0", charter,
                      source="inference_domain")
    for at, verdict, spent, saved in ((T1, "miss", 10.0, 0.0), (T2, "hit", 0.0, 4.0),
                                      (T3, "miss", 6.0, 0.0)):
        kw = {"at": at, "info": {"verdict": verdict}}
        m.record("spent", spent, **kw)
        m.record("saved", saved, **kw)
        m.record("latency", None, **kw)
    return roots


def _COLUMNS() -> dict:
    from cairn.tools.metric import metric
    return dict(metric.COLUMNS)


def _by_name(out) -> dict:
    return {r["name"]: (r["count"], r["sum"]) for r in out.get("totals", [])}


def test_totals_count_and_sum_per_name() -> None:
    from cairn.devices.cairn import metrics
    roots = _world()
    with store.scratch("cairn", "mtot", _COLUMNS()) as t:
        out = metrics.totals(t, roots=roots)
        got = _by_name(out)
        want = {"spent": (3, 16.0), "saved": (3, 4.0), "latency": (3, 0.0)}
        check("test_totals_count_and_sum_per_name", got == want and out.get("collected") == 9,
              f"got {got} collected {out.get('collected')}, wanted {want} / 9")


def test_totals_split_by_an_info_key() -> None:
    from cairn.devices.cairn import metrics
    roots = _world()
    with store.scratch("cairn", "mtot", _COLUMNS()) as t:
        out = metrics.totals(t, by="verdict", roots=roots)
        got = {(r["name"], r["by"]): (r["count"], r["sum"]) for r in out.get("totals", [])}
        want = {("spent", "miss"): (2, 16.0), ("spent", "hit"): (1, 0.0),
                ("saved", "miss"): (2, 0.0), ("saved", "hit"): (1, 4.0),
                ("latency", "miss"): (2, 0.0), ("latency", "hit"): (1, 0.0)}
        check("test_totals_split_by_an_info_key", got == want, f"got {got}")


def test_since_and_until_bound_the_answer() -> None:
    from cairn.devices.cairn import metrics
    roots = _world()
    with store.scratch("cairn", "mtot", _COLUMNS()) as t:
        lacks = []
        upto = _by_name(metrics.totals(t, name="spent", until=T2, roots=roots))
        if upto != {"spent": (2, 10.0)}:
            lacks.append(f"until {T2}: {upto}")
        after = _by_name(metrics.totals(t, name="spent", since=T2, roots=roots))
        if after != {"spent": (2, 6.0)}:
            lacks.append(f"since {T2}: {after}")
        mid = _by_name(metrics.totals(t, name="spent", since=T2, until=T2, roots=roots))
        if mid != {"spent": (1, 0.0)}:
            lacks.append(f"since=until={T2}: {mid}")
        rows = metrics.report(t, name="spent", until=T2, roots=roots)["rows"]
        if [r["value"] for r in rows] != [10.0, 0.0]:
            lacks.append(f"report until {T2}: {[r['value'] for r in rows]}")
        check("test_since_and_until_bound_the_answer", not lacks, "; ".join(lacks))


def test_the_device_answers_totals() -> None:
    from cairn.devices.cairn.device import CairnDevice
    roots = _world()
    with store.scratch("cairn", "mtot", _COLUMNS()) as t:
        dev = CairnDevice(roots=roots, metrics_table=t)
        out = dev.declared_verbs()["metrics"]({"body": {"totals": True, "by": "verdict",
                                                         "source": "inference_domain"}})
        text = json.dumps(out)
        got = {(r["name"], r["by"]): r["count"] for r in out.get("totals", [])}
        ok = "rows" not in out and got.get(("latency", "miss")) == 2 and got.get(("latency", "hit")) == 1
        check("test_the_device_answers_totals", ok, text[:300])


def main() -> int:
    for tooth in (test_totals_count_and_sum_per_name, test_totals_split_by_an_info_key,
                  test_since_and_until_bound_the_answer, test_the_device_answers_totals):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
