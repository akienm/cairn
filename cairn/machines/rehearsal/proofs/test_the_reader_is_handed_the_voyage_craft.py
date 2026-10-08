"""Proof for ticket 996668eceef1 — the rehearsal reader is handed a standing voyage-craft note.

Measured 2026-10-08 on d0672a46aa7e: 12 rehearsal passes to clean (gaps per pass
3,2,6,1,1,3,3,4,1,1,2, then 0), and 11 of its 17 decision lines re-derived voyage craft that is
the same on every ticket — commit messages and trailers, the separate build commit, typed
commands instead of scratchpad scripts, the PROVEME why, the PROVED arguments.

Every tooth runs over a SCRATCH commons holding one ticket (testing-marked, removed at exit);
none reads the live corpus or calls a reader.

  1. THE NOTE IS HANDED BETWEEN THE PROMPT AND THE TICKET. render()'s text begins with the
     prompt, then carries '# VOYAGE CRAFT' and voyage_craft.md's text verbatim, before
     '# THE TICKET'.
  2. A MISSING NOTE REFUSES BY NAME. With the note's path pointed at a file that does not exist,
     render() raises Refused naming that path, and the scratch commons holds only its ticket.
  3. THE NOTE ANSWERS EACH CRAFT QUESTION d0672 FOLDED. voyage_craft.md carries every marker
     in CRAFT.

    python3 cairn/machines/rehearsal/proofs/test_the_reader_is_handed_the_voyage_craft.py   # exit 0 = green
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"996668eceef1": {"1": "test_the_note_is_handed_between_the_prompt_and_the_ticket",
                           "2": "test_a_missing_note_refuses_by_name",
                           "3": "test_the_note_answers_each_craft_question"}}

NOTE = Path(__file__).resolve().parents[1] / "voyage_craft.md"
CRAFT = ["proof —", "build —", "seal —", "trailer", "writes_to", "before the next door",
         "worktree", "siblings", "--proven-by", "--why", "--hollow", "write_verdict",
         "validate berth"]

TID = "996600feed00"
STEM = f"{TID}-testing-996668eceef1-voyage-craft"
TICKET = {
    "id": TID,
    "title": "testing-996668eceef1-voyage-craft",
    "intention": "testing: a fixture ticket for the 996668eceef1 proof",
    "decisions": [{"n": 1, "text": "wire the widget"}],
}

PASS = 0
FAIL = 0


def _tooth(name, fn, world):
    global PASS, FAIL
    try:
        fn(world)
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  PASS  {name}")


class World:
    def __init__(self):
        from cairn.tools.scratch.scratch import scratch_dir
        self.dir = Path(scratch_dir("testing-996668eceef1-voyage-craft-"))
        self.commons = self.dir / "CairnCommons"
        (self.commons / "tickets").mkdir(parents=True)
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.ticket.write_text(json.dumps(TICKET, indent=2) + "\n", encoding="utf-8")

    def render(self):
        from cairn.machines.rehearsal import rehearsal as R
        return R.render(TID, root=self.commons, berths_root=self.dir / "no-berths",
                        repo=self.dir / "no-repo")[0]

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def test_the_note_is_handed_between_the_prompt_and_the_ticket(w):
    from cairn.machines.rehearsal import rehearsal as R
    text = w.render()
    assert text.startswith(R.prompt()), "render() no longer begins with the prompt"
    head = "# VOYAGE CRAFT\n\n"
    assert head in text, "render() hands the reader no '# VOYAGE CRAFT' section"
    note = NOTE.read_text(encoding="utf-8")
    at = text.index(head)
    assert text[at + len(head):].startswith(note), "the VOYAGE CRAFT section is not voyage_craft.md verbatim"
    assert at < text.index("# THE TICKET"), "the VOYAGE CRAFT section comes after THE TICKET"


def test_a_missing_note_refuses_by_name(w):
    from cairn.machines.rehearsal import rehearsal as R
    missing = w.dir / "no-such-voyage-craft.md"
    had = hasattr(R, "VOYAGE_CRAFT_PATH")
    saved = getattr(R, "VOYAGE_CRAFT_PATH", None)
    R.VOYAGE_CRAFT_PATH = missing
    try:
        try:
            w.render()
        except R.Refused as exc:
            assert str(missing) in str(exc), f"the refusal does not name the missing note: {exc}"
        else:
            raise AssertionError("render() handed the reader a text with the voyage-craft note missing")
    finally:
        if had:
            R.VOYAGE_CRAFT_PATH = saved
        else:
            del R.VOYAGE_CRAFT_PATH
    left = sorted(p.relative_to(w.commons).as_posix() for p in w.commons.rglob("*") if p.is_file())
    assert left == [f"tickets/{STEM}.json"], f"a refused render wrote into the commons: {left}"


def test_the_note_answers_each_craft_question(w):
    assert NOTE.is_file(), f"no voyage-craft note at {NOTE}"
    note = NOTE.read_text(encoding="utf-8")
    lacks = [m for m in CRAFT if m not in note]
    assert not lacks, f"the voyage-craft note does not answer: {lacks}"


TEETH = [test_the_note_is_handed_between_the_prompt_and_the_ticket,
         test_a_missing_note_refuses_by_name,
         test_the_note_answers_each_craft_question]

if __name__ == "__main__":
    world = World()
    try:
        for fn in TEETH:
            _tooth(fn.__name__, fn, world)
    finally:
        world.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
