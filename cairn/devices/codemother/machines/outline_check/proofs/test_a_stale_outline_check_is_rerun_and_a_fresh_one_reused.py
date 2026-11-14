"""Proof for ticket a3ac9282bdfa — the outline check reuses a fresh record and re-runs a stale one.

Idea 2026-11-13-an-outline-check-only-stands-for-the (akienasus): an outline check stands only for the documents it
read. Measured on live tickets by the integrator's scratch script /tmp/akienasus_ocfresh.py (Dell, 2026-11-13): stale
because the outline changed (64db, 266d, 17d5), because a plan field changed (207c), because the version it read is
not in git (ee4e); fresh: 2a20. The rule, in the machine: a record is FRESH iff the outline's bytes hash to its
outline_sha256 AND the ticket's plan fields (the charter's plan_fields) equal those of the git revision whose bytes
hash to its ticket_sha256. A cursor-only change never makes it stale; an unfindable revision always does.

Every tooth runs over a SCRATCH world handed to the artifact door: a commons that is a real git repo, a small outline,
one ticket, and a counting stub reader (the live reader is never called). The machine is bound at CALL time, so a
hollow revert reds the teeth instead of breaking this file's import.

    python <this file>
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

PROVES = {
    "a3ac9282bdfa": {
        "1": "a_fresh_record_is_reused_with_no_reader_call_and_a_cursor_only_change_keeps_it_fresh",
        "2": "a_changed_outline_a_changed_plan_field_or_an_unfindable_revision_is_rerun_and_force_reruns",
    },
}

TID = "0badc0ffee09"
STEM = f"{TID}-a-fixture-ticket-for-the-freshness-proof"
OUTLINE = """\
1 THE HOUSE
  1.1 The house has one door.
2 THE WIDGET
  2.1 The widget keeps no state
      of its own.
"""
TICKET = {"id": TID, "title": "a fixture ticket", "how": "the widget keeps its own log on disk",
          "falsifier": {"clauses": [{"n": 1, "claim": "x"}]}, "questions": [],
          "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"}
# Like the real tickets/_charter+why.json: `questions` and `workflow_and_state` are STATE fields (the question door writes a
# question id onto the ticket, and every crossing moves the cursor), so neither makes a record stale.
CHARTER = {"plan_fields": ["id", "title", "how", "falsifier"],
           "state_fields": ["workflow_and_state", "questions"]}
CONFLICT = {"number": "2.1", "ticket_says": "the widget keeps its own log on disk", "why": "a log on disk is state"}


class _CallTime:
    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(
            "cairn.devices.codemother.machines.outline_check.outline_check"), name)


OC = _CallTime()


class Stub:
    """A reader returning one recorded read, counting its calls."""

    def __init__(self, read):
        self.read, self.calls = read, 0

    def __call__(self, text, schema_doc):
        self.calls += 1
        return json.loads(json.dumps(self.read)), {"model": "stub", "cost_usd": 0.0, "duration_ms": 1}


def _git(commons: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(commons), "-c", "user.name=proof", "-c", "user.email=proof@local",
                    "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, text=True)


class World:
    def __init__(self, *, commit_ticket: bool = True):
        from cairn.tools.artifact import artifact as door
        from cairn.tools.scratch.scratch import scratch_dir
        self.door = door
        self.dir = scratch_dir("outline-fresh-proof-")
        self.commons, self.cairn = self.dir / "CairnCommons", self.dir / "cairn"
        for d in ("tickets", "questions", "outline_checks"):
            (self.commons / d).mkdir(parents=True)
        (self.cairn / "press_office").mkdir(parents=True)
        self.outline = self.cairn / "press_office" / "CairnComponentOutline.txt"
        self.outline.write_text(OUTLINE, encoding="utf-8", newline="\n")
        (self.commons / "tickets" / "_charter+why.json").write_text(json.dumps(CHARTER) + "\n", encoding="utf-8", newline="\n")
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.write_ticket(TICKET)
        _git(self.commons, "init", "-q")
        _git(self.commons, "config", "core.autocrlf", "false")
        if commit_ticket:
            self.commit("the ticket as the check reads it")
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def write_ticket(self, doc: dict) -> None:
        self.ticket.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")

    def commit(self, msg: str) -> None:
        _git(self.commons, "add", "-A")
        _git(self.commons, "commit", "-q", "-m", msg)

    def check(self, reader, **kw):
        return OC.check(TID, reader=reader, root=self.commons, **kw)

    def records(self):
        return sorted((self.commons / "outline_checks").glob(f"{TID}-*.json"))

    def questions(self):
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.commons / "questions").glob("open-*.json"))]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)


def a_fresh_record_is_reused_with_no_reader_call_and_a_cursor_only_change_keeps_it_fresh() -> None:
    with World() as w:
        reader = Stub({"touches": ["2.1"], "conflicts": [dict(CONFLICT)]})
        first = w.check(reader)
        assert reader.calls == 1 and len(w.records()) == 1 and len(w.questions()) == 1, (reader.calls, w.records(), w.questions())
        qid = w.questions()[0]["id"]
        second = w.check(reader)
        assert reader.calls == 1, f"a fresh record must be reused: the reader was called {reader.calls} times"
        assert second.get("reused") is True and second["path"] == first["path"], second
        assert len(w.records()) == 1, f"a reuse wrote a new record: {w.records()}"
        assert qid in second["qids"], f"a reuse must name the question the record opened: {second['qids']} vs {qid}"
        assert len(w.questions()) == 1, f"a reuse opened another question: {w.questions()}"
        # the cursor moves at every crossing and is not a plan field: committed, it must leave the record fresh
        moved = dict(TICKET, workflow_and_state="code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED")
        w.write_ticket(moved)
        w.commit("a crossing moves the cursor")
        third = w.check(reader)
        assert reader.calls == 1 and third.get("reused") is True, (
            f"a cursor-only change made the record stale: reader calls {reader.calls}, {third.get('reused')}")


def a_changed_outline_a_changed_plan_field_or_an_unfindable_revision_is_rerun_and_force_reruns() -> None:
    read = {"touches": ["2.1"], "conflicts": []}
    with World() as w:                                   # (a) the outline changed
        reader = Stub(read)
        w.check(reader)
        w.outline.write_text(OUTLINE + "  2.2 A line added after the check ran.\n", encoding="utf-8", newline="\n")
        out = w.check(reader)
        assert reader.calls == 2 and not out.get("reused") and len(w.records()) == 2, (
            f"a changed outline must re-run: calls {reader.calls}, reused {out.get('reused')}")
    with World() as w:                                   # (b) a plan field changed (committed)
        reader = Stub(read)
        w.check(reader)
        w.write_ticket(dict(TICKET, how="the widget keeps its log in memory"))
        w.commit("the plan changed")
        out = w.check(reader)
        assert reader.calls == 2 and not out.get("reused"), f"a changed plan field must re-run: {reader.calls}"
    with World(commit_ticket=False) as w:                # (c) the version the check read was never in git
        reader = Stub(read)
        w.check(reader)
        w.write_ticket(dict(TICKET, workflow_and_state="code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME:waiting] -> PROVED"))
        out = w.check(reader)
        assert reader.calls == 2 and not out.get("reused"), (
            f"a ticket version that is not in git cannot be shown unchanged, so it must re-run: {reader.calls}")
    with World() as w:                                   # (d) --force re-runs a fresh record
        reader = Stub(read)
        w.check(reader)
        out = w.check(reader, force=True)
        assert reader.calls == 2 and not out.get("reused") and len(w.records()) == 2, (
            f"--force must re-run a fresh record: calls {reader.calls}")


TEETH = [a_fresh_record_is_reused_with_no_reader_call_and_a_cursor_only_change_keeps_it_fresh,
         a_changed_outline_a_changed_plan_field_or_an_unfindable_revision_is_rerun_and_force_reruns]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
