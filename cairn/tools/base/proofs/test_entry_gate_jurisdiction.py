"""Proof: the entry gate guards a CROSSING, not a state.

Ticket ``the-buildme-gates-guard-a-crossing-not-a-state`` (2026-08-14). The gate's
jurisdiction was widened from ``target == "BUILDME"`` (one edge) to also fire at
``wf.here == "BUILDME"`` (leaving BUILDME), so a ticketed build that opened its
journal with the cursor already past BUILDME gets the same chart/intent/sorted
checks as one that crossed into BUILDME.

THREE LEGS:
  A. A complete ticket at BUILDME crosses to PROVEME — the entry gate passes.
  B. An incomplete ticket (no chart chain) at BUILDME crosses to PROVEME — EntryGateRed.
  C. An unticketed crossing out of BUILDME records "not_checked" — not refused.

PLUS: the entry_gate field always distinguishes states (never absent).

    python3 cairn/tools/base/proofs/test_entry_gate_jurisdiction.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import transitions
from cairn.tools.charter import projector

_AT_BUILDME = "code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"
_AT_TICKET = "code-seam@v1: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> LEARNME -> PROVED"


def _entry_world(d: Path, *, cast=("widget",), claims=()):
    tickets = d / "tickets"
    tickets.mkdir(exist_ok=True)
    for t in cast:
        (tickets / f"{t}.json").write_text("{}")
    berths = d / "berths"
    (berths / "0" / "packets").mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(claims):
        (berths / "0" / "packets" / f"validate-20260729T00000{i}-feed.json").write_text(
            json.dumps({"ticket": t}))
    return tickets, berths


def _cleared(comp: Path) -> dict:
    from cairn.devices.tester.validation_store import persist_validation, source_fingerprint
    proof = comp / "proofs" / "sealed_fixture.py"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("# fixture\n")
    persist_validation({
        "claim": "fixture proven",
        "caller": "test_entry_gate_jurisdiction.py",
        "date": "2026-08-28T00:00:00",
        "method": "fixture seal",
        "verdict": "green",
        "evidence": {"source_fingerprint": source_fingerprint(str(proof))},
        "falsifier": "source moves",
        "horizon": "until source changes",
    }, proof_path=str(proof))
    return {"cleared_by": "fixture-owner", "proven_by": str(proof),
            "proven_seal_date": "2026-08-28T00:00:00"}


def test_leg_a_complete_ticket_passes_at_leaving_buildme():
    """A cast ticket WITH a claiming chart chain at BUILDME crosses to PROVEME — the
    widened entry gate fires and PASSES. This is route B from the ticket, now green."""
    import cairn.machines.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        tickets, berths = _entry_world(base, cast=("widget",), claims=("widget",))
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            comp = base / "fixture_component"
            comp.mkdir(exist_ok=True)
            hist = str(comp / "history.json")
            state = str(comp / "state.json")
            extra = {"ticket": "widget"}
            extra.update(_cleared(comp))
            new = transitions.emit(_AT_BUILDME, "PROVEME",
                                   history_path=hist, state_path=state, **extra)
            assert "[PROVEME:waiting]" in new, f"crossing did not land: {new}"
            rec = projector.read_history(hist)[0]
            assert rec["entry_gate"].startswith("clean"), \
                f"the entry gate must pass for a complete ticket: {rec['entry_gate']}"
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


def test_leg_b_chartless_ticket_refused_at_leaving_buildme():
    """A cast ticket with NO chart chain at BUILDME crosses to PROVEME — the widened
    entry gate fires and REFUSES with EntryGateRed. This is the ticket's core falsifier:
    route B now refuses for the same reason route A does."""
    import cairn.machines.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        tickets, berths = _entry_world(base, cast=("widget",), claims=())
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            comp = base / "fixture_component"
            comp.mkdir(exist_ok=True)
            hist = str(comp / "history.json")
            state = str(comp / "state.json")
            try:
                transitions.emit(_AT_BUILDME, "PROVEME",
                                 history_path=hist, state_path=state, ticket="widget")
            except transitions.EntryGateRed as e:
                assert "buildme_rides_the_chart" in [f["method"] for f in e.findings], \
                    f"the refusal must name buildme_rides_the_chart: {e.findings}"
            else:
                raise AssertionError(
                    "a chartless ticket at BUILDME crossed to PROVEME ungated — "
                    "the widened predicate is not wired")
            assert not Path(hist).exists(), \
                "a REFUSED crossing must write no record of truth"
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


def test_leg_c_unticketed_crossing_records_not_checked():
    """An unticketed crossing out of BUILDME records 'not_checked' in the entry_gate
    field rather than refusing — unnamed crossings are not builds."""
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        comp = base / "fixture_component"
        comp.mkdir(exist_ok=True)
        hist = str(comp / "history.json")
        state = str(comp / "state.json")
        extra = _cleared(comp)
        new = transitions.emit(_AT_BUILDME, "PROVEME",
                               history_path=hist, state_path=state, **extra)
        assert "[PROVEME:waiting]" in new, f"crossing did not land: {new}"
        rec = projector.read_history(hist)[0]
        assert rec["entry_gate"] == "not_checked", \
            f"unticketed crossing must record 'not_checked', got: {rec['entry_gate']!r}"


def test_entry_gate_field_always_present():
    """The entry_gate field is always present in the journal record — "not_applicable"
    when no build-relevant crossing, never absent (ticket's gate (3): null must stop
    meaning three things)."""
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        comp = base / "fixture_component"
        comp.mkdir(exist_ok=True)
        hist = str(comp / "history.json")
        state = str(comp / "state.json")
        extra = _cleared(comp)
        at_think = "code-seam@v1: [THINKME] -> TICKETME -> BUILDME -> PROVEME -> LEARNME -> PROVED"
        transitions.emit(at_think, "TICKETME",
                         history_path=hist, state_path=state, **extra)
        rec = projector.read_history(hist)[0]
        assert "entry_gate" in rec, \
            "entry_gate must be present even on non-BUILDME crossings"
        assert rec["entry_gate"] == "not_applicable", \
            f"non-BUILDME crossing must say not_applicable, got: {rec['entry_gate']!r}"


def test_into_buildme_still_refuses_chartless():
    """The original entry gate behavior is unchanged: crossing INTO BUILDME with a
    chartless cast ticket still raises EntryGateRed."""
    import cairn.machines.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        tickets, berths = _entry_world(base, cast=("widget",), claims=())
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist = str(base / "history.json")
            state = str(base / "state.json")
            try:
                transitions.emit(_AT_TICKET, "BUILDME",
                                 history_path=hist, state_path=state, ticket="widget")
            except transitions.EntryGateRed:
                pass
            else:
                raise AssertionError("crossing INTO BUILDME with no chart should still refuse")
            assert not Path(hist).exists()
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


TEETH = [
    test_leg_a_complete_ticket_passes_at_leaving_buildme,
    test_leg_b_chartless_ticket_refused_at_leaving_buildme,
    test_leg_c_unticketed_crossing_records_not_checked,
    test_entry_gate_field_always_present,
    test_into_buildme_still_refuses_chartless,
]

if __name__ == "__main__":
    import traceback
    red = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception:
            traceback.print_exc()
            red += 1
    sys.exit(red)
