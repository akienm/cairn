"""Teeth for ticket d65fe3aa96e2 — the hollow follows a moved file to where it went.

MEASURED 2026-10-02 at ticket 9245b9cbce53's PROVEME: `cairn test --hollow` read
"0 file(s) measured · 0 hollow · 3 skipped", because every writes_to the chart named was the
SOURCE of a move, and the per-file loop skipped each one as "not present at HEAD — the build is
not committed" while the build sat committed in front of it. The skip reason was false, and a
move-only build could never be measured. build_inspector already holds the one successor order
(`resolves_to`: the ticket's forwarding order first, git's rename record second), and it is in
that machine's declared public_interface, so the hollow asks it rather than spelling a second.

The fixture is a two-commit repo whose build commit MOVES `old/subject.py` to
`new/subject.py` and changes it; the fixture proof imports it at the new path inside its tooth,
so the counterfactual "the move had not happened" must red that tooth.
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

PROVES = {
    "d65fe3aa96e2": {
        "1": "test_a_moved_file_is_measured_at_its_successor_and_its_tooth_reds",
        "2": "test_an_absent_file_with_no_successor_is_skipped_with_a_reason_naming_the_absence",
        "3": "test_the_live_move_of_9245_resolves_to_a_file_the_hollow_can_measure",
    },
}

FIXTURE = "f1x7m0ve0001"

_PROOF_SRC = '''\
import importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROVES = {"%s": {"1": "test_the_moved_value_is_two"}}

def test_the_moved_value_is_two():
    try:
        return importlib.import_module("new.subject").VALUE == 2
    except Exception:
        return False

if __name__ == "__main__":
    ok = test_the_moved_value_is_two()
    print(("ok" if ok else "FAIL") + " test_the_moved_value_is_two")
    raise SystemExit(0 if ok else 1)
''' % FIXTURE


def _git(repo, *args, env=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          env=env or git_env())


def _fixture(tmp: Path, writes_to: list) -> tuple[Path, Path, Path]:
    """Repo + commons + berth store, wired like a real ticket whose build commit moves a file."""
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", repo / "old", commons / "tickets"):
        d.mkdir(parents=True)
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    _git(repo, "init", "-q", "-b", "main", env=env)
    (repo / "old" / "__init__.py").write_text("")
    (repo / "old" / "subject.py").write_text("VALUE = 1\n" + "# padding so git sees a rename\n" * 20)
    (repo / "proofs" / "test_fixture.py").write_text(_PROOF_SRC)
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-qm", "before the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-01T00:00:00", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00"})

    (repo / "new").mkdir()
    _git(repo, "mv", "old/subject.py", "new/subject.py", env=env)
    _git(repo, "mv", "old/__init__.py", "new/__init__.py", env=env)
    (repo / "new" / "subject.py").write_text("VALUE = 2\n" + "# padding so git sees a rename\n" * 20)
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-qm", "the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-03T00:00:00", "GIT_COMMITTER_DATE": "2020-01-03T00:00:00"})

    berth = berths / "0" / "packets" / "decompose-20200103T000000-f1x7m0ve0001.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": writes_to}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    (repo / "history.json").write_text(json.dumps({"entries": [
        {"ticket": FIXTURE, "direction": "forward", "actor": "fixture", "at": "2020-01-02T00:00:00",
         "to": "BUILDME", "proven_by": "proofs/test_fixture.py"}]}))
    return repo, commons, berths


def test_a_moved_file_is_measured_at_its_successor_and_its_tooth_reds():
    """THE DISCRIMINATING TOOTH. Before the fix the source path is skipped (absent at HEAD) and
    the run raises 'measured nothing'; after it, the successor is reverted and the declared
    tooth reds, so the move is load-bearing and is reported measured, not hollow."""
    tmp = scratch_dir("cairn-hollowmove-")
    repo, commons, berths = _fixture(tmp, ["old/subject.py"])
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)
    assert "new/subject.py" in f["measured"], (f["measured"], f["skipped"])
    assert f["measured"]["new/subject.py"] == ["test_the_moved_value_is_two"], f["measured"]
    assert f["hollow"] == [], f["hollow"]
    assert not any(s["file"] == "old/subject.py" for s in f["skipped"]), f["skipped"]
    # The report says where the measured file came from — the chart named the source.
    assert f.get("moved", {}).get("new/subject.py") == "old/subject.py", f.get("moved")


def test_an_absent_file_with_no_successor_is_skipped_with_a_reason_naming_the_absence():
    """A declared file that is gone with no recorded successor is still skipped, and the reason
    says so truthfully — never 'the build is not committed' when it is."""
    tmp = scratch_dir("cairn-hollowmove-")
    repo, commons, berths = _fixture(tmp, ["old/subject.py", "never/was.py"])
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)
    gone = [s for s in f["skipped"] if s["file"] == "never/was.py"]
    assert len(gone) == 1, f["skipped"]
    assert "no recorded successor" in gone[0]["why"], gone
    assert "not committed" not in gone[0]["why"], gone


def test_the_live_move_of_9245_resolves_to_a_file_the_hollow_can_measure():
    """Over the live repo: the source path ticket 9245b9cbce53 charted is followed to a file
    present in the tree. Asserted as an invariant (the successor exists and is not the source),
    never as a snapshot of where scratch lives today."""
    src = "cairn/devices/tester/scratch.py"
    got = hollow.moved_to(src, "9245b9cbce53", repo_root=_REPO_ROOT, worktree=_REPO_ROOT)
    assert got and got != src, got
    assert (_REPO_ROOT / got).is_file(), got


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
