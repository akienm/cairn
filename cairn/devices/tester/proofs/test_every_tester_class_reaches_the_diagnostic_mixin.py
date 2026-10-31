#!/usr/bin/env python3
"""Proof that every class with code in the tester reaches DiagnosticBase, and loses nothing by it.

Akien 2026-10-27 (recorded on 339a45cee6a1): "everybody must inherit it. that's why it's a mixin" /
"any class with code it in should be able to run a diagnostic report when we need it." Measured
2026-10-30: inspector.every_class_reaches_the_diagnostic_mixin over cairn/devices/tester named
three classes in isolation.py, Seal (:137), Isolation (:636) and NoIsolation (:717). Ticket
668c8d64b4e2 converts Seal and Isolation; NoIsolation reaches the mixin through Isolation.

Teeth, each importing the code under test at call time:
  (1) the sieve returns no findings for component tester;
  (2) Seal is a DiagnosticBase, still frozen, equal by fields with equal hashes, and keeps
      sealed and trustworthy;
  (3) Isolation and NoIsolation are DiagnosticBase subclasses; NoIsolation() constructs, its
      wrap returns the argv unchanged, and available is True;
  (4) cairn.devices.tester.isolation imports in a fresh interpreter (an inconsistent MRO is an
      import-time TypeError).

    bin/cairn test cairn/devices/tester/proofs/test_every_tester_class_reaches_the_diagnostic_mixin.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"668c8d64b4e2": {"all": "test_the_tester_holds_every_clause_of_the_falsifier"}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_sieve_reads_the_tester_green() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        found = inspector.every_class_reaches_the_diagnostic_mixin(
            {"component": "tester", "dir": "cairn/devices/tester"}, Path("cairn/devices/tester"))
    finally:
        os.chdir(here)
    check("test_the_sieve_reads_the_tester_green", found == [],
          f"{len(found)} finding(s): " + "; ".join(str(f.get("about")) for f in found))


def test_the_seal_stays_frozen_and_keeps_its_verdicts() -> None:
    import dataclasses
    from cairn.devices.tester.isolation import OPEN, SEALED, Seal
    from cairn.tools.base.diagnostic import DiagnosticBase
    a, b = Seal(SEALED, "d"), Seal(SEALED, "d")
    bad = []
    if not isinstance(a, DiagnosticBase):
        bad.append("Seal is not a DiagnosticBase")
    if not (a == b and hash(a) == hash(b)):
        bad.append("equal seals differ in == or hash")
    if a == Seal(OPEN, "d"):
        bad.append("seals with different verdicts compare equal")
    try:
        setattr(a, "verdict", OPEN)
        bad.append("a field assignment did not raise")
    except dataclasses.FrozenInstanceError:
        pass
    if not (a.sealed and a.trustworthy and Seal(OPEN, "x").trustworthy
            and not Seal(OPEN, "x").sealed and not Seal("INDETERMINATE", "x").trustworthy):
        bad.append("sealed/trustworthy changed")
    check("test_the_seal_stays_frozen_and_keeps_its_verdicts", not bad, "; ".join(bad))


def test_the_isolations_reach_the_mixin_and_keep_their_behaviour() -> None:
    from cairn.devices.tester.isolation import Isolation, NoIsolation
    from cairn.tools.base.diagnostic import DiagnosticBase
    bad = []
    if not issubclass(Isolation, DiagnosticBase):
        bad.append("Isolation is not a DiagnosticBase subclass")
    if not issubclass(NoIsolation, DiagnosticBase):
        bad.append("NoIsolation is not a DiagnosticBase subclass")
    n = NoIsolation()
    argv = ["python3", "-c", "print(1)"]
    if n.wrap(argv, str(_REPO)) != argv:
        bad.append(f"wrap changed the argv: {n.wrap(argv, str(_REPO))!r}")
    if n.available()[0] is not True:
        bad.append(f"available is {n.available()!r}")
    check("test_the_isolations_reach_the_mixin_and_keep_their_behaviour", not bad, "; ".join(bad))


def test_isolation_imports_fresh() -> None:
    r = subprocess.run([sys.executable, "-c", "import cairn.devices.tester.isolation"],
                       cwd=_REPO, capture_output=True, text=True)
    check("test_isolation_imports_fresh", r.returncode == 0,
          (r.stderr.strip().splitlines() or [""])[-1])


TEETH = (test_the_sieve_reads_the_tester_green,
         test_the_seal_stays_frozen_and_keeps_its_verdicts,
         test_the_isolations_reach_the_mixin_and_keep_their_behaviour,
         test_isolation_imports_fresh)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    check("test_the_tester_holds_every_clause_of_the_falsifier", not FAILURES,
          f"{len(FAILURES)} tooth/teeth red")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
