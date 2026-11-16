"""Proof for ticket 2dda7060d84e: the recompile gate runs a python that runs, from the repo root.

Measured 2026-11-16 on akienyoga9i: recompile_gate.sh ran bare ``python3``, which on a
Windows box is the Store alias stub that exits 9009, and it ran it from the cairn PACKAGE
dir (``$HERE/../..``), where ``import cairn`` only resolves if PYTHONPATH happens to be set.
So the lab never regenerated, and the log said FAILED every time.

Each tooth runs the gate under ``env -i`` in a scratch world. PATH holds only a bin dir of
links to the coreutils the gate needs, plus whichever python names the tooth stubs or links.
Nothing leaks in from the caller: no PYTHONPATH, no venv, no real HOME.

  1. python3 is a stub that exits 9009 and python is the host interpreter. The gate skips
     the stub, writes the lab, and its log gains no FAILED line.
  2. Every PATH python name is a stub, and CAIRN_VENV/bin/python3 is a wrapper over the host
     interpreter. The gate runs the wrapper (its marker appears) and writes the lab.
  3. No venv and every PATH python name a stub. The gate exits 0 and logs a FAILED line
     saying no Python 3 interpreter was found.

A hollow gate (the pre-build one) is red on all three: it runs the stub, and from the
package dir even a real python cannot import cairn without PYTHONPATH.

    PYTHONPATH=. python3 cairn/tools/intentions_model_compiler/proofs/test_the_gate_runs_a_python_that_runs.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "2dda7060d84e": {
        "1": "test_a_stub_python3_is_skipped_for_a_python_that_runs",
        "2": "test_the_venv_interpreter_is_tried_first",
        "3": "test_no_python_at_all_is_logged_and_never_blocks",
    },
}

_GATE = Path(__file__).resolve().parents[1] / "recompile_gate.sh"
_HOST = os.path.realpath(sys.executable)   # the base interpreter, not a venv shim
_BASH = shutil.which("bash") or "/bin/bash"
_COREUTILS = ("dirname", "mkdir", "date")


def _world(tag: str) -> dict:
    """A scratch world: two source trees, a lab, a log dir, a HOME and a bare bin dir."""
    d = Path(scratch_dir(f"rg-python-{tag}-"))
    commons, code = d / "CairnCommons", d / "cairn"
    (commons / "intentions-not-beside-code").mkdir(parents=True)
    (commons / "intentions-congruency-lab").mkdir(parents=True)
    (code / "cairn" / "tools" / "base").mkdir(parents=True)
    (commons / "intentions-not-beside-code" / "telos.md").write_text("the frame")
    (code / "cairn" / "tools" / "base" / ("intention+why" + ".json")).write_text(
        json.dumps({"what": "substrate"}))
    bindir = d / "bin"
    bindir.mkdir()
    for name in _COREUTILS:
        (bindir / name).symlink_to(shutil.which(name))
    (d / "home").mkdir()
    return {"d": d, "commons": commons, "code": code, "bin": bindir,
            "lab": commons / "intentions-congruency-lab", "logs": d / "logs",
            "venv": d / "no-venv"}


def _stub(path: Path) -> None:
    path.write_text("#!/bin/sh\necho 'Python was not found; run without arguments to install "
                    "from the Microsoft Store' >&2\nexit 9009\n")
    path.chmod(0o755)


def _wrapper(path: Path, marker: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/bin/sh\necho ran >> '{marker}'\nexec '{_HOST}' \"$@\"\n")
    path.chmod(0o755)


def _run(w: dict) -> subprocess.CompletedProcess:
    env = {"PATH": str(w["bin"]), "HOME": str(w["d"] / "home"),
           "CAIRN_VENV": str(w["venv"]), "CAIRN_LOG_DIR": str(w["logs"]),
           "CAIRN_LAB_OUT": str(w["lab"]), "CAIRN_COMMONS_ROOT": str(w["commons"]),
           "CAIRN_CODE_ROOT": str(w["code"]),
           "CAIRN_LB_TRACE_ROOT": str(w["d"] / "traces")}
    return subprocess.run(["/usr/bin/env", "-i", *(f"{k}={v}" for k, v in env.items()),
                           _BASH, _GATE.as_posix()], capture_output=True, text=True, timeout=120)


def _log(w: dict) -> str:
    p = w["logs"] / "recompile-gate.log"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _lab_filled(w: dict) -> set[str]:
    return {n for n in os.listdir(w["lab"]) if not n.startswith("_")}


_WANT = {"telos.md", "cairn-tools-base--intention+why" + ".json"}


def test_a_stub_python3_is_skipped_for_a_python_that_runs():
    w = _world("stub3")
    _stub(w["bin"] / "python3")
    (w["bin"] / "python").symlink_to(_HOST)
    r = _run(w)
    assert r.returncode == 0, f"the gate exits 0, got {r.returncode}: {r.stderr!r}"
    assert "FAILED" not in _log(w), f"no FAILED line when a python runs; log: {_log(w)!r}"
    assert _lab_filled(w) == _WANT, f"the lab is written by the python that runs; got {_lab_filled(w)}"


def test_the_venv_interpreter_is_tried_first():
    w = _world("venv")
    for name in ("python3", "python", "py"):
        _stub(w["bin"] / name)
    w["venv"] = w["d"] / "venv"
    marker = w["d"] / "venv-ran"
    _wrapper(w["venv"] / "bin" / "python3", marker)
    r = _run(w)
    assert r.returncode == 0, f"the gate exits 0, got {r.returncode}: {r.stderr!r}"
    assert marker.exists(), "the gate ran CAIRN_VENV/bin/python3 (its marker is absent)"
    assert "FAILED" not in _log(w), f"no FAILED line; log: {_log(w)!r}"
    assert _lab_filled(w) == _WANT, f"the venv's python wrote the lab; got {_lab_filled(w)}"


def test_no_python_at_all_is_logged_and_never_blocks():
    w = _world("none")
    for name in ("python3", "python", "py"):
        _stub(w["bin"] / name)
    r = _run(w)
    assert r.returncode == 0, f"no python never blocks the caller (exit 0), got {r.returncode}"
    log = _log(w)
    assert "FAILED: no Python 3 interpreter found" in log, \
        f"the record names the missing interpreter, not a stub's noise; log: {log!r}"


def _main() -> int:
    checks = [
        test_a_stub_python3_is_skipped_for_a_python_that_runs,
        test_the_venv_interpreter_is_tried_first,
        test_no_python_at_all_is_logged_and_never_blocks,
    ]
    failed = 0
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {check.__name__}: {e}")
    if failed:
        print(f"red — {failed} of {len(checks)} teeth failed")
        return 1
    print("green — the recompile gate finds a python that runs (venv first, then a PATH name "
          "that really is Python 3), runs it from the repo root, and records the case where "
          "there is none without blocking its caller.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
