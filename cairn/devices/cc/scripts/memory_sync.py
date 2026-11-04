"""Keep CC's private memory repo in step across boxes (outline 12.3.5).

    memory_sync.py pull   # SessionStart: take what other CC instances wrote
    memory_sync.py push   # Stop: commit what this session wrote, push it

CC will not remember to commit its memory, so hooks do it. `push` commits only
when something changed and pushes in a detached child, so a turn never waits on
the network. A pull that cannot rebase cleanly is aborted, the local work kept,
and said loudly (Law 7) for CC to resolve by hand.
"""
import datetime, os, socket, subprocess, sys
from pathlib import Path

CLONE = Path(os.environ.get("CAIRN_CC_MEMORY_CLONE", Path.home() / "dev" / "src" / "cc-memory"))


def git(*args, check=False):
    return subprocess.run(["git", "-C", str(CLONE), *args], capture_output=True, text=True,
                          check=check, timeout=30)


def pull() -> int:
    r = git("pull", "-q", "--rebase", "--autostash")
    if r.returncode:
        git("rebase", "--abort")
        print(f"CC MEMORY SYNC: pull failed, local memory kept, resolve by hand in {CLONE}:\n"
              f"{r.stderr.strip()}", file=sys.stderr)
        return 0          # never block a session from opening
    ahead = git("rev-list", "--count", "@{u}..HEAD").stdout.strip()
    if ahead not in ("", "0"):
        p = git("push", "-q")
        if p.returncode:  # a detached push from the last Stop may have just landed
            git("fetch", "-q")
            ahead = git("rev-list", "--count", "@{u}..HEAD").stdout.strip()
        if p.returncode and ahead not in ("", "0"):
            print(f"CC MEMORY SYNC: {ahead} memory commit(s) not pushed from {CLONE}:\n"
                  f"{p.stderr.strip()}", file=sys.stderr)
    return 0


def push() -> int:
    if not git("status", "--porcelain").stdout.strip():
        return 0
    git("add", "-A")
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    git("commit", "-q", "-m", f"memory from {socket.gethostname()} {stamp}")
    subprocess.Popen(["git", "-C", str(CLONE), "push", "-q"], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    if not (CLONE / ".git").exists():
        sys.exit(0)       # this box has no clone yet: memory_link.py makes one
    sys.exit({"pull": pull, "push": push}[sys.argv[1]]())
