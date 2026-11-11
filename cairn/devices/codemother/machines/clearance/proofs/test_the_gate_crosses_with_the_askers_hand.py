"""Proof for ticket f76d01d3170c — the clearance gate crosses with the asker's hand when the
boat's owner admits it.

Outline 9.6: moving a ticket across its workflow is the ticket's own act; CodeMother's gates only
answer it. The gate always crossed as codemother (0be964512fb0 D5), so a boat whose owner admits
only CC could not cross even when CC asked (measured 2026-11-11 on 91a27edfdd81). Now the gate
hands ``clearance.clear`` the asker's hand when the boat's owner admits it, and its own otherwise;
``clear`` still decides authority, so the choice never widens it.

Every tooth runs in a scratch world (a repo with one charter whose ``gated_by`` it sets, a commons
with one plan at TICKETME, a proof declaring it) and patches ``clearance.clear`` on its module to
record the kwargs it is handed and return the next workflow, so what is measured is the hand the
gate chose. The gate module is imported inside each tooth.

    python3 cairn/devices/codemother/machines/clearance/proofs/test_the_gate_crosses_with_the_askers_hand.py
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {
    "f76d01d3170c": {
        "1": "test_a_boat_only_cc_may_move_crosses_with_cc_when_cc_asks",
        "2": "test_an_unadmitted_asker_leaves_the_gate_its_own_hand",
        "3": "test_a_shared_boat_takes_the_askers_hand_and_the_holders_when_unnamed",
    },
}

_DOTTED = "cairn.devices.codemother.machines.clearance"
_CHARTER = "intention" + "+why.json"
_TID = "0f76d01d3170"
_WF = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
_NEXT = "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"


class _Heard:
    def __init__(self) -> None:
        self.said: list = []

    def request(self, **kw):
        self.said.append(("request", kw))
        return {"body": {"accepted": True}}

    def post(self, **kw):
        self.said.append(("post", kw))


@contextmanager
def _asked(gated_by: list[str], sender: str):
    """Queue a scratch boat whose owner admits ``gated_by`` at clearance as ``sender``; yield
    (the gate's answer, the kwargs clearance.clear was handed)."""
    clearance = importlib.import_module(_DOTTED + ".clearance")
    gate_mod = importlib.import_module(_DOTTED + ".gate")
    handed: list[dict] = []

    def recording_clear(workflow, to, **kw):
        handed.append({"workflow": workflow, "to": to, **kw})
        return _NEXT

    with tempfile.TemporaryDirectory(prefix="clearance-hand-") as tmp:
        t = Path(tmp)
        repo, commons = t / "repo", t / "commons"
        (repo / "comp" / "proofs").mkdir(parents=True)
        (commons / "tickets").mkdir(parents=True)
        (repo / "comp" / _CHARTER).write_text(json.dumps({"gated_by": gated_by}))
        (repo / "comp" / "proofs" / "test_the_fixture.py").write_text(
            'PROVES = {"%s": {"1": "test_one"}}\n' % _TID)
        plan = commons / "tickets" / f"{_TID}-the-fixture.json"
        plan.write_text(json.dumps({"id": _TID, "owning_intention": "comp/" + _CHARTER,
                                    "workflow_and_state": _WF}, indent=2) + "\n")
        old_trace = os.environ.get("CAIRN_LB_TRACE_ROOT")
        os.environ["CAIRN_LB_TRACE_ROOT"] = str(t / "traces")
        real_clear = clearance.clear
        clearance.clear = recording_clear
        try:
            gate = gate_mod.ClearanceGate(participant=_Heard(), roots={
                "repo": repo, "commons": commons, "instance": t / "instance"})
            answer = gate.declared_verbs()["queueme"]({"sender": sender,
                                                       "body": {"fileref": str(plan)}})
            yield answer, handed
        finally:
            clearance.clear = real_clear
            if old_trace is None:
                os.environ.pop("CAIRN_LB_TRACE_ROOT", None)
            else:
                os.environ["CAIRN_LB_TRACE_ROOT"] = old_trace


def _actor(handed: list[dict]):
    assert len(handed) == 1, f"clearance.clear was handed {len(handed)} crossing(s): {handed}"
    return handed[0].get("actor")


def test_a_boat_only_cc_may_move_crosses_with_cc_when_cc_asks():
    with _asked(["CC"], "CC") as (answer, handed):
        assert _actor(handed) == "CC", f"actor {_actor(handed)!r}, not CC: {answer}"
        assert answer.get("accepted") is True and answer.get("workflow") == _NEXT \
            and not answer.get("after_crossing"), (
            f"the gate did not answer the workflow clear returned: {answer}")


def test_an_unadmitted_asker_leaves_the_gate_its_own_hand():
    with _asked(["CC"], "cairn-codemother-cli") as (answer, handed):
        assert _actor(handed) == "codemother", f"actor {_actor(handed)!r}, not codemother: {answer}"


def test_a_shared_boat_takes_the_askers_hand_and_the_holders_when_unnamed():
    with _asked(["codemother", "CC"], "CC") as (answer, handed):
        assert _actor(handed) == "CC", f"CC asked a shared boat, actor {_actor(handed)!r}: {answer}"
    with _asked(["codemother", "CC"], "") as (answer, handed):
        assert _actor(handed) == "codemother", (
            f"an unnamed sender, actor {_actor(handed)!r}: {answer}")


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
