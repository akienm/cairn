"""A rehearsal pass whose reader never returns a tree is a RUN: it leaves a record and it counts.

Ticket ba4166fe51c4 (Akien, 2026-09-29: *"shouldn't a rehsersal pass be counted like a testing
pass?"* / *"then that should be standard practice?"*). Measured that day on cd8096f9eeca: two
passes refused with exit 2 wrote no record and did not count toward PASS_CAP — about twenty
minutes of runs the record says never happened (Law 7).

Every tooth runs over a SCRATCH commons handed to the artifact door; the reader is a stub that
always returns nothing, so no model is spent. Every output is marked testing: the scratch dir
names itself and is swept at exit.

Run:  cd ~/dev/src/cairn && bin/cairn test cairn/machines/rehearsal/proofs/test_a_failed_run_is_counted.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.machines.rehearsal import rehearsal as R          # noqa: E402
from cairn.tools.artifact import artifact as door             # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir           # noqa: E402

# The falsifier is one clause (proves_green), so it takes ONE key (clause 1, added by D22): its tooth is the record
# itself. The other three teeth pin the rest of that clause and run beside it in TEETH.
PROVES = {"ba4166fe51c4": {
    "1": "test_a_failed_pass_writes_a_ran_false_record_carrying_the_refusal",
    "2": "test_the_sieve_reds_a_runner_whose_failure_writes_nothing_and_greens_the_declared_ones",
}}
TEETH = [
    "test_a_failed_pass_writes_a_ran_false_record_carrying_the_refusal",
    "test_a_failed_pass_counts_toward_the_cap",
    "test_a_failed_pass_never_moves_the_tickets_rehearsal_pointer",
    "test_the_sieve_reds_a_runner_whose_failure_writes_nothing_and_greens_the_declared_ones",
]

TID = "ba41f00dfa11"
STEM = f"{TID}-testing-a-failed-run-is-counted"
TICKET = {
    "id": TID, "title": "testing: a failed run is counted", "intention": "testing fixture",
    "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PR",
    "decisions": [{"n": 1, "text": "D1 testing: build the widget", "by": "cc", "source": "cast"}],
    "questions": [],
}


class Nothing:
    """A reader that never returns a tree — every attempt is an instrument failure."""

    def __init__(self):
        self.calls = 0

    def __call__(self, text, schema_doc):
        self.calls += 1
        return None, {"model": "stub", "cost_usd": 0.001, "duration_ms": 1, "error": "testing: reader returned nothing"}


class World:
    def __init__(self):
        self.dir = scratch_dir("rehearsal-failed-run-testing-")
        self.commons = self.dir / "CairnCommons"
        self.cairn = self.dir / "cairn"
        for d in ("tickets", "rehearsals", "questions"):
            (self.commons / d).mkdir(parents=True)
        self.cairn.mkdir()
        (self.commons / "tickets" / "_charter+why.json").write_text(json.dumps({
            "plan_fields": ["id", "title", "intention", "workflow_and_state", "decisions", "questions"],
            "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}}) + "\n")
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.ticket.write_text(json.dumps(TICKET, indent=2) + "\n")
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def close(self):
        door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def kw(self):
        return dict(root=self.commons, berths_root=self.dir / "no-berths", repo=self.dir / "no-repo")

    def fail_once(self):
        """One pass with the always-failing reader. Before the build this raised; the raise is
        caught here so the tooth can say what the pass left behind instead of crashing."""
        try:
            return R.rehearse(TID, reader=Nothing(), **self.kw()), None
        except R.Refused as exc:
            return None, exc


def test_a_failed_pass_writes_a_ran_false_record_carrying_the_refusal():
    w = World()
    try:
        rec, raised = w.fail_once()
        recs = sorted((w.commons / "rehearsals").glob(f"{TID}-*.json"))
        assert raised is None, f"the pass raised past the catch: {raised!r}; records left: {[p.name for p in recs]}"
        assert len(recs) == 1, [p.name for p in recs]
        doc = json.loads(recs[0].read_text())
        assert doc["ran"] is False and doc["clean"] is False, doc
        assert "read 1" in doc["why"] and "attempts" in doc["why"], doc["why"]
        assert doc["gaps"] == [] and doc["reads"] == [] and doc["pass"] == 1, doc
        assert len(doc["meta"]["attempts"]) == R.RETRIES_PER_READ + 1, doc["meta"]
        assert doc["ticket_sha256_at_read"], doc
        assert rec["path"] == str(recs[0]) and rec["ran"] is False, rec
        assert [e["verb"] for e in door.read_journal(w.commons)] == ["rehearse"], "the record rides the door"
        print(f"ran:false record {recs[0].name}, why={doc['why'][:60]!r}")
    finally:
        w.close()


def test_a_failed_pass_counts_toward_the_cap():
    w = World()
    try:
        before = R.passes_since_clean(TID, root=w.commons)
        w.fail_once()
        after = R.passes_since_clean(TID, root=w.commons)
        assert (before, after) == (0, 1), (before, after)
        print(f"passes_since_clean {before} -> {after}")
    finally:
        w.close()


def test_a_failed_pass_never_moves_the_tickets_rehearsal_pointer():
    w = World()
    try:
        bytes_before = w.ticket.read_bytes()
        rec, _ = w.fail_once()
        from cairn.tools.base.ticket_log import read_log
        pointers = read_log(w.ticket, "rehearsal")
        assert rec is not None, "the pass left no record to test the pointer against"
        assert pointers == [] and w.ticket.read_bytes() == bytes_before, (pointers,)
        assert R.standing(TID, root=w.commons)["ok"] is False, R.standing(TID, root=w.commons)
        print("pointer unmoved; ticket bytes unchanged")
    finally:
        w.close()


def test_the_sieve_reds_a_runner_whose_failure_writes_nothing_and_greens_the_declared_ones():
    from cairn.machines.build_inspector import inspector as I
    sieve = I.SIEVES.get("a_run_that_fails_to_run_leaves_a_trail")
    assert sieve is not None, "no sieve a_run_that_fails_to_run_leaves_a_trail in build_inspector"
    declared = I.declared_runners()
    names = {r["runner"] for r in declared}
    assert {"rehearsal", "tester"} <= names, names
    planted = {"runner": "testing-planted", "component": "testing-planted",
               "failure": "testing: a drive that writes nothing", "trail": "nothing/*.json",
               "drive": ["true", "{scratch}"]}
    red = sieve({"component": "testing-planted"}, REPO / "cairn", runners=[planted])
    assert len(red) == 1 and red[0]["method"] == "a_run_that_fails_to_run_leaves_a_trail", red
    for row in declared:
        got = sieve({"component": row["component"]}, REPO / "cairn", runners=[row])
        assert got == [], (row["runner"], got)
    assert sieve({"component": "testing-unlisted"}, REPO / "cairn", runners=declared) == []
    print(f"planted red: {red[0]['about'][:70]!r}; declared green: {sorted(names)}")


def main() -> int:
    teeth = TEETH
    failed = 0
    for name in teeth:
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            failed += 1
            print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    print(f"{'GREEN' if not failed else 'RED'} — {len(teeth) - failed}/{len(teeth)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
