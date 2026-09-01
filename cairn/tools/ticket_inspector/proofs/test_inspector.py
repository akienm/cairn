"""Proofs for ticket_inspector — structural completeness checks over tickets.

Each check fires on a fixture exhibiting the defect and stays quiet on a clean
ticket. The corpus sweep is asserted by invariant (finding count > 0 and
matching the roster), never by snapshot.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.ticket_inspector.inspector import (  # noqa: E402
    inspect_ticket, inspect_corpus, ROSTER, TICKETS_DIR,
)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402


CLEAN_TICKET = {
    "id": "a1b2c3d4e5f6",
    "title": "test-clean",
    "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED",
    "intention": "a test intention",
    "why": "a test reason",
    "falsifier": {
        "proves_green": "the proof gate checks this",
        "proves_red": "what would show this node wrong",
    },
    "node_class": "code-seam",
    "traces_to": ["Law 3"],
    "how": "build the thing",
    "children": [],
    "sorted_berth": "none, because test fixture",
    "intent_berth": "none, because test fixture",
    "chart_claim": "none, because test fixture",
}


def test_clean_ticket_is_clean():
    assert inspect_ticket(CLEAN_TICKET) == [], inspect_ticket(CLEAN_TICKET)


def test_required_fields():
    for field in ("id", "title", "workflow_and_state", "intention", "why"):
        t = dict(CLEAN_TICKET)
        t[field] = ""
        ff = inspect_ticket(t)
        checks = [f["check"] for f in ff]
        assert "required_fields" in checks, (field, ff)


def test_required_falsifier():
    t = dict(CLEAN_TICKET)
    t["falsifier"] = None
    ff = inspect_ticket(t)
    checks = [f["check"] for f in ff]
    assert "required_fields" in checks, ff


def test_parseable_workflow_and_state():
    t = dict(CLEAN_TICKET, workflow_and_state="[BUILDME]")
    ff = inspect_ticket(t)
    assert any(f["check"] == "parseable_workflow_and_state" for f in ff), ff


def test_sorted_berth_present():
    t = dict(CLEAN_TICKET)
    del t["sorted_berth"]
    ff = inspect_ticket(t)
    assert any(f["check"] == "sorted_berth_present" for f in ff), ff


def test_sorted_berth_bare_none():
    t = dict(CLEAN_TICKET, sorted_berth="none")
    ff = inspect_ticket(t)
    assert any(f["check"] == "sorted_berth_present" for f in ff), ff


def test_sorted_berth_with_because_is_clean():
    t = dict(CLEAN_TICKET, sorted_berth="none, because test")
    ff = inspect_ticket(t)
    assert not any(f["check"] == "sorted_berth_present" for f in ff), ff


def test_intent_berth_present():
    t = dict(CLEAN_TICKET)
    del t["intent_berth"]
    ff = inspect_ticket(t)
    assert any(f["check"] == "intent_berth_present" for f in ff), ff


def test_chart_claim_present():
    t = dict(CLEAN_TICKET)
    del t["chart_claim"]
    ff = inspect_ticket(t)
    assert any(f["check"] == "chart_claim_present" for f in ff), ff


def test_chart_claim_not_required_at_thinkme():
    t = dict(CLEAN_TICKET,
             workflow_and_state="code-seam@v2: [THINKME] -> TICKETME -> BUILDME -> PROVED")
    if "chart_claim" in t:
        del t["chart_claim"]
    ff = inspect_ticket(t)
    assert not any(f["check"] == "chart_claim_present" for f in ff), ff


def test_falsifier_structure():
    t = dict(CLEAN_TICKET, falsifier={"proves_green": "", "proves_red": "something"})
    ff = inspect_ticket(t)
    assert any(f["check"] == "falsifier_structure" for f in ff), ff


def test_falsifier_string_accepted():
    t = dict(CLEAN_TICKET, falsifier="a plain string falsifier")
    ff = inspect_ticket(t)
    assert not any(f["check"] == "falsifier_structure" for f in ff), ff


def test_node_class_resolves():
    t = dict(CLEAN_TICKET, node_class="nonexistent-class-xyz")
    ff = inspect_ticket(t)
    assert any(f["check"] == "node_class_resolves" for f in ff), ff


def test_traces_present():
    t = dict(CLEAN_TICKET, traces_to=[])
    ff = inspect_ticket(t)
    assert any(f["check"] == "traces_present" for f in ff), ff


def test_watchme_present():
    t = dict(CLEAN_TICKET,
             workflow_and_state="code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> WATCHME(x) -> PROVED")
    ff = inspect_ticket(t)
    assert any(f["check"] == "watchme_present" for f in ff), ff


def test_watchme_with_spec_is_clean():
    t = dict(CLEAN_TICKET,
             workflow_and_state="code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> WATCHME(x) -> PROVED",
             watchme={"object": "x", "trigger": "t", "enough": "e",
                      "carrier": "c", "nexus": "n", "consumer": "u",
                      "probe": "p"})
    ff = inspect_ticket(t)
    assert not any(f["check"] == "watchme_present" for f in ff), ff


def test_buildme_has_how():
    t = dict(CLEAN_TICKET)
    del t["how"]
    ff = inspect_ticket(t)
    assert any(f["check"] == "buildme_has_how" for f in ff), ff


def test_how_not_required_at_proveme():
    t = dict(CLEAN_TICKET,
             workflow_and_state="code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED")
    if "how" in t:
        del t["how"]
    ff = inspect_ticket(t)
    assert not any(f["check"] == "buildme_has_how" for f in ff), ff


def test_children_are_ticket_ids_prose_string():
    t = dict(CLEAN_TICKET,
             children="two children described in prose, not as ticket ids")
    ff = inspect_ticket(t)
    assert any(f["check"] == "children_are_ticket_ids" for f in ff), ff


def test_children_are_ticket_ids_prose_entry():
    t = dict(CLEAN_TICKET,
             children=["a long prose description of a child that is not a ticket id " * 3])
    ff = inspect_ticket(t)
    assert any(f["check"] == "children_are_ticket_ids" for f in ff), ff


def test_children_are_ticket_ids_clean():
    t = dict(CLEAN_TICKET, children=["some-ticket-id"])
    ff = inspect_ticket(t)
    assert not any(f["check"] == "children_are_ticket_ids" for f in ff), ff


def test_child_tickets_exist():
    t = dict(CLEAN_TICKET,
             children=["definitely-not-a-real-ticket-xyz-999"])
    ff = inspect_ticket(t)
    assert any(f["check"] == "child_tickets_exist" for f in ff), ff


def test_owning_intention_resolves():
    t = dict(CLEAN_TICKET,
             owning_intention="no/such/path/intention+why.json")
    ff = inspect_ticket(t)
    assert any(f["check"] == "owning_intention_resolves" for f in ff), ff


def test_workflow_matches_node_class():
    t = dict(CLEAN_TICKET,
             node_class="concept-piece",
             workflow_and_state="code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVED")
    ff = inspect_ticket(t)
    assert any(f["check"] == "workflow_matches_node_class" for f in ff), ff


def test_workflow_matches_node_class_clean():
    t = dict(CLEAN_TICKET,
             node_class="code-seam",
             workflow_and_state="code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVED")
    ff = inspect_ticket(t)
    assert not any(f["check"] == "workflow_matches_node_class" for f in ff), ff


def test_roster_coverage():
    """Every check in the roster fires on at least one fixture."""
    fired = set()
    fixtures = [
        dict(CLEAN_TICKET, id=""),
        dict(CLEAN_TICKET, workflow_and_state="[BUILDME]"),
        {**{k: v for k, v in CLEAN_TICKET.items() if k != "sorted_berth"}},
        {**{k: v for k, v in CLEAN_TICKET.items() if k != "intent_berth"}},
        {**{k: v for k, v in CLEAN_TICKET.items() if k != "chart_claim"}},
        dict(CLEAN_TICKET, falsifier={"proves_green": "", "proves_red": "x"}),
        dict(CLEAN_TICKET, node_class="nonexistent-xyz"),
        dict(CLEAN_TICKET, traces_to=[]),
        dict(CLEAN_TICKET,
             workflow_and_state="code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> WATCHME(x) -> PROVED"),
        {**{k: v for k, v in CLEAN_TICKET.items() if k != "how"}},
        dict(CLEAN_TICKET, children="prose children"),
        dict(CLEAN_TICKET, children=["no-such-child-ticket-xyz"]),
        dict(CLEAN_TICKET, owning_intention="no/such/path.json"),
        dict(CLEAN_TICKET, node_class="concept-piece"),
    ]
    for fix in fixtures:
        for f in inspect_ticket(fix):
            fired.add(f["check"])
    missing = set(ROSTER) - fired
    assert not missing, f"checks never fired: {missing}"


def test_corpus_sweep_produces_findings():
    """The real corpus has findings — an invariant, not a snapshot count."""
    if not TICKETS_DIR.exists():
        return
    result = inspect_corpus()
    assert result["total_findings"] > 0, "corpus sweep found zero findings"
    assert result["tickets_checked"] > 0, "corpus sweep checked zero tickets"
    for check_name in result["by_check"]:
        assert check_name in ROSTER, f"finding from unknown check: {check_name}"


def test_finding_shape():
    """Every finding carries ticket, check, finding, evidence."""
    t = dict(CLEAN_TICKET, id="")
    for f in inspect_ticket(t):
        assert "ticket" in f, f
        assert "check" in f, f
        assert "finding" in f, f
        assert "evidence" in f, f
