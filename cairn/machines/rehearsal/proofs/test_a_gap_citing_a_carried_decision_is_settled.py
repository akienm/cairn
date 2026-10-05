"""Proof for ticket fac1e0dc8f46 — a reader's citation of a carried decision settles its step.

Akien, open-ba8f0eaca8cd (2026-10-05): *"yes on ba8f0eaca8cd, with that condition"* — a gap
counts as settled when its assumption names a decision id in the same ticket AND that id
resolves to a decision there. ``gaps(reads, decision_ids)`` reads it: a builds_under_assumption
node whose assumption names ANOTHER carried id raises no ``assumes`` gap and joins no
``assumption_differs`` comparison. An uncarried id, the step's own id, and a cannot_proceed
node stay gaps; with no ids nothing settles.

Fixtures are the sibling proof's (``test_rehearsal.World`` and friends — the fixture ticket
carries D1 and D2); no tooth reads the live commons or calls the live reader. The machine is
resolved at CALL time inside each tooth, so a reverted build reds teeth instead of killing
the import.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.machines.rehearsal.proofs.test_rehearsal import World, Stub, TID, _kw, _node  # noqa: E402

PROVES = {
    "fac1e0dc8f46": {
        "1": "test_a_citation_of_a_carried_decision_settles_the_step",
        "2": "test_a_citation_of_an_uncarried_id_stays_a_gap",
        "3": "test_a_citation_of_the_steps_own_id_stays_a_gap",
        "4": "test_a_cannot_proceed_node_never_settles",
        "5": "test_without_ids_nothing_settles",
        "6": "test_a_rehearsal_whose_readers_cite_d1_is_clean",
    },
}

CITE = ["as specified in D1", "D1 gives the widget, so D2 proves it", "follows D1's text"]
IDS = {1, 2}


def _R():
    return importlib.import_module("cairn.machines.rehearsal.rehearsal")


def _reads(texts, state="builds_under_assumption", step="D2"):
    return [{"read": i + 1, "nodes": [_node("D1"), _node(step, state, texts[i], "")]}
            for i in range(3)]


def _kinds(found):
    return {(g["kind"], g["step"]) for g in found}


def test_a_citation_of_a_carried_decision_settles_the_step():
    found = _R().gaps(_reads(CITE), IDS)
    assert found == [], found


def test_a_citation_of_an_uncarried_id_stays_a_gap():
    found = _R().gaps(_reads([t.replace("D1", "D9") for t in CITE]), IDS)
    assert ("assumes", "D2") in _kinds(found), found


def test_a_citation_of_the_steps_own_id_stays_a_gap():
    found = _R().gaps(_reads(["D2 says prove it", "per D2", "D2 as written"]), IDS)
    assert ("assumes", "D2") in _kinds(found), found


def test_a_cannot_proceed_node_never_settles():
    found = _R().gaps(_reads(CITE, state="cannot_proceed"), IDS)
    assert ("cannot_proceed", "D2") in _kinds(found), found


def test_without_ids_nothing_settles():
    k = _kinds(_R().gaps(_reads(CITE)))
    assert ("assumes", "D2") in k and ("assumption_differs", "D2") in k, k


def test_a_rehearsal_whose_readers_cite_d1_is_clean():
    w = World()
    try:
        trees = [{"nodes": [_node("D1"), _node("D2", "builds_under_assumption", c)]} for c in CITE]
        rec = _R().rehearse(TID, reader=Stub(trees), **_kw(w))
        assert rec["clean"] and rec["gaps"] == [], rec["gaps"]
    finally:
        w.close()


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
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
    print(f"green — {len(teeth)} teeth: a citation of a carried decision settles its step; an "
          "uncarried id, the step's own id and a cannot_proceed node stay gaps; without ids "
          "nothing settles; a rehearsal whose readers cite D1 is clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
