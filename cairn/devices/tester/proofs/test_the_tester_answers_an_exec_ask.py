#!/usr/bin/env python3
"""Proof for ticket 21f9628872da: the tester answers an ``exec`` ask over the bus.

The verb is the bus face of the sealed exec (2c9eeab2da87): a box with no bubblewrap asks a box
that has it (86cccb7d30f7). The proof drives it through the device's ``declared_verbs`` -- the
public interface -- one tooth per falsifier clause.

  1. ``exec`` is declared, and an ask of a passing command replies exit 0 with the record's keys.
     Where the seal cannot be confirmed (Windows) the reply half reads UNRAN, never green.
  2. A failing command replies its own exit code and output tail, not a refusal (UNRAN likewise).
  3. A box whose seal cannot be confirmed replies the ``cairn test --exec: refused`` line in
     seal_refused, exit 2, and the command is not run (its marker is absent). Reads on every host:
     the seal is made unconfirmable by an environment with no bubblewrap and no inherited seal.
  4. An ask with no command, or a non-string one, is refused by name and nothing is run.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.devices.tester.device import TesterDevice  # noqa: E402
from cairn.devices.tester import isolation  # noqa: E402

PROVES = {"21f9628872da": {
    "1": "test_exec_is_declared_and_a_passing_ask_replies_the_record",
    "2": "test_a_failing_ask_replies_its_own_exit_and_tail",
    "3": "test_an_unconfirmed_seal_replies_the_refusal_and_runs_nothing",
    "4": "test_an_ask_with_no_command_is_refused_by_name",
}}

KEYS = {"command", "exit", "timed_out", "timeout_s", "seconds", "tail"}


def _ask(body: dict) -> dict:
    return TesterDevice().declared_verbs()["exec"]({"body": body, "sender": "proof"})


def _no_seal_env():
    """An environment where this host cannot confirm a seal: no bwrap on PATH, nothing inherited."""
    saved = dict(os.environ)
    os.environ.pop(isolation.INSTANCE_SEAL_MARKER, None)
    keep = [d for d in os.environ.get("PATH", "").split(os.pathsep)
            if d and not (Path(d) / "bwrap").exists() and not (Path(d) / "bwrap.exe").exists()]
    os.environ["PATH"] = os.pathsep.join([str(Path(sys.executable).parent), *keep])
    return saved


def _restore(saved: dict) -> None:
    os.environ.clear()
    os.environ.update(saved)


def test_exec_is_declared_and_a_passing_ask_replies_the_record():
    assert "exec" in TesterDevice().declared_verbs(), "the tester does not declare exec"
    rec = _ask({"command": "true", "timeout": 120}).get("record")
    assert rec is not None, "an exec ask replied no record"
    assert KEYS <= set(rec), f"the record lacks keys: {sorted(KEYS - set(rec))}"
    if rec.get("seal_refused"):
        raise AssertionError(f"UNRAN: this host cannot confirm a seal ({rec['seal_refused']})")
    assert rec["exit"] == 0, rec


def test_a_failing_ask_replies_its_own_exit_and_tail():
    rec = _ask({"command": "echo said-this; exit 3", "timeout": 120})["record"]
    if rec.get("seal_refused"):
        raise AssertionError(f"UNRAN: this host cannot confirm a seal ({rec['seal_refused']})")
    assert rec["exit"] == 3 and "said-this" in rec["tail"], rec


def test_an_unconfirmed_seal_replies_the_refusal_and_runs_nothing():
    with tempfile.TemporaryDirectory(prefix="exec-ask-proof-") as d:
        marker = Path(d) / "ran"
        saved = _no_seal_env()
        try:
            rec = _ask({"command": f"touch '{marker.as_posix()}'", "timeout": 60})["record"]
        finally:
            _restore(saved)
        assert rec["exit"] == 2, rec
        assert str(rec.get("seal_refused", "")).startswith("cairn test --exec: refused"), rec
        assert not marker.exists(), "the command ran although the seal was not confirmed"


def test_an_ask_with_no_command_is_refused_by_name():
    for body in ({}, {"command": ""}, {"command": 7}, {"command": ["true"]}):
        r = _ask(body)
        assert "refused" in r and "command" in r["refused"] and "record" not in r, (body, r)


TEETH = [test_exec_is_declared_and_a_passing_ask_replies_the_record,
         test_a_failing_ask_replies_its_own_exit_and_tail,
         test_an_unconfirmed_seal_replies_the_refusal_and_runs_nothing,
         test_an_ask_with_no_command_is_refused_by_name]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}", flush=True)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {t.__name__}: {type(e).__name__}: {e}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
