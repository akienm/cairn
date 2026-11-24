"""Teeth for ticket 09f5cc38e16f — the hollow reads a tooth this host cannot run as unread.

MEASURED 2026-11-23: on Linux, 8c829d9b38b8's hollow raised HollowUnmeasurable at the HEAD
baseline. Its Windows-only tooth printed UNRAN, so the tester named it in ``not_run_teeth`` and
wrote no red (device.py, ticket 64ae0df3f1f3) — and the hollow's baseline still computed
``missing = declared - teeth_green``, so the tooth read as "not green at HEAD" and the two teeth
that DID run never measured the revert. 364704f371dd held the same way.

The fixture is a two-commit repo whose build commit changes ``subject.py``. Its proof declares
tooth A (reads the subject, or not, per clause) and tooth B, which prints the UNRAN line the
tester's ``unran_only`` parses — or, for clause 4, a real failure.
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

PROOF_TIMEOUT_S = 300

PROVES = {
    "09f5cc38e16f": {
        "1": "test_a_tooth_unran_here_is_unread_and_the_tooth_that_ran_measures_the_revert",
        "2": "test_the_tooth_that_ran_still_reads_a_hollow_file_as_hollow",
        "3": "test_every_declared_tooth_unran_here_refuses_naming_this_host",
        "4": "test_a_tooth_that_ran_and_failed_at_head_still_refuses",
        "5": "test_the_seal_names_the_unread_teeth_on_the_anchor_and_only_when_there_are_any",
    },
}

FIXTURE = "f1x709f5ce01"

# Tooth A's body per clause: reads the subject, or passes without it.
_A_READS = "from subject import VALUE\n    return VALUE == 2"
_A_IGNORES = "return True"
# Tooth B's printed line: the UNRAN shape, or a real failure.
_B_UNRAN = "FAIL test_b: UNRAN: measured on another host only"
_B_FAILS = "FAIL test_b: the assertion failed"

_PROOF_SRC = '''\
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROVES = {"%(fx)s": {"1": "test_a", "2": "test_b"}}

def test_a():
    %(a)s

if __name__ == "__main__":
    ok = %(a_runs)s
    print("ok test_a" if ok else "FAIL test_a: the subject is not the build's")
    print(%(b)r)
    raise SystemExit(1)
'''


def _git(repo, *args, env=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          env=env or git_env())


def _measure(*, a_reads: bool = True, a_unran: bool = False, b_unran: bool = True) -> dict:
    """A repo + commons + berth store wired like a real ticket whose build changes subject.py."""
    tmp = scratch_dir("cairn-hollownotrun-")
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", commons / "tickets"):
        d.mkdir(parents=True)
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    a_runs = "False" if a_unran else "test_a()"
    src = _PROOF_SRC % {"fx": FIXTURE, "a": _A_READS if a_reads else _A_IGNORES,
                        "a_runs": a_runs, "b": _B_UNRAN if b_unran else _B_FAILS}
    if a_unran:
        src = src.replace('print("ok test_a" if ok else "FAIL test_a: the subject is not the build\'s")',
                          'print("FAIL test_a: UNRAN: measured on another host only")')
    _git(repo, "init", "-q", "-b", "main", env=env)
    (repo / "subject.py").write_text("VALUE = 1\n")
    (repo / "proofs" / "test_fixture.py").write_text(src)
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-qm", "before the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-01T00:00:00", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00"})
    (repo / "subject.py").write_text("VALUE = 2\n")
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-qm", f"{FIXTURE}: the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-03T00:00:00", "GIT_COMMITTER_DATE": "2020-01-03T00:00:00"})
    berth = berths / "0" / "packets" / f"decompose-20200103T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": ["subject.py"]}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    (repo / "history.json").write_text(json.dumps({"entries": [
        {"ticket": FIXTURE, "direction": "forward", "actor": "fixture", "at": "2020-01-02T00:00:00",
         "to": "BUILDME", "proven_by": "proofs/test_fixture.py"}]}))
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)


def _refusal(**kw) -> str:
    try:
        f = _measure(**kw)
    except HollowUnmeasurable as e:
        return str(e)
    raise AssertionError(f"no HollowUnmeasurable; the finding: {f.get('measured')}, {f.get('reasons')}")


def test_a_tooth_unran_here_is_unread_and_the_tooth_that_ran_measures_the_revert():
    """THE DISCRIMINATING TOOTH. B printed UNRAN at HEAD, so it measured nothing and is named
    unread on this host; A ran, and reverting the subject reds it."""
    f = _measure()
    assert f["measured"] == {"subject.py": ["test_a"]}, (f["measured"], f["reasons"])
    assert f["hollow_not_run"] == {"proofs/test_fixture.py": ["test_b"]}, f.get("hollow_not_run")
    assert f["verdict"] == "green", f["reasons"]


def test_the_tooth_that_ran_still_reads_a_hollow_file_as_hollow():
    """Carving out B does not hand the subject a coverage it never had: A ignores the subject,
    so the reading is the empty list PROVED's hollow_file rule reds."""
    f = _measure(a_reads=False)
    assert f["measured"] == {"subject.py": []}, (f["measured"], f["reasons"])
    assert f["hollow"] == ["subject.py"], f["hollow"]
    assert f["hollow_not_run"] == {"proofs/test_fixture.py": ["test_b"]}, f.get("hollow_not_run")


def test_every_declared_tooth_unran_here_refuses_naming_this_host():
    """No declared tooth ran on this host, so no reading can be taken: it refuses, loudly, and
    says not run on this host rather than not green."""
    msg = _refusal(a_unran=True)
    assert "not run on this host" in msg, msg
    assert "test_a" in msg and "test_b" in msg, msg


def test_a_tooth_that_ran_and_failed_at_head_still_refuses():
    """A real red at HEAD carries no not_run_teeth, so the baseline refuses exactly as before."""
    msg = _refusal(b_unran=False)
    assert "no reversion reading can be attributed to a file" in msg, msg
    assert "teeth_not_green" in msg and "test_b" in msg, msg
    assert "not run on this host" not in msg, msg


def _anchors_the_cli_hands_the_door(finding: dict) -> list:
    """Run ``cairn test --hollow <ticket> --seal``'s own path (cli._hollow_run) over a reading,
    the store's door captured so nothing reaches a live validation. Returns the anchor each
    record_hollow call was handed."""
    import argparse
    from cairn.devices.tester import cli, hollow
    seen: list = []
    real_measure, real_record = hollow.measure, cli.record_hollow
    hollow.measure = lambda *a, **k: finding
    cli.record_hollow = lambda path, tid, reading, **k: seen.append(k.get("anchor")) or False
    try:
        cli._hollow_run(argparse.Namespace(hollow=FIXTURE, timeout=60, quiet=True, seal=True))
    finally:
        hollow.measure, cli.record_hollow = real_measure, real_record
    assert seen, "the CLI's seal path handed the door nothing"
    return seen


def test_the_seal_names_the_unread_teeth_on_the_anchor_and_only_when_there_are_any():
    """CLAUSE 5, THE CLI'S HALF. Clauses 1-4 drive hollow.measure; the writer that carries its
    ``hollow_not_run`` onto the seal is cli._hollow_run, and reverting cli.py redded nothing
    (akienasus's hollow of 09f5cc38e16f, 2026-11-23). So the seal path runs over the fixture's
    real reading: B printed UNRAN, so the anchor carries not_run = {proof: [teeth]}. The same
    reading with nothing unread hands an anchor with no not_run key."""
    f = _measure()
    with_unran = _anchors_the_cli_hands_the_door(f)
    assert all(a.get("not_run") == {"proofs/test_fixture.py": ["test_b"]} for a in with_unran), with_unran
    none_unread = _anchors_the_cli_hands_the_door(dict(f, hollow_not_run={}))
    assert all("not_run" not in a for a in none_unread), none_unread


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
