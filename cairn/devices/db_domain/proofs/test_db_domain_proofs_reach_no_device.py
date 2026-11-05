#!/usr/bin/env python3
"""Proof that db_domain's proofs reach no device (ticket 7bc784d5a7de).

Measured 2026-11-05, after sibling ad7caca4d54c PROVED: encapsulation_breaches listed one
db_domain row — test_scratch_cannot_outlive_its_process.py:98 importing the cairn device's
bus module for BusDevice.scratch. The killed-minter tooth used that bus only to get a scratch
table with a registered ``_delivery`` companion, and db_domain's own store makes exactly that:
store.scratch, store.create_owned_table, store.register_scratch_companion — the same three
calls the bus's _ensure composes (bus.py:392-400). RULE 1: a component reaches another only
through its public interface, and a sweep tooth about db_domain's sweep has no business in
the bus.

Teeth, one per falsifier clause (PROVES below):
  (1) encapsulation_breaches lists no row whose source is cairn/devices/db_domain;
  (2) the scratch-lifetime proof names no cairn.devices.cairn module, its _fork_minter mints
      the companion through store.register_scratch_companion, and the killed-minter tooth —
      loaded by path and run here — is green.

    PYTHONPATH=. python3 cairn/devices/db_domain/proofs/test_db_domain_proofs_reach_no_device.py
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_SOURCE = "cairn/devices/db_domain"
_LIFETIME = _REPO / "cairn/devices/db_domain/proofs/test_scratch_cannot_outlive_its_process.py"

PROVES = {"7bc784d5a7de": {
    "1": "test_no_db_domain_row",
    "2": "test_the_killed_minter_mints_through_the_store",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_db_domain_row() -> None:
    from cairn.machines.build_inspector import inspector
    rows = [r for r in inspector.encapsulation_breaches(str(_REPO)) if r.get("source") == _SOURCE]
    check("test_no_db_domain_row", not rows,
          "; ".join(f"{r['file']}:{r.get('line')} -> {r.get('module')}" for r in rows))


def test_the_killed_minter_mints_through_the_store() -> None:
    text = _LIFETIME.read_text(encoding="utf-8")
    minter = next((n for n in ast.parse(text).body
                   if isinstance(n, ast.FunctionDef) and n.name == "_fork_minter"), None)
    segment = ast.get_source_segment(text, minter) if minter else ""
    lacks = []
    if "cairn.devices.cairn" in text:
        lacks.append("the file still names a cairn.devices.cairn module")
    if "register_scratch_companion" not in (segment or ""):
        lacks.append("_fork_minter does not mint its companion through store.register_scratch_companion")
    if not lacks:
        spec = importlib.util.spec_from_file_location("_lifetime_under_7bc7", _LIFETIME)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            mod.test_a_killed_minter_is_swept_with_its_delivery_companion()
        except AssertionError as exc:
            lacks.append(f"the killed-minter tooth is red: {exc}")
    check("test_the_killed_minter_mints_through_the_store", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    for tooth in (test_no_db_domain_row, test_the_killed_minter_mints_through_the_store):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
