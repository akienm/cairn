#!/usr/bin/env python3
"""Teeth for the offload probe. The claim under test is that this watch can COUNT.

A probe is the one artifact in a voyage whose failure is silent by construction: it is
armed, it is never fired by anything in this build, and every check you can run on it is a
check on a declaration. So the teeth here are aimed at the two ways a declaration lies.

  (1) IT CANNOT COUNT ITS POPULATION. `shimmed_tickets` is the whole instrument — if it
      counts refused asks, or ticketless ones, or double-counts, then every number the
      carrier ever sends is wrong and looks fine.
  (2) ITS STOPPING CONDITION IS SATISFIABLE BY LESS THAN IT ASKED FOR. `enough` demands
      both columns; one of them has no instrument today. The tooth that matters is the one
      that reds if `enough` ever goes true on the half we can already measure — that is
      the exact edit a future reader makes to "unstick" the probe, and it retires the
      watch at the moment it had learned the less interesting half.

No instance-space is read: every path is injected, which is also the honest test of whether
the probe's seams are injectable at all.
"""

import json
import sys
import tempfile
import traceback
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.aider_shim.probes import offload_yield_probe as probe  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"  ok   {name}")
    except Exception:
        FAILURES.append(name)
        print(f"  FAIL {name}")
        traceback.print_exc()


def ask_log(tmp: Path, rows) -> Path:
    p = tmp / "asks.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def allowed(ticket, model="qwen3-coder:30b"):
    return {"at": "2026-08-16T00:00:00+00:00", "model": model, "verdict": "allowed",
            "provider": "hex", "ticket": ticket, "detail": "miss"}


def refused(ticket, model="gpt-4o"):
    return {"at": "2026-08-16T00:00:00+00:00", "model": model, "verdict": "refused",
            "provider": "", "ticket": ticket, "detail": "off the fence"}


def verdict_berth(root: Path, ticket: str, outcomes=("passed",), stamp="20260816T000000"):
    d = root / "chart" / "packets"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"verdict-{stamp}-{abs(hash(ticket)) % 10**12:012d}.json"
    p.write_text(json.dumps({
        "ticket": ticket,
        "criteria": [{"claim": f"c{i}", "instrument": "an instrument",
                      "outcome": o, "evidence": "evidence"}
                     for i, o in enumerate(outcomes)],
        "hypotheses": [],
    }), encoding="utf-8")
    return p


# ------------------------------------------------- the declaration itself

def test_the_probe_is_armed_at_the_path_the_TICKET_names():
    """The emission gate resolves ARMED from the ticket's spec, so the path is the contract."""
    spec = json.loads((Path.home() / "dev/src/CairnCommons/tickets/aider-shim.json")
                      .read_text(encoding="utf-8"))["watchme"]
    assert Path(spec["probe"]).resolve() == Path(probe.__file__).resolve(), \
        f"the probe is not where the ticket says: {spec['probe']}"
    assert spec["object"] == "aider_shim_offload_yield"


def test_the_probe_carries_BOTH_a_carry_and_an_enough():
    """/sail step 7's requirement, and neither is decoration.

    A carry-less probe says only THAT a line was crossed, which is useless to a consumer who
    has to decide offload-more vs pull-back. An enough-less probe is a standing watch with
    no end — legitimate in general, and wrong here, because the ticket declared a stopping
    condition and a probe that dropped it would be quietly widening its own scope.
    """
    assert probe.PROBE.carry is not None and callable(probe.PROBE.carry)
    assert probe.PROBE.enough is not None and callable(probe.PROBE.enough)
    assert probe.PROBE.horizon and probe.PROBE.horizon > 0
    assert probe.PROBE.why and len(probe.PROBE.why) > 80


def test_the_probe_is_FROZEN():
    """It is a declaration, not a worker — its fire-history lives on whatever fires it."""
    try:
        probe.PROBE.horizon = 1
    except FrozenInstanceError:
        return
    raise AssertionError("the probe accepted a mutation; it is not a declaration")


def test_the_ask_log_path_matches_the_FENCES_own():
    """Two spellings of one path is how a probe ends up counting an empty file forever.

    The probe cannot import the fence (the emission gate loads this module to READ it), so
    the constant is duplicated — and a duplicated constant with nothing comparing the two
    is a drift waiting for its first rename. This is that comparison.
    """
    from cairn.devices.aider_shim.fence import DEFAULT_RECORD
    assert probe.ASK_LOG == DEFAULT_RECORD, f"{probe.ASK_LOG} != {DEFAULT_RECORD}"


# ------------------------------------------------- can it count its population?

def test_only_ALLOWED_asks_count_as_built():
    """A ticket the fence refused was never built through the shim.

    Counting it would inflate the population with exactly the runs that produced no work —
    and it would inflate it in the flattering direction, since a refused run also produces
    no failed verdict to drag the green-rate down.
    """
    with tempfile.TemporaryDirectory() as d:
        log = ask_log(Path(d), [refused("t-refused"), allowed("t-built")])
        assert probe.shimmed_tickets(ask_log=log) == ["t-built"]


def test_a_TICKETLESS_ask_is_not_attributed():
    """A live fire or a proof records honestly as ticketless, and must stay uncounted.

    The failure this stops is attribution-by-adjacency: a run with no ticket getting folded
    into whatever voyage happened to be open, which is the same proxy-by-timing the design
    rejected, arriving through the back door.
    """
    with tempfile.TemporaryDirectory() as d:
        log = ask_log(Path(d), [allowed(""), {**allowed("t"), "ticket": None},
                                allowed("t-real")])
        assert probe.shimmed_tickets(ask_log=log) == ["t-real"]


def test_tickets_are_deduplicated_and_stay_in_order():
    """One ticket makes many asks. The population is tickets, not asks."""
    with tempfile.TemporaryDirectory() as d:
        log = ask_log(Path(d), [allowed("a"), allowed("b"), allowed("a"), allowed("c"),
                                allowed("b")])
        assert probe.shimmed_tickets(ask_log=log) == ["a", "b", "c"]


def test_a_TORN_line_does_not_blind_the_whole_count():
    """A half-written JSONL line is the ordinary state of an append-only log under a crash.

    Reading the file as all-or-nothing would make one torn byte erase the entire population
    — and erase it as a zero, which reads exactly like 'nothing has been shimmed yet'.
    """
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "asks.jsonl"
        p.write_text(json.dumps(allowed("a")) + "\n{\"ticket\": \"b\", \"verdi\n"
                     + json.dumps(allowed("c")) + "\n", encoding="utf-8")
        assert probe.shimmed_tickets(ask_log=p) == ["a", "c"]


def test_a_missing_log_is_ZERO_not_an_error():
    """Before the first shimmed build there is no file, and that is a legitimate answer."""
    with tempfile.TemporaryDirectory() as d:
        assert probe.shimmed_tickets(ask_log=Path(d) / "nope.jsonl") == []


# ------------------------------------------------- can it read the yield?

def test_a_shimmed_ticket_with_NO_verdict_artifact_is_not_a_row():
    """The trigger is 'reaches its verdict artifact'. Not reaching one is not a yield.

    Counting it would put a row in the carrier with no outcome to report, which the
    green-rate would then have to treat as either a pass or a fail — both lies.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = ask_log(tmp, [allowed("built"), allowed("in-flight")])
        root = tmp / "berths"
        verdict_berth(root, "built")
        rows = probe.yields_so_far(ask_log=log, berths_root=root)
        assert [r["ticket"] for r in rows] == ["built"]


def test_passed_is_TRUE_only_when_every_criterion_passed():
    """The green-rate is the measured half, so it may not round in the shim's favour."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = ask_log(tmp, [allowed("green"), allowed("mixed"), allowed("empty")])
        root = tmp / "berths"
        verdict_berth(root, "green", ("passed", "passed"))
        verdict_berth(root, "mixed", ("passed", "failed"), stamp="20260816T000001")
        verdict_berth(root, "empty", (), stamp="20260816T000002")
        rows = {r["ticket"]: r["passed"] for r in
                probe.yields_so_far(ask_log=log, berths_root=root)}
        assert rows == {"green": True, "mixed": False, "empty": False}, rows


def test_the_LATEST_verdict_artifact_is_the_one_that_stands():
    """Latest-wins is the resolver's rule, and the probe composes it rather than re-deriving."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = ask_log(tmp, [allowed("t")])
        root = tmp / "berths"
        verdict_berth(root, "t", ("failed",), stamp="20260816T000000")
        p = verdict_berth(root, "t", ("passed",), stamp="20260816T235959")
        rows = probe.yields_so_far(ask_log=log, berths_root=root)
        assert rows[0]["passed"] is True and rows[0]["verdict_berth"] == str(p)


def test_the_COST_column_is_a_declared_hole_never_a_silent_absence():
    """Law 7 at a diagnostic surface: a row missing a column must SAY it is missing.

    A receiver handed a row whose cost key is simply absent reads the row as complete. One
    handed `cc_calls: None` beside a sentence naming the ticket that owes the instrument
    knows exactly what it does not have, and where the work is.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = ask_log(tmp, [allowed("t")])
        root = tmp / "berths"
        verdict_berth(root, "t")
        row = probe.yields_so_far(ask_log=log, berths_root=root)[0]
        assert "cc_calls" in row and row["cc_calls"] is None
        assert row["cc_calls_hole"] and "the-builds-tool-calls" in row["cc_calls_hole"]
        carried = probe.PROBE.carry({"ask_log": log, "berths_root": root})
        assert carried["shimmed"] == 1 and carried["green"] == 1
        assert "hole" in carried["reads"]


# ------------------------------------------------- the stopping condition

def test_enough_is_FALSE_at_five_tickets_while_the_COST_COLUMN_is_a_HOLE():
    """THE TOOTH THAT MATTERS. `enough` may not go true on the half we can already measure.

    This is the exact edit a future reader makes to unstick a probe that has been standing
    a long time: drop the `cc_calls is not None` clause, and five green tickets retire the
    watch. It would retire having learned that the apprentice's builds pass — and nothing
    at all about whether they COST less, which is the entire question the offload was made
    to answer. The horizon is what is supposed to make the waiting loud; lowering the bar
    is what makes it quiet.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = ask_log(tmp, [allowed(f"t{i}") for i in range(5)])
        root = tmp / "berths"
        for i in range(5):
            verdict_berth(root, f"t{i}", stamp=f"2026081600000{i}")
        ctx = {"ask_log": log, "berths_root": root}
        assert len(probe.yields_so_far(**ctx)) == 5
        assert probe.PROBE.enough(ctx) is False, \
            "enough went true with the cost column still a hole"


def test_enough_goes_TRUE_once_the_cost_column_is_actually_filled():
    """The other half of the previous tooth: the condition is REACHABLE, not merely strict.

    Without this, `enough` returning False forever would be indistinguishable from a
    stopping condition that is simply broken — and a watch that can never stop is a watch
    whose `enough` is decoration.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = ask_log(tmp, [allowed(f"t{i}") for i in range(5)])
        root = tmp / "berths"
        for i in range(5):
            verdict_berth(root, f"t{i}", stamp=f"2026081600000{i}")
        ctx = {"ask_log": log, "berths_root": root}
        real = probe.yields_so_far

        def filled(**kw):
            return [{**r, "cc_calls": 12} for r in real(**kw)]

        probe.yields_so_far = filled
        try:
            assert probe.PROBE.enough(ctx) is True
            probe.yields_so_far = lambda **kw: [{**r, "cc_calls": 12} for r in real(**kw)][:4]
            assert probe.PROBE.enough(ctx) is False, "four is not five"
        finally:
            probe.yields_so_far = real


def test_the_trigger_fires_on_a_NEW_artifact_and_not_on_a_standing_one():
    """A poke per crossing, not per pulse — the count rides context, the probe holds none."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = ask_log(tmp, [allowed("a"), allowed("b")])
        root = tmp / "berths"
        verdict_berth(root, "a")
        ctx = {"ask_log": log, "berths_root": root}
        assert probe.PROBE.trigger(None, {**ctx, "seen": 0}) is True
        assert probe.PROBE.trigger(None, {**ctx, "seen": 1}) is False
        verdict_berth(root, "b", stamp="20260816T000001")
        assert probe.PROBE.trigger(None, {**ctx, "seen": 1}) is True


def main():
    print("aider_shim :: probe")
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            check(name, fn)
    if FAILURES:
        print(f"\nRED — {len(FAILURES)} failure(s): {FAILURES}")
        return 1
    print("\nGREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
