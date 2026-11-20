"""Proof for ticket 21f9628872da — the tester answers an `exec` ask over the bus.

Measured 2026-11-19: TesterDevice.declared_verbs returns run, notices and notice-seen. `run` takes a
proof path at isolation none; the seal-grade command run (run_exec, 2c9eeab2da87) is CLI only, so a
box without bubblewrap has no verb to ask a sealer for an instrument run (outline 9.4.8.1.2: the
instrument is the literal command the sealer runs).

RED-FIRST. The verb is driven through ``declared_verbs()`` with an envelope ``{"body": {command,
timeout}}`` and answers ``{"record": {command, exit, timed_out, timeout_s, seconds, tail,
seal_refused?}}`` (the shape verdict.run_instrument records) or ``{"refused": why}``. The record key
mirrors ``run``; the build may rename it and then renames it here.

1. `exec` is listed in the verbs; a passing command answers exit 0 with the record's keys. The
   sealed run itself needs a confirmed seal, so on a box that cannot build one that half reads a
   named skip (never a pass) and the listing half still stands;
2. a failing command answers that command's own exit and its output tail, not a refusal (same skip);
3. when the seal cannot be confirmed (the device's seal probes are stubbed unconfirmed, so this runs
   on every box) the answer is exit 2 with the `cairn test --exec: refused` line in seal_refused,
   and the command did not run (its marker is absent);
4. no command, or a non-string one, is refused by name and nothing runs.

    bin/cairn test cairn/devices/tester/proofs/test_the_tester_answers_an_exec_ask.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"21f9628872da": {
    "1": "test_exec_is_a_verb_and_a_passing_command_answers_exit_0",
    "2": "test_a_failing_command_answers_its_own_exit",
    "3": "test_an_unconfirmed_seal_refuses_and_runs_nothing",
    "4": "test_a_missing_command_is_refused_by_name"}}

KEYS = {"command", "exit", "timed_out", "timeout_s", "seconds", "tail"}


def _device():
    from cairn.devices.tester import device
    return device, device.TesterDevice()


def _ask(command, timeout=30):
    device, d = _device()
    verbs = d.declared_verbs()
    assert "exec" in verbs, "the tester answers no `exec` verb: %s" % sorted(verbs)
    return verbs["exec"]({"body": {"command": command, "timeout": timeout}})


def _seal_confirmable() -> bool:
    device, _d = _device()
    if device.inside_an_instance_seal():
        return True
    available, _why = device.bwrap_available()
    return bool(available)


def test_exec_is_a_verb_and_a_passing_command_answers_exit_0():
    reply = _ask("true")
    if not _seal_confirmable():
        print("  SKIP-HALF  the sealed run needs a confirmed seal; this box cannot build one")
        return
    record = reply.get("record") or {}
    assert KEYS <= set(record), "the record lacks keys %s: %r" % (sorted(KEYS - set(record)), reply)
    assert record["exit"] == 0, "a passing command answers exit 0: %r" % reply


def test_a_failing_command_answers_its_own_exit():
    reply = _ask("echo boom; exit 3")
    if not _seal_confirmable():
        print("  SKIP-HALF  the sealed run needs a confirmed seal; this box cannot build one")
        return
    record = reply.get("record") or {}
    assert record.get("exit") == 3 and "boom" in (record.get("tail") or ""), \
        "a failing command answers its own exit and output tail, not a refusal: %r" % reply
    assert "seal_refused" not in record, "a real exit is not a seal refusal: %r" % reply


def test_an_unconfirmed_seal_refuses_and_runs_nothing():
    device, d = _device()
    marker = Path(scratch_dir("exec-ask-proof-")) / "ran"
    saved = (device.inside_an_instance_seal, device.bwrap_available)
    device.inside_an_instance_seal = lambda: False
    device.bwrap_available = lambda: (False, "bubblewrap (bwrap) is not installed")
    try:
        reply = _ask("touch %s" % marker.as_posix())
    finally:
        device.inside_an_instance_seal, device.bwrap_available = saved
    record = reply.get("record") or {}
    assert record.get("exit") == 2, "an unconfirmed seal answers exit 2: %r" % reply
    assert str(record.get("seal_refused", "")).startswith("cairn test --exec: refused"), \
        "the refusal line rides seal_refused: %r" % reply
    assert not marker.exists(), "the command ran although the seal was unconfirmed"


def test_a_missing_command_is_refused_by_name():
    for bad in (None, "", 7):
        reply = _ask(bad)
        assert reply.get("refused") and "command" in str(reply["refused"]), \
            "no usable command is refused naming it (%r): %r" % (bad, reply)


def _main() -> int:
    checks = [test_exec_is_a_verb_and_a_passing_command_answers_exit_0,
              test_a_failing_command_answers_its_own_exit,
              test_an_unconfirmed_seal_refuses_and_runs_nothing,
              test_a_missing_command_is_refused_by_name]
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except AssertionError as exc:
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {exc}")
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed: {failed}")
        return 1
    print("green — the tester answers an exec ask: sealed run, own exit, loud refusal, named bad input.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
