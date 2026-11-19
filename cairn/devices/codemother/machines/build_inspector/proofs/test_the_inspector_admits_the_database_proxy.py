"""Proof for ticket d183534450f5 — the database proxy's loopback relay stops redding the inference sole-path.

Measured 2026-11-18 (akiendelllinux at 053ca7cb9): with dbproxy v0 committed (ticket a22eb3c25ccd),
cairn/devices/dbproxy/forward.py and its proof import socket to dial the box's own Postgres on
loopback, and the sole-path mesh read that as a second door to the inference host: test_host.py,
test_import_sieve.py and test_an_admission_holds_at_any_depth.py went red. Outline 11.3.8, CC's
decision: the database proxy dials only loopback Postgres, so dbproxy/ stands on the sole-path
allowed list beside web_operator/ and usage/.

  1. the inspector's sole_path_holds reads the REAL dbproxy row clean, while forward.py still
     imports socket;
  2. in a seeded tree an unreasoned socket importer beside an admitted dbproxy is caught, and it
     is the only one caught;
  3. the three seat proofs are green with dbproxy admitted, and the live repo's
     sole_path_admissions_are_entered names no dbproxy admission.

The inspector's os.sep is pinned to '/', as the usage proof does, so the teeth measure on every box.

    bin/cairn test cairn/devices/codemother/machines/build_inspector/proofs/test_the_inspector_admits_the_database_proxy.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import types
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"d183534450f5": {
    "1": "test_the_real_dbproxy_row_reads_clean",
    "2": "test_an_unreasoned_dialer_beside_dbproxy_is_caught_alone",
    "3": "test_the_seats_are_green_and_no_dbproxy_admission_stands_unentered"}}

SEATS = ("cairn/devices/inferenceproxy/proofs/test_host.py",
         "cairn/tools/import_sieve/proofs/test_import_sieve.py",
         "cairn/tools/import_sieve/proofs/test_an_admission_holds_at_any_depth.py")


def _inspector(monkeypatch):
    """The inspector with its os.sep the import graph's own '/'."""
    from cairn.devices.codemother.machines.build_inspector import inspector
    fake = types.SimpleNamespace(**{k: getattr(os, k) for k in dir(os) if not k.startswith("__")})
    fake.sep = "/"
    monkeypatch.setattr(inspector, "os", fake)
    return inspector


def test_the_real_dbproxy_row_reads_clean(monkeypatch):
    insp = _inspector(monkeypatch)
    dbproxy = _REPO_ROOT / "cairn" / "devices" / "dbproxy"
    assert "import socket" in (dbproxy / "forward.py").read_text(encoding="utf-8"), \
        "forward.py no longer dials: this tooth would read clean for the wrong reason"
    found = insp.sole_path_holds({"component": "dbproxy"}, dbproxy)
    assert found == [], [f["about"] for f in found]


def test_an_unreasoned_dialer_beside_dbproxy_is_caught_alone(monkeypatch):
    insp = _inspector(monkeypatch)
    root = Path(scratch_dir("testing-d183-dbproxy-"))
    for name, file in (("dbproxy", "forward.py"), ("rogue", "dialer.py")):
        (root / name).mkdir()
        (root / name / file).write_text("import socket\n", encoding="utf-8")
    assert insp.sole_path_holds({"component": "dbproxy"}, root / "dbproxy") == [], \
        "the admitted database proxy redded its own row"
    rogue = insp.sole_path_holds({"component": "rogue"}, root / "rogue")
    assert [f["method"] for f in rogue] == ["sole_path_holds"], rogue
    assert "rogue/dialer.py" in rogue[0]["about"], rogue[0]


def test_the_seats_are_green_and_no_dbproxy_admission_stands_unentered():
    env = {**os.environ, "PYTHONPATH": str(_REPO_ROOT)}
    for seat in SEATS:
        r = subprocess.run([sys.executable, str(_REPO_ROOT / seat)], cwd=_REPO_ROOT, env=env,
                           capture_output=True, text=True, timeout=600)
        assert r.returncode == 0, f"{seat} is red:\n{(r.stdout + r.stderr)[-1500:]}"
    from cairn.devices.codemother.machines.build_inspector import inspector
    assert "sole_path_admissions_are_entered" in inspector.SIEVES
    report = inspector.inspect(component="exemptions")
    mine = [f.get("about") for f in report["findings"]
            if f.get("method") == "sole_path_admissions_are_entered"
            and "dbproxy" in str(f.get("about"))]
    assert mine == [], mine


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
