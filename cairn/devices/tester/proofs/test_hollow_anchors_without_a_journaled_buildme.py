"""Teeth for ticket f8d58aff88f9 — hollow anchors a build whose BUILDME predates the journals.

MEASURED 2026-10-12 on 4ddc9df3369e: its BUILDME stood by a 09-07 PROVEME->BUILDME back-edge and
its only forward crossing into BUILDME predated the journals (they begin 2026-09-06), so
``cairn test --hollow 4ddc9df3369e --seal`` refused HollowUnmeasurable over a build committed as
3024a302 "4ddc9df3369e: build", and PROVED bounced the boat to FIXME. By hand at n=1 the build was
measurable: trouble.py reverted redded, node_classes/trouble.json removed redded, both restored
greened. The instrument could not say what a hand could.

THE RULE THESE TEETH HOLD. Only when ``buildme_crossing`` returns None — no journal records a
forward crossing into BUILDME at all — build_anchor anchors at the parent of the ticket's first
build commit after the back-edge bound (rule 'first-build-commit-no-crossing'), a build commit
being one whose subject starts '<tid>: build' or one naming the ticket that changes a measured
file. A journaled forward crossing anchors exactly as before. With neither, the run refuses and
names both lacks. (The peer's reading, 2026-10-12: "no forward BUILDME crossing" means
buildme_crossing() returns None; read literally as "none after the first build commit" it would
switch nearly every ticket onto the fallback.)

Every fixture is a scratch repo with its own journal and decompose berth, copied from
test_hollow_anchors_before_the_build_that_stands.py.
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
    "f8d58aff88f9": {
        "1": "test_no_journaled_buildme_anchors_at_the_first_build_commits_parent",
        "2": "test_a_journaled_buildme_anchors_exactly_as_before",
        "3": "test_no_buildme_and_no_build_commit_refuses_naming_both",
    },
}

FIXTURE = "f1x7a4c40003"

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


def _fixture(events: list) -> tuple[Path, Path, Path, dict]:
    """A scratch repo, commons and berth store played from ``events``, oldest first.

    ("commit", at, label, value, names_ticket) writes subject.py with VALUE = value and commits
    it; ("cross", at, from, to, direction) journals one crossing. Returns the three roots and
    {label: sha}. The first commit ("c0") also lays down the fixture proof.
    """
    tmp = scratch_dir("cairn-hollownocross-")
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", commons / "tickets"):
        d.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / "proofs" / "test_fixture.py").write_text(_PROOF_SRC)
    shas, entries = {}, []
    for ev in events:
        if ev[0] == "commit":
            _, at, label, value, names = ev
            (repo / "subject.py").write_text(f"VALUE = {value}\n")
            (repo / "log.txt").write_text(label)  # so a commit that keeps VALUE still commits
            _git(repo, "add", "-A")
            msg = f"{FIXTURE}: {label}" if names else f"unrelated: {label}"
            _git(repo, "commit", "-qm", msg, at=at)
            shas[label] = _git(repo, "rev-parse", "HEAD").stdout.strip()
        else:
            _, at, frm, to, direction = ev
            entries.append({"ticket": FIXTURE, "direction": direction, "actor": "fixture",
                            "at": at, "from": frm, "to": to,
                            "proven_by": "proofs/test_fixture.py"})
    (repo / "history.json").write_text(json.dumps({"entries": entries}))
    berth = berths / "0" / "packets" / f"decompose-20200101T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": ["subject.py"]}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    return repo, commons, berths, shas


def _measure(repo, commons, berths):
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)


def test_no_journaled_buildme_anchors_at_the_first_build_commits_parent():
    """4ddc's shape: two build commits, and the journals hold only BUILDME->PROVEME forward and
    PROVEME->FIXME back — no forward crossing into BUILDME. The anchor is the FIRST build
    commit's parent, so the later build commit cannot hide, and the reverted file reds."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", 1, False),
        ("commit", "2020-01-02T00:00:00", "build", 5, True),
        ("commit", "2020-01-03T00:00:00", "build more", 2, True),
        ("cross", "2020-01-04T00:00:00", "BUILDME", "PROVEME", "forward"),
        ("cross", "2020-01-05T00:00:00", "PROVEME", "FIXME", "back"),
    ])
    try:
        f = _measure(repo, commons, berths)
    except HollowUnmeasurable as why:
        raise AssertionError(f"refused a measurable build: {why}")
    assert f["commit"] == c["c0"], (f["commit"], c)
    assert f.get("anchor_rule") == "first-build-commit-no-crossing", f.get("anchor_rule")
    assert f["measured"].get("subject.py") == ["test_the_built_value_is_two"], f["measured"]


def test_a_journaled_buildme_anchors_exactly_as_before():
    """A forward TICKETME->BUILDME, an unrelated commit, then the build. The journal rule picks
    the commit before the crossing (c0); the fallback would pick the build's parent (u). The
    crossing exists, so nothing changes."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", 1, False),
        ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
        ("commit", "2020-01-02T00:00:00", "u", 1, False),
        ("commit", "2020-01-03T00:00:00", "build", 2, True),
        ("cross", "2020-01-04T00:00:00", "BUILDME", "PROVEME", "forward"),
    ])
    f = _measure(repo, commons, berths)
    assert f["commit"] == c["c0"], (f["commit"], c)
    assert f.get("anchor_rule") == "journal", f.get("anchor_rule")
    assert f["measured"].get("subject.py") == ["test_the_built_value_is_two"], f["measured"]


def test_no_buildme_and_no_build_commit_refuses_naming_both():
    """No commit names the ticket and no journal crosses into BUILDME: there is no 'before the
    build' anywhere, so the run refuses, and its text names both lacks — never a silent pass."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", 1, False),
        ("commit", "2020-01-02T00:00:00", "u", 2, False),
        ("cross", "2020-01-03T00:00:00", "BUILDME", "PROVEME", "forward"),
    ])
    try:
        f = _measure(repo, commons, berths)
    except HollowUnmeasurable as why:
        text = str(why)
        assert "BUILDME" in text, text
        assert f"{FIXTURE}: build" in text, text
        return
    raise AssertionError(f"returned a reading instead of refusing: {f.get('reasons')}")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
