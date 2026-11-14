"""Proof for ticket de75c632ea30 — an outline check stays fresh while the sections its ticket touches are unchanged.

Outline 9.3.5.1: the check reads a ticket 'beside the outline sections it touches ... so editing the outline costs
nothing'. a3ac9282bdfa made a stored check stand only while the WHOLE outline was unchanged; measured on akiendell,
384 of 404 stored checks were stale on outline change alone. This ticket scopes the outline condition to the touched
sections: each touched line and every line beneath it (the [Q#n] tags are part of an entry's text).

Every tooth runs over a SCRATCH world handed to the artifact door: a commons that is a real git repo, a small
outline, one ticket and a counting stub reader (the live reader is never called). The machine is bound at CALL time,
so a hollow revert reds the teeth instead of breaking this file's import.

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
    "de75c632ea30": {
        "1": "an_edit_to_a_section_the_ticket_does_not_touch_leaves_the_check_fresh",
        "2": "an_edit_to_a_touched_section_or_a_record_without_a_section_hash_is_rerun",
        "3": "a_plan_change_stales_the_check_with_the_outline_unchanged",
    },
}

TID = "0badc0ffee11"
STEM = f"{TID}-a-fixture-ticket-for-the-section-proof"
OUTLINE = """\
1 THE HOUSE
  1.1 The house has one door.
2 THE WIDGET
  2.1 The widget keeps no state
      of its own.
    2.1.1 The widget is a tool.
  2.2 The widget has neighbours.
3 THE RACK
  3.1 The rack is one per instance.
"""
TICKET = {"id": TID, "title": "a fixture ticket", "how": "the widget keeps its own log on disk",
          "falsifier": {"clauses": [{"n": 1, "claim": "x"}]}, "questions": [],
          "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"}
CHARTER = {"plan_fields": ["id", "title", "how", "falsifier"], "state_fields": ["workflow_and_state", "questions"]}
TOUCHES_2_1 = {"touches": ["2.1"], "conflicts": []}
TOUCHES_NOTHING = {"touches": [], "conflicts": []}


class _CallTime:
    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(
            "cairn.devices.codemother.machines.outline_check.outline_check"), name)


OC = _CallTime()


class Stub:
    def __init__(self, read):
        self.read, self.calls = read, 0

    def __call__(self, text, schema_doc):
        self.calls += 1
        return json.loads(json.dumps(self.read)), {"model": "stub", "cost_usd": 0.0, "duration_ms": 1}


def _git(commons: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(commons), "-c", "user.name=proof", "-c", "user.email=proof@local",
                    "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, text=True)


class World:
    def __init__(self, *, outline_in_git: bool = False):
        from cairn.tools.artifact import artifact as door
        from cairn.tools.scratch.scratch import scratch_dir
        self.door = door
        self.dir = scratch_dir("outline-section-proof-")
        self.commons, self.cairn = self.dir / "CairnCommons", self.dir / "cairn"
        for d in ("tickets", "questions", "outline_checks"):
            (self.commons / d).mkdir(parents=True)
        (self.cairn / "press_office").mkdir(parents=True)
        self.outline = self.cairn / "press_office" / "CairnComponentOutline.txt"
        self.set_outline(OUTLINE)
        if outline_in_git:                   # the outline lives in the cairn repo; a record's outline version is found there
            _git(self.cairn, "init", "-q")
            _git(self.cairn, "config", "core.autocrlf", "false")
            _git(self.cairn, "add", "-A")
            _git(self.cairn, "commit", "-q", "-m", "the outline as the check read it")
        (self.commons / "tickets" / "_charter+why.json").write_text(json.dumps(CHARTER) + "\n", encoding="utf-8", newline="\n")
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.write_ticket(TICKET)
        _git(self.commons, "init", "-q")
        _git(self.commons, "config", "core.autocrlf", "false")
        _git(self.commons, "add", "-A")
        _git(self.commons, "commit", "-q", "-m", "the ticket as the check reads it")
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def set_outline(self, text: str) -> None:
        self.outline.write_text(text, encoding="utf-8", newline="\n")

    def write_ticket(self, doc: dict) -> None:
        self.ticket.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")

    def check(self, reader, **kw):
        return OC.check(TID, reader=reader, root=self.commons, **kw)

    def records(self):
        return sorted((self.commons / "outline_checks").glob(f"{TID}-*.json"))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)


def an_edit_to_a_section_the_ticket_does_not_touch_leaves_the_check_fresh() -> None:
    with World() as w:
        reader = Stub(TOUCHES_2_1)
        w.check(reader)
        rec = json.loads(w.records()[0].read_text(encoding="utf-8"))
        assert rec.get("touched_sha256"), f"a record that touched a section must carry its section hash: {sorted(rec)}"
        # edits elsewhere: a changed line in section 3, a line added under section 1, a [Q#n] added in section 3
        elsewhere = (OUTLINE.replace("The rack is one per instance.", "The rack is one per instance, always.")
                     .replace("  1.1 The house has one door.\n", "  1.1 The house has one door.\n  1.2 A second house line. [Q#31: how many?]\n"))
        assert elsewhere != OUTLINE
        w.set_outline(elsewhere)
        out = w.check(reader)
        assert reader.calls == 1 and out.get("reused") is True and len(w.records()) == 1, (
            f"an edit to untouched sections staled the check: reader calls {reader.calls}, reused {out.get('reused')}")
    an_old_record_with_no_section_hash_is_judged_from_the_outline_version_it_read()


def an_old_record_with_no_section_hash_is_judged_from_the_outline_version_it_read() -> None:
    """The field did not exist before this ticket, and every stored record predates it, so the section hash of an old
    record is derived from the outline version it read, found in git by its outline_sha256 (like the ticket's plan)."""
    with World(outline_in_git=True) as w:
        reader = Stub(TOUCHES_2_1)
        w.check(reader)
        path = w.records()[0]
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec.pop("touched_sha256", None)
        path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8", newline="\n")
        w.set_outline(OUTLINE.replace("The rack is one per instance.", "The rack is one per instance, always."))
        out = w.check(reader)
        assert reader.calls == 1 and out.get("reused") is True, (
            f"an old record whose touched sections are unchanged must stay fresh: calls {reader.calls}")
    with World(outline_in_git=True) as w:
        reader = Stub(TOUCHES_2_1)
        w.check(reader)
        path = w.records()[0]
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec.pop("touched_sha256", None)
        path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8", newline="\n")
        w.set_outline(OUTLINE.replace("The widget keeps no state", "The widget keeps all its state"))
        out = w.check(reader)
        assert reader.calls == 2 and not out.get("reused"), "an old record whose touched section changed must re-run"


def an_edit_to_a_touched_section_or_a_record_without_a_section_hash_is_rerun() -> None:
    cases = {
        "the touched line changed": OUTLINE.replace("The widget keeps no state\n      of its own.", "The widget keeps all its state\n      of its own."),
        "a line was added beneath the touched line": OUTLINE.replace("    2.1.1 The widget is a tool.\n", "    2.1.1 The widget is a tool.\n    2.1.2 The widget is also a sink.\n"),
        "a [Q#n] was added beneath the touched line": OUTLINE.replace("The widget is a tool.", "The widget is a tool. [Q#12: which tool?]"),
        "the touched number no longer resolves": OUTLINE.replace("  2.1 The widget keeps no state\n      of its own.\n    2.1.1 The widget is a tool.\n", "  2.0 The widget keeps no state\n      of its own.\n    2.0.1 The widget is a tool.\n"),
    }
    for why, edited in cases.items():
        assert edited != OUTLINE, why
        with World() as w:
            reader = Stub(TOUCHES_2_1)
            w.check(reader)
            w.set_outline(edited)
            out = w.check(reader)
            assert reader.calls == 2 and not out.get("reused"), f"{why}: the check must re-run, reader calls {reader.calls}"
    with World() as w:                       # no section hash AND the outline version it read is not in git: stale
        reader = Stub(TOUCHES_2_1)
        w.check(reader)
        path = w.records()[0]
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec.pop("touched_sha256", None)
        path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8", newline="\n")
        w.set_outline(OUTLINE.replace("The rack is one per instance.", "The rack is one per instance, always."))
        out = w.check(reader)
        assert reader.calls == 2 and not out.get("reused"), "a record whose outline version cannot be found in git must stay stale"
    with World() as w:                       # a ticket that touched nothing: whole-outline rule (a new line could touch it)
        reader = Stub(TOUCHES_NOTHING)
        w.check(reader)
        w.set_outline(OUTLINE.replace("The rack is one per instance.", "The rack is one per instance, always."))
        out = w.check(reader)
        assert reader.calls == 2 and not out.get("reused"), "a zero-touch record must stay stale on any outline change"


def a_plan_change_stales_the_check_with_the_outline_unchanged() -> None:
    with World() as w:
        reader = Stub(TOUCHES_2_1)
        w.check(reader)
        w.write_ticket(dict(TICKET, how="the widget keeps its log in memory"))
        _git(w.commons, "add", "-A")
        _git(w.commons, "commit", "-q", "-m", "the plan changed")
        out = w.check(reader)
        assert reader.calls == 2 and not out.get("reused"), f"a plan change must re-run even with the outline unchanged: {reader.calls}"


TEETH = [an_edit_to_a_section_the_ticket_does_not_touch_leaves_the_check_fresh,
         an_edit_to_a_touched_section_or_a_record_without_a_section_hash_is_rerun,
         a_plan_change_stales_the_check_with_the_outline_unchanged]


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
