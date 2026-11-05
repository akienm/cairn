#!/usr/bin/env python3
"""Proof that every class with code in aider_shim reaches DiagnosticBase, and loses nothing by it.

Measured 2026-11-05: ea19fc079c0b's PROVED crossing was refused BuildGateRed by build_inspector's
every_class_reaches_the_diagnostic_mixin, listing 13 aider_shim classes that did not reach the
mixin (driver.DriveResult, fence.Fence, fence.SeenLog, holder._Recorder, holder._Stub,
interceptor._Message/_Choice/_Usage/_Response/_Logging/_Surface, translate.Brief,
venv.VenvRunFailed). Ticket b13c53dd679c makes DiagnosticBase the first base of each, as
668c8d64b4e2 did for tester.

Teeth, each importing the code under test at call time:
  (1) the sieve returns no findings for component aider_shim;
  (2) behaviour unchanged: all 13 are DiagnosticBase subclasses; Fence stays frozen and equal
      values stay equal; a _Surface still records a non-underscore attribute read; a _stub
      still answers with a _Recorder and still carries its real exception class; VenvRunFailed
      is still a RuntimeError; DriveResult still asdict()s.

    PYTHONPATH=. python3 cairn/devices/aider_shim/proofs/test_every_aider_shim_class_reaches_the_diagnostic_mixin.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"b13c53dd679c": {
    "1": "test_no_bare_class_in_aider_shim",
    "2": "test_behaviour_unchanged",
}}

_CLASSES = (("driver", "DriveResult"), ("fence", "Fence"), ("fence", "SeenLog"),
            ("holder", "_Recorder"), ("holder", "_Stub"), ("interceptor", "_Message"),
            ("interceptor", "_Choice"), ("interceptor", "_Usage"), ("interceptor", "_Response"),
            ("interceptor", "_Logging"), ("interceptor", "_Surface"), ("translate", "Brief"),
            ("venv", "VenvRunFailed"))

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_bare_class_in_aider_shim() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        found = inspector.every_class_reaches_the_diagnostic_mixin(
            {"component": "aider_shim", "dir": "cairn/devices/aider_shim"},
            Path("cairn/devices/aider_shim"))
    finally:
        os.chdir(here)
    check("test_no_bare_class_in_aider_shim", found == [],
          f"{len(found)} finding(s): " + "; ".join(str(f.get("about")) for f in found))


def test_behaviour_unchanged() -> None:
    import dataclasses
    import importlib
    from cairn.tools.base.diagnostic import DiagnosticBase

    lacks: list[str] = []
    mods = {m: importlib.import_module(f"cairn.devices.aider_shim.{m}")
            for m in ("driver", "fence", "holder", "interceptor", "translate", "venv")}
    for mod, name in _CLASSES:
        if not issubclass(getattr(mods[mod], name), DiagnosticBase):
            lacks.append(f"{mod}.{name} is not a DiagnosticBase")

    fence = mods["fence"].Fence
    try:
        f = fence()
        try:
            f.models = ("x",)
            lacks.append("Fence accepted an assignment (no longer frozen)")
        except dataclasses.FrozenInstanceError:
            pass
        if not (fence() == fence() and hash(fence()) == hash(fence())):
            lacks.append("equal Fences are no longer equal with equal hashes")
    except Exception as exc:  # noqa: BLE001
        lacks.append(f"Fence: {type(exc).__name__}: {exc}")

    surface = mods["interceptor"]._Surface("probe_surface")
    object.__setattr__(surface, "_cairn_touched", set())
    surface.completion = lambda: None
    _ = surface.completion
    if "completion" not in object.__getattribute__(surface, "_cairn_touched"):
        lacks.append("_Surface no longer records a touched attribute")

    holder = mods["holder"]
    stub = holder._stub("mixpanel", ("MixpanelException",))
    if not isinstance(stub.anything, holder._Recorder):
        lacks.append("_stub no longer answers with a _Recorder")
    if not issubclass(stub.MixpanelException, Exception):
        lacks.append("_stub's MixpanelException is no longer an Exception class")

    if not issubclass(mods["venv"].VenvRunFailed, RuntimeError):
        lacks.append("VenvRunFailed is no longer a RuntimeError")

    dr = mods["driver"].DriveResult(ticket="t", piece_index=0, model="m", at="now")
    if dataclasses.asdict(dr).get("ticket") != "t":
        lacks.append("DriveResult no longer asdict()s")

    check("test_behaviour_unchanged", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    for tooth in (test_no_bare_class_in_aider_shim, test_behaviour_unchanged):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
