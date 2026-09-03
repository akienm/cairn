#!/usr/bin/env python3
"""Teeth for the writes_to-is-where-it-landed probe. The claim under test is that this
watch can tell whether the DECLARED output address is where the work actually went.

A probe is the one artifact in a voyage whose failure is silent by construction: it is
armed, nothing in this build fires it, and every check you can run is a check on a
declaration. So the teeth are aimed at the ways THIS declaration could lie:

  (1) IT CANNOT SEE THE FOUNDING FAILURE. The n=1 that bore the ticket was `venv.py`
      declared and `driver.py` edited — two files in ONE folder. Any containment rule
      generous enough to call that inside would report the defect as a pass, which is the
      probe measuring itself green on the very case it exists for.
  (2) IT COLLAPSES A MIXTURE. Half the edits inside and half outside reported as either
      one is a record of truth rounding (Law 7), and it rounds in the direction that hides
      the finding.
  (3) IT COUNTS ROWS THAT SAY NOTHING. `unknowable` and `no-edit` are not evidence about
      the declaration; ten of them reaching `enough` is a hollow green (Law 8) — the watch
      retiring having learned nothing, while reporting that it learned enough.
  (4) IT COMPARES A DRIVE AGAINST A DECLARATION IT NEVER SAW. The berth that STANDS is not
      necessarily the berth the drive read. Reporting a re-chart as a disagreement would
      manufacture the ticket's own finding out of time passing.
  (5) ITS FAST ARM DOES NOT FIRE. The spec stops at the FIRST landed-outside, deliberately:
      ten agreeing drives are a weak confirmation and one disagreeing drive is a strong
      falsification. A probe that waited for ten either way would sit on the finding.

EVERY DRIVE FIXTURE GOES THROUGH THE WRITER. The rows are real `DriveResult`s written by
`driver.record` — the one hand that mints a drive row — so a tooth cannot pass by agreeing
with a reader about a shape the writer never produces.

THE BEFORE/AFTER IMAGES ARE DELIBERATELY EMPTY HERE, and that is not a thinned fixture:
this probe reads `files` and `aider_reported_edited` and nothing else off the row. Imaging
would mean writing into the real repo (the declared addresses are real repo-relative paths,
because `translate._files` resolves against the real REPO by construction), and a proof
that writes into class-space to test a reader is a worse fixture, not a better one. The
images are the SIBLING probe's evidence; its own teeth build them through `image_of`.

No instance-space is read or written: the drives path and the berths root are both
injected, which is also the honest test of whether the probe's seams are injectable at all.
"""

import json
import sys
import tempfile
import traceback
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.aider_shim import driver  # noqa: E402
from cairn.devices.aider_shim.probes import writes_to_is_where_it_landed_probe as probe  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
TICKET = "a-piece-names-where-its-output-lands"
FAILURES = []

#: Two real repo-relative paths IN ONE FOLDER — the founding failure's own shape, so tooth
#: (1) is exercised by the standing fixture rather than by one special-case tooth.
DECLARED = "cairn/devices/aider_shim/venv.py"
SIBLING = "cairn/devices/aider_shim/driver.py"


def check(name, fn):
    try:
        fn()
        print(f"  ok   {name}")
    except Exception:
        FAILURES.append(name)
        print(f"  FAIL {name}")
        traceback.print_exc()


def berths(root: Path, writes_to, *, stamp="20260817T120000") -> None:
    """A standing chain for TICKET with ONE ranked piece declaring `writes_to`.

    Only the two links `_declared` reads are berthed — decompose and triage — because that
    is the whole surface this probe touches. A fuller chain would be scaffolding that could
    drift from what the code reads.
    """
    packets = root / "chart" / "packets"
    packets.mkdir(parents=True, exist_ok=True)
    piece = {"what": "the piece", "why": "because", "kind": "build",
             "fills": ["an absence"], "uses": ["cairn/tools/base/probe.py"]}
    if writes_to is not None:
        piece["writes_to"] = list(writes_to)
    (packets / f"decompose-{stamp}-aaaaaaaaaaaa.json").write_text(json.dumps(
        {"ticket": TICKET, "sub_problems": [piece]}), encoding="utf-8")
    (packets / f"triage-{stamp}-aaaaaaaaaaaa.json").write_text(json.dumps(
        {"ticket": TICKET, "order": [{"what": "the piece", "why_now": "first"}]}),
        encoding="utf-8")


def a_drive(drives: Path, *, handed, edited, index=0, n=0) -> dict:
    """One drive row, minted by the driver's own writer.

    `handed` is what the brief opened for editing — repo-relative, exactly as the real
    `drive_brief` records it — and `edited` is what aider said it touched.
    """
    r = driver.DriveResult(
        ticket=TICKET, piece_index=index, model="qwen3-coder:30b",
        at=f"2026-08-17T00:00:{n:02d}+00:00",
        files=list(handed), aider_reported_edited=list(edited))
    return driver.record(r, path=drives)


def ctx(drives: Path, root: Path, **more):
    return {"drives_path": drives, "berths_root": root, "root": REPO, **more}


def one(drives: Path, root: Path) -> dict:
    rows = probe.readings(drives_path=drives, berths_root=root, root=REPO)
    assert len(rows) == 1, rows
    return rows[0]


# ------------------------------------------------- the declaration itself

def test_the_probe_is_armed_at_the_path_the_TICKET_names():
    """The emission gate resolves ARMED from the ticket's spec, so the path IS the contract.

    ASKED THE WAY THE GATE ASKS IT — `armed_error` itself, not a re-derivation of what it
    does, so this tooth cannot go green while the gate would refuse the crossing. (The
    sibling probe's teeth carry the scar that taught this: resolving the berth against the
    CURRENT WORKING DIRECTORY was green bare and red under the netns seal.)
    """
    spec = json.loads((Path.home() / "dev/src/CairnCommons/tickets" / f"{TICKET}.json")
                      .read_text(encoding="utf-8"))["watchme"]
    from cairn.tools.base.watchme_spec import armed_error
    refusal = armed_error(spec)
    assert refusal is None, f"the gate would refuse the WATCHME crossing: {refusal}"
    assert (REPO / spec["probe"]).resolve() == Path(probe.__file__).resolve(), \
        f"the probe is not where the ticket says: {spec['probe']}"
    assert spec["object"] == "piece_output_address", spec["object"]


def test_the_probe_carries_BOTH_a_carry_and_an_enough():
    """The gate demands both: no carry and the poke says only that a line moved; no enough
    and the watch never clears, which is the standing pulse-cost the discipline refuses."""
    assert callable(probe.PROBE.carry), "no carry — nothing would be gathered"
    assert callable(probe.PROBE.enough), "no enough — the spec named a stopping condition"
    assert callable(probe.PROBE.trigger)


def test_the_probe_is_FROZEN():
    try:
        probe.PROBE.to = "somewhere-else"
    except FrozenInstanceError:
        return
    raise AssertionError("the probe is mutable — a declaration that can be edited in flight")


# ------------------------------------------------- can it see the founding failure?

def test_an_edit_AT_THE_DECLARED_ADDRESS_is_landed_inside():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[DECLARED])
        r = one(root / "drives.jsonl", root)
        assert r["disposition"] == probe.INSIDE, r
        assert r["per_path"] == {DECLARED: probe.INSIDE}, r["per_path"]


def test_an_edit_AT_A_SIBLING_IN_THE_SAME_FOLDER_is_landed_outside():
    """THE FOUNDING n=1, REPLAYED: declared `venv.py`, edited `driver.py`.

    THE FALSIFIER IS THE POINT. This goes green only under an equality rule; any rule that
    treats a declared file's directory as a licence — a prefix test, a parent-dir test, a
    'same package' test — reports the defect that bore this whole ticket as a pass, and the
    watch would then confirm the field works by never being able to see it fail.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[SIBLING])
        r = one(root / "drives.jsonl", root)
        assert r["disposition"] == probe.OUTSIDE, r
        assert r["per_path"] == {SIBLING: probe.OUTSIDE}, r["per_path"]


def test_a_MIXTURE_is_carried_whole_and_never_rounded():
    """Law 7 at a record of truth: half-obeying a declaration is its own finding."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[DECLARED, SIBLING])
        r = one(root / "drives.jsonl", root)
        assert r["disposition"] == probe.MIXED, r
        assert r["per_path"] == {DECLARED: probe.INSIDE, SIBLING: probe.OUTSIDE}, r["per_path"]


def test_a_drive_that_edited_NOTHING_is_no_edit_not_landed_outside():
    """A drive that produced nothing says the apprentice is not producing; a drive that
    produced something elsewhere says the CHART was wrong. Collapsing the first into the
    second would report a dead drive as evidence that the declaration is decorative — and
    the six drives standing on the real store on the day this was armed are all in the
    first state, so the collapse would have manufactured a finding out of them."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[])
        r = one(root / "drives.jsonl", root)
        assert r["disposition"] == probe.NO_EDIT, r


# ------------------------------------------------- what it refuses to compare

def test_a_piece_with_NO_writes_to_is_unknowable_not_a_finding():
    """A drive predating the field is not evidence about the field.

    This is what excludes every pre-2026-08-17 drive WITH NO DATE CONSTANT anywhere in the
    module — the declaration simply is not there, and the row says so.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, None)
        a_drive(root / "drives.jsonl", handed=["cairn/tools/base/probe.py"], edited=[SIBLING])
        r = one(root / "drives.jsonl", root)
        assert r["disposition"] == probe.UNKNOWABLE, r
        assert "predates the field" in r["why_unknowable"], r["why_unknowable"]


def test_a_RE_CHARTED_declaration_is_unknowable_not_a_finding():
    """The drive read one declaration and another one stands now — compare them and the
    watch manufactures its own finding out of time passing.

    THE CHECK IS AN AGREEMENT ON DISK, not a clock: the standing `writes_to` is resolved
    through `translate._files` and matched against the `files` the record itself carries.
    A timestamp comparison could not do this job at all — the berth stamps are local time
    and the drive stamps are UTC, so it would be wrong by hours in a way nothing announces.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        # The drive was handed something else entirely: the berth moved under it.
        a_drive(root / "drives.jsonl", handed=["cairn/tools/base/probe.py"], edited=[SIBLING])
        r = one(root / "drives.jsonl", root)
        assert r["disposition"] == probe.UNKNOWABLE, r
        assert "not the one this drive read" in r["why_unknowable"], r["why_unknowable"]


def test_a_drive_appended_TWICE_is_still_ONE_drive():
    """`enough` is a count, and a store that gained a row by accident would retire this
    watch early. Measured at n=2 on the real store the day this was armed: eight rows,
    six drives."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        for _ in range(2):
            a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[DECLARED])
        rows = probe.readings(drives_path=root / "drives.jsonl", berths_root=root, root=REPO)
        assert len(rows) == 1, rows


# ------------------------------------------------- the stopping condition

def test_TEN_HOLLOW_ROWS_DO_NOT_SATISFY_enough():
    """The hollow green this `enough` was written to refuse (Law 8).

    Ten drives that edited nothing, and ten more against a berth carrying no declaration,
    say exactly nothing about whether `writes_to` describes the world. A count over all
    rows would retire the watch here, reporting that it had learned enough.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        for n in range(10):
            a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[], n=n)
        assert probe._enough(ctx(root / "drives.jsonl", root)) is False
        berths(root, None, stamp="20260817T130000")   # a later berth, no declaration
        for n in range(10, 20):
            a_drive(root / "drives.jsonl", handed=["cairn/tools/base/probe.py"],
                    edited=[SIBLING], n=n)
        rows = probe.readings(drives_path=root / "drives.jsonl", berths_root=root, root=REPO)
        assert probe._countable(rows) == [], probe._countable(rows)
        assert probe._enough(ctx(root / "drives.jsonl", root)) is False


def test_ONE_landed_outside_STOPS_THE_WATCH_IMMEDIATELY():
    """The asymmetric arm, and it is the arm that matters.

    Ten agreeing drives buy a weak confirmation; one drive whose edits all land elsewhere
    is a strong falsification — the declared address is not where the work goes and the
    field the door now REQUIRES is decorative. A watch that waited for ten either way would
    sit on that finding for nine more real tickets.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[SIBLING])
        assert probe._enough(ctx(root / "drives.jsonl", root)) is True


def test_NINE_agreeing_drives_are_NOT_enough_and_TEN_are():
    """The spec's number, unlowered — and read at both edges, because a check that only
    asserts the satisfied side goes green under `>= 9` and under `>= 1`."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        for n in range(9):
            a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[DECLARED], n=n)
        assert probe._enough(ctx(root / "drives.jsonl", root)) is False
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[DECLARED], n=9)
        assert probe._enough(ctx(root / "drives.jsonl", root)) is True


def test_the_trigger_pokes_ONLY_on_a_NEW_comparable_row():
    """Not a poll: the count rides context because a Probe is frozen and holds no state."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[DECLARED], n=0)
        assert probe._trigger(context=ctx(root / "drives.jsonl", root, seen=0)) is True
        assert probe._trigger(context=ctx(root / "drives.jsonl", root, seen=1)) is False
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[SIBLING], n=1)
        assert probe._trigger(context=ctx(root / "drives.jsonl", root, seen=1)) is True


def test_the_carrier_names_ITS_OWN_HOLE_and_counts_the_uncountable_separately():
    """Law 7 at a record of truth on its way to a decision: the reading that could not be
    made is reported as such, in the same object, rather than dropped into the total."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[DECLARED], n=0)
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[], n=1)
        a_drive(root / "drives.jsonl", handed=["cairn/tools/base/probe.py"], edited=[], n=2)
        c = probe._carry(ctx(root / "drives.jsonl", root))
        assert c["drives"] == 3 and c["countable"] == 1, c
        assert c["counts"] == {probe.INSIDE: 1, probe.NO_EDIT: 1, probe.UNKNOWABLE: 1}, c["counts"]
        assert "re-charted" in c["hole"], c["hole"]
        assert c["ticket"] == TICKET and c["object"] == "piece_output_address"


def test_the_probe_WRITES_NOTHING(mutates=None):
    """A probe carries no authority (Law 6). It reads drives.jsonl and the standing berths;
    the back-edge that re-opens a node is the owner's act, not this module's."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        berths(root, [DECLARED])
        a_drive(root / "drives.jsonl", handed=[DECLARED], edited=[SIBLING], n=0)
        before = {p: p.stat().st_mtime_ns for p in sorted(root.rglob("*")) if p.is_file()}
        probe.readings(drives_path=root / "drives.jsonl", berths_root=root, root=REPO)
        probe._carry(ctx(root / "drives.jsonl", root))
        probe._enough(ctx(root / "drives.jsonl", root))
        after = {p: p.stat().st_mtime_ns for p in sorted(root.rglob("*")) if p.is_file()}
        assert before == after, "the probe changed something it only had licence to read"


def main():
    print("aider_shim :: writes_to is where it landed")
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
