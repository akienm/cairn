"""CodeMother answers `inspect` over the bus (ticket 266d39d56d06, a child of 4c4addb09adb).

Outline 9.4.4 and ticket 4c4addb09adb: build_inspector moves inside CodeMother. After the move,
code outside her may not import it (RULE 1), so she has to answer its judges over the bus.
Measured 2026-11-13: codemother declared no `inspect` verb, and 18 crossing calls in
transitions.py, plus hollow, corrosion and ten outside proofs, imported the inspector directly.

Each tooth runs over a scratch bus (the cairn device's published scratch_bus), with
CodeMother's shim held on it. One tooth per falsifier clause:
  1. For each allow-listed judge, `inspect` returns the same data as the direct call on the
     same inputs. Every name on the list has a case here, so the two cannot drift apart, and
     at least one case is a red that returns findings.
  2. A judge name off the allow-list is refused with its name in the reason, and nothing runs.
     A spy stands at a real inspector name that is off the list.
  3. A Workflow, a Path and a ticket argument cross and are rebuilt equal to the caller's. A
     spy judge on codemother's side receives the rebuilt arguments.

    bin/cairn test cairn/devices/codemother/proofs/test_codemother_answers_inspect_over_the_bus.py
"""
from __future__ import annotations

import contextlib
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"266d39d56d06": {
    "1": "test_every_allow_listed_judge_answers_as_the_direct_call",
    "2": "test_a_judge_off_the_list_is_refused_by_name_and_nothing_runs",
    "3": "test_a_workflow_a_path_and_a_ticket_cross_and_rebuild_equal",
}}

NOW = datetime(2026, 11, 13, 12, 0, 0)
_SCRATCH = contextlib.ExitStack()
_STATE: dict = {}
_TID = "fa1e0in5ec7d"       # a fixture ticket id; no live ticket carries it


def _bus():
    """A scratch bus with CodeMother's shim held on it, minted once per run."""
    if "bus" not in _STATE:
        from cairn.devices.cairn.tools.scratch_bus.scratch_bus import bus_shim, scratch_bus
        from cairn.devices.codemother.shim import CodeMotherShim
        from cairn.tools.bus_client.roster import DeviceRoster
        bus = _SCRATCH.enter_context(scratch_bus("inspect_266d"))
        loop = DeviceRoster(bus)
        loop.hold(bus_shim(bus, loop))
        loop.hold(CodeMotherShim(bus=bus))
        loop.pulse(NOW)
        _STATE["bus"] = bus
    return _STATE["bus"]


def _ask(judge: str, *args, **kwargs) -> dict:
    from cairn.devices.codemother.shim import wire_encode
    reply = _bus().request(sender="cc", to="codemother", channel="personal", verb="inspect",
                           why="proof 266d39d56d06: a judge asked over the bus",
                           body={"judge": judge, "args": wire_encode(list(args)),
                                 "kwargs": wire_encode(kwargs)}, timeout=300)
    assert reply.get("sender") == "codemother", reply
    return reply["body"]


def _world() -> Path:
    """A scratch tree: one component holding a bare class, a second device importing into the
    first (an encapsulation breach), a run-record folder, and an empty berth root."""
    if "world" in _STATE:
        return _STATE["world"]
    from cairn.tools.scratch.scratch import scratch_dir
    d = scratch_dir("inspect_266d")
    foo = d / "cairn/devices/foo"
    bar = d / "cairn/devices/bar"
    for comp, what in ((foo, "foo"), (bar, "bar")):
        comp.mkdir(parents=True)
        (comp / "intention+why.json").write_text(json.dumps({"what": what, "why": "fixture"}),
                                                 encoding="utf-8")
    (foo / "widget.py").write_text("class Bare:\n    def count(self):\n        return 3\n",
                                   encoding="utf-8")
    (bar / "reach.py").write_text("from cairn.devices.foo.widget import Bare\n", encoding="utf-8")
    runs = d / "runs"
    runs.mkdir()
    for name in ("20261113T010000.json", "20261113T020000.json"):
        (runs / name).write_text("{}", encoding="utf-8")
    (d / "berths").mkdir()
    (d / "questions").mkdir()
    _STATE["world"] = d
    return d


def _cases() -> dict:
    """judge -> [(args, kwargs)], every input in reach of a scratch tree or a fixture id."""
    from cairn.tools.base.transitions import load_class_def
    from cairn.tools.base.workflow_grammar import parse_workflow
    w = _world()
    cd = load_class_def("code-seam")
    wf = parse_workflow("code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED")
    hist = str(w / "cairn/devices/foo/history.json")
    return {
        "crossing_emission": [(["x", None], {}), (["x", _TID], {})],
        "crossing_rules": [([wf, "BUILDME", cd], {}), ([wf, "PROVED", cd], {})],
        "crossing_named_ticket": [(["BUILDME", None], {"history_path": hist, "roster": frozenset({"foo"})}),
                                  (["BUILDME", None], {"history_path": hist, "roster": frozenset()})],
        "crossing_fixme": [([None, None], {}), ([_TID, hist], {})],
        "crossing_demo": [([_TID], {})],
        "crossing_clearance": [(["PROVED", {}], {"history_path": hist, "roster": frozenset({"foo"})})],
        "crossing_proof_named": [([_TID, {}], {}), ([_TID, {"proven_by": [str(w / "nope.py")]}], {})],
        "working_tree_clean": [([{"component": "foo", "crossing_ticket": _TID}, w / "cairn/devices/foo"],
                                {"repos": [w]})],
        "buildme_rides_the_chart": [([_TID], {"berths_root": w / "berths"})],
        "buildme_rides_the_intent": [([_TID], {"tickets_root": w / "berths"})],
        "buildme_rides_the_sorted": [([_TID], {"tickets_root": w / "berths"})],
        "buildme_rides_the_outline_check": [([_TID], {"root": w})],
        "buildme_has_no_open_questions": [([_TID], {"questions_root": w / "questions"})],
        "proved_answers_the_chart": [([_TID], {"berths_root": w / "berths"})],
        "crossing_durability": [([_TID], {"history_path": None})],
        "inspect": [([], {"root": w / "cairn/devices", "component": "foo", "ticket": _TID})],
        "crossing_quorum": [([w / "nope.json", cd], {})],
        "reason_has_referent": [(["none, because it is a fixture"], {"repo": w, "commons": w}),
                                (["see cairn/devices/foo/widget.py"], {"repo": w, "commons": w})],
        "resolves_to": [(["cairn/devices/foo/widget.py", _TID], {"repo_root": str(w)})],
        "encapsulation_breaches": [([str(w)], {})],
        "every_class_reaches_the_diagnostic_mixin": [
            ([{"component": "foo", "dir": str(w / "cairn/devices/foo")}, w / "cairn/devices/foo"], {})],
        "_published_tool": [(["cairn/devices/foo/tools/x/x.py", str(w)], {})],
        "list_runs": [([w / "runs"], {})],
    }


def _direct(judge: str, args, kwargs):
    from cairn.devices.codemother.shim import INSPECT_JUDGES
    fn = getattr(importlib.import_module(INSPECT_JUDGES[judge]), judge)
    try:
        return "ok", fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 — the bus hands the same raise back named
        return "raised", type(exc).__name__


def test_every_allow_listed_judge_answers_as_the_direct_call():
    from cairn.devices.codemother.shim import INSPECT_JUDGES, wire_decode
    cases = _cases()
    assert set(cases) == set(INSPECT_JUDGES), (
        f"allow-list and cases differ: listed only {sorted(set(INSPECT_JUDGES) - set(cases))}, "
        f"cased only {sorted(set(cases) - set(INSPECT_JUDGES))}")
    differ, reds = [], 0
    for judge, calls in cases.items():
        for args, kwargs in calls:
            kind, want = _direct(judge, args, kwargs)
            got = _ask(judge, *args, **kwargs)
            if kind == "raised":
                if got.get("accepted") is not False or got.get("raised") != want:
                    differ.append((judge, f"direct raised {want}", got))
                continue
            if got.get("accepted") is not True:
                differ.append((judge, "refused over the bus", got))
                continue
            data = wire_decode(got["data"])
            if data != want:
                differ.append((judge, want, data))
            if isinstance(want, list) and want and any(
                    isinstance(r, dict) and (r.get("findings") or r.get("finding") or r.get("reason"))
                    for r in want):
                reds += 1
    assert not differ, "over the bus differs from the direct call:\n  " + "\n  ".join(
        repr(x)[:400] for x in differ)
    assert reds, "no case returned a red; clause 1 needs a red fixture"
    print(f"ok test_every_allow_listed_judge_answers_as_the_direct_call "
          f"({sum(len(c) for c in cases.values())} calls, {reds} red)")


def test_a_judge_off_the_list_is_refused_by_name_and_nothing_runs():
    from cairn.devices.codemother.shim import INSPECT_JUDGES
    from cairn.machines.build_inspector import inspector
    name = "history_reach"
    assert hasattr(inspector, name) and name not in INSPECT_JUDGES, name
    ran: list = []
    real = getattr(inspector, name)
    setattr(inspector, name, lambda *a, **k: ran.append((a, k)) or [])
    try:
        got = _ask(name, str(_world()))
    finally:
        setattr(inspector, name, real)
    assert got.get("accepted") is False, got
    assert name in str(got.get("reason")), f"the refusal does not name {name!r}: {got}"
    assert ran == [], f"an off-list judge ran: {ran}"
    print("ok test_a_judge_off_the_list_is_refused_by_name_and_nothing_runs")


def _echo(*args, **kwargs):
    """The spy judge: what codemother's side rebuilt, kept for the tooth to read."""
    _STATE["echo"] = (args, kwargs)
    return []


def test_a_workflow_a_path_and_a_ticket_cross_and_rebuild_equal():
    from cairn.devices.codemother.shim import INSPECT_JUDGES
    from cairn.machines.ticket.ticket import Ticket
    from cairn.tools.base.workflow_grammar import Workflow, parse_workflow
    w = _world()
    plan = w / f"{_TID}-fixture.json"
    plan.write_text(json.dumps({"id": _TID, "title": "fixture"}), encoding="utf-8")
    ticket = Ticket(plan)
    wf = parse_workflow("code-seam@v2: THINKME -> TICKETME -> [BUILDME:in-process] -> "
                        "WATCHME(the widget count) -> PROVEME -> PROVED")
    bare = Workflow("code-seam", "v2", ("THINKME", "BUILDME", "PROVED"), 1)
    path = w / "cairn/devices/foo/widget.py"
    INSPECT_JUDGES["_echo"] = __name__
    sys.modules.setdefault(__name__, sys.modules[__name__])
    _echo.__module__ = __name__
    setattr(sys.modules[__name__], "_echo", _echo)
    try:
        got = _ask("_echo", wf, path, ticket, roster=frozenset({"a", "b"}), bare=bare)
    finally:
        INSPECT_JUDGES.pop("_echo", None)
    assert got.get("accepted") is True, got
    args, kwargs = _STATE.get("echo", ((), {}))
    assert len(args) == 3, f"codemother rebuilt {len(args)} positional arguments: {args}"
    assert isinstance(args[0], Workflow) and args[0] == wf, (args[0], wf)
    assert isinstance(args[1], Path) and args[1] == path, (args[1], path)
    assert args[2] == ticket.id == _TID, (args[2], ticket.id)
    assert kwargs.get("roster") == frozenset({"a", "b"}), kwargs.get("roster")
    assert kwargs.get("bare") == bare, (kwargs.get("bare"), bare)
    print("ok test_a_workflow_a_path_and_a_ticket_cross_and_rebuild_equal")


if __name__ == "__main__":
    try:
        test_every_allow_listed_judge_answers_as_the_direct_call()
        test_a_judge_off_the_list_is_refused_by_name_and_nothing_runs()
        test_a_workflow_a_path_and_a_ticket_cross_and_rebuild_equal()
    finally:
        _SCRATCH.close()
