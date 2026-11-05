#!/usr/bin/env python3
"""Proof that every class with code in codemother reaches DiagnosticBase, and loses nothing by it.

Akien 2026-10-27 (recorded on 339a45cee6a1): "everybody must inherit it. that's why it's a mixin".
Measured 2026-11-05, when codemother's build gate refused 337b78c2667d's PROVED crossing:
inspector.every_class_reaches_the_diagnostic_mixin over cairn/devices/codemother named five
classes, ChallengeResult (challenge.py:25), ConstraintProof (constraint_proof.py:24), QueryResult
(query.py:19), PatternType (types.py:31) and UnificationResult (unify.py:18). Ticket 93265f9215bd
converts all five.

Teeth, each importing the code under test at call time:
  (1) the sieve returns no findings for component codemother;
  (2) the five classes are DiagnosticBase subclasses;
  (3) each of the five modules imports in a fresh interpreter (an inconsistent MRO is an
      import-time TypeError);
  (4) PatternType and UnificationResult stay frozen and equal by fields, with equal hashes.

    bin/cairn test cairn/devices/codemother/proofs/test_every_codemother_class_reaches_the_diagnostic_mixin.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"93265f9215bd": {"all": "test_codemother_holds_every_clause_of_the_falsifier"}}

MODULES = ("challenge", "constraint_proof", "query", "types", "unify")
CLASSES = (("challenge", "ChallengeResult"), ("constraint_proof", "ConstraintProof"),
           ("query", "QueryResult"), ("types", "PatternType"), ("unify", "UnificationResult"))

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_sieve_reads_codemother_green() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        found = inspector.every_class_reaches_the_diagnostic_mixin(
            {"component": "codemother", "dir": "cairn/devices/codemother"},
            Path("cairn/devices/codemother"))
    finally:
        os.chdir(here)
    check("test_the_sieve_reads_codemother_green", found == [],
          f"{len(found)} finding(s): " + "; ".join(str(f.get("about")) for f in found))


def test_the_five_reach_the_mixin() -> None:
    import importlib
    from cairn.tools.base.diagnostic import DiagnosticBase
    bad = [f"{m}.{c}" for m, c in CLASSES
           if not issubclass(getattr(importlib.import_module(f"cairn.devices.codemother.{m}"), c),
                             DiagnosticBase)]
    check("test_the_five_reach_the_mixin", not bad, "not a DiagnosticBase: " + ", ".join(bad))


def test_the_modules_import_fresh() -> None:
    bad = []
    for m in MODULES:
        r = subprocess.run([sys.executable, "-c", f"import cairn.devices.codemother.{m}"],
                           cwd=_REPO, capture_output=True, text=True)
        if r.returncode != 0:
            bad.append(f"{m}: " + (r.stderr.strip().splitlines() or [""])[-1])
    check("test_the_modules_import_fresh", not bad, "; ".join(bad))


def test_the_frozen_stay_frozen_and_equal() -> None:
    import dataclasses
    from cairn.devices.codemother.types import PatternType, TypePolarity
    from cairn.devices.codemother.unify import UnificationResult
    bad = []
    a = PatternType(name="x", why="y", polarity=TypePolarity.POSITIVE)
    b = PatternType(name="x", why="y", polarity=TypePolarity.POSITIVE)
    if not (a == b and hash(a) == hash(b)):
        bad.append("equal PatternTypes differ in == or hash")
    if a == PatternType(name="z", why="y", polarity=TypePolarity.POSITIVE):
        bad.append("PatternTypes with different names compare equal")
    u = UnificationResult(pattern=a, matched=True, score=1.0, evidence=("e",))
    v = UnificationResult(pattern=b, matched=True, score=1.0, evidence=("e",))
    if not (u == v and hash(u) == hash(v)):
        bad.append("equal UnificationResults differ in == or hash")
    for obj, field in ((a, "name"), (u, "score")):
        try:
            setattr(obj, field, "z")
            bad.append(f"{type(obj).__name__}.{field} assignment did not raise")
        except dataclasses.FrozenInstanceError:
            pass
    check("test_the_frozen_stay_frozen_and_equal", not bad, "; ".join(bad))


TEETH = (test_the_sieve_reads_codemother_green,
         test_the_five_reach_the_mixin,
         test_the_modules_import_fresh,
         test_the_frozen_stay_frozen_and_equal)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    check("test_codemother_holds_every_clause_of_the_falsifier", not FAILURES,
          f"{len(FAILURES)} tooth/teeth red")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
