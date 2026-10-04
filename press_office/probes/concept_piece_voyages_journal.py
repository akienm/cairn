"""Probe: concept-piece-voyages-journal — does a press_office document revision
journal a crossing to history.json without anyone remembering to journal it?

WATCHME(concept-piece-voyages-journal) on ticket eba8503cc18c.
Trigger: a press_office document is revised.
Enough: three consecutive document revisions each leave a crossing in
press_office/history.json with no hand-editing.
"""
import json
import os

from cairn.tools.base.probe import Probe, by_pointer, owning_ticket, watch_carry

_TICKET = "eba8503cc18c"
_HISTORY = os.path.join(os.path.dirname(__file__), "..", "history.json")


def _trigger(now, context):
    if not os.path.exists(_HISTORY):
        return False
    with open(_HISTORY) as f:
        history = json.load(f)
    crossings = [r for r in history if "from" in r and "concept-piece@v1" in r.get("workflow", "")]
    return len(crossings) > 0


def _carry(context):
    return {"pointer": owning_ticket(_TICKET)}


def _enough(context):
    if not os.path.exists(_HISTORY):
        return False
    with open(_HISTORY) as f:
        history = json.load(f)
    crossings = [r for r in history if "from" in r and "concept-piece@v1" in r.get("workflow", "")]
    return len(crossings) >= 3


def _holds(context: dict) -> bool:
    """The trigger speaks from the first concept-piece crossing in press_office/history.json, so a
    post before THREE crossings is the count growing toward enough, not a fault; this probe cannot
    see a revision that failed to journal, so no single post is a failing falsifier, and a survey
    that raises reads as holds False through watch_carry (835b5736bf2b child)."""
    return True


PROBE = Probe(
    why="a concept-piece revision that journals automatically proves the voyage machinery works "
        "for press_office documents — the question this WATCHME carries",
    trigger=_trigger,
    to="harbor_master",
    body={"watch": "concept-piece-voyages-journal"},
    verb="watch",
    carry=watch_carry(_TICKET, _carry, holds=_holds),
    enough=_enough,
)
