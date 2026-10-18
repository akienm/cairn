"""Teeth for ticket 5e1b73029444 — a named build commit is read against where its files live now.

MEASURED 2026-10-13 on 87a7f1c7ae21: the chart names cairn/tools/base/bus_client.py, which moved
to cairn/tools/bus_client/bus_client.py before the build, so the correct build_commits
[18e1923d, 3e0a9683] was refused ("changes no measured writes_to file"). Without them hollow
anchored at 973daf6f, AFTER the build, and its 'ok' measured drift, not the build. The named-
commit check now reads the same move map the revert loop follows (``moved_to``): a commit is
accepted when it changed a charted file under its charted path OR where it lives now, and a
commit touching neither still refuses by name (Law 8).

Every fixture is a scratch repo whose move is a real ``git mv`` commit.
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
    "5e1b73029444": {
        "1": "test_a_build_on_the_moved_file_anchors_at_its_parent",
        "2": "test_a_commit_touching_neither_path_still_refuses_naming_it",
        "3": "test_a_commit_on_the_charted_path_is_still_accepted",
        "4": "test_the_live_87a7_build_anchors_at_its_parent",
    },
}

FIXTURE = "f1x75e1b7302"

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}

_BODY = "".join(f"LINE_{i} = {i}\n" for i in range(40))   # long enough for git to see a rename


def _git(repo, *args, at=None):
    env = dict(_ENV)
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture() -> tuple[Path, dict, dict]:
    """c0 lays down pkg_a/w.py; 'pre' changes it at its charted path; 'move' is a git mv to
    pkg_b/w.py; 'build' changes the moved file; 'other' changes only o.py. Subjects name no id.
    Returns the repo, the roots, and {label: sha}."""
    tmp = scratch_dir("cairn-namedmove-")
    repo, commons = tmp / "repo", tmp / "commons"
    (commons / "tickets").mkdir(parents=True)
    (repo / "pkg_a").mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    shas = {}

    def commit(label, at):
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", f"saveslate boundary: {label}", at=at)
        shas[label] = _git(repo, "rev-parse", "HEAD").stdout.strip()

    (repo / "pkg_a" / "w.py").write_text(_BODY)
    commit("c0", "2020-01-01T00:00:00")
    (repo / "pkg_a" / "w.py").write_text(_BODY + "PRE = 1\n")
    commit("pre", "2020-01-02T00:00:00")
    (repo / "pkg_b").mkdir()
    _git(repo, "mv", "pkg_a/w.py", "pkg_b/w.py")
    commit("move", "2020-01-03T00:00:00")
    (repo / "pkg_b" / "w.py").write_text(_BODY + "PRE = 1\nBUILT = 2\n")
    commit("build", "2020-01-04T00:00:00")
    (repo / "o.py").write_text("X = 1\n")
    commit("other", "2020-01-05T00:00:00")
    (repo / "history.json").write_text(json.dumps({"entries": []}))
    roots = {"repo": repo, "commons": commons, "instance": commons}
    return repo, roots, shas


def _anchor(ticket, repo, roots):
    """The chart names the file where it stood BEFORE the move — the 87a7 shape."""
    return build_anchor(ticket, ["pkg_a/w.py"], roots=roots, repo_root=repo)


def test_a_build_on_the_moved_file_anchors_at_its_parent():
    """Clause 1: build_commits names a commit that changed only the moved-to path; the anchor
    is that commit's parent, never a refusal."""
    repo, roots, c = _fixture()
    try:
        f = _anchor({"id": FIXTURE, "build_commits": [c["build"]]}, repo, roots)
    except HollowUnmeasurable as why:
        raise AssertionError(f"a build on the moved file was refused: {why}")
    assert f["commit"] == c["move"], (f, c)
    assert f["anchor_first_build"] == c["build"], (f, c)


def test_a_commit_touching_neither_path_still_refuses_naming_it():
    """Clause 2: a named commit that changes neither the charted path nor its successor reds."""
    repo, roots, c = _fixture()
    try:
        f = _anchor({"id": FIXTURE, "build_commits": [c["build"], c["other"]]}, repo, roots)
    except HollowUnmeasurable as why:
        assert c["other"][:12] in str(why), str(why)
        return
    raise AssertionError(f"anchored over a name that changes neither path: {f}")


def test_a_commit_on_the_charted_path_is_still_accepted():
    """Clause 3: a commit that changed the charted path itself, before the move, still counts."""
    repo, roots, c = _fixture()
    f = _anchor({"id": FIXTURE, "build_commits": [c["pre"]]}, repo, roots)
    assert f["commit"] == c["c0"], (f, c)
    assert f["anchor_first_build"] == c["pre"], (f, c)


def test_the_live_87a7_build_anchors_at_its_parent():
    """Clause 4, live: 87a7f1c7ae21 charts cairn/tools/base/bus_client.py, which moved to
    cairn/tools/bus_client/bus_client.py before its build 18e1923d. Its named build_commits
    anchor at 18e1923d^ — never a refusal, never a later commit (Law 8). Invariant, not a
    snapshot: the parent is read from git, not written here."""
    from cairn.devices.tester.hollow import (COMMONS, _roots, instrument_set, proven_by,
                                             writes_to)
    tid, first = "87a7f1c7ae21", "18e1923d06e13995084b72751801d4ccfd5d9f17"
    ticket = json.loads(next((Path(COMMONS) / "tickets").glob(f"{tid}-*.json")).read_text())
    assert first in (ticket.get("build_commits") or []), ticket.get("build_commits")
    # The files are what 87a7's chart CLAIMS and the instrument is its proofs, read the way
    # ``measure`` reads them — never typed here, so the departed path stays in the chart that
    # named it rather than living on as a literal in class-space (ticket 05662f9e9bc9).
    files = writes_to(ticket)
    instrument = instrument_set(proven_by(ticket), _REPO_ROOT)
    try:
        f = build_anchor(ticket, files, roots=_roots(), repo_root=_REPO_ROOT, instrument=instrument)
    except HollowUnmeasurable as why:
        raise AssertionError(f"87a7's true build_commits were refused: {why}")
    parent = subprocess.run(["git", "-C", str(_REPO_ROOT), "rev-parse", f"{first}^"],
                            capture_output=True, text=True, env=git_env()).stdout.strip()
    assert f["commit"] == parent, (f, parent)


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
