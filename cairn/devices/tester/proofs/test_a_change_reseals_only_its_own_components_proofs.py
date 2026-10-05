"""Proof for ticket 3e80b61b7acf: a staged change re-runs only the proofs of the component
that owns it, never the proofs of components that merely import it.

Akien answered 2026-10-05 (~/.cairn/foreground-decisions.md item 7), verbatim: "tool proofs:
agreed" — option 1 of "when a tool changes, should the proofs of components that use it re-run?":
no, only the tool's own proofs. MEASURED before the question: b9a7d9e5 changed one line in
liveness.py with no value change, and the pre-commit reseal re-ran 55 proofs across 19
components (1 of them liveness's own), with 1 timeout and 57 files in the commit. MEASURED
again 2026-10-05 on be4a7b3c7caa: a commit touching cairn/tools/base/diagnostic.py ran its
pre-commit reseal past a 30-minute limit without landing.

``reseal.proofs_touching`` is the door that decides the reach. Today it crosses components two
ways: a seal carrying an import closure is touched by any staged file in that closure (so a
tool's edit reaches every user of the tool), and a seal predating closures is touched by any
staged file under the component's directory (so a nested machine's edit reaches its holder).
Both teeth that fail today are those two crossings; the owner of a staged path is
``cairn.tools.base.address.component_of`` — the deepest component ancestor.

This proof measures only cairn/devices/tester (RULE 1). Teeth 1-3 hand ``proofs_touching``
census rows directly over real component paths; tooth 4 asks the live census.

  1. A USER'S PROOF IS NOT TOUCHED BY ITS TOOL'S CHANGE. A tester proof whose seal's closure
     names cairn/tools/base/diagnostic.py is not returned for a staged diagnostic.py.
  2. THE CHANGED COMPONENT'S OWN PROOFS ARE TOUCHED. The same proof is returned for a staged
     cairn/devices/tester/reseal.py, under a closure seal and under a pre-closure seal alike.
  3. A NESTED COMPONENT'S CHANGE DOES NOT TOUCH ITS HOLDER. A cairn-device proof (pre-closure
     seal) is not returned for a staged cairn/devices/cairn/machines/bus/bus.py.
  4. ON THE LIVE CENSUS THE REACH STOPS AT THE OWNER. For a staged diagnostic.py, every proof
     returned belongs to cairn/tools/base.

    python3 cairn/devices/tester/proofs/test_a_change_reseals_only_its_own_components_proofs.py
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"3e80b61b7acf": {"1": "a_users_proof_is_not_touched_by_its_tools_change",
                          "2": "the_changed_components_own_proofs_are_touched",
                          "3": "a_nested_components_change_does_not_touch_its_holder",
                          "4": "on_the_live_census_the_reach_stops_at_the_owner"}}

R = _REPO_ROOT
TOOL_FILE = "cairn/tools/base/diagnostic.py"
TESTER = R / "cairn/devices/tester"
TESTER_PROOF = TESTER / "proofs/test_reseal_door.py"
HOLDER = R / "cairn/devices/cairn"
HOLDER_PROOF = HOLDER / "proofs/test_cairn_device.py"
NESTED_FILE = "cairn/devices/cairn/machines/bus/bus.py"
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


def _closure_seal(*files):
    return {"evidence": {"fingerprint_closure": [str(TESTER_PROOF.relative_to(R)), *files]}}


def _touching(staged, rows):
    from cairn.devices.tester.reseal import proofs_touching
    return proofs_touching(staged, root=R, rows=rows)


def a_users_proof_is_not_touched_by_its_tools_change():
    rows = [{"proof": TESTER_PROOF, "component": TESTER,
             "seal": _closure_seal(TOOL_FILE, "cairn/devices/tester/reseal.py")}]
    got = _touching([TOOL_FILE], rows)
    assert got == [], f"a tool's change reached a user's proof: {got}"


def the_changed_components_own_proofs_are_touched():
    staged = ["cairn/devices/tester/reseal.py"]
    for seal in (_closure_seal(TOOL_FILE, "cairn/devices/tester/reseal.py"), {}):
        got = _touching(staged, [{"proof": TESTER_PROOF, "component": TESTER, "seal": seal}])
        assert got == [TESTER_PROOF], f"seal {seal!r}: own change did not reach own proof: {got}"


def a_nested_components_change_does_not_touch_its_holder():
    rows = [{"proof": HOLDER_PROOF, "component": HOLDER, "seal": {}}]
    got = _touching([NESTED_FILE], rows)
    assert got == [], f"a nested machine's change reached its holder's proof: {got}"


def on_the_live_census_the_reach_stops_at_the_owner():
    from cairn.devices.tester.reseal import census
    from cairn.tools.base.address import component_of
    rows = census(R)
    by_proof = {row["proof"]: row["component"] for row in rows}
    got = _touching([TOOL_FILE], rows)
    owner = component_of(R / TOOL_FILE)
    foreign = sorted({str(Path(by_proof[p]).resolve().relative_to(R)) for p in got
                      if Path(by_proof[p]).resolve() != owner})
    assert not foreign, f"{len(foreign)} other component(s) reached: {foreign[:6]}"


TEETH = [a_users_proof_is_not_touched_by_its_tools_change,
         the_changed_components_own_proofs_are_touched,
         a_nested_components_change_does_not_touch_its_holder,
         on_the_live_census_the_reach_stops_at_the_owner]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
