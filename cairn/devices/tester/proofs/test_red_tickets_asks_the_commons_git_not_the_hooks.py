"""Proof for ticket b0bb9743a5f4: the tester's caster asks the commons' git, never the hook's.

Measured 2026-11-15 by akienasus_cc_0 on the Dell: every land_ours held reseal hit "COULD NOT
RUN" with "unable to read 94b599b2c33f" (q57 on 1919, q62 on 8d69). 94b599b2c33f is cairn's
README.md blob, at stage 0 of cairn's index, and no commons object. The reseal runs under a
git hook's environment and keeps GIT_INDEX_FILE for its own question (reseal.py, ticket
ca9d380fe9d6). red_tickets._git handed that inherited environment to
``git -C <commons> diff --cached``, so the commons' object store was read against cairn's index
and failed at the first cairn-only blob. Now red_tickets drops every GIT_* from the environment
of each git it runs, and of the outline check it fires, as reseal's _commits_touching does.

  1. _staged(commons) under another repo's GIT_INDEX_FILE returns the commons' own staged list;
  2. ticket_what_is_new under a hook's GIT_INDEX_FILE, GIT_DIR and GIT_WORK_TREE commits the cast
     into the commons, and the other repo's index and HEAD are untouched;
  3. the outline check the caster fires sees no GIT_* in its environment.

The world: a scratch "hook" repo whose index holds a blob the commons has never seen; a scratch
repo with one red proof and an outline; a scratch commons in git with the live store charter.
The reader is a fake claude that records the GIT_* names in its environment.

    bin/cairn test cairn/devices/tester/proofs/test_red_tickets_asks_the_commons_git_not_the_hooks.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"b0bb9743a5f4": {
    "1": "test_staged_under_a_foreign_index_lists_the_commons_own",
    "2": "test_a_cast_under_a_hooks_env_commits_into_the_commons",
    "3": "test_the_outline_check_sees_no_hook_env"}}

PROOF_TIMEOUT_S = 600

RED = "cairn/a/proofs/test_one.py"
OUTLINE = "1 Cairn\n  1.1 the tester\n"

_FAKE = r'''#!/usr/bin/env python3
"""testing: a fake claude reader for ticket b0bb9743a5f4. Records the GIT_* names it was handed."""
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.stdin.read()
with open(os.path.join(here, "git_env"), "a") as f:
    f.write(json.dumps(sorted(k for k in os.environ if k.startswith("GIT_"))) + "\n")
print(json.dumps({"is_error": False, "structured_output": {"touches": [], "conflicts": []}}))
'''


def _git(where: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    got = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True, env=env)
    assert got.returncode == 0, (args, got.stderr)
    return got.stdout.strip()


def _world(tag: str, monkeypatch) -> types.SimpleNamespace:
    from cairn.devices.tester import red_tickets
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    top = Path(scratch_dir(f"testing-b0bb-{tag}-"))
    hook, repo, commons, reader = top / "hook", top / "repo", top / "CairnCommons", top / "reader"
    hook.mkdir()
    (hook / "README.md").write_text("testing: a blob only the hook repo holds\n", encoding="utf-8")
    for cmd in (["init", "-q"], ["config", "user.name", "testing"],
                ["config", "user.email", "testing@invalid"], ["add", "-A"],
                ["commit", "-q", "-m", "testing: the hook repo"]):
        _git(hook, *cmd)
    (repo / "cairn" / "a" / "proofs").mkdir(parents=True)
    (repo / "cairn/devices/cairn/requirements").mkdir(parents=True)
    (repo / "cairn/devices/cairn/requirements" / "00-outline.md").write_text(OUTLINE, encoding="utf-8")
    (repo / "cairn" / "a" / "intention+why.json").write_text(json.dumps({"component": "a"}), encoding="utf-8")
    (repo / RED).write_text('"""testing: a proof that reds."""\nraise SystemExit(1)\n', encoding="utf-8")
    for cmd in (["init", "-q"], ["add", "-A"]):
        _git(repo, *cmd)
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    live = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    shutil.copyfile(live, tickets / "_charter+why.json")
    for cmd in (["init", "-q"], ["config", "user.name", "testing"],
                ["config", "user.email", "testing@invalid"], ["add", "-A"],
                ["commit", "-q", "-m", "testing: the store charter"]):
        _git(commons, *cmd)
    reader.mkdir()
    fake = reader / "claude"
    fake.write_text(_FAKE, encoding="utf-8")
    fake.chmod(0o755)
    raiser = {"repo": top / "world", "commons": top / "world", "instance": top / "world"}
    monkeypatch.setattr(red_tickets, "ROOTS", {"repo": repo, "tickets": tickets, "commons": commons,
                                               "berths": top / "berths", "trace": top / "trace",
                                               "raiser": raiser, "claude": fake})
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": repo})
    from cairn.tools.base import transitions
    monkeypatch.setenv(transitions.PROOF_ENV, "testing-b0bb9743a5f4")
    return types.SimpleNamespace(top=top, hook=hook, repo=repo, commons=commons, reader=reader)


def _hook_env(w, monkeypatch, full: bool) -> None:
    """What a pre-commit hook in the hook repo hands its children."""
    monkeypatch.setenv("GIT_INDEX_FILE", str(w.hook / ".git" / "index"))
    if full:
        monkeypatch.setenv("GIT_DIR", str(w.hook / ".git"))
        monkeypatch.setenv("GIT_WORK_TREE", str(w.hook))


def _restore():
    from cairn.tools.artifact import artifact as A
    A.set_diagnostic_roots(None)


def test_staged_under_a_foreign_index_lists_the_commons_own(monkeypatch):
    from cairn.devices.tester import red_tickets
    w = _world("staged", monkeypatch)
    try:
        (w.commons / "mine.txt").write_text("testing: staged in the commons\n", encoding="utf-8")
        _git(w.commons, "add", "--", "mine.txt")
        _hook_env(w, monkeypatch, full=False)
        assert red_tickets._staged(w.commons) == ["mine.txt"]
    finally:
        _restore()


def test_a_cast_under_a_hooks_env_commits_into_the_commons(monkeypatch):
    from cairn.devices.tester import red_tickets
    w = _world("cast", monkeypatch)
    try:
        before = _git(w.commons, "rev-parse", "HEAD")
        hook_head = _git(w.hook, "rev-parse", "HEAD")
        hook_index = (w.hook / ".git" / "index").read_bytes()
        _hook_env(w, monkeypatch, full=True)
        plans = red_tickets.ticket_what_is_new([{"proof": RED, "verdict": "red", "teeth_red": ["test_it"]}])
        assert len(plans) == 1, plans
        assert len(_git(w.commons, "rev-list", f"{before}..HEAD").split()) == 1
        files = set(_git(w.commons, "diff", "--name-only", before, "HEAD").split())
        assert plans[0].resolve().relative_to(w.commons.resolve()).as_posix() in files, files
        assert _git(w.commons, "status", "--porcelain", "--untracked-files=all") == ""
        assert _git(w.hook, "rev-parse", "HEAD") == hook_head, "the cast committed into the hook's repo"
        assert (w.hook / ".git" / "index").read_bytes() == hook_index, "the cast staged into the hook's index"
    finally:
        _restore()


def test_the_outline_check_sees_no_hook_env(monkeypatch):
    from cairn.devices.tester import red_tickets
    w = _world("outline", monkeypatch)
    try:
        _hook_env(w, monkeypatch, full=True)
        red_tickets.ticket_what_is_new([{"proof": RED, "verdict": "red", "teeth_red": ["test_it"]}])
        seen = (w.reader / "git_env").read_text().splitlines() if (w.reader / "git_env").exists() else []
        assert seen, "the outline check's reader never ran"
        assert all(json.loads(line) == [] for line in seen), seen
    finally:
        _restore()


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
