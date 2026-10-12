"""Teeth for ticket 2dd69b2ba087 — a plain seal answers rung 4 as the reseal does and keeps the ladder.

MEASURED 2026-10-08 on cairn/tools/scratch/proofs/test_scratch.py: ``cairn test --reseal``
printed RUNG 4 REFUSED (the proof's bytes had moved under an open ladder, and no ruling rode
along); the seal at 21961d19 carried the ladder; ``cairn test --seal`` on the same proof then
wrote a seal with the ladder gone (c3ef0d02). Two seal writers, one rung-4 gate, and only one
of them asked it.

Every tooth runs ``cli.main`` over a SCRATCH component, so the validations it reads and writes
are the scratch component's own (the reseal door's proofs use the same fixture shape). The
tester is faked so the run is a count: rung 4 is a gate BEFORE the run, and "runs nothing" is
the clause a real subprocess could not show. The fake persists when asked to sink, exactly as
``TesterDevice.run_proof`` does, so a seal path that drops the ladder drops it here too. The
answered question is a fixture in a scratch question store — the shape
``cairn.tools.question.question.answer`` writes — read through that tool's own ``QUESTIONS_DIR``.
``cli`` and ``reseal`` are imported inside each tooth, never at module level.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.validation_store.validation_store import (  # noqa: E402
    persist_validation, read_validations, source_fingerprint, validations_path_for,
)
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "2dd69b2ba087": {
        "1": "test_a_moved_proof_under_an_open_ladder_is_refused_without_a_ruling",
        "2": "test_an_answered_question_lets_the_seal_land",
        "3": "test_a_red_seal_over_an_open_ladder_keeps_the_ladder",
    },
}

RUN_CALLER = "the faked seal run"   # the store keeps the standing record, so a landed seal is
                                    # told from the fixture's by who wrote it
MOVED_FROM = "0" * 64   # the bytes the ladder bounded the repair to — never this file's


def _component() -> Path:
    root = scratch_dir("cairn-plainseal-rung4-") / "widget"
    (root / "proofs").mkdir(parents=True)
    (root / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    proof = root / "proofs" / "test_widget.py"
    proof.write_text("assert 2 == 2\n", encoding="utf-8")
    return proof


def _record(proof: Path, verdict: str, evidence: dict | None = None, *,
            caller: str = "the ladder's fixture") -> dict:
    ev = {"source_fingerprint": source_fingerprint(str(proof)),
          "returncode": 0 if verdict == "green" else 1, "seal": {"verdict": "open"}}
    ev.update(evidence or {})
    return {"claim": f"{proof.name} passes", "caller": caller,
            "date": datetime.now().isoformat(timespec="seconds"),
            "method": "fixture", "verdict": verdict, "evidence": ev,
            "falsifier": "the proof exits non-zero", "horizon": "until the proof changes"}


def _open_ladder(proof: Path, bound: str) -> dict:
    """Stand a red seal carrying an open ladder that bounds the repair to ``bound``."""
    ladder = {"proof_sha256": bound, "opened": "2026-10-08T10:00:00",
              "last_red": "2026-10-08T10:00:00", "passes": 1, "rung": 3,
              "trouble": "seal-red-fixture-widget", "ruling": None}
    from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
    persist_validation(_record(proof, "red", {"reseal_ladder": ladder}), proof_path=str(proof),
                       unsealing_because=NETWORK_SEAL_RETIRED)
    return ladder


class _Tester:
    """Counts runs; sinks the way the real runner does, so the seal path is the real one."""

    def __init__(self, verdict: str):
        self.verdict, self.runs = verdict, 0

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        self.runs += 1
        record = _record(Path(proof_path), self.verdict, caller=RUN_CALLER)
        if sink == "validations":
            from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
            persist_validation(record, proof_path=str(proof_path),
                               unsealing_because=NETWORK_SEAL_RETIRED)
        return record


def _seal(monkeypatch, tester: _Tester, *argv: str) -> int:
    from cairn.devices.tester import cli
    monkeypatch.setattr(cli, "TesterDevice", lambda: tester)
    monkeypatch.setattr(cli, "sweep_scratch", lambda: {"dropped": 0, "tables": []})
    return cli.main(["--seal", *argv])


def _bytes(proof: Path) -> bytes:
    return Path(validations_path_for(str(proof))).read_bytes()


def test_a_moved_proof_under_an_open_ladder_is_refused_without_a_ruling(monkeypatch):
    """THE DISCRIMINATING TOOTH FOR cli.py: the ladder bounds hash A, the proof hashes B, no
    ruling rides along — so --seal exits non-zero, the proof never runs, nothing is written."""
    proof = _component()
    _open_ladder(proof, MOVED_FROM)
    before = _bytes(proof)
    tester = _Tester("green")
    rc = _seal(monkeypatch, tester, str(proof))
    assert rc != 0, rc
    assert tester.runs == 0, f"rung 4 is a gate before the run; it ran {tester.runs} time(s)"
    assert _bytes(proof) == before, "a refused seal wrote a record"


def test_an_answered_question_lets_the_seal_land(monkeypatch):
    """The same moved proof with an id Akien answered: the proof runs once and its seal lands."""
    from cairn.tools.question import question as question_mod
    qroot = scratch_dir("cairn-plainseal-questions-")
    qid = "open-f1x72dd60001"
    (qroot / f"{qid}.json").write_text(json.dumps({
        "id": qid, "date": "2026-10-12", "ticket": "f1x72dd60000",
        "question": "may the widget proof's claim change?", "why_it_blocks": "fixture",
        "raised_by": "fixture", "born_of": None, "source": None, "resolved": True,
        "answer": "yes", "answered_by": "Akien, recorded by caller class cc",
        "answered_at": "2026-10-12T09:00:00", "spawned": []}), encoding="utf-8")
    monkeypatch.setattr(question_mod, "QUESTIONS_DIR", qroot)
    proof = _component()
    _open_ladder(proof, MOVED_FROM)
    tester = _Tester("red")
    _seal(monkeypatch, tester, str(proof), "--ruling", qid)
    assert tester.runs == 1, tester.runs
    standing = read_validations(str(proof))[-1]
    assert standing["caller"] == RUN_CALLER, f"the ruled seal did not land: {standing['caller']}"


def test_a_red_seal_over_an_open_ladder_keeps_the_ladder(monkeypatch):
    """The hash unchanged, the ladder open, the run red: the seal that lands carries the
    ladder forward, so read_ladder() reads what it read before the seal."""
    from cairn.devices.tester.reseal import proof_sha256, read_ladder
    proof = _component()
    _open_ladder(proof, proof_sha256(proof))
    before = read_ladder(proof)
    assert before, "fixture: no open ladder stood"
    tester = _Tester("red")
    _seal(monkeypatch, tester, str(proof))
    assert tester.runs == 1, tester.runs
    assert read_ladder(proof) == before, {"before": before, "after": read_ladder(proof)}


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
