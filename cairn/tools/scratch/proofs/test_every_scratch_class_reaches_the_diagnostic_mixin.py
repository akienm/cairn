#!/usr/bin/env python3
"""Proof that every class with code in scratch reaches DiagnosticBase, and loses nothing by it.

Measured 2026-11-11: the build inspector filed inspector-new-finding-every-class-reaches-the-
diagnostic-mixin naming scratch.ScratchPath in scratch. Ticket f1c120719c25 makes DiagnosticBase the first base of
each, as 668c8d64b4e2 did for tester (Akien, 2026-10-27: "any class with code in it should be
able to run a diagnostic report when we need it").

Teeth, each importing the code under test at call time:
  (1) the inspector's every_class_reaches_the_diagnostic_mixin sieve returns no findings for
      component scratch;
  (2) behaviour unchanged: each class is a DiagnosticBase and keeps its original base, and
      the smoke below still holds.

    bin/cairn test cairn/tools/scratch/proofs/test_every_scratch_class_reaches_the_diagnostic_mixin.py
"""

from __future__ import annotations

import builtins
import importlib
import os
import pathlib
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"f1c120719c25": {
    "1": "test_no_bare_class_in_scratch",
    "2": "test_behaviour_unchanged",
}}

_DIR = "cairn/tools/scratch"
_PKG = "cairn.tools.scratch"
_CLASSES = [('scratch', 'ScratchPath', 'PurePath')]
_MODULES = ['scratch']

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_bare_class_in_scratch() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        found = inspector.every_class_reaches_the_diagnostic_mixin(
            {"component": "scratch", "dir": _DIR}, Path(_DIR))
    finally:
        os.chdir(here)
    check("test_no_bare_class_in_scratch", found == [],
          f"{len(found)} finding(s): " + "; ".join(str(f.get("about")) for f in found))


def _base(name):
    if name is None:
        return object
    return getattr(builtins, name, None) or getattr(pathlib, name)


def test_behaviour_unchanged() -> None:
    from cairn.tools.base.diagnostic import DiagnosticBase
    lacks: list[str] = []
    mods = {m: importlib.import_module(f"{_PKG}.{m}") for m in _MODULES}
    for mod, name, base in _CLASSES:
        cls = getattr(mods[mod], name)
        if not issubclass(cls, DiagnosticBase):
            lacks.append(f"{mod}.{name} is not a DiagnosticBase")
        if not issubclass(cls, _base(base)):
            lacks.append(f"{mod}.{name} is no longer a {base}")
    ok = False
    try:
        import pathlib
        sp = mods['scratch'].ScratchPath('/tmp/x')
        with sp as inner:
            pass
        ok = inner is sp and isinstance(sp / 'y', mods['scratch'].ScratchPath) and str(sp / 'y') == '/tmp/x/y' and sp == pathlib.Path('/tmp/x')
    except Exception as exc:  # noqa: BLE001 — a smoke that cannot run is a red, loudly
        lacks.append(f"smoke raised {type(exc).__name__}: {exc}")
    if not ok:
        lacks.append("the smoke no longer holds")
    check("test_behaviour_unchanged", not lacks, "; ".join(lacks))


def main() -> int:
    for tooth in (test_no_bare_class_in_scratch, test_behaviour_unchanged):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
