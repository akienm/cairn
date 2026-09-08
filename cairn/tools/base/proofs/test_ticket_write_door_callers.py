"""PROBE PROOF — the ticket write door is watched for CALLERS, and the watch can un-clear.

Ticket ``9e7867aa1056``. The probe under test is
``cairn/tools/base/probes/the_ticket_write_door_has_callers.py``.

WHAT A HOLLOW BUILD OF THIS WATCH LOOKS LIKE, EXACTLY, because this address has produced it
twice. ``a_pickup_is_witnessed`` cleared on ``pickups >= 1``, took its one record in August
2026, and read green for a month while the door it watched had no caller at all. And the
door THIS probe watches exists only because a grep for ticket writes across ``cairn/``,
``skills/`` and ``bin/`` returned ZERO — every cursor on 259 tickets was a hand-edit. A watch
that clears on "records exist" would reproduce the first failure while pointing at the
second.

So the teeth are not "does it describe today's corpus" — that is a snapshot, and tomorrow's
corpus reds it. They are:

  - IT IS FALSE ON A BATCH-ONLY CORPUS, at any size. Thirty records all written on the day
    the door shipped is a migration script, and scale must not rescue it.
  - IT GOES BACK DOWN, driven in both directions rather than read off the clause.
  - BOTH HALVES ARE LOAD-BEARING — liveness and no-slippage each dropped in turn, so neither
    can rot behind the other.
  - THE BATCH DAY IS DERIVED, not hard-coded: shift the whole corpus in time and the probe's
    verdict must not move.
  - IT WALKS ONCE PER MOVE, not once per beat (live trouble
    ``beat-tail-re-walks-corpora-no-sieve-counts``).
  - THE PROBE IS SHAPED, so the emission gate's ARMED read is not the only thing standing
    between this and an unfired watch.
"""

from __future__ import annotations

import dataclasses
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.base import settled as S  # noqa: E402
from cairn.tools.base.probes import the_ticket_write_door_has_callers as D  # noqa: E402


def _cursor(phase: str | None) -> str:
    tail = f"BUILDME:{phase}" if phase else "BUILDME"
    return f"code-seam@v2: THINKME -> TICKETME -> [{tail}] -> PROVEME -> PROVED"


def _corpus(dirpath: Path, spec: list[tuple[str, str | None, list[str]]]) -> None:
    """``spec`` is (id, phase, [days the door was called]) per ticket.

    Written as files because the probe reads files — a corpus faked at the function boundary
    would not exercise the walk. Each named day produces one phase_writes record whose
    ``workflow`` matches the ticket's own cursor, i.e. a record the door itself would have
    left; a ticket given no days is a hand-edit."""
    for tid, phase, days in spec:
        cur = _cursor(phase)
        doc: dict = {"id": tid, "workflow_and_state": cur}
        if days:
            doc["phase_writes"] = [
                {"act": "set_phase", "actor": "CC", "phase": phase, "release": None,
                 "standing": "BUILDME", "workflow": cur, "at": f"{day}T09:00:00"}
                for day in days
            ]
        (dirpath / f"{tid}.json").write_text(json.dumps(doc))


def _walk(dirpath: Path) -> dict:
    before = D._TICKETS
    try:
        D._TICKETS = dirpath
        return D._walk_tickets()
    finally:
        D._TICKETS = before


def _used(n: int, days: list[str], start: int = 0) -> list[tuple[str, str, list[str]]]:
    """``n`` tickets each backed by a record on every one of ``days``."""
    return [(f"{i:012x}", "hold", list(days)) for i in range(start, start + n)]


def test_a_batch_only_corpus_never_clears_however_large() -> None:
    """THE NAMED FAILURE: the door ships, the backlog goes through it, and nothing calls it
    again. Thirty records is not thirty callers when all thirty share one day — and the
    sibling that cleared on ``>= 1`` would have read every one of these corpora as success."""
    for n in (12, 30, 120):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            _corpus(p, _used(n, ["2026-09-08"]))
            s = _walk(p)
            assert s["records"] == n and s["batch_day"] == "2026-09-08", s
            assert s["records_after_batch"] == 0 and s["days_after_batch"] == [], s
            assert D._enough({"door": s}) is False, f"a batch of {n} cleared the watch"
            # and the TRIGGER fires — a door that went quiet is the finding, not silence
            assert D._trigger(None, {"door": s}) is True, n


def test_the_clear_goes_up_AND_BACK_DOWN() -> None:
    """THE TOOTH THE SIBLING PROBE COULD NOT HAVE PASSED. Cleared on a corpus with real use
    after the batch, then the corpus reverts to hand-edits, then un-cleared."""
    spec = _used(10, ["2026-09-08"])
    spec += _used(2, ["2026-09-11"], start=10)
    spec += _used(2, ["2026-09-15"], start=12)
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _corpus(p, spec)
        s = _walk(p)
        assert s["records_after_batch"] >= D._ENOUGH_AFTER_BATCH, s
        assert len(s["days_after_batch"]) >= D._ENOUGH_DISTINCT_DAYS, s
        assert not s["unbacked_written_phases"], s["unbacked_written_phases"]
        assert D._enough({"door": s}) is True, "a genuinely used door did not clear"

        # A cleared watch is not a finished one: the same probe over a reverted corpus.
        for f in p.glob("*.json"):
            f.unlink()
        _corpus(p, [(f"{i:012x}", "waiting", []) for i in range(40)])
        again = _walk(p)
        assert D._enough({"door": again}) is False, \
            "the clear survived the corpus that earned it — the watch stopped watching"


def test_both_halves_of_the_clear_are_load_bearing() -> None:
    """Liveness and no-slippage measure different failures, so each is dropped in turn. A
    half that no longer decides anything is a half that can rot behind the other."""
    live = _used(10, ["2026-09-08"]) + _used(3, ["2026-09-11", "2026-09-15"], start=10)

    # (1) the door is called, but a hand-edited phase stands beside it — walked around.
    slipped = list(live) + [("ffffffffffff", "blocked", [])]
    # (2) nothing slipped, but every record shares the batch day — the door went quiet.
    quiet = _used(13, ["2026-09-08"])
    # (3) called after the batch, but all on ONE later day — a second migration, not a habit.
    one_day = _used(10, ["2026-09-08"]) + _used(3, ["2026-09-11"], start=10)

    for name, spec in (("a hand-edit slipped past", slipped),
                       ("the door went quiet", quiet),
                       ("one day only", one_day)):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            _corpus(p, spec)
            s = _walk(p)
            assert D._enough({"door": s}) is False, f"the clear ignored: {name}"
            assert D._trigger(None, {"door": s}) is True, f"the trigger ignored: {name}"


def test_a_record_naming_an_OLDER_cursor_does_not_back_the_phase() -> None:
    """The subtlest slip, and the one a records-exist check cannot see: the door WAS used,
    and then the file was hand-edited afterwards. The phase_writes list makes the ticket look
    gated while its cursor says something the record never authorised."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _corpus(p, _used(12, ["2026-09-08"]) + _used(3, ["2026-09-11", "2026-09-15"], start=12))
        victim = p / f"{0:012x}.json"
        doc = json.loads(victim.read_text())
        doc["workflow_and_state"] = _cursor("blocked")   # hand-edited past its own record
        victim.write_text(json.dumps(doc))
        s = _walk(p)
        assert [u["ticket"] for u in s["unbacked_written_phases"]] == [f"{0:012x}"], s
        assert D._enough({"door": s}) is False
        assert D._trigger(None, {"door": s}) is True


def test_the_batch_day_is_DERIVED_so_shifting_the_corpus_in_time_changes_nothing() -> None:
    """A hard-coded batch date is a constant somebody can re-point at a friendlier day to
    make a watch clear. The same corpus shifted wholesale must give the same verdict."""
    verdicts = []
    for base in ("2026-09", "2026-11", "2027-03"):
        spec = _used(10, [f"{base}-08"]) + _used(3, [f"{base}-11", f"{base}-15"], start=10)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            _corpus(p, spec)
            s = _walk(p)
            assert s["batch_day"] == f"{base}-08", s["batch_day"]
            verdicts.append((D._enough({"door": s}), D._trigger(None, {"door": s})))
    assert len(set(verdicts)) == 1 and verdicts[0] == (True, False), verdicts


def test_the_trigger_stays_silent_before_the_batch_has_landed() -> None:
    """A door reds for having no callers only once it has had the chance to have some. Below
    the floor there is nothing to ask about, and a probe that shouted at an empty corpus
    would be noise on every beat between shipping and using."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _corpus(p, _used(2, ["2026-09-08"]) + [(f"{i:012x}", "waiting", []) for i in range(5, 9)])
        s = _walk(p)
        assert s["records"] < D._TRIGGER_FLOOR, s
        assert D._trigger(None, {"door": s}) is False, "shouted before the batch landed"
        assert D._enough({"door": s}) is False, "cleared before the batch landed"


def test_a_record_without_a_readable_time_is_not_counted_rather_than_guessed() -> None:
    """An invented date would let the distinct-days clause clear on nothing — the hollow pass
    this whole probe is shaped against."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _corpus(p, _used(12, ["2026-09-08"]))
        victim = p / f"{0:012x}.json"
        doc = json.loads(victim.read_text())
        doc["phase_writes"][0].pop("at")
        victim.write_text(json.dumps(doc))
        s = _walk(p)
        assert s["records"] == 12, s          # counted as a record
        assert s["days_seen"] == ["2026-09-08"], s   # but contributes no day
        assert D._day({"at": None}) is None and D._day({}) is None and D._day("x") is None


def test_terminal_tickets_leave_the_live_corpus() -> None:
    """The mechanism that lets the clear go back DOWN: a written phase on a ticket that
    reached a terminal is history, not a standing obligation, so it must not be judged."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _corpus(p, _used(3, ["2026-09-08"]))
        done = p / f"{0:012x}.json"
        doc = json.loads(done.read_text())
        doc["workflow_and_state"] = \
            "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]"
        done.write_text(json.dumps(doc))
        s = _walk(p)
        assert s["live_tickets"] == 2, s
        assert not any(u["ticket"] == f"{0:012x}" for u in s["unbacked_written_phases"]), s


def test_the_walk_is_settled_and_re_reads_nothing_over_an_unmoved_corpus() -> None:
    """Live trouble ``beat-tail-re-walks-corpora-no-sieve-counts``: ~78 probes re-walk corpora
    that did not move, once per beat, forever, and nothing reds the 79th. The counter is the
    only surface that can tell a memo from a re-derivation."""
    S.forget()
    cold = D.survey_the_door()
    before = S.DERIVATIONS
    for _ in range(5):
        assert D.survey_the_door() == cold, "the answer moved while the corpus did not"
    assert S.DERIVATIONS == before, (
        f"the walk re-derived {S.DERIVATIONS - before} times over an unmoved corpus — "
        "this probe is the 79th")
    assert cold["live_tickets"] > 0, "a memo over a vacuous walk proves nothing"


def test_the_probe_is_a_frozen_shape_carrying_both_a_carry_and_a_clear() -> None:
    from cairn.tools.base.probe import Probe
    assert isinstance(D.PROBE, Probe)
    assert dataclasses.is_dataclass(D.PROBE) and D.PROBE.__dataclass_params__.frozen
    assert callable(D.PROBE.carry) and callable(D.PROBE.enough) and callable(D.PROBE.trigger)
    body = D.PROBE.carry({})
    for field in ("finding", "counts", "ticket", "against_falsifier", "suggests"):
        assert body.get(field), f"the carry rides back without {field}"
    assert D.PROBE.horizon and D.PROBE.horizon > 0


def _main() -> int:
    checks = [v for k, v in sorted(globals().items())
              if k.startswith("test_") and callable(v)]
    assert len(checks) >= 10, f"a tooth nobody lists is a tooth that did not run: {len(checks)}"
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print(f"\ngreen — {len(checks)} checks: the ticket write door's watch is false on a "
          f"batch-only corpus at any size, false when a hand-edit stands beside the door, "
          f"false when the door was used and then edited past, derives its batch day rather "
          f"than carrying a date somebody can re-point, stays silent before the batch lands, "
          f"counts no record whose time it cannot read, drops terminal tickets so the clear "
          f"can go back DOWN, and walks once per corpus move rather than once per beat")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
