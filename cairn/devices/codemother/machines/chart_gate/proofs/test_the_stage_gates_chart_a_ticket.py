"""Proof for ticket fa4462c803d6 — CodeMother's stage and verdict gates chart a queued ticket.

Outline 9.6 (Akien 2026-11-10, Q#81): each chart stage and the verdict is a gate machine that
answers ``queueme <fileref>``. Outline 3.3.4.3: the gate instantiates the ticket on its own side,
and that instance processes the pass or the fail.

The world: a scratch tickets store (the live store charter copied in, ``ticket_file._TICKETS``
pointed there) holding a fixture whose id is THIS ticket's own, so the stage doors' on-file claim
check resolves against the live commons; a scratch repo carrying the fixture's owning intention
(so a fail's journal lands in scratch); a scratch packets dir; a spy participant for the bus; and,
for the verdict, an injected runner so no instrument forks. The gate is bound inside each tooth.

    python3 cairn/devices/codemother/machines/chart_gate/proofs/test_the_stage_gates_chart_a_ticket.py
"""

from __future__ import annotations

import json
import shutil
import sys
from cairn.tools.scratch.scratch import scratch_dir
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "794835a34ec9": {
        "4": "test_a_door_refusal_fails_the_ticket_with_the_doors_words",
    },
    "fa4462c803d6": {
        "1": "test_the_orient_gate_berths_a_claimed_packet_and_deposits_it",
        "2": "test_the_constrain_gate_reads_the_recorded_orient_berth",
        "3": "test_an_absent_draft_or_earlier_berth_fails_the_ticket_and_writes_nothing",
        "4": "test_a_door_refusal_fails_the_ticket_with_the_doors_words",
        "5": "test_the_verdict_gate_disposes_from_the_observed_runs_not_the_draft",
        "6": "test_gates_carries_eight_stages_and_the_shim_holds_them",
    },
}

_TID = "fa4462c803d6"
_LIVE_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"

# hollow runs this proof in a worktree with no CairnCommons beside it, where transitions'
# repo-relative class table points at nothing (measured 2026-11-11, fa4462c803d6's first hollow):
# so with no sibling, the class-table defaults read the home checkout, for this process only.
if not (_REPO_ROOT.parent / "CairnCommons").is_dir():
    from cairn.tools.base import transitions as _transitions
    _transitions._NODE_CLASSES = _LIVE_STORE_CHARTER.parents[1] / "node_classes"
    for _fn in (_transitions.emit, _transitions.load_class_def):
        for _k in ("node_class_root", "root"):
            if _k in (_fn.__kwdefaults__ or {}):
                _fn.__kwdefaults__[_k] = _LIVE_STORE_CHARTER.parents[1] / "node_classes"
    # and the chart doors' ticket-claim check finds the claim (this ticket's own id) in the
    # commons beside the repo: the same home checkout stands in for it (grammar.ticket_path)
    from cairn.tools.chain import grammar as _grammar
    _grammar.ticket_path.__defaults__ = (_grammar.CAIRN_ROOT, str(_LIVE_STORE_CHARTER.parent))
_WF = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
_OWNING = "machines/fixture_gate/intention+why.json"
_STAGES = ["orient", "constrain", "survey", "decompose", "triage", "hypothesize", "validate",
           "verdict"]
_PROOF = "cairn/devices/codemother/machines/chart_gate/proofs/test_the_stage_gates_chart_a_ticket.py"
_CRITERION = "python3 " + _PROOF
# clause 7 is Ticket.failed's own, proved where Ticket lives; a criterion runs it, as the chart does
_FAILED = "python3 cairn/machines/ticket/proofs/test_a_ticket_queues_itself_at_a_gate.py"
_GATE = "cairn/devices/codemother/machines/chart_gate/gate.py"
_P = [  # two pieces: the first's instrument exits 1 under the injected runner, the second's 0
    {"what": "the stage gate", "why": "the ticket's stage needs a gate", "kind": "build",
     "fills": "a gate per chart stage", "uses": ["cairn/machines/ticket/ticket.py"],
     "writes_to": [_GATE], "why_now": "everything rides it",
     "expect": "the gate berths a claimed packet", "falsifier": "no packet is berthed",
     "instrument": "false"},
    {"what": "the verdict gate", "why": "a disposition is observed", "kind": "build",
     "fills": "an observed verdict", "uses": ["cairn/devices/codemother/machines/verdict/verdict.py"],
     "writes_to": [_GATE], "why_now": "it closes the chart",
     "expect": "dispositions follow the runs", "falsifier": "a disposition follows the draft",
     "instrument": "true"},
]


def _drafts() -> dict:
    """The plan's chart: each stage's packet as the builder authors it, no ticket and no ref."""
    prov = lambda ref, *ks: {ref: "floor", **{k: "claude" for k in ks}}  # noqa: E731
    return {
        "orient": {"request": f"{_TID}: codemother's stage and verdict gates chart a queued ticket",
                   "intent": "a gate per chart stage answers queueme",
                   "scope": "one machine under codemother", "confidence": 0.85,
                   "provenance": {"intent": "claude", "scope": "claude"}},
        "constrain": {"constraints": [{"text": "the ticket sends only its fileref",
                                       "source": "press_office/CairnComponentOutline.txt",
                                       "kind": "law"}],
                      "bounds": {"in": ["cairn/devices/codemother/machines/chart_gate/"],
                                 "out": ["the stage doors"]},
                      "unknowns": [], "confidence": 0.85,
                      "provenance": {"intent_ref": "floor", "bounds": "claude"}},
        "survey": {"sought": ["the ticket class", "the verdict door"],
                   "holdings": [{"what": "Ticket", "address": "cairn/machines/ticket/ticket.py"},
                                {"what": "write_verdict",
                                 "address": "cairn/devices/codemother/machines/verdict/verdict.py"}],
                   "absences": [{"what": "a gate per chart stage",
                                 "measure": "ls cairn/devices/codemother/machines/ shows none"},
                                {"what": "an observed verdict",
                                 "measure": "verdict_ticket.py writes every disposition confirmed"}],
                   "unknowns": [], "confidence": 0.85,
                   "provenance": prov("constrain_ref", "sought", "holdings", "absences", "unknowns")},
        "decompose": {"sub_problems": [{k: p[k] for k in ("what", "why", "kind", "fills", "uses",
                                                          "writes_to")} for p in _P],
                      "unknowns": [], "confidence": 0.85,
                      "provenance": prov("survey_ref", "sub_problems", "unknowns")},
        "triage": {"order": [{"what": p["what"], "why_now": p["why_now"]} for p in _P],
                   "unknowns": [], "confidence": 0.85,
                   "provenance": prov("decompose_ref", "order", "unknowns")},
        "hypothesize": {"hypotheses": [{"piece": p["what"], "expect": p["expect"],
                                        "falsifier": p["falsifier"], "instrument": p["instrument"]}
                                       for p in _P],
                        "unknowns": [], "confidence": 0.85,
                        "provenance": prov("triage_ref", "hypotheses", "unknowns")},
        "validate": {"criteria": [{"claim": "the stage gates chart a ticket",
                                   "instrument": _CRITERION, "covers": [p["what"] for p in _P]},
                                  {"claim": "a fail before BUILDME stands and waits in the trouble lane",
                                   "instrument": _FAILED, "covers": [_P[0]["what"]]}],
                     "unknowns": [], "confidence": 0.85,
                     "provenance": prov("hypothesize_ref", "criteria", "unknowns")},
        "verdict": {"verdicts": [{"claim": "the stage gates chart a ticket",
                                  "instrument": _CRITERION, "outcome": "pass",
                                  "evidence": "the fixture's teeth",
                                  "discriminating_observation": "a hollow gate berths nothing"},
                                 {"claim": "a fail before BUILDME stands and waits in the trouble lane",
                                  "instrument": _FAILED, "outcome": "pass",
                                  "evidence": "Ticket.failed's tooth",
                                  "discriminating_observation": "a kick-back to FIXME raises"}],
                    "dispositions": [{"piece": p["what"], "expect": p["expect"],
                                      "disposition": "confirmed", "by": "the draft says so"}
                                     for p in _P]},
    }


class _Spy:
    """A bus participant: records every request and post; every request is answered accepted."""

    def __init__(self):
        self.requests: list[dict] = []
        self.posts: list[dict] = []

    def request(self, *, to, channel="personal", why, verb="", body=None, timeout=30.0):
        self.requests.append({"to": to, "verb": verb, "body": body})
        return {"body": {"accepted": True, "passed": True}}

    def post(self, *, to, channel="personal", why, verb="", body=None, reply_to=None):
        self.posts.append({"to": to, "verb": verb, "body": body})
        return {"id": f"post-{len(self.posts)}"}


@contextmanager
def _world(chart: dict | None = None, claim: dict | None = None):
    import cairn.tools.base.ticket_file as tf
    tmp = scratch_dir("t4b-gates-")
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    roots = {k: tmp / k for k in ("repo", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    owning = roots["repo"] / _OWNING
    owning.parent.mkdir(parents=True)
    owning.write_text("{}\n")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    doc = {"id": _TID, "title": "a fixture ticket", "owning_intention": _OWNING}
    if chart is not None:
        doc["chart"] = chart
    plan.write_text(json.dumps(doc, indent=2) + "\n")
    state = {"workflow_and_state": _WF, "node_class": "code-seam"}
    if claim:
        state["chart_claim"] = claim
    tf.state_path(plan).write_text(json.dumps(state, indent=2) + "\n")
    packets = tmp / "packets"
    was = tf._TICKETS
    tf._TICKETS = store
    # The constrain door's floor reads the seals of the proofs its refs discover and asks the
    # tester nothing (ticket 5243cf9dc630), so this proof needs no guard to keep it off the bus.
    try:
        yield {"tmp": tmp, "store": store, "plan": plan, "roots": roots, "packets": packets,
               "spy": _Spy()}
    finally:
        tf._TICKETS = was
        shutil.rmtree(tmp, ignore_errors=True)


def _gate(w, stage, runner=None):
    from cairn.devices.codemother.machines.chart_gate.gate import StageGate
    return StageGate(stage, participant=w["spy"], roots=w["roots"], packets_dir=w["packets"],
                     runner=runner)


def _ask(w, stage, runner=None):
    return _gate(w, stage, runner).queueme({"sender": "fixture", "body": {"fileref": str(w["plan"])}})


def _state(w) -> dict:
    import cairn.tools.base.ticket_file as tf
    return json.loads(tf.state_path(w["plan"]).read_text(encoding="utf-8"))


def _packets(w) -> list[Path]:
    return sorted(w["packets"].glob("*.json")) if w["packets"].is_dir() else []


def _deposits(w) -> list[dict]:
    return [p for p in w["spy"].posts if p["verb"] == "deposit"]


def test_the_orient_gate_berths_a_claimed_packet_and_deposits_it():
    from cairn.devices.codemother.machines.orient.orient import floor_packet
    with _world(chart=_drafts()) as w:
        got = _ask(w, "orient")
        assert got.get("accepted") is True and got.get("passed") is True, got
        made = _packets(w)
        assert len(made) == 1 and str(made[0]) == got.get("berth"), (made, got)
        packet = json.loads(made[0].read_text(encoding="utf-8"))
        assert packet.get("ticket") == _TID, packet
        floor = floor_packet(_drafts()["orient"]["request"])
        assert packet.get("domain") == floor["domain"], (packet.get("domain"), floor["domain"])
        assert _state(w).get("chart_claim") == {"orient_berth": got["berth"]}, _state(w)
        assert _deposits(w) == [{"to": "codemother", "verb": "deposit",
                                 "body": {"berth": got["berth"]}}], w["spy"].posts
    print("ok test_the_orient_gate_berths_a_claimed_packet_and_deposits_it")


def test_the_constrain_gate_reads_the_recorded_orient_berth():
    with _world(chart=_drafts()) as w:
        o = _ask(w, "orient")
        c = _ask(w, "constrain")
        assert c.get("passed") is True, c
        packet = json.loads(Path(c["berth"]).read_text(encoding="utf-8"))
        assert packet.get("intent_ref") == o["berth"], (packet.get("intent_ref"), o)
        assert packet.get("constraints") == _drafts()["constrain"]["constraints"], packet
        assert packet.get("ticket") == _TID, packet
        assert _state(w).get("chart_claim") == {"orient_berth": o["berth"],
                                                "constrain_berth": c["berth"]}, _state(w)
    print("ok test_the_constrain_gate_reads_the_recorded_orient_berth")


def _assert_failed(w, got, *words):
    assert got.get("accepted") is True and got.get("passed") is False, got
    said = " ".join(str(one.get("why")) for one in got.get("lacks") or [])
    for word in words:
        assert word in said, (word, got.get("lacks"))
    assert _packets(w) == [], _packets(w)
    _assert_refused_trouble(w, got)
    assert _deposits(w) == [], w["spy"].posts


def _assert_refused_trouble(w, got):
    """The fail of a ticket charting at TICKETME (outline 3.3.4.3): the cursor stands, the lacks
    land as the ticket's fixme, nothing is asked of any verb, and the ticket's refused trouble
    names the stage (outline 3.3.4, Q#85, ticket 794835a34ec9)."""
    st = _state(w)
    assert st.get("workflow_and_state") == _WF, st
    assert [f["missing"] for f in st.get("fixme") or []] == [one["why"] for one in got["lacks"]], st
    assert w["spy"].requests == [], f"a refused ticket asked something: {w['spy'].requests}"
    stage = got["lacks"][0]["kind"]
    assert got.get("trouble") == f"ticket-refused-{_TID}-at-{stage}", got
    assert "design_queued" not in got, f"the answer still speaks of design: {sorted(got)}"


def test_an_absent_draft_or_earlier_berth_fails_the_ticket_and_writes_nothing():
    no_survey = {k: v for k, v in _drafts().items() if k != "survey"}
    with _world(chart=no_survey, claim={"constrain_berth": "/nowhere/constrain.json"}) as w:
        _assert_failed(w, _ask(w, "survey"), "chart.survey")
    with _world(chart=_drafts()) as w:
        _assert_failed(w, _ask(w, "survey"), "constrain_berth")
    print("ok test_an_absent_draft_or_earlier_berth_fails_the_ticket_and_writes_nothing")


def test_a_door_refusal_fails_the_ticket_with_the_doors_words():
    chart = _drafts()
    chart["constrain"] = dict(chart["constrain"], constraints=[])
    with _world(chart=chart) as w:
        o = _ask(w, "orient")
        assert o.get("passed") is True, o
        before = _packets(w)
        got = _ask(w, "constrain")
        assert got.get("accepted") is True and got.get("passed") is False, got
        said = " ".join(str(one.get("why")) for one in got.get("lacks") or [])
        assert "ConstrainRefused" in said, got.get("lacks")
        assert _packets(w) == before, _packets(w)
        _assert_refused_trouble(w, got)
        assert "constrain_berth" not in (_state(w).get("chart_claim") or {}), _state(w)
    print("ok test_a_door_refusal_fails_the_ticket_with_the_doors_words")


def test_the_verdict_gate_disposes_from_the_observed_runs_not_the_draft():
    ran: list[str] = []

    def runner(command, *, timeout_s=600, cwd=None):
        ran.append(command)
        code = 1 if command == "false" else 0
        return {"command": command, "exit": code, "timed_out": False, "timeout_s": timeout_s,
                "seconds": 0.0, "tail": f"fixture exit {code}"}

    with _world(chart=_drafts()) as w:
        for stage in _STAGES[:-1]:
            got = _ask(w, stage)
            assert got.get("passed") is True, (stage, got)
        got = _ask(w, "verdict", runner=runner)
        assert got.get("passed") is True, got
        verdict = json.loads(Path(got["berth"]).read_text(encoding="utf-8"))
        disposed = {d["piece"]: d for d in verdict.get("dispositions") or []}
        assert disposed["the stage gate"]["disposition"] == "killed", disposed
        assert disposed["the verdict gate"]["disposition"] == "confirmed", disposed
        assert "false" in disposed["the stage gate"]["by"] and "1" in disposed["the stage gate"]["by"], disposed
        assert "true" in disposed["the verdict gate"]["by"] and "0" in disposed["the verdict gate"]["by"], disposed
        assert {"false", "true", _CRITERION} <= set(ran), ran
        assert verdict.get("ticket") == _TID and verdict.get("validate_ref") == _state(w)["chart_claim"]["validate_berth"]
        assert _state(w)["chart_claim"].get("verdict_berth") == got["berth"], _state(w)
    print("ok test_the_verdict_gate_disposes_from_the_observed_runs_not_the_draft")


def test_gates_carries_eight_stages_and_the_shim_holds_them():
    from cairn.devices.codemother.machines.chart_gate.gate import StageGate, gates
    from cairn.devices.codemother.shim import CodeMotherDevice
    spy = _Spy()
    built = gates(participant=spy)
    assert list(built) == _STAGES, list(built)
    for stage, gate in built.items():
        assert isinstance(gate, StageGate) and gate.stage == stage, (stage, gate)
        assert set(gate.declared_verbs()) == {"queueme"}, gate.declared_verbs()
    held = CodeMotherDevice().declared_machines()
    assert {"watchme", "clearance", *_STAGES} <= set(held), sorted(held)
    for stage in _STAGES:
        assert isinstance(held[stage], StageGate) and held[stage].stage == stage, held[stage]
    print("ok test_gates_carries_eight_stages_and_the_shim_holds_them")


def main() -> int:
    failed = 0
    for name in PROVES[_TID].values():
        try:
            globals()[name]()
        except Exception as exc:  # noqa: BLE001 — a proof reports every tooth
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print("PASS" if not failed else f"{failed} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
