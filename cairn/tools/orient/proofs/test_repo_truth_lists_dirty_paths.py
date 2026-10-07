"""Teeth for ticket 5ea592dc82ca — repo_truth lists the dirty paths, not only how many.

Parent 316bdd5b5e62's lane must subtract the crossing ticket's own build from the tree's
dirt, and repo_truth (the one repo-state instrument) reported only a count. Each repo row
now carries ``dirty``: the working-tree paths git reports, one per entry — a rename lists
its destination only, an untracked directory lists the files inside it.

Hermetic: every tooth builds its own git repo in a tempdir (git init plus one commit,
with an inline identity), and imports orient INSIDE its body, so a reverted orient.py reds
teeth instead of breaking this file's import.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 120

from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "5ea592dc82ca": {
        "1": "test_dirty_lists_modified_untracked_and_rename_destination",
        "2": "test_dirty_paths_still_counts_porcelain_lines",
        "3": "test_a_clean_repo_lists_nothing",
    },
}


def _git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-C", str(repo), *args],
                       capture_output=True, text=True, check=True)
    return p.stdout


def _fixture(root: Path) -> Path:
    repo = root / "repo_truth_dirty_paths_fixture"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "kept.py").write_text("a = 1\n")
    (repo / "moved.py").write_text("b = 2\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture")
    return repo


def _row(repo: Path) -> dict:
    from cairn.tools.orient.orient import repo_truth
    rows = repo_truth(repos=[repo])["measured"]["repos"]
    assert len(rows) == 1, rows
    return rows[0]


def _dirty_fixture(root: Path) -> Path:
    repo = _fixture(root)
    (repo / "kept.py").write_text("a = 2\n")
    (repo / "newdir").mkdir()
    (repo / "newdir" / "new.py").write_text("c = 3\n")
    _git(repo, "mv", "moved.py", "renamed.py")
    return repo


def test_dirty_lists_modified_untracked_and_rename_destination():
    with tempfile.TemporaryDirectory() as td:
        row = _row(_dirty_fixture(Path(td)))
        assert "dirty" in row, f"repo_truth row has no 'dirty' key: {sorted(row)}"
        dirty = row["dirty"]
        assert set(dirty) == {"kept.py", "newdir/new.py", "renamed.py"}, dirty
        assert "moved.py" not in dirty and "newdir/" not in dirty and "newdir" not in dirty, dirty


def test_dirty_paths_still_counts_porcelain_lines():
    with tempfile.TemporaryDirectory() as td:
        repo = _dirty_fixture(Path(td))
        row = _row(repo)
        assert "dirty" in row, f"repo_truth row has no 'dirty' key: {sorted(row)}"
        lines = _git(repo, "status", "--porcelain").splitlines()
        assert row["dirty_paths"] == len(lines), (row["dirty_paths"], lines)


def test_a_clean_repo_lists_nothing():
    with tempfile.TemporaryDirectory() as td:
        row = _row(_fixture(Path(td)))
        assert "dirty" in row, f"repo_truth row has no 'dirty' key: {sorted(row)}"
        assert row["dirty"] == [] and row["dirty_paths"] == 0, row


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
