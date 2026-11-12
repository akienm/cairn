#!/usr/bin/env python3
"""Proof that the librarian's proofs reach no other device (ticket a16c4d4ff4bd).

Measured 2026-11-10: encapsulation_breaches listed three rows whose source is the librarian —
test_librarian_chat.py:396 and :409 (inference_domain's domain module patched behind a
scratch BusDevice and the inference shim) and test_librarian_loop.py:55 (inference_domain's
canonicalize). RULE 1: a component's proofs measure only that component. The chat stamp tooth
now drives dual_seam over a recording bus and reads what the seam sends; the loop's livelock
tooth keeps the librarian's half (the prompt changed) and leaves the cache key to
inference_domain's own proofs.

Teeth, one per falsifier clause (PROVES below):
  (1) encapsulation_breaches lists no row whose source is cairn/devices/librarian;
  (2) neither proof names a cairn.devices.inference_domain or cairn.devices.cairn module, and
      each, run as its own process, is green.

    PYTHONPATH=. python3 cairn/devices/librarian/proofs/test_the_librarian_proofs_reach_no_device.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_SOURCE = "cairn/devices/librarian"
_PROOFS = (_REPO / "cairn/devices/librarian/proofs/test_librarian_chat.py",
           _REPO / "cairn/devices/librarian/proofs/test_librarian_loop.py")
_FORBIDDEN = ("cairn.devices.inference_domain", "cairn.devices.cairn")

PROVES = {"a16c4d4ff4bd": {
    "1": "test_no_librarian_row",
    "2": "test_the_two_proofs_name_no_other_device_and_run_green",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_librarian_row() -> None:
    from cairn.machines.build_inspector import inspector
    breaches = inspector.encapsulation_breaches(str(_REPO))
    rows = [r for r in breaches if r.get("source") == _SOURCE]
    # Not blind: the sieve read the tree and found breaches elsewhere.
    check("test_no_librarian_row", not rows and bool(breaches),
          f"{len(breaches)} breach(es) in all; "
          + "; ".join(f"{r['file']}:{r.get('line')} -> {r.get('module')}" for r in rows))


def test_the_two_proofs_name_no_other_device_and_run_green() -> None:
    lacks = []
    for proof in _PROOFS:
        text = proof.read_text(encoding="utf-8")
        for mod in _FORBIDDEN:
            if mod in text:
                lacks.append(f"{proof.name} still names {mod}")
    if not lacks:
        env = {**os.environ, "PYTHONPATH": str(_REPO)}
        for proof in _PROOFS:
            run = subprocess.run([sys.executable, str(proof)], cwd=str(_REPO), env=env,
                                 capture_output=True, text=True, timeout=600)
            if run.returncode != 0:
                tail = (run.stdout + run.stderr).strip().splitlines()[-6:]
                lacks.append(f"{proof.name} exited {run.returncode}: {' | '.join(tail)}")
    check("test_the_two_proofs_name_no_other_device_and_run_green", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    for tooth in (test_no_librarian_row, test_the_two_proofs_name_no_other_device_and_run_green):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
