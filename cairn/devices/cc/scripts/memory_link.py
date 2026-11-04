"""Link Claude Code's memory folders to CC's private memory repo (outline 12.3.5).

Claude Code keeps memory per launch folder, at
~/.claude/projects/<slug of the folder>/memory. CC writes there by habit, so each
of those paths becomes a link to one clone of the private repo: every launch
folder, on every box, reads and writes the same memory.

    python3 memory_link.py [--repo URL] [--clone DIR] [LAUNCH_FOLDER ...]

Launch folders default to the home folder and the cairn repo. A real (unlinked)
memory folder that already exists is only replaced when every file in it is
already in the clone, byte for byte; otherwise it refuses and names the files.
Linux/macOS: a symlink. Windows: a directory junction (no admin needed).
"""
import argparse, filecmp, os, re, shutil, subprocess, sys
from pathlib import Path

HOME = Path.home()
REPO = "https://github.com/akienm/cc-memory.git"
CLONE = HOME / "dev" / "src" / "cc-memory"
DEFAULT_LAUNCH = [HOME, HOME / "dev" / "src" / "cairn"]


def slug(folder: Path) -> str:
    """Claude Code's project-folder name: every non-alphanumeric becomes '-'."""
    return re.sub(r"[^A-Za-z0-9-]", "-", str(folder.resolve()))


def is_link(p: Path) -> bool:
    if p.is_symlink():
        return True
    if os.name == "nt" and p.exists():
        try:
            return bool(os.readlink(p))      # junctions read back on 3.8+
        except OSError:
            return False
    return False


def make_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       check=True, stdout=subprocess.DEVNULL)
    else:
        link.symlink_to(target, target_is_directory=True)


def not_in_clone(folder: Path, clone: Path) -> list[str]:
    missing = []
    for f in folder.rglob("*"):
        if f.is_file():
            twin = clone / f.relative_to(folder)
            if not twin.is_file() or not filecmp.cmp(f, twin, shallow=False):
                missing.append(str(f.relative_to(folder)))
    return missing


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--clone", type=Path, default=CLONE)
    ap.add_argument("launch", nargs="*", type=Path)
    a = ap.parse_args()
    clone = a.clone.resolve()
    if not (clone / ".git").exists():
        subprocess.run(["git", "clone", "-q", a.repo, str(clone)], check=True)
    bad = 0
    for folder in a.launch or DEFAULT_LAUNCH:
        mem = HOME / ".claude" / "projects" / slug(folder) / "memory"
        if is_link(mem):
            print(f"linked already  {mem} -> {os.readlink(mem)}")
            continue
        if mem.exists():
            missing = not_in_clone(mem, clone)
            if missing:
                print(f"REFUSED  {mem} holds {len(missing)} file(s) the clone lacks: "
                      f"{', '.join(missing[:10])}", file=sys.stderr)
                bad += 1
                continue
            shutil.rmtree(mem)
        mem.parent.mkdir(parents=True, exist_ok=True)
        make_link(mem, clone)
        print(f"linked  {mem} -> {clone}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
