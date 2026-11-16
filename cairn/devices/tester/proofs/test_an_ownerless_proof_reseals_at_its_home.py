"""Proof for ticket 38dc3a0f93b1: a proof outside cairn/{tools,machines,devices} belongs to its HOME —
the directory holding its proofs/ — so its seal's closure stops at that home and a commit
touching the home reseals it, the same rule a component's proofs already obey.

MEASURED 2026-11-16 on main 4df676bab. ``address.component_of`` knows only the cairn rungs, so it
returns None for skills/sail/proofs/test_sail_door.py and for 69 other proofs (31 under bin/, 2
under press_office/, 37 across 13 skills). Two consequences, both measured:
  - ``validation_store._owned_by_the_proofs_component`` keeps "the whole closure" for a proof
    under no component, so test_sail_door's seal named cairn/machines/learning_block/
    learning_block.py, and f64b87bf0f67's commit c0e3f9428 staled it;
  - ``reseal.proofs_touching`` drops a staged file whose owner is None, so nothing could select
    it — not even an edit to skills/sail/door.py itself.
The lived symptom: 6095 (q164, test_sail_door) and 40e4 (q147, test_sorted_probes) each refused
at close on a seal gone stale on main, a walk apiece.

Akien's 2026-10-05 answer stands (~/.cairn/foreground-decisions.md item 7, "tool proofs:
agreed"): a tool's change re-runs only the tool's own proofs. So a home's proofs re-run on the
home's change, never on learning_block's.

This proof measures cairn/devices/tester's door (RULE 1), reaching validation_store only through
its public ``repo_relative_closure``. Census rows are handed in directly over real paths.

  1. THE CLOSURE STOPS AT THE HOME. A closure taken for test_sail_door and for
     test_sorted_probes_report_to_the_watch over a raw list naming learning_block.py,
     diagnostic.py and the skill's own door.py keeps only the proof and the home's own file.
  2. THE HOME'S OWN EDIT RESEALS ITS PROOF. A staged skills/sail/door.py returns test_sail_door
     under a closure seal and under a pre-closure seal alike; a staged bin file returns a bin
     proof.
  3. A FOREIGN EDIT TOUCHES NO HOME, AND AN OWNER'S REACH IS UNCHANGED. A staged learning_block.py
     returns no skill proof; a staged diagnostic.py returns the tools/base proof and no other.

    PYTHONPATH=. python3 cairn/devices/tester/proofs/test_an_ownerless_proof_reseals_at_its_home.py
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"38dc3a0f93b1": {"1": "the_closure_stops_at_the_home",
                       "2": "the_homes_own_edit_reseals_its_proof",
                       "3": "a_foreign_edit_touches_no_home_and_an_owners_reach_is_unchanged"}}

R = _REPO_ROOT
FOREIGN = "cairn/machines/learning_block/learning_block.py"
TOOL = "cairn/tools/base/diagnostic.py"
SAIL = R / "skills/sail"
SAIL_PROOF = SAIL / "proofs/test_sail_door.py"
SORTED = R / "skills/sorted"
SORTED_PROOF = SORTED / "proofs/test_sorted_probes_report_to_the_watch.py"
BIN = R / "bin"
BIN_PROOF = BIN / "proofs/test_a_word_with_no_script_goes_onto_the_bus.py"
BASE = R / "cairn/tools/base"
BASE_PROOF = BASE / "proofs/test_address_rule.py"
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


def _rel(p):
    return str(Path(p).relative_to(R))


def _closure_seal(proof, *files):
    return {"evidence": {"fingerprint_closure": [_rel(proof), *files]}}


def _touching(staged, rows):
    from cairn.devices.tester.reseal import proofs_touching
    return proofs_touching(staged, root=R, rows=rows)


def the_closure_stops_at_the_home():
    from cairn.tools.validation_store.validation_store import repo_relative_closure
    for proof, own in ((SAIL_PROOF, "skills/sail/door.py"), (SORTED_PROOF, "skills/sorted/door.py")):
        assert proof.is_file() and (R / own).is_file(), f"fixture moved: {proof} / {own}"
        raw = [str(R / FOREIGN), str(R / TOOL), str(R / own), str(proof)]
        got = repo_relative_closure(raw, str(proof))
        assert got == sorted([own, _rel(proof)]), f"{_rel(proof)}: closure crossed its home: {got}"


def the_homes_own_edit_reseals_its_proof():
    for seal in (_closure_seal(SAIL_PROOF, FOREIGN, "skills/sail/door.py"), {}):
        got = _touching(["skills/sail/door.py"],
                        [{"proof": SAIL_PROOF, "component": SAIL, "seal": seal}])
        assert got == [SAIL_PROOF], f"seal {seal!r}: the home's own edit did not reach its proof: {got}"
    assert BIN_PROOF.is_file(), f"fixture moved: {BIN_PROOF}"
    got = _touching(["bin/cmd/trash"], [{"proof": BIN_PROOF, "component": BIN, "seal": {}},
                                        {"proof": SAIL_PROOF, "component": SAIL, "seal": {}}])
    assert got == [BIN_PROOF], f"a bin edit reached {got}, not exactly bin's proof"


def a_foreign_edit_touches_no_home_and_an_owners_reach_is_unchanged():
    rows = [{"proof": SAIL_PROOF, "component": SAIL, "seal": _closure_seal(SAIL_PROOF, FOREIGN, TOOL)},
            {"proof": SORTED_PROOF, "component": SORTED, "seal": _closure_seal(SORTED_PROOF, TOOL)},
            {"proof": BASE_PROOF, "component": BASE, "seal": _closure_seal(BASE_PROOF, TOOL)}]
    assert BASE_PROOF.is_file(), f"fixture moved: {BASE_PROOF}"
    got = _touching([FOREIGN], rows)
    assert got == [], f"learning_block's edit reached a home's proof: {got}"
    got = _touching([TOOL], rows)
    assert got == [BASE_PROOF], f"diagnostic.py's edit reached {got}, not exactly tools/base's proof"


TEETH = [the_closure_stops_at_the_home,
         the_homes_own_edit_reseals_its_proof,
         a_foreign_edit_touches_no_home_and_an_owners_reach_is_unchanged]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
