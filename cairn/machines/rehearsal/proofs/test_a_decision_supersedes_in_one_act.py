"""Proof for ticket c70eeeef73ac — a rehearsal decision can supersede the lines it replaces in
one act.

Measured 2026-10-08 on 996668eceef1: ``--decide D4 "<the corrected D4>"`` landed D13 labelled
'D4' beside D4 instead of in its place; ``--retire D4`` then refused because D13 cited D4; three
lines were spent to say one thing. decide() now takes ``supersedes=[n, ...]``: one write appends
the new line and retires each named line into it (retire()'s rules and refusals), ignoring the
new line's own citations of the ids it supersedes. And a step shaped like a decision id whose
line names that same id as replaced or superseded is refused naming --supersedes — the
996668eceef1 shape — while any other line at a D<n> step lands as today (the peer's ruling
2026-10-11 on clause 2: 1779 of 6398 gaps carry a D<n> step and the CLI's printout advises it).

Every tooth runs over its own SCRATCH commons holding one testing-marked ticket, removed at
exit; none reads the live corpus or calls a reader.

  1. ONE ACT. decide(step='prompt.md', line='... replaces D4 ...', supersedes=[4]) leaves
     exactly one new live line, D4 retired into it on the log, and the plan written ONCE.
  2. THE 996668 SHAPE IS REFUSED, A PLAIN D<n> STEP LANDS. (a) decide(step='D4', line=
     '... replaces D4 ...') refuses naming --supersedes and writes nothing; (b) decide(step='D4',
     line='D4 holds: ...') lands as a new line.

    bin/cairn test cairn/machines/rehearsal/proofs/test_a_decision_supersedes_in_one_act.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"c70eeeef73ac": {"1": "a_decision_supersedes_in_one_write",
                           "2": "the_996668_shape_is_refused_and_a_plain_dn_step_lands"}}

TID = "c70ef00dfeed"
STEM = f"{TID}-testing-c70eeeef73ac-decision-supersedes"
OLD = "the prompt names the gap's step and nothing else"
NEW = "this replaces D4: the prompt names the gap's step and the line that would settle it"
HOLDS = "D4 holds: the step label is the gap's own, and the line adds what D4 left open"

BASE = [{"n": 3, "text": "push both repos", "by": "cc"},
        {"n": 4, "text": OLD, "by": "cc"}]

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


class World:
    def __init__(self, decisions):
        from cairn.tools.scratch.scratch import scratch_dir
        self.dir = Path(scratch_dir("testing-c70eeeef73ac-supersedes-"))
        self.commons = self.dir / "CairnCommons"
        tickets = self.commons / "tickets"
        tickets.mkdir(parents=True)
        # ticket_log reads the declared log kinds beside the plan; a hollow worktree has no
        # live commons beside it to fall back on
        (tickets / "_charter+why.json").write_text(json.dumps({
            "plan_fields": ["id", "title", "intention", "workflow_and_state", "decisions", "questions"],
            "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}}) + "\n")
        self.ticket = tickets / f"{STEM}.json"
        self.ticket.write_text(json.dumps({
            "id": TID, "title": "testing-c70eeeef73ac-decision-supersedes",
            "intention": "testing: a fixture ticket for the c70eeeef73ac proof",
            "decisions": decisions}, indent=2) + "\n", encoding="utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def doc(self):
        return json.loads(self.ticket.read_text(encoding="utf-8"))


def a_decision_supersedes_in_one_write():
    from cairn.machines.rehearsal import rehearsal as R
    from cairn.tools.base.ticket_log import read_log
    with World(BASE) as w:
        writes = []
        real = R._write_ticket

        def counting(tk, doc, *, why):
            writes.append(why)
            return real(tk, doc, why=why)

        R._write_ticket = counting
        try:
            entry = R.decide(TID, "prompt.md", NEW, by="cc", root=w.commons, supersedes=[4])
        finally:
            R._write_ticket = real
        doc = w.doc()
        live = [d for d in doc["decisions"] if not d.get("retired")]
        assert [d["n"] for d in live] == [3, entry["n"]], f"the live lines are not D3 and the new one: {live}"
        assert entry["text"] == NEW and entry["n"] == 5, f"the new line is not D5 carrying NEW: {entry}"
        retired = {x["decision"]["n"]: x["decision"] for x in read_log(w.ticket, "decision_retired")}
        assert 4 in retired and retired[4]["text"] == OLD, f"D4 is not on the log whole: {retired}"
        r = retired[4].get("retired") or {}
        assert r.get("into") == entry["n"] and r.get("by") == "cc", f"D4 is not retired into D5: {r}"
        assert len(writes) == 1, f"the plan was written {len(writes)} times, not once: {writes}"


def the_996668_shape_is_refused_and_a_plain_dn_step_lands():
    from cairn.machines.rehearsal import rehearsal as R
    with World(BASE) as w:
        before = w.ticket.read_bytes()
        try:
            R.decide(TID, "D4", NEW, by="cc", root=w.commons)
        except R.Refused as exc:
            assert "--supersedes" in str(exc), f"the refusal does not name --supersedes: {exc}"
        else:
            raise AssertionError("a line at step D4 that replaces D4 landed beside it")
        assert w.ticket.read_bytes() == before, "a refused decide wrote the ticket"
        entry = R.decide(TID, "D4", HOLDS, by="cc", root=w.commons)
        assert entry["step"] == "D4" and entry["text"] == HOLDS, f"the plain D4 line did not land: {entry}"
        assert [d["n"] for d in w.doc()["decisions"]] == [3, 4, entry["n"]], "D4 itself moved"


TEETH = [a_decision_supersedes_in_one_write, the_996668_shape_is_refused_and_a_plain_dn_step_lands]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
