"""Proof for ticket 8c1329759813: the plan migration selects only tickets still in flight.

Measured 2026-11-16: plan_migration.migrate selected a ticket as open when its workflow carried
no "[PROVED]". On the house commons that picked 264 tickets, and 52 of them stood at a terminal
cursor: 38 SUPERSEDED, 11 RETIRED and 3 DROPPED. akienasus's dry run over its commons would have
rewritten 26 terminal tickets (21 SUPERSEDED, 2 RETIRED, 3 DROPPED). A terminal ticket's voyage
is over, so its plan is a record and not work to migrate. The terminal set is the class's own:
the last state of each of its workflow versions plus its declared dispositions, read from
``<commons>/node_classes/<class>.json``, never a list kept here.

  1. a scratch commons holding one ticket per terminal kind of code-seam (PROVED, SUPERSEDED,
     RETIRED, DROPPED) and one in-flight ticket: only the in-flight one is selected and
     reported, and every terminal ticket's files are byte-identical after a live run;
  2. the terminal set is read from the class definition: a scratch class whose own path ends
     at a state no other class uses (testing-only) has a ticket at that state left alone, and a
     ticket at a disposition the scratch class does not declare is selected;
  3. a ticket whose class has no definition under the commons refuses the run loudly, naming
     the class, instead of being guessed open or closed.

The world: a scratch commons with the live store charter and the live node_classes copied in,
and fixture tickets, each testing-marked. Nothing in the live corpus is written.

    python3 cairn/machines/rehearsal/proofs/test_the_migration_leaves_every_terminal_ticket.py
"""
from __future__ import annotations

import json
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"8c1329759813": {
    "1": "test_only_the_in_flight_ticket_is_selected",
    "2": "test_the_terminal_set_is_the_class_definitions",
    "3": "test_an_unknown_class_refuses_the_run"}}

_COMMONS = _REPO_ROOT.parent / "CairnCommons"
if not (_COMMONS / "node_classes").is_dir():
    _COMMONS = Path.home() / "dev" / "src" / "CairnCommons"
_PATH = "THINKME -> TICKETME -> BUILDME -> PROVEME -> PROVED"
_PLAN = {"falsifier": "RED if the widget is not wired (testing)",
         "decisions": [{"n": 1, "text": "D1: wire the widget", "by": "cc"}]}


def _wf(cursor: str, node_class: str = "code-seam", path: str = _PATH) -> str:
    if cursor in path.split(" -> "):
        return f"{node_class}@v2: " + path.replace(cursor, f"[{cursor}]", 1)
    return f"{node_class}@v2: {path} -> [{cursor}]"


@contextmanager
def _world(tickets: dict, classes: dict | None = None):
    """``tickets`` is {id: workflow_and_state}; ``classes`` adds scratch class definitions."""
    top = Path(scratch_dir("testing-8c13-migration-"))
    commons = top / "CairnCommons"
    store = commons / "tickets"
    store.mkdir(parents=True)
    shutil.copyfile(_COMMONS / "tickets" / "_charter+why.json", store / "_charter+why.json")
    shutil.copytree(_COMMONS / "node_classes", commons / "node_classes")
    for name, body in (classes or {}).items():
        (commons / "node_classes" / f"{name}.json").write_text(json.dumps(body), encoding="utf-8")
    for tid, wf in tickets.items():
        plan = store / f"{tid}-testing-8c13.json"
        nc = wf.split("@", 1)[0]
        plan.write_text(json.dumps({"id": tid, "title": "testing-8c13", **_PLAN}, indent=2) + "\n",
                        encoding="utf-8")
        plan.with_name(plan.name[:-5] + ".state.json").write_text(
            json.dumps({"workflow_and_state": wf, "node_class": nc}, indent=2) + "\n",
            encoding="utf-8")
    try:
        yield commons
    finally:
        shutil.rmtree(top, ignore_errors=True)


def _bytes(commons: Path, tid: str) -> dict:
    return {p.name: p.read_bytes() for p in sorted((commons / "tickets").glob(f"{tid}-*"))}


def _migrate(commons: Path, *, dry_run: bool = False) -> dict:
    from cairn.machines.rehearsal import plan_migration
    return plan_migration.migrate(commons, dry_run=dry_run)


def test_only_the_in_flight_ticket_is_selected():
    terminal = {"8c1300000001": _wf("PROVED"), "8c1300000002": _wf("SUPERSEDED"),
                "8c1300000003": _wf("RETIRED"), "8c1300000004": _wf("DROPPED")}
    flight = {"8c1300000005": _wf("BUILDME")}
    with _world({**terminal, **flight}) as commons:
        assert set(_migrate(commons, dry_run=True)) == set(flight), "the dry run selected a terminal ticket"
        before = {tid: _bytes(commons, tid) for tid in terminal}
        got = _migrate(commons)
        assert set(got) == set(flight), f"selected {sorted(got)}, want only {sorted(flight)}"
        for tid in terminal:
            assert _bytes(commons, tid) == before[tid], f"terminal ticket {tid}'s files changed"


def test_the_terminal_set_is_the_class_definitions():
    path = "THINKME -> BUILDME -> SETTLEDTESTING"
    scratch = {"class": "testing-scratch", "dispositions": ["SUPERSEDED"],
               "workflow_versions": {"v2": {"path": path.split(" -> ")}}}
    tickets = {"8c1300000011": _wf("SETTLEDTESTING", "testing-scratch", path),
               "8c1300000012": _wf("RETIRED", "testing-scratch", path),
               "8c1300000013": _wf("BUILDME", "testing-scratch", path)}
    with _world(tickets, {"testing-scratch": scratch}) as commons:
        got = set(_migrate(commons, dry_run=True))
    assert "8c1300000011" not in got, "a ticket at its class's own path end was selected"
    assert "8c1300000012" in got, "a state the class does not declare terminal was left out"
    assert "8c1300000013" in got, "an in-flight ticket of the scratch class was left out"


def test_an_unknown_class_refuses_the_run():
    with _world({"8c1300000021": _wf("BUILDME", "testing-absent")}) as commons:
        try:
            _migrate(commons, dry_run=True)
        except Exception as exc:  # the kind is the class loader's; the words are measured
            assert "testing-absent" in str(exc), f"the refusal does not name the class: {exc}"
        else:
            raise AssertionError("a ticket with no class definition was guessed, not refused")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
