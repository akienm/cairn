#!/usr/bin/env python3
"""Proof that clearance's code and proofs reach no other device (RULE 1).

The build inspector's encapsulation_holds filed, 2026-11-11,
cairn/devices/codemother/machines/clearance/proofs/test_clearance_asks_the_real_host.py:66
importing cairn.devices.system_rackmount.rackmount: it put the real host device behind
clear(resources=...) in-process. system_rackmount is racked nowhere and publishes no tool, so
it has no public interface to reach; no live caller passes resources= to clear(); and outline
6.6.3.2 puts the host reading in Recovery, reached by subscription. Ticket b546c6efabfb retired
that proof. The gate side of the resource rung stays proven by test_clearance.py against an
ask-door stand-in; the device side stays proven at system_rackmount's own proofs.

Teeth:
  (1) no RULE 1 breach has a file under clearance — the sieve's own breach list, read whole;
  (2) the retired proof and its validation stand nowhere.

    bin/cairn test cairn/devices/codemother/machines/clearance/proofs/test_clearance_proofs_reach_no_other_device.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"b546c6efabfb": {"1": "test_no_breach_has_a_file_under_clearance",
                           "2": "test_the_real_host_proof_stands_nowhere"}}

CLEARANCE = "cairn/devices/codemother/machines/clearance"
RETIRED = (f"{CLEARANCE}/proofs/test_clearance_asks_the_real_host.py",
           f"{CLEARANCE}/validations/test_clearance_asks_the_real_host.json")

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_breach_has_a_file_under_clearance() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        breaches = inspector.encapsulation_breaches(".")
    finally:
        os.chdir(here)
    mine = [b for b in breaches if str(b.get("file", "")).startswith(CLEARANCE + "/")]
    # Not blind: the sieve read the tree and found breaches elsewhere (54 on 2026-11-11). A
    # sieve that returned [] for everything would pass the first half alone.
    check("test_no_breach_has_a_file_under_clearance", not mine and bool(breaches),
          f"{len(breaches)} breach(es) in all; under clearance: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_the_real_host_proof_stands_nowhere() -> None:
    standing = [p for p in RETIRED if (_REPO / p).exists()]
    check("test_the_real_host_proof_stands_nowhere", not standing, "; ".join(standing))


TEETH = (test_no_breach_has_a_file_under_clearance, test_the_real_host_proof_stands_nowhere)


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
