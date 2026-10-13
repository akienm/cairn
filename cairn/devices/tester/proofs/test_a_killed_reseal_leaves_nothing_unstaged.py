"""A reseal killed mid-run leaves no unstaged seal behind: the next run adopts what still reproduces.

WHAT IS BEING PROVED (ticket 143e3974647b, clause 2 — KILLED MID-RUN). Measured on b312: the
17:06 pre-commit was killed after writing 16 green seals it never staged, and the PROVED
clearance's working_tree_clean lane refused until they were committed by hand at e8182202.
``stage_clean_seals`` runs once, AFTER the whole run, so a kill between the first seal and
the stage leaves every seal written so far modified in the working tree; and the next run read
each of them ``unchanged`` (rung 1 — the seal still reproduces) and staged nothing, because
"unchanged" wrote nothing THIS run. The leftover stood until a hand committed it.

THE BUILD (the smaller of the ticket's two options, CC's call per Akien 2026-10-09): the next
run ADOPTS a leftover — an ``unchanged`` result whose validation file differs from the index
is staged under the same clean-closure test as a fresh seal. ``unchanged`` is only ever what
``standing()`` calls proven, i.e. the seal's fingerprint reproduces now; a leftover whose
fingerprint does NOT reproduce never reads ``unchanged`` — it is re-run, and what is staged is
the new seal, not the leftover's bytes.

EVERY TOOTH RUNS IN A SCRATCH GIT REPO, NEVER THE LIVE TREE: the door runs ``git add``.
The kill is a fake tester raising ``KeyboardInterrupt`` on the second proof — what a SIGINT,
a lost session or a timeout looks like to the loop: the exception leaves ``reseal_all`` before
``stage_clean_seals`` is ever called.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "143e3974647b": {
        "1": "test_a_change_that_moves_no_seal_runs_no_proof",
        "2": "test_a_killed_runs_leftover_that_still_reproduces_is_adopted_by_the_next_run",
        "2b": "test_a_leftover_that_no_longer_reproduces_is_rerun_not_adopted",
        "2c": "test_an_unchanged_seal_already_in_the_index_stages_nothing",
    },
}

_A = "widget/proofs/test_a.py"
_B = "widget/proofs/test_b.py"
_VA = "widget/validations/test_a.json"
_JOURNAL = ".artifact-journal.jsonl"
GREEN = "green"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=True).stdout


def _repo() -> Path:
    """A scratch repo holding one committed component with two proofs and no seals yet."""
    repo = scratch_dir("cairn-killedreseal-") / "repo"
    (repo / "widget" / "proofs").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "proof@cairn.invalid")
    _git(repo, "config", "user.name", "killed-reseal proof")
    (repo / "widget" / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    for p in (_A, _B):
        (repo / p).write_text("assert True\n", encoding="utf-8")
    (repo / _JOURNAL).write_text("", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "fixture")
    return repo


def _record(repo: Path, proof: Path) -> dict:
    """A green seal shaped as the runner writes it: fingerprint taken now, closure recorded
    repo-relative to the scratch repo (the stage's clean-closure test reads it)."""
    from cairn.tools.validation_store.validation_store import source_fingerprint
    rel = str(proof.relative_to(repo))
    return {
        "claim": f"{proof.name} passes",
        "caller": "test_a_killed_reseal_leaves_nothing_unstaged fixture",
        "date": datetime.now().isoformat(timespec="seconds"),
        "method": "ran the proof as a subprocess and read its exit code",
        "verdict": GREEN,
        "evidence": {"source_fingerprint": source_fingerprint(str(proof)), "returncode": 0,
                     "fingerprint_closure": ["widget/code.py", rel]},
        "falsifier": "the proof exits non-zero, or the fingerprint of the code it proves moves",
        "horizon": "valid until the proof file or the code it proves changes",
    }


class _Tester:
    """Seals green and COUNTS runs; raises KeyboardInterrupt on any proof named in ``kill_on``."""

    def __init__(self, repo: Path, kill_on: tuple[str, ...] = ()):
        self.repo, self.kill_on, self.runs = repo, kill_on, []

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        proof = Path(proof_path)
        rel = str(proof.relative_to(self.repo))
        if rel in self.kill_on:
            raise KeyboardInterrupt(f"fixture: the run is killed at {rel}")
        self.runs.append(rel)
        return _record(self.repo, proof)


class _Raiser:
    def raise_trouble(self, identity, *, why, detail=None):
        pass

    def clear_trouble(self, identity, *, by, what_changed):
        pass


def _killed_run(repo: Path) -> None:
    """Run 1: proof A seals, then the run is killed at B — before anything is staged."""
    from cairn.devices.tester.reseal import reseal_all
    try:
        reseal_all([repo / _A, repo / _B], tester=_Tester(repo, kill_on=(_B,)), raiser=_Raiser())
    except KeyboardInterrupt:
        pass
    else:
        raise AssertionError("the fixture kill did not fire — the run reached its end")
    status = _git(repo, "status", "--porcelain", "-uall", "--", _VA)
    assert status.startswith("??") or status.startswith(" M"), (
        f"the killed run left no unstaged seal for A, so there is nothing to adopt: {status!r}")


def _next_run(repo: Path, tester: _Tester) -> tuple[dict, dict]:
    from cairn.devices.tester.reseal import reseal_all, stage_clean_seals
    out = reseal_all([repo / _A], tester=tester, raiser=_Raiser())
    return out, stage_clean_seals(out["results"], root=repo)


def test_a_change_that_moves_no_seal_runs_no_proof():
    """CLAUSE 1, AS RESHAPED (D1): ``proofs_touching`` keeps selecting the whole owning
    component; what keeps a commit from re-running every proof there is rung 1 — a proof whose
    standing seal still reproduces reads ``unchanged`` and nothing runs."""
    from cairn.devices.tester.reseal import reseal_all
    repo = _repo()
    first = _Tester(repo)
    reseal_all([repo / _A, repo / _B], tester=first, raiser=_Raiser())
    assert first.runs == [_A, _B], f"the first run did not seal both proofs: {first.runs}"
    (repo / "widget" / "notes.md").write_text("not code\n", encoding="utf-8")
    second = _Tester(repo)
    out = reseal_all([repo / _A, repo / _B], tester=second, raiser=_Raiser())
    assert second.runs == [] and [r["outcome"] for r in out["results"]] == ["unchanged"] * 2, (
        f"a change that moved no seal's fingerprint re-ran proofs: {out}, runs={second.runs}")
    (repo / "widget" / "code.py").write_text("VALUE = 9\n", encoding="utf-8")
    third = _Tester(repo)
    reseal_all([repo / _A, repo / _B], tester=third, raiser=_Raiser())
    assert third.runs == [_A, _B], (
        f"a change that moved the fingerprint was skipped — the skip is not reading the seal: "
        f"{third.runs}")


def test_a_killed_runs_leftover_that_still_reproduces_is_adopted_by_the_next_run():
    repo = _repo()
    _killed_run(repo)
    leftover = (repo / _VA).read_bytes()
    tester = _Tester(repo)
    out, staged = _next_run(repo, tester)
    assert [r["outcome"] for r in out["results"]] == ["unchanged"] and tester.runs == [], (
        f"the leftover still reproduces, so the next run must not re-run A: {out}, runs={tester.runs}")
    assert staged["staged"] == [_VA], (
        f"the next run read A unchanged and left its leftover seal unstaged — the working tree "
        f"stays dirty until a hand commits it (b312, e8182202): {staged}")
    assert _git(repo, "status", "--porcelain", "-uall", "--", _VA).startswith("A "), (
        "the leftover is staged in part, not whole")
    assert _git(repo, "show", f":{_VA}").encode() == leftover, (
        "what was adopted is not the leftover's own bytes")


def test_a_leftover_that_no_longer_reproduces_is_rerun_not_adopted():
    repo = _repo()
    _killed_run(repo)
    leftover = json.loads((repo / _VA).read_text(encoding="utf-8"))
    (repo / "widget" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(repo, "add", "widget/code.py")     # the commit carries the change: the closure is clean
    tester = _Tester(repo)
    out, staged = _next_run(repo, tester)
    assert [r["outcome"] for r in out["results"]] != ["unchanged"] and tester.runs == [_A], (
        f"a leftover whose fingerprint moved was read as still holding: {out}, runs={tester.runs}")
    committed = json.loads(_git(repo, "show", f":{_VA}"))
    assert staged["staged"] == [_VA] and committed[-1]["evidence"]["source_fingerprint"] != \
        leftover[-1]["evidence"]["source_fingerprint"], (
        f"the stale leftover went into the index instead of the re-run's seal: {staged}")


def test_an_unchanged_seal_already_in_the_index_stages_nothing():
    repo = _repo()
    _killed_run(repo)
    _git(repo, "add", "--", _VA)
    _git(repo, "commit", "-qm", "the leftover committed by hand")
    out, staged = _next_run(repo, _Tester(repo))
    assert [r["outcome"] for r in out["results"]] == ["unchanged"], out
    assert staged == {"staged": [], "held": []}, (
        f"a seal the index already carries was re-staged or held — adoption is for leftovers "
        f"only: {staged}")
    assert _git(repo, "diff", "--cached", "--name-only") == "", "the journal moved with nothing staged"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
