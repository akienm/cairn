"""Teeth for ticket 92e0d158b1bc — a voyage starts on a clean tree.

/sail's step 0 sweeps both repos before the chart: any uncommitted change is stashed
(one stash per dirty repo, named by its commit sha, which does not shift the way
stash@{n} does) and raised as ONE trouble naming every path, every stash sha and the
timing suspects (the ticket the newest commons journal line under tickets/ names, then
Akien). Ruling 8w layer 2, narrowed by F11, cleared by 8x ("yes to all.").

Hermetic: every tooth builds two git repos (cairn-like and commons-like) in a tempdir
with an inline identity, passes them, a fixture journal and a ModuleRaiser rooted in the
tempdir explicitly, and never touches the live roots. sweep is imported INSIDE each
tooth, so a reverted skills/sail/sweep.py reds teeth instead of breaking the import.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 120

from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "92e0d158b1bc": {
        "1": "test_dirt_in_both_repos_is_stashed_and_named_in_one_trouble",
        "2": "test_each_stash_restores_its_paths_byte_identical",
        "3": "test_suspects_follow_the_commons_journal",
        "4": "test_clean_repos_raise_nothing_and_stash_nothing",
        "5": "test_dirt_only_in_commons_stashes_only_there",
    },
    "41202d4c8d3b": {
        "1": "test_skill_md_calls_the_sweep",
        "2": "test_skill_md_sweeps_before_it_charts",
    },
}

_SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"
_SWEEP_CALL = "python3 -m skills.sail.sweep"
_CHART_HEADING = "## 0. Chart it"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True).stdout


def _world(tmp: Path) -> tuple[Path, Path]:
    repos = []
    for name in ("cairn", "CairnCommons"):
        r = tmp / name
        r.mkdir()
        _git(r, "init", "-q")
        (r / "kept.txt").write_text(f"{name} committed\n")
        _git(r, "add", "kept.txt")
        _git(r, "commit", "-q", "-m", "init")
        repos.append(r)
    return repos[0], repos[1]


def _raiser(tmp: Path):
    from cairn.tools.base.diagnostic import ModuleRaiser
    inst = tmp / "instance"
    inst.mkdir(exist_ok=True)
    return ModuleRaiser("sail", roots={"repo": tmp / "cairn", "commons": tmp / "CairnCommons", "instance": inst})


def _dirty(repo: Path, tag: str) -> dict[str, bytes]:
    (repo / "kept.txt").write_text(f"{tag} modified\n")
    (repo / "loose.txt").write_text(f"{tag} untracked\n")
    return {"kept.txt": (repo / "kept.txt").read_bytes(), "loose.txt": (repo / "loose.txt").read_bytes()}


def _stashes(repo: Path) -> str:
    return _git(repo, "stash", "list")


def _dirty_paths(repo: Path) -> list[str]:
    from cairn.tools.orient.orient import repo_truth
    return repo_truth(repos=[repo])["measured"]["repos"][0]["dirty"]


def _detail(record: dict) -> dict:
    return record["values"]["detail"]


def test_dirt_in_both_repos_is_stashed_and_named_in_one_trouble():
    from skills.sail.sweep import sweep
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        a, b = _world(tmp)
        _dirty(a, "a")
        _dirty(b, "b")
        rec = sweep(repos=[a, b], ticket="cccccccccccc", raiser=_raiser(tmp), journal=tmp / "none.jsonl")
        assert rec is not None, "dirt in both repos must raise a trouble"
        assert rec["pointer"] == "orphaned-changes-at-sail", rec
        rows = {Path(r["repo"]).name: r for r in _detail(rec)["repos"]}
        assert set(rows) == {"cairn", "CairnCommons"}, rows
        for name, row in rows.items():
            assert sorted(row["paths"]) == ["kept.txt", "loose.txt"], (name, row)
            assert len(row["stash"]) == 40, (name, row)
        assert _dirty_paths(a) == [] and _dirty_paths(b) == []


def test_each_stash_restores_its_paths_byte_identical():
    from skills.sail.sweep import sweep
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        a, b = _world(tmp)
        before = {"cairn": _dirty(a, "a"), "CairnCommons": _dirty(b, "b")}
        rec = sweep(repos=[a, b], ticket="cccccccccccc", raiser=_raiser(tmp), journal=tmp / "none.jsonl")
        for row in _detail(rec)["repos"]:
            repo = Path(row["repo"])
            _git(repo, "stash", "apply", row["stash"])
            for path, content in before[repo.name].items():
                assert (repo / path).read_bytes() == content, (repo.name, path)


def test_suspects_follow_the_commons_journal():
    from skills.sail.sweep import sweep
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        a, b = _world(tmp)
        journal = tmp / "journal.jsonl"
        journal.write_text(
            json.dumps({"at": "2026-10-07T10:00:00Z", "path": "tickets/bbbbbbbbbbbb-older.json"}) + "\n"
            + json.dumps({"at": "2026-10-07T11:00:00Z", "path": "tickets/aaaaaaaaaaaa-newer.json"}) + "\n"
            + json.dumps({"at": "2026-10-07T12:00:00Z", "path": "slates/s.json"}) + "\n")
        _dirty(a, "a")
        rec = sweep(repos=[a, b], ticket="cccccccccccc", raiser=_raiser(tmp), journal=journal)
        assert _detail(rec)["suspects"] == ["aaaaaaaaaaaa", "Akien"], _detail(rec)
        _dirty(a, "a2")
        rec = sweep(repos=[a, b], ticket="cccccccccccc", raiser=_raiser(tmp), journal=tmp / "absent.jsonl")
        assert _detail(rec)["suspects"] == ["Akien"], _detail(rec)


def test_clean_repos_raise_nothing_and_stash_nothing():
    from skills.sail.sweep import sweep
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        a, b = _world(tmp)
        raiser = _raiser(tmp)
        log_before = sorted(p for p in (tmp / "instance").rglob("*") if p.is_file())
        rec = sweep(repos=[a, b], ticket="cccccccccccc", raiser=raiser, journal=tmp / "none.jsonl")
        assert rec is None, rec
        assert _stashes(a) == "" and _stashes(b) == ""
        assert sorted(p for p in (tmp / "instance").rglob("*") if p.is_file()) == log_before, \
            "a clean sweep must write no emission"


def test_dirt_only_in_commons_stashes_only_there():
    from skills.sail.sweep import sweep
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        a, b = _world(tmp)
        _dirty(b, "b")
        rec = sweep(repos=[a, b], ticket="cccccccccccc", raiser=_raiser(tmp), journal=tmp / "none.jsonl")
        rows = _detail(rec)["repos"]
        assert [Path(r["repo"]).name for r in rows] == ["CairnCommons"], rows
        assert _stashes(a) == ""
        assert len(_stashes(b).splitlines()) == 1


# SKILL.md IS /sail's only wiring to the sweep (ticket 41202d4c8d3b, 8y): nothing else calls it,
# so dropping or reordering that one line would silently undo the clean start. Each tooth
# checks the live text and then shows that the same helper reds on a mutated copy of it.

def test_skill_md_calls_the_sweep():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert _sweep_order_problem(text) is None, _sweep_order_problem(text)
    without = "\n".join(line for line in text.splitlines() if _SWEEP_CALL not in line)
    assert _sweep_order_problem(without) == "absent", _sweep_order_problem(without)


def test_skill_md_sweeps_before_it_charts():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert _sweep_order_problem(text) is None, _sweep_order_problem(text)
    lines = text.splitlines()
    sweep = next(line for line in lines if _SWEEP_CALL in line)
    rest = [line for line in lines if line != sweep]
    at = next(i for i, line in enumerate(rest) if line.startswith(_CHART_HEADING))
    moved = "\n".join(rest[:at + 1] + [sweep] + rest[at + 1:])
    assert _sweep_order_problem(moved) == "after /chart", _sweep_order_problem(moved)
    headless = "\n".join(line for line in lines if not line.startswith(_CHART_HEADING))
    assert _sweep_order_problem(headless) == "no /chart heading", _sweep_order_problem(headless)


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
