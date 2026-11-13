"""Proof for ticket 2faf52fb34ca — the skills ask CodeMother to show an artifact.

Outline 7.4: the operator's commands are inbox, review and answer, and 7.3.6.1 takes artifacts
off his to-do list; 9.5 lists operator_inbox among CodeMother's tools and 9.6 gives her `show`.
Akien 2026-09-15: CodeMother answers every command about the code, directly or by delegation.

Teeth, one per falsifier clause:

  1. `cairn codemother show artifact <id>` exits 0 and prints exactly what the operator_inbox
     tool's CLI prints for the same id;
  2. `cairn operator show artifact <id>` exits 2, prints nothing to stdout, and names
     `cairn codemother show artifact` on stderr, also when typed ARTIFACT;
  3. the three skills' step 0 asks CodeMother, and none names the operator verb;
  4. no reader (inbox.py, four charters) is told the operator verb.

Teeth 1 and 2 read this ticket's own deep view; nothing is written.

    python3 cairn/devices/codemother/proofs/test_codemother_shows_an_artifact.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

PROVES = {"2faf52fb34ca": {
    "1": "codemother_shows_what_the_reader_shows",
    "2": "the_operator_points_at_codemother",
    "3": "the_skills_ask_codemother",
    "4": "no_reader_is_told_the_old_verb",
}}

ID = "2faf52fb34ca"
OLD = "cairn operator show artifact"
NEW = "cairn codemother show artifact"
SKILLS = ("skills/chart/SKILL.md", "skills/sorted/SKILL.md", "skills/sail/SKILL.md")
READERS = ("cairn/tools/operator_inbox/inbox.py",
           "cairn/devices/operator/intention+why.json",
           "cairn/tools/operator_inbox/intention+why.json",
           "cairn/tools/question/intention+why.json",
           "skills/sail/intention+why.json")
FAILURES: list[str] = []


def _check(name, fn) -> None:
    try:
        fn()
        print(f"  PASS  {name}", flush=True)
    except Exception as exc:  # noqa: BLE001 — a tooth reds by name, whatever broke it
        print(f"  FAIL  {name}\n        {type(exc).__name__}: {str(exc)[:1200]}", flush=True)
        FAILURES.append(name)


def _run(*argv: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(list(argv), cwd=REPO, capture_output=True, text=True, timeout=300, env=env)


def codemother_shows_what_the_reader_shows():
    from cairn.tools.base.script_argv import bash_script_argv
    asked = _run(*bash_script_argv(REPO / "bin/cairn"), "codemother", "show", "artifact", ID)
    reader = _run(sys.executable, "-m", "cairn.tools.operator_inbox.inbox", "show", "artifact", ID)
    assert reader.returncode == 0 and ID in reader.stdout, ("the reader itself", reader.returncode, reader.stderr[-400:])
    assert asked.returncode == 0, (asked.returncode, asked.stdout[-400:], asked.stderr[-400:])
    assert asked.stdout == reader.stdout, ("bytes differ", asked.stdout[:400], reader.stdout[:400])


def the_operator_points_at_codemother():
    from cairn.tools.base.script_argv import bash_script_argv
    for word in ("artifact", "ARTIFACT"):
        r = _run(*bash_script_argv(REPO / "bin/cairn"), "operator", "show", word, ID)
        assert r.returncode == 2, (word, r.returncode, r.stdout[:300])
        assert r.stdout == "", (word, "stdout", r.stdout[:300])
        assert NEW in r.stderr, (word, "stderr", r.stderr[:300])


def the_skills_ask_codemother():
    for s in SKILLS:
        text = (REPO / s).read_text(encoding="utf-8")
        assert f"{NEW} <id>" in text, (s, "does not ask CodeMother")
        assert OLD not in text, (s, "still names the operator verb")


def no_reader_is_told_the_old_verb():
    told = [r for r in READERS if OLD in (REPO / r).read_text(encoding="utf-8")]
    assert told == [], told


def main() -> int:
    for name in PROVES[ID].values():
        _check(name, globals()[name])
    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
