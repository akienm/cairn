#!/usr/bin/env python3
"""Teeth for the reflection-yield probe. The claim under test is that this watch can say
what the EXTRA ASKS bought — and, harder, that it says so without ever going green for the
wrong reason.

A probe is the one artifact in a voyage whose failure is silent by construction: it is
armed, nothing in this build fires it, and every check you can run is a check on a
declaration. So the teeth are aimed at the ways THIS declaration could lie, and three of
them are specific to this watch rather than to probes in general:

  (1) IT COUNTS A CACHE HIT AS A SECOND OPINION. `prompt_eval_count` is None when no call
      was made. Five cached reflections would retire this watch having learned nothing, and
      a byte-identical hit has already been misread as determinism once in this very
      population.
  (2) ITS CARRIAGE CHECK GOES GREEN FOR THE WRONG REASON. The fence records `ask_chars` and
      never the prompt, so containment is not readable here. The probe's answer is a
      ONE-SIDED necessary condition and its passing word must be `consistent` — a probe that
      said `carried` off a length bound would be reporting a proof it does not have.
  (3) IT UNDER-FIRES THE STOP-EARLY FALSIFIER. `left-changed-and-failing` is deliberately a
      SUPERSET of the state the spec names, because the per-attempt image that would narrow
      it is never taken. Over-firing costs a human a look; under-firing lets the loop go on
      manufacturing the harm it was armed to catch.

EVERY FIXTURE GOES THROUGH THE WRITER. The rows here are real `DriveResult`s written by
`driver.record` — the one hand that mints a drive row. A fixture that agrees with the READER
instead of the WRITER proves only that the two agree with each other.

No instance-space is read or written: the drives path is injected throughout, which is also
the honest test of whether the probe's one seam is injectable at all.
"""

import json
import sys
import tempfile
import traceback
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.aider_shim import driver  # noqa: E402
from cairn.devices.aider_shim.probes import reflection_earns_its_ask as probe  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
TICKET = "the-apprentice-learns-its-test-failed"
FAILURES = []

#: The failure a fixture drive's test reports. Long enough that a "second ask did not grow"
#: fixture is unambiguous rather than an off-by-a-few.
FAIL_TEXT = "AssertionError: add(2,3) == -1, expected 5 — the piece is not done\n"


def check(name, fn):
    try:
        fn()
        print(f"  ok   {name}")
    except Exception:
        FAILURES.append(name)
        print(f"  FAIL {name}")
        traceback.print_exc()


def an_ask(chars: int, *, cached=False, verdict="allowed"):
    """One fence row, shaped the way `SeenLog.record` shapes it — including the honest None
    that a cache hit leaves in `prompt_eval_count` (there was no call, so there is no count)."""
    return {"at": "2026-08-18T00:00:00+00:00", "model": "qwen3-coder:30b", "verdict": verdict,
            "provider": "hex", "ticket": TICKET, "ask_chars": chars, "num_ctx": 16384,
            "prompt_eval_count": None if cached else max(1, chars // 4), "detail": ""}


def a_drive(root: Path, drives: Path, *, index=0, reflections=0, asks=None,
            passed=True, edited=None, moved=True, error="", ticket=TICKET):
    """Write one drive row THROUGH THE DRIVER'S OWN WRITER.

    `edited`/`moved` build the before/after pair the way a real drive does — `driver.image_of`
    takes both images, so `moved=False` produces a row where aider claimed an edit and no
    byte actually changed, which is a real state and one the outcome vocabulary must handle.
    """
    edited = edited if edited is not None else (["a.py"] if not passed else [])
    p = root / "a.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"before-{index}\n", encoding="utf-8")
    before = driver.image_of(["a.py"], root)
    if edited and moved:
        p.write_text(f"after-{index}\n", encoding="utf-8")
    after = driver.image_of(["a.py"], root)
    r = driver.DriveResult(
        ticket=ticket, piece_index=index, model="qwen3-coder:30b",
        at=f"2026-08-18T00:00:{index:02d}+00:00", files=["a.py"],
        before=before, after=after, aider_reported_edited=list(edited),
        asks=list(asks if asks is not None else [an_ask(1000)]),
        num_reflections=reflections, max_reflections=1, error=error,
    )
    r.test = {"cmd": "python3 check.py", "ran": True, "returncode": 0 if passed else 3,
              "stdout": "", "stderr": "" if passed else FAIL_TEXT, "passed": passed}
    driver.record(r, path=drives)
    return r


def a_reflected_drive(root, drives, *, index=0, passed=False, cached=False, grows=True,
                      **more):
    """A drive that reflected: two asks, the second carrying the whole conversation again."""
    first = an_ask(1000)
    second = an_ask(1000 + (len(FAIL_TEXT) + 50 if grows else 5), cached=cached)
    return a_drive(root, drives, index=index, reflections=1, asks=[first, second],
                   passed=passed, **more)


def ctx(drives: Path, **more):
    return {"drives_path": drives, **more}


# ------------------------------------------------- the declaration itself

def test_the_probe_is_armed_at_the_path_the_TICKET_names():
    """The emission gate resolves ARMED from the ticket's spec, so the path IS the contract.

    Asked the way the GATE asks it — `armed_error` itself, not a re-derivation of what it
    does. A relative berth resolved against the cwd is green bare and red under the netns
    seal; the gate joins the berth to the repo root and never touches cwd.
    """
    spec = json.loads((Path.home() / f"dev/src/CairnCommons/tickets/{TICKET}.json")
                      .read_text(encoding="utf-8"))["watchme"]
    from cairn.tools.base.watchme_spec import armed_error
    refusal = armed_error(spec)
    assert refusal is None, f"the gate would refuse the WATCHME crossing: {refusal}"
    assert (REPO / spec["probe"]).resolve() == Path(probe.__file__).resolve(), \
        f"the probe is not where the ticket says: {spec['probe']}"
    assert spec["object"] == "reflection_earns_its_ask", spec["object"]


def test_the_probe_carries_BOTH_a_carry_and_an_enough():
    assert callable(probe.PROBE.carry), "no carry — the poke would say only that a line moved"
    assert callable(probe.PROBE.enough), "no enough — the spec named a stopping condition"
    assert callable(probe.PROBE.trigger)


def test_the_probe_is_FROZEN():
    try:
        probe.PROBE.to = "somewhere-else"
    except FrozenInstanceError:
        return
    raise AssertionError("the probe is mutable — a declaration that can be edited in flight")


# ------------------------------------------------- (1) a cache hit is not a second opinion

def test_a_CACHED_second_ask_does_not_count_as_a_reflected_drive():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        for i in range(5):
            a_reflected_drive(root, drives, index=i, cached=True)
        rows = probe.readings(drives_path=drives)
        assert all(r["num_reflections"] == 1 for r in rows), "the rows did not record reflections"
        assert probe._reflected(rows) == [], \
            "a reflected ask that never reached the host counted as a second opinion"
        assert probe._enough(ctx(drives)) is False, \
            "five cache hits retired the watch having learned nothing"


def test_the_carrier_reports_the_per_ask_counts_so_a_reader_can_check_the_split():
    """The spec names `each ask's prompt_eval_count` — a derived boolean would make the
    cached/live split unauditable by anyone reading the poke."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, cached=True)
        row = probe._carry(ctx(drives))["rows"][0]
        assert row["prompt_eval_counts"][1] is None, row["prompt_eval_counts"]
        assert row["cached_asks"] == 1, row


# ------------------------------------------------- (2) the one-sided carriage check

def test_a_second_ask_TOO_SMALL_to_hold_the_failure_text_is_measured_as_no():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, grows=False, passed=False)
        row = probe.readings(drives_path=drives)[0]
        assert row["second_ask_carriage"] == "no", row["second_ask_carriage"]


def test_a_second_ask_BIG_ENOUGH_is_consistent_and_is_NEVER_called_carried():
    """The length bound cannot prove containment, and the word must not claim it does."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, grows=True, passed=False)
        row = probe.readings(drives_path=drives)[0]
        assert row["second_ask_carriage"] == "consistent", row["second_ask_carriage"]
    body = json.dumps(probe._carry({"drives_path": None}), default=str)
    assert '"carried"' not in body, "the probe claims carriage it cannot measure"


def test_a_PASSING_reflected_drive_has_NO_carriage_question_rather_than_a_green_one():
    """No failure text exists, so `consistent` would be an answer to a question nobody asked —
    and it would pad the denominator with drives that could never have falsified anything."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, passed=True, edited=["a.py"])
        assert probe.readings(drives_path=drives)[0]["second_ask_carriage"] is None


def test_an_UNREFLECTED_drive_has_no_carriage_question():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, passed=False)
        assert probe.readings(drives_path=drives)[0]["second_ask_carriage"] is None


def test_the_carriage_hole_is_NAMED_and_points_at_where_it_IS_measured():
    holes = probe._carry({"drives_path": None})["holes"]
    assert "one-sided" in holes["second_ask_carriage"]
    assert "test_the_second_ask_carries_the_tests_own_failure" in holes["second_ask_carriage"], \
        "the hole is named but the reader is not told where the real measurement lives"


# ------------------------------------------------- (3) the stop-early falsifiers

def test_a_reflected_drive_that_ends_CHANGED_AND_FAILING_fires_the_falsifier():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, passed=False, edited=["a.py"], moved=True)
        carry = probe._carry(ctx(drives))
        which = [f["which"] for f in carry["falsifications"]]
        assert "ended-worse-shoulder" in which, carry["falsifications"]
        assert carry["stop_early"] is True


def test_the_ended_worse_falsifier_ADMITS_it_over_fires():
    """A superset alarm reported as a proof is how a watch spends the consumer's trust."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, passed=False, edited=["a.py"])
        f = [x for x in probe._carry(ctx(drives))["falsifications"]
             if x["which"] == "ended-worse-shoulder"][0]
        assert f["over_fires"], "the alarm claims to be a measurement of the spec's state"


def test_a_reflected_drive_that_APPLIED_NOTHING_does_not_fire_the_ended_worse_falsifier():
    """`no-edit` and `left-changed-and-failing` call for opposite decisions: the apprentice is
    not producing, versus the apprentice is producing harm."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, passed=False, edited=[], moved=False)
        rows = probe.readings(drives_path=drives)
        assert rows[0]["outcome"] == "no-edit", rows[0]["outcome"]
        assert [f for f in probe.falsifications(rows)
                if f["which"] == "ended-worse-shoulder"] == []


def test_an_UNREFLECTED_failing_drive_does_not_fire_the_ended_worse_falsifier():
    """The baseline is full of these. Firing on them would report the pre-existing failure
    rate as harm the reflection loop caused."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, passed=False, edited=["a.py"])
        assert probe.falsifications(probe.readings(drives_path=drives)) == []


def test_the_carriage_falsifier_fires_and_is_NOT_marked_over_firing():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, grows=False, passed=False, edited=[], moved=False)
        f = [x for x in probe._carry(ctx(drives))["falsifications"]
             if x["which"] == "failure-text-did-not-ride"]
        assert f, "a second ask too small to hold the failure text did not fire"
        assert f[0]["over_fires"] == "", "a measured falsifier is labelled as an alarm"


def test_the_falsifiers_speak_BEFORE_enough_is_satisfied():
    """A stop-EARLY signal that waits for the fifth drive is not a stop-early signal."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, passed=False, edited=["a.py"])
        carry = probe._carry(ctx(drives))
        assert probe._enough(ctx(drives)) is False
        assert carry["stop_early"] is True and carry["falsifications"]


# ------------------------------------------------- the stopping condition

def test_an_EMPTY_record_store_is_not_enough_and_is_not_an_error():
    with tempfile.TemporaryDirectory() as tmp:
        drives = Path(tmp) / "drives.jsonl"
        assert probe.readings(drives_path=drives) == []
        assert probe._enough(ctx(drives)) is False
        assert "not enough yet" in probe._carry(ctx(drives))["status"]


def test_enough_goes_TRUE_at_five_reflected_drives_and_FALSE_at_four():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        for i in range(4):
            a_reflected_drive(root, drives, index=i, passed=True, edited=["a.py"])
        assert probe._enough(ctx(drives)) is False, "four reflected drives satisfied a five"
        a_reflected_drive(root, drives, index=4, passed=True, edited=["a.py"])
        assert probe._enough(ctx(drives)) is True, "five reflected drives did not satisfy it"


def test_UNREFLECTED_drives_do_not_count_toward_the_five():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        for i in range(9):
            a_drive(root, drives, index=i, passed=True)
        assert probe._enough(ctx(drives)) is False, \
            "the baseline population retired a watch about reflection"


def test_ONE_drive_appended_TWICE_is_still_ONE_drive():
    """Observed at n=1 in the live store: four rows carry byte-identical `at` because a
    live-fire caller recorded a result `drive_brief` had already recorded."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        r = a_reflected_drive(root, drives, passed=True, edited=["a.py"])
        driver.record(r, path=drives)
        assert len(probe.readings(drives_path=drives)) == 1, "a duplicate row became a drive"


# ------------------------------------------------- the yield comparison

def test_the_yield_splits_reflected_from_baseline_over_ONE_population():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, index=0, passed=True, edited=["a.py"])
        a_reflected_drive(root, drives, index=1, passed=False, edited=["a.py"])
        a_drive(root, drives, index=2, passed=True, edited=["a.py"])
        y = probe._carry(ctx(drives))["yield"]
        assert y["reflected"]["drives"] == 2 and y["reflected"]["applied_and_passing"] == 1
        assert y["unreflected_baseline"]["drives"] == 1
        assert y["reflected"]["rate"] == 0.5


def test_a_REFUSED_drive_lands_in_NEITHER_rate():
    """A drive nothing was heard on says nothing about reflection in either direction, and
    counting it as a failure would make the loop look worse than it is."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, index=0, passed=True, edited=["a.py"], error="THE DRIVE REACHED NO MODEL")
        y = probe._carry(ctx(drives))["yield"]
        assert y["unreflected_baseline"]["drives"] == 0, y
        assert y["unreflected_baseline"]["rate"] is None, "a rate was minted from nothing"


def test_the_probe_does_NOT_grade_the_yield():
    """Whether the difference is worth the tokens is Akien's call at triage; a probe that
    answered it would be exercising authority it does not have (Law 6)."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        for i in range(5):
            a_reflected_drive(root, drives, index=i, passed=True, edited=["a.py"])
        body = json.dumps(probe._carry(ctx(drives)), default=str).lower()
        for word in ("worth it", "verdict", "recommend", "should pull"):
            assert word not in body, f"the probe graded the yield: {word!r}"


# ------------------------------------------------- trigger and authority

def test_the_trigger_fires_on_a_NEW_drive_and_not_on_a_STANDING_one():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, index=0)
        assert probe._trigger(context=ctx(drives, seen=0)) is True
        assert probe._trigger(context=ctx(drives, seen=1)) is False
        a_drive(root, drives, index=1)
        assert probe._trigger(context=ctx(drives, seen=1)) is True


def test_running_the_probe_MOVES_NO_STATE():
    """A probe carries no authority (Law 6): it deposits and pokes, it does not write."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_reflected_drive(root, drives, passed=False, edited=["a.py"])
        before = {p: p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
        probe._trigger(context=ctx(drives))
        probe._carry(ctx(drives))
        probe._enough(ctx(drives))
        after = {p: p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
        assert before == after, "the probe wrote something — it has no authority to"


def _main():
    print(__doc__.splitlines()[0])
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            check(name, fn)
    if FAILURES:
        print(f"\nRED — {len(FAILURES)} failure(s): " + ", ".join(FAILURES))
        return 1
    print("\nGREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
