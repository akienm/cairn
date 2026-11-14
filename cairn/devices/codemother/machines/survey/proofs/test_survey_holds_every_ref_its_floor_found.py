"""Proof for ticket c875e694f1b8 — a survey holds every orient ref its own floor found to exist.

Measured 2026-11-14: a survey berth whose orient refs named the ticket's own target file (which exists) and whose
ceiling-drafted holdings omitted it; decompose then refused the plan's own file as 'not a holding the survey berth
carries'. The survey door now appends each existing orient ref the ceiling left out (``hold_floor_refs``), tagged
``FLOOR_HELD``, and never removes or rewords the ceiling's own holdings.

The world is a scratch repo holding a copy of a real file at its real relative path, because the installed holdings
judge resolves an address against the real roster and is root-blind by design (as test_chart_survey says).

    python <this file>
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.machines.build_inspector.inspector import judge_decompose  # noqa: E402
from cairn.devices.codemother.machines.survey.survey import FLOOR_HELD, write_survey
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

REAL = "cairn/devices/codemother/machines/survey/survey.py"      # exists in the real repo and in the scratch copy

PROVES = {
    "c875e694f1b8": {
        "1": "an_existing_orient_ref_the_ceiling_left_out_is_held_and_decompose_accepts_it",
        "2": "a_missing_ref_is_not_added_and_the_ceilings_own_holdings_are_untouched",
    },
}


def _world():
    tmp = str(scratch_dir("survey_floor_refs_proof_"))
    root = os.path.join(tmp, "repo")
    dest = os.path.join(root, *REAL.split("/"))
    os.makedirs(os.path.dirname(dest))
    shutil.copyfile(REPO / REAL, dest)
    os.makedirs(os.path.join(tmp, "CairnCommons", "tickets"))
    berth_dir = os.path.join(root, "instance", "packets")
    os.makedirs(berth_dir)
    orient = os.path.join(berth_dir, "orient-20261114T000000-aaaaaaaaaaaa.json")
    with open(orient, "w", encoding="utf-8") as fh:
        json.dump({"intent": "sweep the survey door", "domain": "survey", "scope": "IN: survey. OUT: the rest.",
                   "refs": [REAL, "no/such/path.py"], "unknowns": [], "confidence": 0.8,
                   "provenance": {"intent": "cc", "domain": "cc", "scope": "cc", "refs": "floor", "unknowns": "cc"}}, fh)
    constrain = os.path.join(berth_dir, "constrain-20261114T000001-bbbbbbbbbbbb.json")
    with open(constrain, "w", encoding="utf-8") as fh:
        json.dump({"intent_ref": orient, "constraints": [{"text": "survey only", "source": "alpha", "kind": "charter"}],
                   "bounds": {"in": ["survey"], "out": []}, "unknowns": [], "confidence": 0.75,
                   "provenance": {"intent_ref": "floor", "constraints": "cc", "bounds": "cc", "unknowns": "cc"}}, fh)
    return tmp, root, constrain


def _packet(constrain):
    return {"constrain_ref": constrain, "sought": ["what the survey door holds"],
            "holdings": [{"what": "the settled chart machinery", "address": "base"}],
            "absences": [{"what": "a floor merge", "measure": "survey.py has no merge step"}],
            "unknowns": ["none"], "confidence": 0.7,
            "provenance": {"constrain_ref": "floor", "sought": "cc", "holdings": "floor", "absences": "cc",
                           "unknowns": "cc"}}


def an_existing_orient_ref_the_ceiling_left_out_is_held_and_decompose_accepts_it() -> None:
    tmp, root, constrain = _world()
    try:
        berth_dir = os.path.join(root, "instance", "survey_berth")
        path = write_survey(_packet(constrain), instance_dir=berth_dir, root=root)
        berth = json.load(open(path, encoding="utf-8"))
        held = {h["address"]: h["what"] for h in berth["holdings"]}
        assert held.get(REAL) == FLOOR_HELD, f"the existing orient ref is not held by the berthed survey: {held}"
        plan = {"survey_ref": path, "sub_problems": [
            {"what": "edit the survey door", "why": "the plan's own file", "kind": "compose", "uses": [REAL],
             "writes_to": [REAL]}]}
        frags = [f for a in judge_decompose(plan) for f in a["findings"] if "not a holding" in f["finding"]]
        assert not frags, f"decompose still refuses the file as not a holding: {frags}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def a_missing_ref_is_not_added_and_the_ceilings_own_holdings_are_untouched() -> None:
    tmp, root, constrain = _world()
    try:
        packet = _packet(constrain)
        own = json.loads(json.dumps(packet["holdings"]))
        path = write_survey(packet, instance_dir=os.path.join(root, "instance", "survey_berth"), root=root)
        berth = json.load(open(path, encoding="utf-8"))
        addrs = [h["address"] for h in berth["holdings"]]
        assert "no/such/path.py" not in addrs, f"a ref the floor did not find was added: {addrs}"
        assert berth["holdings"][:len(own)] == own, "the ceiling's own holdings were removed or reworded"
        assert addrs.count(REAL) == 1, f"the floor ref was added {addrs.count(REAL)} times"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TEETH = [an_existing_orient_ref_the_ceiling_left_out_is_held_and_decompose_accepts_it,
         a_missing_ref_is_not_added_and_the_ceilings_own_holdings_are_untouched]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:500]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
