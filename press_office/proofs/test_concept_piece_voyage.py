"""Proof: a concept-piece has a voyage (ticket eba8503cc18c).

Criterion 1: press_office has state.json + history.json that the chokepoint
accepts, and a concept-piece@v1 crossing journals successfully.
Criterion 2: three backfill tickets exist with valid concept-piece@v1 workflow
strings and owning_intention=press_office/intention+why.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cairn.tools.base.transitions import parse_workflow, load_class_def
from cairn.tools.charter.projector import read_history, project

PRESS_OFFICE = os.path.join(os.path.dirname(__file__), "..")
TICKETS_DIR = os.path.expanduser("~/dev/src/CairnCommons/tickets")

BACKFILL_TICKETS = [
    "b4c4a0e48287-intention-based-design-for-humans.json",
    "2e46956c5687-graph-tree-memory-technical-brief.json",
    "79ba62aee24f-novelty-driven-graph-tree-expansion.json",
]


def test_history_exists_and_is_valid():
    path = os.path.join(PRESS_OFFICE, "history.json")
    assert os.path.exists(path), f"history.json missing at {path}"
    history = read_history(path)
    assert isinstance(history, list), "history.json must be a list"
    assert len(history) >= 1, "history must have at least the birth record"
    for rec in history:
        assert "standing" in rec, f"record at seq {rec.get('seq')} missing 'standing'"
        assert "at" in rec, f"record at seq {rec.get('seq')} missing 'at'"
        assert "seq" in rec, "record missing 'seq'"


def test_state_exists_and_projects_from_history():
    hist_path = os.path.join(PRESS_OFFICE, "history.json")
    state_path = os.path.join(PRESS_OFFICE, "state.json")
    assert os.path.exists(state_path), f"state.json missing at {state_path}"
    with open(state_path) as f:
        state = json.load(f)
    assert "cursor" in state, "state.json missing 'cursor'"
    assert "window" in state, "state.json missing 'window'"
    assert "count" in state, "state.json missing 'count'"
    history = read_history(hist_path)
    projected = project(history)
    assert projected["count"] == state["count"], (
        f"state.json count ({state['count']}) != projected ({projected['count']})"
    )


def test_concept_piece_v1_crossing_journaled():
    hist_path = os.path.join(PRESS_OFFICE, "history.json")
    history = read_history(hist_path)
    crossings = [r for r in history if "from" in r and "to" in r]
    assert len(crossings) >= 1, "no crossings in history"
    cp_crossings = [
        r for r in crossings
        if "concept-piece@v1" in r.get("workflow", "")
    ]
    assert len(cp_crossings) >= 1, (
        "no concept-piece@v1 crossings in history — "
        f"found {len(crossings)} crossing(s) but none with concept-piece@v1 workflow"
    )
    for c in cp_crossings:
        assert "proved" in c, f"crossing seq {c.get('seq')} has no 'proved' lane"
        assert c["checks_proved"] >= 1, (
            f"crossing seq {c.get('seq')} proved {c['checks_proved']} checks"
        )


def test_backfill_tickets_exist_and_parse():
    for fname in BACKFILL_TICKETS:
        path = os.path.join(TICKETS_DIR, fname)
        assert os.path.exists(path), f"backfill ticket missing: {fname}"
        with open(path) as f:
            ticket = json.load(f)
        assert ticket["node_class"] == "concept-piece", (
            f"{fname}: node_class={ticket['node_class']}, expected concept-piece"
        )
        assert ticket["owning_intention"] == "press_office/intention+why.json", (
            f"{fname}: owning_intention={ticket['owning_intention']}"
        )
        wf = parse_workflow(ticket["workflow_and_state"])
        assert wf.node_class == "concept-piece", f"{fname}: parsed node_class wrong"
        assert wf.version == "v1", f"{fname}: parsed version wrong"


def test_backfill_ticket_schema_complete():
    required = [
        "id", "title", "date", "owner", "owning_intention", "intention",
        "why", "traces_to", "falsifier", "node_class", "workflow_and_state",
        "schema_version",
    ]
    for fname in BACKFILL_TICKETS:
        path = os.path.join(TICKETS_DIR, fname)
        with open(path) as f:
            ticket = json.load(f)
        missing = [k for k in required if k not in ticket]
        assert not missing, f"{fname} missing required fields: {missing}"
        assert ticket["schema_version"] == "v1", (
            f"{fname}: schema_version={ticket['schema_version']}"
        )
        hex_id = ticket["id"]
        assert len(hex_id) == 12, f"{fname}: id length {len(hex_id)}, expected 12"
        assert all(c in "0123456789abcdef" for c in hex_id), (
            f"{fname}: id '{hex_id}' is not valid hex"
        )


def test_class_def_loads():
    class_def = load_class_def("concept-piece")
    assert "v1" in class_def["workflow_versions"], "concept-piece@v1 not in class def"
    v1 = class_def["workflow_versions"]["v1"]
    assert v1["path"] == ["THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"]


if __name__ == "__main__":
    tests = [
        test_history_exists_and_is_valid,
        test_state_exists_and_projects_from_history,
        test_concept_piece_v1_crossing_journaled,
        test_backfill_tickets_exist_and_parse,
        test_backfill_ticket_schema_complete,
        test_class_def_loads,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{passed + failed} passed")
    if failed:
        sys.exit(1)
