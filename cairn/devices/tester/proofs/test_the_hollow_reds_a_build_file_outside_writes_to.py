"""Teeth for the hollow reading a build commit's file that writes_to never named.

MEASURED 2026-10-13 while building f8d58aff88f9 (trouble build-commit-touches-a-file-outside-
writes-to): a '<tid>: build' commit that changes a file the decompose berth's writes_to does not
name is measured by nothing — hollow reverts only writes_to files, and the build commits it
gathers place the anchor and never widen the revert set. Census 2026-10-18 over the '<tid>: build'
commits since 2026-09-15: 20 of 111 tickets changed at least one such file (84 source, 64 proof).

THE RULE THESE TEETH HOLD. Every path a '<tid>: build' commit after the anchor changed is either
named by writes_to (a file, or under a named directory), a record (history.json, state.json,
validations/), the artifact journal, or the instrument. Any other path is a reason — 'unplanned:
<file>' naming the build commit — and the verdict reds. A commit naming the ticket that is not a
build commit (a records commit, a repair) is not read: the trouble is about what the build did.

Every fixture is a scratch repo with its own journal and decompose berth, the shape of
test_hollow_anchors_without_a_journaled_buildme.py.
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
    "1c7e8a2b5f30": {
        "1": "test_a_build_file_outside_writes_to_reds_naming_it",
        "2": "test_records_the_journal_and_writes_to_files_do_not_red",
        "3": "test_a_commit_that_is_not_a_build_commit_is_not_read",
    },
}

FIXTURE = "b0dc0ffee001"

_PROOF_SRC = '''\
import importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROVES = {"%s": {"1": "test_the_built_value_is_two"}}

def test_the_built_value_is_two():
    try:
        sys.modules.pop("subject", None)
        return importlib.import_module("subject").VALUE == 2
    except Exception:
        return False

if __name__ == "__main__":
    ok = test_the_built_value_is_two()
    print(("ok" if ok else "FAIL") + " test_the_built_value_is_two")
    raise SystemExit(0 if ok else 1)
''' % FIXTURE

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}


def _git(repo, *args, at=None):
    env = dict(_ENV)
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _commit(repo, at, msg, writes: dict) -> None:
    for rel, text in writes.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", msg, at=at)


def _fixture(build: dict, after: list[tuple[str, dict]] = ()) -> tuple[Path, Path, Path]:
    """c0 lays down subject.py (VALUE = 1), other.py and the proof; BUILDME is journaled; then
    one '<FIXTURE>: build' commit writes ``build`` (always subject.py VALUE = 2), then each of
    ``after`` as (message, writes); then BUILDME->PROVEME. writes_to names subject.py alone."""
    tmp = scratch_dir("cairn-hollowunplanned-")
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    (commons / "tickets").mkdir(parents=True)
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, "2020-01-01T00:00:00", "unrelated: c0",
            {"subject.py": "VALUE = 1\n", "other.py": "X = 1\n", "proofs/test_fixture.py": _PROOF_SRC})
    _commit(repo, "2020-01-02T00:00:00", f"{FIXTURE}: build", {"subject.py": "VALUE = 2\n", **build})
    for i, (msg, writes) in enumerate(after):
        _commit(repo, f"2020-01-03T0{i}:00:00", msg, writes)
    entries = [{"ticket": FIXTURE, "direction": "forward", "actor": "fixture", "at": at, "from": frm,
                "to": to, "proven_by": "proofs/test_fixture.py"}
               for at, frm, to in (("2020-01-01T12:00:00", "TICKETME", "BUILDME"),
                                   ("2020-01-04T00:00:00", "BUILDME", "PROVEME"))]
    (repo / "history.json").write_text(json.dumps({"entries": entries}))
    berth = berths / "0" / "packets" / f"decompose-20200101T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": ["subject.py"]}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    return repo, commons, berths


def _measure(repo, commons, berths):
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)


def _unplanned(f) -> list[str]:
    return [r for r in f["reasons"] if r.startswith("unplanned:")]


def test_a_build_file_outside_writes_to_reds_naming_it():
    """The build commit also changes other.py, which writes_to never names: nothing reverts it,
    so the reading reds with one 'unplanned' reason naming other.py and the build commit."""
    repo, commons, berths = _fixture({"other.py": "X = 2\n"})
    sha = _git(repo, "log", "-1", "--format=%H", f"--grep={FIXTURE}: build").stdout.strip()
    f = _measure(repo, commons, berths)
    assert f["measured"].get("subject.py") == ["test_the_built_value_is_two"], f["measured"]
    u = _unplanned(f)
    assert len(u) == 1 and "other.py" in u[0] and sha[:12] in u[0], f["reasons"]
    assert f["verdict"] == "red", f["verdict"]


def test_records_the_journal_and_writes_to_files_do_not_red():
    """A build commit that writes, beside subject.py, a state.json, a validations/ record and the
    artifact journal changed nothing a proof could pin: no 'unplanned' reason, verdict green."""
    repo, commons, berths = _fixture({"comp/state.json": "{}\n", "comp/validations/v.json": "{}\n",
                                      ".artifact-journal.jsonl": "{}\n"})
    f = _measure(repo, commons, berths)
    assert _unplanned(f) == [], f["reasons"]
    assert f["verdict"] == "green", f["reasons"]


def test_a_commit_that_is_not_a_build_commit_is_not_read():
    """After the build, a records commit names the ticket and changes other.py: it is not a
    '<tid>: build' commit, so it is not read — the build itself stayed inside writes_to."""
    repo, commons, berths = _fixture({}, after=[(f"records: {FIXTURE} PROVEME", {"other.py": "X = 3\n"})])
    f = _measure(repo, commons, berths)
    assert _unplanned(f) == [], f["reasons"]
    assert f["verdict"] == "green", f["reasons"]


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
