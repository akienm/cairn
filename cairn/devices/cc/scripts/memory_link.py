"""Link Claude Code's memory folders to CC's private memory repo (outline 12.3.5).

Claude Code keeps memory per launch folder, at
~/.claude/projects/<slug of the folder>/memory. CC writes there by habit, so each
of those paths becomes a link to one clone of the private repo: every launch
folder, on every box, reads and writes the same memory.

    python memory_link.py [--repo URL] [--clone DIR] [--no-hooks] [--quiet] [LAUNCH_FOLDER ...]

`cairn superclaude` runs this with --quiet for the folder it was launched in,
before it starts Claude Code, so every repo on every box gets the same memory and
a new box sets itself up the first time it is used. --quiet prints only what
needs a hand (a refusal, a failed clone); the launcher hands that to CC.

One command per box: clones the repo, links every launch folder, and installs
the two sync hooks in ~/.claude/settings.json. Launch folders default to the home
folder and the cairn repo this script sits in. The hooks name the exact Python
that ran this and this script's absolute path, in forward slashes (Windows
Python, cmd and Git Bash all accept them), so nothing depends on `python3` being
on PATH or on where cairn lives. Re-running replaces its own hook entries. A real (unlinked)
memory folder that already exists is only replaced when every file in it is
already in the clone, byte for byte; otherwise it refuses and names the files.
Linux/macOS: a symlink. Windows: a directory junction (no admin needed).

Nothing is written from or for a transient tree (ticket 089ad920fcc5). Under the
system temp folder (CAIRN_CC_MEMORY_TRANSIENT_ROOT overrides it), a script copy
installs no hooks and a launch folder gets no link. Measured 2026-11-05: a proof
launched superclaude from a hollow worktree under /tmp with the live HOME. The
Stop hook then named a memory_sync.py that was deleted with the worktree, and every
session's stop failed. The guard sits here, at the writer, so no caller has to
remember it.
"""
import argparse, filecmp, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HOME = Path.home()
REPO = "https://github.com/akienm/cc-memory.git"
CLONE = HOME / "dev" / "src" / "cc-memory"
HERE = Path(__file__).resolve().parent
CAIRN = HERE.parents[3]                  # <cairn>/cairn/devices/cc/scripts
DEFAULT_LAUNCH = [HOME, CAIRN]
SETTINGS = HOME / ".claude" / "settings.json"
SYNC = HERE / "memory_sync.py"


def install_hooks(clone: Path) -> bool:
    d = json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}
    hooks = d.setdefault("hooks", {})
    base = f'"{Path(sys.executable).as_posix()}" "{SYNC.as_posix()}"'
    for event, verb in (("SessionStart", "pull"), ("Stop", "push")):
        kept = [h for h in hooks.get(event, [])
                if not any("memory_sync.py" in x.get("command", "") for x in h.get("hooks", []))]
        kept.append({"hooks": [{"type": "command", "timeout": 40,
                                "command": f'{base} {verb} "{clone.as_posix()}"'}]})
        hooks[event] = kept
    text = json.dumps(d, indent=2) + "\n"
    if SETTINGS.exists() and SETTINGS.read_text() == text:
        return False
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(text)
    return True


def transient_root() -> Path:
    return Path(os.environ.get("CAIRN_CC_MEMORY_TRANSIENT_ROOT") or tempfile.gettempdir()).resolve()


def is_transient(p: Path) -> bool:
    root, p = transient_root(), p.resolve()
    return p == root or root in p.parents


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
    ap.add_argument("--no-hooks", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("launch", nargs="*", type=Path)
    a = ap.parse_args()
    say = (lambda *_: None) if a.quiet else print
    clone = a.clone.resolve()
    if not (clone / ".git").exists():
        # Never prompt: this runs inside the launcher, and a credential dialog nobody
        # expects blocks the launch (measured 11-04: ksshaskpass waited forever).
        # Stored credentials (gh, Git Credential Manager) still answer; else it fails fast.
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo",
               "SSH_ASKPASS": "echo", "GCM_INTERACTIVE": "never"}
        try:
            r = subprocess.run(["git", "clone", "-q", a.repo, str(clone)], capture_output=True,
                               text=True, env=env, stdin=subprocess.DEVNULL, timeout=120)
        except subprocess.TimeoutExpired as e:
            r = subprocess.CompletedProcess(e.cmd, 1, "", "timed out after 120 s")
        if r.returncode:
            print(f"CC MEMORY: could not clone {a.repo} to {clone}, so this session has only "
                  f"this folder's own memory (GitHub credentials missing? `gh auth login`, "
                  f"then relaunch): {r.stderr.strip()}", file=sys.stderr)
            return 1
        say(f"cloned  {a.repo} -> {clone}")
    bad = 0
    for folder in a.launch or DEFAULT_LAUNCH:
        if is_transient(folder):
            say(f"skipped  {folder}: under the transient root {transient_root()}, nothing linked")
            continue
        mem = HOME / ".claude" / "projects" / slug(folder) / "memory"
        if is_link(mem):
            say(f"linked already  {mem} -> {os.readlink(mem)}")
            continue
        if mem.exists():
            missing = not_in_clone(mem, clone)
            if missing:
                print(f"CC MEMORY: REFUSED to link {mem}: it holds {len(missing)} file(s) the "
                      f"clone {clone} lacks ({', '.join(missing[:10])}). Fold them into the "
                      f"clone, then run {Path(__file__).as_posix()} again.", file=sys.stderr)
                bad += 1
                continue
            shutil.rmtree(mem)
        mem.parent.mkdir(parents=True, exist_ok=True)
        make_link(mem, clone)
        say(f"linked  {mem} -> {clone}")
    if not a.no_hooks and is_transient(HERE):
        say(f"hooks  skipped: this script sits under the transient root {transient_root()}")
    elif not a.no_hooks and install_hooks(clone):
        say(f"hooks  {SETTINGS}: SessionStart pull, Stop push")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
