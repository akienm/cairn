"""Teeth for ticket b312ff041558 — the hollow reverts a commons file in a commons worktree.

Akien's answer to open-90d38cb2bdca (2026-10-04, "a agreed"): a build whose writes_to names
CairnCommons files — node classes, read as code by transitions — is proved like code, so the
hollow reverts those files too. Until this ticket every commons path was skipped as "not a
path in this repo", and a commons-only build (5f217a2d4bd6: three node_classes edits) read
"every writes_to file was skipped", which is a red no build could clear.

THE SHAPE. Code reads the commons beside the repo (``_REPO_ROOT.parent / "CairnCommons"``), and
a scratch worktree has nothing beside it. So the hollow makes a worktree of the commons at its
HEAD and links it beside the repo's worktree under that name; each commons file is reverted
there, to the commons repo's OWN pre-build commit (the same anchor rule, asked of the commons).

The fixture is a repo and a git commons named CairnCommons beside it, as on disk. The build
commit is in the commons, names the ticket, and changes two class files; the fixture proof
reads one of them through the beside path.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.hollow import measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "b312ff041558": {
        "1": "test_a_checked_commons_file_is_reverted_and_its_tooth_reds",
        "2": "test_an_unchecked_commons_file_reads_hollow_not_skipped",
        "3": "test_the_commons_file_reverts_to_the_commons_repos_own_prebuild_commit",
        "4": "test_a_commons_that_is_not_a_repository_is_skipped_with_that_reason",
    },
}

FIXTURE = "f1x7c0mm0001"

_PROOF_SRC = '''\
import json
from pathlib import Path

PROVES = {"%s": {"1": "test_the_class_value_is_two"}}

def test_the_class_value_is_two():
    p = Path(__file__).resolve().parents[1].parent / "CairnCommons" / "classes" / "x.json"
    try:
        return json.loads(p.read_text())["value"] == 2
    except Exception:
        return False

if __name__ == "__main__":
    ok = test_the_class_value_is_two()
    print(("ok" if ok else "FAIL") + " test_the_class_value_is_two")
    raise SystemExit(0 if ok else 1)
''' % FIXTURE

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}


def _git(repo, *args, when=None):
    env = dict(_ENV)
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(tmp: Path, *, commons_is_git: bool = True) -> tuple[Path, Path, Path, dict]:
    """repo/ and CairnCommons/ side by side; the build lives in the commons, naming the ticket."""
    repo, commons, berths = tmp / "repo", tmp / "CairnCommons", tmp / "berths"
    for d in (repo / "proofs", commons / "classes", commons / "tickets"):
        d.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / "proofs" / "test_fixture.py").write_text(_PROOF_SRC)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "the proof", when="2020-01-01T00:00:00")

    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    (commons / "classes" / "x.json").write_text(json.dumps({"value": 1}))
    (commons / "classes" / "y.json").write_text(json.dumps({"value": 1}))
    shas = {}
    if commons_is_git:
        _git(commons, "init", "-q", "-b", "main")
        _git(commons, "add", "-A")
        _git(commons, "commit", "-qm", "before the build", when="2020-01-01T00:00:00")
        shas["prebuild"] = _git(commons, "rev-parse", "HEAD").stdout.strip()
        _git(commons, "commit", "-q", "--allow-empty", "-m", "unrelated, after the crossing",
             when="2020-01-02T12:00:00")
    (commons / "classes" / "x.json").write_text(json.dumps({"value": 2}))
    (commons / "classes" / "y.json").write_text(json.dumps({"value": 2}))
    if commons_is_git:
        _git(commons, "add", "-A")
        _git(commons, "commit", "-qm", f"{FIXTURE}: the build", when="2020-01-03T00:00:00")

    berth = berths / "0" / "packets" / "decompose-20200103T000000-f1x7c0mm0001.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": [str(commons / "classes" / "x.json"),
                                                                 "CairnCommons/classes/y.json"]}]}))
    (repo / "history.json").write_text(json.dumps({"entries": [
        {"ticket": FIXTURE, "direction": "forward", "actor": "fixture", "at": "2020-01-02T00:00:00",
         "to": "BUILDME", "proven_by": "proofs/test_fixture.py"}]}))
    return repo, commons, berths, shas


def _run(**kw):
    tmp = scratch_dir("cairn-hollowcommons-")
    repo, commons, berths, shas = _fixture(tmp, **kw)
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60), shas


def test_a_checked_commons_file_is_reverted_and_its_tooth_reds():
    """THE DISCRIMINATING TOOTH. Before the build both commons paths are skipped as outside the
    repo and the run reds 'measured nothing'; after it, x.json is reverted in the commons
    worktree beside the repo's, the proof reads value 1 there, and its declared tooth reds."""
    f, _ = _run()
    assert f["measured"].get("CairnCommons/classes/x.json") == ["test_the_class_value_is_two"], \
        (f["measured"], f["skipped"])
    assert not any("classes/x.json" in s["file"] for s in f["skipped"]), f["skipped"]


def test_an_unchecked_commons_file_reads_hollow_not_skipped():
    """y.json changed in the build and nothing checks it: it is MEASURED and named hollow, which
    is only possible if it was really reverted — a skip would be the old escape hatch."""
    f, _ = _run()
    assert "CairnCommons/classes/y.json" in f["measured"], (f["measured"], f["skipped"])
    assert f["hollow"] == ["CairnCommons/classes/y.json"], f["hollow"]


def test_the_commons_file_reverts_to_the_commons_repos_own_prebuild_commit():
    """The commons has its own history, so its anchor is asked of the commons under the same
    rule: the earlier of the last commons commit before the BUILDME crossing and the parent of
    the first commons commit naming the ticket. Here that is the commons commit before the
    crossing — not the commons HEAD~1 (an unrelated commit sits between), and not the repo's."""
    f, shas = _run()
    assert f.get("commons_commit") == shas["prebuild"], (f.get("commons_commit"), shas)
    assert f.get("commons_anchor_rule") == "journal", f.get("commons_anchor_rule")
    assert f["commit"] != shas["prebuild"], f["commit"]


def test_a_commons_that_is_not_a_repository_is_skipped_with_that_reason():
    """No git history means no commit to revert to: skipped, and the reason says THAT — never
    'not a path in this repo', which is false for a commons path."""
    try:
        f, _ = _run(commons_is_git=False)
        skipped = {s["file"]: s["why"] for s in f["skipped"]}
    except Exception as e:  # every file skipped reds the run; the reasons ride the message
        skipped = {"*": str(e)}
        f = None
    whys = " ".join(skipped.values())
    assert "not a git repository" in whys, skipped
    assert "not a path in this repo" not in whys, skipped
    if f is not None:
        assert not f["measured"], f["measured"]


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
