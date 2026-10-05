"""Proof for ticket be4a7b3c7caa — the base tool defines the testing mark once, and an emission
born under it carries it.

Child 1 of 71d1bbfa98b0 (everything born of a test is flagged), split per component under RULE 1
(Akien, 2026-10-01). Test against live, marked as testing (ruled 2026-09-28, extended
2026-10-04): every test output carries a mark so it can be thrown away. The mark has two faces,
and both get exactly one definition here, in cairn/tools/base/origin.py:
  - a PROCESS mark: the tester sets CAIRN_TESTER_ORIGIN=<run id> in a proof's environment, and
    test_origin() reads it as {"kind": "test", "run": <id>};
  - a NAME mark: a name a test puts on the live bus starts "testing-", and is_testing_name()
    says so.

This proof measures only cairn/tools/base (RULE 1: a ticket's proofs measure its own component).

  1. THE PROCESS MARK READS ONE WAY. With CAIRN_TESTER_ORIGIN set to a run id, test_origin()
     returns {"kind": "test", "run": that id}; unset or empty, it returns None.
  2. THE NAME MARK READS ONE WAY. is_testing_name() is True for "testing-<anything>" and False
     for a live device id, an empty string and a non-string.
  3. AN EMISSION BORN UNDER THE MARK CARRIES IT. A DiagnosticBase subclass held in memory emits
     a record carrying origin == test_origin() while the env is set, and no origin key when not.
  4. THE MODULE IS PUBLIC. cairn.tools.base.origin is listed in the base tool's charter
     public_interface, so another component importing it is no encapsulation breach.

    python3 cairn/tools/base/proofs/test_origin_marks_what_a_test_bore.py   # exit 0 = green
"""
import importlib
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"be4a7b3c7caa": {"1": "the_process_mark_reads_one_way",
                           "2": "the_name_mark_reads_one_way",
                           "3": "an_emission_born_under_the_mark_carries_it",
                           "4": "the_module_is_public"}}

ENV = "CAIRN_TESTER_ORIGIN"
RUN = "testing-be4a7b3c7caa-run"
PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    saved = os.environ.get(ENV)
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
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = saved


def _origin():
    return importlib.import_module("cairn.tools.base.origin")


def the_process_mark_reads_one_way():
    o = _origin()
    os.environ[ENV] = RUN
    assert o.test_origin() == {"kind": "test", "run": RUN}, o.test_origin()
    os.environ[ENV] = ""
    assert o.test_origin() is None, "an empty mark is no mark"
    os.environ.pop(ENV, None)
    assert o.test_origin() is None, "an unset mark is no mark"


def the_name_mark_reads_one_way():
    o = _origin()
    assert o.is_testing_name("testing-be4a7b3c7caa-sysrm-0f0f0f0f") is True
    for live in ("system_rackmount", "trouble", "", None, 7, "a-testing-name"):
        assert o.is_testing_name(live) is False, f"{live!r} is not a testing name"


def an_emission_born_under_the_mark_carries_it():
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Held(DiagnosticBase):
        pass

    dev = _Held()
    dev.set_diagnostic_receiver(None)       # HOLD: the record stays in memory, nothing reaches disk
    os.environ[ENV] = RUN
    marked = dev.emit("testing-be4a7b3c7caa-gate")
    assert marked.get("origin") == {"kind": "test", "run": RUN}, marked
    os.environ.pop(ENV, None)
    plain = dev.emit("testing-be4a7b3c7caa-gate")
    assert "origin" not in plain, plain


def the_module_is_public():
    charter = json.loads((_REPO_ROOT / "cairn" / "tools" / "base" / ("intention" + "+why.json")).read_text())
    assert "cairn.tools.base.origin" in (charter.get("public_interface") or []), \
        "cairn.tools.base.origin is not in the base tool's public_interface"


TEETH = [the_process_mark_reads_one_way, the_name_mark_reads_one_way,
         an_emission_born_under_the_mark_carries_it, the_module_is_public]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
