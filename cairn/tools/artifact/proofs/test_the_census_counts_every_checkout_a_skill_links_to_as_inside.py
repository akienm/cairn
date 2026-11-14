"""Proof: the outside-readers census counts every checkout a link resolves into as inside.

Measured 2026-11-14 on akiendell: the census (46851816800f) run from a WORKTREE read 210 "readers"
under ~/.claude where the truth was 0, because its default ``inside`` was the running checkout and
CairnCommons only, while the skill entries under ~/.claude/skills are NTFS junctions into the HOUSE
checkout, another worktree of the same repo. Run with the house checkout named inside it read 0
readers and 54 mentions, the same as akienasus. A later reader could mistake the 210 for real readers.

  1. A link (a symlink, or an NTFS junction on Windows) in a scratch ~/.claude/skills into a SECOND
     checkout of this repo (a git worktree) reads 0 readers and 0 mentions under the default
     ``inside``.
  2. The fix walls nothing off: a link into an UNRELATED git repository holding the same file still
     reads as a reader, with its path and line.

    python3 cairn/tools/artifact/proofs/test_the_census_counts_every_checkout_a_skill_links_to_as_inside.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"census-inside": {
    "1": "test_a_link_into_a_second_checkout_of_this_repo_is_inside",
    "2": "test_a_link_into_an_unrelated_repository_is_still_a_reader",
}}

_READER = "import json\n\nDOC = json.load(open('CairnCommons/tickets/abc123.json'))\n"


def _link(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":   # a junction needs no privilege; a symlink does
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)
    else:
        link.symlink_to(target, target_is_directory=True)


def _unlink(link: Path) -> None:
    if os.name == "nt":
        os.rmdir(link)   # removes the junction, never what it points at
    else:
        link.unlink()


def _census_under(home: Path) -> dict:
    from cairn.tools.artifact import outside_readers as O
    return O.census(roots=[home / ".claude"], with_crontab=False)   # inside left to the DEFAULT


def test_a_link_into_a_second_checkout_of_this_repo_is_inside():
    from cairn.tools.scratch.scratch import scratch_dir, scratch_worktree
    second = scratch_worktree("HEAD", repo_root=REPO)
    skill = second / "skills_fixture_x"
    skill.mkdir()
    (skill / "reader.py").write_text(_READER, encoding="utf-8", newline="\n")
    home = scratch_dir("census_inside_")
    link = home / ".claude" / "skills" / "x"
    _link(link, skill)
    try:
        got = _census_under(home)
    finally:
        _unlink(link)
    hits = [x for x in got["readers"] + got["mentions"] if str(home) in x["path"]]
    assert hits == [], f"a link into a second checkout of this repo was counted as outside: {hits}"
    assert {r["status"] for r in got["roots"]} == {"scanned"}, got["roots"]


def test_a_link_into_an_unrelated_repository_is_still_a_reader():
    from cairn.tools.scratch.scratch import git_env, scratch_dir
    other = scratch_dir("census_unrelated_") / "other"
    other.mkdir()
    subprocess.run(["git", "init", "-q", str(other)], check=True, env=git_env())
    (other / "reader.py").write_text(_READER, encoding="utf-8", newline="\n")
    home = scratch_dir("census_inside_")
    link = home / ".claude" / "skills" / "y"
    _link(link, other)
    try:
        got = _census_under(home)
    finally:
        _unlink(link)
    wanted = [(x["path"], x["line"]) for x in got["readers"] if "reader.py" in x["path"] and str(home) in x["path"]]
    assert wanted == [(str(link / "reader.py"), 3)], f"a link into an unrelated repo is not listed as a reader: {got['readers']}"


TEETH = [test_a_link_into_a_second_checkout_of_this_repo_is_inside,
         test_a_link_into_an_unrelated_repository_is_still_a_reader]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except BaseException as e:  # noqa: BLE001 - a proof reports, never hides
            failed += 1
            print(f"  RED  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"{'GREEN' if not failed else 'RED'} - {len(TEETH) - failed}/{len(TEETH)} teeth")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
