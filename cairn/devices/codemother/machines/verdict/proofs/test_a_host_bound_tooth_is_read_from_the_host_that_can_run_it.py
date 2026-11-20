"""Proof for ticket 50ac45cde4dd — a host-bound tooth's verdict is read from the host that can run it.

Measured 2026-11-20 on akiendell (Windows): sail.py verdict 380d524e6e9c was refused, because its
criterion instrument (`bin/cairn test bin/proofs/test_cairn_runs_from_cmd_with_no_bash.py`) cannot run
under a seal there, and on the sealing host (Linux) teeth 1 and 3 of that proof read UNRAN (cairn.cmd is
Windows-only). The proof's Windows seal was green 3 of 3 on the same tree.

The verdict machine is read on Linux, so this proof runs on Linux with a FIXTURE Windows seal in a scratch
component (no live seal, no fork): the observation is the reading the sealing host would have taken.

  1. a run whose only failing teeth read UNRAN, with a green seal on file for the same tree fingerprint
     that names every one of them green and none red, leaves the verdict standing.
  2. a tooth not-run on this host and with no matching green seal anywhere (no seal, or a seal taken on
     other bytes) refuses the verdict, and the refusal says the tooth was not run.
  3. a red reading refuses: a failing tooth that is not UNRAN, or a seal with a red tooth, both refuse
     even when a green seal is on file.

    python3 cairn/devices/codemother/machines/verdict/proofs/test_a_host_bound_tooth_is_read_from_the_host_that_can_run_it.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.devices.codemother.machines.verdict import verdict  # noqa: E402
from cairn.tools.chain.grammar import lacks_of  # noqa: E402
from cairn.tools.validation_store.validation_store import source_fingerprint  # noqa: E402

PROOF_TIMEOUT_S = 240

PROVES = {"50ac45cde4dd": {
    "1": "tooth_1_a_tooth_green_on_the_host_that_can_run_it_stands",
    "2": "tooth_2_a_tooth_not_run_anywhere_refuses",
    "3": "tooth_3_a_red_from_either_host_refuses",
}}

_TEETH = ["tooth_1_a", "tooth_2_b", "tooth_3_c"]


def _component(tmp: Path, *, seal: dict | None, stale: bool = False) -> Path:
    """A scratch component: proofs/test_fx.py and, when asked, validations/test_fx.json."""
    (tmp / "proofs").mkdir()
    proof = tmp / "proofs" / "test_fx.py"
    proof.write_text("PROVES = {}\n", encoding="utf-8")
    if seal is not None:
        fp = source_fingerprint(str(proof))
        seal = dict(seal)
        seal["evidence"] = dict(seal["evidence"], source_fingerprint=("0" * 64) if stale else fp)
        (tmp / "validations").mkdir()
        (tmp / "validations" / "test_fx.json").write_text(json.dumps([seal]), encoding="utf-8")
    return proof


def _windows_seal(green=_TEETH, red=()) -> dict:
    return {"claim": "proof test_fx.py passes", "caller": "cairn test", "verdict": "green" if not red else "red",
            "evidence": {"teeth_green": list(green), "teeth_red": list(red)}}


def _reading(proof: Path, tail: str, fail_lines=None) -> dict:
    command = f"bin/cairn test {proof.as_posix()}"
    return {"claim": "every tooth passes", "instrument": command, "outcome": "pass", "expect_exit": 0,
            "runnable": True,
            "run": {"command": command, "exit": 1, "timed_out": False, "timeout_s": 240, "seconds": 1.0,
                    "tail": tail,
                    "fail_lines": fail_lines if fail_lines is not None
                    else [ln for ln in tail.splitlines() if ln.strip().startswith("FAIL")]}}


def _lacks(proof: Path, tail: str, fail_lines=None) -> list:
    return lacks_of(verdict._observed_entries([_reading(proof, tail, fail_lines)]))


_UNRAN_TAIL = ("  FAIL tooth_1_a: AssertionError: UNRAN: cairn.cmd is Windows-only\n"
               "  ok   tooth_2_b\n"
               "  FAIL tooth_3_c: AssertionError: UNRAN: cairn.cmd is Windows-only\n")


def tooth_1_a_tooth_green_on_the_host_that_can_run_it_stands() -> None:
    with tempfile.TemporaryDirectory(prefix="hostbound50-") as t:
        proof = _component(Path(t), seal=_windows_seal())
        lacks = _lacks(proof, _UNRAN_TAIL)
        assert not lacks, f"the verdict was refused though a green seal covers every UNRAN tooth: {lacks}"


def tooth_2_a_tooth_not_run_anywhere_refuses() -> None:
    with tempfile.TemporaryDirectory(prefix="hostbound50-") as t:
        proof = _component(Path(t), seal=None)
        lacks = _lacks(proof, _UNRAN_TAIL)
        assert lacks, "a tooth not run on any host stood"
    with tempfile.TemporaryDirectory(prefix="hostbound50-") as t:
        proof = _component(Path(t), seal=_windows_seal(), stale=True)
        lacks = _lacks(proof, _UNRAN_TAIL)
        assert lacks, "a seal taken on other bytes was accepted for these bytes"
    with tempfile.TemporaryDirectory(prefix="hostbound50-") as t:
        proof = _component(Path(t), seal=_windows_seal(green=["tooth_2_b"]))
        lacks = _lacks(proof, _UNRAN_TAIL)
        assert lacks, "a seal that does not name the UNRAN teeth green was accepted"


def tooth_3_a_red_from_either_host_refuses() -> None:
    with tempfile.TemporaryDirectory(prefix="hostbound50-") as t:
        proof = _component(Path(t), seal=_windows_seal())
        lacks = _lacks(proof, _UNRAN_TAIL + "  FAIL tooth_2_b: AssertionError: the verb exited 0\n")
        assert lacks, "a red tooth on this host stood beside a green seal"
    with tempfile.TemporaryDirectory(prefix="hostbound50-") as t:
        proof = _component(Path(t), seal=_windows_seal(green=["tooth_1_a", "tooth_3_c"], red=["tooth_2_b"]))
        lacks = _lacks(proof, _UNRAN_TAIL)
        assert lacks, "a seal with a red tooth was accepted"
    # A RED PUSHED OUT OF THE 2000-CHAR TAIL: the tail shows only UNRAN teeth, the full output had a red.
    with tempfile.TemporaryDirectory(prefix="hostbound50-") as t:
        proof = _component(Path(t), seal=_windows_seal())
        full = ["  FAIL tooth_2_b: AssertionError: the verb exited 0"] + _UNRAN_TAIL.splitlines()
        lacks = _lacks(proof, _UNRAN_TAIL, fail_lines=full)
        assert lacks, "a red cut off the tail stood beside a green seal"
    # NO FULL-OUTPUT RECORD AT ALL: the reading cannot rule a red out, so it does not stand.
    with tempfile.TemporaryDirectory(prefix="hostbound50-") as t:
        proof = _component(Path(t), seal=_windows_seal())
        reading = _reading(proof, _UNRAN_TAIL)
        del reading["run"]["fail_lines"]
        assert lacks_of(verdict._observed_entries([reading])), "a reading with no full-output record stood"


if __name__ == "__main__":
    fails = 0
    for fn in (tooth_1_a_tooth_green_on_the_host_that_can_run_it_stands,
               tooth_2_a_tooth_not_run_anywhere_refuses, tooth_3_a_red_from_either_host_refuses):
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print(f"  FAIL {fn.__name__}: {type(exc).__name__}: {exc}")
    sys.exit(1 if fails else 0)
