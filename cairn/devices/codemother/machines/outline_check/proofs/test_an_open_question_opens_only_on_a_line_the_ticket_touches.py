"""Proof for ticket 0d3b8a51c9df — an open [Q#n] opens a question on a ticket only when the
ticket touches the question's own line or a line beneath it (a touched heading above the
question, or a sibling of its line, opens nothing).

Measured 2026-11-12: Q#90 (seals per OS, standing at 9.4.2.3.3) opened on 0bcb816d6e9c,
d58e7887cc99 and 446e42bb2b17, none of which reads or writes a seal. D8 widened every touched
number to its first two components, and 9.4 is the whole of CodeMother.

The world. A scratch commons and class-space handed to the artifact door, with the component
outline as it stood at a63dbc004 (``git show``; the live outline moves, the pin does not). The
reader is a stub that hands back each fixture ticket's RECORDED read: the touches below are
copied from that ticket's first record under ``CairnCommons/outline_checks/``. So the proof pins
the deterministic match after the read, and nothing here calls a model.

    bin/cairn test cairn/devices/codemother/machines/outline_check/proofs/test_an_open_question_opens_only_on_a_line_the_ticket_touches.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "0d3b8a51c9df": {
        "1": "test_three_tickets_that_touch_no_seal_line_open_no_q90",
        "2": "test_a_ticket_touching_the_seal_line_opens_q90_once",
        "3": "test_a_line_beneath_opens_and_a_parent_heading_or_sibling_does_not",
    },
}

_PIN = "a63dbc004"
_OUTLINE = "press_office/CairnComponentOutline.txt"

# each ticket's recorded touches, from CairnCommons/outline_checks/<id>-<stamp>.json
RECORDED = {
    "0bcb816d6e9c": ["3.3.4", "3.3.4.3", "9.4.8", "9.6"],                       # -20261113T023639
    "d58e7887cc99": ["3.3.4.3", "5.5.3.3", "5.5.3.9", "9.3.2", "9.4.2.3.1",
                     "9.4.2.3.4", "9.4.8"],                                     # -20261113T025902
    "446e42bb2b17": ["1.3.7", "9.3.2", "9.4.2", "9.4.2.3.1", "9.4.2.3.2", "9.4.8"],  # -20261113T031923
    "5243cf9dc630": ["3.3.4.3", "9.3.2", "9.4.2", "9.4.2.3.1", "9.4.2.3.3", "9.4.8"],  # -20261113T030452
}


def _oc():
    import importlib
    return importlib.import_module("cairn.devices.codemother.machines.outline_check.outline_check")


class _Stub:
    def __init__(self, touches):
        self.touches = list(touches)

    def __call__(self, text, schema_doc):
        return ({"touches": list(self.touches), "conflicts": []},
                {"model": "stub", "cost_usd": 0.0, "duration_ms": 1})


class _World:
    """A scratch commons (tickets/, questions/, outline_checks/) and a scratch class-space
    holding the pinned outline, with the artifact door pointed at both."""

    def __init__(self, outline_text: str | None = None):
        from cairn.tools.artifact import artifact as door
        from cairn.tools.scratch.scratch import scratch_dir
        self.door = door
        self.dir = scratch_dir("outline-line-rule-")
        self.commons, self.cairn = self.dir / "CairnCommons", self.dir / "cairn"
        for d in ("tickets", "questions", "outline_checks"):
            (self.commons / d).mkdir(parents=True)
        (self.commons / "tickets" / "_charter+why.json").write_text(json.dumps({
            "plan_fields": ["id", "title", "workflow_and_state", "how", "questions"],
            "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {},
                          "decision_retired": {}}}) + "\n")
        (self.cairn / "press_office").mkdir(parents=True)
        if outline_text is None:
            outline_text = subprocess.run(["git", "-C", str(_REPO_ROOT), "show", f"{_PIN}:{_OUTLINE}"],
                                          check=True, capture_output=True, text=True).stdout
        (self.cairn / _OUTLINE).write_text(outline_text)
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def check(self, tid: str, touches) -> dict:
        (self.commons / "tickets" / f"{tid}-a-fixture.json").write_text(json.dumps({
            "id": tid, "title": "a fixture",
            "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED",
            "how": "fixture", "questions": []}, indent=2) + "\n")
        return _oc().check(tid, reader=_Stub(touches), root=self.commons)["record"]


def _opened(record) -> list[int]:
    return sorted(o["n"] for o in record["open_questions"])


def test_three_tickets_that_touch_no_seal_line_open_no_q90():
    with _World() as w:
        for tid in ("0bcb816d6e9c", "d58e7887cc99", "446e42bb2b17"):
            rec = w.check(tid, RECORDED[tid])
            assert 90 not in _opened(rec), (f"{tid} (touches {RECORDED[tid]}) opened Q#90, which "
                                            f"stands at 9.4.2.3.3: {rec['open_questions']}")
    print("ok test_three_tickets_that_touch_no_seal_line_open_no_q90")


def test_a_ticket_touching_the_seal_line_opens_q90_once():
    with _World() as w:
        rec = w.check("5243cf9dc630", RECORDED["5243cf9dc630"])
        q90 = [o for o in rec["open_questions"] if o["n"] == 90]
        assert len(q90) == 1 and q90[0]["number"] == "9.4.2.3.3", rec["open_questions"]
        assert q90[0]["section"] == "9.4.2.3.3", q90[0]
        assert len([q for q in rec["questions_opened"]]) == len(rec["open_questions"]), rec
    print("ok test_a_ticket_touching_the_seal_line_opens_q90_once")


_SMALL = """\
2 THE WIDGET
  2.1 The widget keeps no state. [Q#5: does a heading's question reach its lines?]
    2.1.1 The widget is a tool.
    2.1.2 Where the widget lives. [Q#7: does the widget live in the rack?]
      2.1.2.1 It lives near the door. [Q#8: which door?]
    2.1.3 Its neighbour. [Q#9: how many?]
"""


def test_a_line_beneath_opens_and_a_parent_heading_or_sibling_does_not():
    with _World(_SMALL) as w:
        # a question opens when the ticket touches its line or a line beneath it: touching
        # 2.1.2 opens its own Q#7 and 2.1's Q#5, never Q#8 on the 2.1.2.1 below it
        assert _opened(w.check("0d3b8a510001", ["2.1.2"])) == [5, 7]
        assert _opened(w.check("0d3b8a510002", ["2.1.2.1"])) == [5, 7, 8]
        # a sibling's question (Q#9 on 2.1.3) does not open for 2.1.1; a touched heading (2)
        # reaches none of the questions beneath it
        assert _opened(w.check("0d3b8a510003", ["2.1.1"])) == [5]
        assert _opened(w.check("0d3b8a510004", ["2"])) == []
    print("ok test_a_line_beneath_opens_and_a_parent_heading_or_sibling_does_not")


def main() -> int:
    failed = 0
    for name in PROVES["0d3b8a51c9df"].values():
        try:
            globals()[name]()
        except Exception as exc:  # noqa: BLE001 — every tooth runs; each red is named
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {str(exc)[:400]}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
