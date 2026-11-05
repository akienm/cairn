"""Proof for ticket 0d38d0f5a4e3: the verdict door reads a ! head and refuses an unrunnable
instrument before it runs any.

Measured 2026-10-30 (idea 8d19bdddfde4, on ticket 284798998ab0's PROVED crossing): an instrument
'! grep ...' was refused as carrying no command, and the refusal came only after the slow
instruments listed before it had already run (about 85 minutes of reading thrown away).

  1. test_a_bang_head_is_a_command: extract_command reads '! grep -q x README.md' as a command.
  2. test_an_unrunnable_instrument_is_refused_before_any_run: an artifact whose first instrument
     runs and whose last does not makes zero runner calls, and both readings come back.
  3. test_an_all_runnable_artifact_runs_each_once: with every command extracted, the runner is
     called once per entry, in order.
  4. test_the_standing_verdict_proofs_stay_green: the six other verdict proofs each exit 0.

    python3 cairn/devices/codemother/machines/verdict/proofs/test_the_verdict_door_refuses_before_it_runs.py
"""
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"0d38d0f5a4e3": {
    "1": "test_a_bang_head_is_a_command",
    "2": "test_an_unrunnable_instrument_is_refused_before_any_run",
    "3": "test_an_all_runnable_artifact_runs_each_once",
    "4": "test_the_standing_verdict_proofs_stay_green",
}}

_SIBLINGS = (
    "test_a_live_logs_miss_names_its_cause.py",
    "test_an_instrument_runs_under_the_seal.py",
    "test_chart_verdict.py",
    "test_falsifier_verdict.py",
    "test_the_instrument_is_run.py",
    "test_verdict_probes_report_to_the_watch.py",
)


def _verdict():
    """Bound at call time: the hollow reading takes the build away and the teeth read red."""
    return importlib.import_module("cairn.devices.codemother.machines.verdict.verdict")


class _CountingRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, command, *, timeout_s=None, cwd=None):
        self.calls.append(command)
        return {"exit": 0, "stdout": "", "stderr": "", "timed_out": False}


def test_a_bang_head_is_a_command() -> None:
    cmd = "! grep -q x README.md"
    got = _verdict().extract_command(cmd, str(ROOT))
    assert got == cmd, f"a leading ! read as no command: {got!r}"
    got = _verdict().extract_command("run `! grep -q x README.md` and expect 0", str(ROOT))
    assert got == cmd, f"a backticked ! command not extracted: {got!r}"
    print("ok test_a_bang_head_is_a_command")


def test_an_unrunnable_instrument_is_refused_before_any_run() -> None:
    artifact = {"verdicts": [
        {"claim": "first", "instrument": "true", "outcome": "pass"},
        {"claim": "last", "instrument": "the frobnicator reads green", "outcome": "pass"},
    ]}
    runner = _CountingRunner()
    readings = _verdict().observe_instruments(artifact, str(ROOT), runner=runner)
    assert runner.calls == [], f"ran {runner.calls!r} before refusing an unrunnable instrument"
    assert [r["claim"] for r in readings] == ["first", "last"], readings
    assert [r["runnable"] for r in readings] == [True, False], readings
    refusal = _verdict()._observed_entries(readings)
    assert len(refusal) == 1 and "last" in str(refusal[0]), refusal
    print("ok test_an_unrunnable_instrument_is_refused_before_any_run")


def test_an_all_runnable_artifact_runs_each_once() -> None:
    artifact = {"verdicts": [
        {"claim": "a", "instrument": "true", "outcome": "pass"},
        {"claim": "b", "instrument": "! false", "outcome": "pass"},
    ]}
    runner = _CountingRunner()
    readings = _verdict().observe_instruments(artifact, str(ROOT), runner=runner)
    assert runner.calls == ["true", "! false"], runner.calls
    assert all(r["runnable"] and "run" in r for r in readings), readings
    print("ok test_an_all_runnable_artifact_runs_each_once")


def test_the_standing_verdict_proofs_stay_green() -> None:
    here = Path(__file__).resolve().parent
    red = []
    for name in _SIBLINGS:
        done = subprocess.run([sys.executable, str(here / name)], cwd=str(ROOT),
                              capture_output=True, text=True, timeout=300)
        if done.returncode != 0:
            red.append(f"{name} exit {done.returncode}: {(done.stdout + done.stderr)[-600:]}")
    assert not red, "standing verdict proofs red:\n" + "\n".join(red)
    print("ok test_the_standing_verdict_proofs_stay_green")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
