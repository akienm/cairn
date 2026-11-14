#!/usr/bin/env python3
"""Proof for ticket 21acc004c1fa: ``cairn test`` and ``cairn test --exec`` run bash-free on Windows.

Measured 2026-11-14 on akienyoga9i (ticket 56b61c10bdbe, ruling C): MSYS cannot start at Low
integrity. msys-2.0.dll's NtCreateDirectoryObject gets 0xC0000022 and the process exits 0xC0000142.
So every run that put bash in front of the subject was detect-kind, and `--exec` was ALWAYS bash
(``bash -c COMMAND``). bash -c also ate a Windows path's backslashes: ``touch C:\\Users\\...``
made a ``C:Users...`` file in the cwd. And --exec printed nothing at all, because run_owned starts
the child CREATE_NO_WINDOW, which gave it a hidden console of its own when no handles were named.

  1. clause_1_a_proof_on_cairn_test_argv_runs_prevent_kind_and_green_at_low: a subject that runs
     the tester through cairn_test_argv (no bash) is prevent-kind, and it runs green at Low;
  2. clause_2_a_plain_exec_is_prevent_and_passes_rc_and_stdout_and_a_pipe_is_detect: a plain
     ``--exec '<python> -c ...'`` is prevent with no bash in its argv, runs at Low, and its rc and
     stdout come back unchanged. A command with ``|`` is detect, and its why is "command needs a
     shell";
  3. clause_3_a_backslashed_path_reaches_the_process_intact: a plain --exec hands a Windows path
     to its process byte for byte, and ``touch`` makes exactly that file, with no debris in the cwd;
  4. clause_4_detect_records_bash_spawned_and_a_bare_bin_cairn_mention_is_prevent: a detect-kind
     record says whether bash was in fact spawned (true and false both seen), and a bare
     ``bin/cairn`` mention in a subject no longer makes it detect;
  5. clause_5_the_exec_proofs_reach_the_tester_bash_free: the three --exec proofs (and test_cli's
     cwd case) reach the tester through cairn_test_argv, never bash_script_argv(bin/cairn). Their
     green on Windows is the bounded run reported with the build.

Off Windows, teeth 1-4 SKIP: POSIX is unchanged (exec_kind keeps ``bash -c``, prevent).

Hollow: put ``run_exec`` back on ``["bash", "-c", command]`` and teeth 2-3 red. Put the bare
bin/cairn alternative back in _DRIVES_BASH and tooth 4 reds.

Run bare:  PYTHONPATH=. python cairn/devices/tester/proofs/test_cairn_test_and_exec_run_bash_free_on_windows.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

PROOF_TIMEOUT_S = 600

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.base.script_argv import cairn_test_argv  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "21acc004c1fa": {
        "1": "clause_1_a_proof_on_cairn_test_argv_runs_prevent_kind_and_green_at_low",
        "2": "clause_2_a_plain_exec_is_prevent_and_passes_rc_and_stdout_and_a_pipe_is_detect",
        "3": "clause_3_a_backslashed_path_reaches_the_process_intact",
        "4": "clause_4_detect_records_bash_spawned_and_a_bare_bin_cairn_mention_is_prevent",
        "5": "clause_5_the_exec_proofs_reach_the_tester_bash_free",
    },
}

PY = sys.executable


def _windows() -> bool:
    if sys.platform != "win32":
        print(f"SKIP 21acc004c1fa: the bash-free teeth run on win32 only; this is {sys.platform}")
        return False
    return True


def _names_bash(argv) -> list[str]:
    return [a for a in argv if Path(str(a)).name.lower() in ("bash", "bash.exe", "sh", "sh.exe")]


def _exec(command: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    argv, env, run_cwd = cairn_test_argv("--exec", command, "--timeout", "120", cwd=cwd or REPO)
    return subprocess.run(argv, env=env, cwd=run_cwd, capture_output=True, text=True, timeout=300)


def _low_world() -> Path:
    world = scratch_dir("testing-21ac-world-")
    r = subprocess.run(["icacls", str(world), "/setintegritylevel", "(OI)(CI)L"],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"could not label the proof's own world Low: {r.stdout} {r.stderr}"
    return world


def _run_in_process(source: str, name: str) -> dict:
    """One run_proof of ``source`` (sink none, so nothing persists). Returns the record."""
    from cairn.devices.tester import device as d
    proof = _low_world() / name
    proof.write_text(source, encoding="utf-8")
    return d.TesterDevice().run_proof(proof, sink="none", caller="21acc004c1fa proof", timeout=300)


# Prints whether this process runs at Low: the witness that a run was prevent-kind.
_SAYS_LOW = ("import sys; sys.path.insert(0, r'{repo}'); "
             "from cairn.devices.tester.isolation import _own_integrity_is_low as low; "
             "print('low' if low() else 'not-low'); print('out-{token}'); sys.exit(7)")

# Tooth 1's subject reaches the tester's CLI through cairn_test_argv, with no bash.
_ON_THE_ARGV = r'''
import subprocess, sys
sys.path.insert(0, {repo!r})
from cairn.tools.base.script_argv import cairn_test_argv
argv, env, cwd = cairn_test_argv("--help", cwd={repo!r})
p = subprocess.run(argv, env=env, cwd=cwd, capture_output=True, text=True, timeout=240)
assert p.returncode == 0 and "--exec" in p.stdout, f"rc {{p.returncode}} {{p.stderr[-300:]}}"
print("ok   test_on_the_argv_stand_in", flush=True)
'''

# Tooth 4's subjects. One names bash and spawns it; one names bash and never spawns it; one only
# MENTIONS bin/cairn, as a docstring or a usage line does.
_SPAWNS_BASH = r'''
import shutil, subprocess
assert subprocess.run([shutil.which("bash"), "-c", "exit 0"]).returncode == 0
print("ok   test_spawns_bash_stand_in", flush=True)
'''
_NAMES_BASH_ONLY = r'''
WHAT = "bash"   # named, never run
print("ok   test_names_bash_stand_in", flush=True)
'''
_MENTIONS_BIN_CAIRN = r'''
"""Run me as:  bin/cairn test <this file>"""
from pathlib import Path
CAIRN = Path("x") / "bin" / "cairn"
print("ok   test_mentions_stand_in", flush=True)
'''


def clause_1_a_proof_on_cairn_test_argv_runs_prevent_kind_and_green_at_low():
    if not _windows():
        return
    rec = _run_in_process(_ON_THE_ARGV.format(repo=str(REPO)), "test_21ac_on_the_argv_stand_in.py")
    seal = rec["evidence"]["instance_seal"]
    assert seal.get("seal_kind") == "prevent", f"a cairn_test_argv subject ran {seal.get('seal_kind')!r}: {seal}"
    assert rec["verdict"] == "green", (f"the cairn_test_argv subject did not run green at Low: "
                                       f"{rec['verdict']} {rec['evidence'].get('stderr_tail')}")


def clause_2_a_plain_exec_is_prevent_and_passes_rc_and_stdout_and_a_pipe_is_detect():
    if not _windows():
        return
    from cairn.devices.tester.isolation import DETECT_BECAUSE_SHELL, exec_kind
    token = uuid.uuid4().hex[:10]
    plain = f'"{PY}" -c "{_SAYS_LOW.format(repo=str(REPO), token=token)}"'
    kind, why, argv = exec_kind(plain)
    assert (kind, why) == ("prevent", None), f"a plain command read {kind!r} ({why})"
    assert not _names_bash(argv) and argv[0] == PY, f"the plain argv is not the command itself: {argv}"
    r = _exec(plain)
    assert r.returncode == 7, f"exit 7 came back as {r.returncode}: {r.stderr[-400:]}"
    lines = r.stdout.split()
    assert f"out-{token}" in lines, f"the command's stdout did not arrive: {r.stdout!r} {r.stderr[-300:]}"
    assert "low" in lines, f"the plain command did not run at Low (prevent): {r.stdout!r}"
    piped = f'"{PY}" -c "print(\'piped-{token}\')" | cat'
    kind, why, argv = exec_kind(piped)
    assert kind == "detect" and why == DETECT_BECAUSE_SHELL and argv[:2] == ["bash", "-c"], (
        f"a piped command read {kind!r} ({why}): {argv}")
    r = _exec(piped)
    assert r.returncode == 0 and f"piped-{token}" in r.stdout, (
        f"the piped command did not run through the shell: rc {r.returncode} {r.stdout!r} {r.stderr[-300:]}")


def clause_3_a_backslashed_path_reaches_the_process_intact():
    if not _windows():
        return
    where = scratch_dir("testing-21ac-paths-")
    target = where / "sub dir" / f"made-{uuid.uuid4().hex[:8]}.txt"
    target.parent.mkdir()
    assert "\\" in str(target), f"precondition: a backslashed path: {target}"
    r = _exec(f'"{PY}" -c "import sys; print(sys.argv[1])" "{target}"', cwd=where)
    assert r.returncode == 0 and r.stdout.strip() == str(target), (
        f"the path did not arrive intact: {r.stdout!r} != {str(target)!r} {r.stderr[-300:]}")
    r = _exec(f'touch "{target}"', cwd=where)
    assert r.returncode == 0, f"touch exit {r.returncode}: {r.stderr[-400:]}"
    assert target.is_file(), f"touch did not make the file it was named: {target}"
    debris = sorted(p.name for p in where.iterdir() if p.name != "sub dir")
    assert not debris, f"a mangled path left debris in the cwd: {debris}"


def clause_4_detect_records_bash_spawned_and_a_bare_bin_cairn_mention_is_prevent():
    if not _windows():
        return
    from cairn.devices.tester.isolation import subject_drives_bash
    assert not subject_drives_bash(_MENTIONS_BIN_CAIRN), "a bare bin/cairn mention reads as driving bash"
    assert subject_drives_bash("argv = bash_script_argv(x)"), "bash_script_argv no longer reads as bash"
    seen = {}
    for name, source in (("spawns", _SPAWNS_BASH), ("names", _NAMES_BASH_ONLY),
                         ("mentions", _MENTIONS_BIN_CAIRN)):
        rec = _run_in_process(source, f"test_21ac_{name}_stand_in.py")
        seen[name] = (rec["verdict"], rec["evidence"]["instance_seal"])
    verdict, seal = seen["spawns"]
    assert seal.get("seal_kind") == "detect" and seal.get("bash_spawned") is True, (
        f"a subject that spawned bash did not record bash_spawned true: {verdict} {seal}")
    verdict, seal = seen["names"]
    assert seal.get("seal_kind") == "detect" and seal.get("bash_spawned") is False, (
        f"a subject that only named bash did not record bash_spawned false: {verdict} {seal}")
    verdict, seal = seen["mentions"]
    assert seal.get("seal_kind") == "prevent" and "bash_spawned" not in seal, (
        f"a bare bin/cairn mention did not run prevent-kind: {verdict} {seal}")
    assert verdict == "green", f"the mention subject did not run green at Low: {verdict} {seal}"


_EXEC_PROOFS = ("test_a_command_runs_under_the_seal_by_exec.py", "test_exec_runs_in_the_callers_cwd.py",
                "test_an_exec_bound_reaches_the_proof_it_runs.py")


def clause_5_the_exec_proofs_reach_the_tester_bash_free():
    here = Path(__file__).resolve().parent
    for name in _EXEC_PROOFS:
        text = (here / name).read_text(encoding="utf-8")
        assert "cairn_test_argv" in text, f"{name} does not reach the tester through cairn_test_argv"
        assert "bash_script_argv" not in text, f"{name} still puts bash in front of the tester"


def _main() -> int:
    checks = [clause_1_a_proof_on_cairn_test_argv_runs_prevent_kind_and_green_at_low,
              clause_2_a_plain_exec_is_prevent_and_passes_rc_and_stdout_and_a_pipe_is_detect,
              clause_3_a_backslashed_path_reaches_the_process_intact,
              clause_4_detect_records_bash_spawned_and_a_bare_bin_cairn_mention_is_prevent,
              clause_5_the_exec_proofs_reach_the_tester_bash_free]
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as e:  # noqa: BLE001 - a crash in a tooth is that tooth's red
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {type(e).__name__}: {e}")
    if failed:
        print(f"red - {len(failed)} of {len(checks)} teeth failed")
        return 1
    print("green - cairn test and --exec run bash-free on Windows")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
