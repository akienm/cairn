#!/usr/bin/env python3
"""Proof that the tester's proofs reach trouble only through its published store tool (ticket 4a05db0f2280, RULE 1).

Until this ticket the reseal-door proof stood a real TroubleDevice behind the door's raiser.
The fold is trouble's to prove (test_trouble.py); the tester proves the door signs as the recipient.

Teeth:
  (1) no RULE 1 breach from a file under cairn/devices/tester lands on cairn/devices/trouble;
  (2) the edited files name none of the forbidden modules.

    bin/cairn test cairn/devices/tester/proofs/test_tester_proofs_measure_only_tester.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"4a05db0f2280": {"1": "test_no_tester_proof_reaches_trouble_past_its_store_tool", "2": "test_the_reseal_door_proof_names_no_trouble_module"}}

COMP = "cairn/devices/tester"
TARGETS = ('cairn/devices/trouble',)
FORBID = {'cairn/devices/tester/proofs/test_reseal_door.py': ['cairn.devices.trouble.trouble', 'cairn.devices.trouble.shim', 'cairn.devices.trouble.device']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_tester_proof_reaches_trouble_past_its_store_tool() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        breaches = inspector.encapsulation_breaches(".")
    finally:
        os.chdir(here)
    mine = [b for b in breaches if str(b.get("file", "")).startswith(COMP + "/")
            and str(b.get("target", "")).startswith(TARGETS)]
    # Not blind: the sieve read the tree and found breaches elsewhere. A sieve that returned
    # [] for everything would pass the first half alone.
    check("test_no_tester_proof_reaches_trouble_past_its_store_tool", not mine and bool(breaches),
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_the_reseal_door_proof_names_no_trouble_module() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_the_reseal_door_proof_names_no_trouble_module", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


TEETH = (test_no_tester_proof_reaches_trouble_past_its_store_tool, test_the_reseal_door_proof_names_no_trouble_module)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
