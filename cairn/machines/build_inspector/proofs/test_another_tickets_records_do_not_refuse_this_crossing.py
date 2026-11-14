"""Teeth for ticket 12443bcc113f — another ticket's records do not refuse this ticket's PROVEME
crossing.

MEASURED 2026-11-12 on the Dell: 3195b3b834bc's PROVEME was refused twice by WorkingTreeDirtyRed
over records of OTHER tickets (their tickets/<id>-*.json / .state.json / .log.jsonl), written by
a second builder on the same box. With two builders on one tree, every builder's records are
the other's dirt (Q#94, outline 3.3.5.1: "it's time to reexamine that specific tooth given that
you now have two builders on the box").

Every tooth runs over SCRATCH git repos: a cairn holding one component, a sibling CairnCommons
holding two tickets' records, both committed, then edited. The artifact door's roots are pointed
at the scratch pair, so ``locate`` judges them by the live jurisdiction rules. The subject is
bound inside each tooth, never at module level.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "12443bcc113f": {
        "1": "test_another_tickets_dirty_records_do_not_refuse",
        "2": "test_a_dirty_path_no_record_claims_still_refuses",
        "3": "test_dirty_code_beside_another_tickets_records_still_refuses",
        "4": "test_the_crossing_tickets_own_dirty_records_still_refuse",
    },
}

T = "1244f1x70001"   # scratch ticket ids: never a real ticket's
U = "1244f1x70002"


def _records(tid: str) -> list[str]:
    return [f"tickets/{tid}-testing-1244-scratch.json",
            f"tickets/{tid}-testing-1244-scratch.state.json",
            f"tickets/{tid}-testing-1244-scratch.log.jsonl"]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=testing-1244",
                    "-c", "user.email=testing-1244@invalid", "-c", "commit.gpgsign=false", *args],
                   check=True, capture_output=True, text=True)


def _world() -> tuple[Path, Path, Path]:
    """(cairn repo, commons repo, component dir) — both trees committed and clean."""
    base = Path(scratch_dir("testing-1244-"))
    cairn, commons = base / "cairn", base / "CairnCommons"
    comp = cairn / "widget"
    comp.mkdir(parents=True)
    (comp / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    (commons / "tickets").mkdir(parents=True)
    for tid in (T, U):
        for rel in _records(tid):
            (commons / rel).write_text(json.dumps({"id": tid, "v": 1}) + "\n", encoding="utf-8")
    for repo in (cairn, commons):
        _git(repo, "init", "-q")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "testing-1244 fixture")
    return cairn, commons, comp


def _dirty_records(commons: Path, tid: str) -> None:
    for rel in _records(tid):
        with (commons / rel).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": tid, "v": 2}) + "\n")


def _judge(cairn: Path, commons: Path, comp: Path, ticket):
    from cairn.machines.build_inspector.inspector import working_tree_clean
    from cairn.tools.artifact import artifact
    artifact.set_diagnostic_roots({"cairn": cairn, "CairnCommons": commons})
    try:
        return working_tree_clean({"component": comp.name, "crossing_ticket": ticket}, comp,
                                  repos=[cairn, commons])
    finally:
        artifact.set_diagnostic_roots(None)


def _named(findings) -> set[str]:
    out: set[str] = set()
    for f in findings:
        for paths in ((f.get("values") or f.get("evidence") or f).get("dirty") or {}).values():
            out.update(paths)
    return out


def test_another_tickets_dirty_records_do_not_refuse():
    cairn, commons, comp = _world()
    _dirty_records(commons, U)
    got = _judge(cairn, commons, comp, T)
    assert got == [], f"U's dirty records refused T's crossing: {got}"


def test_a_dirty_path_no_record_claims_still_refuses():
    cairn, commons, comp = _world()
    _dirty_records(commons, U)
    (commons / "notes.txt").write_text("loose\n", encoding="utf-8")
    (commons / "tickets" / "README").write_text("not a record\n", encoding="utf-8")
    got = _judge(cairn, commons, comp, T)
    named = _named(got)
    assert got and {"notes.txt", "tickets/README"} <= named, f"an unclaimed path passed: {got}"
    assert not set(_records(U)) & named, f"U's records were named beside it: {got}"


def test_dirty_code_beside_another_tickets_records_still_refuses():
    cairn, commons, comp = _world()
    _dirty_records(commons, U)
    (comp / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    got = _judge(cairn, commons, comp, T)
    assert got and "widget/code.py" in _named(got), f"loose code beside U's records passed: {got}"


def test_the_crossing_tickets_own_dirty_records_still_refuse():
    cairn, commons, comp = _world()
    _dirty_records(commons, T)
    _dirty_records(commons, U)
    got = _judge(cairn, commons, comp, T)
    named = _named(got)
    assert got and set(_records(T)) <= named, f"T's own dirty records passed T's crossing: {got}"
    got = _judge(cairn, commons, comp, None)
    assert got and set(_records(U)) <= _named(got), f"a ticketless crossing excused U: {got}"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
