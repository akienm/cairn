"""Proof for ticket 64ae0df3f1f3 — a run whose every failing tooth reads UNRAN writes no red seal.

Measured 2026-11-20 on akiendell: bin/validations/test_cairn_runs_from_cmd_with_no_bash.json carried a
green Windows seal (source_fingerprint 452ab81c239e). A Linux landing edited bin/cairn.py, inside that
proof's closure, and the Linux reseal wrote RED over the seal (d1068249ba20, 2 teeth red) because two teeth
read UNRAN (cairn.cmd is Windows-only). Outline 9.4.8.1: a tooth this host cannot run reads not-run, never red.
Two doors write seals: reseal() and run_proof(sink="validations") (cairn test --seal).

Each tooth runs the REAL tester over a fixture proof under a scratch root, through BOTH doors, and reads the
validations file's bytes. It runs on any host: the UNRAN is printed by the fixture, not caused by the host.

  1. every failing tooth reads UNRAN: the validations file is byte-identical after the run, through both doors.
  2. one failing tooth is not UNRAN: red is written over the green seal, through both doors.
  3. a run that goes green still writes green, through both doors.

    python3 cairn/devices/tester/proofs/test_a_run_that_cannot_run_a_tooth_writes_no_red_seal.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"64ae0df3f1f3": {
    "1": "test_an_all_unran_run_writes_no_red_seal",
    "2": "test_a_real_fail_still_writes_red",
    "3": "test_a_green_run_still_writes_green",
}}

_UNRAN = ("print('  ok   tooth_a')\n"
          "print('  FAIL tooth_b: AssertionError: UNRAN: cairn.cmd is Windows-only')\n"
          "raise SystemExit(1)\n")
_REAL = ("print('  ok   tooth_a')\n"
         "print('  FAIL tooth_b: AssertionError: the verb exited 0')\n"
         "raise SystemExit(1)\n")
_MIXED = ("print('  FAIL tooth_a: AssertionError: the verb exited 0')\n"
          "print('  FAIL tooth_b: AssertionError: UNRAN: cairn.cmd is Windows-only')\n"
          "raise SystemExit(1)\n")
_GREEN = "print('  ok   tooth_a')\nprint('  ok   tooth_b')\n"


class _Raiser:
    def raise_trouble(self, identity, *, why, detail=None):
        pass

    def clear_trouble(self, identity, *, by, what_changed):
        pass


def _fixture(body: str) -> tuple[Path, Path, Path]:
    """A scratch component holding a proof, a green seal on it, and a moved closure.

    Returns (proof, validations file, the file whose edit expires the seal)."""
    from cairn.tools.scratch.scratch import scratch_dir
    from cairn.tools.validation_store.validation_store import (
        persist_validation, source_fingerprint, validations_path_for)
    root = scratch_dir("testing-64ae0df3f1f3-") / "widget"
    (root / "proofs").mkdir(parents=True)
    code = root / "code.py"
    code.write_text("VALUE = 1\n", encoding="utf-8")
    proof = root / "proofs" / "test_hostbound.py"
    proof.write_text(_GREEN, encoding="utf-8")
    persist_validation({
        "claim": f"{proof.name} passes", "caller": "64ae0df3f1f3 fixture (the Windows seal)",
        "date": datetime.now().isoformat(timespec="seconds"),
        "method": "ran the proof as a subprocess and read its exit code", "verdict": "green",
        "evidence": {"source_fingerprint": source_fingerprint(str(proof)), "returncode": 0,
                     "teeth_green": ["tooth_a", "tooth_b"], "teeth_red": []},
        "falsifier": "the proof exits non-zero, or the fingerprint of the code it proves moves",
        "horizon": "valid until the proof file or the code it proves changes",
    }, proof_path=str(proof))
    code.write_text("VALUE = 2\n", encoding="utf-8")        # the closure moves: the seal is stale
    proof.write_text(body, encoding="utf-8")
    return proof, Path(validations_path_for(str(proof))), code


def _run_proof_door(proof: Path) -> None:
    from cairn.devices.tester.device import TesterDevice
    TesterDevice().run_proof(proof, sink="validations", caller="64ae0df3f1f3 clause", isolation="none",
                             scratch_sweep={"dropped": 0, "tables": []})


def _reseal_door(proof: Path) -> dict:
    from cairn.devices.tester.device import TesterDevice
    from cairn.devices.tester.reseal import reseal
    return reseal(proof, tester=TesterDevice(), raiser=_Raiser())


def _verdict(val: Path) -> str:
    return json.loads(val.read_text(encoding="utf-8"))[-1]["verdict"]


def test_an_all_unran_run_writes_no_red_seal():
    for door in ("run_proof", "reseal"):
        proof, val, _ = _fixture(_UNRAN)
        before = val.read_bytes()
        out = _run_proof_door(proof) if door == "run_proof" else _reseal_door(proof)
        assert val.read_bytes() == before, (
            f"{door}: a run whose only failing tooth reads UNRAN rewrote the seal: {_verdict(val)}")
        if door == "reseal":
            assert out.get("outcome") == "not-run", f"reseal reported {out.get('outcome')!r}, not 'not-run'"
            assert "tooth_b" in json.dumps(out), "the result does not name the tooth that was not run"


def test_a_real_fail_still_writes_red():
    for door in ("run_proof", "reseal"):
        for body in (_REAL, _MIXED):
            proof, val, _ = _fixture(body)
            _run_proof_door(proof) if door == "run_proof" else _reseal_door(proof)
            assert _verdict(val) == "red", f"{door}: a real FAIL did not write red"


def test_a_green_run_still_writes_green():
    for door in ("run_proof", "reseal"):
        proof, val, _ = _fixture(_GREEN)
        before = val.read_bytes()
        _run_proof_door(proof) if door == "run_proof" else _reseal_door(proof)
        assert _verdict(val) == "green", f"{door}: a green run did not write green"
        assert val.read_bytes() != before, f"{door}: a green run wrote nothing over a stale seal"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
