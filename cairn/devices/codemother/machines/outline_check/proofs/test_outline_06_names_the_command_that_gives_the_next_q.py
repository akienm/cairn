"""Proof for ticket b03dce633aa8 — outline 0.6 names the command that gives the next Q#.

Measured 2026-11-24: 0.6 read 'which is now 128' while the mint had given Q#128-Q#135 that day,
so a hand reading 0.6 would take a number already given; and 0.6's own by-line spelled
'[Q#127]', which joined.markers reads as Q#127's marker in 0.6.

The teeth, one per clause:

  1. `cairn outlinecheck --next-qnum` prints next_qnum over the commons it is pointed at:
     one past Q#900 over a scratch commons whose records reach Q#900, and next_qnum over the
     live one;
  2. the live outline states no hand-kept next unused number, and 0.6 names
     `cairn outlinecheck --next-qnum`;
  3. joined.markers reads no Q# marker in section 0.6 of the live outline.
"""
from __future__ import annotations

import io
import json
import re
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
REQ = REPO / "cairn" / "devices" / "cairn" / "requirements"
COMMAND = "cairn outlinecheck --next-qnum"


class _CallTime:
    """A module under proof, bound at CALL time: the hollow reading takes it away."""

    def __init__(self, mod):
        self._mod = mod

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._mod), name)


J = _CallTime("cairn.devices.codemother.machines.outline_check.joined")
OC = _CallTime("cairn.devices.codemother.machines.outline_check.outline_check")

PROVES = {
    "b03dce633aa8": {
        "1": "test_the_command_prints_the_next_number_the_mint_gives",
        "2": "test_the_outline_keeps_no_count_and_06_names_the_command",
        "3": "test_no_marker_stands_in_06",
    },
}


def _printed(root=None) -> str:
    out = io.StringIO()
    with redirect_stdout(out):
        rc = OC.run(["--next-qnum"], root=root)
    assert rc == 0, f"--next-qnum exited {rc}: {out.getvalue()[:200]!r}"
    return out.getvalue().strip()


def test_the_command_prints_the_next_number_the_mint_gives():
    with tempfile.TemporaryDirectory() as td:
        qd = Path(td) / "questions"; qd.mkdir()
        rec = {"id": "open-000000000900", "date": "2026-11-24", "question": "Q#900 (outline 7.1): far past the live?",
               "resolved": False, "notes": []}
        (qd / f"{rec['id']}.json").write_text(json.dumps(rec))
        assert _printed(Path(td)) == "901", "--next-qnum did not read the commons it was pointed at"
    assert _printed() == str(OC.next_qnum()), "--next-qnum over the live commons is not next_qnum"


def test_the_outline_keeps_no_count_and_06_names_the_command():
    pieces = OC.outline_bytes(REQ).decode("utf-8")
    count = re.search(r"next unused number,\s+which is\s+(?:now\s+)?\d+", pieces)
    assert not count, f"the outline keeps a hand-kept count: {count.group(0)!r}"
    six = [e for e in OC.parse(pieces) if e["number"] == "0.6"]
    assert len(six) == 1, [e["number"] for e in six]
    assert COMMAND in six[0]["text"], f"0.6 does not name {COMMAND}: {six[0]['text'][:300]!r}"


def test_no_marker_stands_in_06():
    marks = J.markers(OC.outline_bytes(REQ).decode("utf-8"))
    in_six = sorted(n for n, sec in marks.items() if sec == "0.6")
    assert not in_six, f"joined.markers reads Q# marker(s) in 0.6: {in_six}"


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    assert len(teeth) == 3, len(teeth)
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
        print(f"\n{len(failed)}/{len(teeth)} teeth red")
        return 1
    print(f"\n{len(teeth)}/{len(teeth)} teeth green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
