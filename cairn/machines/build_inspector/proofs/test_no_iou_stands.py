"""Proof for ticket f5dbfddea8c6 — no IOU stands.

Akien, 2026-09-29: "THERE ARE TO BE NO IOUS EVER". The sieve ``no_iou_stands`` in
build_inspector reads ``git grep -n -w IOU`` over the tracked files of the repo it sits in.
Every hit in an authored file is a red, and so is a renamed resting debt in a file the
census (``iou_census.json``) names. Door-written records quote what was said when, and are
skipped (decision D7). One tooth per falsifier clause (decision D11):

  1. a planted IOU in a tracked file reds, naming its file and line, on the row that holds it,
     and a planted IOU outside every component reds on build_inspector's row (D9);
  2. the red clears once the word is removed, and a history.json, a state.json, a .jsonl and
     a validations/ file saying the word read green;
  3. a synonym ("tracked debt", "not yet enforced", ...) in a file the census names reds,
     and the same phrase in a file the census does not name reads green.

Every tooth runs over a scratch git repo, marked testing in its name. Nothing touches the
live tree.

    bin/cairn test cairn/machines/build_inspector/proofs/test_no_iou_stands.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"f5dbfddea8c6": {
    "1": "test_a_planted_iou_reds_with_its_line",
    "2": "test_removing_the_word_greens_and_records_are_skipped",
    "3": "test_a_synonym_at_a_census_site_reds",
}}

WORD = "IOU"
BI = "machines/build_inspector"


def _repo(files: dict[str, str]) -> Path:
    """A scratch git repo (marked testing) with a cairn/ census: build_inspector and one tool."""
    root = Path(tempfile.mkdtemp(prefix="testing-no-iou-stands-"))
    base = {
        f"cairn/{BI}/intention+why.json": "{}",
        "cairn/tools/testing_tool/intention+why.json": "{}",
    }
    base.update(files)
    for rel, text in base.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    for cmd in (["init", "-q"], ["add", "-A"],
                ["-c", "user.email=testing@example.invalid", "-c", "user.name=testing",
                 "commit", "-q", "-m", "testing"]):
        subprocess.run(["git", "-C", str(root), *cmd], check=True, capture_output=True)
    return root


def _red(root: Path, comp: str) -> list[dict]:
    from cairn.machines.build_inspector import inspector
    inspector._IOU_CACHE.clear()
    row = {"component": comp.rsplit("/", 1)[-1], "dir": comp}
    return inspector.no_iou_stands(row, root / "cairn" / comp)


def test_a_planted_iou_reds_with_its_line():
    root = _repo({
        "cairn/tools/testing_tool/tool.py": f"x = 1\n# the residue is an {WORD} until it is physics\n",
        "skills/testing_skill/SKILL.md": f"an {WORD} held as discipline\n",
    })
    tool = _red(root, "tools/testing_tool")
    assert len(tool) == 1, tool
    assert tool[0]["values"]["file"] == "cairn/tools/testing_tool/tool.py", tool
    assert tool[0]["values"]["line"] == 2, tool
    assert tool[0]["method"] == "no_iou_stands", tool
    home = _red(root, BI)
    assert [f["values"]["file"] for f in home] == ["skills/testing_skill/SKILL.md"], home
    assert not any(f["values"]["file"].startswith("cairn/tools/") for f in home), home


def test_removing_the_word_greens_and_records_are_skipped():
    records = {
        "cairn/tools/testing_tool/history.json": f'[{{"note": "an {WORD} was named"}}]',
        "cairn/tools/testing_tool/state.json": f'{{"why": "the {WORD} is gone"}}',
        "cairn/tools/testing_tool/journal.jsonl": f'{{"said": "{WORD}"}}\n',
        "cairn/tools/testing_tool/validations/test_x.json": f'{{"out": "{WORD}"}}',
    }
    dirty = _repo({**records, "cairn/tools/testing_tool/tool.py": f"# an {WORD}\n"})
    assert len(_red(dirty, "tools/testing_tool")) == 1, "the planted word did not red"
    clean = _repo({**records, "cairn/tools/testing_tool/tool.py": "# a ticket, 0123456789ab\n"})
    assert _red(clean, "tools/testing_tool") == [], _red(clean, "tools/testing_tool")
    assert _red(clean, BI) == [], _red(clean, BI)


def test_a_synonym_at_a_census_site_reds():
    census = {"rows": [{"path": "cairn/tools/testing_tool/tool.py", "line": 1,
                        "text": "(testing)", "rule": "testing", "disposition": "enforced",
                        "evidence": "cairn/tools/testing_tool/tool.py:1"}]}
    phrase = "same placeholder, same tracked debt"
    root = _repo({
        f"cairn/{BI}/iou_census.json": json.dumps(census),
        "cairn/tools/testing_tool/tool.py": f"# {phrase}\n",
        "cairn/tools/testing_tool/other.py": f"# {phrase}\n",
    })
    tool = _red(root, "tools/testing_tool")
    assert [(f["values"]["file"], f["values"]["line"]) for f in tool] == \
        [("cairn/tools/testing_tool/tool.py", 1)], tool
    assert "tracked debt" in tool[0]["about"], tool
    for other in ("not yet enforced", "awaiting physics", "ticket owed"):
        r = _repo({f"cairn/{BI}/iou_census.json": json.dumps(census),
                   "cairn/tools/testing_tool/tool.py": f"# this is {other} here\n"})
        assert len(_red(r, "tools/testing_tool")) == 1, other


def test_a_tree_outside_git_has_no_sites_and_a_broken_repo_is_loud():
    """A sieve fixture tree is not a repo: nothing is tracked, so nothing stands. A tree that
    claims a repo (a .git) git cannot read must refuse, never read as clean (Law 7)."""
    from cairn.machines.build_inspector import inspector
    bare = Path(tempfile.mkdtemp(prefix="testing-no-iou-stands-nogit-"))
    for rel in (f"cairn/{BI}/intention+why.json", "cairn/tools/testing_tool/intention+why.json"):
        (bare / rel).parent.mkdir(parents=True, exist_ok=True)
        (bare / rel).write_text("{}")
    (bare / "cairn/tools/testing_tool/tool.py").write_text(f"# an {WORD}\n")
    assert _red(bare, "tools/testing_tool") == []
    (bare / ".git").write_text("gitdir: /nonexistent-testing-gitdir\n")
    try:
        _red(bare, "tools/testing_tool")
    except inspector.ScanRefused:
        return
    raise AssertionError("an unreadable repo read as clean")


def main() -> int:
    teeth = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in teeth:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{len(teeth) - failed}/{len(teeth)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
