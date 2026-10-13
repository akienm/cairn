"""Proof for ticket ``25ee4866642e`` — a proof's verdict does not depend on the git environment
that called it.

Measured 2026-10-13 on a135bdb13646's build commit: test_rehearsal.py sealed RED ('invalid
object ... Error building trees') because the hook of a ``git commit -- <paths>`` carries
GIT_INDEX_FILE=<abs>/.git/next-index-*.lock, and ``_env_pinned_to`` handed that to the subject,
whose own scratch-repo commit then wrote through the caller's index. Rerun bare it sealed green.
The subject env now starts from ``cairn.tools.scratch.scratch.git_env()`` — the scrub the
tester's own git calls already take — keeping the PYTHONPATH pin.

Each tooth builds an outer scratch repo whose pre-commit hook asks ``_env_pinned_to`` (bound
at call time, inside the hook) for the subject's env and runs a tiny subject that does
``git init`` + ``git commit`` in its own tmp dir. The subject's exit code is the verdict.
Teeth, one per caller the falsifier names:
  (T1) called bare, the subject exits 0;
  (T2) called from a plain ``git commit`` hook, the subject exits 0;
  (T3) called from a ``git commit -- <path>`` hook, the subject exits 0.
Hollow: today's device.py reds T3.

    bin/cairn test cairn/devices/tester/proofs/test_a_proof_does_not_inherit_the_callers_git_env.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# The falsifier reads as one clause ('all'); T3 is the tooth the hollow build reds, and T1/T2
# are the same verdict's other two callers.
PROVES = {"25ee4866642e": {
    "all": "test_path_commit_hook_seals_green",
}}

FAILURES: list[str] = []

SUBJECT = r'''
import os, subprocess, sys, tempfile
d = tempfile.mkdtemp(prefix="cairn-proof-gitenv-subject-")
def g(*a):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)
r = g("init", "-q")
open(os.path.join(d, "f"), "w").write("x\n")
r = r.returncode or g("add", "f").returncode
c = g("-c", "user.name=proof", "-c", "user.email=proof@invalid", "commit", "-q", "-m", "s")
sys.stderr.write(c.stderr)
sys.exit(1 if (r or c.returncode) else 0)
'''

# The hook runs under git's environment: it asks _env_pinned_to for the subject env at call
# time, runs the subject with it, and writes the exit code where the tooth reads it.
HOOK = r'''#!{py}
import subprocess, sys
sys.path.insert(0, {root!r})
from cairn.devices.tester.device import _env_pinned_to
r = subprocess.run([sys.executable, {subject!r}], env=_env_pinned_to({subject!r}),
                   capture_output=True, text=True)
open({out!r}, "w").write(str(r.returncode) + "\n" + r.stderr)
'''


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _clean_env() -> dict:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _run(mode: str) -> tuple[int | None, str]:
    """The subject's exit code when called ``mode``: 'bare', 'plain' or 'paths'."""
    work = Path(tempfile.mkdtemp(prefix="cairn-proof-gitenv-outer-"))
    try:
        subject = work / "subject.py"
        subject.write_text(SUBJECT)
        out = work / "verdict.txt"
        if mode == "bare":
            from cairn.devices.tester.device import _env_pinned_to
            r = subprocess.run([sys.executable, str(subject)], env=_env_pinned_to(str(subject)),
                               capture_output=True, text=True)
            return r.returncode, r.stderr[-300:]
        repo = work / "outer"
        env = _clean_env()
        def git(*a):
            return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True,
                                  env=env)
        repo.mkdir()
        git("init", "-q")
        hook = repo / ".git" / "hooks" / "pre-commit"
        hook.write_text(HOOK.format(py=sys.executable, root=str(_REPO_ROOT),
                                    subject=str(subject), out=str(out)))
        hook.chmod(0o755)
        (repo / "a").write_text("a\n")
        git("add", "a")
        args = ["-c", "user.name=proof", "-c", "user.email=proof@invalid", "commit", "-q", "-m", "o"]
        c = git(*args, "--", "a") if mode == "paths" else git(*args)
        if not out.exists():
            return None, f"hook never wrote: commit rc={c.returncode} {c.stderr[-300:]}"
        rc, _, err = out.read_text().partition("\n")
        return int(rc), err[-300:]
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _tooth(name: str, mode: str) -> None:
    rc, err = _run(mode)
    check(name, rc == 0, f"subject rc={rc} {err.strip()[-200:]}")


def test_bare_call_seals_green() -> None:
    _tooth("test_bare_call_seals_green", "bare")


def test_plain_commit_hook_seals_green() -> None:
    _tooth("test_plain_commit_hook_seals_green", "plain")


def test_path_commit_hook_seals_green() -> None:
    _tooth("test_path_commit_hook_seals_green", "paths")


def main() -> int:
    for tooth in (test_bare_call_seals_green, test_plain_commit_hook_seals_green,
                  test_path_commit_hook_seals_green):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
