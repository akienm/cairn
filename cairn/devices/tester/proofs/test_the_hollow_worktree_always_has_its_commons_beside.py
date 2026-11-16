"""Teeth for ticket 19193ff1e41e — every hollow worktree has the commons beside it.

Measured 2026-11-14: ad6f3d0b265c's hollow refused ("no reversion reading can be attributed to
a file") because two teeth that read ``../CairnCommons`` failed at HEAD in the scratch
worktree: hollow.py placed a commons beside the worktree only when the ticket named a commons
file (b312ff041558), so a ticket that names none measured a missing sibling, not its build.

  (1) a hollow over a ticket naming no commons file runs its proofs in a worktree whose parent
      holds CairnCommons resolving to the standing commons, so a tooth that reads
      ../CairnCommons/tickets/_charter+why.json is green at the baseline and a reversion of
      the built file is attributed;
  (2) a hollow over a ticket naming a commons file still reverts that file in a commons
      worktree beside the repo worktree, as test_the_hollow_reverts_a_commons_file measures;
  (3) the standing commons is byte-identical before and after a hollow over a ticket naming no
      commons file.

The fixture is a repo and a git commons named CairnCommons beside it, as on disk, in a scratch
directory. The build commit is in the repo and names the ticket; the commons only holds the
ticket and a store charter the fixture proof reads.
"""
from __future__ import annotations

import hashlib
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
    "19193ff1e41e": {
        "1": "test_a_ticket_naming_no_commons_file_hollows_with_the_commons_beside",
        "2": "test_a_ticket_naming_a_commons_file_still_reverts_it_in_a_commons_worktree",
        "3": "test_the_standing_commons_is_byte_identical_after_the_hollow",
    },
}

FIXTURE = "f1x71919c0b5"
TOOTH = "test_the_built_value_is_two_beside_the_charter"

_PROOF_SRC = '''\
import json
from pathlib import Path

PROVES = {"%s": {"1": "%s"}}

def %s():
    here = Path(__file__).resolve().parents[1]
    charter = here.parent / "CairnCommons" / "tickets" / "_charter+why.json"
    try:
        return (json.loads((here / "mod.json").read_text())["value"] == 2
                and json.loads(charter.read_text())["kind"] == "the store charter")
    except Exception:
        return False

if __name__ == "__main__":
    ok = %s()
    print(("ok" if ok else "FAIL") + " %s")
    raise SystemExit(0 if ok else 1)
''' % (FIXTURE, TOOTH, TOOTH, TOOTH, TOOTH)

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}


def _git(repo, *args, when=None):
    env = dict(_ENV)
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(tmp: Path) -> tuple[Path, Path, Path]:
    """repo/ and CairnCommons/ side by side; the build is a repo file, and names the ticket."""
    repo, commons, berths = tmp / "repo", tmp / "CairnCommons", tmp / "berths"
    for d in (repo / "proofs", commons / "tickets"):
        d.mkdir(parents=True)
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    (commons / "tickets" / "_charter+why.json").write_text(json.dumps({"kind": "the store charter"}))
    _git(commons, "init", "-q", "-b", "main")
    _git(commons, "add", "-A")
    _git(commons, "commit", "-qm", "the commons", when="2020-01-01T00:00:00")

    _git(repo, "init", "-q", "-b", "main")
    (repo / "proofs" / "test_fixture.py").write_text(_PROOF_SRC)
    (repo / "mod.json").write_text(json.dumps({"value": 1}))
    (repo / "history.json").write_text(json.dumps({"entries": [
        {"ticket": FIXTURE, "direction": "forward", "actor": "fixture", "at": "2020-01-02T00:00:00",
         "to": "BUILDME", "proven_by": "proofs/test_fixture.py"}]}))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "before the build", when="2020-01-01T00:00:00")
    (repo / "mod.json").write_text(json.dumps({"value": 2}))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"{FIXTURE}: the build", when="2020-01-03T00:00:00")

    berth = berths / "0" / "packets" / f"decompose-20200103T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": ["mod.json"]}]}))
    return repo, commons, berths


def _digest(root: Path) -> dict:
    """Every file under ``root`` (its .git included) and its sha256, by relative path."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.is_symlink()}


def _run_no_commons_file():
    tmp = scratch_dir("cairn-hollow1919-")
    repo, commons, berths = _fixture(tmp)
    before = _digest(commons)
    try:
        f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)
    except Exception as e:  # a refused hollow is the red this ticket fixes; its words ride the assert
        f = {"refused": f"{type(e).__name__}: {e}"}
    return f, before, _digest(commons)


def test_a_ticket_naming_no_commons_file_hollows_with_the_commons_beside():
    """THE DISCRIMINATING TOOTH. Before the fix the worktree has nothing beside it, so the
    fixture tooth is red at the baseline and the hollow refuses; after it, the tooth is green at
    HEAD and reverting mod.json reds it — attributed to that file, and no commons worktree made."""
    f, _, _ = _run_no_commons_file()
    assert "refused" not in f, f.get("refused")
    assert f["measured"] == {"mod.json": [TOOTH]}, (f["measured"], f.get("skipped"))
    assert f["verdict"] == "green", f
    assert f.get("commons_worktree") is None, f.get("commons_worktree")


def test_a_ticket_naming_a_commons_file_still_reverts_it_in_a_commons_worktree():
    """b312ff041558's case is unchanged: its own discriminating tooth stays green, and the commons
    the hollow read was a worktree of its own, not the standing commons."""
    from cairn.devices.tester.proofs import test_the_hollow_reverts_a_commons_file as B
    B.test_a_checked_commons_file_is_reverted_and_its_tooth_reds()
    f, _ = B._run()
    cwt = f.get("commons_worktree")
    assert cwt and "cairn-hollow-commons-" in cwt, cwt
    assert f["measured"].get("CairnCommons/classes/x.json") == ["test_the_class_value_is_two"], f["measured"]


def test_the_standing_commons_is_byte_identical_after_the_hollow():
    """The link beside the worktree is read, never written: every byte of the standing commons
    (its git store included) is what it was before the hollow."""
    _, before, after = _run_no_commons_file()
    assert before and after == before, sorted(set(before.items()) ^ set(after.items()))[:5]


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
