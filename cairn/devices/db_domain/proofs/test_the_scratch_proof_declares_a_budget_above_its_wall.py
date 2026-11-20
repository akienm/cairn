"""Proof for ticket cf32e6f141e0 — test_scratch_cannot_outlive_its_process declares its own time limit.

Measured 2026-11-19 on Windows: the default 120 s budget timed it out; at 540 s it finished in 129 s wall.
The budget is the proof's own byte (ticket 8383a32d20c5), so the fix is one declaration.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"cf32e6f141e0": {
    "1": "test_the_scratch_proof_declares_300",
    "2": "test_a_reseal_budget_of_120_runs_it_at_300",
}}

_SUBJECT = _REPO_ROOT / "cairn" / "devices" / "db_domain" / "proofs" / "test_scratch_cannot_outlive_its_process.py"


def test_the_scratch_proof_declares_300():
    from cairn.devices.tester.device import declared_timeout
    assert declared_timeout(_SUBJECT) == 300, declared_timeout(_SUBJECT)


def test_a_reseal_budget_of_120_runs_it_at_300():
    from cairn.devices.tester.device import TesterDevice, declared_timeout
    declared = declared_timeout(_SUBJECT)
    assert declared, "the scratch proof declares no budget"
    root = scratch_dir("cairn-cf32-") / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    fixture = root / "proofs" / "test_fixture.py"
    fixture.write_text(f'PROOF_TIMEOUT_S = {declared}\nPROVES = {{"aaaaaaaaaaaa": {{"1": "test_fixture_tooth"}}}}\n'
                       'print("ok   test_fixture_tooth")\n')
    rec = TesterDevice().run_proof(fixture, sink="none", caller="proof-fixture", timeout=120, isolation="none")
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert rec["evidence"]["conditions"]["timeout"] == 300, rec["evidence"]["conditions"]


def main() -> int:
    fails = 0
    for name in PROVES["cf32e6f141e0"].values():
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
