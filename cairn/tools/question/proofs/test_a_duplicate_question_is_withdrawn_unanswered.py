"""Proof for ticket e1fb0e0bc945 — a duplicate question is withdrawn, unanswered, through the door.

Measured 2026-11-16: Q#119 on e56a68e651c2 and Q#116 on 312be610152e each stood twice, once
opened by hand and once by ``cairn outlinecheck``. Both copies held the BUILDME lane, and the
question door's verbs (open operator answer note rebind list show) offered no way to close one
short of answering it. e1d3fd0f2aab stopped the outline check from opening the second copy; a
question opened twice by hand still had no way out.

  1. ``withdraw`` resolves the duplicate with no answer and names the question that stands:
     the ticket's open list (what the BUILDME lane reads) holds only the kept one;
  2. each bad withdrawal is refused and writes nothing: a question on another ticket, itself,
     one that does not exist, an already-resolved one, a withdrawn one as the keeper, a blank
     why;
  3. ``python3 -m cairn.tools.question withdraw <qid> --duplicate-of <qid> --why ...`` does
     the same from the shell.

Every tooth runs in a scratch commons under scratch diagnostic roots; nothing live is written.
The subject is bound at call time, so a world without ``withdraw`` reds each tooth by name.

    bin/cairn test cairn/tools/question/proofs/test_a_duplicate_question_is_withdrawn_unanswered.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"e1fb0e0bc945": {
    "1": "a_withdrawn_duplicate_leaves_the_open_list_unanswered",
    "2": "each_bad_withdrawal_is_refused_and_writes_nothing",
    "3": "the_cli_withdraws_a_duplicate",
}}
TID, OTHER = "0badc0ffee01", "0badc0ffee02"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:1500]}")
    if not ok:
        FAILURES.append(name)


def _world(tmp: Path):
    """A scratch commons with two tickets filed through the door, under scratch roots."""
    from cairn.tools.artifact import artifact as A
    commons = tmp / "CairnCommons"
    (commons / "questions").mkdir(parents=True)
    (commons / "tickets").mkdir()
    (tmp / "cairn").mkdir()
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn", "parked": tmp / "parked"})
    keys = ["id", "questions", "title"]
    (commons / "tickets" / "_charter+why.json").write_text(json.dumps({"plan_fields": keys}) + "\n")
    for tid in (TID, OTHER):
        A.write_json(commons / "tickets" / f"{tid}-a-proof-world-ticket.json",
                     {"id": tid, "title": "a proof world ticket", "questions": []},
                     verb="cast", why="the scratch ticket the proof's questions are about")
    return commons / "questions"


def _open(Q, qroot: Path, ticket: str, words: str) -> str:
    return Q.open_question(ticket, words, "fixture: it holds the lane", raised_by="proof",
                           root=qroot)["id"]


def _in_process(tmp: Path) -> None:
    from cairn.tools.question import question as Q
    qroot = _world(tmp)
    keep = _open(Q, qroot, TID, "[Q#7] does the fixture hold?")
    dup = _open(Q, qroot, TID, "[Q#7] does the fixture hold? opened again by hand?")
    other = _open(Q, qroot, OTHER, "[Q#7] on another ticket?")
    rec = Q.withdraw(dup, duplicate_of=keep, why="the same [Q#7], opened twice", root=qroot)
    on_disk = Q.read(dup, root=qroot)
    still = [q["id"] for q in Q.open_for(TID, root=qroot)]
    check(PROVES["e1fb0e0bc945"]["1"],
          on_disk.get("resolved") is True and on_disk.get("answer") is None
          and (on_disk.get("withdrawn") or {}).get("duplicate_of") == keep
          and still == [keep] and rec["id"] == dup,
          f"record={on_disk} open_for={still}")

    third = _open(Q, qroot, TID, "[Q#7] a third copy?")
    answered = _open(Q, qroot, TID, "[Q#8] already answered?")
    Q.answer(answered, "yes", spawned=[], root=qroot)
    cases = {
        "another_ticket": dict(qid=third, duplicate_of=other, why="x"),
        "itself": dict(qid=third, duplicate_of=third, why="x"),
        "missing": dict(qid=third, duplicate_of="open-000000000404", why="x"),
        "already_resolved": dict(qid=answered, duplicate_of=keep, why="x"),
        "keeper_withdrawn": dict(qid=third, duplicate_of=dup, why="x"),
        "blank_why": dict(qid=third, duplicate_of=keep, why="  "),
    }
    bad = []
    for name, kw in cases.items():
        qid = kw.pop("qid")
        before = Q._path(qid, qroot).read_bytes()
        try:
            Q.withdraw(qid, root=qroot, **kw)
            bad.append(f"{name}: accepted")
        except Q.Refused as exc:
            if Q._path(qid, qroot).read_bytes() != before:
                bad.append(f"{name}: refused but wrote")
            print(f"        {name}: {str(exc)[:160]}")
    check(PROVES["e1fb0e0bc945"]["2"], not bad, f"bad={bad}")


def _through_cli(tmp: Path) -> None:
    from cairn.tools.question import question as Q
    qroot = _world(tmp)
    commons = qroot.parent
    keep = _open(Q, qroot, TID, "[Q#9] cli keeper?")
    dup = _open(Q, qroot, TID, "[Q#9] cli duplicate?")
    env = dict(os.environ, PYTHONPATH=str(REPO), CAIRN_QUESTIONS_DIR=str(qroot),
               CAIRN_ARTIFACT_ROOTS=json.dumps({"CairnCommons": str(commons),
                                                "cairn": str(commons.parent / "cairn")}))
    r = subprocess.run([sys.executable, "-m", "cairn.tools.question", "withdraw", dup,
                        "--duplicate-of", keep, "--why", "the same [Q#9], opened twice"],
                       cwd=REPO, env=env, capture_output=True, text=True, timeout=120)
    on_disk = json.loads(Q._path(dup, qroot).read_text(encoding="utf-8"))
    check(PROVES["e1fb0e0bc945"]["3"],
          r.returncode == 0 and on_disk.get("resolved") is True
          and (on_disk.get("withdrawn") or {}).get("duplicate_of") == keep,
          f"rc={r.returncode} out={r.stdout[-300:]!r} err={r.stderr[-500:]!r} record={on_disk}")


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    for fn, prefix, teeth in ((_in_process, "qwdin", ("1", "2")), (_through_cli, "qwdcli", ("3",))):
        try:
            fn(Path(scratch_dir(prefix)))
        except Exception as exc:  # noqa: BLE001 — a raising setup reds its teeth by name, loud
            for n in teeth:
                if PROVES["e1fb0e0bc945"][n] not in FAILURES:
                    check(PROVES["e1fb0e0bc945"][n], False, f"{fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}" if FAILURES else "\nall teeth green")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
