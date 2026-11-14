"""Proof: the BUILDME entry gate carries a lane that asks the component-boundary judge.

RULE 1's write side. Measured 2026-11-14: d3248e7cb2fd and 2517060264b4, owned by cairn/tools/base,
wrote cairn/machines/build_inspector/inspector.py and nothing refused the crossing, because
``encapsulation_holds`` checks imports only. build_inspector's ``buildme_stays_in_its_component``
measures the write side (its own ticket and proof); this lane, ``the_ticket_builds_only_inside_its_component``
in ``inspect_entry``, is where that measurement becomes a refusal.

  1. emit into BUILDME for a ticket owned by cairn/tools/base whose decision writes
     cairn/machines/build_inspector/inspector.py (the d3248/2517 shape) is refused, the refusal naming
     the foreign region and the path, together with the chart lane's lack in the same pass, and
     nothing is journaled;
  2. the same crossing for a ticket that writes only cairn/tools/base's own code and proofs/ is admitted.

THE WORLD: the judges run in CodeMother's process, so the fixture reaches them by LAUNCH
(inspect_wire.launch): ``tickets_root`` is a scratch class root whose git index holds the two
charters the paths name (the judge reads the charter list from ``git ls-files`` of that root, and
the ticket from its sibling CairnCommons/tickets), ``ticket_store`` is that tickets dir (the named-
ticket chokepoint reads it), and ``berths`` holds the chart claim tooth 2 needs. No live record is
read or written.

Red-first: until build_inspector publishes the judge and CodeMother answers its name
(INSPECT_JUDGES), the lane's ask is refused and both teeth red.

    bin/cairn test cairn/tools/base/proofs/test_buildme_refuses_a_ticket_that_builds_outside_its_component.py
"""
from __future__ import annotations

import contextlib
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402

PROVES = {"67d479860f5d": {
    "1": "test_a_ticket_writing_outside_its_component_is_refused_with_every_lack_named",
    "2": "test_a_ticket_writing_only_inside_its_component_is_admitted",
}}

PROOF_TIMEOUT_S = 300

_TID = "a1a7e0c0b0d1"
_AT_TICKET = "code-seam@v1: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> LEARNME -> PROVED"
_CHARTERS = ("cairn/tools/base/intention+why.json",
             "cairn/machines/build_inspector/intention+why.json")
_FOREIGN = "cairn/machines/build_inspector/inspector.py"
_METHOD = "buildme_stays_in_its_component"
_LANE = "the_ticket_builds_only_inside_its_component"


@contextlib.contextmanager
def _world(writes: list[str], *, claimed: bool):
    """A scratch class root with the charters indexed, one ticket owned by cairn/tools/base
    writing ``writes``, and (when ``claimed``) a berthed chart chain claiming it; CodeMother
    launched over it. Yields (ticket_file module, history path)."""
    from cairn.tools.base import ticket_file
    from cairn.tools.inspect_wire.inspect_wire import launch
    base = Path(scratch_dir("buildme-component-lane-"))
    root, tickets, berths = base / "cairn", base / "CairnCommons" / "tickets", base / "berths"
    root.mkdir()
    tickets.mkdir(parents=True)
    (berths / "0" / "packets").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True, env=git_env())
    for c in _CHARTERS:
        p = root / c
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}\n", encoding="utf-8", newline="\n")
    subprocess.run(["git", "-C", str(root), "add", "--", *_CHARTERS], check=True, env=git_env())
    (tickets / f"{_TID}-a-fixture-ticket-for-the-component-lane.json").write_text(json.dumps({
        "id": _TID, "title": "a fixture ticket for the component lane",
        "owning_intention": "cairn/tools/base/intention+why.json",
        "decisions": [{"n": 1, "text": "D1", "writes_to": writes, "reads": []}],
        "bounds": {"in": list(writes), "out": []},
        "intent_berth": "none, because this is a proof fixture (bin/cmd/trash names no intent)",
        "sorted_berth": "none, because this is a proof fixture (bin/cmd/trash names no sorted firing)",
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    if claimed:
        (berths / "0" / "packets" / "validate-20261114T000000-feed.json").write_text(
            json.dumps({"ticket": _TID}), encoding="utf-8", newline="\n")
    saved = ticket_file._TICKETS
    ticket_file._TICKETS = tickets
    try:
        with launch(berths=berths, tickets_root=root, crossing_roots=None, ticket_store=tickets):
            yield base / "history.json"
    finally:
        ticket_file._TICKETS = saved


def _emit(hist: Path) -> str:
    from cairn.tools.base import transitions
    return transitions.emit(_AT_TICKET, "BUILDME", history_path=str(hist),
                            state_path=str(hist.with_name("state.json")), ticket=_TID)


def test_a_ticket_writing_outside_its_component_is_refused_with_every_lack_named():
    from cairn.tools.base import transitions
    with _world(["cairn/tools/base/transitions.py", _FOREIGN], claimed=False) as hist:
        try:
            landed = _emit(hist)
        except transitions.EntryGateRed as e:
            findings = e.findings
            said = str(e)
        else:
            raise AssertionError(f"a ticket writing {_FOREIGN} crossed into BUILDME: {landed}")
        assert not hist.exists(), "a refused crossing wrote a record of truth"
    methods = [f.get("method") for f in findings]
    assert _METHOD in methods, f"the refusal does not name {_METHOD}: {methods}"
    assert "buildme_rides_the_chart" in methods, \
        f"the chart lane's lack was not named in the same pass: {methods}"
    mine = [f for f in findings if f.get("method") == _METHOD]
    about = " ".join(str(f.get("about", "")) for f in mine)
    assert "cairn/machines/build_inspector" in about and "inspector.py" in about, \
        f"the containment finding does not name the foreign region and path: {mine}"
    assert all("transitions.py" not in str(f.get("values", {}).get("paths", [])) for f in mine), \
        f"the owner's own write was named foreign: {mine}"
    assert _LANE in said or "inspector.py" in said, f"the refusal message does not carry the lane: {said[:600]}"


def test_a_ticket_writing_only_inside_its_component_is_admitted():
    from cairn.tools.base import transitions
    writes = ["cairn/tools/base/transitions.py",
              "cairn/tools/base/proofs/test_a_fixture_proof_for_the_component_lane.py"]
    with _world(writes, claimed=True) as hist:
        record = transitions.inspect_entry(_TID)
        lane = [r for r in record if r.get("identity") == _LANE]
        assert lane, f"inspect_entry carries no {_LANE} lane: {[r.get('identity') for r in record]}"
        assert lane[0].get("actual") == [], f"the lane reds a ticket writing only its own component: {lane[0]}"
        landed = _emit(hist)
    assert "[BUILDME" in landed, f"the crossing did not land: {landed}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
