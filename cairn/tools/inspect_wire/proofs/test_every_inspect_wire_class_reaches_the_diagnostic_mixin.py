#!/usr/bin/env python3
"""Proof that every class with code in inspect_wire reaches DiagnosticBase, and loses nothing by it.

Measured 2026-11-16: build_inspector's every_class_reaches_the_diagnostic_mixin stood above
baseline at one component, tools/inspect_wire. inspect_wire.py:96 `class InspectRefused(RuntimeError)`
"has code and does not reach DiagnosticBase" ('no route'), added by 3e08102ef35a (080caf937).
Ticket 5a2f128f044d makes DiagnosticBase its first base, the AmbiguousComponent pattern
(cairn/tools/base/address.py).

Teeth, each importing the code under test at call time:
  (1) the sieve, asked over the bus as every outside proof asks it, returns no findings for
      cairn/tools/inspect_wire;
  (2) behaviour unchanged: InspectRefused is a DiagnosticBase and still a RuntimeError, keeps
      its message, args, judge, reason and raised, and is caught by `except RuntimeError`;
      inspect_wire.py's top-level imports are stdlib plus cairn.tools.base.diagnostic only.

    CAIRN_BUS_HOME=<scratch> bin/cairn test cairn/tools/inspect_wire/proofs/test_every_inspect_wire_class_reaches_the_diagnostic_mixin.py
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"5a2f128f044d": {
    "1": "test_no_bare_class_in_inspect_wire",
    "2": "test_behaviour_unchanged",
}}

_WIRE = _REPO / "cairn" / "tools" / "inspect_wire" / "inspect_wire.py"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail[:1500]}" if detail else ""), flush=True)
    if not ok:
        FAILURES.append(name)


def test_no_bare_class_in_inspect_wire() -> None:
    from cairn.tools.inspect_wire.inspect_wire import ask
    found = ask("every_class_reaches_the_diagnostic_mixin",
                {"component": "cairn/tools/inspect_wire", "dir": "cairn/tools/inspect_wire"},
                _REPO / "cairn" / "tools" / "inspect_wire")
    check("test_no_bare_class_in_inspect_wire", found == [],
          f"{len(found)} finding(s): " + "; ".join(str(f.get("about")) for f in found))


def _top_imports(path: Path) -> list[str]:
    mods = []
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module)
    return mods


def test_behaviour_unchanged() -> None:
    from cairn.tools.base.diagnostic import DiagnosticBase
    from cairn.tools.inspect_wire.inspect_wire import InspectRefused

    lacks: list[str] = []
    if not issubclass(InspectRefused, DiagnosticBase):
        lacks.append("InspectRefused is not a DiagnosticBase")
    if not issubclass(InspectRefused, RuntimeError):
        lacks.append("InspectRefused is no longer a RuntimeError")
    exc = InspectRefused("testing_judge", "testing reason", "ValueError")
    if str(exc) != "inspect 'testing_judge' refused: testing reason":
        lacks.append(f"the message changed: {str(exc)!r}")
    if exc.args != ("inspect 'testing_judge' refused: testing reason",):
        lacks.append(f"args changed: {exc.args!r}")
    if (exc.judge, exc.reason, exc.raised) != ("testing_judge", "testing reason", "ValueError"):
        lacks.append(f"attributes changed: {(exc.judge, exc.reason, exc.raised)!r}")
    if InspectRefused("j", "r").raised is not None:
        lacks.append("raised no longer defaults to None")
    try:
        raise InspectRefused("j", "r")
    except RuntimeError:
        pass
    except BaseException as other:  # noqa: BLE001
        lacks.append(f"except RuntimeError missed it: {type(other).__name__}")

    allowed = set(sys.stdlib_module_names) | {"__future__", "cairn.tools.base.diagnostic"}
    extra = [m for m in _top_imports(_WIRE) if m.split(".")[0] not in allowed and m not in allowed]
    if extra:
        lacks.append(f"inspect_wire.py's top-level imports grew beyond stdlib + diagnostic: {extra}")

    check("test_behaviour_unchanged", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    print("5a2f128f044d — every class with code in inspect_wire reaches the diagnostic mixin")
    for tooth in (test_no_bare_class_in_inspect_wire, test_behaviour_unchanged):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
