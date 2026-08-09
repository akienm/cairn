"""Proof: the does-a-domain-ride-the-request probe judges FIXTURE rows correctly and is armed.

The hollow build here is a probe that satisfies the emission gate's ARMED shape and then
judges nothing — a trigger that misses a real unmarked row, a clear that fires on a young
berth, or the coin-toss-green this watch was specified against: a clear BOUGHT by
default-stamping every row (the ticket's enough demands a NON-default vertical from a real
caller, and the all-general fixture below must NOT clear). Every row is a fixture; the live
corpus is the probe's own __main__ smoke-fire, a deliberate act.

    python3 cairn/inference_domain/proofs/test_watch_domain_probe.py     # exit 0 = green, no DB
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.inference_domain.probes import does_a_domain_ride_the_request as watch

_ERA = watch._ERA
_AFTER = _ERA + timedelta(hours=1)
_BEFORE = _ERA - timedelta(hours=1)


def _row(created: datetime, domain: str | None, kind: str = "generate",
         verdict: str = "miss") -> dict:
    prov = {"host": "http://hex.local:11434", "path": "/api/generate", "model": "qwen2.5:7b"}
    if domain is not None:
        prov["domain"] = domain
    return {"canonical": '{"kind":"%s","prompt":"x"}' % kind,
            "verdict": verdict, "provenance": prov, "created": created}


def test_the_probe_is_armed_in_the_emission_gates_shape():
    assert dataclasses.is_dataclass(watch.PROBE) and watch.PROBE.__dataclass_params__.frozen, \
        "the probe must be the frozen declaration, not a stateful worker"
    assert watch.PROBE.carry is not None and watch.PROBE.enough is not None, \
        "WATCHME's emission gate demands both a carry and an enough — absent either, unarmed"
    assert "vertical" in watch.PROBE.why, \
        "the why must carry the question this watch answers for"


def test_the_trigger_fires_on_one_unmarked_post_era_row():
    rows = [
        _row(_BEFORE, None),                       # pre-era: correctly unmarked, the old world
        _row(_AFTER, "general"),                   # marked: denominator only
        _row(_AFTER, "research", verdict="hit"),   # the marker rides hits too — jurisdiction, not exemption
        _row(_AFTER, None, kind="embed"),          # THE offender — all verbs are in jurisdiction
    ]
    s = watch.judge_rows(rows, default_name="general")
    assert s["post_era_rows"] == 3, s
    assert len(s["undomained"]) == 1 and s["undomained"][0]["canonical"], \
        "the offender must carry its row verbatim — the complete first report"
    assert watch._trigger(None, {"corpus": s}) is True, \
        "one unmarked post-era row IS the finding — the rule is EVERY row"
    assert watch._enough({"corpus": s}) is False, "a corpus with an offender never clears"


def test_the_clear_needs_the_denominator_and_a_real_vertical():
    marked = [_row(_AFTER + timedelta(minutes=i), "general") for i in range(11)]
    marked.append(_row(_AFTER + timedelta(minutes=30), "research"))
    s = watch.judge_rows(marked, default_name="general")
    assert s["post_era_rows"] == 12 and not s["undomained"]
    assert s["non_default_riding"] == ["research"], s
    assert watch._enough({"corpus": s}) is True, \
        "12 marked rows with a real non-default vertical is the ticket's own enough"
    assert watch._trigger(None, {"corpus": s}) is False


def test_all_default_rows_cannot_buy_the_clear():
    """The non-vacuity tooth (hypothesize falsifier): default-stamping every row satisfies
    the marker clause and MUST still not clear — only a real caller naming a real vertical
    can, because the seam never invents a non-default marker."""
    vacuous = [_row(_AFTER + timedelta(minutes=i), "general") for i in range(20)]
    s = watch.judge_rows(vacuous, default_name="general")
    assert s["post_era_rows"] == 20 and not s["undomained"] and not s["non_default_riding"]
    assert watch._enough({"corpus": s}) is False, \
        "an all-default corpus clearing would be coin-toss-green — machinery buying a clearance"


def test_a_young_berth_does_not_clear():
    young = [_row(_AFTER, "general"), _row(_AFTER, "research")]
    s = watch.judge_rows(young, default_name="general")
    assert not s["undomained"] and s["non_default_riding"] == ["research"]
    assert watch._enough({"corpus": s}) is False, \
        "two rows is a young berth, not evidence — the denominator floor holds"


def test_the_carry_reports_complete_on_first_pass():
    rows = [_row(_AFTER, None)]
    s = watch.judge_rows(rows, default_name="general")
    got = watch._carry({"corpus": s})
    assert got["counts"]["undomained"] == 1 and got["undomained"][0]["provenance"], \
        "the carry must deliver the offending rows verbatim, not a count to re-run for"
    assert "ticket" in got and "against_falsifier" in got and "suggests" in got, \
        "the finding rides with its ticket, its falsifier clause, and a suggestion — complete on first pass"


def test_dateless_or_naive_rows_never_count():
    naive = _row(_AFTER, None)
    naive["created"] = naive["created"].replace(tzinfo=None)
    s = watch.judge_rows([naive, _row(_AFTER, "general")], default_name="general")
    assert s["post_era_rows"] == 1 and not s["undomained"], \
        "a row that cannot be placed against the era is outside jurisdiction, not an offender"


def _main() -> int:
    checks = [
        test_the_probe_is_armed_in_the_emission_gates_shape,
        test_the_trigger_fires_on_one_unmarked_post_era_row,
        test_the_clear_needs_the_denominator_and_a_real_vertical,
        test_all_default_rows_cannot_buy_the_clear,
        test_a_young_berth_does_not_clear,
        test_the_carry_reports_complete_on_first_pass,
        test_dateless_or_naive_rows_never_count,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the watch fires on the first unmarked post-era row (any verb), clears only "
          "past the denominator floor AND a real non-default vertical (all-default cannot buy "
          "it), ignores the pre-domained era, and carries the complete report on first pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
