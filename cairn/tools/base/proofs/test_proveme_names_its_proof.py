"""Proof for ticket 7203db7f151e — the forward crossing INTO PROVEME names its proof.

The falsifier is one unnumbered clause, so one composite tooth (PROVES keys follow the
falsifier markers): a PROVEME crossing carrying no ``proven_by`` is refused BY NAME
(``ProofNamedRed``, message names ``proven_by`` and the ticket), nothing is written
before the raise; a crossing that names one lands with the lane
``the_proveme_crossing_names_its_proof`` reading expected == actual; a ticketless
crossing records ``proof_gate: not_checked`` and appends NO lane (the entry gate's
v0 jurisdiction — D7/D8 on the ticket).

THE FIXTURE (D9): the seat sits AFTER the entry gate at the same crossing, and the
real entry gate refuses a chartless fixture ticket before the seat is reached — so
legs (a) and (b) run with ``transitions._entry_gate`` replaced by a stub that reads
"charted" and ``transitions._stamp_sail`` replaced by a no-op (a fixture ticket must
not claim the live sail record in instance-space). The seat, the red class, the
inspector and the history write are all REAL; only the chart is pretended. Both are
restored in ``finally``.

The names ``ProofNamedRed`` and ``inspect_proof_named`` are bound at CALL time via
getattr, so a hollow reversion of transitions.py reds this tooth instead of crashing
the runner at import.

Run:
    PYTHONPATH=. python3 cairn/tools/base/proofs/test_proveme_names_its_proof.py   # exit 0 = green
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.tools.base import transitions  # noqa: E402

PROVES = {"7203db7f151e": {"all": "test_a_proveme_crossing_without_a_proof_is_refused_by_name"}}

_AT_BUILDME = "bug@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"
_FIXTURE_TICKET = "fixture-7203-no-journal-carries-this-id"
_LANE = "the_proveme_crossing_names_its_proof"
_THIS_PROOF = "cairn/tools/base/proofs/test_proveme_names_its_proof.py"


def _records(hist: str) -> list[dict]:
    text = Path(hist).read_text()
    doc = json.loads(text)
    if isinstance(doc, dict):
        for key in ("crossings", "entries", "history"):
            if isinstance(doc.get(key), list):
                return doc[key]
        raise AssertionError(f"history at {hist} carries no crossing list: {list(doc)}")
    return doc


class _PretendCharted:
    """Legs (a)/(b): pretend the fixture ticket is charted and keep the sail record clean."""

    def __enter__(self):
        self._saved = (transitions._entry_gate, transitions._stamp_sail)
        transitions._entry_gate = lambda _t: ("clean — fixture chart", [])
        transitions._stamp_sail = lambda _t, _s: None
        return self

    def __exit__(self, *_exc):
        transitions._entry_gate, transitions._stamp_sail = self._saved
        return False


def test_a_proveme_crossing_without_a_proof_is_refused_by_name():
    red = getattr(transitions, "ProofNamedRed", None)
    inspect = getattr(transitions, "inspect_proof_named", None)
    assert red is not None and inspect is not None, \
        "transitions.py carries no ProofNamedRed / inspect_proof_named — the seat is not built"
    assert issubclass(red, transitions.IllegalTransition) and red is not transitions.IllegalTransition
    for sib in (transitions.EntryGateRed, transitions.BuildGateRed, transitions.ExitGateRed):
        assert not issubclass(red, sib), f"ProofNamedRed must be a SIBLING of {sib.__name__}, not a subclass"

    # the fixture id is one no journal carries — the invariant the seat's union rests on
    from cairn.tools.base import crossings
    assert crossings.proven_by_since_buildme(_FIXTURE_TICKET) == [], \
        "the fixture ticket id is carried by a live journal — pick another"

    with tempfile.TemporaryDirectory() as d:
        comp = Path(d) / "fixture_component"
        comp.mkdir()
        hist, state = str(comp / "history.json"), str(comp / "state.json")

        # (a) no proven_by -> ProofNamedRed by name; nothing written
        with _PretendCharted():
            try:
                transitions.emit(_AT_BUILDME, "PROVEME", history_path=hist, state_path=state,
                                 ticket=_FIXTURE_TICKET, actor="proof", note="leg a")
            except red as e:
                assert "proven_by" in str(e), f"the refusal must name the missing argument: {e}"
                assert _FIXTURE_TICKET in str(e), f"the refusal must name the ticket: {e}"
                # the raise carries the lane as a FINDING (_findings_of keys it by ``method``)
                lanes = [f for f in getattr(e, "findings", []) if f.get("method") == _LANE]
                assert len(lanes) == 1, f"the refusal carries the lane as its finding: {e.findings}"
                assert lanes[0]["expected"] != lanes[0]["actual"], lanes[0]
            else:
                raise AssertionError("a PROVEME crossing with no proof named crossed ungated")
            assert not Path(hist).exists(), "a REFUSED crossing must write no record of truth"
            assert not Path(state).exists(), "a REFUSED crossing must write no state"

            # (b) proven_by names this proof -> the crossing lands, the lane reads clean
            new = transitions.emit(_AT_BUILDME, "PROVEME", history_path=hist, state_path=state,
                                   ticket=_FIXTURE_TICKET, actor="proof", note="leg b",
                                   proven_by=_THIS_PROOF)
        assert transitions.parse_workflow(new).here == "PROVEME", new
        rec = _records(hist)[-1]
        assert rec["to"] == "PROVEME" and rec.get("proof_gate", "").startswith("clean — proof named:"), rec
        lanes = [f for f in rec["proved"] if f.get("identity") == _LANE]
        assert len(lanes) == 1, f"exactly one proof-named lane on the record: {rec['proved']}"
        assert lanes[0]["expected"] == lanes[0]["actual"], lanes[0]
        assert lanes[0]["values"]["named"] == [_THIS_PROOF], lanes[0]
        assert lanes[0]["code"] == "transitions.py::inspect_proof_named", lanes[0]
        direct = inspect(_FIXTURE_TICKET, {"proven_by": _THIS_PROOF})
        assert len(direct) == 1 and direct[0]["expected"] == direct[0]["actual"], direct

        # (c) ticketless -> real gates, proof_gate 'not_checked', NO lane
        comp2 = Path(d) / "fixture_component_2"
        comp2.mkdir()
        hist2, state2 = str(comp2 / "history.json"), str(comp2 / "state.json")
        new2 = transitions.emit(_AT_BUILDME, "PROVEME", history_path=hist2, state_path=state2,
                                actor="proof", note="leg c")
        assert transitions.parse_workflow(new2).here == "PROVEME", new2
        rec2 = _records(hist2)[-1]
        assert rec2.get("proof_gate") == "not_checked", rec2
        assert not [f for f in rec2["proved"] if f.get("identity") == _LANE], \
            f"a ticketless crossing appends no proof-named lane: {rec2['proved']}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
