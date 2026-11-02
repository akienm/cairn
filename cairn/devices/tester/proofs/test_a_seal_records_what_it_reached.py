"""Proof: a seal records the components its run reached, and a meta-proof's seal covers the
proof it runs.

Ticket 734b22d09f2e, child of 50e0581737e8 (a seal that reached another component turns yellow
when that component's seals move). Only the tester sees the run, so the recording is the
tester's (RULE 1): a ``sitecustomize`` in ``cairn/devices/tester/reach/`` rides the subject's
``PYTHONPATH``, every python process the run starts logs the cairn files it loaded, and the
seal maps them to components in ``evidence.reached = {dir: seal_digest(dir)}``.

Five teeth, one per falsifier clause. Teeth 1, 2, 3 and 5 seal committed fixture proofs under
``proofs/fixtures/`` through the real tester (``TesterDevice().run_proof``); tooth 4 runs a
child python over a scratch ``sitecustomize`` that the reach one shadows.

  1. A fixture importing cairn.tools.validation_store carries that dir, valued at its digest.
  2. A fixture whose subprocess runs ``python -m`` on system_word carries cairn/tools/system_word.
  3. A fixture that reaches nothing outside its own component carries reached == {}.
  4. The shadowed sitecustomize still runs, and the reach one still logs.
  5. A meta-proof that runs green_proof.py as a subprocess carries it in fingerprint_closure.

    python3 cairn/devices/tester/proofs/test_a_seal_records_what_it_reached.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "734b22d09f2e": {
        "1": "test_an_imported_component_is_reached",
        "2": "test_a_python_m_subprocess_is_reached",
        "3": "test_a_proof_that_reaches_nothing_records_an_empty_map",
        "4": "test_the_shadowed_sitecustomize_still_runs",
        "5": "test_a_meta_proof_seal_covers_the_proof_it_runs",
    },
}

_FIXTURES = _REPO_ROOT / "cairn" / "devices" / "tester" / "proofs" / "fixtures"
_REACH_DIR = _REPO_ROOT / "cairn" / "devices" / "tester" / "reach"


def _seal(fixture: str) -> dict:
    from cairn.devices.tester.device import TesterDevice
    record = TesterDevice().run_proof(_FIXTURES / fixture, sink="none", isolation="none")
    assert record["verdict"] == "green", (fixture, record["evidence"].get("stderr_tail"))
    return record["evidence"]


def _reached(evidence: dict) -> dict:
    reached = evidence.get("reached")
    assert isinstance(reached, dict), f"no evidence.reached on the seal: {sorted(evidence)}"
    return reached


def test_an_imported_component_is_reached():
    from cairn.tools.validation_store.validation_store import seal_digest
    reached = _reached(_seal("reach_imports_a_tool.py"))
    key = "cairn/tools/validation_store"
    assert key in reached, reached
    assert reached[key] == seal_digest(str(_REPO_ROOT / key)), (reached[key], key)


def test_a_python_m_subprocess_is_reached():
    reached = _reached(_seal("reach_runs_a_module.py"))
    assert "cairn/tools/system_word" in reached, reached


def test_a_proof_that_reaches_nothing_records_an_empty_map():
    reached = _reached(_seal("green_proof.py"))
    assert reached == {}, reached


def test_the_shadowed_sitecustomize_still_runs():
    assert (_REACH_DIR / "sitecustomize.py").is_file(), f"no reach sitecustomize at {_REACH_DIR}"
    shadowed = scratch_dir("reach_shadowed_sitecustomize_")
    (shadowed / "sitecustomize.py").write_text(
        "import os\nos.environ['CAIRN_REACH_PROOF_MARK'] = 'chained'\n", encoding="utf-8")
    log = shadowed / "reached.jsonl"
    env = {**os.environ,
           "PYTHONPATH": os.pathsep.join([str(_REACH_DIR), str(shadowed), str(_REPO_ROOT)]),
           "CAIRN_TESTER_REACH_LOG": str(log)}
    proc = subprocess.run(
        [sys.executable, "-c",
         "import os, cairn.tools.system_word.system_word; "
         "print(os.environ.get('CAIRN_REACH_PROOF_MARK', ''))"],
        capture_output=True, text=True, env=env, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "chained", f"the shadowed sitecustomize did not run: {proc.stdout!r}"
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert lines and any(f.endswith("system_word.py") for ln in lines for f in ln["files"]), lines


def test_a_meta_proof_seal_covers_the_proof_it_runs():
    evidence = _seal("reach_runs_a_proof.py")
    closure = evidence.get("fingerprint_closure")
    assert isinstance(closure, list), evidence.get("fingerprint_closure_absent")
    assert "cairn/devices/tester/proofs/fixtures/green_proof.py" in closure, closure


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
