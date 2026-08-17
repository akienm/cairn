#!/usr/bin/env python3
"""Teeth for the edit-survival probe. The claim under test is that this watch can tell
WHO EARNED THE GREEN — the apprentice, or the hand that rewrote its work.

A probe is the one artifact in a voyage whose failure is silent by construction: it is
armed, nothing in this build fires it, and every check you can run is a check on a
declaration. So the teeth are aimed at the ways this particular declaration could lie:

  (1) IT CANNOT TELL THE FOUR STATES APART. `survived`, `rewritten`, `discarded` and
      `not-applied` are four different decisions for the consumer, and three of them are
      easy to collapse into one another. A probe that reports a drive which produced
      NOTHING as a drive whose work was DISCARDED is telling Akien to pull the offload
      back for a reason that never happened.
  (2) IT COLLAPSES A MIXTURE. Two files survived and two rewritten reported as
      "survived" makes an offload look better than it is — the exact direction a
      measurement must never be wrong in (Law 7: a record of truth never collapses).
  (3) ITS STOPPING CONDITION IS SATISFIABLE BY LESS THAN IT ASKED FOR. Five drives that
      all applied nothing would retire this watch having learned nothing about survival.

EVERY FIXTURE GOES THROUGH THE WRITER. The records here are built as real `DriveResult`s
and written by `driver.record` — the one hand that mints a drive row — and the survival
answers come from `driver.survival`. Hand-writing the row shape here is exactly the defect
that put seventeen green teeth on top of a probe reading a key the door had never written:
a fixture that agrees with the READER instead of the WRITER proves only that the two agree
with each other.

No instance-space is read or written: the drives path and the comparison root are both
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
from cairn.devices.aider_shim.probes import edit_survival_probe as probe  # noqa: E402

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


def a_drive(root: Path, drives: Path, *, files: dict, edits: dict, index=0,
            ticket="aider-builds-a-piece"):
    """Write `files`, image them, apply `edits`, image again — and record it THROUGH THE
    DRIVER'S OWN WRITER. `edits` maps a relative path to its post-drive content; a path
    absent from `edits` is one the drive left alone.

    The before/after images are taken by `driver.image_of`, so the row carries exactly the
    shape a real drive carries. Nothing here knows what a drive record looks like.
    """
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    rels = list(files)
    before = driver.image_of(rels, root)
    for rel, text in edits.items():
        (root / rel).write_text(text, encoding="utf-8")
    after = driver.image_of(rels, root)
    r = driver.DriveResult(
        ticket=ticket, piece_index=index, model="qwen3-coder:30b",
        at=f"2026-08-17T00:00:0{index}+00:00", files=rels,
        before=before, after=after, aider_reported_edited=list(edits),
    )
    driver.record(r, path=drives)
    return r


def ctx(drives: Path, root: Path, **more):
    return {"drives_path": drives, "root": root, **more}


# ------------------------------------------------- the declaration itself

def test_the_probe_is_armed_at_the_path_the_TICKET_names():
    """The emission gate resolves ARMED from the ticket's spec, so the path IS the contract.

    ASKED THE WAY THE GATE ASKS IT, and that is a scar one seal deep. The first version
    did `Path(spec["probe"]).resolve()`, which resolves a relative berth against the
    CURRENT WORKING DIRECTORY — green bare, red under the netns seal, and green again for
    the sibling probe only because that ticket happens to spell its berth absolutely. The
    gate never uses cwd: it joins the berth to the repo root. So this calls `armed_error`
    itself rather than re-deriving what it does, which also means a tooth that cannot go
    green while the gate would refuse the crossing.
    """
    spec = json.loads((Path.home() / "dev/src/CairnCommons/tickets/aider-builds-a-piece.json")
                      .read_text(encoding="utf-8"))["watchme"]
    from cairn.tools.base.watchme_spec import armed_error
    refusal = armed_error(spec)
    assert refusal is None, f"the gate would refuse the WATCHME crossing: {refusal}"
    assert (REPO / spec["probe"]).resolve() == Path(probe.__file__).resolve(), \
        f"the probe is not where the ticket says: {spec['probe']}"
    assert spec["object"] == "aider_shim_edit_survival", spec["object"]


def test_the_probe_carries_BOTH_a_carry_and_an_enough():
    """The gate demands both. A watch with no carry pokes with nothing to read; one with no
    enough is a standing watch, which is legal in general and NOT what this spec declared."""
    assert callable(probe.PROBE.carry), "no carry — the poke would say only that a line moved"
    assert callable(probe.PROBE.enough), "no enough — the spec named a stopping condition"
    assert callable(probe.PROBE.trigger)


def test_the_probe_is_FROZEN():
    try:
        probe.PROBE.to = "somewhere-else"
    except FrozenInstanceError:
        return
    raise AssertionError("the probe is mutable — a declaration that can be edited in flight")


# ------------------------------------------------- can it tell the four states apart?

def test_an_edit_LEFT_ALONE_is_survived():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, files={"a.py": "before\n"}, edits={"a.py": "after\n"})
        rows = probe.dispositions(drives_path=drives, root=root)
        assert rows[0]["per_file"] == {"a.py": "survived"}, rows[0]
        assert rows[0]["disposition"] == "survived", rows[0]


def test_an_edit_PUT_BACK_is_discarded_not_survived():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, files={"a.py": "before\n"}, edits={"a.py": "after\n"})
        (root / "a.py").write_text("before\n", encoding="utf-8")   # the hand reverts it
        rows = probe.dispositions(drives_path=drives, root=root)
        assert rows[0]["disposition"] == "discarded", rows[0]


def test_an_edit_MOVED_AGAIN_is_rewritten():
    """The one the consumer most needs: the apprentice's line is gone, replaced by a third
    thing. A green earned here was earned by whoever wrote the third thing."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, files={"a.py": "before\n"}, edits={"a.py": "after\n"})
        (root / "a.py").write_text("a third thing\n", encoding="utf-8")
        rows = probe.dispositions(drives_path=drives, root=root)
        assert rows[0]["disposition"] == "rewritten", rows[0]


def test_a_drive_that_APPLIED_NOTHING_is_not_reported_as_discarded():
    """THE COLLAPSE THAT WOULD SEND THE WRONG DECISION. `not-applied` says the apprentice
    produced nothing; `discarded` says it produced something and was overruled. Those call
    for opposite moves, and the live fire made this the common case, not the exotic one."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, files={"a.py": "before\n"}, edits={})
        rows = probe.dispositions(drives_path=drives, root=root)
        assert rows[0]["per_file"] == {"a.py": "not-applied"}, rows[0]
        assert rows[0]["disposition"] == "not-applied", rows[0]


def test_a_MIXTURE_is_reported_as_mixed_and_carries_every_file():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives,
                files={"a.py": "before\n", "b.py": "before\n", "c.py": "before\n"},
                edits={"a.py": "after\n", "b.py": "after\n", "c.py": "after\n"})
        (root / "b.py").write_text("before\n", encoding="utf-8")        # discarded
        (root / "c.py").write_text("a third thing\n", encoding="utf-8")  # rewritten
        row = probe.dispositions(drives_path=drives, root=root)[0]
        assert row["disposition"] == "mixed", row
        assert row["per_file"] == {"a.py": "survived", "b.py": "discarded",
                                   "c.py": "rewritten"}, row["per_file"]


def test_the_vocabulary_is_a_TRANSLATION_of_the_drivers_and_covers_all_four():
    """Bound to the PRODUCER's words, not to a remembered list. If `driver.survival` ever
    grows a fifth answer, this reds instead of the probe silently passing it through."""
    import inspect
    src = inspect.getsource(driver.survival)
    for word in ("untouched", "survived", "reverted", "changed_again"):
        assert f'"{word}"' in src, f"the driver no longer says {word!r}"
        assert word in probe._SPEAK, f"the probe cannot translate the driver's {word!r}"
    assert set(probe._SPEAK) == {"untouched", "survived", "reverted", "changed_again"}, \
        f"the probe translates words the driver does not say: {set(probe._SPEAK)}"


# ------------------------------------------------- the population and the stop

def test_an_EMPTY_record_store_is_not_enough_and_is_not_an_error():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"   # never written
        assert probe.dispositions(drives_path=drives, root=root) == []
        assert probe._enough(ctx(drives, root)) is False
        carried = probe._carry(ctx(drives, root))
        assert carried["drives"] == 0 and carried["with_survival"] == 0, carried


def test_FIVE_drives_that_applied_NOTHING_do_not_satisfy_enough():
    """The exact edit a future reader makes to unstick a watch: count the drives instead of
    the survivals. It retires the watch having learned nothing about survival."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        for i in range(5):
            a_drive(root, drives, files={f"f{i}.py": "before\n"}, edits={}, index=i)
        assert len(probe.dispositions(drives_path=drives, root=root)) == 5
        assert probe._enough(ctx(drives, root)) is False, \
            "enough went true on five drives that produced no edit at all"


def test_ONE_drive_appended_TWICE_is_still_ONE_drive():
    """Observed at n=1 the day this was built: a caller called `driver.record` on a result
    `drive_brief` had already recorded, and the real store carried two rows per drive.
    Both writes really happened — the log is append-only and its rows are true — so the
    collapse belongs here. Counting it twice would retire the watch one drive early."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        r = a_drive(root, drives, files={"a.py": "before\n"}, edits={"a.py": "after\n"})
        driver.record(r, path=drives)                      # the accidental second write
        assert len(driver.drives(drives)) == 2, "the fixture did not reproduce the double"
        rows = probe.dispositions(drives_path=drives, root=root)
        assert len(rows) == 1, f"one drive counted {len(rows)} times: {rows}"


def test_enough_goes_TRUE_at_five_recorded_survivals_and_FALSE_at_four():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        for i in range(4):
            a_drive(root, drives, files={f"f{i}.py": "before\n"},
                    edits={f"f{i}.py": "after\n"}, index=i)
        assert probe._enough(ctx(drives, root)) is False, "enough at four"
        a_drive(root, drives, files={"f4.py": "before\n"}, edits={"f4.py": "after\n"}, index=4)
        assert probe._enough(ctx(drives, root)) is True, "not enough at five"


def test_the_trigger_fires_on_a_NEW_disposition_and_not_on_a_standing_one():
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, files={"a.py": "before\n"}, edits={"a.py": "after\n"})
        assert probe._trigger(context=ctx(drives, root, seen=0)) is True
        assert probe._trigger(context=ctx(drives, root, seen=1)) is False, \
            "the trigger fires on a standing population — it would poke on every pulse"


def test_the_carrier_NAMES_the_state_it_compared_against():
    """The spec says 'at the PROVED commit' and this reads the working tree. The hole is
    declared rather than papered over, and the head is what makes it checkable."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, files={"a.py": "before\n"}, edits={"a.py": "after\n"})
        carried = probe._carry(ctx(drives, root))
        against = carried["compared_against"]
        assert against["root"] == str(root), against
        assert "hole" in against and "working tree" in against["hole"].lower(), against
        assert "head" in against, "the receiver cannot tell WHEN the reading was taken"
        assert carried["counts"] == {"survived": 1}, carried["counts"]


def test_running_the_probe_MOVES_NO_STATE():
    """A probe carries no authority (Law 6): it deposits and pokes, it does not write."""
    with tempfile.TemporaryDirectory() as tmp:
        root, drives = Path(tmp), Path(tmp) / "drives.jsonl"
        a_drive(root, drives, files={"a.py": "before\n"}, edits={"a.py": "after\n"})
        before = {p: p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
        probe._trigger(context=ctx(drives, root))
        probe._carry(ctx(drives, root))
        probe._enough(ctx(drives, root))
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
