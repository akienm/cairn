"""Proof: the does-the-route-leave-loopback probe judges FIXTURE rows correctly and is armed.

The hollow build here is a probe that exists, satisfies the emission gate's ARMED shape, and
then judges nothing — a trigger that never fires on a real offender, a clear that fires on a
young berth, an era floor that counts the pre-routed world against the ruled NEVER. Every row
below is a fixture; the live corpus is the probe's own __main__ smoke-fire, a deliberate act.

    python3 cairn/devices/inference_domain/proofs/test_watch_probe.py     # exit 0 = green, no DB
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.inference_domain.probes import does_the_route_leave_loopback as watch

_ERA = watch._ERA
_AFTER = _ERA + timedelta(hours=1)
_BEFORE = _ERA - timedelta(hours=1)


def _row(created: datetime, host: str, kind: str = "generate", verdict: str = "miss",
         provider: str | None = None) -> dict:
    prov = {"host": host, "path": "/api/generate", "model": "qwen2.5:7b"}
    if provider:
        prov["provider"] = provider
    return {"canonical": '{"kind":"%s","prompt":"x"}' % kind,
            "verdict": verdict, "provenance": prov, "created": created}


def test_the_probe_is_armed_in_the_emission_gates_shape():
    assert dataclasses.is_dataclass(watch.PROBE) and watch.PROBE.__dataclass_params__.frozen, \
        "the probe must be the frozen declaration, not a stateful worker"
    assert watch.PROBE.carry is not None and watch.PROBE.enough is not None, \
        "WATCHME's emission gate demands both a carry and an enough — absent either, unarmed"
    assert "NEVER" in watch.PROBE.why.upper() or "never" in watch.PROBE.why, \
        "the why must carry the ruled rule this watch answers for"


def test_an_offender_is_exactly_a_post_era_loopback_generate_miss():
    rows = [
        _row(_BEFORE, "http://127.0.0.1:11434"),                    # pre-era: the old world, not a finding
        _row(_AFTER, "http://hex.local:11434", provider="hex"),     # the ruled route: denominator only
        _row(_AFTER, "http://127.0.0.1:11434", kind="embed"),       # embed: outside this watch's question
        _row(_AFTER, "http://localhost:11434", verdict="hit"),      # a hit spent nothing: not a miss
        _row(_AFTER, "http://127.0.0.1:11434"),                     # THE offender
    ]
    s = watch.judge_rows(rows)
    assert s["post_era_generate_misses"] == 2, s   # hex row + the offender
    assert len(s["loopback_offenders"]) == 1, s
    off = s["loopback_offenders"][0]
    assert "127.0.0.1" in off["provenance"]["host"] and off["canonical"], \
        "the offender must carry its row verbatim — the complete first report"


def test_the_trigger_fires_on_one_offender_because_the_rule_is_never():
    corpus = watch.judge_rows([_row(_AFTER, "http://127.0.0.1:11434")])
    assert watch._trigger(None, {"corpus": corpus}) is True, \
        "one loopback generate IS the finding — NEVER has no accumulation floor"
    assert watch._enough({"corpus": corpus}) is False


def test_the_clear_needs_the_denominator_floor_not_just_zero():
    young = watch.judge_rows([_row(_AFTER, "http://hex.local:11434", provider="hex")
                              for _ in range(3)])
    assert watch._trigger(None, {"corpus": young}) is False
    assert watch._enough({"corpus": young}) is False, \
        "zero-of-three is a young berth, not the route proven leaving loopback"
    seasoned = watch.judge_rows([_row(_AFTER + timedelta(minutes=i), "http://hex.local:11434",
                                      provider="hex") for i in range(watch._ENOUGH)])
    assert watch._enough({"corpus": seasoned}) is True and \
        watch._trigger(None, {"corpus": seasoned}) is False, \
        "zero offenders across the floor clears the watch — the pair shares one variable"


def test_the_carry_reports_complete_on_first_pass():
    corpus = watch.judge_rows([_row(_AFTER, "http://127.0.0.1:11434"),
                               _row(_AFTER, "http://hex.local:11434", provider="hex")])
    carried = watch._carry({"corpus": corpus})
    assert carried["counts"] == {"post_era_generate_misses": 2, "loopback_offenders": 1}
    assert len(carried["offenders"]) == 1 and len(carried["todays_shake"]) == 1, \
        "every offender rides the carry with today's shake beside it (or its loud unavailability)"
    assert "ticket" in carried and "suggests" in carried, \
        "the receiver gets the ticket address and a next move, not homework"


def _main() -> int:
    checks = [
        test_the_probe_is_armed_in_the_emission_gates_shape,
        test_an_offender_is_exactly_a_post_era_loopback_generate_miss,
        test_the_trigger_fires_on_one_offender_because_the_rule_is_never,
        test_the_clear_needs_the_denominator_floor_not_just_zero,
        test_the_carry_reports_complete_on_first_pass,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the watch fires on the first post-era loopback generate (the rule is "
          "NEVER), clears only past the denominator floor, ignores the pre-routed era, "
          "embeds, and hits, and carries the complete report on first pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
