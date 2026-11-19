"""Proof for ticket 8e26b0664bb0: the inspector's own-dialog excuse reads the artifact journal as
an INDEX.

Since b15da5656579 the commons journal holds one line per path, its newest, and a door write
replaces that path's line instead of appending one. Akien, 2026-11-16: "the latest entry
remains in cairn commons, and everything else broken into... per day? per week? inside of our
.cairn/logs folder". ``_only_own_dialog`` required HEAD's journal bytes to be a prefix of the
working copy, so a refused crossing's own dialog, written through the door, read as dirt and
refused the ticket's own re-cross.

  1. over a committed scratch index, ticket T's gate dialog written through the door is excused
     for T's crossing;
  2. an index line for any other path, changed or added, is still dirt.

Every tooth runs over scratch git repos (a cairn holding one component and a CairnCommons
holding T's log and one other record), written through the artifact door in a diagnostic world
(set_diagnostic_roots, with its own "trail" key) and committed. No live repo, journal or trail
is touched.

Run bare:  PYTHONPATH=. python3 cairn/devices/codemother/machines/build_inspector/proofs/test_the_own_dialog_excuse_reads_the_index.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "8e26b0664bb0": {
        "1": "test_a_tickets_own_dialog_through_the_door_is_excused",
        "2": "test_another_paths_index_line_changed_or_added_is_dirt",
    },
}

T = "8e26f1x70001"   # scratch ticket id: never a real ticket's
LOG = f"tickets/{T}-testing-8e26-scratch.log.jsonl"
OTHER = "ideas/testing-8e26-other.json"
JOURNAL = ".artifact-journal.jsonl"
PASS = 0
FAIL = 0


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=testing-8e26",
                    "-c", "user.email=testing-8e26@invalid", "-c", "commit.gpgsign=false", *args],
                   check=True, capture_output=True, text=True)


def _line(**kw) -> str:
    return json.dumps(kw, sort_keys=True) + "\n"


def _world():
    """(cairn repo, commons repo, component dir): T's log and one other record written through the
    door, both trees committed and clean."""
    from cairn.tools.artifact import artifact as A
    from cairn.tools.scratch.scratch import scratch_dir
    base = Path(scratch_dir("cairn-8e26-"))
    cairn, commons = base / "cairn", base / "CairnCommons"
    comp = cairn / "widget"
    comp.mkdir(parents=True)
    (comp / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    (commons / "tickets").mkdir(parents=True)
    (commons / "ideas").mkdir()
    for repo in (cairn, commons):
        _git(repo, "init", "-q")
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": base / "parked",
                            "trail": base / "trail"})
    A.write(commons / LOG, _line(kind="field", actor="CC", at="t0", field="f", value=1),
            verb="cast", why="testing-8e26: the scratch ticket's log")
    A.write_json(commons / OTHER, {"n": 1}, verb="cast", why="testing-8e26: another record")
    for repo in (cairn, commons):
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "testing-8e26 fixture")
    assert len((commons / JOURNAL).read_text(encoding="utf-8").splitlines()) == 2, "not an index"
    return cairn, commons, comp


def _refusal_dialog(commons: Path) -> None:
    """What one refused crossing writes, through the door: T's gate dialog, appended to T's log."""
    from cairn.tools.artifact import artifact as A
    text = (commons / LOG).read_text(encoding="utf-8")
    A.write(commons / LOG, text + _line(kind="gate_dialog", actor=T, at="t1", gate="clearance",
                                        queued=False),
            verb="append", why=f"{T} queueme: queued=False")


def _judge(cairn: Path, commons: Path, comp: Path, ticket):
    from cairn.devices.codemother.machines.build_inspector.inspector import working_tree_clean
    return working_tree_clean({"component": comp.name, "crossing_ticket": ticket}, comp,
                              repos=[cairn, commons])


def _named(findings) -> set[str]:
    out: set[str] = set()
    for f in findings:
        for paths in ((f.get("values") or f.get("evidence") or f).get("dirty") or {}).values():
            out.update(paths)
    return out


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {fn.__name__}")


def test_a_tickets_own_dialog_through_the_door_is_excused():
    cairn, commons, comp = _world()
    _refusal_dialog(commons)
    _refusal_dialog(commons)   # two refusals in a row: the index still holds one line for the log
    assert len((commons / JOURNAL).read_text(encoding="utf-8").splitlines()) == 2, "not an index"
    got = _judge(cairn, commons, comp, T)
    assert got == [], f"T's own dialog through the door refused T's re-cross: {got}"


def test_another_paths_index_line_changed_or_added_is_dirt():
    from cairn.tools.artifact import artifact as A
    for case in ("changed", "added"):
        cairn, commons, comp = _world()
        _refusal_dialog(commons)
        if case == "changed":
            A.write_json(commons / OTHER, {"n": 2}, verb="cast", why="testing-8e26: changed")
        else:
            A.write_json(commons / "ideas/testing-8e26-new.json", {"n": 3}, verb="cast",
                    why="testing-8e26: added")
        got = _judge(cairn, commons, comp, T)
        assert got and JOURNAL in _named(got), f"{case}: another path's index line was excused: {got}"


TEETH = [test_a_tickets_own_dialog_through_the_door_is_excused,
         test_another_paths_index_line_changed_or_added_is_dirt]

if __name__ == "__main__":
    from cairn.tools.artifact import artifact as _A
    try:
        for fn in TEETH:
            _tooth(fn)
    finally:
        _A.set_diagnostic_roots(None)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
