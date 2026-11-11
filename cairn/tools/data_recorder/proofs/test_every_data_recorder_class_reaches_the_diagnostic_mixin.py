#!/usr/bin/env python3
"""Proof that every class with code in data_recorder reaches DiagnosticBase, and loses nothing by it.

Measured 2026-11-11: the build inspector filed inspector-new-finding-every-class-reaches-the-
diagnostic-mixin naming data_recorder.DataRecorder in data_recorder. Ticket 4881eace5df8 makes DiagnosticBase the first base of
each, as 668c8d64b4e2 did for tester (Akien, 2026-10-27: "any class with code in it should be
able to run a diagnostic report when we need it").

Teeth, each importing the code under test at call time:
  (1) the inspector's every_class_reaches_the_diagnostic_mixin sieve returns no findings for
      component data_recorder;
  (2) behaviour unchanged: each class is a DiagnosticBase and keeps its original base, and
      the smoke below still holds;
  (3) the mixin makes the recorder no machine (its charter's Law 6 test): records stay
      structured JSON rather than prose, a diagnostic it emits writes nothing at the recorder's
      own address and enters none of its records, and data_recorder.py reads none of its own
      diagnostics, so it gates no writes and acts on no feedback.

    bin/cairn test cairn/tools/data_recorder/proofs/test_every_data_recorder_class_reaches_the_diagnostic_mixin.py
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

PROVES = {"4881eace5df8": {
    "1": "test_no_bare_class_in_data_recorder",
    "2": "test_behaviour_unchanged",
    "3": "test_the_mixin_makes_the_recorder_no_machine",
}}

_DIR = "cairn/tools/data_recorder"
_PKG = "cairn.tools.data_recorder"
_CLASSES = [('data_recorder', 'DataRecorder', None)]
_MODULES = ['data_recorder']

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_bare_class_in_data_recorder() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        found = inspector.every_class_reaches_the_diagnostic_mixin(
            {"component": "data_recorder", "dir": _DIR}, Path(_DIR))
    finally:
        os.chdir(here)
    check("test_no_bare_class_in_data_recorder", found == [],
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
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d) / 'rec'
            mods['data_recorder'].DataRecorder(base)
            ok = not base.exists()
    except Exception as exc:  # noqa: BLE001 — a smoke that cannot run is a red, loudly
        lacks.append(f"smoke raised {type(exc).__name__}: {exc}")
    if not ok:
        lacks.append("the smoke no longer holds")
    check("test_behaviour_unchanged", not lacks, "; ".join(lacks))


def test_the_mixin_makes_the_recorder_no_machine() -> None:
    import ast
    import json
    from cairn.tools.scratch.scratch import scratch_dir
    lacks: list[str] = []
    m = importlib.import_module(f"{_PKG}.data_recorder")
    tree = ast.parse(Path(m.__file__).read_text(encoding="utf-8"))
    own = {"emit", "diagnostic_records", "held_diagnostics", "diagnostic_trail", "_receiver",
           "set_diagnostic_receiver"}
    reads = sorted({n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr in own})
    if reads:
        lacks.append(f"data_recorder.py touches its own diagnostics: {reads}")
    base = scratch_dir("data-recorder-no-machine-") / "rec"
    rec = m.DataRecorder(base)
    rid = rec.write({"probe_source": "p", "inspector_target": "t", "finding": "f", "value": 1})
    before = sorted(p.relative_to(base).as_posix() for p in base.rglob("*"))
    rec.emit("decide", values={"expected": "x", "actual": "y"})
    after = sorted(p.relative_to(base).as_posix() for p in base.rglob("*"))
    if after != before:
        lacks.append(f"emit wrote at the recorder's own address: {before} -> {after}")
    got = rec.read()
    if [r.get("id") for r in got] != [rid] or got[0].get("value") != 1:
        lacks.append(f"the records are not exactly what was written: {got}")
    for line in rec.path.read_text(encoding="utf-8").splitlines():
        try:
            if not isinstance(json.loads(line), dict):
                lacks.append(f"a record is not a JSON object: {line!r}")
        except ValueError:
            lacks.append(f"a record is prose, not structured JSON: {line!r}")
    check("test_the_mixin_makes_the_recorder_no_machine", not lacks, "; ".join(lacks))


def main() -> int:
    for tooth in (test_no_bare_class_in_data_recorder, test_behaviour_unchanged,
                  test_the_mixin_makes_the_recorder_no_machine):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
