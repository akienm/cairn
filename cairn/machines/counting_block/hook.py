"""The counting block's host seam: the post-commit hook that fires the fold (ticket 5a4ec289bf15
D26, D27).

COPIED IN SHAPE FROM THE TESTER'S PAIR, NEVER IMPORTED. ``cairn/devices/tester/reseal.py``
(HOOK_SOURCE, _MARK, hook_path, install_hook, verify_hook) with
``cairn/devices/tester/hooks/pre-commit`` is the precedent; a machine importing a device is red
under machine_imports_no_device, so the shape is carried here and cited instead.
"""
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_SOURCE = Path(__file__).parent / "hooks" / "post-commit"
_MARK = "cairn-counting-block-door"


def hook_path(root: Path | None = None) -> Path:
    """Where git will look for the hook — resolved through ``--git-common-dir`` so it is the
    SHARED hooks directory from a worktree as well as from the main tree."""
    base = Path(root or REPO_ROOT)
    proc = subprocess.run(["git", "-C", str(base), "rev-parse", "--path-format=absolute",
                           "--git-common-dir"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"not a git repository at {base}: {proc.stderr.strip()}")
    return Path(proc.stdout.strip()) / "hooks" / "post-commit"


def install_hook(root: Path | None = None) -> dict:
    """THE APPLY RECIPE — replayable, and re-runnable without a different result. The hook body
    is a tracked file under this component; installing copies it, and a second run is a no-op
    that says so. REFUSES TO CLOBBER A HOOK THAT IS NOT OURS (Law 6)."""
    dest = hook_path(root)
    body = HOOK_SOURCE.read_text(encoding="utf-8")
    if dest.exists():
        existing = dest.read_text(encoding="utf-8", errors="replace")
        if _MARK not in existing:
            return {"installed": False, "path": str(dest), "why": (
                f"{dest} already exists and does not carry the {_MARK!r} marker — it is "
                f"somebody else's hook and this door will not overwrite it (Law 6). Merge "
                f"the body of {HOOK_SOURCE} into it by hand, or move it aside first.")}
        if existing == body:
            return {"installed": False, "path": str(dest), "why": "already installed, unchanged"}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    os.chmod(dest, 0o755)
    return {"installed": True, "path": str(dest), "why": f"copied from {HOOK_SOURCE}"}


def verify_hook(root: Path | None = None) -> dict:
    """THE RE-RUNNABLE VERIFY — a live read of the host, never a record of having installed it
    once, because a host-seam's seal expires with nothing in git changing."""
    try:
        dest = hook_path(root)
    except RuntimeError as err:
        return {"green": False, "why": str(err)}
    if not dest.exists():
        return {"green": False, "path": str(dest), "why": (
            f"no hook at {dest} — run `python3 -m cairn.machines.counting_block install-hook`")}
    body = dest.read_text(encoding="utf-8", errors="replace")
    if _MARK not in body:
        return {"green": False, "path": str(dest),
                "why": f"a post-commit hook is installed at {dest} but it is not this one "
                       f"(no {_MARK!r} marker)"}
    if not os.access(dest, os.X_OK):
        return {"green": False, "path": str(dest), "why": f"{dest} is not executable — git "
                                                          f"will skip it silently"}
    if body != HOOK_SOURCE.read_text(encoding="utf-8"):
        return {"green": False, "path": str(dest),
                "why": f"{dest} has DRIFTED from {HOOK_SOURCE} — reinstall to reconcile"}
    return {"green": True, "path": str(dest), "why": "installed, executable, and identical "
                                                     "to the tracked source"}
