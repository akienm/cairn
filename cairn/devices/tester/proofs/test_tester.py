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
    python3 cairn/devices/tester/proofs/test_tester.py     # exit 0 = green
"""

from __future__ import annotations

import inspect
import json
import sys
import tempfile
from pathlib import Path

# Run bare without an editable install: repo root on the path so `cairn` imports.
# parents[3] is the repo root (fixtures? no — this file is proofs/test_tester.py:
# proofs -> tester -> cairn pkg -> repo).
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.core_values import CoreValuesMixin
from cairn.tools.base.device import BaseDevice
from cairn.devices.tester import validation_store as vs
from cairn.devices.tester.device import GREEN, RED, VALIDATION_FIELDS, TesterDevice

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
    v = TesterDevice().run_proof(_GREEN_FIXTURE, sink="none")
    assert set(v) == set(VALIDATION_FIELDS), f"VALIDATION must carry exactly the 8 fields, got {sorted(v)}"
    assert v["verdict"] == GREEN
    assert v["evidence"]["returncode"] == 0
    assert v["date"], "a VALIDATION must be dated (Law 3: it expires)"


def test_red_proof_validates_red():
    # The hollow-tester killer. An always-green tester passes everything above and
    # dies here — the verdict is read from the subject, not granted by the tester.
    v = TesterDevice().run_proof(_RED_FIXTURE, sink="none")
    assert v["verdict"] == RED, "a failing proof MUST validate red — else the tester is hollow"
    assert v["evidence"]["returncode"] != 0


def test_state_reflects_the_runs():
    t = TesterDevice()
    assert t.state()["proofs_run"] == 0
    assert t.state()["last_verdict"] is None
    t.run_proof(_GREEN_FIXTURE, sink="none")
    t.run_proof(_RED_FIXTURE, sink="none")
    assert t.state()["proofs_run"] == 2
    assert t.state()["last_verdict"] == RED


def test_it_exercises_the_bases_armed_trap():
    # With TesterDevice imported, the base's subclass sweep now covers a REAL device
    # for the first time (it read "0 subclasses — armed, not exercised" until now).
    assert TesterDevice in _all_subclasses(BaseDevice)
    sys.path.insert(0, str(_REPO_ROOT / "cairn" / "tools" / "base" / "proofs"))
    import test_composition as base_comp  # noqa: E402

    base_comp.test_no_subclass_lacks_the_values()  # green: the tester carries the six
    assert base_comp._swept_subclass_count() >= 1, "the tester should now be a swept subject"


def test_the_crossings_are_no_longer_silent():
    """The silent_device disposition (troubles/silent-devices-2026-07-27.json): the
    notary's crossing is the notary ACT — one breadcrumb per run_proof, red and green
    alike (a red is the notary working, not an anomaly of the notary). SILENCED below so the
    breadcrumbs hold — un-wired WRITES since 2026-08-18 (ticket a-device-logs-without-being-wired);
    Law 7 is unchanged, the record is never silently dropped, only its default home moved."""
    t = TesterDevice()
    t.set_diagnostic_receiver(None)
    assert t.held_diagnostics() == [], "construction is not a crossing"
    g = t.run_proof(_GREEN_FIXTURE, sink="none")
    t.run_proof(_RED_FIXTURE, sink="none")
    held = t.held_diagnostics()
    assert [h["gate"] for h in held] == ["run_proof", "run_proof"], (
        f"one breadcrumb per attestation, got {[h['gate'] for h in held]}"
    )
    assert held[0]["pointer"] == str(_GREEN_FIXTURE), \
        "the breadcrumb points at the proof that was attested"
    assert held[0]["values"] == {"verdict": GREEN, "seal": "open"}, \
        "thin values: verdict + seal — readable without opening the eight-field record"
    assert held[1]["values"]["verdict"] == RED, \
        "a red attestation breadcrumbs the same as a green — the notary narrates its acts, not its moods"
    assert all(h["home"] == "held" for h in held), \
        "with no receiver wired the records HOLD (Law 7) — never silently dropped"
    # The breadcrumb never carries the record of truth (the caller holds that).
    assert set(held[0]["values"]) == {"verdict", "seal"} and g["evidence"], \
        "the eight-field VALIDATION stays with the caller; the breadcrumb only points"


def test_run_proof_REQUIRES_a_sink_and_has_no_default_for_it():
    """THE TICKET'S THIRD FALSIFIER CLAUSE. run_proof produced the ratified record and
    DROPPED it, so every caller had to independently remember the store's door — and the
    callers who forgot are how six trails came to hold entries that never came through it.

    The fix is a required keyword, and the REQUIREDNESS is the whole fix. A default of any
    kind preserves the failure exactly: the caller who forgets is the caller who gets the
    default, and a default that seals is worse than one that doesn't — it would mint records
    of truth from every casual diagnostic run. So this asserts the absence of a default, not
    merely the presence of the parameter.

    'validations' persists through persist_validation and nothing else; run_proof composes
    nothing of its own on the way in, which is what keeps the store's one-door claim true."""
    sig = inspect.signature(TesterDevice.run_proof)
    assert "sink" in sig.parameters, "run_proof must take a sink"
    sink = sig.parameters["sink"]
    assert sink.kind is inspect.Parameter.KEYWORD_ONLY, "the sink is named at the call site"
    assert sink.default is inspect.Parameter.empty, (
        "the sink has a DEFAULT — the caller who forgets is the caller who gets it, which "
        "is the exact failure mode the required keyword exists to remove")

    t = TesterDevice()
    try:
        t.run_proof(_GREEN_FIXTURE)
    except TypeError as err:
        assert "sink" in str(err), err
    else:
        raise AssertionError("run_proof without a sink must raise, not guess")
    try:
        t.run_proof(_GREEN_FIXTURE, sink="somewhere")
    except ValueError as err:
        assert "sink" in str(err), err
    else:
        raise AssertionError("an unknown sink must raise — a sink is named, never guessed")

    # sink='none' writes nothing; sink='validations' lands through the door, eight fields,
    # with the link the DOOR minted (run_proof hands over the same record it returns).
    with tempfile.TemporaryDirectory() as tmp:
        proofs = Path(tmp) / "somecomp" / "proofs"
        proofs.mkdir(parents=True)
        stand_in = proofs / "test_thing.py"
        stand_in.write_text(_GREEN_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
        trail = Path(tmp) / "somecomp" / "validations" / "test_thing.json"

        t.run_proof(stand_in, sink="none")
        assert not trail.exists(), "sink='none' must write nothing at all"

        record = t.run_proof(stand_in, sink="validations")
        assert trail.exists(), "sink='validations' must land a VALIDATION beside the proof"
        landed = json.loads(trail.read_text(encoding="utf-8"))
        assert len(landed) == 1, landed
        assert set(landed[0]) == set(VALIDATION_FIELDS), (
            f"the sealing path must persist exactly the ratified eight: {sorted(landed[0])}")
        # WHAT LANDED IS WHAT WAS HANDED OVER, byte for byte. Until 2026-08-16 the door
        # minted a `trail_link` into evidence, so this asserted a difference between the
        # returned record and the stored one; the chain retired with the append-only-ness it
        # protected (ticket a-validation-is-one-current-record-not-a-trail), and the property
        # worth asserting inverted: run_proof hands the door the same record it hands back,
        # and the door decorates neither.
        assert landed[0]["evidence"] == record["evidence"], (
            "the record on disk and the record returned to the caller must be the same thing — "
            "two copies that can differ is how a store grows a rival source of truth")
        assert vs.standing(str(stand_in))["proven"], vs.standing(str(stand_in))["why"]


def _main() -> int:
    checks = [
        test_tester_is_a_device_carrying_the_values,
        test_introspect_reports_the_form_in_order,
        test_green_proof_validates_green,
        test_red_proof_validates_red,
        test_state_reflects_the_runs,
        test_it_exercises_the_bases_armed_trap,
        test_the_crossings_are_no_longer_silent,
        test_run_proof_REQUIRES_a_sink_and_has_no_default_for_it,
    ]
    # THE LIST IS HAND-TYPED HERE, SO THE FLOOR IS WHAT KEEPS IT HONEST. A tooth added to
    # this file and not added to the list never runs, and the file prints the same green
    # line it prints when everything runs — the silence that cost two teeth in the
    # 2026-08-13 sweep. Counting the module's own declarations catches exactly that.
    declared = [k for k in globals() if k.startswith("test_")]
    assert len(checks) == len(declared), (
        f"{len(declared)} teeth are declared in this file and {len(checks)} are listed to "
        f"run — an unlisted tooth is a tooth that did not run: "
        f"{sorted(set(declared) - {c.__name__ for c in checks})}")
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    # Dogfood: the tester's first real act is to validate the actual base proofs.
    print("  --- dogfood: the tester validates the real base proofs ---")
    t = TesterDevice()
    for name in ("test_core_values.py", "test_composition.py"):
        v = t.run_proof(_REPO_ROOT / "cairn" / "tools" / "base" / "proofs" / name, sink="none")
        print(f"    VALIDATION  {v['verdict']:5}  {v['claim']}")
    print("green — TesterDevice runs proofs and emits VALIDATIONS; the red case bites")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
