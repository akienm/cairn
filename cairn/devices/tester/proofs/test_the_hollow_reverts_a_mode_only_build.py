"""Teeth for ticket bfcb0d1cab45 — the hollow reverts a file's git mode as well as its bytes.

MEASURED 2026-11-23 on akiendelllinux at 846b6ca0eaf7's PROVEME: the build only set
cairn/devices/cc/superclaude.py from git mode 100644 to 100755, bytes unchanged, and
`cairn test --hollow` read it "UNWRIT (identical at the pre-build commit — the build did not
write it)", because _revert compared bytes and nothing else. The counterfactual was measurable:
the same worktree with `git update-index --chmod=-x` on that file redded 846b's tooth 1.

The fixture is a two-commit repo whose build commit flips bin/v from 100644 to 100755 (bytes
identical) and edits zz_other.py, which nothing checks. The fixture proof's tooth reads the
index mode of bin/v the way 846b's tooth does, so reverting v's mode must red it; zz_other.py,
measured AFTER v, reds nothing only if v's mode was restored to HEAD's before it was read.

The no-op reading (bytes and mode identical stays UNWRIT) is guarded by test_hollow.py's
test_an_unchanged_file_is_reported_unwritten_not_hollow, not here: a guard a hollow build
passes is no tooth (Law 8, open-1b1c6dbdb877).
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

PROOF_TIMEOUT_S = 600

PROVES = {
    "bfcb0d1cab45": {
        "1": "test_a_mode_only_build_file_is_reverted_and_its_tooth_reds",
        "2": "test_a_tooth_that_never_reads_the_mode_reads_it_hollow",
        "3": "test_the_mode_is_restored_before_the_next_file_is_read",
    },
}

FIXTURE = "f1x7d0de0b17"

# READS_MODE: the tooth reads git's index for bin/v, as 846b's tooth 1 does.
_PROOF_SRC = '''\
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

PROVES = {"%s": {"1": "test_v_is_executable"}}

def test_v_is_executable():
    if not %s:
        return True
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-s", "--", "bin/v"],
                         capture_output=True, text=True).stdout
    return out.startswith("100755 ")

if __name__ == "__main__":
    ok = test_v_is_executable()
    print(("ok" if ok else "FAIL") + " test_v_is_executable")
    raise SystemExit(0 if ok else 1)
'''


def _git(repo, *args, env=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          env=env or git_env())


def _fixture(tmp: Path, writes_to: list, reads_mode: bool) -> tuple[Path, Path, Path]:
    """Repo + commons + berth store, wired like a real ticket whose build commit only flips v's mode."""
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", repo / "bin", commons / "tickets"):
        d.mkdir(parents=True)
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    _git(repo, "init", "-q", "-b", "main", env=env)
    _git(repo, "config", "core.fileMode", "true", env=env)
    (repo / "bin" / "v").write_text("#!/bin/sh\necho v\n")
    (repo / "zz_other.py").write_text("MARK = 'before the build'\n")
    (repo / "proofs" / "test_fixture.py").write_text(_PROOF_SRC % (FIXTURE, reads_mode))
    _git(repo, "add", "-A", env=env)
    _git(repo, "update-index", "--chmod=-x", "--", "bin/v", env=env)
    _git(repo, "commit", "-qm", "before the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-01T00:00:00", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00"})

    _git(repo, "update-index", "--chmod=+x", "--", "bin/v", env=env)
    (repo / "bin" / "v").chmod(0o755)
    (repo / "zz_other.py").write_text("MARK = 'after the build'\n")
    _git(repo, "add", "--", "zz_other.py", env=env)
    _git(repo, "commit", "-qm", f"{FIXTURE}: the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-03T00:00:00", "GIT_COMMITTER_DATE": "2020-01-03T00:00:00"})
    head_v = _git(repo, "ls-files", "-s", "--", "bin/v").stdout
    assert head_v.startswith("100755 "), f"fixture: the build did not set v's mode: {head_v!r}"

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


def _measure(writes_to: list, reads_mode: bool = True) -> dict:
    repo, commons, berths = _fixture(scratch_dir("cairn-hollowmode-"), writes_to, reads_mode)
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)
    # the live fixture tree is never touched: the mode revert happens in the worktree only
    assert _git(repo, "ls-files", "-s", "--", "bin/v").stdout.startswith("100755 "), \
        "the mode revert leaked into the repo's own index"
    return f


def test_a_mode_only_build_file_is_reverted_and_its_tooth_reds():
    """THE DISCRIMINATING TOOTH: v's bytes are identical at the anchor, its mode is not, and the
    revert of the mode reds the tooth that reads it — measured, never UNWRIT."""
    f = _measure(["bin/v", "zz_other.py"])
    assert "bin/v" not in f["unchanged"], (f["unchanged"], f["skipped"])
    assert f["measured"].get("bin/v") == ["test_v_is_executable"], (f["measured"], f["skipped"])


def test_a_tooth_that_never_reads_the_mode_reads_it_hollow():
    """The same revert under a tooth that ignores the mode reds nothing, so v reads hollow."""
    f = _measure(["bin/v", "zz_other.py"], reads_mode=False)
    assert "bin/v" not in f["unchanged"], f["unchanged"]
    assert f["measured"].get("bin/v") == [], f["measured"]
    assert "bin/v" in f["hollow"], f["hollow"]


def test_the_mode_is_restored_before_the_next_file_is_read():
    """zz_other.py is read AFTER v. Its revert touches only its bytes, so the mode tooth reds on
    it only if v's mode was left at the anchor's — the restore has to put the index back."""
    f = _measure(["bin/v", "zz_other.py"])
    assert f["measured"].get("bin/v") == ["test_v_is_executable"], f["measured"]
    assert f["measured"].get("zz_other.py") == [], f["measured"]
    assert f["hollow"] == ["zz_other.py"], f["hollow"]


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
