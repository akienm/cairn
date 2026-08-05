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

import json
import os
import re
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


def test_the_NAIVE_overwrite_cannot_land_bytes():
    """THE TICKET'S FALSIFIER, first half: 'a test that writes the validation file by a path
    OTHER than persist_validation and is NOT refused.'

    The lived symptom, verbatim from the trouble: a hand-write 'destroys a proof's whole seal
    history silently and permanently, and looks exactly like a fresh seal.' This is that
    hand-write — the plainest one, the one nobody meant to do — and it now raises at the
    ``open`` because the door left the trail at 0444."""
    v = TesterDevice().run_proof(_GREEN_FIXTURE, isolation="none")
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        path = vs.persist_validation(v, proof_path=proof)
        assert oct(os.stat(path).st_mode & 0o777) == "0o444", oct(os.stat(path).st_mode)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([{"gotcha": True}], f)
        except PermissionError:
            pass
        else:
            raise AssertionError(
                "a second path landed bytes on the trail — the gate is not physics")
        assert len(vs.read_validations(proof)) == 1, "the trail must be untouched"


def test_a_FORCED_write_cannot_pass_for_a_seal():
    """THE TICKET'S FALSIFIER, second half — the deliberate bypass, which the mode bit alone
    cannot stop and is not meant to.

    Force it the only way a real bypass can: chmod the file writable, then overwrite the whole
    trail with a plausible-looking green. Every one of the eight fields is right. What it
    cannot fake is the link, because only ``persist_validation`` mints one — so ``standing``
    refuses the TRAIL rather than reading a verdict out of it, and says so in one pass.

    This is the tooth that carries the trouble's actual sentence: it no longer looks exactly
    like a fresh seal."""
    real = TesterDevice().run_proof(_GREEN_FIXTURE, isolation="none")
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        # The fingerprint must describe THIS tmp component, not the fixture's — otherwise
        # standing() refuses on a closed horizon and the tooth would never reach the chain.
        v = dict(real, evidence=dict(real["evidence"],
                                     source_fingerprint=vs.source_fingerprint(proof)))
        path = vs.persist_validation(v, proof_path=proof)
        assert vs.standing(proof)["proven"], vs.standing(proof)["why"]

        forged = {k: val for k, val in v.items()}
        forged["evidence"] = {k: val for k, val in v["evidence"].items()
                              if k != vs.TRAIL_LINK}
        os.chmod(path, 0o644)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([forged], f)

        breaks = vs.verify_trail(vs.read_validations(proof))
        assert breaks, "an unlinked record written over a linked trail must be a break"
        verdict = vs.standing(proof)
        assert verdict["proven"] is False, "a trail written around the door cannot clear"
        assert "DID NOT COME WHOLE THROUGH persist_validation" in verdict["why"], verdict["why"]
        assert "recover the trail from git" in verdict["why"].lower(), \
            "the refusal must carry its remediation — one report, no second call"


def test_an_EDIT_to_an_older_entry_breaks_the_newest_link():
    """History is what a hand-write destroys, so history is what the chain has to cover.

    Two seals, then an in-place edit of the FIRST — the shape that is invisible to a
    length check and to a 'newest entry' reader, because the trail still has two entries and
    the newest one is untouched. The link on entry 1 commits to entry 0, so entry 0 cannot
    move without entry 1 saying so."""
    dev = TesterDevice()
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        path = vs.persist_validation(dev.run_proof(_GREEN_FIXTURE, isolation="none"),
                                     proof_path=proof)
        vs.persist_validation(dev.run_proof(_GREEN_FIXTURE, isolation="none"),
                              proof_path=proof)
        trail = vs.read_validations(proof)
        assert not vs.verify_trail(trail), "the door's own two-entry trail must verify"

        trail[0]["verdict"] = "green"          # rewriting the past, leaving the present alone
        trail[0]["claim"] = "it always passed"
        os.chmod(path, 0o644)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(trail, f)

        breaks = vs.verify_trail(vs.read_validations(proof))
        # BOTH entries are named, and entry 0 is named FIRST — a link covers the record
        # itself as well as everything under it, so the report localizes the tamper to its
        # earliest point instead of only saying "somewhere below here" (Law 7: the complete
        # diagnostic on the first pass, no second call to find out where).
        assert len(breaks) == 2, breaks
        assert breaks[0].startswith("entry 0") and "entry 1" in breaks[1], breaks
        assert all("changed after it was sealed" in b for b in breaks), breaks


def test_ADOPTION_links_a_legacy_trail_and_REFUSES_to_repair_a_broken_one():
    """73 trails predated links. The first draft tolerated an unlinked leading prefix as
    'prehistory' — and the tooth above killed that in one firing, because an overwrite that
    drops every link is then indistinguishable from a legacy trail. A tolerance is a forger's
    costume whenever the forger can produce the thing being tolerated. So the legacy trails
    are ADOPTED, once, and after that a missing link is a break like any other.

    The second half is the part that keeps adoption from becoming a laundering tool: a trail
    with a link that no longer verifies is REFUSED, not re-linked. A migration that quietly
    re-chained a tampered trail would erase exactly the evidence the chain exists to keep."""
    v = TesterDevice().run_proof(_GREEN_FIXTURE, isolation="none")
    legacy = {k: val for k, val in v.items()}
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        path = vs.validations_path_for(proof)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:      # a trail from before links existed
            json.dump([legacy, legacy], f)
        assert len(vs.verify_trail(vs.read_validations(proof))) == 2, \
            "an unlinked entry is a break — there is no prehistory clause to hide in"

        assert vs.adopt_chain(path) == 2
        assert vs.verify_trail(vs.read_validations(proof)) == [], "adoption must chain the trail"
        assert vs.adopt_chain(path) == 0, "adoption is idempotent — re-running links nothing"

        vs.persist_validation(v, proof_path=proof)        # the door appends onto adopted history
        trail = vs.read_validations(proof)
        assert len(trail) == 3 and not vs.verify_trail(trail), trail

        os.chmod(path, 0o644)                             # now tamper, then try to launder it
        tampered = [dict(trail[0], claim="rewritten history"), trail[1], trail[2]]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tampered, f)
        try:
            vs.adopt_chain(path)
        except ValueError as err:
            assert "BREAK" in str(err) and "recover from git" in str(err), err
        else:
            raise AssertionError("adoption must refuse to re-link a tampered trail")


def test_the_caller_cannot_hand_the_door_a_link():
    """The link is evidence only because ONE hand mints it. A caller that supplies its own is
    either replaying an existing entry or hand-building a forgery, and either way the door was
    not the hand that sealed it (Law 6)."""
    v = TesterDevice().run_proof(_GREEN_FIXTURE, isolation="none")
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        premined = dict(v, evidence=dict(v["evidence"], **{vs.TRAIL_LINK: "de" * 32}))
        try:
            vs.persist_validation(premined, proof_path=proof)
        except ValueError as err:
            assert vs.TRAIL_LINK in str(err), err
        else:
            raise AssertionError("a caller-supplied link must be refused")
        assert vs.read_validations(proof) == [], "a refused write leaves nothing behind"

        blob = dict(v, evidence="a stringified blob")
        try:
            vs.persist_validation(blob, proof_path=proof)
        except ValueError as err:
            assert "structure, not a blob" in str(err), err
        else:
            raise AssertionError("evidence that cannot carry a link must be refused")


def test_NO_SECOND_WRITER_EXISTS_IN_THE_CORPUS():
    """The third layer, and the one that keeps the other two honest over time: the mode bit
    and the chain both act at RUNTIME, on a bypass that already happened. This one refuses the
    bypass at BUILD time — a module that writes a validations/ path and is not the store
    itself reds the corpus on arrival.

    Censused by the SHAPE OF USE, not by an identifier: what is scanned for is an open/write
    aimed at a ``validations/`` address, however it is spelled. A scan keyed on a constant's
    NAME misses every instance that wrote the path inline as a literal."""
    repo = Path(__file__).resolve().parents[3]
    store = (repo / "cairn" / "tester" / "validation_store.py").resolve()
    offenders, scanned = [], 0
    for path in sorted(repo.glob("**/*.py")):
        if "__pycache__" in str(path) or path.resolve() == store:
            continue
        if "/proofs/" in str(path):
            continue          # a proof MUST be able to forge one — that is how it proves this
        src = path.read_text(encoding="utf-8", errors="replace")
        if "validations" not in src:
            continue
        scanned += 1
        for lineno, line in enumerate(src.splitlines(), 1):
            if "validations" not in line or line.lstrip().startswith("#"):
                continue
            if re.search(r'open\s*\([^)]*validations|json\.dump\s*\([^)]*validations', line):
                offenders.append(f"{path.relative_to(repo)}:{lineno}: {line.strip()}")
    assert scanned >= 3, f"only {scanned} file(s) mention validations — the scan lost its corpus"
    assert not offenders, (
        "a second writer to the validation trail exists in the corpus — persist_validation is "
        "not the only path (Law 6):\n" + "\n".join(offenders))


def _main() -> int:
    checks = [
        test_a_real_validation_round_trips_beside_its_proof,
        test_append_only_a_rerun_does_not_overwrite,
        test_a_drifted_record_is_refused,
        test_the_NAIVE_overwrite_cannot_land_bytes,
        test_a_FORCED_write_cannot_pass_for_a_seal,
        test_an_EDIT_to_an_older_entry_breaks_the_newest_link,
        test_ADOPTION_links_a_legacy_trail_and_REFUSES_to_repair_a_broken_one,
        test_the_caller_cannot_hand_the_door_a_link,
        test_NO_SECOND_WRITER_EXISTS_IN_THE_CORPUS,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — validation_store: a VALIDATION lands beside its proof, append-only, drift refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
