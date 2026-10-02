"""Proof for ticket eb1c943e09b9 — a gap disposed with ``cairn rehearse --decide`` lands in the
line it settles, and every decision carries its own D<n> in the text the reader is handed.

Measured 2026-09-29 on cd8096f9eeca, and again 2026-10-02 on d8e8a2dc1176 and e8fe361a5b2f: a
decide line is appended as a NEW decision whose text carries no D<n>, so a read refuses
'missing D<n>', and a settled step is re-flagged while its answer stands elsewhere in the list.

THE STANDING BASELINE (D4), measured 2026-10-02 over CairnCommons/rehearsals/*.json: 77
tickets rehearsed, 71 reached clean, MEDIAN 4 RECORDS TO CLEAN (mean 4.15), counting a
ticket's records in 'at' order up to and including its first clean one. Not the 'pass'
field: it restarts after every --decide (its first-clean median is 1).

Every tooth runs over a SCRATCH commons holding one ticket (testing-marked, removed at exit);
none reads the live corpus or calls a reader.

  1. EVERY DECISION IS LABELED. render() shows each decision's text beginning 'D<n> ', its own
     n, and a text already labeled is not labeled twice.
  2. THE ANSWER LANDS IN ITS LINE. A rehearsal-sourced decision with step 'D<m>' appears inside
     D<m>'s rendered text as '[settled by D<n>: <its text>]', and stays in the list labeled.
  3. THE HASH IS OF THE FILE. render() still returns sha256 of the ticket file bytes.
  4. THE FILE IS UNTOUCHED. The ticket's bytes are the same after render() as before.

    python3 cairn/machines/rehearsal/proofs/test_decide_lands_in_its_line.py   # exit 0 = green
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"eb1c943e09b9": {"1": "every_decision_is_labeled",
                           "2": "the_answer_lands_in_its_line",
                           "3": "the_hash_is_of_the_file",
                           "4": "the_file_is_untouched"}}

TID = "eb1cf00dfeed"
STEM = f"{TID}-testing-eb1c943e09b9-decide-lands-in-its-line"
SETTLED = "the widget is wired off the rack shim, at shim.py's verb table"
TICKET = {
    "id": TID,
    "title": "testing-eb1c943e09b9-decide-lands-in-its-line",
    "intention": "testing: a fixture ticket for the eb1c943e09b9 proof",
    "decisions": [
        {"n": 1, "text": "wire the widget"},
        {"n": 2, "text": "D2 lint the widget"},
        {"n": 3, "text": SETTLED, "by": "cc", "step": "D1", "source": "rehearsal"},
        {"n": 4, "text": "a step naming no decision", "by": "cc", "step": "unlisted: polish",
         "source": "rehearsal"},
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
        self.dir = Path(scratch_dir("testing-eb1c943e09b9-decide-lands-"))
        self.commons = self.dir / "CairnCommons"
        (self.commons / "tickets").mkdir(parents=True)
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.ticket.write_text(json.dumps(TICKET, indent=2) + "\n", encoding="utf-8")
        self.before = self.ticket.read_bytes()
        from cairn.machines.rehearsal import rehearsal as R
        self.text, self.sha, self.path = R.render(TID, root=self.commons,
                                                  berths_root=self.dir / "no-berths",
                                                  repo=self.dir / "no-repo")

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def decisions(self) -> dict[int, str]:
        head = "# THE TICKET\n\n```json\n"
        i = self.text.index(head) + len(head)
        doc = json.loads(self.text[i:self.text.index("\n```", i)])
        return {d["n"]: d["text"] for d in doc["decisions"]}


def every_decision_is_labeled(w):
    got = w.decisions()
    bad = {n: t for n, t in got.items() if not t.startswith(f"D{n} ")}
    assert not bad, f"decisions rendered without their own label: {bad}"
    assert not got[2].startswith("D2 D2"), f"an already-labeled text was labeled twice: {got[2]!r}"


def the_answer_lands_in_its_line(w):
    got = w.decisions()
    want = f"[settled by D3: {SETTLED}]"
    assert want in got[1], f"D1's rendered line does not carry its answer: {got[1]!r}"
    assert 3 in got and SETTLED in got[3], f"the settling decision left the list: {got}"
    assert "settled by D4" not in w.text, "a step naming no decision was folded somewhere"


def the_hash_is_of_the_file(w):
    assert w.sha == hashlib.sha256(w.before).hexdigest(), \
        f"render() hashed something other than the ticket bytes: {w.sha}"


def the_file_is_untouched(w):
    assert w.ticket.read_bytes() == w.before, "render() changed the ticket file"


TEETH = [every_decision_is_labeled, the_answer_lands_in_its_line, the_hash_is_of_the_file,
         the_file_is_untouched]

if __name__ == "__main__":
    world = World()
    try:
        for fn in TEETH:
            _tooth(fn.__name__, fn, world)
    finally:
        world.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
