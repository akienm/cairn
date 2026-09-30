"""The pre-commit hook stages what it sealed — only the seals whose whole closure is the commit's.

WHAT IS BEING PROVED (2026-09-30, Akien: *"sounds like you should fix the pre-commit hook?"*).
The reseal proves the working tree and writes seals through ``persist_validation``; nothing
staged them, and 104 validation files sat modified after a day of commits. The fix,
``stage_clean_seals``, stages a seal only when every file in its closure has no unstaged
change and nothing untracked — so a committed seal describes the committed tree (Law 8) —
and stages the artifact journal beside them so ``cairn artifact check`` sees the bytes came
through the door.

EVERY TOOTH RUNS IN A SCRATCH GIT REPO, NEVER THE LIVE TREE: the function runs ``git add``,
and a proof that staged into the live index would be committing on the operator's behalf.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.reseal import stage_clean_seals  # noqa: E402
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

_PROOF = "widget/proofs/test_widget.py"
_VALIDATION = "widget/validations/test_widget.json"
_JOURNAL = ".artifact-journal.jsonl"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=True).stdout


def _repo(closure: list[str] | None = None) -> Path:
    """A scratch repo holding one committed component, then a fresh seal over it (unstaged)."""
    repo = scratch_dir("cairn-stageseals-") / "repo"
    (repo / "widget" / "proofs").mkdir(parents=True)
    (repo / "widget" / "validations").mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "proof@cairn.invalid")
    _git(repo, "config", "user.name", "stage-seals proof")
    (repo / "widget" / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / _PROOF).write_text("assert True\n", encoding="utf-8")
    (repo / _VALIDATION).write_text("[]\n", encoding="utf-8")
    (repo / _JOURNAL).write_text("", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "fixture")
    seal = {"verdict": "green", "seal": "sealed",
            "evidence": {"fingerprint_closure": closure if closure is not None
                         else ["widget/code.py", _PROOF]}}
    (repo / _VALIDATION).write_text(json.dumps([seal]) + "\n", encoding="utf-8")
    (repo / _JOURNAL).write_text('{"rel": "fixture"}\n', encoding="utf-8")
    return repo


def _staged(repo: Path) -> set[str]:
    return set(_git(repo, "diff", "--cached", "--name-only").split())


def test_a_seal_over_a_clean_closure_is_staged_with_the_journal():
    repo = _repo()
    (repo / "widget" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(repo, "add", "widget/code.py")
    got = stage_clean_seals([{"proof": _PROOF, "outcome": "resealed"}], root=repo)
    assert got["staged"] == [_VALIDATION], got
    assert _staged(repo) == {"widget/code.py", _VALIDATION, _JOURNAL}, _staged(repo)


def test_a_seal_over_an_unstaged_change_is_held_out_of_the_commit():
    repo = _repo()
    (repo / "widget" / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    got = stage_clean_seals([{"proof": _PROOF, "outcome": "sealed"}], root=repo)
    assert got["staged"] == [] and got["held"][0]["because"] == ["widget/code.py"], got
    assert _staged(repo) == set(), (
        f"a seal over a working tree the commit does not carry was staged: {_staged(repo)}")


def test_an_untracked_file_in_the_closure_holds_the_seal():
    repo = _repo(closure=["widget/code.py", "widget/helper.py", _PROOF])
    (repo / "widget" / "helper.py").write_text("X = 1\n", encoding="utf-8")
    got = stage_clean_seals([{"proof": _PROOF, "outcome": "resealed"}], root=repo)
    assert got["staged"] == [] and got["held"][0]["because"] == ["widget/helper.py"], got
    assert _staged(repo) == set(), _staged(repo)


def test_only_a_fresh_seal_is_staged():
    repo = _repo()
    results = [{"proof": _PROOF, "outcome": o} for o in
               ("unchanged", "red", "settled-red", "timeout")]
    got = stage_clean_seals(results, root=repo)
    assert got == {"staged": [], "held": []}, got
    assert _staged(repo) == set(), _staged(repo)


def test_the_hook_passes_stage_and_rechecks_the_artifact_door():
    hook = (_REPO_ROOT / "cairn/devices/tester/hooks/pre-commit").read_text(encoding="utf-8")
    reseal_at = hook.index("--reseal --stage")
    assert "cairn.tools.artifact check" in hook[reseal_at:], (
        "the hook stages seals and the journal but never re-asks the artifact question over "
        "the new index")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
