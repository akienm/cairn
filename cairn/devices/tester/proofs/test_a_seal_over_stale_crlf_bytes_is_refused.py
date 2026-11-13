"""Proof for ticket 8cc2a5752b6a: a seal over stale CRLF bytes is refused, naming the file.

MEASURED 2026-11-13. The Windows seal of cairn/tools/base/proofs/test_flock_stands_for_fcntl.py
at 52890c2f8 carries fp 133032682e11; Linux hashes 8318d78f2eda over the same committed closure.
The one match over every version of each file x CRLF-per-file: the committed bytes with
cairn/tools/base/__init__.py alone in CRLF. That file last changed before the *.py eol=lf pin
(88e30cde9bd4), and git rewrites a working file under a new attribute only when it writes it
again. ``git status`` reads such a tree clean, so every git-diff-based check let the seal land.

The tester now refuses a seal whose closure holds a file git calls unchanged but whose raw bytes
are not what checking out its index blob would write today (``working_bytes.unnormalized``).

EVERY TOOTH RUNS IN A SCRATCH GIT REPO with core.autocrlf=true, never the live tree.

  1. A FILE CHECKED OUT CRLF BEFORE THE PIN IS NAMED, by the predicate and by the hook's hold.
  2. AN ALL-LF TREE IS NAMED BY NEITHER; A GENUINE EDIT IS DIRTY, NEVER UNNORMALISED.
  3. run_proof (sink=validations) OVER SUCH A CLOSURE REFUSES, NAMING THE FILE, PERSISTING NOTHING.

    bin/cairn test cairn/devices/tester/proofs/test_a_seal_over_stale_crlf_bytes_is_refused.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"8cc2a5752b6a": {"1": "a_file_checked_out_crlf_before_the_pin_is_named",
                           "2": "an_lf_tree_and_a_genuine_edit_are_not_unnormalised",
                           "3": "run_proof_refuses_a_seal_over_stale_crlf_bytes"}}

CODE = "widget/widget_code.py"
PROOF = "widget/proofs/test_widget.py"
PROOF_SRC = ("import sys, pathlib\n"
             "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))\n"
             "import widget_code  # noqa: F401  (widget/widget_code.py)\n"
             "raise SystemExit(0)\n")
PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=True).stdout


def _repo(*, stale: bool) -> Path:
    """A scratch repo, core.autocrlf=true. ``stale``: the .py files are checked out (CRLF)
    BEFORE the eol=lf pin lands, so they stay CRLF in the working tree; else the pin is in
    the first commit and they check out LF."""
    from cairn.tools.scratch.scratch import scratch_dir
    repo = scratch_dir("testing-8cc2a5752b6a-") / "repo"
    (repo / "widget" / "proofs").mkdir(parents=True)
    (repo / "widget" / "validations").mkdir()
    _git(repo, "init", "-q")
    for k, v in (("core.autocrlf", "true"), ("user.email", "fixture@cairn"),
                 ("user.name", "fixture"), ("commit.gpgsign", "false")):
        _git(repo, "config", k, v)
    (repo / CODE).write_bytes(b"X = 1\n")
    (repo / PROOF).write_bytes(PROOF_SRC.encode())
    pin = b"*.py text eol=lf\n"
    if not stale:
        (repo / ".gitattributes").write_bytes(pin)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "one")
    (repo / CODE).unlink()
    (repo / PROOF).unlink()
    _git(repo, "checkout", "--", ".")                # a checkout under autocrlf, pre-pin: CRLF
    if stale:
        (repo / ".gitattributes").write_bytes(pin)
        _git(repo, "add", ".gitattributes")
        _git(repo, "commit", "-qm", "pin")
    return repo


def _drop(repo: Path) -> None:
    shutil.rmtree(repo.parent, ignore_errors=True)


def unnormalized(*a, **k):
    """Bound at call time: the hollow reading takes the module away."""
    from cairn.devices.tester.working_bytes import unnormalized as subject
    return subject(*a, **k)


def dirty_against_index(*a, **k):
    from cairn.devices.tester.reseal import dirty_against_index as subject
    return subject(*a, **k)


def a_file_checked_out_crlf_before_the_pin_is_named():
    repo = _repo(stale=True)
    try:
        assert b"\r\n" in (repo / CODE).read_bytes(), "fixture: the stale checkout is not CRLF"
        assert _git(repo, "status", "--porcelain").strip() == "", "fixture: git status not clean"
        got = unnormalized([CODE, PROOF], repo)
        assert got == sorted([CODE, PROOF]), f"unnormalized named {got}"
        held = dirty_against_index(PROOF, [CODE], repo)
        assert CODE in held, f"the hook's hold did not name {CODE}: {held}"
    finally:
        _drop(repo)


def an_lf_tree_and_a_genuine_edit_are_not_unnormalised():
    repo = _repo(stale=False)
    try:
        assert b"\r\n" not in (repo / CODE).read_bytes(), "fixture: the LF checkout carries CRLF"
        assert unnormalized([CODE, PROOF], repo) == [], "an all-LF tree was named"
        assert dirty_against_index(PROOF, [CODE], repo) == [], "an all-LF tree was held"
        (repo / CODE).write_bytes(b"X = 2\n")         # a real, uncommitted edit
        assert unnormalized([CODE, PROOF], repo) == [], "a genuine edit was named unnormalised"
        assert dirty_against_index(PROOF, [CODE], repo) == [CODE], "the edit is not dirty"
    finally:
        _drop(repo)


def run_proof_refuses_a_seal_over_stale_crlf_bytes():
    from cairn.devices.tester.device import TesterDevice
    from cairn.devices.tester.working_bytes import UnnormalizedClosure
    from cairn.tools.validation_store import validation_store as vs
    repo = _repo(stale=True)
    saved = vs._REPO_ROOT
    vs._REPO_ROOT = str(repo)
    try:
        try:
            TesterDevice().run_proof(repo / PROOF, sink="validations", caller="cairn test",
                                     timeout=60, isolation="none",
                                     scratch_sweep={"skipped": "proof fixture"})
        except UnnormalizedClosure as refusal:
            assert CODE in str(refusal) and CODE in refusal.files, (
                f"the refusal does not name {CODE}: {refusal}")
        else:
            raise AssertionError("run_proof sealed over a stale CRLF closure")
        landed = list((repo / "widget" / "validations").iterdir())
        assert landed == [], f"a validation persisted: {landed}"
    finally:
        vs._REPO_ROOT = saved
        _drop(repo)


def main() -> int:
    for name in PROVES["8cc2a5752b6a"].values():
        _tooth(name, globals()[name])
    print(f"\n{PASS}/{PASS + FAIL} teeth green")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
