"""Proof for ticket 3a977523f644: the cast sweep and the casting-door probe read the artifact
TRAIL, not the index.

Since b15da5656579 the commons journal is an index holding only each path's newest entry, and
every entry lands in a day trail under this box's logs for 30 days. Akien, 2026-11-16: "the
latest entry remains in cairn commons, and everything else broken into... per day? per week?
inside of our .cairn/logs folder". Reading the index, ``sweep_casts`` classified a ticket by
its newest entry: a ticket cast through the door and written once more afterwards read
``journaled_beside``.

  1. a ticket whose first trail entry is the door's creation, and whose newest (the index's) is
     a later write, is classed through_the_door, read from the trail;
  2. a ticket the index names but the trail does not reads past_horizon; one neither names reads
     unjournaled;
  3. the_casting_door_has_callers counts every creation the trail holds, puts the
     index-only ticket in past_horizon and not in unjournaled, and its finding names the 30-day
     horizon.

Every clause runs in a scratch diagnostic world (set_diagnostic_roots with a "trail" key). The
index and trail lines are written there as plain files in the door's own shapes, so the readers
are measured over the formats b15d defined; no live journal, trail or commons is touched.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_the_cast_census_reads_the_artifact_trail.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {
    "3a977523f644": {
        "1": "test_a_ticket_is_classed_by_its_first_entry_in_the_trail",
        "2": "test_an_index_only_ticket_reads_past_horizon",
        "3": "test_the_probe_counts_the_trail_and_names_its_horizon",
    },
}

DOOR_FRAME = "cairn/tools/base/transitions.py:123:cast_ticket"
T_DOOR = "tickets/aaaaaaaaaaaa-cast-then-written.json"      # created by the door, written again later
T_OLD = "tickets/bbbbbbbbbbbb-cast-past-the-horizon.json"   # the index names it, the trail does not
T_HAND = "tickets/cccccccccccc-dropped-by-hand.json"        # nothing names it
DAYS = ("2026-11-10", "2026-11-12", "2026-11-14")
PASS = 0
FAIL = 0


def _entry(path, at, *, created, door):
    return {"path": path, "at": at, "verb": "cast", "sha_before": "absent" if created else "0" * 64,
            "sha_after": "1" * 64, "stack": [DOOR_FRAME] if door else ["somewhere.py:1:writer"]}


def _world():
    from cairn.tools.artifact import artifact as A
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = Path(scratch_dir("cairn-3a97-"))
    root = tmp / "CairnCommons"
    (root / "tickets").mkdir(parents=True)
    A.set_diagnostic_roots({"CairnCommons": root, "parked": tmp / "parked", "trail": tmp / "trail"})
    for rel in (T_DOOR, T_OLD, T_HAND):
        (root / rel).write_text(json.dumps({"id": rel[8:20]}) + "\n", encoding="utf-8")
    trail = [_entry(T_DOOR, f"{DAYS[0]}T10:00:00+00:00", created=True, door=True),
             _entry(T_DOOR, f"{DAYS[2]}T10:00:00+00:00", created=False, door=False)]
    for n, day in enumerate(DAYS):        # three more door casts, one per day, removed since
        trail.append(_entry(f"tickets/dddddddddd{n:02d}-gone.json", f"{day}T11:00:00+00:00",
                            created=True, door=True))
    index = [trail[1], _entry(T_OLD, "2026-09-01T10:00:00+00:00", created=True, door=True)]
    d = A.trail_dir("CairnCommons")
    d.mkdir(parents=True, exist_ok=True)
    for day in DAYS:
        rows = [e for e in trail if e["at"].startswith(day)]
        (d / f"{day}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in rows), encoding="utf-8")
    A.journal_path(root).write_text("".join(json.dumps(e) + "\n" for e in index), encoding="utf-8")
    return root, len([e for e in trail if e["sha_before"] == "absent"])


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {fn.__name__}")


def test_a_ticket_is_classed_by_its_first_entry_in_the_trail():
    from cairn.tools.base.cast import sweep_casts
    root, _ = _world()
    got = sweep_casts(root)["tickets"]
    assert got.get(T_DOOR) == "through_the_door", f"{T_DOOR} read {got.get(T_DOOR)!r}: {got}"


def test_an_index_only_ticket_reads_past_horizon():
    from cairn.tools.base.cast import sweep_casts
    root, _ = _world()
    s = sweep_casts(root)
    got = s["tickets"]
    assert got.get(T_OLD) == "past_horizon", f"{T_OLD} read {got.get(T_OLD)!r}"
    assert got.get(T_HAND) == "unjournaled", f"{T_HAND} read {got.get(T_HAND)!r}"
    assert s["counts"].get("past_horizon") == 1, f"counts {s['counts']}"


def test_the_probe_counts_the_trail_and_names_its_horizon():
    from cairn.tools.base.probes import the_casting_door_has_callers as P
    root, creations = _world()
    s = P.survey_the_casts(root)
    assert s["arrivals"] == creations, f"arrivals {s['arrivals']} != the trail's {creations} creations: {s}"
    assert s["unjournaled"] == [T_HAND], f"unjournaled {s['unjournaled']}"
    assert s["past_horizon"] == 1, f"past_horizon {s.get('past_horizon')}"
    finding = P._carry({"roots": {"commons": str(root)}})["finding"]
    assert "30 days" in finding, f"the finding does not name its horizon: {finding!r}"


TEETH = [test_a_ticket_is_classed_by_its_first_entry_in_the_trail,
         test_an_index_only_ticket_reads_past_horizon,
         test_the_probe_counts_the_trail_and_names_its_horizon]

if __name__ == "__main__":
    from cairn.tools.artifact import artifact as _A
    try:
        for fn in TEETH:
            _tooth(fn)
    finally:
        _A.set_diagnostic_roots(None)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
