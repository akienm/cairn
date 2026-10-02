"""Teeth for ticket e0f318650123 at codemother's address — a commit reaches the watcher as an event.

MEASURED 2026-10-02: codemother heard about commits only by ``groundloop/pulse.py`` reading git
HEAD on every beat and diffing it against ``last_seen_head.json`` — the one tracked
``*/groundloop/*.py`` that reads HEAD. The commit is the event; the beat is not. So codemother's
own tracked ``hooks/post-commit`` (run by the fan-out at ``cairn/tools/post_commit``) reads the
commit and posts it to her own ``commit`` verb through her bus, and the poller is gone.

These teeth hold clauses (2) and (4). The fan-out's clauses are proved at the tool's address
(RULE 1). ``post_commit`` is imported inside each tooth, so a reverted build reds a tooth instead
of breaking this file's import.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402

PROVES = {
    "e0f318650123": {
        "2": "test_a_commit_posts_one_commit_envelope_and_flushes_it",
        "2b": "test_the_subscriber_reads_the_commit_it_was_fired_for",
        "2c": "test_the_tracked_hook_runs_the_subscriber_and_never_blocks",
        "4": "test_nothing_reads_git_head_on_the_beat",
    },
}

_CM = _REPO / "cairn" / "devices" / "codemother"


def _post_commit():
    return importlib.import_module("cairn.devices.codemother.post_commit")


class _StubBus:
    def __init__(self):
        self.posts, self.flushed_after = [], None

    def post(self, **kw):
        self.posts.append(kw)
        return {"id": "stub"}

    def flush(self):
        self.flushed_after = len(self.posts)


def test_a_commit_posts_one_commit_envelope_and_flushes_it():
    bus = _StubBus()
    _post_commit().announce(bus, commit="abc123", files=["cairn/x.py", "cairn/y.py"],
                            message="a subject line")
    assert len(bus.posts) == 1, bus.posts
    env = bus.posts[0]
    assert env["to"] == "codemother" and env["verb"] == "commit", env
    assert env["channel"] == "personal" and env["why"], env
    assert env["body"] == {"hash": "abc123", "files": ["cairn/x.py", "cairn/y.py"],
                           "message": "a subject line"}, env["body"]
    assert bus.flushed_after == 1, "the ring was not flushed after the post — the envelope " \
                                   "would die with the hook's process"


def test_the_subscriber_reads_the_commit_it_was_fired_for():
    repo = Path(str(scratch_dir("codemother-post-commit-proof-repo-")))
    env = git_env()

    def git(*a):
        out = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True,
                             env=env, timeout=60)
        assert out.returncode == 0, out.stderr
        return out.stdout.strip()

    git("init", "-q")
    (repo / "first.txt").write_text("1\n")
    git("add", "-A"); git("commit", "-q", "-m", "first")
    (repo / "sub").mkdir()
    (repo / "sub" / "second.txt").write_text("2\n")
    (repo / "first.txt").write_text("1b\n")
    git("add", "-A"); git("commit", "-q", "-m", "the second commit\n\nwith a body")
    got = _post_commit().read_commit(repo)
    assert got == {"hash": git("rev-parse", "HEAD"),
                   "files": ["first.txt", "sub/second.txt"],
                   "message": "the second commit"}, got


def test_the_tracked_hook_runs_the_subscriber_and_never_blocks():
    hook = _CM / "hooks" / "post-commit"
    assert hook.is_file(), f"no subscriber at {hook}"
    tracked = subprocess.run(["git", "-C", str(_REPO), "ls-files", "--error-unmatch",
                              str(hook.relative_to(_REPO))], capture_output=True, text=True)
    assert tracked.returncode == 0, "the subscriber is not tracked, so the fan-out cannot see it"
    src = hook.read_text(encoding="utf-8")
    assert "-m cairn.devices.codemother.post_commit" in src, "the hook does not run the subscriber"
    lines = [ln.strip() for ln in src.splitlines() if ln.strip()]
    assert lines[-1] == "exit 0", f"the hook's last word is {lines[-1]!r}, not exit 0"


def test_nothing_reads_git_head_on_the_beat():
    pulse = _CM / "groundloop" / "pulse.py"
    assert not pulse.exists(), f"{pulse} still polls HEAD on the beat"
    files = subprocess.run(["git", "-C", str(_REPO), "ls-files", "*/groundloop/*.py"],
                           capture_output=True, text=True, timeout=60).stdout.split()
    readers = [f for f in files if (_REPO / f).is_file() and any(
        w in (_REPO / f).read_text(encoding="utf-8", errors="replace")
        for w in ("rev-parse", "git log", "\"HEAD\"", "'HEAD'"))]
    assert readers == [], f"a beat-side module still reads git HEAD: {readers}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
