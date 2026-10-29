#!/usr/bin/env python3
"""Teeth for ticket db99e97f7b4f — an open question takes a note before it is answered.

Over a scratch questions root the proof owns (``artifact.set_diagnostic_roots`` for the
writes, ``CAIRN_QUESTIONS_DIR`` + ``CAIRN_ARTIFACT_ROOTS`` for the CLI subprocess):

  1. ``note()`` on an open question appends one ``{text, by, at}`` entry and ``render()``
     prints it under the question; a second note appends a second (a note() that overwrites
     instead of appending reds here — the hollow reading); the CLI ``note`` verb reaches the
     same path and ``show`` prints it;
  2. a note on an answered question, with empty text, or with no ``by`` each refuse and
     write nothing (the record's bytes are unchanged).

The subject is bound at CALL time so a reverted world reds every declared tooth by name.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

Q = None  # type: ignore[assignment]  — bound in main()
A = None  # type: ignore[assignment]

REPO = Path(__file__).resolve().parents[4]
TICKET = "db99e97f7b4f"
FAILURES: list[str] = []

PROVES = {
    "db99e97f7b4f": {
        "1": "test_a_note_appends_under_an_open_question_and_renders",
        "2": "test_a_note_on_an_answered_question_or_without_text_or_by_is_refused",
    },
}


def _exe(path: Path) -> list:
    """argv head for a shebang script: Windows cannot exec one, so go through PATH's bash."""
    return [shutil.which("bash") or "bash", path.as_posix()] if os.name == "nt" else [str(path)]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _world(tmp: Path) -> Path:
    commons = tmp / "CairnCommons"
    (commons / "questions").mkdir(parents=True)
    (commons / "tickets").mkdir()
    (tmp / "cairn").mkdir()
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn", "parked": tmp / "parked"})
    return commons / "questions"


def _env(qdir: Path) -> dict:
    commons = qdir.parent
    return dict(os.environ, PYTHONPATH=str(REPO), CAIRN_QUESTIONS_DIR=str(qdir),
                CAIRN_ARTIFACT_ROOTS=json.dumps({"CairnCommons": str(commons),
                                                 "cairn": str(commons.parent / "cairn")}))


def teeth(tmp: Path) -> None:
    qdir = _world(tmp)
    rec = Q.open_question("proof-db99-note-world", "does a note land under the question?",
                          "the proof's own question", root=qdir)
    qid = rec["id"]

    # 1. two notes append; render shows both; the CLI reaches the same door and show prints it
    Q.note(qid, "measured: the first note", by="cc", root=qdir)
    Q.note(qid, "measured: the second note", by="peer", root=qdir)
    back = Q.read(qid, root=qdir)
    notes = back.get("notes") or []
    shape = (len(notes) == 2 and [n.get("text") for n in notes]
             == ["measured: the first note", "measured: the second note"]
             and [n.get("by") for n in notes] == ["cc", "peer"]
             and all(n.get("at") for n in notes) and not back.get("resolved"))
    shown = Q.render([back])
    rendered = "measured: the first note" in shown and "measured: the second note" in shown
    cli = _exe(REPO / "bin" / "cairn") + ["question"]
    r = subprocess.run(cli + ["note", qid, "measured: a cli note", "--by", "cc"],
                       capture_output=True, text=True, env=_env(qdir), timeout=120)
    s = subprocess.run(cli + ["show", qid], capture_output=True, text=True, env=_env(qdir), timeout=120)
    cli_ok = r.returncode == 0 and "measured: a cli note" in s.stdout
    check(PROVES[TICKET]["1"], shape and rendered and cli_ok,
          f"notes={len(notes)} shape={shape} rendered={rendered} cli rc={r.returncode} "
          f"shown={'measured: a cli note' in s.stdout} {r.stderr[-160:]}")

    # 2. refusals write nothing
    path = qdir / f"{qid}.json"
    refused = []
    for kw in ({"text": "", "by": "cc"}, {"text": "a note", "by": ""}):
        before = path.read_bytes()
        try:
            Q.note(qid, kw["text"], by=kw["by"], root=qdir)
            refused.append(False)
        except Q.Refused:
            refused.append(path.read_bytes() == before)
    Q.answer(qid, "yes", spawned=[], root=qdir)
    before = path.read_bytes()
    try:
        Q.note(qid, "too late", by="cc", root=qdir)
        refused.append(False)
    except Q.Refused:
        refused.append(path.read_bytes() == before)
    r2 = subprocess.run(cli + ["note", qid, "too late"], capture_output=True, text=True,
                        env=_env(qdir), timeout=120)
    refused.append(r2.returncode != 0 and path.read_bytes() == before)
    check(PROVES[TICKET]["2"], refused == [True, True, True, True],
          f"empty text / empty by / answered / cli without --by → {refused}")


def _red_every_declared_tooth(reason: str) -> None:
    for name in PROVES[TICKET].values():
        if name not in FAILURES:
            check(name, False, reason)


def main() -> int:
    global Q, A
    try:
        from cairn.tools.question import question as subject
        from cairn.tools.artifact import artifact as door
        getattr(subject, "note")
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject does not load: {exc!r}")
        _red_every_declared_tooth("subject absent")
        print(f"\nRED — {len(FAILURES)} failure(s)")
        return 1
    Q, A = subject, door
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-question-note-proof-") as d:
            try:
                teeth(Path(d))
            finally:
                A.set_diagnostic_roots(None)
    except Exception as exc:  # noqa: BLE001 — a subject whose world was taken away
        import traceback; traceback.print_exc()
        _red_every_declared_tooth(f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
