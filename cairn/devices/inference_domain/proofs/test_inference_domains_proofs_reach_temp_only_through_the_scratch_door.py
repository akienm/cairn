"""Proof for ticket c7fbc7f63fd1 — inference_domain's proofs reach the system temp directory only through the
scratch door, and inference_domain holds its own proofs to that by calling the scratch tool's published scan.

Measured 2026-10-30: cairn.tools.scratch.scratch.bare_temp_reach over cairn/devices/inference_domain named exactly
cairn/devices/inference_domain/proofs/test_a_request_naming_no_model_gets_its_kind_default.py:106 — the standing offenders the corpus tooth in
cairn/tools/scratch/proofs/test_scratch.py reads at this address. Under RULE 1 the scan is the
scratch tool's public interface and this component proves its own proofs clean with it.

The scan is reached at call time, so a missing scan reds the tooth rather than crashing the
import. This file names no temp-directory call of its own, so the scan has nothing here to see.

    bin/cairn test cairn/devices/inference_domain/proofs/test_inference_domains_proofs_reach_temp_only_through_the_scratch_door.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"c7fbc7f63fd1": {"all": "test_no_proof_in_inference_domain_reaches_temp_bare"}}


def test_no_proof_in_inference_domain_reaches_temp_bare():
    from cairn.tools.scratch.scratch import bare_temp_reach
    named = bare_temp_reach(REPO / "cairn/devices/inference_domain")
    assert named == [], f"{len(named)} bare reach(es) into the system temp directory: {named}"
    print("bare_temp_reach over cairn/devices/inference_domain names nothing")


def main() -> int:
    try:
        test_no_proof_in_inference_domain_reaches_temp_bare()
        print("  PASS  test_no_proof_in_inference_domain_reaches_temp_bare")
        return 0
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        print("  FAIL  test_no_proof_in_inference_domain_reaches_temp_bare")
        print(f"        {type(exc).__name__}: {str(exc)[:300]}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
