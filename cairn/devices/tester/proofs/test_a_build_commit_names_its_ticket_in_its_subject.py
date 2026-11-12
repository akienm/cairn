"""Teeth for ticket 38a790293259 — a build commit names its ticket in its subject.

MEASURED 2026-11-12: the hollow prediction for 96f71a89a0fa read its charters unseen. The anchor
was 2cc799a6, because commit 0115dfff (a scrub, 2026-09-09) names 96f71a89a0fa only in
its BODY and touched a charter the ticket later rewrote. ``_build_commits`` grepped the whole
message, so a passing mention counted as the build, and the reading reverted two months of other
work instead of this build. Over 751 cast tickets, 55 had a body-only mention before every
subject mention; 54 of them were passing mentions.

THE RULE THESE TEETH HOLD. A commit is the ticket's build only when its subject names the id.
A body-only mention never moves the anchor. A ticket's ``build_commits`` (ticket 217c82fe7b57)
stays the escape for a build whose subject names no id.

Every fixture is a scratch repo with no journaled crossing, so the anchor comes from the build
commits alone (rule 'first-build-commit-no-crossing').
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "38a790293259": {
        "1": "test_a_body_only_mention_does_not_move_the_anchor",
        "2": "test_a_subject_mention_anchors_at_its_parent",
        "3": "test_a_named_build_commit_with_no_id_in_its_subject_still_anchors",
    },
}

FIXTURE = "f1x7a4c4038a"

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}


def _git(repo, *args, at=None):
    env = dict(_ENV)
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(commits: list) -> tuple[Path, dict, dict]:
    """``commits`` is [(label, value, subject, body)], oldest first. Each writes w.py with
    VALUE = value and commits under that subject and body. Returns the repo, the roots, and
    {label: sha}."""
    tmp = scratch_dir("cairn-subjectbuild-")
    repo, commons = tmp / "repo", tmp / "commons"
    (commons / "tickets").mkdir(parents=True)
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "history.json").write_text(json.dumps({"entries": []}))
    shas = {}
    for day, (label, value, subject, body) in enumerate(commits, start=1):
        (repo / "w.py").write_text(f"VALUE = {value}\n")
        _git(repo, "add", "-A")
        msg = subject + (f"\n\n{body}" if body else "")
        _git(repo, "commit", "-qm", msg, at=f"2020-01-{day:02d}T00:00:00")
        shas[label] = _git(repo, "rev-parse", "HEAD").stdout.strip()
    roots = {"repo": repo, "commons": commons, "instance": commons}
    return repo, roots, shas


def _anchor(ticket, repo, roots):
    from cairn.devices.tester.hollow import build_anchor
    return build_anchor(ticket, ["w.py"], roots=roots, repo_root=repo)


def _passing_mention_then_build():
    """0115dfff's shape: c0, then an unrelated commit naming the ticket in its body and
    changing a writes_to file, then the real build naming it in its subject."""
    return _fixture([
        ("c0", 1, "lay down w.py", ""),
        ("scrub", 1.5, "scrub: 9 stale sites", f"Also touches w.py for ticket {FIXTURE}."),
        ("build", 2, f"{FIXTURE}: build", ""),
    ])


def test_a_body_only_mention_does_not_move_the_anchor():
    """The scrub names the ticket only in its body: the anchor is the build's parent (the
    scrub), never c0, and the scrub is not the first build commit."""
    repo, roots, c = _passing_mention_then_build()
    f = _anchor({"id": FIXTURE}, repo, roots)
    assert f["commit"] == c["scrub"], ("a body-only mention moved the anchor", f, c)
    assert f["anchor_first_build"] == c["build"], (f, c)


def test_a_subject_mention_anchors_at_its_parent():
    """A build naming the ticket in its subject anchors at its parent, as before; a later
    commit naming it in its subject joins the build and moves nothing."""
    repo, roots, c = _fixture([
        ("c0", 1, "lay down w.py", ""),
        ("build", 2, f"{FIXTURE}: build", ""),
        ("fix", 3, f"{FIXTURE}: FIXME 1 — the repair", ""),
    ])
    f = _anchor({"id": FIXTURE}, repo, roots)
    assert f["commit"] == c["c0"], (f, c)
    assert f["anchor_first_build"] == c["build"], (f, c)


def test_a_named_build_commit_with_no_id_in_its_subject_still_anchors():
    """The escape holds: a build whose subject names no id (the ticket in its body only) is
    still the build when the ticket's build_commits names it."""
    repo, roots, c = _fixture([
        ("c0", 1, "lay down w.py", ""),
        ("build", 2, "a-gate-is-a-class: the build under its slug", f"Ticket {FIXTURE}."),
        ("other", 3, "saveslate boundary: auto-commit", ""),
    ])
    f = _anchor({"id": FIXTURE, "build_commits": [c["build"]]}, repo, roots)
    assert f["commit"] == c["c0"], (f, c)
    assert f["anchor_first_build"] == c["build"], (f, c)


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
