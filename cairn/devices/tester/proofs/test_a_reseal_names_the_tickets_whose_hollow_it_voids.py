"""Teeth for ticket d5a05b6d1752 — a seal that replaces a validation a hollow reading was taken
over names the ticket(s) that lost it, and says to retake it after PROVEME.

MEASURED 2026-11-12, n=5 (3195, 59f7, d692; 5defc and e8fb pending): a reseal over moved code
replaced the standing validation, ``persist_validation`` carried ``evidence.hollow`` forward only
when the fingerprint was unchanged, so the reading dropped silently, and each ticket's next PROVED
crossing bounced to FIXME on ``hollow_evidence_absent``. Dropping the reading is right (Law 3: the
code it measured is gone). Nobody being told is the defect.

Every tooth runs over a SCRATCH component, so the validations read and written are its own. The
tester is faked and sinks exactly as ``TesterDevice.run_proof`` does, so the seal path is the real
store door. ``cli`` and ``reseal`` are bound inside each tooth, never at module level.
"""
from __future__ import annotations

import contextlib
import io
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.validation_store.validation_store import (  # noqa: E402
    persist_validation, read_validations, record_hollow, source_fingerprint,
)
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "d5a05b6d1752": {
        "1": "test_a_seal_over_moved_code_names_the_ticket_whose_hollow_it_voided",
        "2": "test_a_seal_over_unchanged_code_carries_the_hollow_and_names_nobody",
        "3": "test_a_reseal_names_the_ticket_whose_hollow_it_voided",
    },
}

TID = "d5a0f1x70001"   # a scratch ticket id: never a real ticket's


def _component() -> tuple[Path, Path]:
    root = scratch_dir("cairn-hollow-voided-") / "widget"
    (root / "proofs").mkdir(parents=True)
    (root / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    proof = root / "proofs" / "test_widget.py"
    proof.write_text("assert 2 == 2\n", encoding="utf-8")
    return root, proof


def _record(proof: Path, *, caller: str = "the hollow fixture") -> dict:
    return {"claim": f"{proof.name} passes", "caller": caller,
            "date": datetime.now().isoformat(timespec="seconds"), "method": "fixture",
            "verdict": "green",
            "evidence": {"source_fingerprint": source_fingerprint(str(proof)), "returncode": 0,
                         "seal": {"verdict": "open"}},
            "falsifier": "the proof exits non-zero", "horizon": "until the proof changes"}


def _hollowed() -> tuple[Path, Path]:
    """A green standing seal with TID's hollow reading taken over it."""
    from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
    root, proof = _component()
    persist_validation(_record(proof), proof_path=str(proof), unsealing_because=NETWORK_SEAL_RETIRED)
    assert record_hollow(str(proof), TID, {"widget/code.py": ["test_widget"]}), "fixture: no seal"
    assert TID in read_validations(str(proof))[-1]["evidence"]["hollow"], "fixture: no hollow"
    return root, proof


class _Tester:
    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        record = _record(Path(proof_path), caller="the faked seal run")
        if sink == "validations":
            from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
            persist_validation(record, proof_path=str(proof_path),
                               unsealing_because=NETWORK_SEAL_RETIRED)
        return record


class _Raiser:
    def raise_trouble(self, identity, *, why, detail=None):
        pass

    def clear_trouble(self, identity, *, by, what_changed):
        pass


def _seal(monkeypatch, proof: Path) -> tuple[int, str]:
    from cairn.devices.tester import cli
    monkeypatch.setattr(cli, "TesterDevice", lambda: _Tester())
    monkeypatch.setattr(cli, "sweep_scratch", lambda: {"dropped": 0, "tables": []})
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = cli.main(["--seal", str(proof)])
    return rc, out.getvalue()


def test_a_seal_over_moved_code_names_the_ticket_whose_hollow_it_voided(monkeypatch):
    root, proof = _hollowed()
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    rc, out = _seal(monkeypatch, proof)
    standing = read_validations(str(proof))[-1]
    assert standing["caller"] == "the faked seal run", "fixture: the seal did not land"
    assert TID not in ((standing["evidence"].get("hollow")) or {}), "the moved code kept the reading"
    assert "HOLLOW VOIDED" in out and TID in out, f"the voided ticket was not named:\n{out}"
    assert f"cairn test --hollow {TID} --seal" in out, f"no retake command named:\n{out}"
    assert rc == 0, f"printed, never refused: rc={rc}\n{out}"


def test_a_seal_over_unchanged_code_carries_the_hollow_and_names_nobody(monkeypatch):
    _root, proof = _hollowed()
    rc, out = _seal(monkeypatch, proof)
    standing = read_validations(str(proof))[-1]
    assert TID in (standing["evidence"].get("hollow") or {}), "unchanged code lost the reading"
    assert "HOLLOW VOIDED" not in out and TID not in out, f"a carried hollow was named:\n{out}"
    assert rc == 0, rc


def test_a_reseal_names_the_ticket_whose_hollow_it_voided():
    from cairn.devices.tester.reseal import hollow_voided_lines, reseal_all
    root, proof = _hollowed()
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    outcome = reseal_all([proof], tester=_Tester(), raiser=_Raiser())
    results = outcome["results"]
    assert results and results[0].get("hollow_voided") == [TID], f"reseal named {results}"
    lines = "\n".join(hollow_voided_lines(results[0]["proof"], results[0]["hollow_voided"]))
    assert f"cairn test --hollow {TID} --seal" in lines, lines


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
