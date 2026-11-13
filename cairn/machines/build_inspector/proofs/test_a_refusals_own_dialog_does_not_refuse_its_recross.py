"""Teeth for ticket 3ba20f30a585 — a refused crossing's own gate-dialog record does not refuse
the same ticket's re-cross.

MEASURED 2026-11-12 on akiendelllinux (3195b3b834bc's log): PROVED was refused at 21:21:33 on
the_stones_are_pushed, and the re-cross at 21:22:02 was refused by working_tree_clean over
exactly two dirty paths in CairnCommons, both written by that refusal: the gate_dialog line
appended to tickets/3195b3b834bc-...log.jsonl (ticket.py append_log) and the artifact-journal
line naming that log. Each refusal cost a commit before the retry.

Every tooth runs over SCRATCH git repos: a cairn holding one component, and a sibling
CairnCommons holding one ticket log and the artifact journal, both committed, then appended
to. ``working_tree_clean`` is read through its ``repos=`` keyword or derived from the scratch
component's address. The subject is bound inside each tooth, never at module level.
"""
from __future__ import annotations

import ast
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
    "3ba20f30a585": {
        "1": "test_a_tickets_own_dialog_is_not_dirt_for_its_own_crossing",
        "2": "test_the_same_dialog_still_refuses_another_ticket_or_none",
        "3": "test_another_kind_another_actor_or_a_rewritten_line_still_refuses",
        "4": "test_any_other_dirty_path_still_refuses_and_is_named",
        "5": "test_emit_hands_the_crossing_ticket_to_both_gates",
    },
}

T = "3ba2f1x70001"   # scratch ticket ids: never a real ticket's
U = "3ba2f1x70002"
LOG = f"tickets/{T}-testing-3ba2-scratch.log.jsonl"
JOURNAL = ".artifact-journal.jsonl"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=testing-3ba2",
                    "-c", "user.email=testing-3ba2@invalid", "-c", "commit.gpgsign=false", *args],
                   check=True, capture_output=True, text=True)


def _line(**kw) -> str:
    return json.dumps(kw, sort_keys=True) + "\n"


def _world() -> tuple[Path, Path, Path]:
    """(cairn repo, commons repo, component dir) — both trees committed and clean."""
    base = Path(scratch_dir("cairn-own-dialog-"))
    cairn, commons = base / "cairn", base / "CairnCommons"
    comp = cairn / "widget"
    comp.mkdir(parents=True)
    (comp / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    (commons / "tickets").mkdir(parents=True)
    (commons / LOG).write_text(_line(kind="field", actor="CC", at="t0", field="f", value=1),
                               encoding="utf-8")
    (commons / JOURNAL).write_text(_line(path="questions/open-x.json", verb="answer"),
                                   encoding="utf-8")
    for repo in (cairn, commons):
        _git(repo, "init", "-q")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "testing-3ba2 fixture")
    return cairn, commons, comp


def _append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(text)


def _refusal_dialog(commons: Path, actor: str = T, kind: str = "gate_dialog") -> None:
    """What one refused queueme writes: the dialog line, and the journal line naming the log."""
    _append(commons / LOG, _line(kind=kind, actor=actor, at="t1", gate="clearance",
                                 queued=False))
    _append(commons / JOURNAL, _line(path=LOG, verb="append", why=f"{T} queueme: queued=False"))


def _judge(cairn: Path, commons: Path, comp: Path, ticket):
    from cairn.machines.build_inspector.inspector import working_tree_clean
    return working_tree_clean({"component": comp.name, "crossing_ticket": ticket}, comp,
                              repos=[cairn, commons])


def _named(findings) -> set[str]:
    out: set[str] = set()
    for f in findings:
        for paths in ((f.get("values") or f.get("evidence") or f).get("dirty") or {}).values():
            out.update(paths)
    return out


def test_a_tickets_own_dialog_is_not_dirt_for_its_own_crossing():
    cairn, commons, comp = _world()
    _refusal_dialog(commons)
    _refusal_dialog(commons)   # two refusals in a row: still only T's own dialog
    got = _judge(cairn, commons, comp, T)
    assert got == [], f"T's own refusal dialog refused T's re-cross: {got}"


def test_the_same_dialog_still_refuses_another_ticket_or_none():
    cairn, commons, comp = _world()
    _refusal_dialog(commons)
    for other in (U, None):
        got = _judge(cairn, commons, comp, other)
        assert got, f"T's dialog was excused for a crossing of {other!r}"
        assert {LOG, JOURNAL} <= _named(got), f"both paths not named for {other!r}: {got}"


def test_another_kind_another_actor_or_a_rewritten_line_still_refuses():
    for case in ("kind", "actor", "rewritten"):
        cairn, commons, comp = _world()
        if case == "kind":
            _refusal_dialog(commons, kind="field")
        elif case == "actor":
            _refusal_dialog(commons, actor=U)
        else:
            _refusal_dialog(commons)
            text = (commons / LOG).read_text(encoding="utf-8")
            (commons / LOG).write_text(text.replace('"value": 1', '"value": 2', 1),
                                       encoding="utf-8")
        got = _judge(cairn, commons, comp, T)
        assert got and LOG in _named(got), f"{case}: T's log was excused: {got}"


def test_any_other_dirty_path_still_refuses_and_is_named():
    cairn, commons, comp = _world()
    _refusal_dialog(commons)
    (comp / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    got = _judge(cairn, commons, comp, T)
    assert got and "widget/code.py" in _named(got), f"loose code beside T's dialog passed: {got}"
    cairn, commons, comp = _world()
    _refusal_dialog(commons)
    _append(commons / JOURNAL, _line(path="tickets/other.json", verb="cast"))
    got = _judge(cairn, commons, comp, T)
    assert got and JOURNAL in _named(got), f"a journal line naming another path passed: {got}"


def test_emit_hands_the_crossing_ticket_to_both_gates(monkeypatch):
    from cairn.tools.base import transitions
    from cairn.machines.build_inspector import inspector
    # (a) emit's two call sites pass the crossing's ticket.
    tree = ast.parse(Path(transitions.__file__).read_text(encoding="utf-8"))
    emit = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "emit")
    seen = {}
    for call in ast.walk(emit):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) \
                and call.func.id in ("_build_gate", "_clean_tree_gate"):
            kw = {k.arg: ast.unparse(k.value) for k in call.keywords}
            seen[call.func.id] = kw.get("ticket")
    want = "journal_extra.get('ticket')"
    assert seen.get("_build_gate") == want, f"emit's build gate call: {seen}"
    assert seen.get("_clean_tree_gate") == want, f"emit's clean-tree call: {seen}"
    # (b) the build-gate path carries the ticket into inspect().
    got = {}

    def fake_inspect(**kw):
        got.update(kw)
        return {"sieves_run": [], "proof_record": []}
    monkeypatch.setattr(inspector, "inspect", fake_inspect)
    transitions.inspect_build("/nonexistent/testing-3ba2/widget/history.json", ticket=T)
    assert got.get("ticket") == T, f"inspect_build did not pass the ticket: {got}"
    monkeypatch.undo()
    # (c) the clean-tree path, over a scratch world, excuses T's dialog and only T's.
    cairn, commons, comp = _world()
    _refusal_dialog(commons)
    findings, _ = transitions.inspect_clean_tree(comp, ticket=T)
    assert findings == [], f"the clean-tree seat refused T over its own dialog: {findings}"
    findings, _ = transitions.inspect_clean_tree(comp, ticket=U)
    assert findings, "the clean-tree seat excused T's dialog for U"
    # (d) inspect() stamps the crossing ticket on the rows it shakes.
    rows = []
    real = dict(inspector.SIEVES)
    monkeypatch.setattr(inspector, "SIEVES",
                        {k: (lambda row, d, _f=v: rows.append(row) or []) for k, v in real.items()})
    inspector.inspect(component="build_inspector", ticket=T)
    assert rows and all(r.get("crossing_ticket") == T for r in rows), "rows unstamped"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
