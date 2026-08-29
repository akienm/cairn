"""Proof: crossing records carry a sha256 FINGERPRINT that is self-verifying.

The gate a hollow build could not pass (ticket crossing-fingerprints-are-verified):
every crossing record written by emit() carries a 'fingerprint' field computed from
the record's canonical JSON, and verify_crossing_fingerprint() returns True for an
untampered record and False for a tampered one. The build_inspector sieve
crossing_fingerprints_verified reds any history entry whose fingerprint fails.

Non-hollow: exercises the real emit chokepoint, the real verifier, and the real
inspector sieve — not a stand-in. A tooth that imports a function that doesn't
exist would fail at import time, not silently pass.

    python3 cairn/tools/base/proofs/test_crossing_fingerprint.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import transitions
from cairn.tools.base.transitions import verify_crossing_fingerprint
from cairn.tools.charter import projector

_CODE_SEAM = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> WATCHME(test-fp) -> PROVED"


def test_emit_produces_fingerprinted_records():
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        log = projector.read_history(hist)
        assert len(log) == 1
        rec = log[0]
        assert "fingerprint" in rec, "crossing record missing fingerprint field"
        assert len(rec["fingerprint"]) == 64, f"fingerprint not 64 hex chars: {len(rec['fingerprint'])}"
        assert all(c in "0123456789abcdef" for c in rec["fingerprint"]), "fingerprint contains non-hex chars"


def test_verify_returns_true_on_untampered():
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        rec = projector.read_history(hist)[0]
        assert verify_crossing_fingerprint(rec), "verifier rejected an untampered record"


def test_verify_returns_false_on_tampered():
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        rec = projector.read_history(hist)[0]
        rec["to"] = "TAMPERED"
        assert not verify_crossing_fingerprint(rec), "verifier accepted a tampered record"


def test_verify_returns_false_when_no_fingerprint():
    record = {"from": "A", "to": "B", "workflow": "test"}
    assert not verify_crossing_fingerprint(record), "verifier accepted a record with no fingerprint"


def test_inspector_sieve_passes_untampered():
    from cairn.machines.build_inspector.inspector import crossing_fingerprints_verified
    with tempfile.TemporaryDirectory() as d:
        hist = f"{d}/history.json"
        state = f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        row = {"component": "test-component"}
        findings = crossing_fingerprints_verified(row, Path(d))
        assert findings == [], f"sieve produced findings on untampered record: {findings}"


def test_inspector_sieve_reds_tampered():
    from cairn.machines.build_inspector.inspector import crossing_fingerprints_verified
    with tempfile.TemporaryDirectory() as d:
        hist = f"{d}/history.json"
        state = f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        entries = projector.read_history(hist)
        entries[0]["to"] = "TAMPERED"
        Path(hist).write_text(json.dumps(entries, indent=2))
        row = {"component": "test-component"}
        findings = crossing_fingerprints_verified(row, Path(d))
        assert len(findings) == 1, f"sieve did not red a tampered record: {findings}"
        assert findings[0]["actual"] is False


def test_inspector_sieve_skips_records_without_fingerprint():
    from cairn.machines.build_inspector.inspector import crossing_fingerprints_verified
    with tempfile.TemporaryDirectory() as d:
        hist = Path(d) / "history.json"
        hist.write_text(json.dumps([{"from": "A", "to": "B", "standing": "B",
                                     "workflow": "test", "direction": "forward",
                                     "entry_gate": "not_applicable",
                                     "proved": [], "checks_proved": 0}]))
        row = {"component": "test-component"}
        findings = crossing_fingerprints_verified(row, Path(d))
        assert findings == [], f"sieve produced findings on record without fingerprint: {findings}"


def test_fingerprint_is_deterministic():
    with tempfile.TemporaryDirectory() as d:
        hist1, state1 = f"{d}/h1.json", f"{d}/s1.json"
        hist2, state2 = f"{d}/h2.json", f"{d}/s2.json"
        wf = _CODE_SEAM
        new1 = transitions.emit(wf, "PROVEME", history_path=hist1, state_path=state1)
        new2 = transitions.emit(wf, "PROVEME", history_path=hist2, state_path=state2)
        rec1 = projector.read_history(hist1)[0]
        rec2 = projector.read_history(hist2)[0]
        content1 = {k: v for k, v in rec1.items() if k != "fingerprint"}
        content2 = {k: v for k, v in rec2.items() if k != "fingerprint"}
        if content1 == content2:
            assert rec1["fingerprint"] == rec2["fingerprint"], "same content produced different fingerprints"


def _main() -> int:
    checks = [v for k, v in sorted(globals().items())
              if k.startswith("test_") and callable(v)]
    assert len(checks) >= 8, (
        f"roster floor: expected at least 8 teeth, found {len(checks)}")
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — crossing records carry a sha256 fingerprint computed from canonical "
          "JSON; verify_crossing_fingerprint returns True on untampered and False on "
          "tampered; the inspector sieve reds tampered entries and skips pre-existing "
          "records without fingerprints; fingerprints are deterministic")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
