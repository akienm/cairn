"""Proof for ticket d89bad1d9d09 — validation_store's proofs reach the system temp directory only through the scratch door.

Measured 2026-11-12: cairn.tools.scratch.scratch.bare_temp_reach over cairn/tools/validation_store named test_source_files_are_lf_on_every_box.py:52 and test_the_hook_source_checks_out_lf.py:64.
Under RULE 1 the scan is the scratch tool's public interface; this component proves its own proofs clean with it.

The scan is reached at call time, so a missing scan reds the tooth rather than crashing the import. This file
names no temp-directory call of its own, so the scan has nothing here to see.

    bin/cairn test cairn/tools/validation_store/proofs/test_validation_stores_proofs_reach_temp_only_through_the_scratch_door.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"d89bad1d9d09": {"1": "test_no_proof_in_validation_store_reaches_temp_bare"}}


def test_no_proof_in_validation_store_reaches_temp_bare():
    from cairn.tools.scratch.scratch import bare_temp_reach
    named = bare_temp_reach(REPO / "cairn/tools/validation_store")
    assert named == [], f"{len(named)} bare reach(es) into the system temp directory: {named}"
    print("bare_temp_reach over cairn/tools/validation_store names nothing")


def main() -> int:
    try:
        test_no_proof_in_validation_store_reaches_temp_bare()
        print("  PASS  test_no_proof_in_validation_store_reaches_temp_bare")
        return 0
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        print("  FAIL  test_no_proof_in_validation_store_reaches_temp_bare")
        print(f"        {type(exc).__name__}: {str(exc)[:300]}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
