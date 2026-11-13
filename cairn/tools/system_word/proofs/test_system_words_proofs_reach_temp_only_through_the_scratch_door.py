"""Proof for ticket 85848910db3a — system_word's proofs reach the system temp directory only through the scratch door.

Measured 2026-11-12: cairn.tools.scratch.scratch.bare_temp_reach over cairn/tools/system_word named cairn/tools/system_word/proofs/test_a_probe_stub_is_lf_on_every_box.py:52.
Under RULE 1 the scan is the scratch tool's public interface; this component proves its own proofs clean with it.

The scan is reached at call time, so a missing scan reds the tooth rather than crashing the import. This file
names no temp-directory call of its own, so the scan has nothing here to see.

    bin/cairn test cairn/tools/system_word/proofs/test_system_words_proofs_reach_temp_only_through_the_scratch_door.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"85848910db3a": {"1": "test_no_proof_in_system_word_reaches_temp_bare"}}


def test_no_proof_in_system_word_reaches_temp_bare():
    from cairn.tools.scratch.scratch import bare_temp_reach
    named = bare_temp_reach(REPO / "cairn/tools/system_word")
    assert named == [], f"{len(named)} bare reach(es) into the system temp directory: {named}"
    print("bare_temp_reach over cairn/tools/system_word names nothing")


def main() -> int:
    try:
        test_no_proof_in_system_word_reaches_temp_bare()
        print("  PASS  test_no_proof_in_system_word_reaches_temp_bare")
        return 0
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        print("  FAIL  test_no_proof_in_system_word_reaches_temp_bare")
        print(f"        {type(exc).__name__}: {str(exc)[:300]}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
