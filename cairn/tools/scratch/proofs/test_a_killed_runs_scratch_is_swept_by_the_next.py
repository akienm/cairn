"""Proof for ticket 4784351e4838 — a killed run's scratch is swept by the next run that asks for one.

MEASURED 2026-10-08: /tmp held 1068 entries (1.7G on a tmpfs, so RAM) — 254
``watch-receives-a-finding-*``, 112 ``ws-proof-roster-*``, 63 ``cairn-hollow-*`` worktree
parents among them — while a clean run of test_watch_receives_a_finding.py left the count at
254 before and 254 after. The atexit door holds for every run that EXITS; the leak is the runs
that are killed (the tester's timeout, bf3c16162827), which no exit hook can reach.

Three teeth, one per falsifier clause, each measured from OUTSIDE in real processes, because
"killed" and "the next run" exist nowhere else:
  (1) a scratch_dir made by a SIGKILLed process is gone once the next process under the same
      temp root has asked for a scratch_dir;
  (2) a scratch_worktree made by a SIGKILLed process is gone AND deregistered — the fixture
      repo's ``git worktree list`` no longer names it;
  (3) a LIVE process's scratch_dir, and an unmarked directory beside it, survive that call.

THE FIXTURE WORLD: every child runs with TMPDIR pointed at a scratch directory of this proof's
own, so the host /tmp is never the population a tooth reads, and the fixture repo is a ``git
init`` inside it. Tooth 3 is the guard (the old door also leaves a live dir alone); 1 and 2 red
against today's scratch.py, which sweeps nothing it did not make itself.

    python3 cairn/tools/scratch/proofs/test_a_killed_runs_scratch_is_swept_by_the_next.py
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402

PROVES = {
    "4784351e4838": {
        "1": "test_a_killed_runs_scratch_dir_is_gone_after_the_next_call",
        "2": "test_a_killed_runs_worktree_is_gone_and_deregistered_after_the_next_call",
        "3": "test_a_live_owners_dir_and_an_unmarked_dir_survive_the_next_call",
    },
}

_HEAD = "import sys; sys.path.insert(0, {repo!r})\nfrom cairn.tools.scratch.scratch import scratch_dir, scratch_worktree\n"


def _env(tmp: Path) -> dict:
    env = git_env()
    env["TMPDIR"] = str(tmp)
    return env


def _hold(tmp: Path, body: str) -> tuple[subprocess.Popen, Path]:
    """Start a child that makes what ``body`` makes, prints its path, and then waits forever."""
    src = _HEAD.format(repo=str(REPO)) + body + "\nprint(p, flush=True)\nimport time\ntime.sleep(600)\n"
    child = subprocess.Popen([sys.executable, "-c", src], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, env=_env(tmp))
    line = child.stdout.readline().strip()
    assert line, f"the holding child printed no path: {child.stderr.read() if child.poll() is not None else ''}"
    return child, Path(line)


def _kill(child: subprocess.Popen) -> None:
    child.send_signal(signal.SIGKILL)
    child.wait(timeout=30)


def _next_call(tmp: Path) -> None:
    """A fresh process under the same temp root asks for one scratch_dir and exits normally."""
    src = _HEAD.format(repo=str(REPO)) + "scratch_dir('fixture-sweep-next-caller-')\n"
    r = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True, env=_env(tmp), timeout=120)
    assert r.returncode == 0, f"the next caller failed: {r.stderr}"


def _fixture_repo(tmp: Path) -> Path:
    repo = tmp / "fixture-sweep-repo"
    repo.mkdir()
    for argv in (["init", "-q"], ["-c", "user.name=fixture", "-c", "user.email=fixture@invalid",
                                  "commit", "-q", "--allow-empty", "-m", "fixture"]):
        subprocess.run(["git", "-C", str(repo)] + argv, check=True, capture_output=True, env=git_env())
    return repo


def test_a_killed_runs_scratch_dir_is_gone_after_the_next_call():
    tmp = scratch_dir("scratch-sweep-killed-dir-world-")
    child, d = _hold(tmp, "p = scratch_dir('fixture-sweep-killed-dir-')\n(p / 'a_file').write_text('x')")
    _kill(child)
    assert d.is_dir(), f"the kill should have left {d} behind (atexit never fired) — the fixture measures nothing"
    _next_call(tmp)
    assert not d.exists(), f"a SIGKILLed run's scratch_dir outlived the next call: {d}"


def test_a_killed_runs_worktree_is_gone_and_deregistered_after_the_next_call():
    tmp = scratch_dir("scratch-sweep-killed-worktree-world-")
    repo = _fixture_repo(tmp)
    child, wt = _hold(tmp, f"p = scratch_worktree('HEAD', repo_root={str(repo)!r}, prefix='fixture-sweep-killed-wt-')")
    _kill(child)
    listed = lambda: subprocess.run(["git", "-C", str(repo), "worktree", "list", "--porcelain"],
                                    capture_output=True, text=True, env=git_env()).stdout
    assert wt.is_dir() and str(wt) in listed(), "the kill should have left the worktree registered and on disk"
    _next_call(tmp)
    assert not wt.parent.exists(), f"a SIGKILLed run's worktree parent outlived the next call: {wt.parent}"
    assert str(wt) not in listed(), f"the dead worktree is still registered:\n{listed()}"


def test_a_live_owners_dir_and_an_unmarked_dir_survive_the_next_call():
    tmp = scratch_dir("scratch-sweep-live-owner-world-")
    unmarked = tmp / "fixture-sweep-unmarked-not-a-scratch-name"
    unmarked.mkdir()
    child, d = _hold(tmp, "p = scratch_dir('fixture-sweep-live-owner-')")
    try:
        _next_call(tmp)
        assert d.is_dir(), f"a LIVE owner's scratch_dir was swept: {d}"
        assert unmarked.is_dir(), f"an unmarked directory was swept: {unmarked}"
    finally:
        _kill(child)


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
