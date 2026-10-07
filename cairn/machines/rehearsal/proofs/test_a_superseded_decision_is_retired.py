"""Proof for ticket 4968b5d18645 — a superseded decision line is retired through the rehearsal
door: the reader stops being handed it, and the file keeps its text and who retired it.

Measured 2026-10-06 on 45c168cc1ff1: ``--decide`` only appends, so D22, D31 and D32 each
corrected D3 while D3's wrong text stayed on the ticket, and round 9 returned 'cannot_proceed D3
... D3's instructions are explicitly retired by D31 and contradicted by D32'. The fix was folded
by hand (F5, commons 35fa25a); this is the door that does it instead.

Every tooth runs over its own SCRATCH commons holding one ticket (testing-marked, removed at
exit); none reads the live corpus or calls a reader.

  1. RETIRED LINES LEAVE THE VIEW AND STAY IN THE FILE. After decide() of a corrected D5 and
     retire([3, 22], into=5), reader_view's copy holds neither text, decision_ids_of omits 3
     and 22, and the file keeps both texts with retired.by/at/because/into.
  2. A FOREIGN AUTHOR'S LINE IS REFUSED. Retiring a line whose by is 'akien' with by='cc'
     refuses and writes nothing.
  3. A DANGLING CITATION IS REFUSED. Retiring D3 while a live D4 says 'per D3' refuses naming D4.
  4. A BAD INTO IS REFUSED. into an absent id, or a retired one, refuses.

    bin/cairn test cairn/machines/rehearsal/proofs/test_a_superseded_decision_is_retired.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"4968b5d18645": {"1": "retired_lines_leave_the_view_and_stay_in_the_file",
                           "2": "a_foreign_authors_line_is_refused",
                           "3": "a_dangling_citation_is_refused",
                           "4": "a_bad_into_is_refused"}}

TID = "4968f00dfeed"
STEM = f"{TID}-testing-4968b5d18645-superseded-decision-retired"
WRONG = "reseal the loop proof with plain bin/cairn test --seal"
PATCH = "do not plain-seal the loop proof; reseal it with --reseal --ruling"
RIGHT = "reseal the loop proof with --reseal --ruling open-feedfeedfeed; plain --seal refuses"


def _ticket(decisions):
    return {"id": TID, "title": "testing-4968b5d18645-superseded-decision-retired",
            "intention": "testing: a fixture ticket for the 4968b5d18645 proof",
            "decisions": decisions}


BASE = [
    {"n": 3, "text": WRONG, "by": "cc"},
    {"n": 4, "text": "push both repos", "by": "cc"},
    {"n": 22, "text": PATCH, "by": "cc", "step": "D3", "source": "rehearsal"},
]

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


class World:
    def __init__(self, decisions):
        from cairn.tools.scratch.scratch import scratch_dir
        self.dir = Path(scratch_dir("testing-4968b5d18645-retired-"))
        self.commons = self.dir / "CairnCommons"
        (self.commons / "tickets").mkdir(parents=True)
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.ticket.write_text(json.dumps(_ticket(decisions), indent=2) + "\n", encoding="utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def doc(self):
        return json.loads(self.ticket.read_text(encoding="utf-8"))


def _refuses(fn, *needles):
    from cairn.machines.rehearsal import rehearsal as R
    try:
        fn()
    except R.Refused as exc:
        for n in needles:
            assert n in str(exc), f"the refusal does not name {n!r}: {exc}"
        return
    raise AssertionError("retire did not refuse")


def retired_lines_leave_the_view_and_stay_in_the_file():
    from cairn.machines.rehearsal import rehearsal as R
    with World(BASE) as w:
        new = R.decide(TID, "D3", RIGHT, by="cc", root=w.commons)["n"]
        R.retire(TID, [3, 22], by="cc", because="folded into the corrected line", into=new,
                 root=w.commons)
        doc = w.doc()
        view = R.reader_view(w.ticket.read_bytes())
        assert WRONG not in view and PATCH not in view, f"a retired text is still handed to the reader: {view}"
        assert RIGHT in view, "the corrected line left the view"
        ids = R.decision_ids_of(doc)
        assert 3 not in ids and 22 not in ids and new in ids, f"vocabulary still owes a retired id: {ids}"
        by_n = {d["n"]: d for d in doc["decisions"]}
        assert by_n[3]["text"] == WRONG and by_n[22]["text"] == PATCH, "the file lost a retired text"
        for n in (3, 22):
            r = by_n[n].get("retired")
            assert isinstance(r, dict) and r.get("by") == "cc" and r.get("at") and r.get("because") \
                and r.get("into") == new, f"D{n} lacks its retired stamp: {r}"


def a_foreign_authors_line_is_refused():
    from cairn.machines.rehearsal import rehearsal as R
    with World([{"n": 1, "text": "his words", "by": "akien"}, {"n": 2, "text": "mine", "by": "cc"}]) as w:
        before = w.ticket.read_bytes()
        _refuses(lambda: R.retire(TID, [1], by="cc", because="superseded", root=w.commons), "D1")
        assert w.ticket.read_bytes() == before, "a refused retire wrote the ticket"


def a_dangling_citation_is_refused():
    from cairn.machines.rehearsal import rehearsal as R
    with World([{"n": 3, "text": WRONG, "by": "cc"},
                {"n": 4, "text": "seal the tester proof per D3", "by": "cc"}]) as w:
        before = w.ticket.read_bytes()
        _refuses(lambda: R.retire(TID, [3], by="cc", because="superseded", root=w.commons), "D4")
        assert w.ticket.read_bytes() == before, "a refused retire wrote the ticket"


def a_bad_into_is_refused():
    from cairn.machines.rehearsal import rehearsal as R
    with World(BASE) as w:
        before = w.ticket.read_bytes()
        _refuses(lambda: R.retire(TID, [22], by="cc", because="superseded", into=99, root=w.commons), "D99")
        assert w.ticket.read_bytes() == before, "a refused retire wrote the ticket"
        R.retire(TID, [22], by="cc", because="superseded", root=w.commons)
        mid = w.ticket.read_bytes()
        _refuses(lambda: R.retire(TID, [4], by="cc", because="superseded", into=22, root=w.commons), "D22")
        assert w.ticket.read_bytes() == mid, "a refused retire wrote the ticket"


TEETH = [retired_lines_leave_the_view_and_stay_in_the_file, a_foreign_authors_line_is_refused,
         a_dangling_citation_is_refused, a_bad_into_is_refused]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
