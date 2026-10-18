"""A timeout is not a red (ticket 3dfceaa272ec).

A proof that outlives its budget measured the budget, not the proof. Until this ticket the
TimeoutExpired arm of ``run_proof`` set ``verdict = RED`` and the seal path persisted it, so a
record of truth carried a red nobody measured — the same lie as a hollow green, pointed the
other way (Law 7). The reseal door already declined to write one (its own TIMEOUT rung); the
hand seal did not.

1. a run over the budget returns the third outcome, ``timeout``, and writes no validation:
   ``persist_validation`` is never called, so the standing seal stays what it was;
2. the CLI prints that proof in its own TIMEOUT column, naming the budget it exceeded;
3. the closing counts carry a ``timeout`` bucket distinct from ``red``;
4. the process exit code still refuses to read as success.

Guards: a proof that exits 1 still seals red (a red still seals red), and the reseal door reads
the runner's outcome rather than the wording of its stderr tail.

The fixtures sleep 30 s under a 1 s budget, in a scratch tree. The store's door is replaced by
a recorder for the device-level teeth, so nothing lands on disk either way. Every tooth imports
the tester INSIDE its body, so a reverted device.py, cli.py or reseal.py reds a tooth instead of
breaking this file's import.
"""
from __future__ import annotations

import contextlib
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"3dfceaa272ec": {
    "1": "test_a_run_over_its_budget_is_a_timeout_and_writes_nothing",
    "2": "test_the_cli_prints_a_timeout_in_its_own_column_naming_the_budget",
    "3": "test_the_closing_counts_carry_timeout_distinct_from_red",
    "4": "test_a_timeout_still_fails_the_run",
    "a red still seals red": "test_a_proof_that_exits_one_still_seals_red",
    "the reseal door reads the outcome": "test_the_reseal_door_reads_the_outcome_not_the_wording",
}}

_SLEEPS = 'import time\ntime.sleep(30)\nprint("ok   test_never_reached")\n'
_EXITS_ONE = 'print("FAIL test_fixture_fails")\nraise SystemExit(1)\n'


def _fixture(prefix: str, body: str, name: str = "test_sleeps.py") -> Path:
    root = scratch_dir(prefix) / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    proof = root / "proofs" / name
    proof.write_text(body)
    return proof


@contextlib.contextmanager
def _recording_store():
    """persist_validation records instead of writing; read_validations answers nothing."""
    import cairn.tools.validation_store.validation_store as vs
    persisted: list = []
    saved = (vs.read_validations, vs.persist_validation)
    vs.read_validations = lambda proof_path=None, **kw: []
    vs.persist_validation = lambda record, **kw: persisted.append(record) or "recorded"
    try:
        yield persisted
    finally:
        vs.read_validations, vs.persist_validation = saved


def _seal(proof: Path, timeout: int) -> tuple[dict, list]:
    from cairn.devices.tester.device import TesterDevice
    with _recording_store() as persisted:
        record = TesterDevice().run_proof(proof, sink="validations", caller="proof-fixture",
                                          timeout=timeout, isolation="none",
                                          scratch_sweep={"skipped": "proof fixture"})
    return record, persisted


_CLI: dict = {}


def _cli_over_a_sleeper() -> subprocess.CompletedProcess:
    """One diagnostic CLI run over the sleeping fixture, shared by teeth 2-4."""
    if "done" not in _CLI:
        proof = _fixture("cairn-timeout-cli-", _SLEEPS)
        _CLI["proof"] = proof
        _CLI["done"] = subprocess.run(
            [sys.executable, "-m", "cairn.devices.tester.cli", "--timeout", "1", str(proof)],
            cwd=_REPO_ROOT, capture_output=True, text=True, timeout=300,
            env={**os.environ, "PYTHONPATH": str(_REPO_ROOT)})
    return _CLI["done"]


def test_a_run_over_its_budget_is_a_timeout_and_writes_nothing():
    record, persisted = _seal(_fixture("cairn-timeout-1-", _SLEEPS), timeout=1)
    ev = record["evidence"]
    assert record["verdict"] == "timeout", (record["verdict"], ev.get("stderr_tail"))
    assert ev["returncode"] is None and ev.get("timeout_s") == 1, ev
    assert persisted == [], f"a timed-out run persisted {len(persisted)} record(s): " \
                            f"{[r.get('verdict') for r in persisted]}"


def test_the_cli_prints_a_timeout_in_its_own_column_naming_the_budget():
    done = _cli_over_a_sleeper()
    lines = [l for l in done.stdout.splitlines() if l.startswith("  TIMEOUT ")]
    assert len(lines) == 1, done.stdout[-1500:]
    assert "test_sleeps.py" in lines[0] and "1s budget" in lines[0], lines[0]
    assert not any(l.startswith("  RED ") for l in done.stdout.splitlines()), done.stdout[-1500:]


def test_the_closing_counts_carry_timeout_distinct_from_red():
    done = _cli_over_a_sleeper()
    closing = [l for l in done.stdout.splitlines() if l.startswith("1 proof ·")]
    assert closing, done.stdout[-1500:]
    assert "1 timeout" in closing[0] and "0 red" in closing[0] and "0 green" in closing[0], closing[0]


def test_a_timeout_still_fails_the_run():
    done = _cli_over_a_sleeper()
    assert done.returncode != 0, (done.returncode, done.stdout[-800:])


def test_a_proof_that_exits_one_still_seals_red():
    record, persisted = _seal(_fixture("cairn-timeout-c-", _EXITS_ONE, "test_exits.py"), timeout=30)
    assert record["verdict"] == "red", record["evidence"].get("stderr_tail")
    assert [r.get("verdict") for r in persisted] == ["red"], persisted


def test_the_reseal_door_reads_the_outcome_not_the_wording():
    """A TIMEOUT whose tail does not say 'timed out after' is still the door's timeout rung."""
    from cairn.devices.tester import reseal as door
    from cairn.devices.tester.device import TesterDevice
    proof = _fixture("cairn-timeout-r-", _SLEEPS)

    class _Killed:
        runs = 0

        def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                      scratch_sweep=None):
            self.runs += 1
            rec = TesterDevice().run_proof(proof_path, sink="none", caller="proof-fixture",
                                           timeout=1, isolation="none")
            rec["evidence"] = dict(rec["evidence"], stderr_tail="killed at its budget")
            return rec

    class _Raiser:
        raised: list = []
        cleared: list = []

        def raise_trouble(self, identity, **kw):
            self.raised.append(identity)

        def clear_trouble(self, identity, **kw):
            self.cleared.append(identity)

    with _recording_store() as persisted:
        out = door.reseal(proof, tester=_Killed(), raiser=_Raiser(), timeout=1)
    assert out.get("outcome") == "timeout", out
    assert persisted == [], [r.get("verdict") for r in persisted]


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
