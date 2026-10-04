"""Proof: a file the tester sent to the operator is COVERED at PROVED (ticket 0069ce6b8681).

Akien's answer to open-ed0a56ce6357: a green the measurement cannot vouch for COMPLETES and
NOTIFIES him — "because the repo has the whole history anyway, we can back out a part if
needed". The tester will seal such a file's hollow reading as ``{"notified": <notice id>}``
(sibling child under df05d93da4c0); this rung must read that as covered, or every unvouched
green is refused at PROVED as ``hollow_unreadable`` — which is what any non-list reading
reds as today.

Two teeth:
  1. a notified file beside a covered file yields NO lack. A build that ignored the marker
     reds it as unreadable and dies here.
  2. the hard refusals stand: an empty list is still ``hollow_file``; the unreadable dict, an
     empty-string marker and a null marker are still ``hollow_unreadable``; an empty reading
     is still ``hollow_nothing_measured``. A build that waved every dict through (or any
     ``notified`` key, however blank) dies here.

The fake ``seal_reader`` hands hollow_lacks a reading directly, so this measures the rung
and nothing else (RULE 1). ``hollow_lacks`` is resolved at call time so reverting
clearance.py reds a tooth instead of breaking the import.
    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_a_notified_file_is_covered.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "0069ce6b8681": {
        "1": "test_a_notified_file_is_covered",
        "2": "test_the_hard_refusals_stand",
    },
}

_TID = "0069ce6b8681"
_PROOF = "cairn/devices/cairn/machines/harbor_master/proofs/test_clearance.py"


def _lacks(reading) -> list[dict]:
    clearance = importlib.import_module("cairn.devices.cairn.machines.harbor_master.clearance")

    def seal_reader(path, artifact=False):
        return {"evidence": {"hollow": {_TID: reading}}}

    ticket = {"id": _TID, "node_class": "code-seam"}
    return clearance.hollow_lacks(ticket, [_PROOF], repo_root=_REPO_ROOT,
                                  seal_reader=seal_reader)


def _kinds(lacks) -> list[str]:
    return sorted(l["kind"] for l in lacks)


def test_a_notified_file_is_covered():
    reading = {"a.py": ["test_x"], "b.py": {"notified": "notice-0123abcd"}}
    got = _lacks(reading)
    assert got == [], f"a notified file beside a covered one must yield [], got {_kinds(got)}"


def test_the_hard_refusals_stand():
    cases = [
        ({"a.py": []}, ["hollow_file"]),
        ({"a.py": {"unreadable": ["p.py"]}}, ["hollow_unreadable"]),
        ({"a.py": {"notified": ""}}, ["hollow_unreadable"]),
        ({"a.py": {"notified": "   "}}, ["hollow_unreadable"]),
        ({"a.py": {"notified": None}}, ["hollow_unreadable"]),
        ({}, ["hollow_nothing_measured"]),
        ({"a.py": [], "b.py": {"notified": "notice-1"}}, ["hollow_file"]),
    ]
    for reading, want in cases:
        got = _kinds(_lacks(reading))
        assert got == want, f"{reading!r}: want {want}, got {got}"


def main() -> int:
    failed = 0
    for name in PROVES[_TID].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("GREEN" if not failed else f"RED ({failed} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
