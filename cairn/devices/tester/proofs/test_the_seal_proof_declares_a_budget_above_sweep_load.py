"""Proof for ticket 6c253323d4f2 — test_seal_is_never_silently_dropped declares its own time limit.

Measured 2026-11-19: 53 s wall idle on Windows, 23.4 s and 24.2 s idle on Linux, and over the
default 120 s during cc_0's 39-validation reseal sweep, which reded it (a timeout, not a hang:
every wait inside it is bounded). The budget is the proof's own byte (ticket 8383a32d20c5), so
the fix is one declaration, and these teeth read it the way the tester does.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"6c253323d4f2": {
    "1": "test_the_seal_proof_declares_300",
    "2": "test_a_reseal_budget_of_120_runs_it_at_300",
}}

_SEAL = _REPO_ROOT / "cairn" / "devices" / "tester" / "proofs" / "test_seal_is_never_silently_dropped.py"


def test_the_seal_proof_declares_300():
    from cairn.devices.tester.device import declared_timeout
    assert declared_timeout(_SEAL) == 300, declared_timeout(_SEAL)


def test_a_reseal_budget_of_120_runs_it_at_300():
    from cairn.devices.tester.device import TesterDevice, declared_timeout
    declared = declared_timeout(_SEAL)
    assert declared, "the seal proof declares no budget"
    root = scratch_dir("cairn-6c25-") / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    fixture = root / "proofs" / "test_fixture.py"
    fixture.write_text(f'PROOF_TIMEOUT_S = {declared}\nPROVES = {{"aaaaaaaaaaaa": {{"1": "t"}}}}\nprint("ok   t")\n')
    rec = TesterDevice().run_proof(fixture, sink="none", caller="proof-fixture", timeout=120, isolation="none")
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert rec["evidence"]["conditions"]["timeout"] == 300, rec["evidence"]["conditions"]


def main() -> int:
    fails = 0
    for name in PROVES["6c253323d4f2"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
