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
from cairn.devices.builder.machines.verdict.verdict import (  # noqa: E402
    OUTCOMES, verdict_error,
)

REPO = Path(__file__).resolve().parents[4]
#: The door's word for a passing verdict, IMPORTED. Spelling it here by hand is the
#: exact defect these teeth were blind to; a rename in the door must red this file.
PASS, FAIL = OUTCOMES[0], OUTCOMES[1]
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


def verdict_berth(root: Path, ticket: str, outcomes=(PASS,), stamp="20260816T000000",
                  *, door_shaped=True):
    """A stand-in for an artifact the verdict door wrote — and it must EARN that.

    THE FIXTURE IS CHECKED BY THE WRITER'S OWN GATE, which is the whole lesson of
    2026-08-16. This helper used to hand-write `{"criteria": [...], "outcome":
    "passed"}` — a shape the door has never produced in its life — and the probe read
    exactly that shape, so seventeen teeth went green proving the reader and the fixture
    agreed with each other. `verdict_error` is the door's own pure-shape check (no disk,
    no chain), so running the fixture through it makes a fixture the door would refuse
    unable to stand for one it wrote. `door_shaped=False` is the deliberate escape, and
    it exists only so a tooth can feed the probe a malformed artifact on purpose.
    """
    d = root / "chart" / "packets"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"verdict-{stamp}-{abs(hash(ticket)) % 10**12:012d}.json"
    artifact = {
        "ticket": ticket,
        "validate_ref": f"falsifier@{ticket}",
        "verdicts": [{"claim": f"c{i}", "instrument": "an instrument",
                      "outcome": o, "evidence": "evidence",
                      "discriminating_observation": "reverted the fix; instrument exits 1"}
                     for i, o in enumerate(outcomes)],
        "dispositions": [],
    }
    if door_shaped:
        refusal = verdict_error(artifact)
        assert refusal is None, (
            "THE FIXTURE IS NOT A SHAPE THE DOOR WOULD BERTH, so it cannot stand for an "
            f"artifact the door wrote: {refusal}")
    p.write_text(json.dumps(artifact), encoding="utf-8")
    return p


# ------------------------------------------------- the declaration itself

def test_the_probe_is_armed_at_the_path_the_TICKET_names():
    """The emission gate resolves ARMED from the ticket's spec, so the path is the contract.

    ASKED THE WAY THE GATE ASKS IT. This tooth used to resolve the berth against the
    CURRENT WORKING DIRECTORY, and passed for a reason that was luck: this ticket happens
    to spell its berth absolutely, so cwd never entered. Its sibling's ticket spells the
    same field relatively, and the identical line went green bare and red under the netns
    seal — same tooth, same claim, different answer depending on where it was run from.
    Both now call `armed_error`, which is the gate's own question and joins to the repo
    root rather than to wherever the runner happened to stand.
    """
    spec = json.loads((Path.home() / "dev/src/CairnCommons/tickets/aider-shim.json")
                      .read_text(encoding="utf-8"))["watchme"]
    from cairn.tools.base.watchme_spec import armed_error
    refusal = armed_error(spec)
    assert refusal is None, f"the gate would refuse the WATCHME crossing: {refusal}"
    assert (REPO / spec["probe"]).resolve() == Path(probe.__file__).resolve(), \
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
        verdict_berth(root, "green", (PASS, PASS))
        verdict_berth(root, "mixed", (PASS, FAIL), stamp="20260816T000001")
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
        verdict_berth(root, "t", (FAIL,), stamp="20260816T000000")
        p = verdict_berth(root, "t", (PASS,), stamp="20260816T235959")
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


def test_EVERY_column_the_charter_PROMISES_is_present_hole_or_measurement():
    """The charter's ``how_it_learns`` is a promise about this probe's carry, and drift
    between them is silent in both directions: the charter reads as a description of a
    working instrument, and the probe reads as complete because nothing states what it
    left out. Three columns are named there — passed physics, CC call count, and whether
    CC had to supply context beyond the piece and the bounds. The third was MISSING at
    the close of the building voyage; a hole is the honest shape for it, an absence is
    not, and this is the tooth that keeps a promised column from going quiet.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = ask_log(tmp, [allowed("t")])
        root = tmp / "berths"
        verdict_berth(root, "t")
        row = probe.yields_so_far(ask_log=log, berths_root=root)[0]
        for col in ("passed", "cc_calls", "extra_context"):
            assert col in row, f"the charter promises {col!r} and the row does not carry it"
        for hole in ("cc_calls_hole", "extra_context_hole"):
            assert row.get(hole), f"{hole} is empty — a None with no referent is an absence"
        assert "filed edge (c)" in row["extra_context_hole"], (
            "the extra-context hole must name the decision it would falsify, or a reader "
            "cannot tell why the column is worth waiting for")


def test_the_probe_reads_the_shape_the_DOOR_WRITES_not_one_it_invented():
    """THE TOOTH THAT WAS MISSING, and its absence cost this device a dead column.

    Until 2026-08-16 the probe read ``artifact["criteria"]`` and compared outcomes to
    ``"passed"``. The door writes ``verdicts`` and its vocabulary is ``("pass","fail")``.
    Both spellings were wrong; every real artifact yielded ``0 criteria, passed False``,
    and the carrier looked healthy while ``green`` sat at zero forever. The seventeen
    teeth that stood here all missed it because the FIXTURE hand-wrote the reader's
    invented shape — the two halves of one head agreeing with each other.

    So this tooth refuses to DESCRIBE the artifact at all. It builds one THROUGH THE
    DOOR'S OWN WRITER and asserts the probe reads it green. The falsifier form
    (``falsifier@<ticket>``) is used because it needs no chart chain on disk — and both
    the ticket root and the berth root are injected, so this reads a synthetic world in
    a tempdir: no CairnCommons, no instance-space. If anyone renames a key or a
    vocabulary word on either side of the seam, this goes red AT the seam instead of
    going quiet in the carrier.
    """
    from cairn.devices.builder.machines.verdict.verdict import (
        falsifier_criteria, write_verdict,
    )
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        ticket = "probe-reads-the-door"
        tickets = tmp / "CairnCommons" / "tickets"
        tickets.mkdir(parents=True)
        (tickets / f"{ticket}.json").write_text(json.dumps({
            "id": ticket,
            "falsifier": "RED on any of: (1) the probe cannot read a door-written "
                         "artifact. (2) the count of verdicts comes back zero.",
        }), encoding="utf-8")
        fake_root = str(tmp / "cairn")           # ticket_path reads dirname(root)/CairnCommons
        owed, err = falsifier_criteria(ticket, root=fake_root)
        assert err is None and len(owed) == 2, (err, owed)

        log = ask_log(tmp, [allowed(ticket)])
        root = tmp / "berths"
        (root / "chart" / "packets").mkdir(parents=True, exist_ok=True)
        written = write_verdict({
            "ticket": ticket,
            "validate_ref": f"falsifier@{ticket}",
            # claims VERBATIM from the door's own deriver — the point of it being public
            "verdicts": [{"claim": c["claim"], "instrument": "this tooth",
                          "outcome": PASS, "evidence": "the assertions below",
                          "discriminating_observation": "reverted the fix; instrument exits 1"}
                         for c in owed],
            "dispositions": [],
        }, instance_dir=str(root / "chart" / "packets"), root=fake_root)

        rows = probe.yields_so_far(ask_log=log, berths_root=root)
        assert len(rows) == 1, f"the door's own artifact was not read at all: {rows}"
        assert rows[0]["verdict_berth"] == written
        assert rows[0]["passed"] is True, (
            "THE PROBE CANNOT READ WHAT THE DOOR WRITES — this is the 2026-08-16 defect "
            f"returning: {rows[0]}")
        assert rows[0]["verdicts"] > 0, (
            "zero verdicts counted from a real artifact: the key the probe reads is not "
            "the key the door writes")
        assert rows[0]["shape_refusal"] is None


def test_an_artifact_the_DOOR_WOULD_REFUSE_is_not_counted_as_a_FAILED_build():
    """A malformed artifact and a failed build are different facts, and collapsing them
    is the quiet lie the old reader told: a shape it could not parse came out as
    ``passed: False``, indistinguishable from a voyage whose criteria genuinely failed.
    Now it comes out ``None`` with the door's own refusal text beside it, and the carry
    counts it in ``unshaped`` rather than in the not-green pile.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        log = ask_log(tmp, [allowed("t")])
        root = tmp / "berths"
        p = verdict_berth(root, "t", door_shaped=False)
        junk = json.loads(p.read_text(encoding="utf-8"))
        junk["verdicts"][0]["evidence"] = ""      # narration — the door refuses it
        p.write_text(json.dumps(junk), encoding="utf-8")
        row = probe.yields_so_far(ask_log=log, berths_root=root)[0]
        assert row["passed"] is None, "a shape the door refuses was scored as a build result"
        assert row["shape_refusal"] and "evidence" in row["shape_refusal"]
        carried = probe.PROBE.carry({"ask_log": log, "berths_root": root})
        assert carried["green"] == 0 and carried["unshaped"] == 1, carried


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
