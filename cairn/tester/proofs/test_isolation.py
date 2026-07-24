"""Proof for the tester's owned network — the measured seal (cairn/tester/isolation.py).

The stone's claim: a run the tester supervises can be stripped of its route to a
constrained resource, and the seal is MEASURED from inside, never assumed. Teeth a
hollow build could not pass:

  - THE HOLLOW-SEAL KILLER (deterministic). An isolation that CLAIMS to seal
    (``seals_network = True``) but whose ``wrap`` does not actually remove the route
    must be caught: the measurement returns BREACHED, not SEALED. A sandbox that says
    "sealed" while handing out live sockets is the exact defect the tester exists to
    kill (Law 8). We prove the four seal verdicts by feeding the probe scripted
    outcomes — no network needed, so the tooth bites everywhere.
  - THE LIVE PHYSICS (measured here, honest when it can't be). On a host that can build
    the namespace, ``NetnsIsolation`` really does turn an off-host route into
    "no route" — asserted live. On a host that cannot, the verdict is INDETERMINATE and
    we say so loudly (CP1), rather than fake a pass; only an actual BREACH on a
    seal-capable host reds.
  - NO SCHEMA DRIFT. Folding the seal into a VALIDATION keeps the record at exactly the
    ratified eight fields — the seal rides inside ``method`` + ``evidence``.

Runnable bare:
    python3 cairn/tester/proofs/test_isolation.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tester.device import GREEN, VALIDATION_FIELDS, TesterDevice
from cairn.tester.isolation import (
    BREACHED,
    INDETERMINATE,
    OPEN,
    SEALED,
    Isolation,
    NetnsIsolation,
    NoIsolation,
    Seal,
    get_isolation,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_GREEN_FIXTURE = _FIXTURES / "green_proof.py"


class _Scripted(Isolation):
    """A seal-claiming isolation whose probe outcomes we dictate — lets us prove the
    verdict logic (including the hollow-seal case) without touching the network."""

    name = "scripted"
    seals_network = True

    def __init__(self, control: str, inside: str) -> None:
        self._control = control
        self._inside = inside

    def wrap(self, argv, cwd):
        return ["WRAPPED", *argv]

    def _run_probe(self, argv, cwd):
        # Return the "inside" outcome for a wrapped probe, the baseline otherwise.
        return self._inside if argv and argv[0] == "WRAPPED" else self._control


def test_no_isolation_is_honestly_open():
    iso = NoIsolation()
    assert iso.wrap(["echo", "hi"], ".") == ["echo", "hi"], "no isolation must not alter the argv"
    seal = iso.check_seal(".")
    assert seal.verdict == OPEN
    assert seal.sealed is False
    assert seal.trustworthy is True, "a deliberately-named OPEN is an honest state, not a failure"


def test_the_four_seal_verdicts_are_measured_not_assumed():
    # SEALED: baseline route, none inside → the seal removed it.
    assert _Scripted("ROUTE", "NOROUTE").check_seal(".").verdict == SEALED
    # BREACHED — THE HOLLOW-SEAL KILLER: claims to seal, route still there inside.
    assert _Scripted("ROUTE", "ROUTE").check_seal(".").verdict == BREACHED
    # INDETERMINATE: no baseline route to compare against — CP1, cannot prove anything.
    assert _Scripted("NOROUTE", "NOROUTE").check_seal(".").verdict == INDETERMINATE
    # INDETERMINATE: the inside probe gave an ambiguous answer (timeout/errno) — no guess.
    assert _Scripted("ROUTE", "ERR:110").check_seal(".").verdict == INDETERMINATE


def test_only_sealed_and_open_are_trustworthy():
    assert Seal(SEALED, "").trustworthy is True
    assert Seal(OPEN, "").trustworthy is True
    assert Seal(INDETERMINATE, "").trustworthy is False
    assert Seal(BREACHED, "").trustworthy is False, "a breached seal must never earn trust"


def test_unknown_isolation_is_refused():
    try:
        get_isolation("bogus")
    except ValueError:
        return
    raise AssertionError("get_isolation must refuse an unknown isolation name")


def test_netns_really_seals_on_this_host():
    # Live physics: measured, and honest when the host cannot build the namespace.
    iso = NetnsIsolation()
    ok, why = iso.available()
    if not ok:
        print(f"  INDETERMINATE  netns unavailable here: {why} (CP1 — not faking a pass)")
        return
    seal = iso.check_seal(str(_FIXTURES))
    print(f"  LIVE SEAL  {seal.verdict}: {seal.detail}")
    assert seal.verdict != BREACHED, f"bwrap is present but the seal did not hold: {seal.detail}"
    # SEALED is the expected live result; INDETERMINATE (e.g. this box is offline) is
    # honest, not a failure of the code. Only a BREACH on a seal-capable host is a red.
    assert seal.verdict in (SEALED, INDETERMINATE)


def test_run_proof_records_the_seal_without_schema_drift():
    t = TesterDevice()
    v = t.run_proof(_GREEN_FIXTURE, isolation="none")
    assert set(v) == set(VALIDATION_FIELDS), f"seal must ride inside the 8 fields, got {sorted(v)}"
    assert v["evidence"]["seal"]["verdict"] == OPEN
    assert "unsealed" in v["method"]
    assert v["verdict"] == GREEN


def test_run_proof_under_netns_when_available():
    iso = NetnsIsolation()
    ok, _ = iso.available()
    if not ok:
        print("  skipped netns run_proof: namespace unavailable here (honest, not faked)")
        return
    v = TesterDevice().run_proof(_GREEN_FIXTURE, isolation="netns")
    assert set(v) == set(VALIDATION_FIELDS)
    seal_verdict = v["evidence"]["seal"]["verdict"]
    print(f"  run_proof netns  proof={v['verdict']}  seal={seal_verdict}")
    assert seal_verdict != BREACHED, "a green proof under a broken seal must not pass silently"
    # The proof itself passes inside the seal (a seal removes the network, not the fixture).
    assert v["verdict"] == GREEN
    if seal_verdict == SEALED:
        assert "seal=sealed" in v["method"]


def test_the_seal_does_not_depend_on_how_the_path_is_spelled():
    # REGRESSION (2026-07-24). The netns seal runs the subject under `bwrap --chdir
    # <proof.parent>`; a RELATIVE parent resolves against the namespace root (/), not the
    # host cwd, so a relative-path call silently broke the chdir — failing the proof (false
    # RED) and downgrading the seal to INDETERMINATE. run_proof now resolve()s the path, so
    # the measured seal must be identical whether the caller spells the path relative or
    # absolute (Law 4: the guarantee is physics, not a "pass an absolute path" convention).
    iso = NetnsIsolation()
    ok, _ = iso.available()
    if not ok:
        print("  skipped path-spelling regression: netns unavailable here (honest, not faked)")
        return
    t = TesterDevice()
    absolute = t.run_proof(_GREEN_FIXTURE, isolation="netns")
    rel = os.path.relpath(_GREEN_FIXTURE, os.getcwd())
    assert not os.path.isabs(rel), "the regression needs a genuinely relative spelling"
    relative = t.run_proof(rel, isolation="netns")
    print(f"  abs seal={absolute['evidence']['seal']['verdict']}  rel seal={relative['evidence']['seal']['verdict']}")
    assert relative["verdict"] == absolute["verdict"] == GREEN, "a relative path must not fail the proof"
    assert relative["evidence"]["seal"]["verdict"] == absolute["evidence"]["seal"]["verdict"], (
        "the seal verdict must not depend on how the caller spelled the path"
    )
    assert relative["evidence"]["seal"]["verdict"] == SEALED, "on a netns host both spellings must SEAL"


def _main() -> int:
    checks = [
        test_no_isolation_is_honestly_open,
        test_the_four_seal_verdicts_are_measured_not_assumed,
        test_only_sealed_and_open_are_trustworthy,
        test_unknown_isolation_is_refused,
        test_netns_really_seals_on_this_host,
        test_run_proof_records_the_seal_without_schema_drift,
        test_run_proof_under_netns_when_available,
        test_the_seal_does_not_depend_on_how_the_path_is_spelled,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the tester owns a MEASURED network seal; the hollow-seal case is caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
