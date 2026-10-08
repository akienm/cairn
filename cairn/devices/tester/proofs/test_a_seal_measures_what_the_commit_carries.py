"""Proof for ticket 42075a49c121 — the pre-commit reseal holds a proof whose closure the commit
does not carry, BEFORE running it.

WHAT IS BEING PROVED. Commit 4faf4e29 (2026-10-07, 11cd253f10bc's BUILDME records) staged only
cairn/tools/base records. The hook's reseal then ran every cairn/tools/base proof over the
working tree, which carried 11cd's uncommitted transitions.py. test_transitions.py ran red,
the run raised seal-red-cairn-tools-base, and 22 seals were held after the fact (F17 (b),
~/.cairn/foreground-decisions.md). A seal and a trouble must describe the tree being
committed, so with ``index_only`` (the hook's ``--stage``) a proof whose closure is dirty
against the index is held: never run, nothing written, nothing raised.

EVERY TOOTH RUNS IN A SCRATCH GIT REPO, NEVER THE LIVE TREE, with a counting tester and a
recording raiser (the shape of test_reseal_door.py), so no tooth files a trouble into the
live store or stages into the live index.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester import reseal as door  # noqa: E402
from cairn.devices.tester.device import GREEN  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.validation_store.validation_store import (  # noqa: E402
    persist_validation, source_fingerprint, standing, validations_path_for,
)
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "42075a49c121": {
        "1": "test_a_proof_whose_closure_is_dirty_against_the_index_is_held_and_never_run",
        "2": "test_the_same_proof_runs_once_the_commit_carries_its_closure",
        "3": "test_the_stage_lists_a_held_result_and_a_manual_reseal_still_runs",
        "4": "test_the_hook_path_passes_index_only",
    }
}

_PROOF = "widget/proofs/test_widget.py"
_VALIDATION = "widget/validations/test_widget.json"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=True).stdout


def _record(proof: Path) -> dict:
    return {
        "claim": f"{proof.name} passes",
        "caller": "test_a_seal_measures_what_the_commit_carries fixture",
        "date": datetime.now().isoformat(timespec="seconds"),
        "method": "ran the proof as a subprocess and read its exit code",
        "verdict": GREEN,
        "evidence": {"source_fingerprint": source_fingerprint(str(proof)), "returncode": 0},
        "falsifier": "the proof exits non-zero, or the fingerprint of the code it proves moves",
        "horizon": "valid until the proof file or the code it proves changes",
    }


class _FakeTester:
    """Counts runs; every run returns a green taken over the tree as it is now."""

    def __init__(self):
        self.runs = 0

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        self.runs += 1
        return _record(Path(proof_path))


class _FakeRaiser:
    def __init__(self):
        self.raised, self.cleared = [], []

    def raise_trouble(self, identity, *, why, detail=None):
        self.raised.append(identity)

    def clear_trouble(self, identity, *, by, what_changed):
        self.cleared.append(identity)


def _dirty_repo() -> tuple[Path, Path]:
    """A scratch repo with one component sealed green and committed, then its code.py
    changed and left UNSTAGED, and an unrelated file of the same component staged — the
    shape of 4faf4e29: the commit carries something of the component, not its build."""
    repo = scratch_dir("cairn-sealcommit-") / "repo"
    (repo / "widget" / "proofs").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "proof@cairn.invalid")
    _git(repo, "config", "user.name", "seal-commit proof")
    (repo / "widget" / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "widget" / "notes.md").write_text("notes\n", encoding="utf-8")
    proof = repo / _PROOF
    proof.write_text("assert True\n", encoding="utf-8")
    persist_validation(_record(proof), proof_path=str(proof))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "fixture")
    assert standing(str(proof))["proven"] is True
    (repo / "widget" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    (repo / "widget" / "notes.md").write_text("notes, staged\n", encoding="utf-8")
    _git(repo, "add", "widget/notes.md")
    assert standing(str(proof))["proven"] is False, "the fixture's code moved under the seal"
    return repo, proof


# ── tooth 1 ───────────────────────────────────────────────────────────────────────────

def test_a_proof_whose_closure_is_dirty_against_the_index_is_held_and_never_run():
    repo, proof = _dirty_repo()
    seals = Path(validations_path_for(str(proof))).read_bytes()
    fake, raiser = _FakeTester(), _FakeRaiser()
    out = door.reseal(proof, index_only=True, tester=fake, raiser=raiser)
    assert fake.runs == 0, f"the proof ran over a tree the commit does not carry: {out}"
    assert out["outcome"] == "held" and out["ran"] is False, out
    assert "widget/code.py" in out["because"], out
    assert Path(validations_path_for(str(proof))).read_bytes() == seals, "a hold wrote a seal"
    assert raiser.raised == [], f"a hold raised a trouble: {raiser.raised}"


# ── tooth 2 ───────────────────────────────────────────────────────────────────────────

def test_the_same_proof_runs_once_the_commit_carries_its_closure():
    repo, proof = _dirty_repo()
    _git(repo, "add", "widget/code.py")
    fake = _FakeTester()
    out = door.reseal(proof, index_only=True, tester=fake, raiser=_FakeRaiser())
    assert fake.runs == 1 and out["ran"] is True, out
    assert out["outcome"] in ("resealed", "sealed"), out


# ── tooth 3 ───────────────────────────────────────────────────────────────────────────

def test_the_stage_lists_a_held_result_and_a_manual_reseal_still_runs():
    repo, proof = _dirty_repo()
    held = {"proof": _PROOF, "outcome": "held", "rung": 1, "ran": False,
            "because": ["widget/code.py"], "why": "fixture"}
    got = door.stage_clean_seals([held], root=repo)
    assert got["held"] == [{"validation": _VALIDATION, "because": ["widget/code.py"]}], got
    assert got["staged"] == [], got
    fake = _FakeTester()
    out = door.reseal(proof, index_only=False, tester=fake, raiser=_FakeRaiser())
    assert fake.runs == 1, f"a manual reseal (no --stage) must still measure the working tree: {out}"


# ── tooth 4 ───────────────────────────────────────────────────────────────────────────

def test_the_hook_path_passes_index_only():
    from cairn.devices.tester import cli
    seen = []
    saved = {n: getattr(door, n) for n in ("staged_files", "proofs_touching", "reseal_all",
                                            "stage_clean_seals")}

    def reseal_all(proofs, **kw):
        seen.append(kw.get("index_only"))
        return {"results": [], "refusals": [], "counts": {}, "red": []}

    try:
        door.staged_files = lambda *a, **k: ["widget/notes.md"]
        door.proofs_touching = lambda *a, **k: [Path("/nowhere/widget/proofs/test_widget.py")]
        door.reseal_all = reseal_all
        door.stage_clean_seals = lambda *a, **k: {"staged": [], "held": []}
        for stage in (True, False):
            args = argparse.Namespace(targets=[], ruling=None, timeout=120, quiet=True, stage=stage)
            cli._reseal_run(args)
    finally:
        for n, fn in saved.items():
            setattr(door, n, fn)
    assert seen == [True, False], f"the hook path must pass index_only from --stage, got {seen}"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
