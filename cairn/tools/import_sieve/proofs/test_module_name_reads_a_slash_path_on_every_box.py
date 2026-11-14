"""Proof for ticket 41fdc9cb5d50 — module_name reads a '/' path as a dotted module on every box.

Measured 2026-11-13 on akienyoga9i (Windows): module_name('cairn/tools/base/diagnostic.py')
answered 'cairn/tools/base/diagnostic', because it split on os.sep and os.sep is a backslash
there. Its docstring and every caller hand it '/' paths (3db1656ee keyed the import graph with
'/'), so build_inspector's every_class_reaches_the_diagnostic_mixin named no module and read
DiagnosticBase itself as 'no route': its proof red 4 teeth on Windows while sealed green on Linux.

The teeth pin the separator to a backslash inside the module, so they red the unfixed split on
any box, Linux included:

  1. under a backslash os.sep, a '/' path and a '/' package __init__ name their dotted module;
  2. under a backslash os.sep, a native backslash path still names its dotted module.

    bin/cairn test cairn/tools/import_sieve/proofs/test_module_name_reads_a_slash_path_on_every_box.py
"""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"41fdc9cb5d50": {
    "1": "test_a_slash_path_names_its_module_under_a_backslash_sep",
    "2": "test_a_native_backslash_path_still_names_its_module"}}


def _windows_sieve(monkeypatch):
    """The sieve module with its os seeing a backslash separator, as on Windows."""
    from cairn.tools.import_sieve import sieve
    fake = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith("__")})
    fake.sep = "\\"
    monkeypatch.setattr(sieve, "os", fake)
    return sieve


def test_a_slash_path_names_its_module_under_a_backslash_sep(monkeypatch):
    sieve = _windows_sieve(monkeypatch)
    got = (sieve.module_name("cairn/tools/base/diagnostic.py"),
           sieve.module_name("cairn/tools/base/__init__.py"))
    assert got == ("cairn.tools.base.diagnostic", "cairn.tools.base"), got


def test_a_native_backslash_path_still_names_its_module(monkeypatch):
    sieve = _windows_sieve(monkeypatch)
    got = sieve.module_name("cairn\\tools\\base\\probe.py")
    assert got == "cairn.tools.base.probe", got


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
