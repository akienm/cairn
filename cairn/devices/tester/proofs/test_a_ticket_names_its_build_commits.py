"""Teeth for ticket 217c82fe7b57 — a ticket built before hex ids names its build commits.

MEASURED 2026-10-13: hollow finds a build only by ``git log --grep=<hex id>`` over the writes_to
files (and, with no journaled crossing, by subjects '<hex>: build'). Tickets built before hex ids
name neither — d48d54dccde6's commits name the old slug, 95f8c561e742's name nothing — so the
grep finds 0 commits and every such ticket is unsealable. The ticket's ``build_commits`` names
them; each named sha must resolve AND change a measured writes_to file, or the run refuses
naming the sha, so a wrong name reds instead of greening (Law 8).

Every fixture is a scratch repo whose build commit message names no ticket id.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.hollow import HollowUnmeasurable, build_anchor  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "217c82fe7b57": {
        "1": "test_no_named_build_commits_refuses_as_today",
        "2": "test_a_named_build_commit_anchors_at_its_parent",
        "3": "test_a_named_sha_that_changes_no_measured_file_refuses_naming_it",
        "4": "test_a_named_sha_that_does_not_resolve_refuses_naming_it",
    },
}

FIXTURE = "f1x7a4c40217"

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}


def _git(repo, *args, at=None):
    env = dict(_ENV)
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(crossings: list | None = None) -> tuple[Path, dict, dict]:
    """c0 lays down w.py; 'build' changes w.py under a subject naming no id; 'other' changes
    only o.py. ``crossings`` are journal entries (at, from, to, direction). Returns the repo,
    the roots, and {label: sha}."""
    tmp = scratch_dir("cairn-namedbuild-")
    repo, commons = tmp / "repo", tmp / "commons"
    (commons / "tickets").mkdir(parents=True)
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    shas = {}
    for at, label, path, body in [("2020-01-01T00:00:00", "c0", "w.py", "VALUE = 1\n"),
                                  ("2020-01-02T00:00:00", "build", "w.py", "VALUE = 2\n"),
                                  ("2020-01-03T00:00:00", "other", "o.py", "X = 1\n")]:
        (repo / path).write_text(body)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", f"saveslate boundary: {label}", at=at)
        shas[label] = _git(repo, "rev-parse", "HEAD").stdout.strip()
    entries = [{"ticket": FIXTURE, "direction": d, "actor": "fixture", "at": at,
                "from": frm, "to": to} for at, frm, to, d in (crossings or [])]
    (repo / "history.json").write_text(json.dumps({"entries": entries}))
    roots = {"repo": repo, "commons": commons, "instance": commons}
    return repo, roots, shas


def _anchor(ticket, repo, roots):
    return build_anchor(ticket, ["w.py"], roots=roots, repo_root=repo)


def test_no_named_build_commits_refuses_as_today():
    """No build_commits, no crossing, no commit naming the id: the refusal stands, unchanged."""
    repo, roots, c = _fixture()
    for ticket in ({"id": FIXTURE}, {"id": FIXTURE, "build_commits": []}):
        try:
            f = _anchor(ticket, repo, roots)
        except HollowUnmeasurable:
            continue
        raise AssertionError(f"anchored with nothing named: {f}")


def test_a_named_build_commit_anchors_at_its_parent():
    """build_commits=[the build sha]: with no crossing the anchor is its parent (c0); with a
    BUILDME journaled AFTER the build (the August shape: a fresh crossing over an old build)
    the anchor is still the build's parent, never the commit after the build."""
    repo, roots, c = _fixture()
    f = _anchor({"id": FIXTURE, "build_commits": [c["build"]]}, repo, roots)
    assert f["commit"] == c["c0"], (f, c)
    assert f["anchor_first_build"] == c["build"], (f, c)
    repo, roots, c = _fixture([("2020-01-04T00:00:00", "TICKETME", "BUILDME", "forward")])
    f = _anchor({"id": FIXTURE, "build_commits": [c["build"][:10]]}, repo, roots)
    assert f["commit"] == c["c0"], (f, c)
    assert f["anchor_first_build"] == c["build"], (f, c)


def test_a_named_sha_that_changes_no_measured_file_refuses_naming_it():
    """A named commit that resolves but changes no writes_to file is a wrong name: it reds."""
    repo, roots, c = _fixture()
    try:
        f = _anchor({"id": FIXTURE, "build_commits": [c["build"], c["other"]]}, repo, roots)
    except HollowUnmeasurable as why:
        assert c["other"][:12] in str(why), str(why)
        return
    raise AssertionError(f"anchored over a name that changes no measured file: {f}")


def test_a_named_sha_that_does_not_resolve_refuses_naming_it():
    """A named sha that resolves to no commit reds, naming it."""
    repo, roots, c = _fixture()
    bogus = "0123456789abcdef0123456789abcdef01234567"
    try:
        f = _anchor({"id": FIXTURE, "build_commits": [bogus]}, repo, roots)
    except HollowUnmeasurable as why:
        assert bogus[:12] in str(why), str(why)
        return
    raise AssertionError(f"anchored over a name that does not resolve: {f}")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
