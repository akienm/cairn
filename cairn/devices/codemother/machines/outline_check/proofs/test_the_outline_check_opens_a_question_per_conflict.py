"""Proof for ticket 6541ccd1594c — the outline check reads a ticket beside the component outline
and opens a question for each conflict, and for each open [Q#n] in a section the ticket touches.

Every tooth runs over a SCRATCH world handed to the artifact door (``set_diagnostic_roots``): a
fixture commons with a small outline, one ticket, its own journal, questions/ and outline_checks/.
No tooth calls the live reader (D13) — the reader is a stub returning a recorded read, so the
proof pins the MACHINE (parse, resolve, de-duplicate, open, record, standing); the live fire is
the measurement of the reader.

The teeth, one per falsifier clause:

  1. parse joins continuation lines onto their entry; open_questions finds a tagged [Q#7: ...]
     and a bare [Q#8], and not a digitless [Q#n: ...];
  2. a conflict on 2.1 opens exactly one question, source outline_check, quoting 2.1's text as
     the FILE says it — never the reader's words for the line;
  3. a rerun opens nothing new and lists the first question under questions_already_open;
  4. a touched 2.1 with Q#7 open on 2.1.2 opens one question naming Q#7; Q#9 on 2.2 opens none;
  5. a number the outline does not carry (9.9) opens nothing and is listed under unresolved;
  6. the record lands under outline_checks/ with a journal entry of verb outline_check, and
     carries the outline's and the ticket's sha256;
  7. a reader failing the schema twice writes a ran:false record, opens no question, and the
     CLI's run returns 2;
  8. standing() is false with no record, false over a ran:false record only, true after a run
     that read.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))


class _CallTime:
    """The machine under proof, bound at CALL time, never at import: the hollow reading takes
    outline_check.py away, and a module-level import would die before the first tooth printed."""

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(
            "cairn.devices.codemother.machines.outline_check.outline_check"), name)


OC = _CallTime()
from cairn.tools.artifact import artifact as door             # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir          # noqa: E402

PROVES = {
    "6541ccd1594c": {
        "1": "test_parse_joins_continuations_and_finds_tagged_and_bare_questions_but_not_a_digitless_one",
        "2": "test_a_conflict_opens_one_question_quoting_the_files_line_not_the_readers",
        "3": "test_a_rerun_opens_nothing_new_and_names_the_question_already_open",
        "4": "test_an_open_question_in_a_touched_section_opens_one_question_and_one_elsewhere_opens_none",
        "5": "test_a_number_the_outline_does_not_carry_opens_nothing_and_is_listed_unresolved",
        "6": "test_the_record_is_journaled_under_outline_checks_with_both_hashes",
        "7": "test_a_reader_failing_the_schema_twice_writes_ran_false_opens_nothing_and_the_cli_returns_2",
        "8": "test_standing_reads_only_a_run_that_read",
    },
}
TID = "0badc0ffee02"
STEM = f"{TID}-a-fixture-ticket-the-outline-check-reads"
TICKET = {"id": TID, "title": "a fixture ticket the outline check reads",
          "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED",
          "how": "the widget keeps its own log on disk", "questions": []}
OUTLINE = """\
A preamble line that is no entry.

1 THE HOUSE
  1.1 The house has one door.
2 THE WIDGET
  2.1 The widget keeps no state
      of its own.
    2.1.1 The widget is a tool.
    2.1.2 Where the widget lives. [Q#7: does the widget live in the rack?]
    2.1.3 A placeholder [Q#n: not a numbered question]
  2.2 The widget's neighbours. [Q#9: how many?]
3 THE RACK
  3.1 The rack is one per instance. [Q#8]
"""
LINE_21 = "The widget keeps no state of its own."
CONFLICT = {"number": "2.1", "ticket_says": "the widget keeps its own log on disk",
            "why": "a log on disk is state"}


class Stub:
    """A reader returning recorded reads in order (cycling), counting its calls. ``None`` is
    'the reader returned nothing'."""

    def __init__(self, *script):
        self.script, self.calls = list(script), 0

    def __call__(self, text, schema_doc):
        out = self.script[self.calls % len(self.script)]
        self.calls += 1
        self.last_text = text
        return (json.loads(json.dumps(out)) if out is not None else None,
                {"model": "stub", "cost_usd": 0.0, "duration_ms": 1})


def _read(touches=(), conflicts=()):
    return {"touches": list(touches), "conflicts": [dict(c) for c in conflicts]}


def _fixture_charter(tickets: Path) -> None:
    (tickets / "_charter+why.json").write_text(json.dumps({
        "plan_fields": ["id", "title", "workflow_and_state", "how", "questions"],
        "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}}) + "\n")


class World:
    def __init__(self):
        self.dir = scratch_dir("outline-check-proof-")
        self.commons = self.dir / "CairnCommons"
        self.cairn = self.dir / "cairn"
        for d in ("tickets", "questions", "outline_checks"):
            (self.commons / d).mkdir(parents=True)
        self.cairn.mkdir()
        _fixture_charter(self.commons / "tickets")
        self.outline = self.commons / "CairnComponentOutline.txt"
        self.outline.write_text(OUTLINE)
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.ticket.write_text(json.dumps(TICKET, indent=2) + "\n")
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def check(self, reader):
        return OC.check(TID, reader=reader, root=self.commons)

    def questions(self):
        return [json.loads(p.read_text()) for p in sorted((self.commons / "questions").glob("open-*.json"))]

    def records(self):
        return sorted((self.commons / "outline_checks").glob(f"{TID}-*.json"))


def test_parse_joins_continuations_and_finds_tagged_and_bare_questions_but_not_a_digitless_one():
    entries = OC.parse(OUTLINE)
    by = {e["number"]: e["text"] for e in entries}
    assert [e["number"] for e in entries] == ["1", "1.1", "2", "2.1", "2.1.1", "2.1.2", "2.1.3",
                                              "2.2", "3", "3.1"], entries
    assert by["2.1"] == LINE_21, by["2.1"]
    qs = {q["n"]: q for q in OC.open_questions(entries)}
    assert sorted(qs) == [7, 8, 9], qs
    assert qs[7]["number"] == "2.1.2" and qs[7]["text"] == "does the widget live in the rack?", qs[7]
    assert qs[8]["number"] == "3.1" and qs[8]["text"] == "The rack is one per instance.", qs[8]


def test_a_conflict_opens_one_question_quoting_the_files_line_not_the_readers():
    with World() as w:
        # the reader cannot hand the line's words in: a conflict carrying its own text fails
        # the schema, so the text the question quotes can only come from the file
        lying = dict(CONFLICT, text="THE READER'S OWN WORDS FOR THE LINE")
        assert OC.validate(_read(conflicts=[lying])), "a reader-supplied text passed the schema"
        out = w.check(Stub(_read(conflicts=[CONFLICT])))
        qs = w.questions()
        assert len(qs) == 1, qs
        q = qs[0]
        assert q["source"] == "outline_check" and q["ticket"] == TID, q
        assert f'"{LINE_21}"' in q["question"], q["question"]
        rec = out["record"]
        assert rec["conflicts"] == [{"number": "2.1", "text": LINE_21,
                                     "ticket_says": CONFLICT["ticket_says"], "why": CONFLICT["why"]}], rec
        assert rec["questions_opened"] == [q["id"]], rec


def test_a_rerun_opens_nothing_new_and_names_the_question_already_open():
    with World() as w:
        reader = Stub(_read(conflicts=[CONFLICT]))
        first = w.check(reader)["record"]
        second = w.check(reader)["record"]
        assert len(w.questions()) == 1, w.questions()
        assert second["questions_opened"] == [], second
        assert second["questions_already_open"] == first["questions_opened"], (first, second)
        assert len(w.records()) == 2, w.records()


def test_an_open_question_in_a_touched_section_opens_one_question_and_one_elsewhere_opens_none():
    with World() as w:
        rec = w.check(Stub(_read(touches=["2.1"])))["record"]
        qs = w.questions()
        assert len(qs) == 1, qs
        assert "Q#7" in qs[0]["question"] and "Q#9" not in qs[0]["question"], qs[0]["question"]
        assert [(o["n"], o["section"]) for o in rec["open_questions"]] == [(7, "2.1")], rec["open_questions"]
        # a section is two dot-components (D8): '2.1' reaches 2.1.2 and not its sibling 2.2;
        # a touched chapter '2' is its own section and reaches both
        w2 = w.check(Stub(_read(touches=["2"])))["record"]
        assert sorted(o["n"] for o in w2["open_questions"]) == [7, 9], w2["open_questions"]


def test_a_number_the_outline_does_not_carry_opens_nothing_and_is_listed_unresolved():
    with World() as w:
        rec = w.check(Stub(_read(touches=["9.9"], conflicts=[dict(CONFLICT, number="9.9")])))["record"]
        assert w.questions() == [], w.questions()
        assert rec["unresolved"] == ["9.9"], rec
        assert rec["touches"] == [] and rec["conflicts"] == [], rec


def test_the_record_is_journaled_under_outline_checks_with_both_hashes():
    with World() as w:
        out = w.check(Stub(_read()))
        path = Path(out["path"])
        assert path.parent == w.commons / "outline_checks" and path.name.startswith(f"{TID}-"), path
        rec = json.loads(path.read_text())
        assert rec["ran"] is True, rec
        assert rec["outline_sha256"] == hashlib.sha256(w.outline.read_bytes()).hexdigest(), rec
        assert rec["ticket_sha256"] == hashlib.sha256(w.ticket.read_bytes()).hexdigest(), rec
        rel = str(path.relative_to(w.commons))
        hits = [e for e in door.read_journal(w.commons) if e.get("path") == rel]
        assert len(hits) == 1 and hits[0]["verb"] == "outline_check", hits


def test_a_reader_failing_the_schema_twice_writes_ran_false_opens_nothing_and_the_cli_returns_2():
    with World() as w:
        bad = Stub({"touches": "not a list"}, None)
        out = w.check(bad)
        assert bad.calls == 2, bad.calls
        rec = out["record"]
        assert rec["ran"] is False and rec["lacks"], rec
        assert w.questions() == [], w.questions()
        assert OC.run([TID], reader=Stub(None), root=w.commons) == 2
        assert OC.run([TID], reader=Stub(_read()), root=w.commons) == 0
        assert OC.run([TID], reader=Stub(_read(conflicts=[CONFLICT])), root=w.commons) == 1


def test_standing_reads_only_a_run_that_read():
    with World() as w:
        s = OC.standing(TID, root=w.commons)
        assert s["ok"] is False and f"cairn outlinecheck {TID}" in s["lack"], s
        w.check(Stub(None))
        assert OC.standing(TID, root=w.commons)["ok"] is False
        out = w.check(Stub(_read()))
        s = OC.standing(TID, root=w.commons)
        assert s["ok"] is True and s["record"] == out["path"], s


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    assert len(teeth) >= 8, len(teeth)
    failed = []
    for tooth in teeth:
        try:
            tooth()
        except Exception as e:                       # noqa: BLE001 — the reason is the record
            failed.append(tooth.__name__)
            print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {str(e)[:300]}")
            continue
        print(f"  PASS  {tooth.__name__}")
    if failed:
        print(f"red — {len(failed)} of {len(teeth)} teeth: {', '.join(failed)}")
        return 1
    print(f"green — {len(teeth)} teeth: the outline check parses the outline, resolves the reader's "
          "numbers against the file, opens one de-duplicated question per conflict and per open Q#n "
          "in a touched section, writes a journaled record with both hashes, and stands only on a run "
          "that read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
