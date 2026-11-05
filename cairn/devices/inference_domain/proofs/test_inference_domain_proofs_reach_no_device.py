#!/usr/bin/env python3
"""Proof that inference_domain's bus proofs reach no device (ticket 12e6ecd87700).

Measured 2026-11-05: encapsulation_breaches listed four inference_domain rows —
test_bus_infer.py:46-47 and test_resolve_verb.py:37-38 importing the cairn device's bus
machine (bus.bus and bus.shim) to stand up a private scratch bus with a roster, a BusShim and
a caller shim. RULE 1: a component reaches another only through its public interface, and a
device's is the bus, reached through bus_client. The perform mark (d0c8c4b4283e) lets a proof
hand the device's own shim a testing-marked request and read the reply off the bus, so neither
proof needs the bus device's code.

Teeth, one per falsifier clause (PROVES below):
  (1) encapsulation_breaches lists no row whose source is cairn/devices/inference_domain;
  (2) neither bus proof names a cairn.devices.cairn module, each reaches the bus through
      bus_client, and each, run as its own process, is green.

    PYTHONPATH=. python3 cairn/devices/inference_domain/proofs/test_inference_domain_proofs_reach_no_device.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_SOURCE = "cairn/devices/inference_domain"
_PROOFS = (_REPO / "cairn/devices/inference_domain/proofs/test_resolve_verb.py",
           _REPO / "cairn/devices/inference_domain/proofs/test_bus_infer.py")

PROVES = {"12e6ecd87700": {
    "1": "test_no_inference_domain_row",
    "2": "test_the_bus_proofs_ride_bus_client",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_inference_domain_row() -> None:
    from cairn.machines.build_inspector import inspector
    rows = [r for r in inspector.encapsulation_breaches(str(_REPO)) if r.get("source") == _SOURCE]
    check("test_no_inference_domain_row", not rows,
          "; ".join(f"{r['file']}:{r.get('line')} -> {r.get('module')}" for r in rows))


def test_the_bus_proofs_ride_bus_client() -> None:
    lacks = []
    for proof in _PROOFS:
        text = proof.read_text(encoding="utf-8")
        if "cairn.devices.cairn" in text:
            lacks.append(f"{proof.name} still names a cairn.devices.cairn module")
        if "bus_client" not in text:
            lacks.append(f"{proof.name} does not reach the bus through bus_client")
    if not lacks:
        env = {**os.environ, "PYTHONPATH": str(_REPO)}
        for proof in _PROOFS:
            run = subprocess.run([sys.executable, str(proof)], cwd=str(_REPO), env=env,
                                 capture_output=True, text=True, timeout=600)
            if run.returncode != 0:
                tail = (run.stdout + run.stderr).strip().splitlines()[-6:]
                lacks.append(f"{proof.name} exited {run.returncode}: {' | '.join(tail)}")
    check("test_the_bus_proofs_ride_bus_client", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    for tooth in (test_no_inference_domain_row, test_the_bus_proofs_ride_bus_client):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
