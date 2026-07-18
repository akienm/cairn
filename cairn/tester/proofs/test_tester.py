"""Proof for the TesterDevice — the first real device on the spine.

The minimal provable stone: a device that runs a proof and produces a VALIDATION
record (MAP.md:569 — claim, caller, date, method, verdict, evidence, falsifier,
horizon). Teeth a hollow tester could not pass:

  - it calls a KNOWN-GREEN proof green AND a KNOWN-RED proof red. An always-green
    tester (the classic hollow build) passes every other check and dies on the red
    case: the verdict is read from the subject's exit code, not granted by goodwill.
  - the VALIDATION carries exactly the ratified eight fields — a drifted record reds.
  - it is the FIRST real subject of the base's armed composition trap
    (base/proofs/test_composition.py, which read "0 subclasses" until now). We
    import the tester and run that sweep here, exercising it on a real device.

Runnable bare (the tester will one day own how proofs run; today it runs like its
siblings):
    python3 cairn/tester/proofs/test_tester.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

# Run bare without an editable install: repo root on the path so `cairn` imports.
# parents[3] is the repo root (fixtures? no — this file is proofs/test_tester.py:
# proofs -> tester -> cairn pkg -> repo).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CoreValuesMixin
from cairn.base.device import BaseDevice
from cairn.tester.device import GREEN, RED, VALIDATION_FIELDS, TesterDevice

EXPECTED_IDS = ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_GREEN_FIXTURE = _FIXTURES / "green_proof.py"
_RED_FIXTURE = _FIXTURES / "red_proof.py"


def _all_subclasses(cls: type) -> set:
    seen: set = set()
    stack = list(cls.__subclasses__())
    while stack:
        sub = stack.pop()
        if sub not in seen:
            seen.add(sub)
            stack.extend(sub.__subclasses__())
    return seen


def test_tester_is_a_device_carrying_the_values():
    # It rides the Form: a BaseDevice subclass, so it carries CP1-CP6 structurally,
    # and it is concrete (implements the whole Form v0 #2 surface — instantiable).
    assert issubclass(TesterDevice, BaseDevice)
    assert issubclass(TesterDevice, CoreValuesMixin)
    assert [v.id for v in TesterDevice.CORE_VALUES] == EXPECTED_IDS
    assert isinstance(TesterDevice(), BaseDevice)


def test_introspect_reports_the_form_in_order():
    surface = TesterDevice().introspect()
    assert list(surface.keys()) == ["intention", "state", "settings", "other"]
    for key in ("intention", "state", "settings"):
        assert isinstance(surface[key], dict), f"{key} must be a dict (Form v0 #2)"


def test_green_proof_validates_green():
    v = TesterDevice().run_proof(_GREEN_FIXTURE)
    assert set(v) == set(VALIDATION_FIELDS), f"VALIDATION must carry exactly the 8 fields, got {sorted(v)}"
    assert v["verdict"] == GREEN
    assert v["evidence"]["returncode"] == 0
    assert v["date"], "a VALIDATION must be dated (Law 3: it expires)"


def test_red_proof_validates_red():
    # The hollow-tester killer. An always-green tester passes everything above and
    # dies here — the verdict is read from the subject, not granted by the tester.
    v = TesterDevice().run_proof(_RED_FIXTURE)
    assert v["verdict"] == RED, "a failing proof MUST validate red — else the tester is hollow"
    assert v["evidence"]["returncode"] != 0


def test_state_reflects_the_runs():
    t = TesterDevice()
    assert t.state()["proofs_run"] == 0
    assert t.state()["last_verdict"] is None
    t.run_proof(_GREEN_FIXTURE)
    t.run_proof(_RED_FIXTURE)
    assert t.state()["proofs_run"] == 2
    assert t.state()["last_verdict"] == RED


def test_it_exercises_the_bases_armed_trap():
    # With TesterDevice imported, the base's subclass sweep now covers a REAL device
    # for the first time (it read "0 subclasses — armed, not exercised" until now).
    assert TesterDevice in _all_subclasses(BaseDevice)
    sys.path.insert(0, str(_REPO_ROOT / "cairn" / "base" / "proofs"))
    import test_composition as base_comp  # noqa: E402

    base_comp.test_no_subclass_lacks_the_values()  # green: the tester carries the six
    assert base_comp._swept_subclass_count() >= 1, "the tester should now be a swept subject"


def _main() -> int:
    checks = [
        test_tester_is_a_device_carrying_the_values,
        test_introspect_reports_the_form_in_order,
        test_green_proof_validates_green,
        test_red_proof_validates_red,
        test_state_reflects_the_runs,
        test_it_exercises_the_bases_armed_trap,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    # Dogfood: the tester's first real act is to validate the actual base proofs.
    print("  --- dogfood: the tester validates the real base proofs ---")
    t = TesterDevice()
    for name in ("test_core_values.py", "test_composition.py"):
        v = t.run_proof(_REPO_ROOT / "cairn" / "base" / "proofs" / name)
        print(f"    VALIDATION  {v['verdict']:5}  {v['claim']}")
    print("green — TesterDevice runs proofs and emits VALIDATIONS; the red case bites")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
