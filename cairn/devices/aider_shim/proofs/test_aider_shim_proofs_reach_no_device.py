#!/usr/bin/env python3
"""Proof that aider_shim's proofs reach no device (ticket ea19fc079c0b).

Measured 2026-11-05: encapsulation_breaches listed two aider_shim rows —
test_no_direct_reach.py:179 and :194 importing cairn.devices.inference_domain.device to
construct the provider and call its ``get`` verb in-process. aider_shim's runtime code was
already clean (50ad391f4e95); its proof was not. RULE 1: a component reaches another only
through its public interface, and a device's is the bus, reached through bus_client —
which already asks this exact view (bus_client.models_stack).

Teeth, one per falsifier clause (PROVES below):
  (1) encapsulation_breaches lists no row whose source is cairn/devices/aider_shim;
  (2) test_no_direct_reach.py imports nothing from cairn.devices.inference_domain (ast — its
      FORBIDDEN_MODULE string is the instrument, not a reach), carries
      test_inference_domain_answers_the_models_view_over_the_bus, its composite declared
      tooth calls it, and the proof, run as its own process, is green.

    PYTHONPATH=. python3 cairn/devices/aider_shim/proofs/test_aider_shim_proofs_reach_no_device.py
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_SOURCE = "cairn/devices/aider_shim"
_PROOF = _REPO / "cairn/devices/aider_shim/proofs/test_no_direct_reach.py"
_FORBIDDEN = "cairn.devices.inference_domain"
_NEW_TOOTH = "test_inference_domain_answers_the_models_view_over_the_bus"
_COMPOSITE = "test_aider_shim_reaches_inference_domain_only_through_a_door"

PROVES = {"ea19fc079c0b": {
    "1": "test_no_aider_shim_row",
    "2": "test_the_door_proof_asks_over_the_bus",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_aider_shim_row() -> None:
    from cairn.machines.build_inspector import inspector
    rows = [r for r in inspector.encapsulation_breaches(str(_REPO)) if r.get("source") == _SOURCE]
    check("test_no_aider_shim_row", not rows,
          "; ".join(f"{r['file']}:{r.get('line')} -> {r.get('module')}" for r in rows))


def _calls(fn: ast.FunctionDef) -> set[str]:
    return {n.func.id for n in ast.walk(fn)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


def test_the_door_proof_asks_over_the_bus() -> None:
    lacks = []
    tree = ast.parse(_PROOF.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods = [node.module]
        for m in mods:
            if m == _FORBIDDEN or m.startswith(_FORBIDDEN + "."):
                lacks.append(f"line {node.lineno} imports {m}")
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    if _NEW_TOOTH not in fns:
        lacks.append(f"no tooth named {_NEW_TOOTH}")
    if _COMPOSITE not in fns or _NEW_TOOTH not in _calls(fns[_COMPOSITE]):
        lacks.append(f"{_COMPOSITE} does not call {_NEW_TOOTH}")
    if not lacks:
        env = {**os.environ, "PYTHONPATH": str(_REPO)}
        run = subprocess.run([sys.executable, str(_PROOF)], cwd=str(_REPO), env=env,
                             capture_output=True, text=True, timeout=600)
        if run.returncode != 0:
            tail = (run.stdout + run.stderr).strip().splitlines()[-6:]
            lacks.append(f"{_PROOF.name} exited {run.returncode}: {' | '.join(tail)}")
    check("test_the_door_proof_asks_over_the_bus", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    for tooth in (test_no_aider_shim_row, test_the_door_proof_asks_over_the_bus):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
