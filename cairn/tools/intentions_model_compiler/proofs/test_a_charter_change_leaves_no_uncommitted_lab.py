r"""Proof for ticket 09b1565a2045 — a charter change and its compiled lab copy reach the commons
together, so the derived intentions-congruency-lab never stands as uncommitted tracked dirt.

Measured 2026-11-19 on akiendell: charters skills/note, commit and challenge gained
runtime_role and gated_by; the post-merge recompile regenerated their lab copies in the commons
working tree and nothing committed them, so a ``git pull --ff-only`` there aborted on local
changes. RED-FIRST: on the gate as it stands (it regenerates, never commits) teeth 1, 2 and 4
fail; tooth 3 holds today and keeps holding (it is the assumption the fix leans on, measured).

One tooth per falsifier clause, over a scratch commons (a git repo, plus a clone of it) and a
scratch code root; the live commons is never touched:

  1. after a charter changes and the gate runs, git status over the lab is clean (the
     regenerated lab files are committed);
  2. a clone taken before the change can ``git pull --ff-only`` afterwards and receives the lab;
  3. two scratch boxes compile the same charters into byte-identical lab files, so a lab commit
     from either merges without conflict;
  4. when the commit step fails (a pre-commit hook refuses), the gate still exits 0 and records
     the failure to its log, naming the lab file left uncommitted (Law 7).

    python3 cairn/tools/intentions_model_compiler/proofs/test_a_charter_change_leaves_no_uncommitted_lab.py
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"09b1565a2045": {
    "1": "test_a_charter_change_leaves_the_lab_committed",
    "2": "test_a_clone_can_fast_forward_pull_after_the_change",
    "3": "test_two_boxes_compile_byte_identical_lab_files",
    "4": "test_a_failed_commit_is_recorded_and_never_blocks"}}

_GATE = Path(__file__).resolve().parents[1] / "recompile_gate.sh"
_LAB = "intentions-congruency-lab"
_CHARTER = Path("cairn", "tools", "base", "intention+why.json")
_LAB_FILE = "cairn-tools-base--intention+why.json"


def _git(cwd, *args, check=True):
    done = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if check and done.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed in {cwd}: {done.stderr!r}")
    return done


def _code_root(d: str, charter: dict) -> str:
    code = os.path.join(d, "cairn")
    path = os.path.join(code, _CHARTER)
    os.makedirs(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(charter, f)
    return code


def _commons(d: str) -> str:
    """A scratch commons: a git repo whose first commit holds the lab as compiled from the
    ORIGINAL charter, the state every box is in before a charter changes."""
    commons = os.path.join(d, "CairnCommons")
    os.makedirs(os.path.join(commons, "intentions-not-beside-code"))
    os.makedirs(os.path.join(commons, _LAB))
    with open(os.path.join(commons, "intentions-not-beside-code", "telos.md"), "w", newline="\n") as f:
        f.write("the frame")
    _git(commons, "init", "-q", "-b", "main")
    _git(commons, "config", "user.name", "proof")
    _git(commons, "config", "user.email", "proof@example.invalid")
    _git(commons, "config", "core.autocrlf", "false")
    return commons


def _run(commons: str, code: str, logdir: str) -> subprocess.CompletedProcess:
    # A proof-poked gate run is not a real firing: its trace goes to a scratch berth.
    env = {**os.environ, "CAIRN_LB_TRACE_ROOT": str(scratch_dir("lab-commit-proof-traces-")),
           "CAIRN_COMMONS_ROOT": commons, "CAIRN_CODE_ROOT": code,
           "CAIRN_LAB_OUT": os.path.join(commons, _LAB), "CAIRN_LOG_DIR": logdir}
    return subprocess.run([shutil.which("bash") or "bash", _GATE.as_posix()],
                          capture_output=True, text=True, env=env)


def _baseline(d: str):
    """Commons + code root at the original charter, gate run once, everything committed."""
    commons = _commons(d)
    code = _code_root(d, {"what": "substrate"})
    _run(commons, code, os.path.join(d, "logs"))
    _git(commons, "add", "-A")
    _git(commons, "commit", "-q", "-m", "baseline lab")
    return commons, code


def _change_the_charter(code: str) -> None:
    with open(os.path.join(code, _CHARTER), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"what": "substrate", "runtime_role": "machine", "gated_by": ["Akien", "CC"]}, f)


def test_a_charter_change_leaves_the_lab_committed():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _baseline(d)
        _change_the_charter(code)
        r = _run(commons, code, os.path.join(d, "logs"))
        assert r.returncode == 0, f"the gate must exit 0, got {r.returncode}: {r.stderr!r}"
        lab = Path(commons, _LAB, _LAB_FILE).read_text(encoding="utf-8")
        assert "runtime_role" in lab, "the gate regenerated the lab from the changed charter"
        dirt = _git(commons, "status", "--porcelain", "--", _LAB).stdout
        assert dirt.strip() == "", \
            f"the regenerated lab stands as uncommitted tracked dirt in the commons: {dirt!r}"


def test_a_clone_can_fast_forward_pull_after_the_change():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _baseline(d)
        clone = os.path.join(d, "clone")
        _git(d, "clone", "-q", commons, clone)
        _change_the_charter(code)
        _run(commons, code, os.path.join(d, "logs"))
        pulled = _git(clone, "pull", "--ff-only", check=False)
        assert pulled.returncode == 0, \
            f"the clone's pull --ff-only aborted: {pulled.stdout!r} {pulled.stderr!r}"
        got = Path(clone, _LAB, _LAB_FILE).read_text(encoding="utf-8")
        assert "runtime_role" in got, "the clone received the regenerated lab through the pull"


def test_two_boxes_compile_byte_identical_lab_files():
    digests = []
    for box in ("one", "two"):
        with tempfile.TemporaryDirectory() as d:
            commons = _commons(d)
            code = _code_root(d, {"what": "substrate", "runtime_role": "machine"})
            _run(commons, code, os.path.join(d, "logs"))
            digests.append(hashlib.sha256(
                Path(commons, _LAB, _LAB_FILE).read_bytes()).hexdigest())
    assert digests[0] == digests[1], \
        f"two boxes compiled different lab bytes from the same charters: {digests}"


def test_a_failed_commit_is_recorded_and_never_blocks():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _baseline(d)
        hook = Path(commons, ".git", "hooks", "pre-commit")
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text("#!/bin/sh\necho refused-by-proof >&2\nexit 1\n", encoding="utf-8", newline="\n")
        hook.chmod(0o755)
        _change_the_charter(code)
        logdir = os.path.join(d, "logs")
        r = _run(commons, code, logdir)
        assert r.returncode == 0, "a failed commit never blocks the caller (exit 0)"
        log = os.path.join(logdir, "recompile-gate.log")
        assert os.path.exists(log), "the failed commit is recorded, not swallowed (Law 7)"
        said = Path(log).read_text(encoding="utf-8")
        assert "FAILED" in said and _LAB_FILE in said, \
            f"the record names the lab file left uncommitted: {said!r}"


def _main() -> int:
    checks = [test_a_charter_change_leaves_the_lab_committed,
              test_a_clone_can_fast_forward_pull_after_the_change,
              test_two_boxes_compile_byte_identical_lab_files,
              test_a_failed_commit_is_recorded_and_never_blocks]
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
    print("green — a charter change and its lab copy reach the commons together.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
