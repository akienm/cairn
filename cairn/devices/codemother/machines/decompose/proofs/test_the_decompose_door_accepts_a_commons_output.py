"""The decompose door reads a writes_to under CairnCommons as in bounds (ticket 9bd674040f48).

A concept-piece's only output is prose in CairnCommons/intentions-not-beside-code, and the
door refused every writes_to outside the cairn repo, so no concept-piece's chart could berth
and none could enter BUILDME (measured 2026-10-04 at df05d93da4c0's chart). The rule's why
(68f1fc073512: a write this system does not gate and git cannot see) is false for the commons,
which is git-tracked and whose records pass the artifact door; Akien answered
open-90d38cb2bdca "a agreed". Anything outside the two roots (/etc/passwd, instance-space
~/.cairn) still lacks, and the lack names both roots. The promotion judge the door composes
carries the same change at its own address (sibling fb85042b8342).

Every tooth imports the door INSIDE its body, so a reverted decompose.py reds teeth instead
of breaking this file's import.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"9bd674040f48": {
    "1": "test_a_commons_address_lacks_nothing",
    "2": "test_an_address_outside_both_roots_still_lacks",
    "3": "test_the_lack_names_both_roots",
}}


def _lacks(addr: str) -> list[str]:
    from cairn.devices.codemother.machines.decompose.decompose import writes_to_lacks
    return writes_to_lacks([{"what": "p", "writes_to": [addr]}])


def test_a_commons_address_lacks_nothing():
    from cairn.tools.chain.grammar import CAIRN_ROOT
    piece = os.path.join(os.path.dirname(CAIRN_ROOT), "CairnCommons",
                         "intentions-not-beside-code", "I-x.md")
    got = _lacks(piece)
    assert got == [], got


def test_an_address_outside_both_roots_still_lacks():
    for addr in ("/etc/passwd", str(Path.home() / ".cairn" / "x.json")):
        got = _lacks(addr)
        assert len(got) == 1, (addr, got)
        assert "outside" in got[0], got


def test_the_lack_names_both_roots():
    lack = _lacks("/etc/passwd")[0]
    assert "cairn repo" in lack and "CairnCommons" in lack, lack


def main() -> int:
    fails = 0
    for name in PROVES["9bd674040f48"].values():
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
