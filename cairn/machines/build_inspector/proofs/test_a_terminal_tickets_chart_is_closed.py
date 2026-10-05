"""A ticket at any terminal state has its chart closed, not only one at PROVED (ticket e85878726213).

_component_tickets decides which of a component's tickets are still in work; the chart judges
read only those tickets' packets. It used to count every ticket not at [PROVED] as active, so a
SUPERSEDED ticket's six-week-old chart (b5b5e0483af1's 2026-08-17 decompose berth) held
164da559823d's PROVED crossing on ground_loop. Terminal is the system's word
(cairn.tools.base.transitions.TERMINAL_STATES), and the inspector now reads it.

Three teeth: over a scratch tickets root, a SUPERSEDED ticket is closed while a BUILDME one is
kept; a ticket whose workflow does not parse is kept (an unreadable cursor still reds); and the
live ground_loop sweep carries no finding from b5b5e0483af1. The inspector is imported inside
each tooth, so a reverted inspector.py reds a tooth instead of breaking the file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"e85878726213": {
    "1": "test_a_superseded_ticket_is_closed_and_a_buildme_one_is_kept",
    "2": "test_an_unparseable_ticket_is_kept",
    "3": "test_ground_loop_carries_no_superseded_chart",
}}

_FIXTURES = {
    "aaaaaaaaaa01": ("scratch-superseded",
                     "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [SUPERSEDED]"),
    "aaaaaaaaaa02": ("scratch-buildme",
                     "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"),
    "aaaaaaaaaa03": ("scratch-unparseable", "not a workflow at all"),
}


def _active_over_scratch() -> set:
    """_component_tickets over a scratch root holding the three fixture tickets."""
    from cairn.machines.build_inspector import inspector
    td = scratch_dir("cairn-terminal-tickets-chart-")
    filed = td / "CairnCommons" / "tickets"
    filed.mkdir(parents=True)
    comp = td / "cairn" / "comp"
    comp.mkdir(parents=True)
    for tid, (slug, state) in _FIXTURES.items():
        (filed / f"{tid}-{slug}.json").write_text(
            json.dumps({"id": tid, "title": slug, "workflow_and_state": state}))
    (comp / "history.json").write_text(json.dumps([{"ticket": tid} for tid in _FIXTURES]))
    saved = inspector._TICKETS_ROOT
    inspector._TICKETS_ROOT = str(td / "cairn")
    try:
        return inspector._component_tickets(comp)
    finally:
        inspector._TICKETS_ROOT = saved


def test_a_superseded_ticket_is_closed_and_a_buildme_one_is_kept():
    active = _active_over_scratch()
    assert "aaaaaaaaaa02" in active, sorted(active)
    assert not any(a.startswith("aaaaaaaaaa01") or "scratch-superseded" in a for a in active), sorted(active)


def test_an_unparseable_ticket_is_kept():
    active = _active_over_scratch()
    assert "aaaaaaaaaa03" in active, sorted(active)


def _live_tickets_root() -> str:
    """A cairn checkout whose sibling holds the live commons: this repo when CairnCommons sits beside
    it, else the home checkout — hollow's worktree under /tmp has no commons beside it, and the
    ticket states this tooth reads live only there (hollow.py resolves it the same way)."""
    if (_REPO_ROOT.parent / "CairnCommons" / "tickets").is_dir():
        return str(_REPO_ROOT)
    return str(Path.home() / "dev" / "src" / "cairn")


def test_ground_loop_carries_no_superseded_chart():
    from cairn.machines.build_inspector import inspector
    from cairn.tools.chain import grammar
    live = _live_tickets_root()
    saved_root, saved_exists = inspector._TICKETS_ROOT, inspector.ref_exists
    try:
        # the code under test, over the live records: ticket states and commons-relative
        # refs (tickets/...) are read where the commons actually is
        inspector._TICKETS_ROOT = live
        inspector.ref_exists = lambda r: saved_exists(r) or grammar.ref_exists(r, live)
        found = inspector.inspect(component="ground_loop")["findings"]
    finally:
        inspector._TICKETS_ROOT, inspector.ref_exists = saved_root, saved_exists
    assert isinstance(found, list), type(found)
    hits = [f for f in found if "b5b5e0483af1" in str(f)
            or "staleness-is-about-this-process-not-about-disk" in str(f)]
    assert hits == [], [f.get("method") for f in hits]


def main() -> int:
    fails = 0
    for name in PROVES["e85878726213"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
