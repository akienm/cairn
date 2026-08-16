"""Proof: the QUORUM SIGNATURE GATE — a node proved by human judgment can actually be sealed.

THE DEFECT THIS CLOSES (2026-07-25). ``node_classes/concept-piece.json`` has specified this
gate since 2026-07-15, and in that time ZERO concept-piece VALIDATIONs were written. Not
because a reviewer was slow — because ``validations_path_for`` derived a seal's address from a
PROOF FILE path, and a concept-piece has no proof file. The single write-door could not
physically accept the record. The gate was never awaiting a signature; it was awaiting an
ADDRESS, and CC repeatedly reported the former, which is the report that kept it stuck.

WHAT THIS PROVES:
  - THE ADDRESS EXISTS. A concept-piece seal lands in ``validations/<stem>.json`` beside the
    artifact — derived, never chosen (Law 5).
  - IT IS THE SAME SCHEMA, NOT A NEW ONE. The record is the ratified eight fields and goes
    through the SAME ``persist_validation``. No rival door (Law 6).
  - A SELF-SEAL IS IMPOSSIBLE. Verdict and seal are different hands for a human-proved node; a
    notary who also reviewed is REFUSED. This is the hollow build in its purest form (Law 8).
  - A RUBBER STAMP IS IMPOSSIBLE. A signature with no restated-back understanding is refused —
    it would prove someone clicked, not that anyone read.
  - A QUORUM MEANS DISTINCT HANDS. One reviewer signing twice does not make two.
  - A REJECTION IS A VERDICT, NOT AN ERROR. A red seals red and is recorded, so the kick-back
    to the point of creation has evidence (CP2).
  - THE TRAIL APPENDS. A second review is a new dated entry, never a replacement (Law 7).

    python3 cairn/devices/tester/proofs/test_quorum.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.tester import quorum
from cairn.devices.tester.device import GREEN, RED, VALIDATION_FIELDS
from cairn.devices.tester.validation_store import (
    announce_verdict_change as vs_announce,
    verdict_change as vs_verdict_change,
    read_validations,
    validations_path_for_artifact,
)

AKIEN = {"signer": "akien", "verdict": GREEN, "restated": "the report resolves it on the first pass"}
CC = {"signer": "cc", "verdict": GREEN, "restated": "complete on first emission, no second run"}


def _seal(tmp, **over):
    art = Path(tmp) / "I-thing.md"
    art.write_text("# a concept-piece\n", encoding="utf-8")
    kw = dict(
        claim="the piece faithfully states the method",
        signatures=[dict(AKIEN)],
        notary="cc",
        falsifier="a reviewer withdraws, or the piece is edited after signing",
        horizon="valid until the artifact changes",
    )
    kw.update(over)
    return str(art), quorum.seal(str(art), **kw)


def _expect_refused(fn, needle):
    try:
        fn()
    except quorum.QuorumRefused as e:
        assert needle in str(e), f"refused for the wrong reason: {e}"
        return
    raise AssertionError(f"expected a refusal mentioning {needle!r} — a quiet pass here is the defect")


def test_a_concept_piece_can_finally_be_sealed():
    with tempfile.TemporaryDirectory() as tmp:
        art, v = _seal(tmp)
        path = validations_path_for_artifact(art)
        assert Path(path).exists(), "the seal must LAND — this is the thing that was impossible"
        assert Path(path).parent.name == "validations" and Path(path).name == "I-thing.json"
        assert Path(path).parent.parent == Path(art).parent, "beside the artifact it seals (Law 5)"
        assert read_validations(path=path) == [v]


def test_it_is_the_same_ratified_record_not_a_new_type():
    with tempfile.TemporaryDirectory() as tmp:
        _, v = _seal(tmp)
    assert set(v) == set(VALIDATION_FIELDS), \
        f"a quorum seal is the SAME eight fields — got {sorted(v)}"
    assert v["verdict"] == GREEN
    assert v["caller"] == "akien", "caller = THE REVIEWERS, per the class def — not the notary"
    assert "quorum signature gate" in v["method"] and "different hands" in v["method"]


def test_a_notary_who_reviewed_cannot_seal_their_own_verdict():
    """The one thing physics must hold here. Verdict and seal are different hands."""
    with tempfile.TemporaryDirectory() as tmp:
        _expect_refused(lambda: _seal(tmp, notary="akien"), "self-seal")
        _expect_refused(lambda: _seal(tmp, notary=""), "no notary")
        assert not (Path(tmp) / "validations").exists(), \
            "REFUSED BEFORE THE WRITE — an append-only trail cannot un-record a bad seal"


def test_a_rubber_stamp_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        _expect_refused(
            lambda: _seal(tmp, signatures=[{"signer": "akien", "verdict": GREEN, "restated": "  "}]),
            "rubber stamp")
        _expect_refused(
            lambda: _seal(tmp, signatures=[{"signer": "", "verdict": GREEN, "restated": "x"}]),
            "no signer")
        _expect_refused(
            lambda: _seal(tmp, signatures=[{"signer": "akien", "verdict": "maybe", "restated": "x"}]),
            "not verdicts")


def test_a_quorum_means_distinct_hands():
    with tempfile.TemporaryDirectory() as tmp:
        _expect_refused(lambda: _seal(tmp, signatures=[dict(AKIEN), dict(AKIEN)], quorum=2),
                        "repeat signer")
        _expect_refused(lambda: _seal(tmp, signatures=[], quorum=1), "empty room")
        _expect_refused(lambda: _seal(tmp, quorum=0), "nobody having read it")
        _, v = _seal(tmp, signatures=[dict(AKIEN), dict(CC)], quorum=2, notary="fable")
    assert v["verdict"] == GREEN and v["evidence"]["distinct_signers"] == 2
    assert v["caller"] == "akien, cc", "both reviewers own the verdict"


def test_a_rejection_is_a_verdict_and_is_recorded():
    """A reviewer saying no is a RED that routes back to origin (CP2) — not an exception."""
    with tempfile.TemporaryDirectory() as tmp:
        art, v = _seal(tmp, signatures=[
            dict(AKIEN), {"signer": "cc", "verdict": RED, "restated": "this misstates the why"}],
            quorum=2, notary="fable")
        trail = read_validations(path=validations_path_for_artifact(art))
    assert v["verdict"] == RED, "one rejection reds the whole gate — a quorum is not a majority vote"
    assert v["evidence"]["rejected_by"] == ["cc"], "the kick-back must name who rejected it"
    assert len(trail) == 1, "and the red is RECORDED, or the kick-back has no evidence"


def test_a_SECOND_REVIEW_replaces_the_first_AND_ANNOUNCES_THE_FLIP():
    """THE INVERSION, on the human-proved half (2026-08-16, ticket
    a-validation-is-one-current-record-not-a-trail). This asserted the opposite until today —
    that the earlier red SURVIVES the later green — and the reversal is the ticket's whole
    subject: the validation is ONE record, and the accumulation belongs to the ticket.

    But the review cycle is exactly where dropping the earlier record would be worst, because
    the red IS the kick-back's evidence, so the tooth asserts both halves together. What
    replaces the red is louder than what held it: the flip fires out of TroubleDevice before
    the green lands, carrying both verdicts, both dates and both callers. Under the old shape
    it sat at index 0 of a file whose every reader took [-1].

    The trouble device is INJECTED with a temp root so proving this never writes into the
    commons — but the ARTIFACT is deliberately not under the temp root, because the guard in
    persist_validation is 'is this a fixture address', and a temp artifact would test the
    guard instead of the announcement."""
    from cairn.devices.tester.validation_store import persist_validation
    from cairn.devices.trouble.trouble import TroubleDevice

    with tempfile.TemporaryDirectory() as tmp:
        art = Path(tmp) / "I-thing.md"
        art.write_text("# a concept-piece\n", encoding="utf-8")
        common = dict(claim="c", notary="cc", falsifier="f", horizon="h")
        quorum.seal(str(art), signatures=[
            {"signer": "akien", "verdict": RED, "restated": "not yet — the why is thin"}], **common)
        quorum.seal(str(art), signatures=[
            {"signer": "akien", "verdict": GREEN, "restated": "the rewrite is faithful"}], **common)
        trail = read_validations(path=validations_path_for_artifact(str(art)))
        assert [t["verdict"] for t in trail] == [GREEN], (
            "the second review REPLACES the first — one current record per artifact")

        # And the flip is announced. Replayed through the door directly, with a non-fixture
        # address, so the announcement path is the one under test rather than the guard.
        device = TroubleDevice(root=os.path.join(tmp, "troubles"))
        outside = Path.home() / "dev" / "src" / "cairn" / "cairn" / "devices" / "tester" \
            / "proofs" / "fixtures" / "green_proof.py"
        record = dict(trail[0])
        change = vs_verdict_change([dict(record, verdict=RED, caller="akien")], record)
        assert change is not None and change["from"] == RED and change["to"] == GREEN
        vs_announce(str(outside), change, device=device)
        live = device.live()
        assert len(live) == 1 and RED in live[0]["why"] and GREEN in live[0]["why"], live


def test_the_door_refuses_a_caller_that_has_not_decided_what_it_seals():
    from cairn.devices.tester.validation_store import persist_validation
    rec = {k: "x" for k in VALIDATION_FIELDS}
    for kwargs in ({}, {"proof_path": "a/proofs/b.py", "artifact_path": "a/b.md"}):
        try:
            persist_validation(rec, **kwargs)
        except ValueError as e:
            assert "EITHER" in str(e)
        else:
            raise AssertionError("naming both addresses, or neither, must be refused")


def test_the_real_intention_is_a_real_file_the_gate_can_address():
    """Non-hollow: the piece this gate was built to seal is on disk and addressable.
    Asserts the INVARIANT (it exists, the address derives beside it), never its seal state —
    that legitimately moves the moment it is signed."""
    art = Path(__file__).resolve().parents[4].parent / "CairnCommons" / \
        "intentions-not-beside-code" / "I-complete-diagnostic-on-first-pass.md"
    assert art.exists(), f"the concept-piece must be a real artifact, not a plan: {art}"
    seal_path = Path(validations_path_for_artifact(str(art)))
    assert seal_path.parent.parent == art.parent and seal_path.name.endswith(".json")


TESTS = [
    test_a_concept_piece_can_finally_be_sealed,
    test_it_is_the_same_ratified_record_not_a_new_type,
    test_a_notary_who_reviewed_cannot_seal_their_own_verdict,
    test_a_rubber_stamp_is_refused,
    test_a_quorum_means_distinct_hands,
    test_a_rejection_is_a_verdict_and_is_recorded,
    test_a_SECOND_REVIEW_replaces_the_first_AND_ANNOUNCES_THE_FLIP,
    test_the_door_refuses_a_caller_that_has_not_decided_what_it_seals,
    test_the_real_intention_is_a_real_file_the_gate_can_address,
]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
