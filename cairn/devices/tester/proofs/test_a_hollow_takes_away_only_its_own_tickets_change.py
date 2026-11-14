"""Teeth for "a hollow reverts only the ticket's own change to a file, not later tickets' changes
to the same file".

MEASURED 2026-11-14 on 852b6b5fa4bd (`bin/cairn test --hollow`, diagnostic, on 8d20852d6): the
hollow put cairn/tools/scratch/scratch.py back whole to the anchor 29f2393aa463, which also took
away e4be129fd (d95796cdfb9b) and d839314f7 (0c2c3f53c2be), two LATER tickets' changes to the
same file. 852b's own change is one line. So the reading was "the world without three tickets":
a tooth that reds because a later ticket's function went missing reads ``ok`` and is credited to
this ticket's build.

The fixture: c0 lays down ``f.py`` and fixture proofs that import it. Build commit A names the
fixture ticket and adds ``built()`` near the top. Later commit B, which names another ticket,
appends ``later()`` far below (or, for clause 2, also edits A's own line).

  1. test_a_later_tickets_change_stays_and_the_builds_goes: a proof checking B's ``later()``
     reads f.py HOLLOW (B stayed), a proof checking A's ``built()`` reds (A went), mode hunks;
  2. test_a_build_hunk_under_a_later_change_is_refused_by_name: B edits A's line, so A's hunk
     will not reverse-apply: measure raises naming f.py, A's commit and B's, and never returns;
  3. test_with_no_later_change_by_others_the_whole_file_revert_stays: no B, the whole-file
     revert stands (mode whole-file) and reads as before.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.hollow import HollowUnmeasurable, measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "9fbffaad248a": {
        "1": "test_a_later_tickets_change_stays_and_the_builds_goes",
        "2": "test_a_build_hunk_under_a_later_change_is_refused_by_name",
        "3": "test_with_no_later_change_by_others_the_whole_file_revert_stays",
    },
}

FIXTURE = "f1x7a0wnhunk"
OTHER = "f1x7b0thertk"

_PAD = "".join(f"PAD_{i} = {i}\n" for i in range(12))  # keeps B's hunk apart from A's

_PROOF = '''\
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import f

PROVES = {"%s": {"1": "%s"}}

def %s():
    try:
        return %s
    except Exception:
        return False

if __name__ == "__main__":
    ok = %s()
    print(("ok" if ok else "FAIL") + " %s")
    raise SystemExit(0 if ok else 1)
'''


def _proof_src(name: str, expr: str) -> str:
    return _PROOF % (FIXTURE, name, name, expr, name, name)


def _git(repo, *args, at=None):
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(later: str) -> tuple[Path, Path, Path, str, str | None]:
    """later: 'apart' (B appends later() far below A's hunk), 'overlaps' (B also edits A's own
    line) or 'none' (no B). Returns repo, commons, berths, A's sha and B's (None without B)."""
    tmp = scratch_dir("cairn-hollow-own-hunks-")
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", commons / "tickets"):
        d.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / "f.py").write_text("def base():\n    return 1\n\n" + _PAD)
    (repo / "proofs" / "test_built.py").write_text(_proof_src("test_built_is_two", "f.built() == 2"))
    (repo / "proofs" / "test_later.py").write_text(_proof_src("test_later_is_nine", "f.later() == 9"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "before the build", at="2020-01-01T00:00:00")

    src = (repo / "f.py").read_text()
    (repo / "f.py").write_text(src.replace("def base():", "def built():\n    return 2\n\n\ndef base():", 1))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"{FIXTURE}: the build", at="2020-01-03T00:00:00")
    a = _git(repo, "rev-parse", "HEAD").stdout.strip()

    b = None
    if later != "none":
        src = (repo / "f.py").read_text() + "\n\ndef later():\n    return 9\n"
        if later == "overlaps":
            src = src.replace("    return 2\n", "    return 2  # touched by the later ticket\n", 1)
        (repo / "f.py").write_text(src)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", f"{OTHER}: a later ticket's change", at="2020-01-05T00:00:00")
        b = _git(repo, "rev-parse", "HEAD").stdout.strip()

    berth = berths / "0" / "packets" / f"decompose-20200103T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": ["f.py"]}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    (repo / "history.json").write_text(json.dumps({"entries": [
        {"ticket": FIXTURE, "direction": "forward", "actor": "fixture", "at": "2020-01-02T00:00:00",
         "to": "BUILDME"}]}))
    return repo, commons, berths, a, b


def _measure(later: str, proof: str):
    repo, commons, berths, a, b = _fixture(later)
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60,
                log=lambda m: None, proofs=[str(repo / "proofs" / proof)])
    return f, a, b


def test_a_later_tickets_change_stays_and_the_builds_goes():
    """Clause 1: B's later() survives A's hollow (its proof reads f.py HOLLOW, not ok), and A's
    built() is taken away (its proof reds), in hunk mode."""
    kept, _, _ = _measure("apart", "test_later.py")
    assert kept["hollow"] == ["f.py"], \
        f"a later ticket's change was taken away with the build: measured={kept['measured']}"
    assert kept.get("revert_mode", {}).get("f.py") == "hunks", kept.get("revert_mode")
    gone, _, _ = _measure("apart", "test_built.py")
    assert gone["measured"].get("f.py") == ["test_built_is_two"], \
        f"the build's own change was not taken away: measured={gone['measured']}"
    assert gone.get("unran", {}) == {}, gone.get("unran")


def test_a_build_hunk_under_a_later_change_is_refused_by_name():
    """Clause 2: B edits A's own line, so A's hunk will not reverse-apply over it: measure raises,
    naming f.py, A's commit and B's. A whole-file fallback would return a reading instead."""
    repo, commons, berths, a, b = _fixture("overlaps")
    try:
        f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60,
                    log=lambda m: None, proofs=[str(repo / "proofs" / "test_built.py")])
    except HollowUnmeasurable as why:
        said = str(why)
        assert "f.py" in said and "will not reverse-apply" in said, said
        assert a[:12] in said, f"the refusal does not name the build commit {a[:12]}: {said}"
        assert b[:12] in said, f"the refusal does not name the later commit {b[:12]}: {said}"
        return
    raise AssertionError(f"an overlapping later change returned a reading: measured={f['measured']} "
                         f"revert_mode={f.get('revert_mode')}")


def test_with_no_later_change_by_others_the_whole_file_revert_stays():
    """Clause 3: with no later commit by others the whole-file revert stands and reads as before."""
    f, _, _ = _measure("none", "test_built.py")
    assert f["measured"].get("f.py") == ["test_built_is_two"], f["measured"]
    assert f.get("revert_mode", {}).get("f.py") == "whole-file", f.get("revert_mode")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
