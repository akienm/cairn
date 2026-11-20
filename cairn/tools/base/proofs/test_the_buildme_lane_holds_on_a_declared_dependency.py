"""Proof for ticket bdd02e0ad010 — the BUILDME entry holds on a declared dependency.

Measured 2026-11-19: inspect_entry (cairn/tools/base/transitions.py) composes six lanes and none
reads a dependency on another ticket, so "BUILDME waits on X PROVED" in a ticket's how text (as for
86cccb7d30f7, a DECISIONS plan) holds nothing. 46 of the open plans are decisions plans, which have
no outcome `after`, so the lane reads the state's BUILDME `stage_needs` (both shapes can carry it)
as well as outcome `after`.

RED-FIRST. The proof drives ``transitions.inspect_entry(<id>)`` over scratch tickets (the store
patched to a scratch dir, the six existing sieves stubbed clean) and reads the lane named
``the_ticket_waits_on_nothing_unproved``. My labelled guesses, which the build may rename and must
then rename here: that lane name; a need entry carries an optional ``ticket`` (12-hex id) and is
met when that ticket's state workflow reads ``[PROVED``; a need without ``ticket`` is met by a
DONE latest mark. Today the lane does not exist, so every tooth fails.

1. a DECISIONS-plan ticket whose BUILDME need names an unproved ticket: the lane refuses, naming it;
2. the same ticket once that ticket reads PROVED: the lane passes;
3. a need with no `ticket` and no DONE mark refuses naming the need; with a DONE mark (when,
   how_measured) it passes;
4. a named id that resolves to no ticket (in a need or in an outcome `after`) refuses by name;
5. an OUTCOMES-plan ticket whose outcome `after` names an unproved ticket refuses; passes when PROVED;
6. a ticket declaring nothing passes, and one refusal names every unmet dependency at once.

    bin/cairn test cairn/tools/base/proofs/test_the_buildme_lane_holds_on_a_declared_dependency.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"bdd02e0ad010": {
    "1": "test_an_unproved_named_ticket_holds_a_decisions_plan",
    "2": "test_the_same_ticket_crosses_once_it_is_proved",
    "3": "test_an_unmarked_need_holds_and_a_done_mark_releases",
    "4": "test_an_unknown_id_is_held_by_name",
    "5": "test_an_outcome_after_holds_and_releases",
    "6": "test_nothing_declared_passes_and_one_refusal_names_every_unmet"}}

LANE = "the_ticket_waits_on_nothing_unproved"
OPEN = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
DONE = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]"
DEP, DEP2, WAITER, GHOST = "bdd0aaaa0001", "bdd0aaaa0002", "bdd0bbbb0001", "bdd0ffff0fff"
MARK = {"status": "DONE", "when": "2026-11-19", "how_measured": "ls known/akiendell.pem on the Dell"}
DECISIONS = [{"n": 1, "text": "D1: x", "writes_to": [], "reads": []}]
OUTCOMES = [{"n": 1, "claim": "x", "writes_to": [], "reads": []}]


class _Store:
    """A scratch ticket store the lane is driven over, the six existing sieves stubbed clean."""

    def __init__(self):
        from cairn.tools.base import ticket_file, transitions
        self.tf, self.tr = ticket_file, transitions
        self.dir = Path(tempfile.mkdtemp(prefix="bdd0-lane-"))
        self.saved = (ticket_file._TICKETS, transitions._judge)
        ticket_file._TICKETS = self.dir
        transitions._judge = lambda judge: (lambda *a, **k: [])

    def close(self):
        self.tf._TICKETS, self.tr._judge = self.saved

    def put(self, tid, *, workflow=OPEN, plan=None, needs=None):
        doc = {"id": tid, "title": "testing " + tid, **(plan or {"decisions": DECISIONS})}
        (self.dir / f"{tid}-testing.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        state = {"workflow_and_state": workflow, "node_class": "code-seam"}
        if needs is not None:
            state["stage_needs"] = {"BUILDME": needs}
        (self.dir / f"{tid}-testing.state.json").write_text(json.dumps(state, indent=2) + "\n",
                                                            encoding="utf-8")

    def lane(self, tid):
        rec = self.tr.inspect_entry(tid)
        hit = [e for e in rec if e["identity"] == LANE]
        assert hit, "inspect_entry has no lane %r: %s" % (LANE, [e["identity"] for e in rec])
        lane = hit[0]
        found = (lane.get("values") or {}).get("findings") or []
        return self.tr.gate.passed(lane), repr(found)


def _need(ticket=None, marks=None, text="waits on a thing"):
    entry = {"need": text, "marks": marks or []}
    if ticket:
        entry["ticket"] = ticket
    return entry


def test_an_unproved_named_ticket_holds_a_decisions_plan():
    s = _Store()
    try:
        s.put(DEP)
        s.put(WAITER, needs=[_need(DEP, text="tester exec PROVED")])
        passed, found = s.lane(WAITER)
        assert not passed and DEP in found, "an unproved %s holds the waiter, naming it: %s" % (DEP, found)
    finally:
        s.close()


def test_the_same_ticket_crosses_once_it_is_proved():
    s = _Store()
    try:
        s.put(DEP, workflow=DONE)
        s.put(WAITER, needs=[_need(DEP, text="tester exec PROVED")])
        passed, found = s.lane(WAITER)
        assert passed, "a PROVED %s releases the waiter: %s" % (DEP, found)
    finally:
        s.close()


def test_an_unmarked_need_holds_and_a_done_mark_releases():
    s = _Store()
    try:
        s.put(WAITER, needs=[_need(text="akiendell pinned to the Dell")])
        passed, found = s.lane(WAITER)
        assert not passed and "akiendell pinned" in found, "an unmarked need holds, named: %s" % found
        s.put(WAITER, needs=[_need(text="akiendell pinned to the Dell", marks=[MARK])])
        passed, found = s.lane(WAITER)
        assert passed, "a DONE mark with when and how_measured releases it: %s" % found
    finally:
        s.close()


def test_an_unknown_id_is_held_by_name():
    s = _Store()
    try:
        s.put(WAITER, needs=[_need(GHOST, text="a ticket that is not there")])
        passed, found = s.lane(WAITER)
        assert not passed and GHOST in found, "an unresolved need ticket is held by name: %s" % found
        s.put(WAITER, plan={"outcomes": [{**OUTCOMES[0], "after": [GHOST]}]})
        passed, found = s.lane(WAITER)
        assert not passed and GHOST in found, "an unresolved outcome after is held by name: %s" % found
    finally:
        s.close()


def test_an_outcome_after_holds_and_releases():
    s = _Store()
    try:
        s.put(DEP)
        s.put(WAITER, plan={"outcomes": [{**OUTCOMES[0], "after": [DEP]}]})
        passed, found = s.lane(WAITER)
        assert not passed and DEP in found, "an unproved outcome after holds, naming it: %s" % found
        s.put(DEP, workflow=DONE)
        passed, found = s.lane(WAITER)
        assert passed, "the PROVED after releases it: %s" % found
    finally:
        s.close()


def test_nothing_declared_passes_and_one_refusal_names_every_unmet():
    s = _Store()
    try:
        s.put(WAITER)
        passed, found = s.lane(WAITER)
        assert passed, "a ticket declaring nothing crosses as before: %s" % found
        s.put(DEP)
        s.put(DEP2)
        s.put(WAITER, needs=[_need(DEP, text="one"), _need(DEP2, text="two"), _need(text="three")])
        passed, found = s.lane(WAITER)
        assert not passed and DEP in found and DEP2 in found and "three" in found, \
            "one refusal names every unmet dependency: %s" % found
    finally:
        s.close()


def _main() -> int:
    checks = [test_an_unproved_named_ticket_holds_a_decisions_plan,
              test_the_same_ticket_crosses_once_it_is_proved,
              test_an_unmarked_need_holds_and_a_done_mark_releases,
              test_an_unknown_id_is_held_by_name,
              test_an_outcome_after_holds_and_releases,
              test_nothing_declared_passes_and_one_refusal_names_every_unmet]
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except AssertionError as exc:
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {exc}")
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed: {failed}")
        return 1
    print("green — the BUILDME entry holds on a declared dependency, both plan shapes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
