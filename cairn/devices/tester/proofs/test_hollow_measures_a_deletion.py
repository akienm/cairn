"""Teeth for ticket 7bd839827172 — the hollow reading measures a deletion.

MEASURED 2026-11-08 at ticket 80df7712b8c5's PROVEME: `cairn test --hollow` read "0 file(s)
measured · 2 skipped", because the build DELETED cairn/machines/quarry_index and the per-file
loop skipped it as "not present at HEAD and no recorded successor — there is nothing to revert".
There was something to revert: the folder as the anchor held it. A deletion is a move with no
successor, and its counterfactual is the deleted file back where it stood — so a retirement
ticket (outline rule 1.3.7) could never be measured, only refused at PROVED.

The fixture is a two-commit repo whose build commit deletes the package `gone/` (and edits
`zz_other.py`, which nothing checks). The fixture proof's one tooth asserts `gone` is not
importable, so restoring any file of `gone/` must red it, and undoing the restore must leave
no trace — an empty `gone/` left behind still imports as a namespace package, so it would red
`zz_other.py`'s reading too, and the hollow file would read as checked.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester import hollow  # noqa: E402
from cairn.devices.tester.hollow import measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROOF_TIMEOUT_S = 600

PROVES = {
    "7bd839827172": {
        "1": "test_a_deleted_file_is_restored_measured_and_taken_away_again",
        "2": "test_a_path_that_never_existed_is_still_skipped_for_its_absence",
        "3": "test_a_deleted_directory_is_measured_file_by_file",
    },
}

FIXTURE = "f1x7de1e7e01"

_PROOF_SRC = '''\
import importlib.util, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROVES = {"%s": {"1": "test_gone_is_gone"}}

def test_gone_is_gone():
    return importlib.util.find_spec("gone") is None

if __name__ == "__main__":
    ok = test_gone_is_gone()
    print(("ok" if ok else "FAIL") + " test_gone_is_gone")
    raise SystemExit(0 if ok else 1)
''' % FIXTURE


def _git(repo, *args, env=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          env=env or git_env())


def _fixture(tmp: Path, writes_to: list) -> tuple[Path, Path, Path]:
    """Repo + commons + berth store, wired like a real ticket whose build commit deletes gone/."""
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", repo / "gone", commons / "tickets"):
        d.mkdir(parents=True)
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    _git(repo, "init", "-q", "-b", "main", env=env)
    (repo / "gone" / "__init__.py").write_text("")
    (repo / "gone" / "mod.py").write_text("VALUE = 1\n")
    (repo / "zz_other.py").write_text("MARK = 'before the build'\n")
    (repo / "proofs" / "test_fixture.py").write_text(_PROOF_SRC)
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-qm", "before the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-01T00:00:00", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00"})

    _git(repo, "rm", "-rq", "gone", env=env)
    (repo / "zz_other.py").write_text("MARK = 'after the build'\n")
    _git(repo, "add", "-A", env=env)
    # the ticket id in the message: a directory is expanded over THIS ticket's build commits
    _git(repo, "commit", "-qm", f"{FIXTURE}: the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-03T00:00:00", "GIT_COMMITTER_DATE": "2020-01-03T00:00:00"})

    berth = berths / "0" / "packets" / f"decompose-20200103T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": writes_to}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    (repo / "history.json").write_text(json.dumps({"entries": [
        {"ticket": FIXTURE, "direction": "forward", "actor": "fixture", "at": "2020-01-02T00:00:00",
         "to": "BUILDME", "proven_by": "proofs/test_fixture.py"}]}))
    return repo, commons, berths


def _measure(writes_to: list) -> dict:
    repo, commons, berths = _fixture(scratch_dir("cairn-hollowdel-"), writes_to)
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)
    # the live fixture tree is never touched: the restore happens in the worktree only
    assert not (repo / "gone").exists(), "the restore leaked into the repo's own tree"
    return f


def test_a_deleted_file_is_restored_measured_and_taken_away_again():
    """THE DISCRIMINATING TOOTH, both halves from one run. gone/mod.py, restored, reds the
    declared tooth; zz_other.py, measured AFTER it, reds nothing — which it can only do if the
    restore was undone whole, empty folder included, before zz_other.py was read."""
    f = _measure(["gone/mod.py", "zz_other.py"])
    assert f["measured"].get("gone/mod.py") == ["test_gone_is_gone"], (f["measured"], f["skipped"])
    assert f["measured"].get("zz_other.py") == [], f["measured"]
    assert f["hollow"] == ["zz_other.py"], f["hollow"]
    assert not any(s["file"] == "gone/mod.py" for s in f["skipped"]), f["skipped"]


def test_a_path_that_never_existed_is_still_skipped_for_its_absence():
    """The skip stays where it was true: absent at HEAD AND at the anchor, nothing to restore."""
    f = _measure(["never/was.py", "gone/mod.py"])
    gone = [s for s in f["skipped"] if s["file"] == "never/was.py"]
    assert len(gone) == 1, f["skipped"]
    assert "no recorded successor" in gone[0]["why"], gone
    assert f["measured"].get("gone/mod.py") == ["test_gone_is_gone"], f["measured"]


def test_a_deleted_directory_is_measured_file_by_file():
    """A writes_to naming a directory the build deleted is read over the files this ticket's
    build commits deleted under it — the same rule a directory present at HEAD already follows
    (ticket e08c996f939c) — and never skipped as 'not present at HEAD'. Then the live invariant:
    ticket 80df7712b8c5's anchor holds cairn/machines/quarry_index as files, and the expansion
    finds them, so the retirement's hollow can be measured."""
    f = _measure(["gone"])
    assert f["measured"].get("gone/__init__.py") == ["test_gone_is_gone"], (f["measured"], f["skipped"])
    assert f["measured"].get("gone/mod.py") == ["test_gone_is_gone"], f["measured"]
    assert not any(s["file"] == "gone" for s in f["skipped"]), f["skipped"]

    anchor = "e88175086e2d"
    if _git(_REPO_ROOT, "cat-file", "-e", f"{anchor}^{{commit}}").returncode == 0:
        files, skips = hollow._expand_dirs(["cairn/machines/quarry_index"], anchor, _REPO_ROOT,
                                           tid="80df7712b8c5")
        assert "cairn/machines/quarry_index/compiler.py" in files, (files, skips)
        assert not skips, skips


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
