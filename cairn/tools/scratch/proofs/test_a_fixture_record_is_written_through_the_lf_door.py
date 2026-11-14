"""Proof: a record fixture a proof writes for the artifact door is written LF, through the scratch door.

Measured 2026-11-14 on Windows: ``Path.write_text`` turns ``\\n`` into ``\\r\\n``, the artifact door's
byte round-trip (ticket_file.ticket_shape, "the ticket's serialisation cannot be reproduced")
refuses a plan it cannot reproduce, and ``test_a_hand_kick_back_writes_the_fixme_list`` reds on
Windows only. The door stays strict (it protects a record of truth); the fix is the WRITER, and a
sieve that keeps it so. Census over origin/main: 746 proof files, 1369 text-mode writes without
``newline=``; only 83 record-looking writes in 27 files sit in a file that also reaches the door.

  1. write_fixture(path, text) writes bytes with no CR, with and without newlines, and returns the
     path.
  2. fixture_writes_without_lf names a record write lacking newline= in a file that reaches the door
     (write_text and open('w') spellings; the real pre-fix test_a_hand_kick_back_writes_the_fixme_list
     is the known positive), and names nothing for write_fixture, newline="\\n", or a file with no
     door call.
  3. over the repo's real tree it names only the files an open ticket still owns.

    python3 cairn/tools/scratch/proofs/test_a_fixture_record_is_written_through_the_lf_door.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"lf-fixture-writer": {
    "1": "test_write_fixture_writes_no_carriage_return",
    "2": "test_the_sieve_names_a_record_write_beside_a_door_call_and_nothing_else",
    "3": "test_the_real_tree_names_only_the_files_an_open_ticket_owns",
}}

# Files whose migration waits on another open ticket (the LF-fixture ticket, red3, the 3e08 residue).
# Each leaves this list when its owner lands; a name here that the sieve no longer finds is fine.
OWNED = {
    "cairn/tools/base/proofs/test_a_hand_kick_back_writes_the_fixme_list.py",
    "cairn/tools/base/proofs/test_a_fixme_answer_binds_to_its_kick_back.py",
    "cairn/tools/base/proofs/test_every_watching_class_can_fixme.py",
    "cairn/tools/base/proofs/test_fixme.py",
    "cairn/tools/base/proofs/test_transitions.py",
}
_PRE_FIX = "8d20852d6"   # main before the LF-fixture build: the file with the measured Windows red


def test_write_fixture_writes_no_carriage_return():
    from cairn.tools.scratch.scratch import scratch_dir, write_fixture
    d = scratch_dir("lf_writer_")
    for name, text in (("a.json", '{\n  "a": 1\n}\n'), ("b.txt", "no newline at all"), ("c.txt", "x\ny\r\nz\n")):
        got = write_fixture(d / name, text)
        assert got == d / name, got
        raw = (d / name).read_bytes()
        assert b"\r\r" not in raw and raw.count(b"\r") == text.count("\r"), (name, raw)
    assert (d / "a.json").read_bytes() == b'{\n  "a": 1\n}\n'
    assert sorted(p.name for p in d.iterdir()) == ["a.json", "b.txt", "c.txt"]


def _tree(files: dict[str, str]) -> Path:
    from cairn.tools.scratch.scratch import scratch_dir, write_fixture
    root = scratch_dir("lf_sieve_")
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        write_fixture(p, body)
    return root


def test_the_sieve_names_a_record_write_beside_a_door_call_and_nothing_else():
    from cairn.tools.scratch.scratch import fixture_writes_without_lf
    door = "from x import rewrite_ticket\n"
    files = {
        "c/proofs/test_bad_write_text.py": door + 'def t(plan):\n    plan.write_text("{}\\n", encoding="utf-8")\n    rewrite_ticket(plan, {}, why="x")\n',
        "c/proofs/test_bad_open.py": door + 'def t(plan):\n    with open(plan, "w") as f:\n        f.write("{}")\n    rewrite_ticket(plan, {}, why="x")\n',
        "c/proofs/test_good_writer.py": door + 'def t(plan):\n    write_fixture(plan, "{}\\n")\n    rewrite_ticket(plan, {}, why="x")\n',
        "c/proofs/test_good_newline.py": door + 'def t(plan):\n    plan.write_text("{}\\n", encoding="utf-8", newline="\\n")\n    rewrite_ticket(plan, {}, why="x")\n',
        "c/proofs/test_no_door.py": 'def t(plan):\n    plan.write_text("{}\\n", encoding="utf-8")\n',
        "c/proofs/test_not_a_record.py": door + 'def t(note):\n    note.write_text("hi")\n    rewrite_ticket(1, {}, why="x")\n',
    }
    got = fixture_writes_without_lf(_tree(files))
    names = sorted(g.split(":")[0] for g in got)
    assert names == ["c/proofs/test_bad_open.py", "c/proofs/test_bad_write_text.py"], got
    assert any(g.startswith("c/proofs/test_bad_write_text.py:3 plan") for g in got), got
    # the measured positive: the real file, before its fix, reds the sieve at the write the door refused
    shown = subprocess.run(["git", "-C", str(REPO), "show",
                            f"{_PRE_FIX}:cairn/tools/base/proofs/test_a_hand_kick_back_writes_the_fixme_list.py"],
                           capture_output=True, text=True, encoding="utf-8")
    assert shown.returncode == 0, f"cannot read the known positive at {_PRE_FIX}: {shown.stderr[-300:]}"
    known = fixture_writes_without_lf(_tree({"c/proofs/test_known.py": shown.stdout}))
    assert any(g.startswith("c/proofs/test_known.py:78 plan") for g in known), known


def test_the_real_tree_names_only_the_files_an_open_ticket_owns():
    from cairn.tools.scratch.scratch import fixture_writes_without_lf
    named = {g.split(":")[0] for g in fixture_writes_without_lf(REPO)}
    stray = sorted(named - OWNED)
    assert not stray, f"proofs that write a record fixture without LF beside a door call: {stray}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
