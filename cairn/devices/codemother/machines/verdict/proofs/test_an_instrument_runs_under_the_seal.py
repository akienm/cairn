#!/usr/bin/env python3
"""verdict.run_instrument runs every chart instrument under the tester's instance seal.

WHAT THIS DEFENDS (ticket 68cef2ddd8ef, child of dda0e72b9c67). ``run_instrument`` forked
``bash -c <instrument>`` with no seal, and a chart instrument runs the ticket's proofs
(``python3 <proof> | ...``), so every PROVED crossing executed proofs against live
``~/.cairn`` with no CC in the loop. The tester publishes one sealed entry for an arbitrary
command, ``cairn test --exec`` (2c9eeab2da87, PROVED); the verdict reaches the seal through
that published interface (RULE 1) and builds none of its own.

THE CLAIM, clause by clause of the ticket's falsifier:
  (1) an instrument runs with CAIRN_TESTER_INSTANCE_SEALED=1, inside a run --exec minted;
  (2) a write under ~/.cairn never reaches the live root: the instrument goes to
      ``bin/cairn test --exec <command> --timeout N`` and nowhere else;
  (3) the record keeps its keys, an exit 3 reads 3, and a timeout still reads as one;
  (4) a refused seal is a recorded reading, and nothing runs bare after it.

NESTED, AS EVERY SEALED RUN OF THIS FILE IS. Under ``cairn test`` this process already sits
in an instance swap and already carries the seal marker, so a bare ``bash -c`` would echo
the marker too. What tells the two apart is the RUN ID: --exec mints a fresh
CAIRN_TESTER_TEST_ID for every command, a bare fork inherits this proof's own. Tooth (2)
reads the composition run_instrument hands subprocess, because the seal itself is the
tester's proven claim (2c9eeab2da87) and this machine's claim is only that it goes there.

Proof: exit 0 = green.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

PROOF_TIMEOUT_S = 300

_REPO_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(_REPO_ROOT))

# Reached through the module, never from-imported: a hollow revert must fail a tooth,
# not kill collection (see test_the_instrument_is_run.py's note on the same point).
from cairn.devices.codemother.machines.verdict import verdict as _verdict  # noqa: E402

_CAIRN = str(_REPO_ROOT / "bin" / "cairn")
_LIVE = Path.home() / ".cairn"
_MARKER = "CAIRN_TESTER_INSTANCE_SEALED"
_RUN_ID = "CAIRN_TESTER_TEST_ID"
_KEYS = {"command", "exit", "timed_out", "timeout_s", "seconds", "tail"}

PROVES = {"68cef2ddd8ef": {
    "1": "test_an_instrument_runs_inside_a_sealed_exec",
    "2": "test_an_instrument_goes_to_the_sealed_exec_and_nowhere_else",
    "3": "test_the_record_keeps_its_keys_and_its_exit",
    "4": "test_a_refused_seal_is_recorded_and_nothing_runs_bare",
}, "68e897fc74b8": {
    "1": "test_the_proof_reaches_no_device_off_its_interface",
    "2": "test_an_instrument_goes_to_the_sealed_exec_and_nowhere_else",
}}


def _drive(code: str) -> dict:
    """Run ``code`` in a child interpreter whose subprocess.run is a recorder.

    The patches die with the child. ``code`` sees ``v`` (the verdict module), ``seen`` (every
    argv handed to subprocess.run) and ``answer`` (a function of argv returning the
    CompletedProcess or raising), and prints one JSON line."""
    prelude = r'''
import json, subprocess, sys
from cairn.devices.codemother.machines.verdict import verdict as v
seen = []
def answer(argv):
    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
def fake_run(argv, *a, **k):
    seen.append(list(argv))
    return answer(argv)
v.subprocess.run = fake_run
'''
    r = subprocess.run([sys.executable, "-c", prelude + code], capture_output=True, text=True,
                       timeout=60, cwd=str(_REPO_ROOT),
                       env={**os.environ, "PYTHONPATH": str(_REPO_ROOT)})
    assert r.returncode == 0, f"could not drive run_instrument: {r.stderr[-600:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_an_instrument_runs_inside_a_sealed_exec():
    rec = _verdict.run_instrument(f'echo "${_MARKER} ${_RUN_ID}"', timeout_s=120)
    assert rec["exit"] == 0, f"instrument exit {rec['exit']}: {rec.get('tail', '')[-400:]}"
    words = rec["tail"].split()
    assert len(words) == 2 and words[0] == "1", \
        f"the instrument did not run under the instance seal: tail {rec['tail']!r}"
    assert words[1].startswith("test-") and words[1] != os.environ.get(_RUN_ID), \
        f"no fresh run id: the instrument was forked bare, not run by cairn test --exec ({rec['tail']!r})"


def test_an_instrument_goes_to_the_sealed_exec_and_nowhere_else():
    fixture = _LIVE / f"verdict-seal-fixture-written-by-a-proof-{os.getpid()}"
    try:
        rec = _verdict.run_instrument(f"touch {fixture}", timeout_s=120)
        assert rec["exit"] == 0, f"instrument exit {rec['exit']}: {rec.get('tail', '')[-400:]}"
        if fixture.exists():
            from cairn.devices.tester.isolation import _mount_points
            assert os.path.realpath(_LIVE) in _mount_points(), \
                f"{fixture} is present and {_LIVE} is no mount point here — the write reached the live root"
    finally:
        try:
            fixture.unlink()
        except OSError:
            pass
    got = _drive(r'''
rec = v.run_instrument("touch verdict-proof-fixture", timeout_s=30, cwd="/tmp")
print(json.dumps({"seen": seen, "rec": rec}))
''')
    assert got["seen"], f"run_instrument forked nothing: {got}"
    assert all(a[:3] == [_CAIRN, "test", "--exec"] for a in got["seen"]), \
        f"an instrument was forked somewhere other than {_CAIRN} test --exec: {got['seen']}"
    argv = got["seen"][-1]
    assert argv == [_CAIRN, "test", "--exec", "touch verdict-proof-fixture", "--timeout", "30"], \
        f"the instrument or its bound was altered on the way to the seal: {argv}"


def test_the_record_keeps_its_keys_and_its_exit():
    command = f'echo "${_RUN_ID}"; echo to-stderr >&2; exit 3'
    rec = _verdict.run_instrument(command, timeout_s=120)
    assert _KEYS <= set(rec), f"the record lost keys: {sorted(_KEYS - set(rec))}"
    assert rec["command"] == command, f"the record names a different command: {rec['command']!r}"
    assert rec["exit"] == 3 and rec["timed_out"] is False, f"exit 3 came back as {rec}"
    assert "to-stderr" in rec["tail"], f"stderr fell out of the tail: {rec['tail']!r}"
    ran = rec["tail"].split()[0] if rec["tail"].split() else ""
    assert ran.startswith("test-") and ran != os.environ.get(_RUN_ID), \
        f"exit 3 came from a bare fork, not the sealed exec: {rec['tail']!r}"
    got = _drive(r'''
def answer(argv):
    return subprocess.CompletedProcess(argv, 124, stdout="",
                                       stderr="cairn test --exec: timed out after 5s\n")
rec = v.run_instrument("sleep 30", timeout_s=5)
print(json.dumps(rec))
''')
    assert got["timed_out"] is True and got["exit"] is None and got["timeout_s"] == 5, \
        f"the sealed exec's timeout does not read as a timeout: {got}"


def test_a_refused_seal_is_recorded_and_nothing_runs_bare():
    got = _drive(r'''
REFUSAL = ("cairn test --exec: refused — the instance seal is not confirmed "
           "(indeterminate: fixture: no bwrap); the command was not run\n")
def answer(argv):
    if argv and argv[0] == "bash":
        return subprocess.CompletedProcess(argv, 0, stdout="ran bare\n", stderr="")
    return subprocess.CompletedProcess(argv, 2, stdout="", stderr=REFUSAL)
rec = v.run_instrument("echo would-have-run", timeout_s=30)
print(json.dumps({"seen": seen, "rec": rec}))
''')
    rec, seen = got["rec"], got["seen"]
    assert not any(a and a[0] == "bash" for a in seen), f"the instrument ran bare after a refusal: {seen}"
    assert len(seen) == 1, f"one refusal, one fork — anything more is a fallback: {seen}"
    assert rec["exit"] == 2 and "instance seal is not confirmed" in (rec.get("seal_refused") or ""), \
        f"the refusal is not a recorded reading: {rec}"
    assert "ran bare" not in rec["tail"], f"bare output reached the record: {rec}"


def test_the_proof_reaches_no_device_off_its_interface():
    # RULE 1 holds inside a proof too (68e897fc74b8): build_inspector publishes the sieve,
    # resolved at call time so a reverted build reads as this tooth's red.
    inspector = importlib.import_module("cairn.machines.build_inspector.inspector")
    rows = [b for b in inspector.encapsulation_breaches(str(_REPO_ROOT))
            if Path(b.get("file") or "").name == Path(__file__).name]
    assert not rows, f"{len(rows)} reach(es) off a published interface from this proof: " + "; ".join(
        f"{b['file']}:{b['line']} {b['module']}" for b in rows)


def test_the_whole_falsifier_holds_end_to_end():
    test_the_proof_reaches_no_device_off_its_interface()
    test_an_instrument_runs_inside_a_sealed_exec()
    test_an_instrument_goes_to_the_sealed_exec_and_nowhere_else()
    test_the_record_keeps_its_keys_and_its_exit()
    test_a_refused_seal_is_recorded_and_nothing_runs_bare()


def _main() -> int:
    checks = [
        test_the_proof_reaches_no_device_off_its_interface,
        test_an_instrument_runs_inside_a_sealed_exec,
        test_an_instrument_goes_to_the_sealed_exec_and_nowhere_else,
        test_the_record_keeps_its_keys_and_its_exit,
        test_a_refused_seal_is_recorded_and_nothing_runs_bare,
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
    print("green — every chart instrument runs under the instance seal, or is refused on the record")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
