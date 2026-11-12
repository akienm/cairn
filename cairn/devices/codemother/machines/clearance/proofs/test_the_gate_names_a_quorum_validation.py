"""Proof for ticket b548983a15ba — the clearance gate names a human-proved piece's quorum
validation on its crossing out of PROVEME.

The chokepoint's quorum seat (transitions.py ``_quorum_gate``) reads ``emit(..., validation=<path>)``.
A ticket asks the gate with only its fileref, and the gate never named one, so no concept-piece
could cross into PROVED through the queue (measured 2026-11-12 on 0682e51ab011: "the crossing names
no validation"). Now the gate derives it the way the seal did, beside the piece the crossings named
(``validations_path_for_artifact``).

One tooth per falsifier clause. Each runs in a scratch world (a repo with one charter, a commons with
one plan, a piece and, where the tooth wants one, its seal) and patches ``clearance.clear`` on its
module to record the kwargs it is handed. The gate module is imported inside each tooth.

    python3 cairn/devices/codemother/machines/clearance/proofs/test_the_gate_names_a_quorum_validation.py
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {
    "b548983a15ba": {
        "1": "test_a_sealed_concept_piece_crosses_naming_its_seal",
        "2": "test_a_code_seam_crossing_names_no_validation",
        "3": "test_an_unsealed_concept_piece_names_none",
    },
}

_DOTTED = "cairn.devices.codemother.machines.clearance"
_CHARTER = "intention" + "+why.json"
_TID = "0a0b0c0d0e0f"
_CP = "concept-piece@v1: THINKME -> TICKETME -> FIXME -> BUILDME -> [PROVEME:waiting] -> PROVED"
_CS = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME:waiting] -> PROVED"
_STORE_CHARTER = _REPO.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _STORE_CHARTER.is_file():
    _STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"

# hollow runs this proof in a worktree with no CairnCommons beside it, where transitions'
# repo-relative class table points at nothing (measured 2026-11-12, this ticket's first hollow:
# every tooth red at HEAD): so with no sibling, the class table reads the home checkout, for
# this process only (the same fallback as cairn/machines/ticket/proofs/test_a_ticket_queues_itself_at_a_gate.py).
if not (_REPO.parent / "CairnCommons").is_dir():
    from cairn.tools.base import transitions as _transitions
    _transitions._NODE_CLASSES = _STORE_CHARTER.parents[1] / "node_classes"
    for _fn in (_transitions.emit, _transitions.load_class_def):
        for _k in ("node_class_root", "root"):
            if _k in (_fn.__kwdefaults__ or {}):
                _fn.__kwdefaults__[_k] = _STORE_CHARTER.parents[1] / "node_classes"


class _Heard:
    def request(self, **kw):
        return {"body": {"accepted": True}}

    def post(self, **kw):
        pass


@contextmanager
def _asked(workflow: str, sealed: bool):
    """Queue a scratch boat standing at PROVEME on ``workflow``; its crossings name one piece,
    sealed beside it when ``sealed``. Yield (the answer, the kwargs clear was handed, the seal)."""
    from cairn.tools.base import ticket_file
    clearance = importlib.import_module(_DOTTED + ".clearance")
    gate_mod = importlib.import_module(_DOTTED + ".gate")
    handed: list[dict] = []

    def recording_clear(wf, to, **kw):
        handed.append({"workflow": wf, "to": to, **kw})
        return wf.replace("[PROVEME:waiting] -> PROVED", "PROVEME -> [PROVED]")

    with tempfile.TemporaryDirectory(prefix="clearance-quorum-") as tmp:
        t = Path(tmp)
        repo, commons = t / "repo", t / "commons"
        (repo / "comp").mkdir(parents=True)
        (commons / "tickets" / "validations").mkdir(parents=True)
        shutil.copy(_STORE_CHARTER, commons / "tickets" / _STORE_CHARTER.name)
        (repo / "comp" / _CHARTER).write_text(json.dumps({"gated_by": ["CC"]}))
        piece = commons / "tickets" / f"{_TID}-the-piece.md"
        piece.write_text("the piece\n")
        seal = commons / "tickets" / "validations" / f"{_TID}-the-piece.json"
        if sealed:
            seal.write_text(json.dumps([{"verdict": "green", "method": "quorum signature gate"}]))
        plan = commons / "tickets" / f"{_TID}-the-fixture.json"
        plan.write_text(json.dumps({"id": _TID, "owning_intention": "comp/" + _CHARTER,
                                    "workflow_and_state": workflow}, indent=2) + "\n")
        old_trace = os.environ.get("CAIRN_LB_TRACE_ROOT")
        os.environ["CAIRN_LB_TRACE_ROOT"] = str(t / "traces")
        real_clear, real_tickets = clearance.clear, ticket_file._TICKETS
        clearance.clear = recording_clear
        ticket_file._TICKETS = commons / "tickets"
        try:
            gate = gate_mod.ClearanceGate(participant=_Heard(), roots={
                "repo": repo, "commons": commons, "instance": t / "instance"})
            gate.proven_by = lambda tid, target: [str(piece)]
            answer = gate.declared_verbs()["queueme"]({"sender": "CC",
                                                       "body": {"fileref": str(plan)}})
            yield answer, handed, str(seal)
        finally:
            clearance.clear, ticket_file._TICKETS = real_clear, real_tickets
            if old_trace is None:
                os.environ.pop("CAIRN_LB_TRACE_ROOT", None)
            else:
                os.environ["CAIRN_LB_TRACE_ROOT"] = old_trace


def _one(handed: list[dict], answer: dict) -> dict:
    assert len(handed) == 1, f"clearance.clear was handed {len(handed)} crossing(s): {answer}"
    return handed[0]


def test_a_sealed_concept_piece_crosses_naming_its_seal():
    with _asked(_CP, sealed=True) as (answer, handed, seal):
        got = _one(handed, answer).get("validation")
        assert got == seal, f"validation {got!r}, not the seal beside the piece {seal!r}: {answer}"


def test_a_code_seam_crossing_names_no_validation():
    with _asked(_CS, sealed=True) as (answer, handed, _seal):
        crossing = _one(handed, answer)
        assert "validation" not in crossing, f"a code-seam was handed {crossing.get('validation')!r}"


def test_an_unsealed_concept_piece_names_none():
    with _asked(_CP, sealed=False) as (answer, handed, _seal):
        crossing = _one(handed, answer)
        assert "validation" not in crossing, (
            f"no seal on disk, yet the gate named {crossing.get('validation')!r}")


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
