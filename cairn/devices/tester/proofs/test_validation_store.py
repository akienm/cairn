"""Proof for tester/validation_store — a VALIDATION lands as git-JSON beside the proof it seals.

This is the beside-code home that REPLACED db_domain's `validations` table (ruling in
tickets/charter-state-history-split.json child b; migration 2026-07-22). It closes the
tester's long-standing open edge (a): VALIDATIONS were produced but not persisted. Teeth a
hollow store could not pass:

  - A REAL VALIDATION ROUND-TRIPS AS STRUCTURE. A genuine record from TesterDevice.run_proof
    persists and greps back with exactly the ratified eight fields, its `evidence` (seal +
    returncode) intact as a dict, not a stringified blob.
  - PLACEMENT IS DERIVED, NOT CHOSEN (Law 5). A proof at .../proofs/<stem>.py seals into
    .../validations/<stem>.json — beside the code it explains. The caller never picks the
    path, so the seal cannot drift away from the thing it seals.
  - ONE CURRENT RECORD (2026-08-16, ticket a-validation-is-one-current-record-not-a-trail).
    A second persist REPLACES the first: the file holds one record, because a VALIDATION
    expires (Law 3) and what verifies the survivor is its fingerprint, not the pile beneath it.
  - AND THE REPLACE IS LOUD, which is what makes it legal under Law 7. A verdict that CHANGES
    fires out of TroubleDevice before the replace lands; a re-run that agrees fires nothing.
    Six teeth cover that door, including the one that proves it does not swallow the new
    measurement when the trouble store is unreachable.
  - DRIFT IS REFUSED (physics, mirroring the Postgres CHECK it replaced). A record that is not
    exactly the eight fields is rejected, so a malformed dict cannot land and pass for a seal.

WHAT THIS FILE NO LONGER CLAIMS, AND THE MEASUREMENT THAT TOOK IT AWAY. Ten teeth here used
to rest on the hash chain, and one of them —``test_a_FORCED_write_cannot_pass_for_a_seal`` —
said in its own docstring that a forger "cannot fake the link". That was tested against a
forger who did not bother to try: ``_link_for`` was a pure importable function over
(trail, record), so calling it produced a trail that verified and stood green. Run on
2026-08-16, not reasoned. What the chain actually bought was append-only-ness — a DELETION
was detectable — and that is the property this ticket deliberately gives up, so the chain
retired with it. The tamper story that survives is narrower and true, and it is asserted
here rather than asserted about: the mode bit, the corpus second-writer census, the source
fingerprint, and git.

Self-cleaning: writes into a throwaway temp component tree, so no real component's
`validations/` is touched — and the announcement door is injected with a temp trouble root,
so proving the loud half never writes a trouble into the commons.

    python3 cairn/devices/tester/proofs/test_validation_store.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester import validation_store as vs
from cairn.devices.tester.device import VALIDATION_FIELDS, TesterDevice
from cairn.devices.trouble.trouble import TroubleDevice

_GREEN_FIXTURE = _REPO_ROOT / "cairn" / "devices" / "tester" / "proofs" / "fixtures" / "green_proof.py"

# A POPULATION FLOOR, NOT A CENSUS. The corpus-wide tooth below asserts a property over
# every real validations file, and the failure mode it is most exposed to is passing
# because it found nothing to check — a broken glob and a clean corpus look identical from
# the outside. 90 files were measured on 2026-08-16; the floor sits under that with room
# for ordinary churn, so it bites on a lost population rather than on a deleted component.
# It is deliberately NOT the count: asserting 90 would red the moment a legitimate new
# validations file appeared, which is the snapshot-instead-of-invariant failure.
_CORPUS_FLOOR = 70


def _fake_proof(tmp: str) -> str:
    """A stand-in proof at <tmp>/somecomp/proofs/test_thing.py — its parent tree is real dirs
    so the derived validations/ path is a real place to write, but nothing real is touched."""
    proofs = os.path.join(tmp, "somecomp", "proofs")
    os.makedirs(proofs, exist_ok=True)
    p = os.path.join(proofs, "test_thing.py")
    Path(p).write_text("# stand-in proof\n", encoding="utf-8")
    return p


def _sealable(proof: str) -> dict:
    """A real eight-field VALIDATION whose fingerprint describes THIS temp component.

    Without the re-fingerprint every seal here would be born expired — ``standing`` would
    refuse on a closed horizon before reaching whatever the tooth is actually asking about,
    which is a green (or a red) earned for the wrong reason."""
    real = TesterDevice().run_proof(_GREEN_FIXTURE, sink="none", isolation="none")
    return dict(real, evidence=dict(real["evidence"],
                                    source_fingerprint=vs.source_fingerprint(proof)))


def test_a_real_validation_round_trips_beside_its_proof():
    v = TesterDevice().run_proof(_GREEN_FIXTURE, sink="none", isolation="none")
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
        # AND NOTHING WAS ADDED ON THE WAY THROUGH. The door used to mint a `trail_link` into
        # evidence, so what came back was not what was handed in. It does not any more.
        assert stored["evidence"] == v["evidence"], (
            "the door must persist the caller's evidence unchanged — a door that decorates "
            "the record makes the returned dict and the stored one two different things")


def test_a_RERUN_REPLACES_the_standing_record():
    """THE INVERSION, and the ticket's whole subject. This tooth asserted the opposite until
    2026-08-16 (`a second seal APPENDS — the trail is a record of truth (Law 7)`), and it is
    left standing here in its new direction rather than deleted, so the reversal is visible in
    the file's own history instead of only in a charter.

    Akien's ruling is what turned it: *"the validation is a single record. so is the preceeding
    one. so a ticket should accumulate them? and all we need to keep of a proof is enough data
    to verify it. So do we need it's whole history? no, in fact it tends to create noise."*

    The shape is asserted as well as the length — the file stays a LIST holding one record,
    because every reader in the corpus opens it with ``[-1]`` and a bare dict would red them
    all at once."""
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        first = _sealable(proof)
        vs.persist_validation(first, proof_path=proof)
        second = dict(first, date="2030-01-01T00:00:00", claim="the re-run's claim")
        path = vs.persist_validation(second, proof_path=proof)

        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        assert isinstance(raw, list) and len(raw) == 1, (
            f"a re-run REPLACES — one record per proof, in a list: {raw}")
        assert raw[0]["claim"] == "the re-run's claim", "the survivor is the NEWEST seal"
        assert vs.read_validations(proof)[-1]["date"] == "2030-01-01T00:00:00"


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
        # and nothing landed — a refused write leaves nothing behind
        assert vs.read_validations(proof) == []


def test_evidence_that_is_not_a_STRUCTURE_is_refused():
    """`evidence` is where the fingerprint rides, and the fingerprint is the entire tamper
    story now that the chain is gone. A stringified blob has nowhere to carry it, so a record
    whose evidence is not a dict cannot be checked against the world at read time — it would
    stand green forever on a claim nothing could expire."""
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        blob = dict(_sealable(proof), evidence="a stringified blob")
        try:
            vs.persist_validation(blob, proof_path=proof)
        except ValueError as err:
            assert "structure, not a blob" in str(err), err
        else:
            raise AssertionError("evidence that cannot carry a fingerprint must be refused")
        assert vs.read_validations(proof) == [], "a refused write leaves nothing behind"


def test_the_NAIVE_overwrite_cannot_land_bytes():
    """THE ORIGINAL TICKET'S FALSIFIER, first half: 'a test that writes the validation file by
    a path OTHER than persist_validation and is NOT refused.'

    The lived symptom, verbatim from the trouble: a hand-write 'destroys a proof's whole seal
    history silently and permanently, and looks exactly like a fresh seal.' This is that
    hand-write — the plainest one, the one nobody meant to do — and it raises at the ``open``
    because the door left the file at 0444. This tooth is UNTOUCHED by the collapse: the mode
    bit protects one record exactly as it protected a trail."""
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        path = vs.persist_validation(_sealable(proof), proof_path=proof)
        assert oct(os.stat(path).st_mode & 0o777) == "0o444", oct(os.stat(path).st_mode)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([{"gotcha": True}], f)
        except PermissionError:
            pass
        else:
            raise AssertionError(
                "a second path landed bytes on the record — the gate is not physics")
        assert len(vs.read_validations(proof)) == 1, "the record must be untouched"


def test_the_FINGERPRINT_is_what_a_FORCED_write_cannot_fake_and_the_LIMIT_is_asserted_too():
    """THE HONEST REPLACEMENT for ``test_a_FORCED_write_cannot_pass_for_a_seal``, which
    claimed more than it measured.

    The old tooth chmod'd the file, wrote a plausible green over it WITHOUT a trail_link, and
    concluded that a hand-write cannot pass for a seal. It proved only that a hand-write
    lacking a link cannot — and the link was mintable by anyone who imported ``_link_for``.
    A tolerance is a forger's costume whenever the forger can produce the thing being
    tolerated, and that was one.

    So this measures BOTH ENDS, and the second is the point:

      (a) a forced write whose fingerprint does not describe the component REFUSES, and the
          refusal names the file, the two fingerprints and the remedy in one pass.
      (b) a forced write whose fingerprint DOES describe the component STANDS. That is the
          residue, and it is asserted rather than admitted in prose, so nobody can quietly
          re-acquire the old overclaim: the store cannot tell a correct hand-write from a
          seal, and what tells them apart is git, one directory up.
    """
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        v = _sealable(proof)
        path = vs.persist_validation(v, proof_path=proof)
        assert vs.standing(proof)["proven"], vs.standing(proof)["why"]

        # (a) the forger who does not do the work: a stale fingerprint.
        stale = dict(v, evidence=dict(v["evidence"], source_fingerprint="00" * 32))
        os.chmod(path, 0o644)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([stale], f)
        verdict = vs.standing(proof)
        assert verdict["proven"] is False, "a stale fingerprint must not clear"
        assert "HORIZON HAS CLOSED" in verdict["why"], verdict["why"]
        assert proof in verdict["why"], "the refusal must name what it read"
        assert "000000000000" in verdict["why"] and "re-run the proof" in verdict["why"].lower(), (
            f"one report, no second call: both fingerprints and the remedy: {verdict['why']}")

        # (b) THE LIMIT. A hand-write that gets the fingerprint right is indistinguishable
        # from a seal, and saying so out loud is the whole reason this half exists.
        os.chmod(path, 0o644)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([dict(v, claim="written by hand, not by the door")], f)
        stands = vs.standing(proof)
        assert stands["proven"] is True, (
            "if this ever reds, the store has grown a new tamper-detection layer and this "
            "tooth's docstring is stale — say what the new layer is, do not just flip the "
            "assertion")
        assert vs.read_validations(proof)[0]["claim"] == "written by hand, not by the door"


def test_standing_answers_all_FOUR_outcomes_and_says_which():
    """``standing`` is the reader that replaced MethodRegistry, and its one consumer turns a
    False straight into a refusal a human must act on — so every False names which of the
    reasons it was, in one pass (I-complete-diagnostic-on-first-pass).

    Four outcomes, and the fourth is the one the in-memory registry could not reach: a green
    seal whose fingerprint has moved is EXPIRED, because the code changed underneath it
    (Law 3). A cache holding a bool has no way to notice that."""
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)

        never = vs.standing(proof)
        assert never["proven"] is False and never["seal"] is None
        assert "no VALIDATION has ever sealed" in never["why"], never["why"]

        v = _sealable(proof)
        vs.persist_validation(dict(v, verdict="red"), proof_path=proof)
        red = vs.standing(proof)
        assert red["proven"] is False and "did not pass" in red["why"], red["why"]

        vs.persist_validation(v, proof_path=proof)
        assert vs.standing(proof)["proven"] is True, vs.standing(proof)["why"]

        # THE HORIZON: move the code, not the record. The seal is still green and still says
        # so; it is the world that changed.
        Path(tmp, "somecomp", "extra.py").write_text("# the code moved\n", encoding="utf-8")
        expired = vs.standing(proof)
        assert expired["proven"] is False, "a green seal over moved code is not green (Law 3)"
        assert expired["seal"]["verdict"] == "green", "the SEAL is untouched — the horizon closed"
        assert "HORIZON HAS CLOSED" in expired["why"], expired["why"]


def test_a_CHANGED_verdict_is_ANNOUNCED_before_the_replace_lands():
    """THE PERMISSION SLIP FOR THE WHOLE COLLAPSE, and the tooth that would have to red for
    the collapse to be illegal.

    Law 7 lets a presentation surface collapse an error into a coherent shape and never lets a
    record of truth do it. Replacing a record IS collapsing it. The only argument that survives
    is that the error gets LOUDER — so the loudness is a route to a surface, asserted here, not
    a sentence in a charter.

    BEFORE, not after: the announcement carries the OLD verdict, and the old record is about to
    stop existing in the working tree. Announcing afterwards would mean a crash between the two
    acts loses the change and the record together."""
    with tempfile.TemporaryDirectory() as tmp:
        troubles = os.path.join(tmp, "troubles")
        device = TroubleDevice(root=troubles)
        proof = _fake_proof(tmp)
        v = _sealable(proof)

        standing_trail = [dict(v, verdict="green", date="2026-08-01T00:00:00", caller="the-past")]
        incoming = dict(v, verdict="red", date="2026-08-16T00:00:00", caller="the-present")

        change = vs.verdict_change(standing_trail, incoming)
        assert change is not None, "green -> red is a change"
        assert change["from"] == "green" and change["to"] == "red"
        assert change["was_caller"] == "the-past" and change["now_caller"] == "the-present"

        vs.announce_verdict_change(vs.validations_path_for(proof), change, device=device)
        live = device.live()
        assert len(live) == 1, live
        why = live[0]["why"]
        for needed in ("'green'", "'red'", "2026-08-01T00:00:00", "the-past", "git"):
            assert needed in why, f"the announcement must carry {needed!r}: {why}"
        # THE DAMPING IS THE REASON THIS IS TroubleDevice AND NOT A NEW DOOR: a proof that
        # flaps for a week is ONE trouble whose count climbs, never a week of tickets.
        vs.announce_verdict_change(vs.validations_path_for(proof), change, device=device)
        vs.announce_verdict_change(vs.validations_path_for(proof), change, device=device)
        live = device.live()
        assert len(live) == 1 and live[0]["count"] == 3, (
            f"three flaps must be one trouble counted three times: {live}")


def test_an_AGREEING_rerun_announces_NOTHING():
    """The overwhelmingly common case, and the one that decides whether this door is usable at
    all: 52 of the 54 multi-record files measured on 2026-08-16 held nothing but re-runs
    agreeing with themselves. A door that announced those would raise a trouble on every
    green proof run in the corpus — the noise Akien's ruling was about, re-created in the
    place built to prevent it."""
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        v = _sealable(proof)
        assert vs.verdict_change([], v) is None, "a first seal changes nothing — there is no was"
        assert vs.verdict_change([v], dict(v, date="later")) is None, \
            "a re-run that agrees with itself is silence"
        assert vs.verdict_change(["not a record at all"], v) is None, \
            "an unreadable standing entry is not a verdict change — it is a different defect"


def test_the_announcement_fires_in_BOTH_directions():
    """A red going green destroys the red, and 'this was failing on <date> and passes now' is
    the same fact read from the other end. Firing only on green->red would make the store's
    memory asymmetric in exactly the direction that flatters the builder."""
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        v = _sealable(proof)
        recovering = vs.verdict_change([dict(v, verdict="red")], dict(v, verdict="green"))
        assert recovering is not None and recovering["from"] == "red" and recovering["to"] == "green"


def test_a_FAILING_announcement_does_not_lose_the_NEW_measurement():
    """THE ORDERING'S COST, asserted rather than hoped for. Announce-then-write means the
    write can be reached with the announcement already failed — and the disposition is that
    the seal lands anyway, because refusing would throw away the freshly proved fact to
    protect the superseded one, which is in git either way.

    The residue this tooth pins: the door cannot report its own silence. That is why the
    announcement is a durable trouble rather than a log line — the NEXT change announces, and
    the record on disk still shows the verdict that got there."""
    class Unreachable:
        def raise_trouble(self, *a, **k):
            raise OSError("the trouble store is unreachable")

    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        v = _sealable(proof)
        vs.persist_validation(dict(v, verdict="green"), proof_path=proof)
        # Force the announce path to be reached even though this is a tmpdir: call it directly,
        # the way persist_validation does, and assert the raise it would have to swallow.
        change = vs.verdict_change(vs.read_validations(proof), dict(v, verdict="red"))
        assert change is not None
        try:
            vs.announce_verdict_change(vs.validations_path_for(proof), change,
                                       device=Unreachable())
        except OSError:
            pass
        else:
            raise AssertionError("the injected device must actually fail — else this proves nothing")
        # ...and the door still seals, swallowing it.
        vs.persist_validation(dict(v, verdict="red"), proof_path=proof,
                              trouble_device=Unreachable())
        assert vs.read_validations(proof)[-1]["verdict"] == "red", (
            "an unreachable trouble store must not cost us the new measurement")


def test_a_FIXTURE_seal_under_the_TEMP_ROOT_announces_NOTHING():
    """Proofs and tester fixtures seal into tmpdirs by the dozen, and a verdict change inside a
    fixture is the fixture DOING ITS JOB. Announcing those would fill the trouble store with
    the noise of its own tests — the damped door's failure mode arriving by a different route.

    THE PREDICATE IS THE TEMP ROOT, NOT CLASS-SPACE, and the first draft had it the other way
    round. ``quorum.seal`` addresses human-proved concept-pieces that live in CairnCommons, so
    a class-space test would have silenced every review verdict that ever flipped — in the one
    half of this store that has no tester to catch it. This tooth exists at all because the
    narrower guard passed its own proofs and was still wrong.

    It is the reason every other tooth in this file can seal freely: it asserts that the
    default (uninjected) path is never taken for a temp address. Proved against the REAL
    TroubleDevice's real root, read before and after — an injected device here would be
    proving the injection, not the guard."""
    real_root = TroubleDevice()._root
    before = sorted(p.name for p in Path(real_root).glob("*.json")) if Path(real_root).exists() else []
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        v = _sealable(proof)
        vs.persist_validation(dict(v, verdict="green"), proof_path=proof)
        vs.persist_validation(dict(v, verdict="red"), proof_path=proof)   # a real change
        assert vs.read_validations(proof)[-1]["verdict"] == "red"
    after = sorted(p.name for p in Path(real_root).glob("*.json")) if Path(real_root).exists() else []
    assert before == after, (
        f"a tmpdir seal wrote into the real trouble store: {sorted(set(after) - set(before))}")


def test_NO_SECOND_WRITER_EXISTS_IN_THE_CORPUS():
    """The layer that keeps the mode bit honest over time: the mode bit acts at RUNTIME, on a
    bypass that already happened. This one refuses the bypass at BUILD time — a module that
    writes a validations/ path and is not the store itself reds the corpus on arrival.

    Censused by the SHAPE OF USE, not by an identifier: what is scanned for is an open/write
    aimed at a ``validations/`` address, however it is spelled. A scan keyed on a constant's
    NAME misses every instance that wrote the path inline as a literal."""
    repo = Path(__file__).resolve().parents[4]
    store = (repo / "cairn" / "devices" / "tester" / "validation_store.py").resolve()
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
        "a second writer to the validation record exists in the corpus — persist_validation is "
        "not the only path (Law 6):\n" + "\n".join(offenders))


def test_EVERY_VALIDATIONS_FILE_IN_THE_CORPUS_HOLDS_EXACTLY_ONE_RECORD():
    """THE CLAUSE-(3) CENSUS — the tooth that measures the WORLD rather than a fixture, over
    the exact property the collapse claims.

    ``persist_validation`` writes a one-element list, always. So a validations file holding two
    or more records is a write that did not come through this door — and unlike a hash link,
    that is not a number a bypassing hand can compute its way past: producing it requires doing
    the exact thing being watched for. This is strictly harder to fake than what it replaced.

    THE VACUOUS GREEN IS THE REAL RISK HERE, not the assertion: a corpus scan that passes
    because it found nothing looks identical to one that passed on the merits. So the
    population floor is asserted, and the check is first pointed at a known-bad fixture corpus
    and an empty one, and required to red on both."""
    repo = Path(__file__).resolve().parents[4]

    def multi_record(root: Path) -> tuple[list[str], int]:
        """-> (files holding more than one record, files read)."""
        bad, seen = [], 0
        for path in sorted(root.glob("**/validations/*.json")):
            if "__pycache__" in str(path):
                continue
            trail = vs.read_validations(path=str(path))
            if not trail:
                continue
            seen += 1
            if len(trail) > 1:
                bad.append(f"{path.relative_to(root)}: {len(trail)} records")
        return bad, seen

    # (1) A KNOWN-BAD FIXTURE CORPUS — the check must find the planted one and name it.
    with tempfile.TemporaryDirectory() as tmp:
        good_proof = _fake_proof(os.path.join(tmp, "good"))
        bad_proof = _fake_proof(os.path.join(tmp, "bad"))
        for p in (good_proof, bad_proof):
            vs.persist_validation(_sealable(p), proof_path=p)
        planted = vs.validations_path_for(bad_proof)
        record = vs.read_validations(bad_proof)[0]
        os.chmod(planted, 0o644)
        with open(planted, "w", encoding="utf-8") as f:
            json.dump([record, record], f)          # the shape the door cannot write

        found, seen = multi_record(Path(tmp))
        assert seen == 2, f"the fixture corpus should hold 2 files, read {seen}"
        assert len(found) == 1 and "bad/" in found[0], (
            f"the census must find the planted file and name it: {found}")

    # (2) AN EMPTY CORPUS MUST NOT PASS. A glob that matched nothing is not evidence that
    # everything holds one record — it is evidence the scan lost its population, and the two
    # look exactly alike from the outside.
    with tempfile.TemporaryDirectory() as tmp:
        _, seen = multi_record(Path(tmp))
        assert seen == 0, "sanity: an empty tree holds no validations files"
        try:
            assert seen >= _CORPUS_FLOOR
        except AssertionError:
            pass
        else:
            raise AssertionError("an empty corpus passed the population floor — vacuous green")

    # (3) THE REAL CORPUS.
    found, seen = multi_record(repo)
    assert seen >= _CORPUS_FLOOR, (
        f"only {seen} validations file(s) read in class-space — the census lost its "
        f"population, and a census that passes by finding nothing proves nothing")
    assert not found, (
        "a validations file in class-space holds more than one record — a shape "
        "persist_validation cannot produce, so something wrote around the door:\n  "
        + "\n  ".join(found))
    print(f"    ({seen} validations files; every one holds exactly one current record)")


def _main() -> int:
    # THE ROSTER IS DERIVED, NOT TYPED. It was a hand-maintained list, and the 2026-08-13
    # sweep walked straight into what that costs: two teeth were added and neither ran,
    # and the file printed the same triumphant line it prints when everything runs. A
    # check nobody listed is a check that did not run, which is the exact silence the
    # proof-record ruling names — so the list is now the module's own declaration order.
    checks = [v for k, v in globals().items()
              if k.startswith("test_") and callable(v)]
    assert len(checks) >= 13, (
        "the derived roster collapsed — teeth are being counted by a broken rule, and a "
        f"roster that shrinks silently is the defect it replaced: {len(checks)}")
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — validation_store: one current record beside its proof, drift refused, "
          "a changed verdict announced before the replace")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
