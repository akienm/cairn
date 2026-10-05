"""Proof for ticket be4a7b3c7caa — the base tool defines the testing mark once, and the mark
carries a KIND.

Child of 71d1bbfa98b0, split per component under RULE 1 (Akien, 2026-10-01), reshaped
2026-10-05 by Akien's re-plan (~/.cairn/foreground-decisions.md items 8c-8e). How a consumer
tolerates a testing artifact is RETURN TO SENDER, Akien verbatim: "code mother should return it
to the tester ... "Yep, got here" is implicit in the return. so the tester would see that it's a
returning message, from test abcdefg, and that test can now be marked complete." And where:
"the shim. device gets the "perform this test" kind later". So the mark is {kind, test}; today the
only kind is "return", and a future "perform this test" kind must fit without a reshape.

The first build stamped every DiagnosticBase emission with a process mark. Measured 2026-10-05:
no production code reads that stamp, and its one named consumer (a tester debris census) is
superseded by the tester killing what it started and sweeping the rest to logging (8d). A stamp
nobody reads goes, so tooth 3 holds its absence.

This proof measures only cairn/tools/base (RULE 1).

  1. A MARK IS BUILT ONE WAY. mark("t") is {"kind": "return", "test": "t"}; an empty test id
     and a kind other than "return" are refused (nothing builds the future kind yet).
  2. A MARK IS READ ONE WAY. mark_of() returns the mark riding under FIELD on an artifact, and
     None for an artifact without one, a non-dict, an empty test id or an empty kind. A
     well-formed mark of a kind this code does not know is still returned, so the future kind
     reads as a mark and its handling stays the reader's choice.
  3. NO EMISSION IS STAMPED. A held DiagnosticBase emission carries neither "origin" nor FIELD,
     even with CAIRN_TESTER_ORIGIN set.
  4. ONE DEFINITION, AND IT IS PUBLIC. cairn.tools.base.testing_mark is in the base tool's
     charter public_interface; cairn.tools.base.origin is not, and does not import.

    python3 cairn/tools/base/proofs/test_the_testing_mark_carries_a_kind.py   # exit 0 = green
"""
import importlib
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"be4a7b3c7caa": {"1": "a_mark_is_built_one_way",
                           "2": "a_mark_is_read_one_way",
                           "3": "no_emission_is_stamped",
                           "4": "one_definition_and_it_is_public"}}

TEST = "testing-be4a7b3c7caa-test"
PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    saved = os.environ.get("CAIRN_TESTER_ORIGIN")
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")
    finally:
        if saved is None:
            os.environ.pop("CAIRN_TESTER_ORIGIN", None)
        else:
            os.environ["CAIRN_TESTER_ORIGIN"] = saved


def _tm():
    return importlib.import_module("cairn.tools.base.testing_mark")


def _refused(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def a_mark_is_built_one_way():
    tm = _tm()
    assert tm.RETURN == "return" and tm.KINDS == ("return",), (tm.RETURN, tm.KINDS)
    assert tm.mark(TEST) == {"kind": "return", "test": TEST}, tm.mark(TEST)
    assert _refused(lambda: tm.mark("")), "an empty test id was not refused"
    assert _refused(lambda: tm.mark(TEST, kind="perform")), "a kind nothing builds was not refused"


def a_mark_is_read_one_way():
    tm = _tm()
    m = tm.mark(TEST)
    assert tm.mark_of({"verb": "x", tm.FIELD: m}) == m
    future = {"kind": "perform", "test": TEST}
    assert tm.mark_of({tm.FIELD: future}) == future, "a well-formed future kind must still read as a mark"
    for bad in ({}, {"verb": "x"}, None, "x", {tm.FIELD: "return"}, {tm.FIELD: {"kind": "return", "test": ""}},
                {tm.FIELD: {"kind": "", "test": TEST}}, {tm.FIELD: {"test": TEST}}):
        assert tm.mark_of(bad) is None, f"{bad!r} is not a marked artifact"


def no_emission_is_stamped():
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Held(DiagnosticBase):
        pass

    dev = _Held()
    dev.set_diagnostic_receiver(None)       # HOLD: the record stays in memory, nothing reaches disk
    os.environ["CAIRN_TESTER_ORIGIN"] = TEST
    rec = dev.emit("testing-be4a7b3c7caa-gate")
    assert "origin" not in rec and "testing" not in rec, rec


def one_definition_and_it_is_public():
    charter = json.loads((_REPO_ROOT / "cairn" / "tools" / "base" / ("intention" + "+why.json")).read_text())
    public = charter.get("public_interface") or []
    assert "cairn.tools.base.testing_mark" in public, "cairn.tools.base.testing_mark is not public"
    assert "cairn.tools.base.origin" not in public, "cairn.tools.base.origin is still public"
    try:
        importlib.import_module("cairn.tools.base.origin")
    except ModuleNotFoundError:
        return
    raise AssertionError("cairn.tools.base.origin still imports — two definitions of the mark")


TEETH = [a_mark_is_built_one_way, a_mark_is_read_one_way, no_emission_is_stamped,
         one_definition_and_it_is_public]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
