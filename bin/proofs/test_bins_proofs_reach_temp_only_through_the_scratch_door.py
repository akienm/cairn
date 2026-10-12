"""Proof for ticket 7afb00d72c6c — bin's proofs reach the system temp directory only through the scratch
door, and bin holds its own proofs to that by calling the scratch tool's published scan.

Measured 2026-10-12: cairn.tools.scratch.scratch.bare_temp_reach over bin named exactly
bin/proofs/test_proof_gate.py:217 — the one standing offender the corpus tooth in
cairn/tools/scratch/proofs/test_scratch.py reads at this address. Under RULE 1 the scan is the
scratch tool's public interface and this component proves its own proofs clean with it.

The scan is reached at call time, so a missing scan reds the tooth rather than crashing the
import. This file names no temp-directory call of its own, so the scan has nothing here to see.

    bin/cairn test bin/proofs/test_bins_proofs_reach_temp_only_through_the_scratch_door.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"7afb00d72c6c": {"all": "test_no_proof_in_bin_reaches_temp_bare"}}


def test_no_proof_in_bin_reaches_temp_bare():
    from cairn.tools.scratch.scratch import bare_temp_reach
    named = bare_temp_reach(REPO / "bin")
    assert named == [], f"{len(named)} bare reach(es) into the system temp directory: {named}"
    print("bare_temp_reach over bin names nothing")


def main() -> int:
    try:
        test_no_proof_in_bin_reaches_temp_bare()
        print("  PASS  test_no_proof_in_bin_reaches_temp_bare")
        return 0
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        print("  FAIL  test_no_proof_in_bin_reaches_temp_bare")
        print(f"        {type(exc).__name__}: {str(exc)[:300]}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
