"""Proof for ticket 4431cf2bc625 — a seal MEASUREMENT is never replaced by the absence of one.

THE MEASURED FAILURE THIS EXISTS FOR. On 2026-09-08 a whole-corpus re-seal was fired bare
(`cairn test <dir> --seal`, no `--netns`). Forty-four validations that carried
`seal: {verdict: "sealed"}` came back carrying `seal: {verdict: "open", detail: "none: no
seal requested"}`, and nothing anywhere refused it. The store's door REPLACES rather than
appends (2026-08-16), so the sealed reading was not superseded by a newer reading of the
same question — it was superseded by a record saying nobody had asked the question. It was
caught by diffing one file by hand.

THE AXIS IS WHETHER ANYONE LOOKED, NOT HOW STRONG THE SEAL IS, and isolation.py's own
comments draw it: `open` is "not asked for; the route is open by construction, said so" —
the one verdict of the four that is the ABSENCE of a measurement. The other three are
measurements. So the teeth below assert a NARROW predicate and, just as deliberately,
assert what it must NOT refuse: `sealed -> breached` and `sealed -> indeterminate` have to
land, because a guard that blocked those would be protecting an old green from a new red,
which is Law 7 inverted at the exact door Law 7 most cares about.

AND THE MIRROR, BUILT 2026-09-10 (ticket 299d4f72ae40). The guard above left the opposite
direction open, and the asymmetry was the finding: the same door refused to retire a
MEASUREMENT without a written reason while letting a deliberate NON-measurement be retired
without one. `open` is a recorded choice not to ask — and one `cairn test --seal --netns` over
a proof standing at `open` converted it to `sealed`, silently, irreversibly, because the door
REPLACES. Measured at HEAD 57bd9cf on a fixture: rc 0, four lines of output, no mention of the
override, and the `open` unrecoverable. 54 of the 219 standing validations across both roots
were convertible by one such sweep. So `SealConversionRefused` mirrors `SealDowngradeRefused`
in shape, in raise site, and in its escape — and the teeth below assert BOTH predicates are
narrow, because two guards at one door is two chances to wall off the ordinary entrance.

Teeth a hollow build could not pass:

  1. A MEASUREMENT CANNOT BE REPLACED BY THE ABSENCE OF ONE. sealed -> open raises
     SealDowngradeRefused, and the file on disk still carries `sealed` afterwards — a
     refusal that had already written would not be a refusal.
  2. THE ESCAPE IS RECORDED, NOT AMBIENT. With `unsealing_because` the same write lands,
     and the reason rides permanently in the stored record's evidence. A gate whose escape
     leaves no trace is a gate that gets used and forgotten.
  3. THE GUARD DOES NOT BLOCK A NEW MEASUREMENT. sealed -> breached and sealed ->
     indeterminate both land untouched, and so does open -> sealed (the first seal of an
     unsealed proof, which is the ordinary sealing act).
  4. THE STANDING SEAL IS READABLE, AND ITS ISOLATION REPRODUCIBLE. standing_seal returns
     the verdict on disk, None when nothing stands (never `open` — "nothing stands" is not
     a fourth verdict), and isolation_for_seal maps it back to the isolation that would
     reproduce it.
  5. THE --seal SUMMARY COUNTS WHAT LANDED, NOT WHAT PASSED. Over a batch of one green and
     one red fixture, the printed persist count equals the number of validation files
     actually on disk. Until 2026-09-09 the line printed `total - reds` in the same breath
     as its own sentence "a red seals its red" — a record-of-truth command miscounting the
     records it had just written.

Self-cleaning: every tooth writes into a throwaway temp component tree, so no real
component's `validations/` is touched.

    python3 cairn/devices/tester/proofs/test_seal_is_never_silently_dropped.py   # exit 0 = green
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester import validation_store as vs
from cairn.devices.tester.device import TesterDevice
from cairn.devices.tester.isolation import BREACHED, INDETERMINATE, OPEN, SEALED
from cairn.tools.base import validation as public_validation

_FIXTURES = _REPO_ROOT / "cairn" / "devices" / "tester" / "proofs" / "fixtures"
_GREEN_FIXTURE = _FIXTURES / "green_proof.py"
_RED_FIXTURE = _FIXTURES / "red_proof.py"


def _fake_proof(tmp: str, stem: str = "test_thing") -> str:
    """A stand-in proof at <tmp>/somecomp/proofs/<stem>.py, with a real parent tree so the
    DERIVED validations/ path is a real place to write and nothing real is touched."""
    proofs = os.path.join(tmp, "somecomp", "proofs")
    os.makedirs(proofs, exist_ok=True)
    p = os.path.join(proofs, f"{stem}.py")
    Path(p).write_text("# stand-in proof\n", encoding="utf-8")
    return p


def _sealable(proof: str, verdict: str) -> dict:
    """A real eight-field VALIDATION carrying a named seal verdict, fingerprinted for THIS tree.

    Built from a genuine run rather than typed, so the record that meets the door is the
    shape the door actually receives in life; only the seal verdict and the fingerprint are
    substituted. Without the re-fingerprint the seal would be born expired and `standing`
    would refuse it on a closed horizon — a red earned for the wrong reason."""
    real = TesterDevice().run_proof(_GREEN_FIXTURE, sink="none", isolation="none")
    evidence = dict(real["evidence"],
                    seal=dict(real["evidence"]["seal"], verdict=verdict),
                    source_fingerprint=vs.source_fingerprint(proof))
    return dict(real, evidence=evidence)


def _standing_verdict(proof: str) -> str | None:
    """Read the seal verdict off disk DIRECTLY, not through the reader under test.

    A tooth that verifies standing_seal by asking standing_seal proves only that the
    function is consistent with itself."""
    trail = vs.read_validations(proof)
    return trail[-1]["evidence"]["seal"]["verdict"] if trail else None


def test_a_measured_seal_cannot_be_replaced_by_the_absence_of_one():
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        vs.persist_validation(_sealable(proof, SEALED), proof_path=proof)
        assert _standing_verdict(proof) == SEALED, "setup failed — nothing sealed stands"

        try:
            vs.persist_validation(_sealable(proof, OPEN), proof_path=proof)
        except vs.SealDowngradeRefused as refusal:
            # THE REFUSAL HAS TO BE ACTIONABLE, not merely raised. It names both verdicts
            # and both ways forward, because a refusal a caller cannot act on is a refusal
            # they learn to route around.
            text = str(refusal)
            assert SEALED in text and OPEN in text, f"the refusal names neither verdict: {text}"
            assert "unsealing_because" in text, f"the refusal hides its own escape: {text}"
        else:
            raise AssertionError(
                "sealed -> open landed. This door REPLACES, so it just retired a measurement "
                "and left nothing on disk saying one was ever taken (Law 3) — the exact "
                "2026-09-08 failure, 44 times over.")

        # AND NOTHING LANDED. The guard fires before the announce and before the write, so a
        # refused downgrade leaves the standing measurement exactly as it was.
        assert _standing_verdict(proof) == SEALED, (
            "the door refused and wrote anyway — the guard is downstream of the write")


def test_the_escape_is_recorded_permanently_not_ambient():
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        vs.persist_validation(_sealable(proof, SEALED), proof_path=proof)
        why = "the netns is unavailable on this host and the run is diagnostic"
        path = vs.persist_validation(_sealable(proof, OPEN), proof_path=proof,
                                     unsealing_because=why)

        assert _standing_verdict(proof) == OPEN, "the stated escape did not let the write land"
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        assert raw[-1]["evidence"]["unsealing_because"] == why, (
            "the reason did not ride into the record — an escape that leaves no trace on "
            f"disk is indistinguishable from no gate at all: {raw[-1]['evidence']}")

        # A BLANK REASON IS NOT A REASON. The field exists to make the choice legible; a
        # whitespace string would satisfy a truthiness check and legible nothing.
        #
        # THE RE-ARM CARRIES ITS OWN REASON, AND THAT IS NOT SCAFFOLDING. The standing record is
        # `open` at this point, so putting `sealed` back is a genuine conversion and meets the
        # MIRROR guard built on ticket 299d4f72ae40. Before that guard existed this line was
        # silent; the fact that it now has to say why it is converting is the ticket working on
        # its own proof file, which is the cheapest possible demonstration that the door sees
        # every caller.
        vs.persist_validation(_sealable(proof, SEALED), proof_path=proof,
                              converting_because="re-arming the fixture for the blank-reason "
                                                 "half of this tooth")
        try:
            vs.persist_validation(_sealable(proof, OPEN), proof_path=proof, unsealing_because="   ")
        except vs.SealDowngradeRefused:
            pass
        else:
            raise AssertionError("a whitespace reason passed for a stated one")


def test_the_guard_does_not_block_a_NEW_measurement():
    """THE HALF THAT IS EASY TO GET BACKWARDS. `breached` is a measured RED and
    `indeterminate` is CP1 — both are answers to "is there a route?", and a guard that
    refused them would be protecting a standing green from a newer, worse reading, which is
    Law 7 pointed the wrong way at the door Law 7 exists for."""
    for landing in (BREACHED, INDETERMINATE):
        with tempfile.TemporaryDirectory() as tmp:
            proof = _fake_proof(tmp)
            vs.persist_validation(_sealable(proof, SEALED), proof_path=proof)
            vs.persist_validation(_sealable(proof, landing), proof_path=proof)
            assert _standing_verdict(proof) == landing, (
                f"sealed -> {landing} was blocked; the guard is reading strength, not "
                "whether anyone looked")

    # AND THE ORDINARY SEALING ACT IS UNTOUCHED — which is `None` -> sealed, NOT `open` ->
    # sealed. This clause used to run `open` -> sealed under the words "the first real seal of
    # a proof that had never been asked", and the file's own fourth tooth already said that was
    # wrong: NOTHING STANDING IS NOT `open`. A proof that had never been asked has no record at
    # all. Corrected on ticket 299d4f72ae40, whose whole subject is that distinction; the
    # `open` -> measured half moved into its own tooth below, where it now refuses.
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        assert _standing_verdict(proof) is None, "the fixture was not a virgin tree"
        vs.persist_validation(_sealable(proof, SEALED), proof_path=proof)
        assert _standing_verdict(proof) == SEALED, (
            "a FIRST seal was blocked — nothing was standing, so neither guard had anything to "
            "protect, and walling off the ordinary entrance to proven-space is the one thing "
            "they must never do")


def test_the_standing_seal_is_readable_and_its_isolation_reproducible():
    """THE READER THAT DID NOT EXIST. Measured 2026-09-09: a grep for `["seal"]` /
    `.get("seal"` across cairn/, bin/ and skills/ returned sixteen lines, and not one of
    them opened a standing on-disk validation to ask what seal it carried. That absence is
    why one batch-wide flag could decide the isolation of every proof in the corpus."""
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)

        # NOTHING STANDING IS NOT `open`. `open` is a recorded answer ("asked for nothing,
        # and said so"); None is the absence of a record. Collapsing them would make an
        # unsealed proof indistinguishable from one measured unsealed — and the guard's
        # whole subject is that distinction.
        assert vs.standing_seal(proof) is None, "an unsealed proof must read None, not a verdict"
        assert vs.isolation_for_seal(None) is None

        vs.persist_validation(_sealable(proof, SEALED), proof_path=proof)
        assert vs.standing_seal(proof) == SEALED == _standing_verdict(proof)
        assert vs.isolation_for_seal(vs.standing_seal(proof)) == "netns", (
            "a sealed proof must re-run under the isolation that produced its seal")

        vs.persist_validation(_sealable(proof, OPEN), proof_path=proof,
                              unsealing_because="proving the reader, not the guard")
        assert vs.standing_seal(proof) == OPEN == _standing_verdict(proof)
        assert vs.isolation_for_seal(vs.standing_seal(proof)) == "none"

        # A measured failure still reproduces at the isolation it was measured under —
        # `breached` means the netns was asked for and did not hold, so re-running bare
        # would answer a different question. The standing record is `open` here, so landing a
        # measured reading over it is a conversion and carries its reason (ticket
        # 299d4f72ae40); this tooth is about the READER, and the reason keeps it about that.
        vs.persist_validation(_sealable(proof, BREACHED), proof_path=proof,
                              converting_because="posing a measured failure to prove the "
                                                 "reader maps it back to netns")
        assert vs.isolation_for_seal(vs.standing_seal(proof)) == "netns"


def test_the_seal_summary_counts_what_LANDED_not_what_passed():
    """Over a real batch through the real CLI: one green fixture, one red. Both are
    persisted — the command's own sentence says so ("a red seals its red; Law 7") — and
    until 2026-09-09 the count printed beside that sentence omitted the reds. Measured that
    day over the corpus: 49 proofs, 6 red, the line said 43, and all 49 files were on disk.

    The assertion is an INVARIANT (printed count == files on disk), never the number 2, so
    it keeps biting if the fixture batch grows."""
    from cairn.devices.tester import cli

    with tempfile.TemporaryDirectory() as tmp:
        proofs_dir = Path(tmp) / "somecomp" / "proofs"
        proofs_dir.mkdir(parents=True)
        for fixture in (_GREEN_FIXTURE, _RED_FIXTURE):
            (proofs_dir / f"test_{fixture.stem}.py").write_text(
                fixture.read_text(encoding="utf-8"), encoding="utf-8")

        out = io.StringIO()
        with redirect_stdout(out):
            cli.main([str(proofs_dir), "--seal"])
        text = out.getvalue()

        landed = sorted((Path(tmp) / "somecomp" / "validations").glob("*.json"))
        assert len(landed) == 2, f"the batch did not seal both fixtures: {landed}\n{text}"

        line = [ln for ln in text.splitlines() if "VALIDATION(s) persisted" in ln]
        assert len(line) == 1, f"no persist count on the summary:\n{text}"
        claimed = int(line[0].split("—")[1].split()[0])
        assert claimed == len(landed), (
            f"the command says it persisted {claimed} VALIDATION(s) and {len(landed)} are on "
            f"disk — a record-of-truth surface miscounting its own records (Law 7):\n{text}")

        # AND THE RED WAS ONE OF THEM, which is the specific omission the old count made.
        reds = [p for p in landed
                if json.loads(p.read_text(encoding="utf-8"))[-1]["verdict"] != "green"]
        assert len(reds) == 1, f"the red fixture did not seal its red: {[p.name for p in landed]}"


# ─── THE MIRROR (ticket 299d4f72ae40) ────────────────────────────────────────────────────────

def test_a_recorded_choice_not_to_measure_is_not_silently_converted():
    """`open` -> sealed RAISES, and the file on disk is byte-identical afterwards.

    THE BYTES, NOT THE VERDICT. Asserting the standing verdict is still `open` would pass for
    a door that wrote and then rolled back, or one that rewrote the record with the same
    verdict and a new timestamp. The claim is that nothing landed at all — which is what makes
    it a refusal rather than an undo — so the tooth compares the file's bytes.
    """
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        vs.persist_validation(_sealable(proof, OPEN), proof_path=proof)
        before = Path(vs.validations_path_for(proof)).read_bytes()

        raised = None
        try:
            vs.persist_validation(_sealable(proof, SEALED), proof_path=proof)
        except vs.SealConversionRefused as refusal:
            raised = refusal
        assert raised is not None, (
            "open -> sealed landed unannounced — a recorded choice not to measure was retired "
            "by a measurement, and nothing on disk says the choice was ever made")
        assert OPEN in str(raised) and SEALED in str(raised), (
            f"the refusal names neither reading, so it cannot be acted on: {raised}")
        assert Path(vs.validations_path_for(proof)).read_bytes() == before, (
            "the refusal wrote anyway — a door that refuses after writing is not a door")


def test_the_conversion_escape_is_recorded_permanently_not_ambient():
    """With a reason the conversion LANDS, the reason rides inside the surviving record, and
    the evidence already there survives it.

    INSIDE, NOT BESIDE, AND THE REASON IS STRUCTURAL: this door replaces, so there is no
    superseded record left to carry one. Measured 2026-09-10 across both roots: all 219
    validation files hold exactly one record, and `_atomic_write(path, [record])` is why.
    """
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        vs.persist_validation(_sealable(proof, OPEN), proof_path=proof)
        landing = _sealable(proof, SEALED)
        vs.persist_validation(landing, proof_path=proof,
                              converting_because="the proof was always meant to be sealed")
        assert _standing_verdict(proof) == SEALED, "the stated reason did not open the gate"

        stored = vs.read_validations(proof)[-1]["evidence"]
        assert stored.get("converting_because") == (
            "the proof was always meant to be sealed"), (
            f"the reason did not ride into the record: {sorted(stored)}")
        # AND IT DISPLACED NOTHING. The escape merges into evidence; a write that replaced the
        # dict would drop source_fingerprint and silently un-expire the seal.
        for key in landing["evidence"]:
            assert key in stored, f"the escape dropped evidence key {key!r} on its way in"


def test_both_guards_are_narrow_and_neither_walls_the_ordinary_door():
    """THE THREE TRANSITIONS THAT MUST STILL LAND, run against the mirror rather than its
    sibling: `open` -> `open` (a re-run reproducing the standing choice — the ordinary path,
    and the one `cairn test --seal` takes on every commit), `sealed` -> `sealed`, and
    `None` -> `open` (a first record that honestly asked for nothing).

    A guard testing `was != now` instead of the two named verdicts would pass every tooth
    above and red the whole pre-commit ladder on the next commit. This is the tooth that
    catches it.
    """
    for standing, landing in ((OPEN, OPEN), (SEALED, SEALED)):
        with tempfile.TemporaryDirectory() as tmp:
            proof = _fake_proof(tmp)
            vs.persist_validation(_sealable(proof, standing), proof_path=proof)
            vs.persist_validation(_sealable(proof, landing), proof_path=proof)
            assert _standing_verdict(proof) == landing, (
                f"{standing} -> {landing} was blocked; a guard reading 'anything changed' has "
                "replaced one reading 'a choice was retired'")

    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        vs.persist_validation(_sealable(proof, OPEN), proof_path=proof)
        assert _standing_verdict(proof) == OPEN, (
            "a first record carrying `open` was refused — nothing was standing, so there was "
            "no choice to retire")


def test_the_guard_covers_every_persisting_caller_not_only_the_flag():
    """THE GUARD IS AT THE DOOR, NOT AT THE FLAG, and this is the tooth that says so in
    behaviour rather than in a comment.

    TWO READINGS, AND THE SECOND IS THE HONEST SHAPE OF THE FIRST. `cairn/tools/base/validation.py`'s
    public `run_proof` persists with `sink="validations"` and NEVER forwards isolation — measured
    2026-09-10 at its own signature, which takes no isolation argument at all. So today it can
    only ever mint an `open` reading, and it cannot itself perform a conversion. What it CAN do
    is meet the door: reading 1 fires the sibling guard through it, proving the wrapper passes
    through `persist_validation` with no escape kwarg of its own. Reading 2 then fires the
    conversion guard through the exact call shape `device.py` uses when that wrapper seals —
    `persist_validation(record, proof_path=...)`, positional record, no reason — so the two
    together say: any caller reaching this door meets both guards, whichever direction it moves.

    A fix bolted to `--netns` would have passed neither reading, and that is the latent miss
    this placement was chosen against.
    """
    # READING 1: the wrapper reaches the guarded door with no escape of its own. The fixture is
    # COPIED into the temp tree first, so the wrapper's real persist lands there and no real
    # component's validations/ is touched — this file's self-cleaning promise holds.
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        Path(proof).write_text(_GREEN_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
        vs.persist_validation(_sealable(proof, SEALED), proof_path=proof)

        raised = None
        try:
            public_validation.run_proof(proof, sink="validations", caller="the coverage tooth")
        except vs.SealDowngradeRefused as refusal:
            raised = refusal
        assert raised is not None, (
            "the public wrapper sealed without meeting the door's guards. It forwards no "
            "isolation, so its run reads `open`; landing that over a standing `sealed` is "
            "exactly what SealDowngradeRefused exists to refuse, and a caller that walks past "
            "it is a caller a CLI-bolted fix would never have covered")
        assert _standing_verdict(proof) == SEALED, "the refusal wrote anyway"

    # READING 2: the conversion guard fires through the exact call shape device.py uses.
    with tempfile.TemporaryDirectory() as tmp:
        proof = _fake_proof(tmp)
        vs.persist_validation(_sealable(proof, OPEN), proof_path=proof)
        raised = None
        try:
            # device.py:604 verbatim in shape: positional record, proof_path only, no reason.
            vs.persist_validation(_sealable(proof, SEALED), proof_path=proof)
        except vs.SealConversionRefused as refusal:
            raised = refusal
        assert raised is not None, (
            "a caller that names no reason walked the conversion through — the guard is "
            "reading something the CLI supplies, not something the door sees")


def test_the_watchme_probe_is_armed_and_can_be_made_to_fire():
    """THE PROBE EXISTS AT THE BERTH THE TICKET NAMES, declares a frozen module-level PROBE
    with both a carry and an enough, and its reading FIRES when handed the pre-build answer.

    A probe nobody has watched fire is a probe nobody has measured. The sibling probe's own
    pattern: the reading takes its predicate as an argument so a tooth can substitute one.
    """
    from cairn.devices.tester.probes import an_open_reading_is_not_silently_converted as probe

    assert callable(probe.PROBE.carry) and callable(probe.PROBE.enough), (
        "the probe carries no carry or no enough, and the emission gate reads both")

    # THE PRE-BUILD WORLD: a door that let the conversion through.
    fired = probe.conversion_reading(refuses=lambda was, now: False)
    assert fired["fires"], "the probe cannot be made to fire, so its quiet means nothing"
    # AND THE WORLD AS BUILT.
    live = probe.conversion_reading()
    assert not live["fires"], f"the probe fires against the built guard: {live['what']}"


def _main() -> int:
    # The roster is DERIVED from declaration order, never typed — a hand-kept list is a list
    # a new tooth can be left off, and the file prints the same triumphant line either way.
    checks = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    assert len(checks) >= 10, (
        "the derived roster collapsed — five teeth for ticket 4431cf2bc625 and five for its "
        f"mirror 299d4f72ae40, and the roster found {len(checks)}")
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — a measured seal is never replaced by an unrequested one, the escape is on "
          "the record, and the summary counts what landed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
