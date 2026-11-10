"""Proof for ticket 0615d8cdc998 — the inference proxy records its meter as metrics.

Outline 11.4.4.2 (Akien 2026-11-09, answering Q#78): the yield report reads the metrics table
(17.27); "each call records its spent, saved and latency rows under the call as subject, kept
forever, so the all-time total is a sum." This proof measures the RECORDING half: what one call
leaves in the device's own metrics recorder (17.27.1), read off disk through the metric tool.

One tooth per numbered falsifier clause:

  1. A MISS records three rows under the call's task ticket id: inference.spent = the cost the
     resolver reported, inference.saved = 0, inference.latency = the ticket's elapsed_ms; the
     source is inference_domain and the units are tokens, tokens, ms.
  2. A HIT of the same request records inference.saved = the stored cost and inference.spent = 0,
     and a REFUSED call records spent 0 and saved 0 with its latency; every call's three rows
     share one subject and no two calls share it.
  3. The three names are declared in the device's charter, each with a consumer naming the yield
     report (11.4.4.2), and the records land under the trail's roots, never the live tree.

Requires the db_domain provisioning; the cache table is scratch, dropped on the way out.

    bin/cairn test cairn/devices/inference_domain/proofs/test_the_proxy_records_its_meter_as_metrics.py
"""

from __future__ import annotations

import contextlib
import json
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import address
from cairn.tools.scratch.scratch import scratch_dir

PROVES = {"0615d8cdc998": {
    "1": "a_miss_records_spent_saved_and_latency_under_the_call",
    "2": "a_hit_saves_and_a_refusal_spends_nothing",
    "3": "the_names_are_declared_and_land_under_the_trails_roots",
}}

NAMES = ("inference.spent", "inference.saved", "inference.latency")
CHARTER = _REPO_ROOT / "cairn" / "devices" / "inference_domain" / "intention+why.json"
_RUN = uuid.uuid4().hex[:8]
_SCRATCH = contextlib.ExitStack()
_HELD: list[str] = []

PASS = 0
FAIL = 0


def _domain():
    from cairn.devices.inference_domain import domain
    return domain


def _table() -> str:
    if not _HELD:
        _HELD.append(_SCRATCH.enter_context(_domain().scratch_cache("metered")))
    return _HELD[0]


class _Resolver:
    def __init__(self, cost: float = 7.0):
        self.cost = cost

    def __call__(self, request: dict) -> dict:
        return {"answer": {"text": "an answer"}, "cost": self.cost,
                "provenance": {"host": "http://testing.invalid", "model": "testing-model"}}


class _Refusing:
    def __call__(self, request: dict) -> dict:
        raise RuntimeError("testing: the host refused")


@contextlib.contextmanager
def _isolated():
    tmp = scratch_dir("testing-0615d8cdc998-")
    domain = _domain()
    domain.set_diagnostic_roots({**address.ROOTS, "instance": tmp})
    try:
        yield tmp
    finally:
        domain.set_diagnostic_roots(None)


def _records(tmp: Path) -> list[dict]:
    from cairn.tools.metric import metric
    return metric.recorder(tmp / "devices" / "inference_domain" / "0").read()


def _by_subject(records: list[dict]) -> dict:
    out: dict = {}
    for r in records:
        out.setdefault(r["subject"], {})[r["finding"]] = r
    return out


def _ticket_id(result_or_path) -> str:
    return Path(result_or_path).stem


def a_miss_records_spent_saved_and_latency_under_the_call():
    domain = _domain()
    with _isolated() as tmp:
        out = domain.resolve({"q": f"miss_{_RUN}"}, resolver=_Resolver(7.0), table=_table())
        assert out.get("ticket"), f"the call wrote no task ticket: {out}"
        tid = _ticket_id(out["ticket"])
        ticket = json.loads(Path(out["ticket"]).read_text(encoding="utf-8"))
        rows = _by_subject(_records(tmp))
        assert list(rows) == [tid], f"subjects recorded {list(rows)}, expected only the call {tid}"
        got = rows[tid]
        assert sorted(got) == sorted(NAMES), f"names recorded {sorted(got)}"
        assert got["inference.spent"]["value"] == 7.0, got["inference.spent"]
        assert got["inference.saved"]["value"] == 0.0, got["inference.saved"]
        assert got["inference.latency"]["value"] == ticket["timings"]["elapsed_ms"], (
            got["inference.latency"], ticket["timings"])
        assert {r["probe_source"] for r in got.values()} == {"inference_domain"}
        assert [got[n]["unit"] for n in NAMES] == ["tokens", "tokens", "ms"], [got[n]["unit"] for n in NAMES]


def a_hit_saves_and_a_refusal_spends_nothing():
    domain = _domain()
    with _isolated() as tmp:
        ask = {"q": f"hit_{_RUN}"}
        first = domain.resolve(dict(ask), resolver=_Resolver(5.0), table=_table())
        hit = domain.resolve(dict(ask), resolver=_Resolver(99.0), table=_table())
        assert hit["hit"], f"the second call was not a hit: {hit}"
        try:
            domain.resolve({"q": f"refused_{_RUN}"}, resolver=_Refusing(), table=_table())
        except RuntimeError as refusal:
            refused_id = _ticket_id(getattr(refusal, "task_ticket", "") or "missing")
        else:
            raise AssertionError("the refusing resolver did not raise")
        rows = _by_subject(_records(tmp))
        ids = [_ticket_id(first["ticket"]), _ticket_id(hit["ticket"]), refused_id]
        assert sorted(rows) == sorted(ids) and len(set(ids)) == 3, (sorted(rows), ids)
        h = rows[ids[1]]
        assert (h["inference.saved"]["value"], h["inference.spent"]["value"]) == (5.0, 0.0), h
        r = rows[ids[2]]
        assert (r["inference.spent"]["value"], r["inference.saved"]["value"]) == (0.0, 0.0), r
        assert isinstance(r["inference.latency"]["value"], float), r["inference.latency"]
        assert {x["info"]["verdict"] for x in r.values()} == {"refused"}, r


def the_names_are_declared_and_land_under_the_trails_roots():
    from cairn.tools.metric import metric
    declared = metric.declared(CHARTER)
    for name in NAMES:
        spec = declared.get(name) or {}
        assert "yield report" in str(spec.get("consumer") or ""), f"{name} declared as {spec!r}"
    domain = _domain()
    with _isolated() as tmp:
        assert domain.metrics_holder() == tmp / "devices" / "inference_domain" / "0"
    assert domain.metrics_holder() == address.instance_path("inference_domain", 0)


TEETH = [a_miss_records_spent_saved_and_latency_under_the_call,
         a_hit_saves_and_a_refusal_spends_nothing,
         the_names_are_declared_and_land_under_the_trails_roots]

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
        _SCRATCH.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
