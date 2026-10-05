"""The promotion judge reads a writes_to under CairnCommons as in bounds (ticket fb85042b8342).

A concept-piece's only output is prose in CairnCommons/intentions-not-beside-code, and the
judge redded every writes_to outside the cairn repo, so no concept-piece's chart could berth
and none could enter BUILDME. The rule's why (68f1fc073512: a write this system does not gate
and git cannot see) is false for the commons, which is git-tracked and whose records pass the
artifact door; Akien answered open-90d38cb2bdca "a agreed" (commons files read as code are
proved like code). Anything outside the two roots (/etc/passwd, instance-space ~/.cairn) still
reds, and the red names both roots.

Every tooth imports the inspector INSIDE its body, so a reverted inspector.py reds teeth
instead of breaking this file's import.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"fb85042b8342": {
    "1": "test_a_commons_address_draws_no_finding",
    "2": "test_an_address_outside_both_roots_still_reds",
    "3": "test_the_red_names_both_roots",
}}


def _frags(addr: str) -> list[dict]:
    from cairn.machines.build_inspector.inspector import _writes_to_frags
    return _writes_to_frags(0, {"what": "p", "writes_to": [addr]})


def test_a_commons_address_draws_no_finding():
    from cairn.machines.build_inspector.inspector import _REPO_ROOT as root
    piece = root.parent / "CairnCommons" / "intentions-not-beside-code" / "I-x.md"
    got = _frags(str(piece))
    assert got == [], got


def test_an_address_outside_both_roots_still_reds():
    for addr in ("/etc/passwd", str(Path.home() / ".cairn" / "x.json")):
        got = _frags(addr)
        assert len(got) == 1, (addr, got)
        assert got[0]["judge"] == "decompose_composes_holdings", got
        assert "outside" in got[0]["finding"], got


def test_the_red_names_both_roots():
    finding = _frags("/etc/passwd")[0]["finding"]
    assert "cairn repo" in finding and "CairnCommons" in finding, finding


def main() -> int:
    fails = 0
    for name in PROVES["fb85042b8342"].values():
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
