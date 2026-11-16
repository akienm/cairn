"""Proof for ticket 322ed56e5362: a redraft over a standing validate berth is charted or refused.

Measured 2026-11-15 on 8f3d61c0ae47: a redraft rewrote only the plan's ``chart`` field. The old
validate berth (berths/chart/validate-20261114T171135-081afd0c1df2.json) went on claiming the
ticket, and the verdict gate, which reads that berth and never the plan, refused twice on a
criterion the redraft had removed. Now ``sail.py draft`` refuses while a validate berth stands,
and ``--rechart`` drafts, charts, and refuses unless the validate berth moved.

  1. a validate berth claiming the ticket in the berth store: draft refuses, names the berth,
     and writes nothing to the plan;
  2. a validate berth recorded only in the ticket's chart_claim: draft refuses the same way;
  3. with no validate berth standing, draft writes every stage as before;
  4. --rechart over a standing berth drafts and charts, and passes when the gate wrote a new
     validate berth that now claims the ticket;
  5. --rechart whose charting leaves the old validate berth standing returns 1 and says so.

The world: a scratch tickets store (the live store charter, one fixture plan and state), a
scratch berth store handed to sail as ``berths_root``, and a recording bus behind sail's real
``Asker``. At validate the bus can write a new claiming packet, as codemother's gate does.

    python3 cairn/devices/cc/proofs/test_a_redraft_over_a_standing_validate_berth_is_charted_or_refused.py
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"322ed56e5362": {
    "1": "test_a_berth_claiming_the_ticket_refuses_the_redraft",
    "2": "test_a_berth_in_the_chart_claim_refuses_the_redraft",
    "3": "test_no_standing_berth_drafts_every_stage",
    "4": "test_rechart_passes_when_the_validate_berth_moves",
    "5": "test_rechart_refuses_when_the_old_berth_still_stands"}}

PROOF_TIMEOUT_S = 300

_SAIL = _REPO_ROOT / "cairn" / "devices" / "cc" / "scripts" / "sail.py"
_TID = "fixture322ed"
_CHART = ["orient", "constrain", "survey", "decompose", "triage", "hypothesize", "validate"]
_OLD = "validate-20261114T171135-081afd0c1df2.json"
_NEW = "validate-20261115T230000-aaaaaaaaaaaa.json"
_LIVE_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"

# hollow runs this in a worktree with no CairnCommons beside it (memory:
# hollow-worktree-has-no-commons-beside): the class table reads the home checkout instead.
if not (_REPO_ROOT.parent / "CairnCommons").is_dir():
    from cairn.tools.base import transitions as _transitions
    _transitions._NODE_CLASSES = _LIVE_STORE_CHARTER.parents[1] / "node_classes"
    for _fn in (_transitions.emit, _transitions.load_class_def):
        for _k in ("node_class_root", "root"):
            if _k in (_fn.__kwdefaults__ or {}):
                _fn.__kwdefaults__[_k] = _LIVE_STORE_CHARTER.parents[1] / "node_classes"


def _sail():
    spec = importlib.util.spec_from_file_location("cc_sail_under_proof_322e", _SAIL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Bus:
    """A recording bus. Every chart stage passes; at validate it writes ``writes`` (a packet
    name) into the berth store, claiming the ticket, as codemother's validate gate does."""

    def __init__(self, packets: Path, writes: str | None):
        self.requests: list[dict] = []
        self._packets, self._writes = packets, writes

    def request(self, **kw):
        self.requests.append(kw)
        stage = kw["verb"].split("/")[1]
        berth = f"/b/{stage}"
        if stage == "validate" and self._writes:
            (self._packets / self._writes).write_text(json.dumps({"ticket": _TID}), encoding="utf-8")
            berth = str(self._packets / self._writes)
        return {"body": {"accepted": True, "passed": True, "berth": berth}}

    def post(self, **kw):
        return {"id": "post"}


@contextmanager
def _world(claim: dict | None = None, chain_berth: bool = False):
    import cairn.tools.base.ticket_file as tf
    from cairn.machines.ticket.ticket import Ticket
    tmp = scratch_dir("testing-322e-")
    store, berths = tmp / "tickets", tmp / "berths"
    packets = berths / "chart" / "packets"
    store.mkdir()
    packets.mkdir(parents=True)
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "cairn/devices/cc/intention+why.json"},
                               indent=2) + "\n", newline="\n")
    state = {"workflow_and_state": "code-seam@v2: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> PROVED",
             "node_class": "code-seam"}
    if claim is not None:
        state["chart_claim"] = claim
    tf.state_path(plan).write_text(json.dumps(state, indent=2) + "\n", newline="\n")
    if chain_berth:
        (packets / _OLD).write_text(json.dumps({"ticket": _TID}), encoding="utf-8")
    roots = {k: tmp / k for k in ("repo", "commons", "instance")}
    was = tf._TICKETS
    tf._TICKETS = store
    Ticket._diagnostic_roots = roots
    try:
        yield {"store": store, "plan": plan, "berths": berths, "packets": packets}
    finally:
        del Ticket._diagnostic_roots
        tf._TICKETS = was


def _spec() -> dict:
    piece = {"what": "p1", "why": "w", "kind": "build", "fills": "f", "uses": ["u.py"],
             "writes_to": ["u.py"], "why_now": "now", "expect": "e", "falsifier": "x",
             "instrument": "bin/cairn test a/proofs/test_p.py"}
    return {"ticket": _TID, "request": "R", "intent": "I", "scope": "S", "unknowns": [],
            "constraints": [{"text": "c", "source": "CLAUDE.md", "kind": "law"}],
            "bounds": {"in": ["u.py"], "out": ["v.py"]}, "sought": ["s"],
            "holdings": [{"what": "h", "address": "u.py"}],
            "absences": [{"what": "a", "measure": "m"}], "pieces": [piece],
            "criteria": [{"claim": "C1", "instrument": "bin/cairn test a/proofs/test_p.py"}]}


def _draft(sail, w, **kw):
    said: list[str] = []
    rc = sail.draft(_TID, _spec(), tickets_dir=w["store"], out=said.append, err=said.append,
                    berths_root=w["berths"], **kw)
    return rc, said


def _chart(w) -> dict:
    return json.loads(w["plan"].read_text(encoding="utf-8")).get("chart") or {}


def test_a_berth_claiming_the_ticket_refuses_the_redraft():
    sail = _sail()
    with _world(chain_berth=True) as w:
        before = w["plan"].read_bytes()
        rc, said = _draft(sail, w)
        assert rc == 1, said
        assert any(_OLD in s and "--rechart" in s for s in said), said
        assert w["plan"].read_bytes() == before, "a refused redraft wrote the plan"


def test_a_berth_in_the_chart_claim_refuses_the_redraft():
    sail = _sail()
    with _world(claim={"validate_berth": f"/old/{_OLD}"}) as w:
        before = w["plan"].read_bytes()
        rc, said = _draft(sail, w)
        assert rc == 1, said
        assert any(_OLD in s for s in said), said
        assert w["plan"].read_bytes() == before, "a refused redraft wrote the plan"


def test_no_standing_berth_drafts_every_stage():
    sail = _sail()
    with _world() as w:
        rc, said = _draft(sail, w)
        assert rc == 0, said
        assert sorted(_chart(w)) == sorted(_CHART), sorted(_chart(w))


def test_rechart_passes_when_the_validate_berth_moves():
    sail = _sail()
    with _world(chain_berth=True) as w:
        bus = _Bus(w["packets"], writes=_NEW)
        rc, said = _draft(sail, w, rechart=True, participant=sail.Asker(bus))
        assert rc == 0, said
        assert sorted(_chart(w)) == sorted(_CHART)
        assert [r["verb"] for r in bus.requests] == [f"machines/{s}/queueme" for s in _CHART]
        from cairn.tools.chain.chain import chain_for_ticket
        assert Path(chain_for_ticket(_TID, berths_root=w["berths"])["validate"]).name == _NEW


def test_rechart_refuses_when_the_old_berth_still_stands():
    sail = _sail()
    with _world(chain_berth=True) as w:
        bus = _Bus(w["packets"], writes=None)
        rc, said = _draft(sail, w, rechart=True, participant=sail.Asker(bus))
        assert rc == 1, said
        assert any("did not move" in s and _OLD in s for s in said), said


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
