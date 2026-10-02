"""Teeth for ticket e0f318650123 — the commit fans out to its subscribers.

MEASURED 2026-10-02: git runs exactly one installed ``.git/hooks/post-commit``, and the counting
block held it (``cairn-counting-block-door``), so a second component that wanted the commit had
no way to hear it except by polling HEAD on the beat — which is what codemother's
``groundloop/pulse.py`` did. The fan-out takes the installed hook and runs every component's own
tracked ``hooks/post-commit``, found by ``git ls-files`` (no master index), each once, and never
lets one subscriber's failure block the commit or silence another.

These teeth hold the fan-out's clauses, (1) and (3). Codemother's clauses, (2) and (4), are
proved at codemother's own address (RULE 1: a proof measures only its component). The names this
build adds (``fanout.subscribers``, ``fanout.fire``, ``fanout.verify_hook``) are looked up inside
each tooth, so a reverted build reds a tooth instead of breaking this file's import.
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
        "1": "test_every_tracked_subscriber_runs_once_and_the_fanout_skips_itself",
        "1b": "test_the_live_install_is_the_fanout_and_it_sees_both_subscribers",
        "3": "test_a_failing_subscriber_blocks_nothing_and_silences_no_one",
    },
}

_OWN_HOOK = "cairn/tools/post_commit/hooks/post-commit"


def _fanout():
    return importlib.import_module("cairn.tools.post_commit.fanout")


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                         env=git_env(), timeout=60)
    assert out.returncode == 0, f"git {args}: {out.stderr.strip()}"
    return out.stdout


def _subscriber_repo(prefix: str, *, failing: str = "b") -> tuple[Path, Path]:
    """A throwaway repo with three tracked subscribers (``failing`` exits 3), the fan-out's own
    hook path tracked beside them, and an untracked hooks/post-commit that must NOT run."""
    repo = Path(str(scratch_dir(prefix)))
    log = repo / "fanout-proof-ran.log"
    _git(repo, "init", "-q")
    for name in ("a", "b", "c"):
        hook = repo / name / "hooks" / "post-commit"
        hook.parent.mkdir(parents=True)
        tail = "exit 3" if name == failing else "exit 0"
        hook.write_text(f"#!/usr/bin/env bash\necho {name} >> {log}\n"
                        f"echo {name}-said-something >&2\n{tail}\n", encoding="utf-8")
    own = repo / _OWN_HOOK
    own.parent.mkdir(parents=True)
    own.write_text(f"#!/usr/bin/env bash\necho SELF >> {log}\nexit 0\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fanout proof fixture")
    stray = repo / "untracked" / "hooks" / "post-commit"
    stray.parent.mkdir(parents=True)
    stray.write_text(f"#!/usr/bin/env bash\necho STRAY >> {log}\n", encoding="utf-8")
    return repo, log


def test_every_tracked_subscriber_runs_once_and_the_fanout_skips_itself():
    fanout = _fanout()
    repo, log = _subscriber_repo("fanout-proof-every-subscriber-")
    found = [str(p) for p in fanout.subscribers(repo)]
    assert found == ["a/hooks/post-commit", "b/hooks/post-commit", "c/hooks/post-commit"], found
    results = fanout.fire(repo)
    ran = log.read_text(encoding="utf-8").split()
    assert sorted(ran) == ["a", "b", "c"], f"each tracked subscriber once, nothing else: {ran}"
    assert [r["subscriber"] for r in results] == found, results


def test_the_live_install_is_the_fanout_and_it_sees_both_subscribers():
    fanout = _fanout()
    got = fanout.verify_hook(_REPO)
    assert got["green"] is True, got
    body = Path(got["path"]).read_text(encoding="utf-8")
    assert fanout._MARK in body, f"the installed hook does not carry {fanout._MARK!r}"
    found = {str(p) for p in fanout.subscribers(_REPO)}
    for want in ("cairn/machines/counting_block/hooks/post-commit",
                 "cairn/devices/codemother/hooks/post-commit"):
        assert want in found, f"{want} is not a subscriber the fan-out sees: {sorted(found)}"
    assert _OWN_HOOK not in found, "the fan-out lists its own hook as a subscriber"
    cb = subprocess.run([sys.executable, "-m", "cairn.machines.counting_block", "verify-hook"],
                        capture_output=True, text=True, cwd=str(_REPO), timeout=120)
    assert cb.returncode == 0, f"counting_block verify-hook: {cb.stdout}{cb.stderr}"


def test_a_failing_subscriber_blocks_nothing_and_silences_no_one():
    fanout = _fanout()
    repo, log = _subscriber_repo("fanout-proof-failing-subscriber-", failing="a")
    results = {r["subscriber"]: r for r in fanout.fire(repo)}
    assert results["a/hooks/post-commit"]["exit"] == 3, results
    assert "a-said-something" in results["a/hooks/post-commit"]["stderr"], results
    assert sorted(log.read_text(encoding="utf-8").split()) == ["a", "b", "c"], \
        "the failing subscriber (run first) silenced the ones after it"
    log.unlink()
    cli = subprocess.run([sys.executable, "-m", "cairn.tools.post_commit", "fire",
                          "--repo", str(repo)],
                         capture_output=True, text=True, cwd=str(_REPO), timeout=120)
    assert cli.returncode == 0, f"the fan-out's exit is the commit's to ignore, and must be 0: " \
                                f"rc={cli.returncode} {cli.stderr[-300:]}"
    assert "a/hooks/post-commit" in cli.stdout + cli.stderr, "the refusal is not named"
    assert sorted(log.read_text(encoding="utf-8").split()) == ["a", "b", "c"]


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
