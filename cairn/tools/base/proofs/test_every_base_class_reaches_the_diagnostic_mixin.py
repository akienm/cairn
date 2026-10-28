#!/usr/bin/env python3
"""Proof that every class with code in cairn/tools/base reaches DiagnosticBase, and loses nothing by it.

Akien 2026-10-27 (open-4141d959b634): "everybody must inherit it. that's why it's a mixin" /
"any class with code it in should be able to run a diagnostic report when we need it." The
sieve from 339a45cee6a1 measured 18 base classes that did not reach the mixin: AmbiguousComponent,
BreadcrumbLog, CoreValuesMixin, ExternalParticipant, TransitionGate, the nested _Loud, Workflow,
and the 11 IllegalTransition subclasses in transitions.py. Ticket e8b58520aeb9 converts them.

Teeth, each importing the code under test at call time:
  (1) the sieve returns no findings for component base;
  (2) diagnostic.py's top-level imports are __future__ and stdlib only, so every module that
      gains the mixin stays as light as it was;
  (3) every touched base module imports in a fresh interpreter (an inconsistent MRO is an
      import-time TypeError);
  (4) each converted exception keeps its str and args and is a DiagnosticBase; the ten that
      round-tripped through pickle before the build still do, and carry NOT_WIRED by identity.
      CastRefused and AmbiguousComponent did not round-trip before the build (measured
      2026-10-27: their __init__ takes arguments args does not carry); that is unchanged and
      out of scope here;
  (5) Workflow stays frozen, equal values stay equal with equal hashes, and emit works on it;
  (6) BaseShim's MRO lists CoreValuesMixin before DiagnosticBase, as BaseDevice's does.

    bin/cairn test cairn/tools/base/proofs/test_every_base_class_reaches_the_diagnostic_mixin.py
"""

from __future__ import annotations

import ast
import os
import pickle
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_BASE = _REPO / "cairn" / "tools" / "base"

PROVES = {"e8b58520aeb9": {"all": "test_base_holds_every_clause_of_the_falsifier"}}

_MODULES = ("diagnostic", "address", "breadcrumb_log", "core_values", "external", "gate_class",
            "probe", "workflow_grammar", "transitions", "shim", "device")

_GATE_REDS = ("EntryGateRed", "BuildGateRed", "ExitGateRed", "WatchmeEmissionRed", "ProofNamedRed",
              "WorkingTreeDirtyRed", "TicketRequiredRed", "ClearanceRequiredRed", "DemoGateRed",
              "FixmeGateRed")

_WORKFLOW = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _top_level_imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add("." * node.level + (node.module or ""))
    return names


def test_the_sieve_reads_base_green() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        found = inspector.every_class_reaches_the_diagnostic_mixin(
            {"component": "base", "dir": "cairn/tools/base"}, Path("cairn/tools/base"))
    finally:
        os.chdir(here)
    check("test_the_sieve_reads_base_green", found == [],
          f"{len(found)} finding(s): " + "; ".join(str(f.get("about")) for f in found))


def test_diagnostic_loads_only_the_standard_library() -> None:
    names = _top_level_imports(_BASE / "diagnostic.py")
    stray = sorted(n for n in names
                   if n.split(".")[0] not in sys.stdlib_module_names and n != "__future__")
    check("test_diagnostic_loads_only_the_standard_library", not stray and bool(names),
          f"stray {stray}")


def test_every_touched_module_imports_fresh() -> None:
    bad = []
    for mod in _MODULES:
        r = subprocess.run([sys.executable, "-c", f"import cairn.tools.base.{mod}"],
                           cwd=_REPO, capture_output=True, text=True)
        if r.returncode != 0:
            bad.append(f"{mod}: {(r.stderr.strip().splitlines() or ['?'])[-1]}")
    check("test_every_touched_module_imports_fresh", not bad, "; ".join(bad))


def test_the_exceptions_keep_their_shape() -> None:
    from cairn.tools.base import transitions as T
    from cairn.tools.base.address import AmbiguousComponent
    from cairn.tools.base.diagnostic import NOT_WIRED, DiagnosticBase
    bad = []
    for name in _GATE_REDS:
        cls = getattr(T, name)
        e = cls("msg")
        if not (str(e) == "msg" and e.args == ("msg",)):
            bad.append(f"{name} str/args {str(e)!r} {e.args!r}")
        if not isinstance(e, DiagnosticBase):
            bad.append(f"{name} is not a DiagnosticBase")
            continue
        r = pickle.loads(pickle.dumps(e))
        if not (type(r) is cls and r.args == e.args and str(r) == str(e)):
            bad.append(f"{name} pickle round-trip changed it")
        if r.__dict__.get("_diagnostic_receiver") is not NOT_WIRED:
            bad.append(f"{name} unpickled receiver is not NOT_WIRED")
    c = T.CastRefused(["a lack"])
    if str(c) != "cast_ticket refused (1 lack): a lack. Nothing was written." \
            or c.args != (str(c),) or not isinstance(c, DiagnosticBase):
        bad.append(f"CastRefused {str(c)!r} {c.args!r}")
    a = AmbiguousComponent("x", [Path("/a"), Path("/b")])
    if not (a.args == (str(a),) and str(a).startswith("'x' names 2 components, not one: /a, /b")
            and isinstance(a, LookupError) and isinstance(a, DiagnosticBase)):
        bad.append(f"AmbiguousComponent {str(a)[:60]!r}")
    check("test_the_exceptions_keep_their_shape", not bad, "; ".join(bad))


class _Collect:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)


def test_the_workflow_stays_frozen_and_can_emit() -> None:
    import dataclasses
    from cairn.tools.base.diagnostic import DiagnosticBase
    from cairn.tools.base.workflow_grammar import parse_workflow
    w1, w2 = parse_workflow(_WORKFLOW), parse_workflow(_WORKFLOW)
    bad = []
    if not isinstance(w1, DiagnosticBase):
        bad.append("Workflow is not a DiagnosticBase")
    if not (w1 == w2 and hash(w1) == hash(w2)):
        bad.append("equal workflows differ in == or hash")
    try:
        setattr(w1, "cursor", 0)
        bad.append("a field assignment did not raise")
    except dataclasses.FrozenInstanceError:
        pass
    sink = _Collect()
    w1.__dict__["_diagnostic_receiver"] = sink   # the frozen setters refuse; __dict__ is the honest door
    rec = w1.emit("probe-gate")
    if not (isinstance(rec, dict) and sink.records == [rec] and rec.get("source") == "Workflow"):
        bad.append(f"emit returned {rec!r}")
    if not (w1 == w2 and hash(w1) == hash(w2)):
        bad.append("emitting changed equality or hash")
    check("test_the_workflow_stays_frozen_and_can_emit", not bad, "; ".join(bad))


def test_the_shim_orders_core_values_first() -> None:
    from cairn.tools.base.core_values import CoreValuesMixin
    from cairn.tools.base.diagnostic import DiagnosticBase
    from cairn.tools.base.shim import BaseShim
    mro = BaseShim.__mro__
    ok = CoreValuesMixin in mro and DiagnosticBase in mro \
        and mro.index(CoreValuesMixin) < mro.index(DiagnosticBase) \
        and issubclass(CoreValuesMixin, DiagnosticBase)
    check("test_the_shim_orders_core_values_first", ok, " -> ".join(c.__name__ for c in mro))


TEETH = (test_the_sieve_reads_base_green,
         test_diagnostic_loads_only_the_standard_library,
         test_every_touched_module_imports_fresh,
         test_the_exceptions_keep_their_shape,
         test_the_workflow_stays_frozen_and_can_emit,
         test_the_shim_orders_core_values_first)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    check("test_base_holds_every_clause_of_the_falsifier", not FAILURES,
          f"{len(FAILURES)} tooth/teeth red")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
