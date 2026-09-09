"""Scratch — a throwaway directory a proof CANNOT leave behind.

THE STONE, IN ONE SENTENCE: ``scratch_dir(prefix)`` hands back a temp directory whose
removal is registered BY THE DOOR, not by the caller. There is no cleanup for a proof
author to forget, because there is no cleanup for a proof author to write.

MEASURED, 2026-08-03, and the measurement is why this is a door and not a convention:
thirty ``tempfile.mkdtemp`` call sites across twenty-five proof files, ZERO cleanup at any
of them, and no ``atexit`` anywhere in the repository. Two months of proof runs had left
**3581 leaked entries and 33M in /tmp** (swept the same day; /tmp went 3635 -> 54). Nobody
was careless. Thirty authors — all of them the same one — each wrote the obvious line, and
the obvious line leaks; the largest single prefix, 556 of them, belonged to a component
built THIS WEEK, so this was not old debt draining away. That is the
signature of policy: it binds only the callers who happen to remember it, and there is no
moment at which anyone is told. Law 4 — a rule that matters is enforced by physics.

AND THE SPELLING WAS NOT THE DEFECT. The first pass fixed thirty ``mkdtemp`` sites and the
corpus tooth guarding them grepped for ``mkdtemp`` — which missed a thirty-first leak
wearing a different spelling (``tempfile.gettempdir()`` in ``launchers/proofs/test_bootstrap.py``,
one boot-log FILE per run, 18 of them standing). A tooth narrower than its own defect is
the hollow kind. The rule is therefore about the REACH, not the function name: a proof
touches the system temp directory only through this door. The three call sites that merely
NAMED a deliberately-nonexistent path came through it too — not because they leaked, but
so that no exemption exists to maintain and no one has to adjudicate which reach is
harmless (the exemption-roster pattern is what let a node through with no watch at all).

HOW IT WAS FOUND, recorded because the finding is worse than the leak: BY ACCIDENT, while
chasing an unrelated ``PermissionError`` in a different proof. Every scan Cairn owns —
``device_census``, ``import_map``, ``repo_truth``, ``call_sites`` — reads CLASS-SPACE,
because class-space is git and git is what we can see. Nothing observes the host. Garbage
accumulated for two months on the machine the system runs on and no feedback loop had an
eye pointed at it. The missing thing was not a check, it was an ADDRESS.
    -> CairnCommons/tickets/nothing-observes-the-host.json

WHY ATEXIT AND NOT A CONTEXT MANAGER. ``tempfile.TemporaryDirectory`` is already the
context-manager answer, and a proof that can use it should (``test_emission_gate`` does).
These thirty could not: they are module-level roots and helper-function returns, alive
across many teeth, with no single ``with`` block whose scope matches. ``atexit`` is the
scope that actually fits their lifetime — the run.

WHAT THIS DOES NOT CLAIM. A run killed with SIGKILL fires no atexit hook and leaks. That
is the tail; it is not the two-month case, and it does not justify a supervisor process to
watch a directory. The honest boundary is stated rather than papered over (CP1).
"""

from __future__ import annotations

import atexit
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def scratch_dir(prefix: str) -> Path:
    """A temp directory removed when this process exits. The caller writes no cleanup."""
    d = Path(tempfile.mkdtemp(prefix=prefix))
    atexit.register(_sweep, d)
    return d


def _sweep(d: Path) -> None:
    """Remove it, and SAY SO if it cannot be removed.

    A cleanup that fails silently is the leak wearing a hat — invisible accumulation was
    this defect's entire nature, so a sweep that quietly gives up would reproduce it with
    a clean conscience. It reports at the diagnostic surface and never raises: an
    exception escaping an atexit hook at interpreter shutdown buries the proof's own
    verdict under a teardown traceback, which trades one loud thing for a louder wrong
    thing (Law 7 — loud means legible).
    """
    try:
        shutil.rmtree(d)
    except FileNotFoundError:
        pass                      # the proof cleaned up after itself — nothing to report
    except OSError as e:
        print(f"scratch: could not remove {d}: {type(e).__name__}: {e}", file=sys.stderr)


def scratch_worktree(commit: str, *, repo_root: str | Path, prefix: str = "cairn-hollow-") -> Path:
    """A git worktree at ``commit``, removed AND DEREGISTERED when this process exits.

    The hollow verb (ticket d0f2b03952e3) needs a second copy of the repo it can revert files
    inside, because the alternative — reverting in the live tree and putting it back — leaves
    the operator's copy in a state he did not make the first time the run crashes between the
    two acts (Law 6: his tree is his).

    WHY THIS IS A DOOR HERE AND NOT A ``subprocess.run`` AT THE CALL SITE, and it is the same
    reason as ``scratch_dir`` above: a worktree leaks in TWO places, and the second one is
    invisible. ``shutil.rmtree`` removes the directory and leaves the registration behind in
    ``.git/worktrees``, so ``git worktree list`` goes on naming a path that is not there —
    the leak with a clean-looking tree. A caller who remembers the directory is exactly the
    caller who forgets the registration, which is what makes this physics rather than advice.

    THE SWEEP IS ``git worktree remove --force`` FIRST, because that is the one act that does
    both halves; ``prune`` afterwards is the belt for the case where the directory went away
    by some other hand and ``remove`` therefore refuses. Neither raises: an exception escaping
    an atexit hook buries the proof's verdict under a teardown traceback (see ``_sweep``).
    """
    repo_root = Path(repo_root).resolve()
    parent = Path(tempfile.mkdtemp(prefix=prefix))
    wt = parent / "worktree"
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "worktree", "add", "--detach", "--quiet", str(wt), commit],
        capture_output=True, text=True)
    if proc.returncode != 0:
        shutil.rmtree(parent, ignore_errors=True)
        raise WorktreeUnavailable(
            f"scratch_worktree: git worktree add failed for commit {commit!r} in {repo_root}: "
            f"{(proc.stderr or proc.stdout).strip()}")
    atexit.register(_sweep_worktree, repo_root, wt, parent)
    return wt


class WorktreeUnavailable(RuntimeError):
    """git could not make the worktree — said out loud, never worked around silently."""


def _sweep_worktree(repo_root: Path, wt: Path, parent: Path) -> None:
    """Remove the worktree AND its registration, and SAY SO if either half cannot be done."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "worktree", "remove", "--force", str(wt)],
            capture_output=True, text=True)
        if proc.returncode != 0:
            # The directory may already be gone by another hand; prune is what clears the
            # registration in that case, and it is a no-op when there is nothing stale.
            subprocess.run(["git", "-C", str(repo_root), "worktree", "prune"],
                           capture_output=True, text=True)
    except OSError as e:
        print(f"scratch: could not remove worktree {wt}: {type(e).__name__}: {e}", file=sys.stderr)
    try:
        shutil.rmtree(parent)
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"scratch: could not remove {parent}: {type(e).__name__}: {e}", file=sys.stderr)
