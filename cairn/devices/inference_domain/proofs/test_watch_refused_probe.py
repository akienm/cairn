"""Proof: the a-refused-ask-leaves-a-row probe judges FIXTURE rows correctly and is armed.

The hollow build here is a probe that satisfies the emission gate's ARMED shape and then
judges nothing — a trigger that misses a refusal replayed as an answer, or the coin-toss-green
this watch was specified against: a clear BOUGHT by a corpus that has never recorded a single
refusal. That corpus is the SILENT one, and silence is what the old defect looked like; a watch
that clears on it would be certifying the exact state it exists to detect. The ticket's own
enough says so, and `test_a_corpus_with_no_refusal_cannot_buy_the_clear` is that sentence with
teeth.

Every row here is a fixture, judged by the probe's pure `judge_rows`; the live corpus is the
probe's own __main__ smoke-fire, a deliberate act. A fixture that agrees only with this
reader would be worthless, so the row shape is taken from the REAL writer — and the real
writer's output is fed to this same judge, over a live store, by
`test_the_watch_reads_a_row_the_real_writer_made` in test_inference_domain.py.

    python3 cairn/devices/inference_domain/proofs/test_watch_refused_probe.py   # exit 0 = green, no DB
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.inference_domain.probes import a_refused_ask_leaves_a_row as watch

_ERA = watch._ERA
_AFTER = _ERA + timedelta(hours=1)
_BEFORE = _ERA - timedelta(hours=1)


def _answered(created: datetime, *, verdict: str = "miss", cost: float = 42.0,
              answer: dict | None = None) -> dict:
    """An ordinary answered row, shaped as domain.resolve() writes one."""
    return {"canonical": '{"kind":"generate","prompt":"x"}', "verdict": verdict,
            "answer": {"text": "hello"} if answer is None else answer,
            "cost": cost, "created": created,
            "provenance": {"host": "http://hex.local:11434", "path": "/api/generate",
                           "domain": "general"}}


def _refused(created: datetime, *, refused: str | None = "HostUnreachable",
             cost: float = 0.0, answer=None) -> dict:
    """A refused row, shaped as domain.resolve()'s except clause writes one: no answer, no
    cost, and a provenance carrying the domain plus what refused it and its words. No
    host/path — the resolver raised before it returned a provenance."""
    prov = {"domain": "general", "detail": "the dial failed"}
    if refused is not None:
        prov["refused"] = refused
    return {"canonical": '{"kind":"generate","prompt":"x"}', "verdict": "refused",
            "answer": answer, "cost": cost, "created": created, "provenance": prov}


def test_the_probe_is_armed_in_the_emission_gates_shape():
    assert dataclasses.is_dataclass(watch.PROBE) and watch.PROBE.__dataclass_params__.frozen, \
        "the probe must be the frozen declaration, not a stateful worker"
    assert watch.PROBE.carry is not None and watch.PROBE.enough is not None, \
        "WATCHME's emission gate demands both a carry and an enough — absent either, unarmed"
    assert "refusal" in watch.PROBE.why, "the why must carry the question this watch answers for"


def test_a_refusal_replayed_as_an_answer_is_the_finding():
    """The ticket's red (3), and the worst outcome available: a loud error turned into a
    permanent quiet wrong answer. It cannot happen today because the read path selects
    verdict='miss' — which is exactly why it is watched, since nothing declares that WHERE
    clause load-bearing and the next edit deletes the guarantee silently."""
    replayed = _answered(_AFTER, verdict="hit")
    replayed["provenance"] = dict(replayed["provenance"], refused="HostUnreachable")
    rows = [_answered(_AFTER), _refused(_AFTER), replayed]
    s = watch.judge_rows(rows)
    assert len(s["offenders"]) == 1, s
    assert s["offenders"][0]["finding"] == "a refusal was served back as a cache hit", s
    assert watch._trigger(None, {"corpus": s}) is True, "one replayed refusal IS the finding"
    assert watch._enough({"corpus": s}) is False, "a corpus with an offender never clears"


def test_a_refused_row_that_cannot_say_what_refused_it_is_the_finding():
    """Ticket red (2): the row exists and is useless — a record of truth carrying an error
    quietly (Law 7)."""
    s = watch.judge_rows([_answered(_AFTER), _refused(_AFTER, refused=None)])
    assert len(s["offenders"]) == 1 and "does not name" in s["offenders"][0]["finding"], s
    assert s["refused_by_type"] == {"(unnamed)": 1}, "the nameless one is COUNTED, not dropped"
    assert watch._trigger(None, {"corpus": s}) is True


def test_a_refusal_that_spends_or_answers_is_the_finding():
    """Ticket red (4): the fix breaking the path it was grafted beside. Two shapes, and the
    probe must catch each on its own — a refusal metered as spend, and one claiming an answer."""
    spent = watch.judge_rows([_refused(_AFTER, cost=17.0)])
    assert len(spent["offenders"]) == 1 and "metered as work" in spent["offenders"][0]["finding"], spent

    claiming = watch.judge_rows([_refused(_AFTER, answer={"text": "an answer it never got"})])
    assert len(claiming["offenders"]) == 1, claiming


def test_a_damaged_answered_row_beside_the_graft_is_the_finding():
    """The graft's neighbour: an answered row that lost its content or its cost. The old
    build could not tell that from a refusal at all — which is the whole reason this ticket
    exists — so the watch that closes it must be able to."""
    s = watch.judge_rows([_answered(_AFTER, cost=0.0), _refused(_AFTER)])
    assert len(s["hollow_answers"]) == 1, s
    assert watch._trigger(None, {"corpus": s}) is True
    empty = watch.judge_rows([_answered(_AFTER, answer={"text": ""})])
    assert len(empty["hollow_answers"]) == 1, "an answer that is there but empty is not content"


def test_a_corpus_with_no_refusal_cannot_buy_the_clear():
    """THE NON-VACUITY TOOTH, and the reason this watch exists in this shape. Twenty healthy
    answered rows and not one refusal is precisely what the DEFECT looked like from the store:
    total silence about refusals. Clearing on it would certify the state being watched for."""
    healthy = [_answered(_AFTER + timedelta(minutes=i)) for i in range(20)]
    s = watch.judge_rows(healthy)
    assert s["answered"] == 20 and s["refused"] == 0 and not s["offenders"]
    assert watch._enough({"corpus": s}) is False, \
        "zero recorded refusals is not a pass — a path that never fired is unproven, not proven"


def test_the_clear_needs_a_real_refusal_beside_healthy_answers():
    rows = [_answered(_AFTER + timedelta(minutes=i)) for i in range(12)]
    rows.append(_refused(_AFTER + timedelta(minutes=30)))
    s = watch.judge_rows(rows)
    assert s["answered"] == 12 and s["refused"] == 1
    assert s["refused_by_type"] == {"HostUnreachable": 1}, "the clear reports refusals BY KIND"
    assert watch._enough({"corpus": s}) is True, "the ticket's own enough, both halves met"
    assert watch._trigger(None, {"corpus": s}) is False


def test_a_young_berth_does_not_clear():
    s = watch.judge_rows([_answered(_AFTER), _refused(_AFTER)])
    assert not s["offenders"] and s["refused"] == 1
    assert watch._enough({"corpus": s}) is False, \
        "one refusal and one answer is a young berth — the answered denominator floor holds"


def test_the_pre_era_corpus_is_out_of_jurisdiction():
    """The 2520 rows written before this build recorded only answers because refusals left no
    trace at all. Counting them would fire the probe at its own birth about a world that no
    longer exists."""
    s = watch.judge_rows([_answered(_BEFORE), _answered(_BEFORE, cost=0.0)])
    assert s["post_era_rows"] == 0 and not s["offenders"] and not s["hollow_answers"], s
    assert watch._enough({"corpus": s}) is False, "an empty jurisdiction is not a clear"


def test_dateless_or_naive_rows_never_count():
    naive = _refused(_AFTER, refused=None)
    naive["created"] = naive["created"].replace(tzinfo=None)
    s = watch.judge_rows([naive, _answered(_AFTER)])
    assert s["post_era_rows"] == 1 and not s["offenders"], \
        "a row that cannot be placed against the era is outside jurisdiction, not an offender"


def test_the_carry_reports_complete_on_first_pass():
    s = watch.judge_rows([_refused(_AFTER, refused=None), _answered(_AFTER, cost=0.0)])
    got = watch._carry({"corpus": s})
    assert got["counts"]["offending"] == 1 and got["offenders"][0]["provenance"], \
        "the carry must deliver the offending rows verbatim, not a count to re-run for"
    assert got["counts"]["hollow_answers"] == 1 and got["hollow_answers"][0]["canonical"]
    assert "ticket" in got and "against_falsifier" in got and "suggests" in got, \
        "the finding rides with its ticket, its falsifier clause, and a suggestion"


def _main() -> int:
    checks = [
        test_the_probe_is_armed_in_the_emission_gates_shape,
        test_a_refusal_replayed_as_an_answer_is_the_finding,
        test_a_refused_row_that_cannot_say_what_refused_it_is_the_finding,
        test_a_refusal_that_spends_or_answers_is_the_finding,
        test_a_damaged_answered_row_beside_the_graft_is_the_finding,
        test_a_corpus_with_no_refusal_cannot_buy_the_clear,
        test_the_clear_needs_a_real_refusal_beside_healthy_answers,
        test_a_young_berth_does_not_clear,
        test_the_pre_era_corpus_is_out_of_jurisdiction,
        test_dateless_or_naive_rows_never_count,
        test_the_carry_reports_complete_on_first_pass,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the watch fires on a replayed refusal, a nameless refused row, a refusal "
          "metered as work, or a damaged answer beside the graft; and it CANNOT be cleared by "
          "a corpus that has never recorded a refusal — silence is the defect, not the pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
