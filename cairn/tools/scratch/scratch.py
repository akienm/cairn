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

A KILLED RUN IS SWEPT BY THE NEXT ONE (ticket 4784351e4838). A run killed with SIGKILL
fires no atexit hook — the tester's timeout kills that way — and on 2026-10-08 /tmp held
1068 entries (1.7G of tmpfs) while a clean run left the count unchanged: the leak was the
killed runs, not the exiting ones. So every scratch name carries its owner's pid namespace
and pid behind a fixed marker, and each process's FIRST scratch call removes the marked
entries whose owner is dead in its own namespace (a worktree is also deregistered). No
supervisor watches a directory; the next process to ask is the sweep. An entry from another
pid namespace is never judged by its pid, and entries made before the marker existed carry
no owner and are not this door's to judge.
"""

from __future__ import annotations

import atexit
import shutil
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


# THE MARK (ticket 4784351e4838): ``<prefix>scratch.<pid-namespace inode>-<pid>-<mkdtemp suffix>``.
# The name is the record — a tool holds no state of its own (Law 6).
_MARK = "scratch."
_NS = os.stat("/proc/self/ns/pid").st_ino
_OWNED = re.compile(r"scratch\.(\d+)-(\d+)-[a-z0-9_]{8}$")
_swept = False


class ScratchPath(type(Path())):
    """A scratch Path that still works as a with-block.

    Python 3.13 removed pathlib.Path.__enter__/__exit__ (since 3.9 they returned self and
    did nothing). 27 sealed with-sites in build_inspector's proofs hold a scratch path that
    way, so the door keeps the old contract. Entering removes nothing on exit: removal stays
    with the atexit sweep below, exactly as before.
    """

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None


def scratch_dir(prefix: str) -> Path:
    """A temp directory removed when this process exits. The caller writes no cleanup."""
    _sweep_once()
    d = ScratchPath(tempfile.mkdtemp(prefix=f"{prefix}{_MARK}{_NS}-{os.getpid()}-"))
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


# THE VARIABLES GIT EXPORTS INTO A HOOK, WHICH A CHILD MUST NOT INHERIT WHEN IT MEANS A
# DIFFERENT REPOSITORY THAN ITS CALLER DID. Each pins some part of "which repo, which index" to
# the invoking process's answer, and ``git -C <root>`` does NOT override them — GIT_DIR wins.
_GIT_LOCATION_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX",
                      "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                      "GIT_ALTERNATE_OBJECT_DIRECTORIES")


def git_env() -> dict:
    """The caller's environment with git's repo-location variables removed.

    MEASURED, NOT REASONED (2026-09-09). ``test_hollow.py``'s standing seal was found RED —
    nine teeth failed in 0.75s, every one of them a tooth that makes a worktree — and the
    record had been written by the pre-commit hook's ``cairn test --reseal``. Reproduced in
    one line: ``GIT_INDEX_FILE=.git/index pytest ...`` turns those teeth from green into
    ``WorktreeUnavailable`` in 0.12s. The hook runs the reseal door, the door runs proofs as
    subprocesses, and they inherit.

    WHAT GIT ACTUALLY EXPORTS, from a real commit against a scratch repo whose hook dumps
    ``env | grep ^GIT_``: ``GIT_INDEX_FILE=.git/index`` and ``GIT_PREFIX=``, plus the author
    fields. NOT ``GIT_DIR`` — and that mattered, because the first version of this tooth
    guessed ``GIT_DIR``, set it ABSOLUTE, and went green against the unfixed door. The
    RELATIVE path is the defect: it resolves against whatever directory the child is in. The
    rest of the tuple below is guarded anyway — a variable git does not export today is a
    variable another git, or another caller, still can.

    THE DAMAGE IS WORSE THAN A FAILED RUN, which is why the scrub is here rather than in the
    hook. The reseal door does four things with a red — replaces the standing record, bounds a
    repair to the proof's current bytes, opens a ladder, files a trouble — so a commit that
    happened to stage the right file REPLACED A GREEN SEAL WITH A RED ONE and demanded a
    repair to a proof that was never broken. That is a record of truth contradicting the
    measurement (Law 7), manufactured by the machinery built to protect it.

    AND THE FIRST DIAGNOSIS WAS WRONG, which is why this docstring names the experiment. The
    obvious reading was ``index.lock``: a commit is in flight, so git must be locked. Holding
    ``.git/index.lock`` and re-running the tooth passes in 0.17s — ``git worktree add`` never
    wanted that lock. The plausible cause and the real one differed, and only running it told
    them apart (Law 3).

    IT IS PUBLIC, AND THAT WAS MEASURED TOO. The first fix scrubbed only the three calls
    below, on the reasoning that this is the sole door to a worktree — true, and not enough.
    Under the same hook environment four of ``test_hollow.py``'s teeth still failed, and the
    one that named itself was ``test_a_proof_declaring_no_tooth...``: it asserted one hollow
    file and got NONE. The cause is ``hollow._restore``, a ``git -C <worktree> checkout --``
    that silently no-ops against the caller's index — so the PREVIOUS file stays reverted, the
    next file's teeth red for a reason that has nothing to do with it, and a file that really
    is hollow is reported ``ok``. **A hollow read as green is the exact failure the whole verb
    exists to catch** (Law 8: a false green gets leaned on by a peer), manufactured inside the
    catcher. So every git call in the tester takes this env, not only the ones that make
    worktrees — ``git -C <root>`` is not a defence anywhere, because GIT_DIR outranks it
    everywhere. A caller who remembers to scrub is exactly the caller who forgets, which is
    why the scrub is a named import rather than a convention.

    NOT EVERY GIT CALL WANTS THIS, and the line is worth stating because it is easy to over-
    apply. A call that means "the repository I am pointing at" scrubs; a call that means "the
    index my caller is committing" must NOT. ``reseal.staged_files`` is the second kind and is
    deliberately left alone: under ``git commit -a`` git writes a TEMPORARY index and points
    ``GIT_INDEX_FILE`` at it, so the hook's staged set lives there and nowhere else — scrubbing
    would read the pre-``-a`` index and reseal the wrong proofs.
    """
    return {k: v for k, v in os.environ.items() if k not in _GIT_LOCATION_VARS}


def bare_temp_reach(root: str | Path) -> list[str]:
    """Every live line under ``root``'s ``proofs/test_*.py`` that reaches the system temp
    directory bare — ``mkdtemp`` or ``gettempdir`` — as ``'<relpath>:<line>: <stripped line>'``.

    It names no caller and exempts nothing: a consumer that must reach bare (a control group
    showing bare still leaks) drops its own lines from the result, in its own proof, out loud.
    The scan is public so each component holds its own proofs to the door (RULE 1); its first
    copy lived inline in one proof (e038544a9b60, after 3581 leaked entries were swept), and
    b4d39f3610f3 moved it here.

    gettempdir is here because the FIRST version grepped only for mkdtemp and missed a real
    leak of a different spelling — 18 boot-log FILES from launchers/proofs/test_bootstrap.py,
    one per run. A scan narrower than its own defect is the hollow kind. Both reach the system
    temp dir; only the door may. The three sites that named a deliberately-NONEXISTENT path came
    through the door too, so there is no exemption to maintain and no judgement call about
    which reach is harmless."""
    root = Path(root)
    out = []
    for py in sorted(root.rglob("proofs/test_*.py")):
        if "__pycache__" in py.parts:
            continue
        for n, line in enumerate(py.read_text(errors="replace").splitlines(), 1):
            if not line.lstrip().startswith("#") and ("mkdtemp" in line or "gettempdir" in line):
                out.append(f"{py.relative_to(root)}:{n}: {line.strip()}")
    return out


def _owner_alive(pid: int) -> bool:
    """Is ``pid`` alive as read from this namespace — copied from isolation._pid_alive, not
    imported (RULE 1)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _sweep_dead_owners(tmp: str | None = None) -> list[str]:
    """Remove every marked scratch entry under the temp root whose owner is dead in THIS pid
    namespace, deregistering a worktree's registration too; return what was removed.

    Judges only what carries the mark and this namespace's inode: an unmarked entry, a live
    owner's entry and an entry from another namespace are never touched. Like ``_sweep``, it
    says so at the diagnostic surface and never raises.
    """
    root = Path(tmp or tempfile.gettempdir())
    try:
        entries = list(root.iterdir())
    except OSError:
        return []
    swept = []
    for entry in entries:
        try:
            m = _OWNED.search(entry.name)
            if not m or not entry.is_dir() or int(m.group(1)) != _NS:
                continue
            pid = int(m.group(2))
            if pid == os.getpid() or _owner_alive(pid):
                continue
            gitfile = entry / "worktree" / ".git"
            if gitfile.is_file():
                first = gitfile.read_text().splitlines()[0]
                if not first.startswith("gitdir:"):
                    raise ValueError(f"{gitfile} does not name a gitdir: {first!r}")
                gitdir = first[len("gitdir:"):].strip()
                shutil.rmtree(entry)
                subprocess.run(["git", "--git-dir", str(Path(gitdir).parents[1]), "worktree", "prune"],
                               capture_output=True, text=True, env=git_env())
            else:
                shutil.rmtree(entry)
            swept.append(str(entry))
        except (OSError, ValueError, IndexError) as e:
            print(f"scratch: could not sweep {entry}: {type(e).__name__}: {e}", file=sys.stderr)
    return swept


def _sweep_once() -> None:
    """Sweep dead owners at this process's first scratch call — no clock, no daemon."""
    global _swept
    if _swept:
        return
    _swept = True
    _sweep_dead_owners()


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
    _sweep_once()
    repo_root = Path(repo_root).resolve()
    parent = Path(tempfile.mkdtemp(prefix=f"{prefix}{_MARK}{_NS}-{os.getpid()}-"))
    wt = parent / "worktree"
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "worktree", "add", "--detach", "--quiet", str(wt), commit],
        capture_output=True, text=True, env=git_env())
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
            capture_output=True, text=True, env=git_env())
        if proc.returncode != 0:
            # The directory may already be gone by another hand; prune is what clears the
            # registration in that case, and it is a no-op when there is nothing stale.
            subprocess.run(["git", "-C", str(repo_root), "worktree", "prune"],
                           capture_output=True, text=True, env=git_env())
    except OSError as e:
        print(f"scratch: could not remove worktree {wt}: {type(e).__name__}: {e}", file=sys.stderr)
    try:
        shutil.rmtree(parent)
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"scratch: could not remove {parent}: {type(e).__name__}: {e}", file=sys.stderr)
