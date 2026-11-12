"""Proof for ticket d23356c26e7d — every question Akien answered before the question door existed
stands as a resolved record in the corpus, copied by ``question.migrate``.

One tooth per falsifier clause, each over a scratch world: a commons with two tickets, three
rulings, decision lines of every kind, and a transcript folder with one pair of each kind. The
live census is the verdict's instrument (D15), not a tooth here.

The subject is bound at CALL time (inside each tooth), so a reverted world reds every tooth by
name rather than crashing the reader.

    python3 cairn/tools/question/proofs/test_every_answered_question_rides_the_door.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from contextlib import contextmanager
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "d23356c26e7d": {
        "1": "test_a_ruling_stands_as_a_resolved_record_with_its_words_and_date",
        "2": "test_a_decision_line_citing_him_is_copied_or_linked_and_names_its_record",
        "3": "test_every_ticket_questions_list_holds_open_ids_only",
        "4": "test_a_second_run_writes_nothing_and_every_record_is_journaled",
        "5": "test_a_chat_reply_is_copied_and_the_counted_out_are_not",
        "6": "test_after_the_run_nothing_stands_outside",
    },
}

T1, T2 = "aaaaaaaaaaa1", "bbbbbbbbbbb2"
LIST_WORDS = ["a DEVICE is a top level thingie.", "i like yuour devices list."]
STRING_WORDS = "  keep the leading spaces, and the trailing ones too  "
THIRD_WORDS = "no ticket named here"
QUOTED = "the answer is the decision"
EXISTING = "open-0123456789ab"
TODAY = date.today().isoformat()


def _plan(tid: str, decisions: list) -> dict:
    return {"id": tid, "date": "2026-09-01", "title": f"ticket {tid}", "decisions": decisions,
            "questions": [EXISTING] if tid == T2 else "none, because a proof world"}


@contextmanager
def _world():
    from cairn.tools.artifact import artifact as A
    with tempfile.TemporaryDirectory(prefix="question-migrate-") as tmp:
        t = Path(tmp)
        commons, cairn, chat = t / "CairnCommons", t / "cairn", t / "chat"
        for d in (commons / "questions", commons / "tickets", commons / "decisions", cairn, chat):
            d.mkdir(parents=True)
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": t / "parked"})
        try:
            plans = {
                T1: _plan(T1, [
                    {"n": 1, "text": "Copy it.", "by": f"Akien verbatim 2026-09-15: '{QUOTED}'"},
                    {"n": 2, "text": "Delegated.", "by": "cc (CC's call, per Akien 2026-10-09)"},
                    {"n": 3, "text": "No words.", "by": "akien"},
                    {"n": 4, "text": "Not his.", "by": "CC at cast"},
                ]),
                T2: _plan(T2, [
                    {"n": 1, "text": f"Settled by {EXISTING}.", "by": "Akien 2026-09-16, answer recorded"},
                ]),
            }
            keys = sorted({k for p in plans.values() for k in p})
            (commons / "tickets" / "_charter+why.json").write_text(json.dumps({"plan_fields": keys}) + "\n")
            for tid, doc in plans.items():
                A.write_json(commons / "tickets" / f"{tid}-a-proof-ticket.json", doc,
                             verb="cast", why="a scratch ticket for the migration proof")
            (commons / "questions" / f"{EXISTING}.json").write_text(json.dumps({
                "id": EXISTING, "date": "2026-09-16", "ticket": T2, "question": "already here?",
                "resolved": True, "answer": "yes", "spawned": []}) + "\n")
            rulings = {
                "2026-08-13-a-device-is-its-own-process.json": {
                    "id": "2026-08-13-a-device-is-its-own-process", "date": "2026-08-13",
                    "ruled_by": "Akien", "the_ruling_verbatim": LIST_WORDS,
                    "confirmation_verbatim": "RULED YES", "context": f"for {T1}"},
                "2026-08-14-two-tickets.json": {
                    "id": "2026-08-14-two-tickets", "date": "2026-08-14",
                    "question": "Which one wins?", "the_ruling_verbatim": STRING_WORDS,
                    "context": f"{T2} and then {T1}"},
                "2026-08-15-no-ticket.json": {
                    "id": "2026-08-15-no-ticket", "date": "2026-08-15",
                    "the_ruling_verbatim": THIRD_WORDS},
                "2026-08-16-no-words.json": {"id": "2026-08-16-no-words", "date": "2026-08-16"},
            }
            for name, d in rulings.items():
                (commons / "decisions" / name).write_text(json.dumps(d, indent=2) + "\n")

            def turn(kind, content, uid, ts="2026-10-01T10:00:00Z"):
                return json.dumps({"type": kind, "uuid": uid, "timestamp": ts, "sessionId": "s1",
                                   "message": {"role": kind, "content": content}})
            (chat / "s1.jsonl").write_text("\n".join([
                turn("assistant", [{"type": "text", "text": f"Built {T1}. Shall I seal it?"}], "a1"),
                turn("user", "yes, seal it", "u1", "2026-10-01T10:01:00Z"),
                turn("assistant", [{"type": "text", "text": "Which key?"}], "a2"),
                turn("user", "token: abcdefabcdefabcdef", "u2"),
                turn("assistant", [{"type": "text", "text": "Is the weather station up?"}], "a3"),
                turn("user", "yes", "u3"),
                turn("assistant", [{"type": "text", "text": "Run it?"}], "a4"),
                turn("user", [{"type": "tool_result", "content": "ok"}], "u4"),
                turn("assistant", [{"type": "text", "text": "Done."}], "a5"),
                turn("user", "thanks", "u5"),
            ]) + "\n")
            yield commons, chat, {n: (commons / "decisions" / n).read_bytes() for n in rulings}
        finally:
            A.set_diagnostic_roots(None)


def _records(commons: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((commons / "questions").glob("open-*.json"))]


def _migrated(commons: Path, chat: Path) -> dict:
    from cairn.tools.question import migrate as M
    return M.run(transcripts=chat, root=commons / "questions")


def _plan_doc(commons: Path, tid: str) -> dict:
    return json.loads(next((commons / "tickets").glob(f"{tid}-*.json")).read_text(encoding="utf-8"))


def test_a_ruling_stands_as_a_resolved_record_with_its_words_and_date():
    with _world() as (commons, chat, before):
        _migrated(commons, chat)
        by = {r["source"]: r for r in _records(commons) if str(r.get("source", "")).startswith("decisions/")}
        assert len(by) == 3, f"3 rulings carry the_ruling_verbatim; the corpus holds {sorted(by)}"
        one = by["decisions/2026-08-13-a-device-is-its-own-process.json"]
        assert one["answer"] == "\n".join(LIST_WORDS), f"list words not copied verbatim: {one['answer']!r}"
        assert (one["ticket"], one["resolved"], one["answered_at"], one["date"]) == (T1, True, "2026-08-13", "2026-08-13"), one
        assert one["confirmation"] == "RULED YES" and one["question"].endswith("?"), one
        two = by["decisions/2026-08-14-two-tickets.json"]
        assert two["answer"] == STRING_WORDS, f"string words differ from the source: {two['answer']!r}"
        assert (two["ticket"], two["question"], two["tickets_named"]) == (T2, "Which one wins?", [T2, T1]), two
        three = by["decisions/2026-08-15-no-ticket.json"]
        assert three["ticket"] == "2026-08-15-no-ticket", f"an unbound ruling binds to its own id: {three['ticket']}"
        assert all(r["answered_at"] != TODAY and r["date"] != TODAY for r in by.values()), "a today-date"
        after = {n: (commons / "decisions" / n).read_bytes() for n in before}
        assert after == before, "decisions/ was written"
        assert any(r["id"] in (_plan_doc(commons, T1)["questions"]) for r in by.values()), \
            "the ruling's ticket does not name its record"


def test_a_decision_line_citing_him_is_copied_or_linked_and_names_its_record():
    with _world() as (commons, chat, _):
        _migrated(commons, chat)
        recs = {r["id"]: r for r in _records(commons)}
        lines = _plan_doc(commons, T1)["decisions"]
        qid = lines[0].get("question")
        assert qid in recs, f"the quoted line names no corpus record: {lines[0]}"
        r = recs[qid]
        assert (r["answer"], r["ticket"], r["answered_at"], r["source"]) == (
            QUOTED, T1, "2026-09-15", f"tickets/{T1}-a-proof-ticket.json#D1"), r
        assert all("question" not in x for x in lines[1:]), f"a delegated, wordless or CC line was copied: {lines[1:]}"
        linked = _plan_doc(commons, T2)["decisions"][0]
        assert linked.get("question") == EXISTING, f"a line citing a held record is not linked to it: {linked}"
        assert sum(1 for x in recs.values() if x.get("ticket") == T2 and
                   str(x.get("source", "")).startswith("tickets/")) == 0, "a cited record was copied twice"


def test_every_ticket_questions_list_holds_open_ids_only():
    with _world() as (commons, chat, _):
        _migrated(commons, chat)
        for tid in (T1, T2):
            qs = _plan_doc(commons, tid)["questions"]
            assert isinstance(qs, list) and qs and all(isinstance(q, str) and q.startswith("open-") for q in qs), \
                f"{tid} questions: {qs}"


def test_a_second_run_writes_nothing_and_every_record_is_journaled():
    with _world() as (commons, chat, _):
        first = _migrated(commons, chat)
        n = len(_records(commons))
        bytes_before = {p: p.read_bytes() for p in commons.rglob("*.json")}
        second = _migrated(commons, chat)
        assert sum(v["wrote"] for v in second.values()) == 0, f"the second run wrote: {second}"
        assert len(_records(commons)) == n and {p: p.read_bytes() for p in commons.rglob("*.json")} == bytes_before, \
            "the second run changed a file"
        journal = [json.loads(x) for x in (commons / ".artifact-journal.jsonl").read_text().splitlines() if x]
        migrated = [e for e in journal if "migrated" in str(e.get("why", "")) and e.get("verb") == "answer"]
        wrote = sum(v["wrote"] for v in first.values())
        assert wrote == n - 1 == len(migrated), f"wrote {wrote}, {n - 1} new records, {len(migrated)} journaled"


def test_after_the_run_nothing_stands_outside():
    with _world() as (commons, chat, _):
        from cairn.tools.question import migrate as M
        before = M.run(transcripts=chat, root=commons / "questions", write=False)
        assert (before["rulings"]["outside"], before["decision_lines"]["outside"], before["chat"]["outside"]) == (3, 2, 1), before
        assert sum(v["wrote"] for v in before.values()) == 0 and len(_records(commons)) == 1, "a census wrote"
        _migrated(commons, chat)
        after = M.run(transcripts=chat, root=commons / "questions", write=False)
        assert [after[k]["outside"] for k in ("rulings", "decision_lines", "chat")] == [0, 0, 0], after


def test_a_chat_reply_is_copied_and_the_counted_out_are_not():
    with _world() as (commons, chat, _):
        report = _migrated(commons, chat)
        recs = [r for r in _records(commons) if str(r.get("source", "")).startswith("chat:")]
        assert len(recs) == 1, f"one pair is his typed reply to a question; the corpus holds {recs}"
        r = recs[0]
        assert (r["question"], r["answer"], r["ticket"], r["answered_at"]) == (
            "Shall I seal it?", "yes, seal it", T1, "2026-10-01T10:01:00Z"), r
        c = report["chat"]
        assert (c["secret_shaped"], c["other_project"]) == (1, 1), c
        text = "".join(p.read_text() for p in (commons / "questions").glob("*.json"))
        assert "abcdefabcdef" not in text and "weather" not in text, "a counted-out reply reached the corpus"


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)
