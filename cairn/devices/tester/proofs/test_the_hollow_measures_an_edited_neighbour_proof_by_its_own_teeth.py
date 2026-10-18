"""Teeth for the hollow reading a neighbour proof the build edited by that proof's OWN teeth.

MEASURED 2026-10-12 on 86423bb5f054 (trouble hollow-reads-an-edited-neighbour-proof-as-hollow)
and 2026-10-14 on 15d6a0ef9c11 (trouble hollow-reads-a-sibling-proof-as-source): a build that
edits another ticket's proof so it keeps reading true against the new code gets that proof
reverted as source, and no declared tooth of THIS ticket can see a proof file, so it reads
HOLLOW. Naming it on the PROVEME crossing makes hollow skip it as the instrument, and then
clearance refuses PROVED because it declares no PROVES for the ticket. Two gates, no honest path.

THE RULE THESE TEETH HOLD. A proof file outside the instrument is still an instrument, and its
own red under its own reversion is what shows the edit was load-bearing: the pre-build text,
run against today's code, fails a tooth it passes at HEAD. So such a file is measured by the
teeth it loses, named '<proof>::<tooth>'. A cosmetic edit loses none and stays hollow (unseen,
complete and notify). Reverting a SOURCE file still counts declared teeth only: the neighbour's
teeth say nothing about this ticket there.

Each fixture is a scratch repo with its own journal and decompose berth, the shape of
test_the_hollow_reds_a_build_file_outside_writes_to.py.
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
    "ee0a8e836cdb": {
        "1": "test_an_edited_neighbour_proof_is_measured_by_its_own_teeth",
        "2": "test_a_cosmetic_neighbour_edit_stays_hollow",
        "3": "test_a_source_revert_counts_declared_teeth_only",
    },
}

FIXTURE = "b0dc0ffee002"
NEIGHBOUR = "proofs/test_neighbour.py"
OWN = f"{NEIGHBOUR}::test_the_neighbour_value"

_PROOF_SRC = '''\
import importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROVES = {"%s": {"1": "%s"}}

def %s():
    try:
        sys.modules.pop("subject", None)
        return importlib.import_module("subject").VALUE == %d
    except Exception:
        return False

if __name__ == "__main__":
    ok = %s()
    print(("ok" if ok else "FAIL") + " %s")
    raise SystemExit(0 if ok else 1)
'''


def _proof(ticket: str, tooth: str, value: int, tail: str = "") -> str:
    return _PROOF_SRC % (ticket, tooth, tooth, value, tooth, tooth) + tail


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


def _fixture(neighbour_after: str) -> tuple[Path, Path, Path]:
    """c0 lays down subject.py (VALUE = 1), the instrument (asserts VALUE == 2 for FIXTURE) and a
    neighbour proof for another ticket asserting VALUE == 1; BUILDME is journaled; one
    '<FIXTURE>: build' commit sets VALUE = 2 and writes the neighbour as ``neighbour_after``;
    then BUILDME->PROVEME. writes_to names subject.py and the neighbour."""
    tmp = scratch_dir("cairn-hollowneighbour-")
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    (commons / "tickets").mkdir(parents=True)
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, "2020-01-01T00:00:00", "unrelated: c0",
            {"subject.py": "VALUE = 1\n",
             "proofs/test_fixture.py": _proof(FIXTURE, "test_the_built_value_is_two", 2),
             NEIGHBOUR: _proof("feedfacef00d", "test_the_neighbour_value", 1)})
    _commit(repo, "2020-01-02T00:00:00", f"{FIXTURE}: build",
            {"subject.py": "VALUE = 2\n", NEIGHBOUR: neighbour_after})
    entries = [{"ticket": FIXTURE, "direction": "forward", "actor": "fixture", "at": at, "from": frm,
                "to": to, "proven_by": "proofs/test_fixture.py"}
               for at, frm, to in (("2020-01-01T12:00:00", "TICKETME", "BUILDME"),
                                   ("2020-01-04T00:00:00", "BUILDME", "PROVEME"))]
    (repo / "history.json").write_text(json.dumps({"entries": entries}))
    berth = berths / "0" / "packets" / f"decompose-20200101T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": ["subject.py", NEIGHBOUR]}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    return repo, commons, berths


def _measure(repo, commons, berths):
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)


def test_an_edited_neighbour_proof_is_measured_by_its_own_teeth():
    """The build re-points the neighbour from VALUE == 1 to VALUE == 2. Its pre-build text fails
    against today's subject.py, so its own tooth reds: measured, not hollow, verdict green."""
    f = _measure(*_fixture(_proof("feedfacef00d", "test_the_neighbour_value", 2)))
    assert f["measured"].get(NEIGHBOUR) == [OWN], f["measured"]
    assert NEIGHBOUR not in f["hollow"] and NEIGHBOUR not in f["unseen"], f["hollow"]
    assert f["verdict"] == "green", f["reasons"]


def test_a_cosmetic_neighbour_edit_stays_hollow():
    """The build only appends a comment to the neighbour, which still asserts VALUE == 1 and so
    reads red at HEAD and reverted alike: it loses no tooth, so it stays hollow and unseen."""
    f = _measure(*_fixture(_proof("feedfacef00d", "test_the_neighbour_value", 1, "# touched\n")))
    assert f["measured"].get(NEIGHBOUR) == [], f["measured"]
    assert NEIGHBOUR in f["unseen"], f["unseen"]


def test_a_source_revert_counts_declared_teeth_only():
    """Reverting subject.py reds the neighbour's tooth as well as the instrument's; only the
    declared instrument tooth is counted for this ticket."""
    f = _measure(*_fixture(_proof("feedfacef00d", "test_the_neighbour_value", 2)))
    assert f["measured"].get("subject.py") == ["test_the_built_value_is_two"], f["measured"]


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
