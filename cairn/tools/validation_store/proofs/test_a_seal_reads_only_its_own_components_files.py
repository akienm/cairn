"""Proof for ticket 184d211153ff: a seal's import closure records only the files owned by the
proof's own component, so a change to a tool a component imports no longer moves that
component's seal.

The sibling of 3e80b61b7acf (the reseal door re-runs only the owning component's proofs). Akien
answered 2026-10-05, "tool proofs: agreed" (~/.cairn/foreground-decisions.md item 7). With only
the door narrowed, a tool's edit would still move every user's seal — component_color reds them
and nothing would re-run them: a red with no path to green (the peer akiendelllinux_cc_0, 2026-10-05,
deriving from RULE 1 and Akien's "then what files changed elsewhere doesn't matter one whit").
MEASURED 2026-10-05 at HEAD 94334efb: 336 of 342 standing seals carry a closure naming files
owned by another component, 7,543 foreign entries in all.

The narrowing is at the point a closure is TAKEN (``repo_relative_closure``). A seal is re-read
under the recipe it recorded (``sealed_fingerprint_now``), so a seal taken before this build
keeps reading its own wider closure until it is resealed — nothing expires at once.

This proof measures only cairn/tools/validation_store (RULE 1).

  1. A CLOSURE DROPS ANOTHER COMPONENT'S FILE. Taken for a tester proof over a raw list naming
     cairn/tools/base/diagnostic.py, the closure does not contain it.
  2. IT KEEPS ITS OWN. The same closure keeps cairn/devices/tester/reseal.py and the proof itself.
  3. A HOLDER'S CLOSURE DROPS ITS NESTED MACHINE. Taken for a cairn-device proof over a raw list
     naming cairn/devices/cairn/machines/bus/bus.py, the closure does not contain it.
  4. AN OLD SEAL STILL READS UNDER ITS OWN RECIPE. A seal whose recorded closure names a foreign
     file is re-taken over exactly that recorded closure (``sealed_fingerprint_now`` equals
     ``source_fingerprint(proof, closure=<recorded>)``), so no standing seal expires by this build.

    python3 cairn/tools/validation_store/proofs/test_a_seal_reads_only_its_own_components_files.py
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"184d211153ff": {"1": "a_closure_drops_another_components_file",
                           "2": "it_keeps_its_own",
                           "3": "a_holders_closure_drops_its_nested_machine",
                           "4": "an_old_seal_still_reads_under_its_own_recipe"}}

R = _REPO_ROOT
TOOL_FILE = "cairn/tools/base/diagnostic.py"
OWN_FILE = "cairn/devices/tester/reseal.py"
TESTER_PROOF = "cairn/devices/tester/proofs/test_reseal_door.py"
HOLDER_PROOF = "cairn/devices/cairn/proofs/test_cairn_device.py"
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


def _closure(proof, *files):
    from cairn.tools.validation_store.validation_store import repo_relative_closure
    return repo_relative_closure([str(R / f) for f in files], str(R / proof))


def a_closure_drops_another_components_file():
    got = _closure(TESTER_PROOF, TOOL_FILE, OWN_FILE)
    assert TOOL_FILE not in got, f"a tool's file stayed in a user's closure: {got}"


def it_keeps_its_own():
    got = _closure(TESTER_PROOF, TOOL_FILE, OWN_FILE)
    assert OWN_FILE in got and TESTER_PROOF in got, f"own files missing from the closure: {got}"


def a_holders_closure_drops_its_nested_machine():
    got = _closure(HOLDER_PROOF, NESTED_FILE)
    assert NESTED_FILE not in got, f"a nested machine's file stayed in its holder's closure: {got}"


def an_old_seal_still_reads_under_its_own_recipe():
    from cairn.tools.validation_store.validation_store import (
        sealed_fingerprint_now, source_fingerprint)
    recorded = sorted([TESTER_PROOF, OWN_FILE, TOOL_FILE])
    seal = {"evidence": {"fingerprint_closure": recorded}}
    proof = str(R / TESTER_PROOF)
    want = source_fingerprint(proof, closure=recorded)
    got = sealed_fingerprint_now(proof, seal)
    assert got == want, "an old seal was not re-taken over the closure it recorded"


TEETH = [a_closure_drops_another_components_file, it_keeps_its_own,
         a_holders_closure_drops_its_nested_machine, an_old_seal_still_reads_under_its_own_recipe]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
