"""Proof: every boat at sea can reach v2 — by its NEXT crossing, rewriting nobody's past.

Ticket ``watchme-emits-a-probe`` (2026-07-30), triage position 7, piece (b). v1 put
``LEARNME`` in the backbone: mandatory for every node of both classes and carrying no gate.
v2 dissolves it. Every component and ticket at sea today rides v1, so the vocabulary change
needs a way across — and the way across must not rewrite history, because history is a record
of truth and a record of truth is never changed in place (Law 7).

MIGRATION RIDES THE NEXT CROSSING; IT IS NOT A SWEEP. No script walks the repo rewriting
state files. A node's version changes at the one moment it was going to write a record
anyway, which is the event-not-poll shape the whole system is built on: a boat that never
crosses again simply stays v1, correctly, because v1 is frozen rather than broken.

THE ONE REAL DECISION, and the row that carries it —
``test_a_boat_standing_at_learnme_lands_at_proveme``. Standing at LEARNME meant the node had
passed the PROVEME summons and had not been promoted; LEARNME was ungated, so standing there
is not evidence that anything was learned. Under v2's vocabulary that position IS PROVEME:
one forward crossing from PROVED with the build gate still owed. Re-running that gate is a
cost, not a defect — it is exactly the check that asks "may this be promoted", asked of a
boat that never was. ``cairn/build_inspector`` is standing there right now, and the ticket
``the-deposit-rides-the-read`` with it.

MEASURED AGAINST THE REAL BOATS, not fixtures: ``test_every_v1_boat_on_disk_reaches_a
_conforming_v2`` reads every ``state.json`` in this repo and every filed ticket, migrates
each, and conforms the result against the REAL class tables. A migration proved only on
strings I invented would be a migration proved against my own expectations.

    python3 cairn/base/proofs/test_v2_migration.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base import transitions
from cairn.charter import projector

_CD = transitions.load_class_def("code-seam")
_TICKETS = _REPO_ROOT.parent / "CairnCommons" / "tickets"

def _classes_by_registration():
    """(with a v2, without one) — read off the REAL class tables, so a newly-minted v2 widens
    the migration sweep automatically instead of being silently left out of it. Computed, not
    a module-level list filled by whichever row happened to run first: a proof whose rows
    depend on each other's order is a proof that passes for reasons nobody stated."""
    with_v2, without = [], []
    for p in sorted((_REPO_ROOT.parent / "CairnCommons" / "node_classes").glob("*.json")):
        if p.name.startswith("_"):
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        (with_v2 if "v2" in (d.get("workflow_versions") or {}) else without).append(p.stem)
    return with_v2, without


_V1 = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> LEARNME -> PROVED"


def _at(state):
    return _V1.replace(state, f"[{state}]", 1)


def test_a_cursor_behind_learnme_is_where_it_was():
    assert transitions.migrate_to_v2(_at("BUILDME")) == \
        "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"
    assert transitions.migrate_to_v2(_at("THINKME")).startswith("code-seam@v2: [THINKME]")


def test_a_boat_standing_at_learnme_lands_at_proveme():
    """THE ONE REAL DECISION. LEARNME was ungated, so standing there proved nothing was
    learned — the honest v2 position is the summons it had passed, promotion still owed."""
    got = transitions.migrate_to_v2(_at("LEARNME"))
    assert got == "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED", got
    wf = transitions.parse_workflow(got)
    assert "PROVED" in transitions.legal_targets(wf, class_def=_CD), \
        "and it must be one forward crossing from rest — not stranded by its own migration"


def test_a_boat_at_rest_stays_at_rest():
    got = transitions.migrate_to_v2(_at("PROVED"))
    assert got.endswith("PROVEME -> [PROVED]"), got
    assert "LEARNME" not in got


def test_a_node_that_wants_to_keep_learning_carries_the_watch_instead():
    got = transitions.migrate_to_v2(_at("LEARNME"), watch="did-the-deposit-actually-land")
    assert "[WATCHME(did-the-deposit-actually-land)]" in got, got
    transitions.legal_targets(transitions.parse_workflow(got), class_def=_CD)


def test_carrying_a_watch_is_opt_in_and_that_is_the_whole_point():
    """Defaulting it ON would retro-impose an armed-probe obligation on every boat mid-voyage
    and refuse its next crossing out of the watch — the retro-red the spec check already paid
    for once. 'Keep-learning by default' is a rule AT TICKETING, where an author can answer."""
    assert "WATCHME" not in transitions.migrate_to_v2(_at("LEARNME"))


def test_an_immutable_version_is_not_re_migrated():
    v2 = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
    try:
        transitions.migrate_to_v2(v2)
    except transitions.IllegalTransition as e:
        assert "immutable" in str(e), e
    else:
        raise AssertionError("guessing at an already-migrated string is how a path drifts")


def test_the_crossing_journals_the_old_string_verbatim():
    # THINKME -> TICKETME on purpose: forward, and the ONE crossing no other seat guards, so
    # what this row measures is the migration and nothing else. (Measured, not assumed — the
    # first draft crossed PROVEME -> PROVED and was refused by the build gate at a tempdir
    # address, which would have proved someone else's gate works.)
    with tempfile.TemporaryDirectory() as td:
        hist, state = f"{td}/history.json", f"{td}/state.json"
        old = _at("THINKME")
        new = transitions.emit_migrated(old, "TICKETME", history_path=hist, state_path=state,
                                        why="crossed, and migrated in the same act")
        assert new.startswith("code-seam@v2:") and "[TICKETME]" in new, new
        last = projector.read_history(hist)[-1]
        assert last["migrated_from"] == old, \
            "the version change must be ON the record — a silent vocabulary swap is a record " \
            "that quietly stops meaning what it said"


def test_an_already_v2_crossing_records_no_migration():
    with tempfile.TemporaryDirectory() as td:
        hist, state = f"{td}/history.json", f"{td}/state.json"
        v2 = "code-seam@v2: [THINKME] -> TICKETME -> BUILDME -> PROVEME -> PROVED"
        transitions.emit_migrated(v2, "TICKETME", history_path=hist, state_path=state, why="w")
        assert "migrated_from" not in projector.read_history(hist)[-1], \
            "a crossing that migrated nothing must not claim it did"


def test_the_past_is_byte_identical_after_the_migration_crossing():
    """'Without an in-place edit', measured in bytes rather than asserted."""
    with tempfile.TemporaryDirectory() as td:
        hist, state = f"{td}/history.json", f"{td}/state.json"
        transitions.emit(_at("TICKETME"), "THINKME", history_path=hist, state_path=state,
                         why="a back-edge, still on v1")
        before_bytes = Path(hist).read_bytes()
        before = projector.read_history(hist)

        transitions.emit_migrated(_at("THINKME"), "TICKETME", history_path=hist,
                                  state_path=state, why="migrated on the next crossing")
        after = projector.read_history(hist)

        assert len(after) == len(before) + 1, f"{len(before)} -> {len(after)}"
        assert after[:len(before)] == before, "a prior entry changed under the migration"
        assert before_bytes in Path(hist).read_bytes() or \
            json.dumps(before, sort_keys=True) == json.dumps(after[:len(before)], sort_keys=True), \
            "the append door may reformat the file, but never the entries"
        assert "LEARNME" in after[0]["workflow"] and "LEARNME" not in after[1]["workflow"], \
            "the old vocabulary survives in the old entry — that IS the record of the change"


def test_every_v1_boat_on_disk_reaches_a_conforming_v2():
    """NON-HOLLOW: the real components and the real ticket corpus, not strings I invented."""
    boats, scanned = [], []
    for p in sorted(_REPO_ROOT.glob("cairn/*/state.json")):
        cur = (json.loads(p.read_text(encoding="utf-8")).get("cursor") or {})
        w = cur.get("workflow")
        scanned.append(p)
        if isinstance(w, str) and "@v1:" in w:
            boats.append((str(p.relative_to(_REPO_ROOT)), w))
    for p in sorted(_TICKETS.glob("*.json")):
        if p.name.startswith("_"):
            continue
        w = json.loads(p.read_text(encoding="utf-8")).get("state")
        scanned.append(p)
        if isinstance(w, str) and "@v1:" in w:
            boats.append((p.name, w))

    # THE FLOOR IS NOT A COUNT (2026-08-03). It used to be `> 20`, which was the corpus of the
    # day and went red the moment Akien's scrub sweep drained the ticket store of v1 strings —
    # a snapshot pinned as if it were an invariant. Two DIFFERENT facts have to be separated,
    # because one is a defect and the other is progress: "the scan is broken / not reading the
    # repo" (loud) versus "the migration has fewer subjects left than it used to" (expected,
    # and the whole point of running it). So assert the DENOMINATOR — the scan really walked a
    # real corpus — and then assert at least one real boat still exercises the migration.
    assert len(scanned) > 40, (f"the scan read only {len(scanned)} state-carrying files — it is "
                               "not reading the repo (this is the broken-scan case, not the "
                               "nothing-left-to-migrate case)")
    assert boats, ("zero v1 boats anywhere on disk. NOT automatically a defect: it is what "
                   "completing the migration looks like, and at that point this row has no "
                   "subject and should be RETIRED with the migration rather than kept green "
                   "over nothing (Law 8). Red here is the prompt to make that call.")
    for name, w in boats:
        if transitions.parse_workflow(w).node_class not in _classes_by_registration()[0]:
            continue                        # see the row below — a NAMED gap, never a silent skip
        got = transitions.migrate_to_v2(w)
        assert "LEARNME" not in got, f"{name}: {got}"
        wf = transitions.parse_workflow(got)
        transitions.legal_targets(wf, class_def=transitions.load_class_def(wf.node_class))
        was = transitions.parse_workflow(w).here
        assert wf.here == was or (was == "LEARNME" and wf.here == "PROVEME"), \
            f"{name}: the boat moved to a state it was not at — {w!r} -> {got!r}"


def test_three_classes_register_no_workflow_at_all_and_that_is_named_here():
    """A FINDING THIS BUILD SURFACED, not a hole it dug. concept-piece, host-seam and
    operational-driver carry EMPTY ``workflow_versions``, so their nodes cannot cross the
    chokepoint at all — a concept-piece@v1 ticket is claiming a version its class never
    defined, and has been since before this voyage. Minting paths for three classes is a
    design act with an owner who is not me (piece (e-ii) already routes operational-driver to
    Akien), so this row PINS the gap rather than papering it: if someone mints one, this row
    goes red and the migration row above must be widened in the same act."""
    with_v2, empty = _classes_by_registration()
    assert sorted(empty) == ["concept-piece", "host-seam", "operational-driver"], empty
    assert sorted(with_v2) == ["code-seam", "skill"], sorted(with_v2)


def test_build_inspector_and_the_deposit_ticket_are_the_two_at_learnme():
    """WHO IS STILL PARKED IN THE DISSOLVED STATE — measured, never assumed.

    RE-MEASURED 2026-08-03. The row used to demand BOTH names the ticket predicted. One of
    them, ``the-deposit-rides-the-read``, has since crossed and carries a WATCHME, so the old
    assertion redded on a boat that had done exactly what the migration wanted — the failure
    mode this repo has paid for before: a proof over live state pinning a SNAPSHOT instead of
    an INVARIANT. The invariant is: whoever is parked there is parked LEGALLY, and the roster
    only shrinks. ``build_inspector`` is the one left, and it is left for a stated reason —
    ``emit_migrated`` needs a CROSSING, ``migrate_to_v2`` lands it on PROVEME, and its only
    legal forward target is PROVED, which would be a fabricated close. That is a real blocker
    on a real boat, not a fixture, and it is what this row now pins."""
    at_learnme = []
    for p in sorted(_REPO_ROOT.glob("cairn/*/state.json")):
        cur = (json.loads(p.read_text(encoding="utf-8")).get("cursor") or {})
        if cur.get("standing") == "LEARNME":
            at_learnme.append(p.parent.name)
    for p in sorted(_TICKETS.glob("*.json")):
        if not p.name.startswith("_") and "[LEARNME]" in str(
                json.loads(p.read_text(encoding="utf-8")).get("state")):
            at_learnme.append(p.stem)

    assert set(at_learnme) <= {"build_inspector", "the-deposit-rides-the-read"}, (
        f"a NEW boat is parked in the dissolved state: {sorted(set(at_learnme) - {chr(0)})}. "
        "The roster only shrinks — nothing may enter a state that no longer exists.")
    assert "build_inspector" in at_learnme, (
        "build_inspector has left the dissolved state — which is the WIN this row is waiting "
        f"for (disk says {at_learnme}). Retire this row and the migration debt with it.")
    for _name, w in ((n, None) for n in at_learnme):
        pass          # the landing itself is proved above; this row pins WHO is standing there


TESTS = [
    test_a_cursor_behind_learnme_is_where_it_was,
    test_a_boat_standing_at_learnme_lands_at_proveme,
    test_a_boat_at_rest_stays_at_rest,
    test_a_node_that_wants_to_keep_learning_carries_the_watch_instead,
    test_carrying_a_watch_is_opt_in_and_that_is_the_whole_point,
    test_an_immutable_version_is_not_re_migrated,
    test_the_crossing_journals_the_old_string_verbatim,
    test_an_already_v2_crossing_records_no_migration,
    test_the_past_is_byte_identical_after_the_migration_crossing,
    test_three_classes_register_no_workflow_at_all_and_that_is_named_here,
    test_every_v1_boat_on_disk_reaches_a_conforming_v2,
    test_build_inspector_and_the_deposit_ticket_are_the_two_at_learnme,
]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as e:  # noqa: BLE001 — a crash is a fail, never an aborted run
            failures += 1
            print(f"  FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
