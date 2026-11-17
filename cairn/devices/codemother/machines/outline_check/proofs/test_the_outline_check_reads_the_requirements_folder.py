"""Proof for ticket e4a12d8e0cbf — the outline becomes the schematic: one markdown file per
section in cairn/devices/cairn/requirements/, a TOC.md naming each, and the outline check
reading the folder.

The teeth, one per outcome:

  1. the live pieces are one outline: each NN-*.md opens with '# N ...' where N is its
     filename number, the numbers run 0..k with no gap, every entry in a piece sits under that
     piece's section, and no number appears twice across the folder. (Fidelity to the outline
     at a921554bf was measured once, at build, and stands on the verdict: the outline moves.)
  2. every NN-*.md is named in TOC.md, and every file TOC.md links exists;
  3. parse() reads the markdown form ('# 9 X', nested '- 9.4.2 text' items, continuation
     lines) into numbered entries with their text joined, and check() over a scratch cairn
     whose requirements folder holds two pieces renders both into the prompt, in filename
     order, and records the folder as outline_path and the joined bytes' sha256;
  4. the five proofs that wrote a scratch press_office outline write a scratch requirements
     piece instead;
  5. press_office/CairnComponentOutline.txt is gone, and no .py, bin/ or skills/ file outside
     proofs/ and validations/ names CairnComponentOutline.txt.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
REQ = REPO / "cairn" / "devices" / "cairn" / "requirements"
NAME = "CairnComponentOutline.txt"


class _CallTime:
    """The machine under proof, bound at CALL time: the hollow reading takes it away."""

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(
            "cairn.devices.codemother.machines.outline_check.outline_check"), name)


OC = _CallTime()

PROVES = {
    "e4a12d8e0cbf": {
        "1": "test_the_live_pieces_are_one_outline_numbered_by_their_filenames",
        "2": "test_the_toc_names_every_piece_and_every_name_it_links_exists",
        "3": "test_parse_reads_markdown_and_check_renders_every_piece_and_records_the_folder",
        "4": "test_the_scratch_outline_proofs_write_a_requirements_piece",
        "5": "test_the_txt_is_gone_and_nothing_outside_proofs_names_it",
    },
}

PIECE_A = """\
# 1 THE HOUSE
- 1.1 The house has one door.
"""
PIECE_B = """\
# 2 THE WIDGET (a wrapped
- 2.1 The widget keeps no state
  of its own.
  - 2.1.1 The widget is a tool.
    - 2.1.1.1 A deep line
      that wraps. [Q#7: where?]
* 2.2 A star item.
"""


def _pieces() -> list[Path]:
    return sorted(REQ.glob("[0-9][0-9]-*.md"))


def test_the_live_pieces_are_one_outline_numbered_by_their_filenames():
    pieces = _pieces()
    assert pieces, f"no pieces under {REQ}"
    nums = [int(p.name[:2]) for p in pieces]
    assert nums == list(range(len(pieces))), nums
    seen: set[str] = set()
    for p, n in zip(pieces, nums):
        text = p.read_text(encoding="utf-8")
        first = text.splitlines()[0]
        assert re.match(rf"^# {n} \S", first), (p.name, first)
        for e in OC.parse(text):
            assert e["number"] == str(n) or e["number"].startswith(f"{n}."), (p.name, e["number"])
            assert e["number"] not in seen, (p.name, e["number"])
            seen.add(e["number"])
    assert len(seen) > 100, len(seen)


def test_the_toc_names_every_piece_and_every_name_it_links_exists():
    toc = (REQ / "TOC.md").read_text(encoding="utf-8")
    linked = re.findall(r"\]\(([^)]+)\)", toc)
    assert linked, toc[:200]
    for name in linked:
        assert (REQ / name).is_file(), name
    for p in _pieces():
        assert p.name in linked, p.name


def test_parse_reads_markdown_and_check_renders_every_piece_and_records_the_folder():
    by = {e["number"]: e["text"] for e in OC.parse(PIECE_A + "\n" + PIECE_B)}
    assert list(by) == ["1", "1.1", "2", "2.1", "2.1.1", "2.1.1.1", "2.2"], by
    assert by["2"] == "THE WIDGET (a wrapped", by["2"]
    assert by["2.1"] == "The widget keeps no state of its own.", by["2.1"]
    assert by["2.1.1.1"] == "A deep line that wraps. [Q#7: where?]", by["2.1.1.1"]
    assert by["2.2"] == "A star item.", by["2.2"]

    from cairn.tools.artifact import artifact as door
    from cairn.tools.scratch.scratch import scratch_dir
    d = scratch_dir("outline-folder-proof-")
    try:
        commons, cairn = d / "CairnCommons", d / "cairn"
        for sub in ("tickets", "questions", "outline_checks"):
            (commons / sub).mkdir(parents=True)
        (commons / "tickets" / "_charter+why.json").write_text(json.dumps({
            "plan_fields": ["id", "title", "workflow_and_state", "how", "questions"],
            "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {},
                          "decision_retired": {}}}) + "\n")
        folder = cairn / "cairn" / "devices" / "cairn" / "requirements"
        folder.mkdir(parents=True)
        (folder / "02-the-widget.md").write_text(PIECE_B)
        (folder / "01-the-house.md").write_text(PIECE_A)
        (folder / "TOC.md").write_text("# not a piece: 9 NOT READ\n")
        tid = "0badc0ffee03"
        (commons / "tickets" / f"{tid}-a-fixture.json").write_text(json.dumps({
            "id": tid, "title": "a fixture", "how": "the widget",
            "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED",
            "questions": []}) + "\n")
        door.set_diagnostic_roots({"cairn": cairn, "CairnCommons": commons})
        seen = {}

        def reader(text, schema_doc):
            seen["text"] = text
            return ({"touches": ["2.1"], "conflicts": []},
                    {"model": "stub", "cost_usd": 0.0, "duration_ms": 1})

        out = OC.check(tid, reader=reader, root=commons)
        text = seen["text"]
        assert "1.1 The house has one door." in text and "2.1 The widget keeps no state" in text, text
        assert text.index("# 1 THE HOUSE") < text.index("# 2 THE WIDGET"), "pieces out of filename order"
        assert "NOT READ" not in text, "TOC.md was read as a piece"
        rec = out["record"]
        assert rec["outline_path"] == str(folder), rec["outline_path"]
        joined = PIECE_A.encode() + b"\n" + PIECE_B.encode()
        assert rec["outline_sha256"] == hashlib.sha256(joined).hexdigest(), rec
        assert rec["touches"] and rec["unresolved"] == [], rec
    finally:
        door.set_diagnostic_roots(None)
        shutil.rmtree(d, ignore_errors=True)


SCRATCH_PROOFS = [
    "cairn/devices/codemother/machines/outline_check/proofs/test_the_outline_check_opens_a_question_per_conflict.py",
    "cairn/devices/codemother/machines/outline_check/proofs/test_an_open_question_opens_only_on_a_line_the_ticket_touches.py",
    "cairn/devices/tester/proofs/test_a_cast_red_commits_past_the_armed_path_check.py",
    "cairn/devices/tester/proofs/test_a_tester_cast_red_ticket_carries_its_outline_check.py",
    "cairn/devices/tester/proofs/test_red_tickets_asks_the_commons_git_not_the_hooks.py",
]


def test_the_scratch_outline_proofs_write_a_requirements_piece():
    for rel in SCRATCH_PROOFS:
        src = (REPO / rel).read_text(encoding="utf-8")
        assert "cairn/devices/cairn/requirements" in src and "00-outline.md" in src, rel
        assert not re.search(r'"press_office"\)\.mkdir', src), rel
        assert not re.search(rf'/ "{re.escape(NAME)}"\)?\.write_text', src), rel


def test_the_txt_is_gone_and_nothing_outside_proofs_names_it():
    assert not (REPO / "press_office" / NAME).exists()
    hits = []
    for top in ("cairn", "bin", "skills"):
        for p in (REPO / top).rglob("*"):
            if not p.is_file() or {"proofs", "validations", "__pycache__"} & set(p.parts):
                continue
            if top == "cairn" and p.suffix != ".py":
                continue
            try:
                if NAME in p.read_text(encoding="utf-8"):
                    hits.append(str(p.relative_to(REPO)))
            except (UnicodeDecodeError, OSError):
                continue
    assert hits == [], hits


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
    print("green — 5 teeth: the requirements pieces are one numbered outline the TOC names, the "
          "check reads the folder in filename order, the scratch proofs write a piece, and the .txt is gone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
