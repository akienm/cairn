#!/usr/bin/env python3
"""A network seal the tester cannot build refuses the run — it never lands a harness failure as RED.

WHAT THIS DEFENDS (ticket 67af8b743a63). Inside `cairn test --exec` the instance seal is
inherited (c54d744aa9ac) but the network is OPEN: measured 2026-10-06, a connect to
1.1.1.1:443 succeeded with CAIRN_TESTER_INSTANCE_SEALED=1 and CAIRN_TESTER_SEALED unset. A
netns seal asked for there cannot be cut (this host refuses a namespace inside a namespace),
and NetnsIsolation.available() already says so. run_proof used to mint an `indeterminate`
seal and run the subject anyway; wrap() still emitted `bwrap --unshare-net`, the subject died
"bwrap: No permissions to create a new namespace", and `--seal` persisted that as the proof's
RED. The record said the proof failed when what failed was the harness (Law 7).

THE CLAIM, clause by clause of the ticket's falsifier:
  (1) run_proof(sink='validations', isolation='netns') under the nested markers raises the
      refusal — the subject never runs and no validation is written;
  (2) `bin/cairn test --seal` under the same markers exits non-zero, prints a REFUSED line,
      and leaves the proof's validation file untouched;
  (3) `bin/cairn test --hollow` under the same markers exits 2 instead of measuring a proof
      at netns — refusing up front, naming the seal, not crashing a proof into bwrap;
  (4) the tester charter's public_interface entry for `cairn test --exec` says what --exec
      measured as: instance-sealed, network open — so no consumer reads it as the full seal.

THE NESTED CONDITION IS TWO ENV MARKERS, NOT A REAL NESTED NAMESPACE. available() reads only
CAIRN_TESTER_INSTANCE_SEALED and CAIRN_TESTER_SEALED, so a child process carrying the first and
lacking the second is exactly the --exec shape. The fixture proof lives in a tmp directory, so
its validation (`<tmp>/.../validations/<stem>.json`) can never touch the live store, and it
writes a /tmp mark when it runs, so "the subject never ran" is a file that is absent.

Proof: exit 0 = green.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROOF_TIMEOUT_S = 1200

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

_CAIRN = _REPO_ROOT / "bin" / "cairn"
_INST = "CAIRN_TESTER_INSTANCE_SEALED"
_NET = "CAIRN_TESTER_SEALED"
# A ticket whose proof stands sealed under the netns, so the hollow measures it at netns.
_NETNS_SEALED_TICKET = "72a37498c601"

PROVES = {"67af8b743a63": {
    "1": "test_run_proof_refuses_before_the_subject_runs",
    "2": "test_cairn_test_seal_refuses_and_persists_nothing",
    "3": "test_the_hollow_exits_2_instead_of_measuring",
    "4": "test_the_charter_says_exec_leaves_the_network_open",
}}
_CHARTER = _REPO_ROOT / "cairn" / "devices" / "tester" / ("intention+" "why.json")


def _nested_env() -> dict:
    """The --exec shape: instance seal marked, network seal absent."""
    env = {k: v for k, v in os.environ.items() if k != _NET}
    env[_INST] = "1"
    env["PYTHONPATH"] = str(_REPO_ROOT)
    return env


class _Fixture:
    """A green fixture proof in a tmp component, and the mark it leaves when it runs."""

    def __enter__(self):
        self.root = Path(tempfile.mkdtemp(prefix="unbuildable_seal_proof_fixture_"))
        proofs = self.root / "fixture_component" / "proofs"
        proofs.mkdir(parents=True)
        self.mark = self.root / "the-fixture-subject-ran"
        self.proof = proofs / "test_fixture_green_for_unbuildable_seal.py"
        self.proof.write_text(
            "from pathlib import Path\n"
            f"Path({str(self.mark)!r}).write_text('ran')\n"
            "print('  PASS  test_fixture_green')\n")
        self.validation = self.root / "fixture_component" / "validations" / f"{self.proof.stem}.json"
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.root, ignore_errors=True)


def test_run_proof_refuses_before_the_subject_runs():
    code = r'''
import json, sys
from pathlib import Path
import cairn.devices.tester.device as d
try:
    rec = d.TesterDevice().run_proof(Path(sys.argv[1]), sink="validations", caller="unbuildable-seal fixture",
                                     timeout=60, isolation="netns",
                                     scratch_sweep={"skipped": "fixture: nothing to sweep"})
    print(json.dumps({"raised": None, "verdict": rec["verdict"], "seal": rec["evidence"].get("seal")}))
except Exception as e:
    print(json.dumps({"raised": type(e).__name__, "msg": str(e)}))
'''
    with _Fixture() as fx:
        r = subprocess.run([sys.executable, "-c", code, str(fx.proof)], capture_output=True, text=True,
                           timeout=180, cwd=str(_REPO_ROOT), env=_nested_env())
        assert r.returncode == 0 and r.stdout.strip(), f"could not drive run_proof: {r.stderr[-600:]}"
        got = json.loads(r.stdout.strip().splitlines()[-1])
        assert got["raised"] == "SealUnavailable", f"run_proof did not refuse the unbuildable seal: {got}"
        assert "cannot be built" in got["msg"] and "not run" in got["msg"], \
            f"the refusal must say the seal cannot be built and the proof was not run: {got['msg']!r}"
        assert not fx.mark.exists(), "the subject ran although its seal could not be built"
        assert not fx.validation.exists(), f"a validation landed for a run that was refused: {fx.validation}"


def test_cairn_test_seal_refuses_and_persists_nothing():
    with _Fixture() as fx:
        r = subprocess.run([str(_CAIRN), "test", "--seal", "--netns", str(fx.proof)], capture_output=True,
                           text=True, timeout=300, cwd=str(_REPO_ROOT), env=_nested_env())
        assert r.returncode != 0, f"cairn test --seal exited 0 over a refused seal: {r.stdout[-600:]}"
        assert "REFUSED" in r.stdout, f"no REFUSED line on the surface: {r.stdout[-600:]} {r.stderr[-300:]}"
        assert not fx.mark.exists(), "the subject ran although its seal could not be built"
        assert not fx.validation.exists(), f"cairn test --seal persisted a record for a refused run: {fx.validation}"


def test_the_hollow_exits_2_instead_of_measuring():
    r = subprocess.run([str(_CAIRN), "test", "--hollow", _NETNS_SEALED_TICKET], capture_output=True,
                       text=True, timeout=900, cwd=str(_REPO_ROOT), env=_nested_env())
    assert r.returncode == 2, (f"the hollow did not exit 2 under an unbuildable seal (exit {r.returncode}): "
                               f"{r.stdout[-400:]} {r.stderr[-400:]}")
    # THE EXIT 2 MUST BE THE REFUSAL, NOT THE CRASH. Measured 2026-10-06 at f5e53ec9: inside a
    # real --exec the hollow already exited 2, but only after running the proof, whose bwrap died
    # on the namespace and printed no tooth ("the proof never reached a check"); on a bare host
    # with the markers it measured at netns and exited 0. Either way it tried to measure.
    out = r.stdout + r.stderr
    assert "cannot be built" in out, f"the hollow did not refuse the unbuildable seal up front: {out[-600:]!r}"
    assert "No permissions to create a new namespace" not in out, \
        f"the hollow ran a proof into the namespace refusal instead of refusing first: {out[-600:]!r}"


def test_the_charter_says_exec_leaves_the_network_open():
    iface = json.loads(_CHARTER.read_text()).get("public_interface") or []
    entries = [e if isinstance(e, str) else json.dumps(e) for e in iface]
    exec_entries = [e for e in entries if "--exec" in e]
    assert exec_entries, f"the tester charter's public_interface names no --exec entry: {iface}"
    for e in exec_entries:
        low = e.lower()
        assert "instance" in low and "network open" in low, \
            f"the --exec entry does not say instance-sealed, network open: {e!r}"


def test_the_whole_falsifier_holds_end_to_end():
    test_run_proof_refuses_before_the_subject_runs()
    test_cairn_test_seal_refuses_and_persists_nothing()
    test_the_hollow_exits_2_instead_of_measuring()
    test_the_charter_says_exec_leaves_the_network_open()


def _main() -> int:
    checks = [
        test_run_proof_refuses_before_the_subject_runs,
        test_cairn_test_seal_refuses_and_persists_nothing,
        test_the_hollow_exits_2_instead_of_measuring,
        test_the_charter_says_exec_leaves_the_network_open,
        test_the_whole_falsifier_holds_end_to_end,
    ]
    # EVERY TOOTH PRINTS, red ones too, so a red names which clause fell.
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as e:  # noqa: BLE001 — a crash in a tooth is that tooth's red
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {type(e).__name__}: {e}")
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed")
        return 1
    print("green — a network seal the tester cannot build refuses the run and persists nothing")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
