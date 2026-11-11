"""Proof for ticket 91a27edfdd81 — CC charts, crosses and closes a ticket through the ticket machine.

Outline 9.6 and 3.3.4.3 (Akien 2026-11-10, Q#80/Q#81): a ticket crosses a gate by sending its
fileref to codemother's ``machines/<gate>/queueme``. cairn/devices/cc/scripts/sail.py is CC's hand
on that, and it must reach CodeMother only over the bus (RULE 1).

Every tooth runs in a scratch world: a tempdir tickets store (the live store charter copied in,
one fixture plan and state, ``ticket_file._TICKETS`` pointed at it), and a recording bus behind
sail's REAL ``Asker``, so the sender the gate would see is the one sail stamps. The script is
loaded by path inside each tooth, never at import: a hollow reading takes it away.

    python3 cairn/devices/cc/proofs/test_sail_queues_the_ticket_at_codemothers_gates.py   # exit 0 = green
"""

from __future__ import annotations

import ast
import importlib.util
import json
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "91a27edfdd81": {
        "1": "test_sail_imports_no_device_and_the_old_helpers_are_gone",
        "2": "test_draft_writes_each_stage_without_claim_or_refs",
        "3": "test_chart_queues_each_stage_in_order_from_cc_and_stops_at_a_fail",
        "4": "test_cross_with_no_target_queues_at_clearance",
        "5": "test_cross_by_name_is_a_back_edge_or_a_disposition_only",
        "6": "test_verdict_drafts_every_criterion_and_queues_at_the_verdict_gate",
    },
}

_SCRIPTS = _REPO_ROOT / "cairn" / "devices" / "cc" / "scripts"
_SAIL = _SCRIPTS / "sail.py"
_TID = "fixture91a2a"
_CHART = ["orient", "constrain", "survey", "decompose", "triage", "hypothesize", "validate"]
_LIVE_STORE_CHARTER = (_REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json")
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"

# hollow runs this proof in a worktree with no CairnCommons beside it, where transitions'
# repo-relative class table points at nothing (memory: hollow-worktree-has-no-commons-beside):
# with no sibling, the class-table defaults read the home checkout, for this process only.
if not (_REPO_ROOT.parent / "CairnCommons").is_dir():
    from cairn.tools.base import transitions as _transitions
    _transitions._NODE_CLASSES = _LIVE_STORE_CHARTER.parents[1] / "node_classes"
    for _fn in (_transitions.emit, _transitions.load_class_def):
        for _k in ("node_class_root", "root"):
            if _k in (_fn.__kwdefaults__ or {}):
                _fn.__kwdefaults__[_k] = _LIVE_STORE_CHARTER.parents[1] / "node_classes"


def _sail():
    spec = importlib.util.spec_from_file_location("cc_sail_under_proof", _SAIL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Bus:
    """A recording bus: every request and post, as the wire would carry it; scripted replies."""

    def __init__(self, replies=None):
        self.requests: list[dict] = []
        self.posts: list[dict] = []
        self._replies = list(replies or [])

    def request(self, **kw):
        self.requests.append(kw)
        return self._replies.pop(0) if self._replies else {"body": {"accepted": True}}

    def post(self, **kw):
        self.posts.append(kw)
        return {"id": f"post-{len(self.posts)}"}


def _wf(cursor: str) -> str:
    steps = ["THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"]
    return "code-seam@v2: " + " -> ".join(f"[{s}]" if s == cursor else s for s in steps)


@contextmanager
def _world(cursor: str = "TICKETME", plan_extra: dict | None = None):
    import cairn.tools.base.ticket_file as tf
    tmp = Path(tempfile.mkdtemp(prefix="t5-sail-"))
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "cairn/devices/cc/intention+why.json",
                                **(plan_extra or {})}, indent=2) + "\n")
    tf.state_path(plan).write_text(json.dumps({"workflow_and_state": _wf(cursor),
                                               "node_class": "code-seam"}, indent=2) + "\n")
    was = tf._TICKETS
    tf._TICKETS = store
    try:
        yield {"tmp": tmp, "store": store, "plan": plan}
    finally:
        tf._TICKETS = was
        shutil.rmtree(tmp, ignore_errors=True)


def _spec() -> dict:
    piece = {"what": "p1", "why": "w", "kind": "build", "fills": "f", "uses": ["u.py"],
             "writes_to": ["u.py"], "why_now": "now", "expect": "e", "falsifier": "x",
             "instrument": "bin/cairn test a/proofs/test_p.py"}
    return {"ticket": _TID, "request": "R", "intent": "I", "scope": "S", "unknowns": ["U"],
            "constraints": [{"text": "c", "source": "CLAUDE.md", "kind": "law"}],
            "bounds": {"in": ["u.py"], "out": ["v.py"]}, "sought": ["s"],
            "holdings": [{"what": "h", "address": "u.py"}],
            "absences": [{"what": "a", "measure": "m"}], "pieces": [piece],
            "criteria": [{"claim": "C1", "instrument": "bin/cairn test a/proofs/test_p.py",
                          "timeout_s": 60}]}


def _plan(w) -> dict:
    return json.loads(w["plan"].read_text(encoding="utf-8"))


def _files(w) -> dict:
    return {p.name: p.read_bytes() for p in w["store"].iterdir() if p.is_file()}


def _quiet():
    said: list[str] = []
    return said, said.append


def test_sail_imports_no_device_and_the_old_helpers_are_gone():
    assert _SAIL.is_file(), f"{_SAIL} is absent"
    reaches = []
    for node in ast.walk(ast.parse(_SAIL.read_text(encoding="utf-8"))):
        names = ([node.module] if isinstance(node, ast.ImportFrom) and node.module
                 else [a.name for a in node.names] if isinstance(node, ast.Import) else [])
        reaches += [n for n in names if n.split(".")[:2] == ["cairn", "devices"]]
    assert reaches == [], f"sail.py imports another device: {reaches}"
    left = [n for n in ("cross.py", "chart_ticket.py", "verdict_ticket.py")
            if (_SCRIPTS / n).exists()]
    assert left == [], f"the old helpers still stand: {left}"


def test_draft_writes_each_stage_without_claim_or_refs():
    sail = _sail()
    with _world() as w:
        said, out = _quiet()
        assert sail.draft(_TID, _spec(), tickets_dir=w["store"], out=out) == 0
        chart = _plan(w).get("chart") or {}
        assert sorted(chart) == sorted(_CHART), sorted(chart)
        for stage, packet in chart.items():
            bad = [k for k in packet if k == "ticket" or k.endswith("_ref")]
            assert bad == [], f"chart.{stage} carries {bad}: the gate fills those"
        assert chart["orient"]["request"] == "R" and chart["orient"]["unknowns"] == ["U"]
        assert chart["constrain"]["bounds"] == {"in": ["u.py"], "out": ["v.py"]}
        assert chart["survey"]["holdings"] == [{"what": "h", "address": "u.py"}]
        assert chart["decompose"]["sub_problems"][0]["writes_to"] == ["u.py"]
        assert chart["triage"]["order"] == [{"what": "p1", "why_now": "now"}]
        assert chart["hypothesize"]["hypotheses"][0]["instrument"] == "bin/cairn test a/proofs/test_p.py"
        assert chart["validate"]["criteria"][0]["covers"] == ["p1"]


def test_chart_queues_each_stage_in_order_from_cc_and_stops_at_a_fail():
    sail = _sail()
    with _world() as w:
        bus = _Bus([{"body": {"accepted": True, "passed": True, "berth": f"/b/{s}"}}
                    for s in _CHART])
        said, out = _quiet()
        assert sail.chart(_TID, participant=sail.Asker(bus), tickets_dir=w["store"],
                          out=out, err=out) == 0, said
        assert [r["verb"] for r in bus.requests] == [f"machines/{s}/queueme" for s in _CHART]
        for r in bus.requests:
            assert (r["to"], r["sender"], r["body"]) == ("codemother", "CC",
                                                         {"fileref": str(w["plan"])}), r
    with _world() as w:
        lacks = [{"kind": "survey", "why": "no constrain_berth"}]
        bus = _Bus([{"body": {"accepted": True, "passed": True, "berth": "/b/o"}},
                    {"body": {"accepted": True, "passed": True, "berth": "/b/c"}},
                    {"body": {"accepted": True, "passed": False, "lacks": lacks}}])
        said, out = _quiet()
        assert sail.chart(_TID, participant=sail.Asker(bus), tickets_dir=w["store"],
                          out=out, err=out) == 1
        assert len(bus.requests) == 3, [r["verb"] for r in bus.requests]
        refusal = [s for s in said if s.startswith("refused at")]
        assert refusal and "survey" in refusal[0] and "no constrain_berth" in refusal[0], said


def test_cross_with_no_target_queues_at_clearance():
    sail = _sail()
    with _world("BUILDME") as w:
        wf = _wf("PROVEME")
        bus = _Bus([{"body": {"accepted": True, "workflow": wf}}])
        said, out = _quiet()
        assert sail.cross(_TID, participant=sail.Asker(bus), tickets_dir=w["store"],
                          out=out, err=out) == 0, said
        assert [(r["to"], r["verb"], r["sender"], r["body"]) for r in bus.requests] == [
            ("codemother", "machines/clearance/queueme", "CC", {"fileref": str(w["plan"])})]
        assert wf in said, said
    with _world("BUILDME") as w:
        bus = _Bus([{"body": {"accepted": False, "reason": "ExitGateRed: no verdict"}}])
        said, out = _quiet()
        assert sail.cross(_TID, participant=sail.Asker(bus), tickets_dir=w["store"],
                          out=out, err=out) == 1
        assert len(bus.requests) == 1
        assert any("ExitGateRed: no verdict" in s for s in said), said


def test_cross_by_name_is_a_back_edge_or_a_disposition_only():
    sail = _sail()
    with _world("TICKETME") as w:
        before = _files(w)
        bus, calls = _Bus(), []
        said, out = _quiet()
        rc = sail.cross(_TID, "BUILDME", why="w", participant=sail.Asker(bus),
                        tickets_dir=w["store"], crosser=lambda *a, **k: calls.append((a, k)),
                        out=out, err=out)
        assert rc == 1 and calls == [] and bus.requests == [] and bus.posts == [], said
        assert _files(w) == before, "a refused forward crossing changed the store"
    for cursor, target in (("BUILDME", "FIXME"), ("TICKETME", "RETIRED")):
        with _world(cursor) as w:
            bus, calls = _Bus(), []

            def crosser(tid, tgt, **kw):
                calls.append((tid, tgt, kw))
                return "new-workflow"

            said, out = _quiet()
            rc = sail.cross(_TID, target, why="the why", proven_by=["a/proofs/test_p.py"],
                            missing=["m1"], participant=sail.Asker(bus),
                            tickets_dir=w["store"], crosser=crosser, out=out, err=out)
            assert rc == 0, said
            assert len(calls) == 1, calls
            tid, tgt, kw = calls[0]
            assert (tid, tgt) == (_TID, target), calls
            assert (kw["actor"], kw["why"], kw["proven_by"], kw["missing"]) == (
                "CC", "the why", ["a/proofs/test_p.py"], ["m1"]), kw
            assert bus.requests == [] and bus.posts == [], bus.requests


def test_verdict_drafts_every_criterion_and_queues_at_the_verdict_gate():
    sail = _sail()
    criteria = [{"claim": "C1", "instrument": "bin/cairn test a/proofs/test_p.py", "timeout_s": 60},
                {"claim": "C2 verbatim", "instrument": "bin/cairn test b/proofs/test_q.py"}]
    with _world("PROVEME") as w:
        vb = w["tmp"] / "validate.json"
        vb.write_text(json.dumps({"criteria": criteria}))
        import cairn.tools.base.ticket_file as tf
        st = json.loads(tf.state_path(w["plan"]).read_text())
        st["chart_claim"] = {"validate_berth": str(vb)}
        tf.state_path(w["plan"]).write_text(json.dumps(st))
        bus = _Bus([{"body": {"accepted": True, "passed": True, "berth": "/b/verdict"}}])
        said, out = _quiet()
        rc = sail.verdict(_TID, "the hollow reds every tooth", participant=sail.Asker(bus),
                          tickets_dir=w["store"], out=out, err=out)
        assert rc == 0, said
        got = (_plan(w).get("chart") or {}).get("verdict") or {}
        vs = got.get("verdicts") or []
        assert [(v["claim"], v["instrument"], v["outcome"], v["discriminating_observation"])
                for v in vs] == [(c["claim"], c["instrument"], "pass",
                                  "the hollow reds every tooth") for c in criteria], vs
        assert "dispositions" not in got, "a disposition is the gate's to observe"
        assert [(r["verb"], r["sender"], r["body"]) for r in bus.requests] == [
            ("machines/verdict/queueme", "CC", {"fileref": str(w["plan"])})], bus.requests
    with _world("PROVEME") as w:
        bus = _Bus()
        said, out = _quiet()
        assert sail.verdict(_TID, "obs", participant=sail.Asker(bus), tickets_dir=w["store"],
                            out=out, err=out) == 1
        assert bus.requests == [], bus.requests


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)
