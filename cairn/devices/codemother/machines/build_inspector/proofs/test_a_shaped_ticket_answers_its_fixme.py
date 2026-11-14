"""Proof: a shaped ticket answers its FIXME on the entry the kick-back wrote.

Measured 2026-11-18 on 78a600419a21: a shaped (outcomes) ticket kicked into FIXME had no door
out. The FIXME gate (``crossing_fixme``, lane ``every_fixme_entry_is_answered``) counted only
``decisions`` lines with step ``FIXME <n>``, and the cast door's shape check refuses decisions
beside outcomes ("a plan is outcomes, or decisions with a falsifier, never both"). The answer
now sits on the fixme entry it answers, ``fixme[n-1].answer = {text, by, at}``, written by the
inspector's ``answer_fixme`` door into the ticket's state file, so the plan is never touched.

Teeth, one per outcome:

  1. A shaped ticket kicked into FIXME, answered through the door, crosses out: the gate passes
     and the plan file's bytes are what they were (no ``decisions`` line was added).
  2. An answer on the entry counts only after the latest kick-back: of two entries, the one
     answered after it is counted and the one answered an hour before is named.
  3. A decisions-plan ticket's ``FIXME n`` decision still counts beside an entry answered
     through the door.
  4. The door refuses, writing nothing, an entry number the list does not hold, a blank text,
     and a ticket with no fixme list.

Fixtures follow test_a_fixme_answer_binds_to_its_kick_back.py: the node class is a copy of the
live code-seam.json with ``repair_summons`` set, the ticket corpus is repointed for the length
of a tooth (and a CodeMother launched naming it, since the gate's judges run in her), and every
build name is resolved inside its tooth so a reverted build reds teeth instead of the import.

    PYTHONPATH=. python3 cairn/machines/build_inspector/proofs/test_a_shaped_ticket_answers_its_fixme.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.base import transitions  # noqa: E402
from cairn.tools.base import ticket_file  # noqa: E402

PROVES = {
    "e1d5f00a2b6c": {
        "1": "test_a_shaped_ticket_answered_through_the_door_crosses_out",
        "2": "test_an_entry_answer_counts_only_after_the_latest_kick_back",
        "3": "test_a_decisions_plans_fixme_n_still_counts",
        "4": "test_the_door_refuses_and_writes_nothing",
    },
}

_COMMONS_CLASSES = (transitions._NODE_CLASSES if transitions._NODE_CLASSES.is_dir()
                    else Path.home() / "dev" / "src" / "CairnCommons" / "node_classes")
_LIVE_CLASS = _COMMONS_CLASSES / "code-seam.json"
_AT_PROVEME = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
_NAME = "shaped_fixme_fixture_ticket"
_SHAPED = {"title": "a shaped fixture", "outcomes": [
    {"n": 1, "claim": "the fixture does a thing", "writes_to": [], "reads": [], "after": []}]}


def _class_root() -> Path:
    d = json.loads(_LIVE_CLASS.read_text(encoding="utf-8"))
    d["workflow_versions"]["v2"]["repair_summons"] = {"FIXME": "BUILDME"}
    root = scratch_dir("shaped_fixme_node_classes_")
    (root / "code-seam.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    return root


def _kicked() -> tuple[str, datetime]:
    """One real kick-back through emit into a scratch component; its history and its stamp."""
    from cairn.tools.charter import projector
    comp = scratch_dir("shaped_fixme_component_") / "comp"
    comp.mkdir()
    hist, state = str(comp / "history.json"), str(comp / "state.json")
    transitions.emit(_AT_PROVEME, "FIXME", history_path=hist, state_path=state,
                     node_class_root=_class_root(), ticket=_NAME, missing=["the fixture lacks a thing"])
    last = projector.read_history(hist)[-1]
    assert last.get("to") == "FIXME" and last.get("ticket") == _NAME, last
    return hist, datetime.fromisoformat(last["at"]).astimezone()


class _Corpus:
    """One fixture ticket, plan and state split as the store writes them, as the gate's corpus."""

    def __init__(self, plan: dict, state: dict):
        self._plan, self._state = plan, state

    def __enter__(self) -> Path:
        d = scratch_dir("shaped_fixme_tickets_")
        self.plan = d / f"{_NAME}.json"
        self.plan.write_text(json.dumps(self._plan, indent=2) + "\n", encoding="utf-8")
        ticket_file.state_path(self.plan).write_text(json.dumps(self._state, indent=2) + "\n",
                                                     encoding="utf-8")
        self._saved = ticket_file._TICKETS
        ticket_file._TICKETS = d
        from cairn.tools.inspect_wire.inspect_wire import launch
        self._world = launch(ticket_store=d)
        self._world.__enter__()
        return self.plan

    def __exit__(self, *a):
        try:
            self._world.__exit__(*a)
        finally:
            ticket_file._TICKETS = self._saved
        return False


def _entries(k: int) -> list[dict]:
    return [{"n": i, "kind": "hand_kickback", "missing": f"thing {i}"} for i in range(1, k + 1)]


def _stamp(at: datetime) -> str:
    return at.astimezone(timezone.utc).isoformat(timespec="seconds")


def _gate(hist: str) -> str | None:
    """None when the FIXME gate passes, else its refusal's words."""
    try:
        transitions._fixme_gate(_NAME, history_path=hist)
    except transitions.FixmeGateRed as e:
        return str(e)
    return None


def test_a_shaped_ticket_answered_through_the_door_crosses_out():
    from cairn.machines.build_inspector.inspector import answer_fixme
    hist, _kick = _kicked()
    with _Corpus(_SHAPED, {"fixme": _entries(1)}) as plan:
        before = plan.read_bytes()
        assert _gate(hist) is not None, "an unanswered entry must hold the crossing"
        answer_fixme(_NAME, 1, "the thing was done, and here is the reading", by="cc")
        refusal = _gate(hist)
        assert refusal is None, f"the entry answered through the door did not open the gate: {refusal}"
        assert plan.read_bytes() == before, "the door touched the plan; the answer belongs in the state"
        body = ticket_file.read_ticket(plan)
        assert "decisions" not in body, body
        ans = body["fixme"][0].get("answer") or {}
        assert ans.get("text", "").startswith("the thing was done") and ans.get("by") == "cc", ans


def test_an_entry_answer_counts_only_after_the_latest_kick_back():
    hist, kick = _kicked()
    entries = _entries(2)
    entries[0]["answer"] = {"text": "answered after", "by": "cc", "at": _stamp(kick + timedelta(hours=1))}
    entries[1]["answer"] = {"text": "answered before", "by": "cc", "at": _stamp(kick - timedelta(hours=1))}
    with _Corpus(_SHAPED, {"fixme": entries}):
        refusal = _gate(hist)
    assert refusal is not None, "an answer an hour before the kick-back was counted"
    assert "[2]" in refusal, f"the refusal must name only entry 2, the stale one: {refusal}"


def test_a_decisions_plans_fixme_n_still_counts():
    from cairn.machines.build_inspector.inspector import answer_fixme
    hist, kick = _kicked()
    plan = {"title": "a decisions fixture", "falsifier": {"clauses": [{"n": 1, "claim": "c"}]},
            "decisions": [{"n": 1, "step": "FIXME 1", "text": "answered the old way",
                           "at": _stamp(kick + timedelta(seconds=1)), "writes_to": [], "reads": []}]}
    with _Corpus(plan, {"fixme": _entries(2)}):
        answer_fixme(_NAME, 2, "answered on the entry", by="cc")
        refusal = _gate(hist)
    assert refusal is None, f"FIXME 1 as a decision beside FIXME 2 on its entry should pass: {refusal}"


def test_the_door_refuses_and_writes_nothing():
    from cairn.machines.build_inspector.inspector import FixmeAnswerRefused, answer_fixme
    for state, n, text, why in (({"fixme": _entries(1)}, 2, "an answer", "entry 2 does not stand"),
                                ({"fixme": _entries(1)}, 1, "   ", "a blank text"),
                                ({}, 1, "an answer", "no fixme list")):
        with _Corpus(_SHAPED, state) as plan:
            sp = ticket_file.state_path(plan)
            before = (plan.read_bytes(), sp.read_bytes())
            try:
                answer_fixme(_NAME, n, text, by="cc")
            except FixmeAnswerRefused:
                pass
            else:
                raise AssertionError(f"the door wrote an answer for {why}")
            assert (plan.read_bytes(), sp.read_bytes()) == before, f"the refusal for {why} wrote"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
