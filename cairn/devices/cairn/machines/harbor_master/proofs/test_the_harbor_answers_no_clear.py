#!/usr/bin/env python3
"""Proof that the harbor's bus face answers no `clear`, and still answers `crossing`.

Akien 2026-11-10 (outline 9.4.1.5, Q#80): the harbor's verbs are status queries (show, get)
and crossing; it answers no gate and moves no ticket, and `clear` leaves. Ticket
0be964512fb0 moved the clearance gate to CodeMother (cairn/devices/codemother/machines/
clearance); this tooth stands at the harbor's own address because no other component may
import the harbor (RULE 1).

    bin/cairn test cairn/devices/cairn/machines/harbor_master/proofs/test_the_harbor_answers_no_clear.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"0be964512fb0": {"3": "test_the_harbor_answers_no_clear"}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_harbor_answers_no_clear() -> None:
    from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice
    verbs = HarborMasterDevice().declared_verbs()
    check("test_the_harbor_answers_no_clear", "clear" not in verbs and "crossing" in verbs,
          f"verbs: {sorted(verbs)}")


def main() -> int:
    try:
        test_the_harbor_answers_no_clear()
    except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
        check("test_the_harbor_answers_no_clear", False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
