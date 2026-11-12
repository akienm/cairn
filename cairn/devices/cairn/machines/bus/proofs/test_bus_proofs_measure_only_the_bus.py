#!/usr/bin/env python3
"""Proof that the bus machine's proofs reach no aider_shim module (ticket 30b03739df9c, RULE 1).

Until this ticket the inference-rides-the-bus proof imported aider_shim's interceptor and
fence to drive aider's no-bus surface; that tooth now berths with aider_shim (51fa6654ed3e).

Teeth:
  (1) no RULE 1 breach from a file under cairn/devices/cairn/machines/bus lands on cairn/devices/aider_shim;
  (2) the edited files name none of the forbidden modules.

    bin/cairn test cairn/devices/cairn/machines/bus/proofs/test_bus_proofs_measure_only_the_bus.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"30b03739df9c": {"1": "test_no_bus_machine_file_reaches_aider_shim", "2": "test_the_inference_proof_names_no_aider_shim_module"}}

COMP = "cairn/devices/cairn/machines/bus"
TARGETS = ('cairn/devices/aider_shim',)
FORBID = {'cairn/devices/cairn/machines/bus/proofs/test_inference_rides_the_bus.py': ['cairn.devices.aider_shim']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_bus_machine_file_reaches_aider_shim() -> None:
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
    check("test_no_bus_machine_file_reaches_aider_shim", not mine and bool(breaches),
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_the_inference_proof_names_no_aider_shim_module() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_the_inference_proof_names_no_aider_shim_module", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


TEETH = (test_no_bus_machine_file_reaches_aider_shim, test_the_inference_proof_names_no_aider_shim_module)


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
