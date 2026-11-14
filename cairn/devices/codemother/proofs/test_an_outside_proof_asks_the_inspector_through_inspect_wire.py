"""Proof: an outside proof asks build_inspector's judges through inspect_wire (ticket 7ea59855b1f4).

A child of 4c4addb09adb, before 149b9a1ab9c4. Code outside codemother may not import the
inspector (RULE 1), and outline 9.4.3.3.4 (Q#88) puts the answer on the bus. Measured
2026-11-13: an outside proof had no published way to hold CodeMother on a scratch bus, 13 judges
it called were off INSPECT_JUDGES, and 7 proofs stood a fixture world behind the inspector by
writing its globals. inspect_wire now carries ``ask`` (the bus client), ``fixture`` (the world,
set on codemother's side) and the allow-list carries the 13 names.

One tooth per falsifier clause. Teeth 1, 2, 3, 5 and the ask half of 4 ride a scratch bus, so
they need Postgres on 5432; on a box without it they read red here and the Linux sealer's run
is the seal (outline 9.4.8.1).

  1. ask answers equal to the direct call for an allow-listed judge on a fixture charter.
  2. A judge off the allow-list raises InspectRefused naming it; a judge that raised over the
     bus raises again carrying its type name.
  3. Two asks in one process mint one scratch bus.
  4. Every name the ticket adds is on INSPECT_JUDGES and resolves to a callable, and the ones
     that take no fixture answer over ask equal to the direct call.
  5. Inside ``fixture``, a chart judge asked over the bus reads the berths it names, the
     tickets root and crossing roots are the fixture's, and all three are put back after;
     with a CodeMother on any other bus in the process, fixture refuses and writes nothing.

    python3 cairn/devices/codemother/proofs/test_an_outside_proof_asks_the_inspector_through_inspect_wire.py
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "7ea59855b1f4": {
        "1": "test_ask_answers_as_the_direct_call",
        "2": "test_a_refusal_raises_naming_the_judge",
        "3": "test_two_asks_mint_one_scratch_bus",
        "4": "test_every_added_name_is_answered",
        "5": "test_the_fixture_world_stands_behind_the_inspector_and_goes",
    },
}

_TID = "fa1e7ea5a5c0"   # a fixture ticket id; no live ticket carries it
ADDED = ("claim_provenance", "proofs_exist", "constraint_enforcement_holds",
         "crossing_fingerprints_verified", "the_nest", "declared_runners", "_workflow_cursor",
         "proof_covers_the_ticket", "buildme_rides_the_rehearsal", "build_started",
         "_source_fingerprint", "sieve_names", "run_sieve", "proven_space")


def _wire():
    from cairn.devices.codemother.tools.inspect_wire import inspect_wire
    return inspect_wire


def _insp():
    return importlib.import_module("cairn.machines.build_inspector.inspector")


def _charter_dir() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    d = scratch_dir("inspect_ask_charter_")
    (d / "intention+why.json").write_text(json.dumps(
        {"component": "fixture", "claim_provenance": {}}), encoding="utf-8")
    return d


def test_ask_answers_as_the_direct_call():
    d = _charter_dir()
    row = {"component": "fixture"}
    direct = _insp().claim_provenance(row, d)
    assert direct, "the fixture charter has an empty claim_provenance, so the sieve must red it"
    got = _wire().ask("claim_provenance", row, d)
    assert got == json.loads(json.dumps(direct, default=str)), (got, direct)


def test_a_refusal_raises_naming_the_judge():
    w = _wire()
    try:
        w.ask("not_a_judge_anyone_listed")
    except w.InspectRefused as exc:
        assert exc.judge == "not_a_judge_anyone_listed" and exc.raised is None, vars(exc)
        assert "not_a_judge_anyone_listed" in str(exc), str(exc)
    else:
        raise AssertionError("an unlisted judge was answered")
    try:
        w.ask("run_sieve", "no_sieve_has_this_name")
    except w.InspectRefused as exc:
        assert exc.raised == "KeyError", vars(exc)
        assert "no_sieve_has_this_name" in exc.reason, exc.reason
    else:
        raise AssertionError("run_sieve on an unregistered name answered instead of raising")


def test_two_asks_mint_one_scratch_bus():
    w = _wire()
    w.ask("sieve_names")
    first = w._HELD["bus"]
    w.ask("proven_space")
    assert w._HELD["bus"] is first and w._HELD["minted"] == 1, w._HELD


def test_every_added_name_is_answered():
    from cairn.devices.codemother.shim import INSPECT_JUDGES
    missing = [n for n in ADDED if n not in INSPECT_JUDGES]
    assert not missing, f"not on codemother's inspect allow-list: {missing}"
    uncallable = [n for n in ADDED
                  if not callable(getattr(importlib.import_module(INSPECT_JUDGES[n]), n, None))]
    assert not uncallable, f"listed but not a callable in its module: {uncallable}"
    insp, w = _insp(), _wire()
    wf = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
    for judge, args in (("sieve_names", ()), ("proven_space", ()), ("the_nest", ()),
                        ("declared_runners", ()), ("_workflow_cursor", (wf,))):
        direct = json.loads(json.dumps(getattr(insp, judge)(*args), default=str))
        assert w.ask(judge, *args) == direct, judge
    assert "PROVED" in w.ask("proven_space") and "BUILDME" not in w.ask("proven_space")


def test_the_fixture_world_stands_behind_the_inspector_and_goes():
    from cairn.tools.scratch.scratch import scratch_dir
    insp, w = _insp(), _wire()
    berths, tickets = scratch_dir("inspect_ask_berths_"), scratch_dir("inspect_ask_tickets_")
    roots = {"repo": str(tickets), "commons": str(tickets)}
    before = (insp._CHART_BERTHS, insp._TICKETS_ROOT, insp._crossing_roots)
    with w.fixture(berths=berths, tickets_root=tickets, crossing_roots=roots):
        findings = w.ask("buildme_rides_the_chart", _TID)
        assert findings and findings[0]["values"]["searched"] == str(berths), findings
        assert insp._TICKETS_ROOT == tickets and insp._crossing_roots() == roots
    after = (insp._CHART_BERTHS, insp._TICKETS_ROOT, insp._crossing_roots)
    assert after == before, ("the fixture world outlived its block", after, before)
    live = w.ask("buildme_rides_the_chart", _TID)
    assert live and live[0]["values"]["searched"] != str(berths), live
    # a CodeMother on any other bus in this process is a live one: the fixture refuses to stand
    # behind it, and writes nothing
    from cairn.devices.codemother.shim import CodeMotherShim
    stand_in = CodeMotherShim(bus=object())
    try:
        with w.fixture(berths=berths):
            raise AssertionError("fixture stood behind a CodeMother that is not on ask()'s bus")
    except w.InspectRefused as exc:
        assert exc.judge == "fixture" and "d2ecdb867bc9" in exc.reason, vars(exc)
    finally:
        del stand_in
    assert insp._CHART_BERTHS == before[0], "a refused fixture wrote the chart berths"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
