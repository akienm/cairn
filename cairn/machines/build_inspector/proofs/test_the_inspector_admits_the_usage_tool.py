"""Proof for ticket dd79ed8a1ece — the usage tool's account read stops redding the inference sole-path.

Measured 2026-11-13 (Linux census at 6cbae796b): cairn/tools/usage/usage.py and its proof import
urllib.request for one HTTPS GET of the account's usage, and the sole-path mesh read that as a
second door to the inference host. Q#95, CC's decision (outline 11.4.10.1): reading the account's
usage calls no model, so usage/ stands on the sole-path allowed list beside web_operator/.

  1. the inspector's sole_path_holds reads the REAL usage row clean;
  2. in a seeded tree an unreasoned urllib importer beside an admitted usage tool is caught,
     and it is the only one caught;
  3. the live repo's sole_path_admissions_are_entered names no usage admission: the usage
     admission at test_host.py either carries an exemption_set entry or no longer exists as a
     single-file member (measured 2026-11-14 by akiendelllinux on main b9ac3f87c: two findings,
     test_host.py::cairn/tools/usage/usage.py and ::its proof, because 6b0dfaa14efd admitted the
     two files singly and D1 admits the tool directory, which needs no entry).

The teeth pin the inspector's os.sep to '/', the separator import_graph keys every file with
(3db1656ee): on main the row prefix is built with os.sep (ticket d64e7aa418d2 fixes that), so on
Windows every row would read green and neither tooth could red. Pinned, they measure the
admission on every box.

    bin/cairn test cairn/machines/build_inspector/proofs/test_the_inspector_admits_the_usage_tool.py
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

PROVES = {"dd79ed8a1ece": {
    "1": "test_the_real_usage_row_reads_clean",
    "2": "test_an_unreasoned_dialer_beside_usage_is_caught_alone",
    "3": "test_no_usage_admission_stands_unentered"}}


def _inspector(monkeypatch):
    """The inspector with its os.sep the import graph's own '/'."""
    from cairn.machines.build_inspector import inspector
    fake = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith("__")})
    fake.sep = "/"
    monkeypatch.setattr(inspector, "os", fake)
    return inspector


def test_the_real_usage_row_reads_clean(monkeypatch):
    insp = _inspector(monkeypatch)
    usage = _REPO_ROOT / "cairn" / "tools" / "usage"
    assert (usage / "usage.py").read_text(encoding="utf-8").count("import urllib.request") >= 1, \
        "usage.py no longer dials: this tooth would read clean for the wrong reason"
    found = insp.sole_path_holds({"component": "usage"}, usage)
    assert found == [], [f["about"] for f in found]


def test_an_unreasoned_dialer_beside_usage_is_caught_alone(monkeypatch):
    insp = _inspector(monkeypatch)
    root = Path(scratch_dir("testing-dd79-usage-"))
    for name, file in (("usage", "usage.py"), ("rogue", "dialer.py")):
        (root / name).mkdir()
        (root / name / file).write_text("import urllib.request\n", encoding="utf-8")
    assert insp.sole_path_holds({"component": "usage"}, root / "usage") == [], \
        "the admitted usage tool redded its own row"
    rogue = insp.sole_path_holds({"component": "rogue"}, root / "rogue")
    assert [f["method"] for f in rogue] == ["sole_path_holds"], rogue
    assert "rogue/dialer.py" in rogue[0]["about"], rogue[0]


def test_no_usage_admission_stands_unentered():
    from cairn.machines.build_inspector import inspector
    assert "sole_path_admissions_are_entered" in inspector.SIEVES
    report = inspector.inspect(component="exemptions")
    mine = [f.get("about") for f in report["findings"]
            if f.get("method") == "sole_path_admissions_are_entered"
            and "cairn/tools/usage" in str(f.get("about"))]
    assert mine == [], mine


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
