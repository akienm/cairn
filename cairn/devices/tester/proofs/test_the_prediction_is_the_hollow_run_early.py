"""Teeth for ticket fb47d26f7a43 — the prediction is the hollow run early.

Peer F18 (2026-10-07): 11cd253f10bc's hollow refused ('no reversion reading can be
attributed'; all 4 teeth failed at HEAD) while the builder's pre-PROVEME prediction had been
green, because the prediction ran beside a CairnCommons symlink next to the scratchpad and the
hollow's worktree has nothing beside it. Two constructions kept equal by hand. So the
prediction becomes the hollow's own measurement, run before any proven_by exists:
``measure(ticket, proofs=[...])`` and ``cairn test --hollow <ticket> --proof <path>``, which
never seals (a seal lands only from the proofs the crossing named).

The fixture is a repo with a build commit naming the ticket, and a CairnCommons beside it as
on disk. ``measure`` is imported at module level because it stands before this build; the
``proofs=`` keyword is what the build adds, and it is only reached inside a tooth.
"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.hollow import measure, HollowUnmeasurable  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROOF_TIMEOUT_S = 600

PROVES = {
    "fb47d26f7a43": {
        "1": "test_a_ticket_with_no_proven_by_is_measured_over_the_named_proof",
        "2": "test_the_prediction_and_the_hollow_read_a_commons_reader_alike",
        "3": "test_a_prediction_refuses_to_seal",
    },
}

FIXTURE = "f1x7b47ed0001"

# The fixture proof checks the build file; when READS_COMMONS it also reads the commons
# through the beside path, the way 11cd253f10bc's proofs did.
_PROOF_SRC = '''\
import json
from pathlib import Path

PROVES = {"%s": {"1": "test_the_value_is_two"}}
READS_COMMONS = %s

def test_the_value_is_two():
    here = Path(__file__).resolve().parents[1]
    try:
        if READS_COMMONS:
            json.loads((here.parent / "CairnCommons" / "classes" / "x.json").read_text())
        return (here / "src.py").read_text().strip() == "VALUE = 2"
    except Exception:
        return False

if __name__ == "__main__":
    ok = test_the_value_is_two()
    print(("ok" if ok else "FAIL") + " test_the_value_is_two")
    raise SystemExit(0 if ok else 1)
'''

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
PROOF = "proofs/test_fixture.py"


def _git(repo, *args, when=None):
    env = dict(_ENV)
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(*, reads_commons: bool) -> tuple[Path, Path, Path]:
    """repo/ (proof, src.py built 1 -> 2 by a commit naming the ticket) and CairnCommons/ beside
    it; the only BUILDME crossing names NO proof, as at the moment a builder predicts."""
    tmp = scratch_dir("cairn-hollowpredict-")
    repo, commons, berths = tmp / "repo", tmp / "CairnCommons", tmp / "berths"
    for d in (repo / "proofs", commons / "classes", commons / "tickets"):
        d.mkdir(parents=True)
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    (commons / "classes" / "x.json").write_text(json.dumps({"value": 1}))
    _git(repo, "init", "-q", "-b", "main")
    (repo / PROOF).write_text(_PROOF_SRC % (FIXTURE, reads_commons))
    (repo / "src.py").write_text("VALUE = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "before the build", when="2020-01-01T00:00:00")
    (repo / "src.py").write_text("VALUE = 2\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"{FIXTURE}: the build", when="2020-01-03T00:00:00")
    berth = berths / "0" / "packets" / f"decompose-20200103T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": ["src.py"]}]}))
    _crossings(repo, proven_by=None)
    return repo, commons, berths


def _crossings(repo: Path, *, proven_by: str | None) -> None:
    entry = {"ticket": FIXTURE, "direction": "forward", "actor": "fixture",
             "at": "2020-01-02T00:00:00", "to": "BUILDME"}
    if proven_by:
        entry["proven_by"] = proven_by
    (repo / "history.json").write_text(json.dumps({"entries": [entry]}))


def _outcome(call) -> dict:
    """A finding's reading, or the refusal's text — the two shapes a measurement can end in."""
    try:
        f = call()
    except HollowUnmeasurable as e:
        return {"refused": str(e)}
    return {"verdict": f["verdict"], "measured": f["measured"], "hollow": f["hollow"]}


def test_a_ticket_with_no_proven_by_is_measured_over_the_named_proof():
    """THE DISCRIMINATING TOOTH FOR hollow.py. No crossing names a proof, so the hollow as it
    stood refused ('no crossing names a proof'); handed the proof by name, the same worktree
    and the same reversion read src.py as load-bearing."""
    repo, commons, berths = _fixture(reads_commons=False)
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60,
                proofs=[PROOF])
    assert f["measured"] == {"src.py": ["test_the_value_is_two"]}, (f["measured"], f["skipped"])
    assert f["verdict"] == "green", f


def test_the_prediction_and_the_hollow_read_a_commons_reader_alike():
    """F18's shape. The proof reads the commons through REPO.parent, and writes_to names no
    commons file, so the hollow's worktree stands no commons beside it. A prediction that ran
    anywhere else could go green here; run early through measure it reads exactly what the
    hollow reads once proven_by names the proof — the same verdict, the same refusal text."""
    repo, commons, berths = _fixture(reads_commons=True)
    kw = dict(repo_root=repo, commons=commons, berths_root=berths, timeout=60)
    early = _outcome(lambda: measure(FIXTURE, proofs=[PROOF], **kw))
    _crossings(repo, proven_by=PROOF)
    late = _outcome(lambda: measure(FIXTURE, **kw))
    assert early == late, {"prediction": early, "hollow": late}
    # And it is the refusal F18's builder never saw coming: nothing stands beside the worktree.
    assert "refused" in late and "teeth_not_green" in late["refused"], late


def test_a_prediction_refuses_to_seal():
    """--proof names proofs by hand; a seal lands only from the proofs the crossing named. So
    --proof with --seal exits non-zero, says --seal, and nothing is written beside the proof."""
    from cairn.devices.tester.cli import main
    repo, _commons, _berths = _fixture(reads_commons=False)
    proof = repo / PROOF

    def tree() -> list[str]:
        return sorted(str(p.relative_to(repo)) for p in repo.rglob("*") if ".git" not in p.parts)

    before = tree()
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        try:
            rc = main(["--hollow", FIXTURE, "--proof", str(proof), "--seal"])
        except SystemExit as e:  # argparse refusing an unknown flag is not this refusal
            rc = ("SystemExit", e.code)
    text = err.getvalue()
    assert isinstance(rc, int) and rc != 0, (rc, text)
    assert "--seal" in text and "unrecognized" not in text, text
    assert tree() == before, (before, tree())


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
