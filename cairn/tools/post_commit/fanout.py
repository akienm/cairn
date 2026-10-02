"""The commit fans out to its subscribers (ticket e0f318650123).

Git runs exactly one installed ``post-commit``. Until this tool, the counting block held it, so a
second component that wanted the commit could only poll HEAD on the beat. The fan-out takes the
installed hook and runs every component's own TRACKED ``hooks/post-commit`` — found by
``git ls-files``, no master index: a component declares its subscription by carrying the file.

Each subscriber runs once, with the repo root as its working directory. A subscriber's exit and
stderr are recorded and printed by name; none of them can block the commit (it has already
landed) or stop the ones after it. The fan-out holds no state of its own (Law 6: a tool has users).

THE HOST-SEAM PAIR IS COPIED IN SHAPE FROM ``cairn/machines/counting_block/hook.py`` (itself copied
from the tester's ``reseal.py``), never imported: ``hook_path`` through ``--git-common-dir``,
``install_hook`` refusing to clobber a hook not its own, ``verify_hook`` as a live read.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_SOURCE = Path(__file__).parent / "hooks" / "post-commit"
OWN_HOOK = "cairn/tools/post_commit/hooks/post-commit"
_MARK = "cairn-post-commit-fanout"
# The hook this one replaced. Taking it over is the migration this ticket IS, so it is the one
# foreign marker install_hook will overwrite; its body lives on as a subscriber.
_PREDECESSOR = "cairn-counting-block-door"
_STDERR_KEEP = 2000


def subscribers(repo: Path | str | None = None) -> list[Path]:
    """Every tracked ``*/hooks/post-commit`` but this tool's own, repo-relative, sorted."""
    base = Path(repo or REPO_ROOT)
    out = subprocess.run(["git", "-C", str(base), "ls-files", "-z", "--",
                          "*/hooks/post-commit"], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"git ls-files at {base}: {out.stderr.strip()}")
    return sorted(Path(p) for p in out.stdout.split("\0") if p and p != OWN_HOOK)


def fire(repo: Path | str | None = None, *, timeout_s: float = 600.0) -> list[dict]:
    """Run each subscriber once and return ``[{subscriber, exit, stderr}]`` in run order.

    Never raises for a subscriber: a non-zero exit, a timeout or a spawn failure is that
    subscriber's record, and the next one still runs."""
    base = Path(repo or REPO_ROOT)
    results = []
    for rel in subscribers(base):
        rec = {"subscriber": str(rel), "exit": None, "stderr": ""}
        try:
            proc = subprocess.run(["bash", str(base / rel)], cwd=str(base), capture_output=True,
                                  text=True, timeout=timeout_s)
            rec["exit"], rec["stderr"] = proc.returncode, proc.stderr[-_STDERR_KEEP:]
            if proc.stdout:
                print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        except subprocess.TimeoutExpired as exc:
            rec["exit"], rec["stderr"] = "timeout", f"no exit inside {timeout_s:.0f}s: {exc}"
        except OSError as exc:
            rec["exit"], rec["stderr"] = "unspawnable", f"{type(exc).__name__}: {exc}"
        results.append(rec)
    return results


def hook_path(root: Path | None = None) -> Path:
    """Where git will look for the hook — the SHARED hooks directory, from a worktree too."""
    base = Path(root or REPO_ROOT)
    proc = subprocess.run(["git", "-C", str(base), "rev-parse", "--path-format=absolute",
                           "--git-common-dir"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"not a git repository at {base}: {proc.stderr.strip()}")
    return Path(proc.stdout.strip()) / "hooks" / "post-commit"


def install_hook(root: Path | None = None) -> dict:
    """THE APPLY RECIPE — replayable; a second run is a no-op that says so. Refuses to clobber a
    hook that is neither this one nor the counting block's it replaces (Law 6)."""
    dest = hook_path(root)
    body = HOOK_SOURCE.read_text(encoding="utf-8")
    if dest.exists():
        existing = dest.read_text(encoding="utf-8", errors="replace")
        if _MARK not in existing and _PREDECESSOR not in existing:
            return {"installed": False, "path": str(dest), "why": (
                f"{dest} already exists and carries neither {_MARK!r} nor {_PREDECESSOR!r} — "
                f"it is somebody else's hook and this door will not overwrite it (Law 6). Make "
                f"it a subscriber (a tracked <component>/hooks/post-commit) and move it aside.")}
        if existing == body:
            return {"installed": False, "path": str(dest), "why": "already installed, unchanged"}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    os.chmod(dest, 0o755)
    return {"installed": True, "path": str(dest), "why": f"copied from {HOOK_SOURCE}"}


def verify_hook(root: Path | None = None) -> dict:
    """THE RE-RUNNABLE VERIFY — a live read of the host, because a host-seam's seal expires with
    nothing in git changing."""
    try:
        dest = hook_path(root)
    except RuntimeError as err:
        return {"green": False, "why": str(err)}
    if not dest.exists():
        return {"green": False, "path": str(dest), "why": (
            f"no hook at {dest} — run `python3 -m cairn.tools.post_commit install-hook`")}
    body = dest.read_text(encoding="utf-8", errors="replace")
    if _MARK not in body:
        return {"green": False, "path": str(dest),
                "why": f"a post-commit hook is installed at {dest} but it is not the fan-out "
                       f"(no {_MARK!r} marker)"}
    if not os.access(dest, os.X_OK):
        return {"green": False, "path": str(dest),
                "why": f"{dest} is not executable — git will skip it silently"}
    if body != HOOK_SOURCE.read_text(encoding="utf-8"):
        return {"green": False, "path": str(dest),
                "why": f"{dest} has DRIFTED from {HOOK_SOURCE} — reinstall to reconcile"}
    return {"green": True, "path": str(dest),
            "why": "installed, executable, and identical to the tracked source"}
