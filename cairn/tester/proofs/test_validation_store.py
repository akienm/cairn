"""Proof for tester/validation_store — a VALIDATION lands as git-JSON beside the proof it seals.

This is the beside-code home that REPLACED db_domain's `validations` table (ruling in
tickets/charter-state-history-split.json child b; migration 2026-07-22). It closes the
tester's long-standing open edge (a): VALIDATIONS were produced but not persisted. Teeth a
hollow store could not pass:

  - A REAL VALIDATION ROUND-TRIPS AS STRUCTURE. A genuine record from TesterDevice.run_proof
    persists and greps back with exactly the ratified eight fields, its `evidence` (seal +
    returncode) intact as a dict, not a stringified blob. (The property db_domain's jsonb
    used to guarantee, now guaranteed by JSON on disk.)
  - PLACEMENT IS DERIVED, NOT CHOSEN (Law 5). A proof at .../proofs/<stem>.py seals into
    .../validations/<stem>.json — beside the code it explains. The caller never picks the
    path, so the seal cannot drift away from the thing it seals.
  - APPEND-ONLY (Law 7). A second persist APPENDS a fresh dated entry; it never overwrites
    the first. A record of truth admits no update-in-place and no delete — a re-run's verdict
    is a new entry (Law 3: the old seal expired), not a replacement.
  - DRIFT IS REFUSED (physics, mirroring the Postgres CHECK it replaced). A record that is not
    exactly the eight fields is rejected, so a malformed dict cannot land and pass for a seal.

Self-cleaning: writes into a throwaway temp component tree, so no real component's
`validations/` is touched.

    python3 cairn/tester/proofs/test_validation_store.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tester import validation_store as vs
from cairn.tester.device import VALIDATION_FIELDS, TesterDevice

_GREEN_FIXTURE = _REPO_ROOT / "cairn" / "tester" / "proofs" / "fixtures" / "green_proof.py"


def _fake_proof(tmp: str) -> str:
    """A stand-in proof at <tmp>/somecomp/proofs/test_thing.py — its parent tree is real dirs
    so the derived validations/ path is a real place to write, but nothing real is touched."""
    proofs = os.path.join(tmp, "somecomp", "proofs")
    os.makedirs(proofs, exist_ok=True)
    p = os.path.join(proofs, "test_thing.py")
    Path(p).write_text("# stand-in proof\n", encoding="utf-8")
    return p


def test_a_real_validation_round_trips_beside_its_proof():
    v = TesterDevice().run_proof(_GREEN_FIXTURE, isolation="none")
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        path = vs.persist_validation(v, proof_path=proof)

        # PLACEMENT: validations/<stem>.json beside proofs/, name derived from the proof.
        assert path == os.path.join(tmp, "somecomp", "validations", "test_thing.json"), path
        assert os.path.exists(path)

        back = vs.read_validations(proof)
        assert len(back) == 1, "the persisted VALIDATION must grep back"
        stored = back[0]
        assert set(stored) == set(VALIDATION_FIELDS), f"exactly the 8 fields, got {sorted(stored)}"
        assert stored["verdict"] == v["verdict"]
        # evidence must survive as STRUCTURE, seal and all.
        assert isinstance(stored["evidence"], dict)
        assert stored["evidence"]["seal"]["verdict"] == v["evidence"]["seal"]["verdict"]


def test_append_only_a_rerun_does_not_overwrite():
    v = TesterDevice().run_proof(_GREEN_FIXTURE, isolation="none")
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        vs.persist_validation(v, proof_path=proof)
        vs.persist_validation(v, proof_path=proof)  # a re-run seals again

        back = vs.read_validations(proof)
        assert len(back) == 2, "a second seal APPENDS — the trail is a record of truth (Law 7)"


def test_a_drifted_record_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        missing_a_field = {k: "x" for k in VALIDATION_FIELDS if k != "horizon"}
        try:
            vs.persist_validation(missing_a_field, proof_path=proof)
        except ValueError:
            pass
        else:
            raise AssertionError("a record that is not exactly the 8 fields must be REFUSED (Law 7)")
        # and nothing landed — a refused write leaves no trail
        assert vs.read_validations(proof) == []


def _main() -> int:
    checks = [
        test_a_real_validation_round_trips_beside_its_proof,
        test_append_only_a_rerun_does_not_overwrite,
        test_a_drifted_record_is_refused,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — validation_store: a VALIDATION lands beside its proof, append-only, drift refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
