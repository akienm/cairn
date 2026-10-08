"""Proof for the tester — its own proofs reach the system temp directory only through the scratch door.

The scratch tool publishes ``bare_temp_reach(root)``: every live line in ``root``'s
``proofs/test_*.py`` that takes a temp directory without going through ``scratch_dir``.
The tool names no caller (RULE 1), so each component proves its own proofs clean at its
own address. This is the tester's. Akien on open-551895c1adad: "prove it with a tooth in
this component's own proofs that calls scratch's public bare_temp_reach on its own proofs
dir; hollow = revert the edits."

The tooth reds while any tester proof reaches the temp directory bare, and it names the
lines. It also reds on an empty population: a scan over a directory that holds no proofs
names nothing, and that silence would read as clean.

    python3 cairn/devices/tester/proofs/test_the_testers_proofs_reach_temp_only_through_the_scratch_door.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROOF_TIMEOUT_S = 120

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

_TESTER = _REPO_ROOT / "cairn" / "devices" / "tester"

PROVES = {"017d8298662a": {"all": "test_the_testers_proofs_name_no_bare_temp_reach"}}


def test_the_testers_proofs_name_no_bare_temp_reach():
    from cairn.tools.scratch.scratch import bare_temp_reach

    proofs = sorted(p for p in _TESTER.rglob("proofs/test_*.py") if "__pycache__" not in p.parts)
    assert Path(__file__).resolve() in proofs, \
        f"the scan's population does not hold this proof — it is not reading the tester's proofs: {len(proofs)} file(s)"
    offenders = bare_temp_reach(_TESTER)
    assert offenders == [], (
        f"{len(offenders)} tester proof line(s) reach the system temp directory bare — "
        "take the directory from cairn.tools.scratch.scratch.scratch_dir:\n  " + "\n  ".join(offenders))


def _main() -> int:
    checks = [test_the_testers_proofs_name_no_bare_temp_reach]
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as e:  # noqa: BLE001 — a crash in a tooth is that tooth's red
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {type(e).__name__}: {e}")
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed")
        return 1
    print("green — every tester proof takes its temp directory through the scratch door")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
