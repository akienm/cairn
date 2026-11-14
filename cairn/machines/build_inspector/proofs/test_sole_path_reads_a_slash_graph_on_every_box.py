"""Proof for ticket d64e7aa418d2 — sole_path_holds matches its row against the '/'-keyed import graph on every box.

Measured 2026-11-13 on akienyoga9i (Windows) at main: test_inspector.py's planted-dialer tooth red
"the planted dialer must red exactly sole_path_holds: []". sole_path_holds built its row prefix as
component + os.sep, a backslash there, while import_sieve.import_graph keys every file with '/'
(3db1656ee); no key started with 'rogue\', so a second door to the inference host read green on
Windows. Sealed green on Linux, where os.sep is '/'.

The teeth pin the inspector's os.sep to a backslash, so they red the os.sep prefix on any box:

  1. under a backslash os.sep, a component that imports a dialer reds its own row, naming the file;
  2. under a backslash os.sep, a sibling whose name extends the row's ('rogue_two') does not red it.

    bin/cairn test cairn/machines/build_inspector/proofs/test_sole_path_reads_a_slash_graph_on_every_box.py
"""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"d64e7aa418d2": {
    "1": "test_a_planted_dialer_reds_its_own_row_under_a_backslash_sep",
    "2": "test_a_sibling_with_a_longer_name_does_not_red_the_row"}}


def _windows_inspector(monkeypatch):
    """The inspector with its os seeing a backslash separator, as on Windows."""
    from cairn.machines.build_inspector import inspector
    fake = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith("__")})
    fake.sep = "\\"
    monkeypatch.setattr(inspector, "os", fake)
    return inspector


def _tree(prefix: str, dialers: list[str]) -> Path:
    root = Path(scratch_dir(prefix))
    for name in dialers:
        (root / name).mkdir()
        (root / name / "dialer.py").write_text("import urllib.request\n", encoding="utf-8")
    return root


def test_a_planted_dialer_reds_its_own_row_under_a_backslash_sep(monkeypatch):
    insp = _windows_inspector(monkeypatch)
    root = _tree("testing-sole-own-", ["rogue"])
    found = insp.sole_path_holds({"component": "rogue"}, root / "rogue")
    assert [f["method"] for f in found] == ["sole_path_holds"], found
    assert "rogue/dialer.py" in found[0]["about"], found[0]


def test_a_sibling_with_a_longer_name_does_not_red_the_row(monkeypatch):
    insp = _windows_inspector(monkeypatch)
    root = _tree("testing-sole-sib-", ["rogue_two"])
    (root / "rogue").mkdir()
    assert insp.sole_path_holds({"component": "rogue"}, root / "rogue") == []
    assert [f["method"] for f in insp.sole_path_holds({"component": "rogue_two"}, root / "rogue_two")] \
        == ["sole_path_holds"], "the control did not red: the sibling's own row must"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
