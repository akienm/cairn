#!/usr/bin/env python3
"""`cairn test --exec '<command>'` — any command, run under the tester's instance seal.

WHAT THIS DEFENDS (ticket 2c9eeab2da87, child of dda0e72b9c67). The instance seal used to be
reachable only through ``run_proof``, which takes a proof PATH. Two hands run proofs some
other way: CC's tool calls (a ``python3 <proof> | grep`` pipeline is not a path) and
codemother's verdict, which runs chart instruments as ``bash -c``. Measured 2026-10-06: 88 of
290 proofs write live ``~/.cairn`` when run that way. The tester publishes one sealed entry
for an arbitrary command, so both hands can be rewritten onto it (1af0564c0db3, 68cef2ddd8ef)
instead of each building a second seal.

THE CLAIM, clause by clause of the ticket's falsifier:
  (1) the command runs with CAIRN_TESTER_INSTANCE_SEALED=1 and the exit is 0;
  (2) a write under ~/.cairn inside --exec never reaches the live root;
  (3) the command's exit code and stdout pass through unchanged;
  (4) with no bwrap and no inherited seal it exits 2 naming the seal and never runs bare;
  (5) the tester charter's public_interface names the entry.

NESTED, AS EVERY SEALED RUN OF THIS FILE IS. Under `cairn test` this proof already runs inside
an instance swap, and this host refuses a namespace inside a namespace (c54d744aa9ac), so a
real --exec here INHERITS that swap. A write it makes lands in the outer swap, which is what
this process sees as ~/.cairn; tooth (2) therefore accepts a present fixture only when
~/.cairn is a mount point here (the swap, not the live root), and measures the bare-host shape
separately: with inheritance off, the argv --exec would run binds a fresh snapshot over
~/.cairn. Tooth (4) is what stops a hollow --exec that simply runs ``bash -c``.

Proof: exit 0 = green.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROOF_TIMEOUT_S = 300

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

_CAIRN = _REPO_ROOT / "bin" / "cairn"
_CHARTER = _REPO_ROOT / "cairn" / "devices" / "tester" / "intention+why.json"
_LIVE = Path.home() / ".cairn"
_MARKER = "CAIRN_TESTER_INSTANCE_SEALED"

PROVES = {"2c9eeab2da87": {
    "1": "test_exec_runs_the_command_with_the_seal_marker",
    "2": "test_a_write_inside_exec_never_reaches_the_live_root",
    "3": "test_exit_code_and_stdout_pass_through_unchanged",
    "4": "test_no_bwrap_and_no_inherited_seal_refuses_never_bare",
    "5": "test_the_charter_publishes_the_entry",
}}


def _exec(command: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(_CAIRN), "test", "--exec", command, *extra],
                          capture_output=True, text=True, timeout=240, cwd=str(_REPO_ROOT))


def test_exec_runs_the_command_with_the_seal_marker():
    r = _exec(f'echo "${_MARKER}"')
    assert r.returncode == 0, f"--exec exit {r.returncode}: {r.stderr[-400:]}"
    assert r.stdout.strip() == "1", f"the command did not run sealed: stdout {r.stdout!r}"


def _bare_host_argv() -> list:
    """The argv --exec would hand subprocess on a host with bwrap and no outer seal.

    Driven in a child interpreter so the patches die with it. Inheritance is switched off,
    the snapshot is a fixture directory, and the seal measurement is reported SEALED; the
    runner records argv instead of executing it. What comes back is the composition --exec
    performs, nothing else."""
    code = r'''
import json, subprocess, sys, tempfile
from pathlib import Path
import cairn.devices.tester.device as d
from cairn.devices.tester.isolation import SEALED, Seal
swap = str(Path(tempfile.mkdtemp(prefix="exec_proof_fixture_swap_")) / "cairn")
Path(swap).mkdir()
d.inside_an_instance_seal = lambda: False
d.bwrap_available = lambda: (True, "fixture: bwrap present")
d.snapshot_instance_space = lambda: swap
d.check_instance_seal = lambda iso, root, cwd: Seal(SEALED, "fixture: measured elsewhere")
seen = []
def fake_run(argv, *a, **k):
    seen.append(list(argv))
    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
d.subprocess.run = fake_run
rc = d.TesterDevice().run_exec("touch exec-proof-fixture", timeout=30)
print(json.dumps({"rc": rc, "argv": seen, "swap": swap}))
'''
    # a bare host carries no outer seal marker, and wrap() reads the marker itself
    bare = {k: v for k, v in os.environ.items() if k != _MARKER}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
                       cwd=str(_REPO_ROOT), env={**bare, "PYTHONPATH": str(_REPO_ROOT)})
    assert r.returncode == 0, f"could not drive run_exec: {r.stderr[-600:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_a_write_inside_exec_never_reaches_the_live_root():
    fixture = _LIVE / f"exec-seal-fixture-written-by-a-proof-{os.getpid()}"
    try:
        r = _exec(f"touch {fixture}")
        assert r.returncode == 0, f"--exec exit {r.returncode}: {r.stderr[-400:]}"
        if fixture.exists():
            from cairn.devices.tester.isolation import _mount_points
            assert os.path.realpath(_LIVE) in _mount_points(), \
                f"{fixture} is present and {_LIVE} is no mount point here — the write reached the live root"
    finally:
        try:
            fixture.unlink()
        except OSError:
            pass
    got = _bare_host_argv()
    runs = [a for a in got["argv"] if "bash" in a]
    assert runs, f"run_exec never ran the command through bash: {got}"
    argv = runs[-1]
    assert argv[0] == "bwrap", f"on a bare host the command must run inside bwrap: {argv}"
    i = argv.index("--bind") if "--bind" in argv else -1
    assert i >= 0 and argv[i + 1] == got["swap"] and argv[i + 2] == str(_LIVE), \
        f"the snapshot is not bound over {_LIVE}: {argv}"
    assert argv[-3:] == ["bash", "-c", "touch exec-proof-fixture"], f"the command was altered: {argv}"


def test_exit_code_and_stdout_pass_through_unchanged():
    r = _exec("echo '  PASS  test_fixture_tooth'; echo to-stderr >&2; exit 3")
    assert r.returncode == 3, f"exit 3 came back as {r.returncode}: {r.stderr[-300:]}"
    assert r.stdout == "  PASS  test_fixture_tooth\n", f"stdout changed: {r.stdout!r}"
    assert "to-stderr" in r.stderr, f"stderr was not passed through: {r.stderr!r}"


def test_no_bwrap_and_no_inherited_seal_refuses_never_bare():
    mark = Path(f"/tmp/exec-proof-ran-bare-{os.getpid()}")
    code = rf'''
import cairn.devices.tester.device as d
d.bwrap_available = lambda: (False, "fixture: bubblewrap (bwrap) is not installed")
d.inside_an_instance_seal = lambda: False
raise SystemExit(d.TesterDevice().run_exec("touch {mark}", timeout=30))
'''
    try:
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
                           cwd=str(_REPO_ROOT), env={**os.environ, "PYTHONPATH": str(_REPO_ROOT)})
        assert not mark.exists(), "the command ran bare when no seal could be built"
        assert r.returncode == 2, f"expected exit 2, got {r.returncode}: {r.stderr[-400:]}"
        assert "seal" in r.stderr.lower(), f"the refusal must name the seal: {r.stderr!r}"
    finally:
        try:
            mark.unlink()
        except OSError:
            pass


def test_the_charter_publishes_the_entry():
    iface = json.loads(_CHARTER.read_text()).get("public_interface") or []
    text = json.dumps(iface)
    assert "--exec" in text and "run_exec" in text, \
        f"the tester charter's public_interface does not name `cairn test --exec` / run_exec: {iface}"


def test_the_whole_falsifier_holds_end_to_end():
    test_exec_runs_the_command_with_the_seal_marker()
    test_a_write_inside_exec_never_reaches_the_live_root()
    test_exit_code_and_stdout_pass_through_unchanged()
    test_no_bwrap_and_no_inherited_seal_refuses_never_bare()
    test_the_charter_publishes_the_entry()


def _main() -> int:
    checks = [
        test_exec_runs_the_command_with_the_seal_marker,
        test_a_write_inside_exec_never_reaches_the_live_root,
        test_exit_code_and_stdout_pass_through_unchanged,
        test_no_bwrap_and_no_inherited_seal_refuses_never_bare,
        test_the_charter_publishes_the_entry,
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
    print("green — cairn test --exec runs any command under the instance seal, or refuses")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
