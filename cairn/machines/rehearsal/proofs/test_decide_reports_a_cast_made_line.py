"""Proof for ticket b9be8f2e3e68 — `cairn rehearse --decide D<n>` over a line the cast wrote
reports what it did instead of crashing after the write lands.

Measured 2026-11-05 on 0d38d0f5a4e3 (idea 4d8b017e3873): the cast writes decisions as
{n, text, by, source} with no step; decide() rewrites such a line in place keeping its keys,
and __main__ then printed entry['step'], raising KeyError after the record had landed.

Every tooth runs over a SCRATCH commons holding one testing-marked ticket (removed at exit);
none reads the live corpus or calls a reader.

  1. a_cast_made_line_is_decided_cleanly: main([id, --decide, D1, line, --by, cc]) returns 0
     and prints 'decided D1'.
  2. the_line_carries_the_new_text: --decide D2 over cast-made line 2 returns 0 and the
     ticket's line 2 carries the new text.
  3. an_appended_line_still_names_its_step: the rewrite prints "at 'D1'", and --decide at a
     label that is not D<n> still returns 0 and prints "at 'a label'".

    python3 cairn/machines/rehearsal/proofs/test_decide_reports_a_cast_made_line.py   # exit 0 = green
"""
from __future__ import annotations

import contextlib
import importlib
import io
import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"b9be8f2e3e68": {"1": "a_cast_made_line_is_decided_cleanly",
                           "2": "the_line_carries_the_new_text",
                           "3": "an_appended_line_still_names_its_step"}}

TID = "b9bef00dfeed"
STEM = f"{TID}-testing-b9be8f2e3e68-decide-reports-a-cast-made-line"
NEW = "the widget is wired at shim.py's verb table"
TICKET = {
    "id": TID,
    "title": "testing-b9be8f2e3e68-decide-reports-a-cast-made-line",
    "intention": "testing: a fixture ticket for the b9be8f2e3e68 proof",
    "decisions": [
        {"n": 1, "text": "D1: wire the widget", "by": "cc", "source": "cast"},
        {"n": 2, "text": "D2: lint the widget", "by": "cc", "source": "cast"},
    ],
}

PASS = 0
FAIL = 0


def _tooth(name, fn, world):
    global PASS, FAIL
    try:
        fn(world)
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


class World:
    def __init__(self):
        from cairn.tools.scratch.scratch import scratch_dir
        self.dir = Path(scratch_dir("testing-b9be8f2e3e68-decide-reports-"))
        self.commons = self.dir / "CairnCommons"
        (self.commons / "tickets").mkdir(parents=True)
        # ticket_log reads the declared log kinds beside the plan; a hollow worktree has no
        # live commons beside it to fall back on
        (self.commons / "tickets" / "_charter+why.json").write_text(json.dumps({
            "plan_fields": ["id", "title", "intention", "workflow_and_state", "decisions", "questions"],
            "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}}) + "\n")
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.ticket.write_text(json.dumps(TICKET, indent=2) + "\n", encoding="utf-8")

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run(self, argv):
        """main(argv) with the rehearsal pointed at the scratch commons; (exit, stdout)."""
        R = importlib.import_module("cairn.machines.rehearsal.rehearsal")
        cli = importlib.import_module("cairn.machines.rehearsal.__main__")
        real = R.commons
        R.commons = lambda root=None: Path(root) if root is not None else self.commons
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                try:
                    code = cli.main(argv)
                except SystemExit as e:
                    code = e.code
        finally:
            R.commons = real
        return code, out.getvalue()


def a_cast_made_line_is_decided_cleanly(w):
    code, out = w.run([TID, "--decide", "D1", NEW, "--by", "cc"])
    assert code == 0, f"--decide D1 over a cast-made line exited {code}: {out!r}"
    assert "decided D1" in out, f"no report of the rewrite: {out!r}"


def the_line_carries_the_new_text(w):
    code, out = w.run([TID, "--decide", "D2", NEW + " (D2)", "--by", "cc"])
    assert code == 0, f"--decide D2 over a cast-made line exited {code}: {out!r}"
    doc = json.loads(w.ticket.read_text(encoding="utf-8"))
    two = [d for d in doc["decisions"] if isinstance(d, dict) and d.get("n") == 2]
    assert two and NEW + " (D2)" in two[0]["text"], f"line 2 does not carry the new text: {two}"


def an_appended_line_still_names_its_step(w):
    code, out = w.run([TID, "--decide", "D1", NEW + " again", "--by", "cc"])
    assert code == 0 and "at 'D1'" in out, f"the rewrite does not name its step: {code} {out!r}"
    code, out = w.run([TID, "--decide", "a label", "an appended line", "--by", "cc"])
    assert code == 0, f"--decide at a label exited {code}: {out!r}"
    assert "at 'a label'" in out, f"the appended line's step is not reported: {out!r}"


TEETH = [a_cast_made_line_is_decided_cleanly, the_line_carries_the_new_text,
         an_appended_line_still_names_its_step]

if __name__ == "__main__":
    world = World()
    try:
        for fn in TEETH:
            _tooth(fn.__name__, fn, world)
    finally:
        world.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
