"""Proof for ticket 3f544e08a783: a conflict only one of the UNION reads names gets one confirm read.

Measured 2026-11-24 (win32, 10 single reads each): the control 6cd13a3a5f42 read clean 10 of 10,
but in a three-read check one false positive kept by UNION=3 stood once in 3. The kept fix (the
orchestrator's hypothesis under outline 0.6.1): UNION stays 3; a conflict line named by exactly
one of the three reads is asked once more, yes/no, "does this ticket's work contradict this
line"; yes keeps it, no drops it LOUDLY (the record lists it under ``dropped`` and the CLI
prints it), and an unreadable confirm keeps it (a lost read never clears a conflict).

No tooth calls the live reader: the reader is a stub that tells a main read from a confirm read
by the schema it is handed, so the proof pins the MACHINE. The live pair is a separate, held run.

  1. a conflict one read names, confirm says yes: kept, one question opened, 3 + 1 calls;
  2. the same, confirm says no: no conflict, no question, the line under ``dropped`` with the
     confirm's why, 3 + 1 calls, and the CLI prints a ``dropped`` line;
  3. a conflict two reads name (one as ``2.1``, one as the clause ``2.1(1)``): kept, no confirm
     read, 3 calls;
  4. a confirm read the reader fails to return: the conflict is kept, listed under
     ``kept_unconfirmed``, and the confirm is read once, not retried (3 + 1 calls);
  5. two single-read conflicts, one confirmed and one not: only the unconfirmed one is dropped,
     each line gets its own confirm read, and the confirm prompt names that line and what the
     ticket says.
"""
from __future__ import annotations

import io
import json
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))


class _CallTime:
    """The machine under proof, bound at CALL time, never at import."""

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(
            "cairn.devices.codemother.machines.outline_check.outline_check"), name)


OC = _CallTime()
from cairn.tools.artifact import artifact as door             # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir          # noqa: E402

PROVES = {
    "3f544e08a783": {
        "1": "test_a_single_read_conflict_the_confirm_affirms_is_kept_and_opens_a_question",
        "2": "test_a_single_read_conflict_the_confirm_denies_is_dropped_loudly",
        "3": "test_a_conflict_two_reads_name_needs_no_confirm_read",
        "4": "test_an_unreadable_confirm_keeps_the_conflict_and_is_not_retried",
        "5": "test_each_single_read_line_gets_its_own_confirm_naming_it",
    },
}
TID = "0badc0ffee03"
STEM = f"{TID}-a-fixture-ticket-the-confirm-read-reads"
TICKET = {"id": TID, "title": "a fixture ticket the confirm read reads",
          "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED",
          "how": "the widget keeps its own log on disk", "questions": []}
OUTLINE = """\
1 THE WIDGET
  1.1 The widget keeps no state of its own.
  1.2 The widget has one door.
"""
C11 = {"number": "1.1", "ticket_says": "the widget keeps its own log on disk",
       "why": "a log on disk is state"}
C11_CLAUSE = dict(C11, number="1.1(1)")
C12 = {"number": "1.2", "ticket_says": "the widget opens a second door", "why": "two doors"}


def _read(*conflicts):
    return {"touches": [], "conflicts": [dict(c) for c in conflicts]}


def _yes(why="it does"):
    return {"contradicts": True, "why": why}


def _no(why="it does not"):
    return {"contradicts": False, "why": why}


class Stub:
    """Main reads come from ``mains`` (cycling); confirm reads, told apart by their schema
    carrying ``contradicts``, come from ``confirms`` in order (None = nothing returned)."""

    def __init__(self, mains, confirms=()):
        self.mains, self.confirms = list(mains), list(confirms)
        self.main_calls, self.confirm_calls, self.confirm_prompts = 0, 0, []

    @property
    def calls(self):
        return self.main_calls + self.confirm_calls

    def __call__(self, text, schema_doc):
        meta = {"model": "stub", "cost_usd": 0.0, "duration_ms": 1}
        if "contradicts" in json.dumps(schema_doc):
            self.confirm_prompts.append(text)
            out = self.confirms[self.confirm_calls] if self.confirm_calls < len(self.confirms) else None
            self.confirm_calls += 1
        else:
            out = self.mains[self.main_calls % len(self.mains)]
            self.main_calls += 1
        return (json.loads(json.dumps(out)) if out is not None else None), meta


class World:
    def __init__(self):
        self.dir = scratch_dir("confirm-read-proof-")
        self.commons, self.cairn = self.dir / "CairnCommons", self.dir / "cairn"
        for d in ("tickets", "questions", "outline_checks"):
            (self.commons / d).mkdir(parents=True)
        # bytes, never write_text: on Windows text mode turns "\n" into "\r\n" and the ticket
        # door refuses a file whose serialisation it cannot reproduce
        (self.commons / "tickets" / "_charter+why.json").write_bytes((json.dumps({
            "plan_fields": ["id", "title", "workflow_and_state", "how", "questions"],
            "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}})
            + "\n").encode())
        folder = self.cairn / "cairn/devices/cairn/requirements"
        folder.mkdir(parents=True)
        (folder / "00-outline.md").write_bytes(OUTLINE.encode())
        (self.commons / "tickets" / f"{STEM}.json").write_bytes(
            (json.dumps(TICKET, indent=2) + "\n").encode())
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def check(self, reader):
        return OC.check(TID, reader=reader, root=self.commons)

    def questions(self):
        return sorted((self.commons / "questions").glob("open-*.json"))


def test_a_single_read_conflict_the_confirm_affirms_is_kept_and_opens_a_question():
    with World() as w:
        reader = Stub([_read(C11), _read(), _read()], [_yes()])
        out = w.check(reader)
        rec = out["record"]
        assert [c["number"] for c in rec["conflicts"]] == ["1.1"], rec["conflicts"]
        assert rec.get("dropped") == [] and rec.get("kept_unconfirmed") == [], rec
        assert len(w.questions()) == 1, w.questions()
        assert (reader.main_calls, reader.confirm_calls) == (3, 1), (reader.main_calls, reader.confirm_calls)


def test_a_single_read_conflict_the_confirm_denies_is_dropped_loudly():
    with World() as w:
        reader = Stub([_read(), _read(C11), _read()], [_no("the log is the ticket's own, not the widget's")])
        out = w.check(reader)
        rec = out["record"]
        assert rec["conflicts"] == [] and w.questions() == [], (rec["conflicts"], w.questions())
        assert len(rec["dropped"]) == 1, rec.get("dropped")
        d = rec["dropped"][0]
        assert d["number"] == "1.1" and d["ticket_says"] == C11["ticket_says"], d
        assert d["confirm_why"] == "the log is the ticket's own, not the widget's", d
        assert (reader.main_calls, reader.confirm_calls) == (3, 1)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = OC.run([TID], reader=Stub([_read(), _read(C11), _read()], [_no()]), root=w.commons)
        assert code == 0 and "dropped 1.1" in buf.getvalue(), (code, buf.getvalue())


def test_a_conflict_two_reads_name_needs_no_confirm_read():
    with World() as w:
        reader = Stub([_read(C11), _read(C11_CLAUSE), _read()], [_no()])
        rec = w.check(reader)["record"]
        assert [c["number"] for c in rec["conflicts"]] == ["1.1"], rec["conflicts"]
        assert rec["dropped"] == [], rec
        assert (reader.main_calls, reader.confirm_calls) == (3, 0), (reader.main_calls, reader.confirm_calls)


def test_an_unreadable_confirm_keeps_the_conflict_and_is_not_retried():
    with World() as w:
        reader = Stub([_read(C11), _read(), _read()], [None, _no()])
        rec = w.check(reader)["record"]
        assert [c["number"] for c in rec["conflicts"]] == ["1.1"], rec["conflicts"]
        assert rec["kept_unconfirmed"] == ["1.1"] and rec["dropped"] == [], rec
        assert (reader.main_calls, reader.confirm_calls) == (3, 1), (reader.main_calls, reader.confirm_calls)
        assert len(w.questions()) == 1


def test_each_single_read_line_gets_its_own_confirm_naming_it():
    with World() as w:
        reader = Stub([_read(C11, C12), _read(), _read()], [_yes(), _no()])
        rec = w.check(reader)["record"]
        assert [c["number"] for c in rec["conflicts"]] == ["1.1"], rec["conflicts"]
        assert [d["number"] for d in rec["dropped"]] == ["1.2"], rec["dropped"]
        assert reader.confirm_calls == 2, reader.confirm_calls
        first, second = reader.confirm_prompts
        assert OUTLINE.splitlines()[1].strip().split(" ", 1)[1] in first and C11["ticket_says"] in first, first[-600:]
        assert "The widget has one door." in second and C12["ticket_says"] in second, second[-600:]


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    assert len(teeth) == 5, len(teeth)
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
    print(f"green — {len(teeth)} teeth: a conflict one of three reads names is confirmed once, kept "
          "on yes or an unreadable confirm, and dropped loudly on no")
    return 0


if __name__ == "__main__":
    sys.exit(main())
