#!/usr/bin/env python3
"""Proof that every class with code in diagnostic_inspector reaches DiagnosticBase, and loses nothing by it.

Measured 2026-11-11: the build inspector filed inspector-new-finding-every-class-reaches-the-
diagnostic-mixin naming inspector.Mailbox, inspector._Filter, inspector.Inspector, inspector.CompletenessRegistry in diagnostic_inspector. Ticket 86b1694956b0 makes DiagnosticBase the first base of
each, as 668c8d64b4e2 did for tester (Akien, 2026-10-27: "any class with code in it should be
able to run a diagnostic report when we need it").

Teeth, each importing the code under test at call time:
  (1) the inspector's every_class_reaches_the_diagnostic_mixin sieve returns no findings for
      component diagnostic_inspector;
  (2) behaviour unchanged: each class is a DiagnosticBase and keeps its original base, and
      the smoke below still holds;
  (3) it writes its own logs and decides nothing from them (Akien, open-d32047bb1759): inspector.py
      reads none of its own diagnostics, a trail it emitted into a mailbox never changes what it
      finds in the log it is handed, and with the mixin made unimportable it reads on and says so
      (charter edge (g)).

    bin/cairn test cairn/machines/diagnostic_inspector/proofs/test_every_diagnostic_inspector_class_reaches_the_diagnostic_mixin.py
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

PROVES = {"86b1694956b0": {
    "1": "test_no_bare_class_in_diagnostic_inspector",
    "2": "test_behaviour_unchanged",
    "3": "test_it_writes_its_own_logs_and_decides_nothing_from_them",
}}

_DIR = "cairn/machines/diagnostic_inspector"
_PKG = "cairn.machines.diagnostic_inspector"
_CLASSES = [('inspector', 'Mailbox', None), ('inspector', '_Filter', None), ('inspector', 'Inspector', None), ('inspector', 'CompletenessRegistry', None)]
_MODULES = ['inspector']

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_bare_class_in_diagnostic_inspector() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        found = inspector.every_class_reaches_the_diagnostic_mixin(
            {"component": "diagnostic_inspector", "dir": _DIR}, Path(_DIR))
    finally:
        os.chdir(here)
    check("test_no_bare_class_in_diagnostic_inspector", found == [],
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
        m = mods['inspector']
        m.Mailbox(); m.Inspector(); m.CompletenessRegistry(); m._Filter('x', lambda r: True)
        ok = True
    except Exception as exc:  # noqa: BLE001 — a smoke that cannot run is a red, loudly
        lacks.append(f"smoke raised {type(exc).__name__}: {exc}")
    if not ok:
        lacks.append("the smoke no longer holds")
    check("test_behaviour_unchanged", not lacks, "; ".join(lacks))


def test_it_writes_its_own_logs_and_decides_nothing_from_them() -> None:
    import ast
    lacks: list[str] = []
    m = importlib.import_module(f"{_PKG}.inspector")
    src = Path(m.__file__).read_text(encoding="utf-8")
    own = {"emit", "diagnostic_records", "held_diagnostics", "diagnostic_trail", "_receiver"}
    reads = sorted({n.attr for n in ast.walk(ast.parse(src))
                    if isinstance(n, ast.Attribute) and n.attr in own})
    if reads:
        lacks.append(f"inspector.py touches its own diagnostics: {reads}")
    log = [{"gate": "enter", "pointer": "ticket/A", "ts": "2026-11-11T00:00:01", "us": "000001"},
           {"gate": "verify", "pointer": "ticket/A", "ts": "2026-11-11T00:00:02", "us": "000002"}]
    quiet = m.Inspector(m.CompletenessRegistry()).inspect(list(log), m.by_pointer("ticket/A"))
    loud = m.Inspector(m.CompletenessRegistry())
    box = m.Mailbox()
    loud.set_diagnostic_receiver(box)
    loud.emit("decide", pointer="ticket/A", values={"expected": "x", "actual": "y"})
    heard = loud.inspect(list(log), m.by_pointer("ticket/A"))
    if not box.records():
        lacks.append("the inspector's own emit reached no mailbox — it cannot write its own logs")
    if heard != quiet:
        lacks.append(f"its own trail changed its findings: {heard} != {quiet}")
    # Charter edge (g): the reader works even when logging itself is broken. Make the mixin
    # unimportable in a fresh interpreter; the inspector must still load, read, and say why.
    import subprocess
    broken = ("import sys; sys.modules['cairn.tools.base.diagnostic'] = None\n"
              f"import {_PKG}.inspector as m\n"
              "f = m.Inspector(m.CompletenessRegistry()).inspect([], lambda r: True)\n"
              "print('READ', f['gates'] == [] and m.DiagnosticBase is object)")
    run = subprocess.run([sys.executable, "-c", broken], cwd=_REPO, capture_output=True,
                         text=True, timeout=60)
    if "READ True" not in run.stdout or "did not import" not in run.stderr:
        lacks.append(f"with the mixin broken the inspector did not read on loudly: "
                     f"rc={run.returncode} out={run.stdout[-200:]!r} err={run.stderr[-300:]!r}")
    check("test_it_writes_its_own_logs_and_decides_nothing_from_them", not lacks, "; ".join(lacks))


def main() -> int:
    for tooth in (test_no_bare_class_in_diagnostic_inspector, test_behaviour_unchanged,
                  test_it_writes_its_own_logs_and_decides_nothing_from_them):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
