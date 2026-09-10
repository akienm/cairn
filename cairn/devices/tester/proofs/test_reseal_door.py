"""The reseal door's teeth — ticket 4d9115eb04cd, a-seal-that-cannot-be-reproven-rides-the-ruled-ladder.

WHAT IS BEING PROVED, in the ticket's own frame: a green seal that stops reproducing is
RED at rung 1, is repaired at rung 2 under a bound, becomes ATTENTION at rung 3 when the
repair does not come, and only Akien's ruling reopens the design at rung 4. The five teeth
below are the ticket's five `proves_red` clauses, one function each, plus the WRONG INTENT
clause held as its own tooth because a clause nothing can fail is decoration.

EVERY TOOTH RUNS OVER A SCRATCH COMPONENT, NEVER THE LIVE TREE. The door's whole job is to
land seals and raise troubles, so a tooth pointed at a real proof would be a proof writing
into the store every later measurement is read from — the failure
`a-proof-cannot-seed-the-tree-it-reads` exists to stop. `scratch_dir` gives a component
root the process sweeps on exit, and `persist_validation` already suppresses its announce
and clear for addresses under the system temp directory, so the fixture's deliberate
verdict flips do not fill the trouble store with the noise of their own tests.

THE TESTER IS FAKED IN FIVE OF THE SIX. What is under test is the DISPOSAL of a run's
verdict — which rung fires, what gets bound, what is written, what is raised — and a real
subprocess run would buy nothing but seconds while making the red half hard to stage. The
one thing a fake could hide is that the door never runs anything at all, and that is
exactly what the sixth tooth measures: a tester whose `run_proof` explodes must leave the
validations file byte-identical, because a seal written without a run in the same act is
the ticket's WRONG INTENT.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.device import GREEN, RED  # noqa: E402
from cairn.devices.tester.reseal import (  # noqa: E402
    ResealRefused, proof_sha256, read_ladder, reseal, ruling_refusal, trouble_identity,
)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
from cairn.devices.tester.validation_store import (  # noqa: E402
    persist_validation, read_validations, source_fingerprint, standing, validations_path_for,
)
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "4d9115eb04cd": {
        "1": "test_a_component_whose_source_moved_reads_red_with_no_human_act",
        "2": "test_a_repair_leaving_the_proof_hash_alone_reseals_green_and_closes_the_ladder",
        "3": "test_a_moved_proof_is_refused_without_a_ruling_and_accepted_with_a_confirmed_one",
        "4": "test_an_unrepaired_red_is_one_trouble_carrying_the_tail_and_it_clears_on_the_green",
        "5": "test_no_pulse_path_reaches_the_door",
        "6": "test_no_rung_writes_a_seal_without_a_run_in_the_same_act",
        "7": "test_a_timeout_writes_no_seal_and_bounds_no_repair",
        "8": "test_a_settled_red_costs_no_run_and_keeps_its_trouble_standing",
    }
}

# A REAL, CONFIRMED RULING — the one this ticket was cast under. Rung 4 leans on the
# `confirmed` flag the intake door DERIVES from Akien's own RULED marker, so a tooth that
# invented a ruling id would be proving the door against a fixture of its own authorship.
_RULING = "2026-09-06-a-seal-that-cannot-be-reproven-is-red-then-repaired-then-a-trouble-then-design"


# ── the fixture ───────────────────────────────────────────────────────────────────────

def _component(prefix: str = "cairn-resealproof-") -> tuple[Path, Path]:
    """A scratch component: `<tmp>/widget/{code.py, proofs/test_widget.py}`. Returns both."""
    root = scratch_dir(prefix) / "widget"
    (root / "proofs").mkdir(parents=True)
    (root / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    proof = root / "proofs" / "test_widget.py"
    proof.write_text("assert 2 == 2\n", encoding="utf-8")
    return root, proof


def _record(proof: Path, verdict: str, *, evidence=None) -> dict:
    """The ratified eight fields, with a fingerprint taken over the tree AS IT IS NOW.

    Taken at call time on purpose: a fake tester's record must carry the post-repair
    fingerprint for the same reason the real runner takes it around the run — a seal whose
    fingerprint predates the code it sealed cannot be reproduced by anyone, including the
    door that wrote it."""
    ev = {"source_fingerprint": source_fingerprint(str(proof)),
          "returncode": 0 if verdict == GREEN else 1}
    ev.update(evidence or {})
    return {
        "claim": f"{proof.name} passes",
        "caller": "test_reseal_door fixture",
        "date": datetime.now().isoformat(timespec="seconds"),
        "method": "ran the proof as a subprocess and read its exit code",
        "verdict": verdict,
        "evidence": ev,
        "falsifier": "the proof exits non-zero, or the fingerprint of the code it proves moves",
        "horizon": "valid until the proof file or the code it proves changes",
    }


class _FakeTester:
    """Returns a verdict the tooth chose, and COUNTS the runs. The count is the tooth's
    handle on the WRONG INTENT clause: every seal must have exactly one run behind it."""

    def __init__(self, verdict: str, *, tail: str = ""):
        self.verdict, self.tail, self.runs, self.callers = verdict, tail, 0, []

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none"):
        self.runs += 1
        self.callers.append(caller)
        assert sink == "none", f"the door must dispose of the record itself, not sink={sink!r}"
        return _record(Path(proof_path), self.verdict,
                       evidence={"stderr_tail": self.tail} if self.tail else None)


class _TimingOut:
    """What `TesterDevice.run_proof` returns when the subject is killed: RED, no returncode,
    and the runner's own wording. Copied from the runner rather than invented, because a
    tooth that made up the shape would prove the door against a fixture of its own design."""

    def __init__(self, timeout: int = 120):
        self.timeout, self.runs = timeout, 0

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none"):
        self.runs += 1
        return _record(Path(proof_path), RED, evidence={
            "returncode": None, "stdout_tail": "",
            "stderr_tail": f"timed out after {timeout}s",
            "teeth_green": [], "teeth_red": []})


class _Exploding:
    def run_proof(self, proof_path, **kw):
        raise RuntimeError("fixture: the run dies, deliberately")


class _FakeRaiser:
    """Records what the door raised and cleared. Injected rather than let the real
    ModuleRaiser write, because a proof that files troubles into the live store is a proof
    seeding the tree it reads."""

    def __init__(self):
        self.raised, self.cleared = [], []

    def raise_trouble(self, identity, *, why, detail=None):
        self.raised.append({"identity": identity, "why": why, "detail": detail or {}})

    def clear_trouble(self, identity, *, by, what_changed):
        self.cleared.append({"identity": identity, "by": by, "what_changed": what_changed})


# ── tooth 1 ───────────────────────────────────────────────────────────────────────────

def test_a_component_whose_source_moved_reads_red_with_no_human_act():
    """RUNG 1. Nobody declares the red; the fingerprint stops reproducing and the reader
    derives it. The tooth asserts the DERIVATION, not a message: `standing()` flips from
    proven to not-proven with nothing between the two calls but an edit to a source file
    the proof's seal covers — and it stays not-proven when the door asks."""
    root, proof = _component()
    persist_validation(_record(proof, GREEN), proof_path=str(proof))

    before = standing(str(proof))
    assert before["proven"] is True, before["why"]

    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")

    after = standing(str(proof))
    assert after["proven"] is False, "the source moved and the seal still read green"
    assert "fingerprint" in after["why"].lower(), after["why"]
    # And the door agrees: it does not short-circuit on a seal whose horizon has closed.
    fake = _FakeTester(GREEN)
    out = reseal(proof, tester=fake, raiser=_FakeRaiser())
    assert out["ran"] is True and fake.runs == 1, out


# ── tooth 2 ───────────────────────────────────────────────────────────────────────────

def test_a_repair_leaving_the_proof_hash_alone_reseals_green_and_closes_the_ladder():
    """RUNG 2. The repair moves the CODE and leaves the PROOF's bytes alone, which is the
    bound rung 2 permits. The seal comes back green through the store's door and the ladder
    is closed on the record — closed, not deleted: the record of the repair is provenance,
    and a ladder that vanished on success would leave nothing saying it had ever been
    climbed."""
    root, proof = _component()
    bound = proof_sha256(proof)
    persist_validation(_record(proof, RED, evidence={"reseal_ladder": {
        "proof_sha256": bound, "opened": "2026-09-09T09:00:00", "last_red": "2026-09-09T09:00:00",
        "passes": 1, "rung": 3, "trouble": trouble_identity(proof), "ruling": None}}),
        proof_path=str(proof))
    assert read_ladder(proof) is not None

    (root / "code.py").write_text("VALUE = 2  # repaired\n", encoding="utf-8")
    assert proof_sha256(proof) == bound, "the fixture moved the proof; that is tooth 3's case"

    raiser = _FakeRaiser()
    out = reseal(proof, tester=_FakeTester(GREEN), raiser=raiser)

    assert out["outcome"] == "resealed" and out["rung"] == 2 and out["ladder_closed"] is True, out
    assert out.get("ruling") is None, "rung 2 is the UNruled repair — a ruling here is rung 4"

    seal = read_validations(str(proof))[-1]
    assert seal["verdict"] == GREEN, seal
    closed = seal["evidence"]["reseal_closed"]
    assert closed["proof_sha256"] == bound and closed["closed_proof_sha256"] == bound, closed
    assert closed["opened"] == "2026-09-09T09:00:00", "the ladder's opening is provenance, not now"
    assert "reseal_ladder" not in seal["evidence"], "a closed ladder is not still open"
    assert read_ladder(proof) is None, "a green seal closes the ladder by definition"
    assert standing(str(proof))["proven"] is True, standing(str(proof))["why"]

    # THE DEFAULT MUST NEVER SKIP. A red that a hand explicitly asks about has to run, or an
    # environmental red — the database was down, and came back — is pinned red with no key,
    # because coming back moves no bytes. The flag is the difference between the hook's
    # automatic sweep and somebody typing the proof's name, and if it ever stopped being the
    # difference this assertion is the only thing that would say so.
    root3, proof3 = _component()
    persist_validation(_record(proof3, RED), proof_path=str(proof3))
    asked = _FakeTester(GREEN)
    out3 = reseal(proof3, tester=asked, raiser=_FakeRaiser())
    assert asked.runs == 1, (
        "a hand named a settled-red proof and the door skipped it anyway — an environmental "
        "red now has no way back to green short of editing code that was never wrong")
    assert out3["outcome"] == "resealed", out3
    assert [c["identity"] for c in raiser.cleared] == [trouble_identity(proof)], raiser.cleared


# ── tooth 3 ───────────────────────────────────────────────────────────────────────────

def test_a_moved_proof_is_refused_without_a_ruling_and_accepted_with_a_confirmed_one():
    """RUNGS 3→4. Once the proof file's own bytes move, the act stops being a repair and
    becomes 'the claim no longer matches the spec' — Akien's, and nobody else's.

    THE REFUSAL NAMES BOTH HASHES, which the ticket asks for by name: a refusal saying only
    'the proof changed' makes the reader re-derive two numbers by hand at the one moment
    they are already stuck. And an UNCONFIRMED ruling is refused exactly like a missing
    one — `confirmed` is derived from Akien's RULED marker, so leaning on the id alone
    would let CC's reading of a ruling open his gate."""
    root, proof = _component()
    bound = proof_sha256(proof)
    persist_validation(_record(proof, RED, evidence={"reseal_ladder": {
        "proof_sha256": bound, "opened": "2026-09-09T09:00:00", "last_red": "2026-09-09T09:00:00",
        "passes": 1, "rung": 3, "trouble": trouble_identity(proof), "ruling": None}}),
        proof_path=str(proof))

    proof.write_text("assert 3 == 3   # the claim itself moved\n", encoding="utf-8")
    moved = proof_sha256(proof)
    assert moved != bound

    fake = _FakeTester(GREEN)
    try:
        reseal(proof, tester=fake, raiser=_FakeRaiser())
        raise AssertionError("a moved proof resealed with no ruling — rung 4 did not fire")
    except ResealRefused as refusal:
        text = str(refusal)
    assert bound in text and moved in text, "the refusal must name BOTH hashes verbatim"
    assert fake.runs == 0, "the refusal must come BEFORE the run — a discarded run is a run wasted"

    # An id that resolves to nothing, and one that resolves to an UNCONFIRMED ruling, both refuse.
    assert ruling_refusal("") is not None
    assert ruling_refusal("2026-01-01-there-is-no-such-ruling") is not None
    assert ruling_refusal(_RULING) is None, "the ticket's own ruling must read confirmed"

    raiser = _FakeRaiser()
    out = reseal(proof, ruling_id=_RULING, tester=_FakeTester(GREEN), raiser=raiser)
    assert out["outcome"] == "resealed" and out["rung"] == 4, out
    seal = read_validations(str(proof))[-1]
    assert seal["evidence"]["reseal_ruling"] == _RULING, seal["evidence"]
    assert seal["evidence"]["reseal_closed"]["closed_proof_sha256"] == moved, seal["evidence"]


# ── tooth 4 ───────────────────────────────────────────────────────────────────────────

def test_an_unrepaired_red_is_one_trouble_carrying_the_tail_and_it_clears_on_the_green():
    """RUNG 3. A red nobody repairs must become ATTENTION — and exactly one piece of it.

    ONE IDENTITY ACROSS EVERY FAILING PASS is the whole point: per-pass identities are
    per-pass first-sightings, and every first sighting notifies. The bound must not move
    either — carrying today's hash forward on each red would re-bound the repair to
    whatever the proof happens to say on the pass that failed, which is a bound moving with
    the thing it bounds, i.e. none."""
    root, proof = _component()
    bound = proof_sha256(proof)
    persist_validation(_record(proof, GREEN), proof_path=str(proof))
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")

    raiser = _FakeRaiser()
    tail = "AssertionError: fixture: VALUE is 3, not 2"
    first = reseal(proof, tester=_FakeTester(RED, tail=tail), raiser=raiser)
    second = reseal(proof, tester=_FakeTester(RED, tail=tail), raiser=raiser)

    identity = trouble_identity(proof)
    assert first["outcome"] == second["outcome"] == "red"
    assert first["rung"] == second["rung"] == 3
    assert {r["identity"] for r in raiser.raised} == {identity}, raiser.raised
    assert len(raiser.raised) == 2, "both passes raise; the DAMPER folds them, not the door"
    assert raiser.raised[0]["detail"]["stderr_tail"] == tail, raiser.raised[0]["detail"]
    assert raiser.raised[0]["detail"]["rung"] == 3

    ladder = read_ladder(proof)
    assert ladder["proof_sha256"] == bound, ladder
    assert ladder["passes"] == 2, ladder
    assert ladder["last_red"] >= ladder["opened"]
    assert standing(str(proof))["proven"] is False

    # `opened` IS PROVENANCE AND MUST SURVIVE EVERY LATER PASS. Measured against a value
    # the fixture chose, not against one the door minted a moment ago: the timestamps have
    # second resolution, so two passes inside one second compare equal and a door re-taking
    # `_now()` on every red would pass a tooth written the obvious way (mutation D, hollow,
    # 2026-09-09). Backdating the standing ladder makes the two answers unmistakable.
    OPENED = "2026-09-09T09:00:00"
    backdated = {**ladder, "opened": OPENED}
    persist_validation(_record(proof, RED, evidence={"reseal_ladder": backdated}),
                       proof_path=str(proof))
    third = reseal(proof, tester=_FakeTester(RED, tail=tail), raiser=raiser)
    assert third["outcome"] == "red", third
    assert read_ladder(proof)["opened"] == OPENED, (
        "the ladder's opening moved — a trouble that keeps re-dating itself has no age, and "
        "age is the only thing that says a red has been standing untouched for a week")
    ladder = read_ladder(proof)

    # AND THE CARRY-FORWARD IS ONLY OBSERVABLE THROUGH A RULING. Rung 4 refuses every
    # unruled pass whose proof moved, so on the unruled path the carried hash and today's
    # hash are the same number by construction — a mutation swapping them survived every
    # tooth (2026-09-09). What CAN be told apart is the ruled path: Akien rules the claim
    # may change, the changed proof still fails, and the ladder must RE-BASE to the new
    # bytes. If it carried the old hash forward instead, his ruling would buy exactly one
    # pass and the pass after it would refuse over a change he had already ruled on.
    proof.write_text("assert 3 == 3   # ruled: the claim moved\n", encoding="utf-8")
    rebased = proof_sha256(proof)
    assert rebased != bound
    ruled = reseal(proof, ruling_id=_RULING, tester=_FakeTester(RED, tail=tail), raiser=raiser)
    assert ruled["outcome"] == "red", ruled
    after = read_ladder(proof)
    assert after["proof_sha256"] == rebased, (
        "a ruled proof change did not re-base the ladder — the next unruled pass will refuse "
        "over a change Akien has already ruled on")
    assert after["opened"] == OPENED, (
        "the ruling re-based WHEN the trouble started; it may only re-base what the repair "
        "is bounded to")
    assert after["ruling"] == _RULING, after
    # ...and the proof of it: the very next pass needs no ruling at all.
    again = reseal(proof, tester=_FakeTester(RED, tail=tail), raiser=raiser)
    assert again["outcome"] == "red", again

    proof.write_text("assert 2 == 2\n", encoding="utf-8")
    persist_validation(_record(proof, RED, evidence={"reseal_ladder": {
        "proof_sha256": proof_sha256(proof), "opened": ladder["opened"],
        "last_red": ladder["opened"], "passes": 4, "rung": 3,
        "trouble": trouble_identity(proof), "ruling": None}}), proof_path=str(proof))

    # The repair lands, the door reseals, and the SAME identity clears. A trouble that
    # outlived its cause is a diagnostic surface lying about the world (Law 7).
    (root / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    out = reseal(proof, tester=_FakeTester(GREEN), raiser=raiser)
    assert out["outcome"] == "resealed", out
    assert [c["identity"] for c in raiser.cleared] == [identity], raiser.cleared
    assert read_ladder(proof) is None
    assert standing(str(proof))["proven"] is True


# ── tooth 5 ───────────────────────────────────────────────────────────────────────────

def _code_without_prose(path: Path) -> str:
    """The file's code with its comments and docstrings taken off.

    A mention of a door is not a reach for it. Comments vanish because ``ast.parse``
    never keeps them; docstrings are popped by hand because they are ordinary string
    expressions and would survive the round trip. Everything else survives — including
    string literals in live positions, which is where a dynamic import would hide."""
    import ast

    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text  # unparseable: measure it whole rather than measure nothing
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)) or not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            body.pop(0)
            if not body:
                body.append(ast.Pass())
    return ast.unparse(tree)


def test_no_pulse_path_reaches_the_door():
    """The ticket's third constraint, as a grep: *fired from pre-commit over staged files;
    never from any on_pulse path.* The door runs proofs — minutes of subprocess — and the
    beat already spends 23.5 of every 23.7 seconds re-walking corpora that did not move. A
    reseal sweep on the beat would not be slow, it would be a machine that never finishes
    one pulse before the next.

    Measured over shims, probes and the ground loop rather than over a list of files a
    future caller could sidestep: those three ARE the pulse surface.

    AND IT IS MEASURED OVER THE CODE, NOT OVER THE PROSE (2026-09-09, ticket
    1accdc1781aa). Until today the tooth grepped the raw file text, so the first shim to
    merely *explain* the door in a docstring redded it — measured when codemother's new
    ``sealed`` handler wrote the word "resealed" in a sentence about why it reads only the
    LATEST crossing. A tooth that reds a comment is not measuring its own claim: the claim
    is that a pulse path REACHES the door, and a paragraph reaches nothing. So comments and
    docstrings come off first and the grep runs over what is left, which still catches a
    dynamic reach — ``ast.unparse`` keeps every string literal that is not a docstring, so
    ``import_module("...reseal...")`` is as visible as an ``import``. The narrowing is not a
    weakening in the direction that matters: an unparseable file is measured WHOLE."""
    surfaces = []
    surfaces += sorted((_REPO_ROOT / "cairn").rglob("shim.py"))
    surfaces += [p for p in sorted((_REPO_ROOT / "cairn").rglob("probes/*.py"))]
    surfaces += sorted((_REPO_ROOT / "cairn" / "devices" / "cairn" / "machines"
                        / "ground_loop").rglob("*.py"))
    assert surfaces, "the grep found no pulse surfaces at all — the tooth measured nothing"

    offenders = []
    for path in surfaces:
        if "reseal" in _code_without_prose(path):
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert not offenders, (
        f"the reseal door is named on a pulse path: {offenders}. It runs proofs; the beat "
        f"cannot afford it, and the ticket bounds it to pre-commit and a direct call.")


# ── tooth 6 — the WRONG INTENT clause ─────────────────────────────────────────────────

def test_no_rung_writes_a_seal_without_a_run_in_the_same_act():
    """THE WRONG INTENT CLAUSE, as a tooth: *the door writes a seal for a proof it did not
    just run, or a rung restores green without a run.*

    Two halves, because the clause has two. FIRST: a run that dies leaves the validations
    file byte-identical — no partial seal, no optimistic green. SECOND: rung 1 short-
    circuits on a still-standing seal and writes NOTHING, which is the case where a door
    that 'refreshed' the record would be minting a seal from a run that never happened."""
    root, proof = _component()
    persist_validation(_record(proof, GREEN), proof_path=str(proof))
    store = Path(validations_path_for(str(proof)))
    before = store.read_bytes()

    # SECOND HALF FIRST: nothing standing to re-run, so nothing written and nothing run.
    fake = _FakeTester(GREEN)
    out = reseal(proof, tester=fake, raiser=_FakeRaiser())
    assert out["outcome"] == "unchanged" and out["ran"] is False and out["rung"] == 1, out
    assert fake.runs == 0, "rung 1 ran a proof it had no reason to run"
    assert store.read_bytes() == before, "rung 1 rewrote the seal with no run behind it"

    # FIRST HALF: the run explodes. Nothing may land.
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    assert standing(str(proof))["proven"] is False
    raised = False
    try:
        reseal(proof, tester=_Exploding(), raiser=_FakeRaiser())
    except RuntimeError:
        raised = True
    assert raised, "the fixture's explosion was swallowed — a swallowed run is an unmeasured one"
    assert store.read_bytes() == before, (
        "a seal moved after a run that never produced a record — this is the WRONG INTENT")

    # And the door is honest about what it just refused to do: the seal on disk is still the
    # stale green, so `standing` still reads red. The door never launders; it only records.
    assert json.loads(store.read_text())[-1]["verdict"] == GREEN
    assert standing(str(proof))["proven"] is False


# ── tooth 7 — the door's impatience is not the proof's verdict ────────────────────────

def test_a_timeout_writes_no_seal_and_bounds_no_repair():
    """MEASURED ON THIS DOOR'S OWN COMPONENT, 2026-09-09: `test_hollow.py`'s live tooth
    takes 364s and the door's default budget is 120s. The tester reads a hang as RED and is
    right to — but this door does four more things with a red: it replaces the standing
    record, bounds a repair to the proof's current bytes, opens a ladder, and files a
    trouble. Doing all four off its own impatience would manufacture the exact defect it
    exists to detect, and demand a repair for a proof that was never broken.

    So a timeout is its own outcome, and the tooth measures the four things that must NOT
    happen — plus the one that must: the trouble still fires, saying which of the two it
    was. What the door declines to do is add a verdict it did not earn; the component is
    already red at rung 1 and stays there."""
    root, proof = _component()
    persist_validation(_record(proof, GREEN), proof_path=str(proof))
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    store = Path(validations_path_for(str(proof)))
    before = store.read_bytes()

    raiser = _FakeRaiser()
    fake = _TimingOut()
    out = reseal(proof, tester=fake, raiser=raiser, timeout=120)

    assert fake.runs == 1, "the door must actually try before reporting a timeout"
    assert out["outcome"] == "timeout" and out["ran"] is True, out
    assert store.read_bytes() == before, (
        "a timeout replaced the standing record — the door wrote a verdict its own budget "
        "manufactured")
    assert read_ladder(proof) is None, "a timeout bounded a repair for a proof nobody broke"
    assert [r["identity"] for r in raiser.raised] == [trouble_identity(proof)], raiser.raised
    assert "timed out" in raiser.raised[0]["why"], raiser.raised[0]["why"]
    assert raiser.raised[0]["detail"]["timeout"] == 120
    assert not raiser.cleared, "a timeout cleared a trouble it never resolved"
    # AND THE COMPONENT IS STILL RED. Declining to write is not laundering: the fingerprint
    # that expired is what brought us here, and it has not moved back.
    assert standing(str(proof))["proven"] is False

    # THE OTHER HALF, AND IT IS NOT HYPOTHETICAL: a proof that ASSERTS ON TIMEOUT HANDLING
    # prints "timed out after" on its way to failing — this very file contains the string.
    # If the wording alone decided, that proof's honest red would be filed as the door's own
    # impatience and its ladder would never open. The returncode is the load-bearing half;
    # the wording only corroborates. (Mutation J, 2026-09-09: dropping the returncode
    # conjunct passed every tooth until this one existed.)
    root2, proof2 = _component()
    persist_validation(_record(proof2, GREEN), proof_path=str(proof2))
    (root2 / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    raiser2 = _FakeRaiser()
    liar = _FakeTester(RED, tail="AssertionError: expected 'timed out after 5s', got ''")
    out2 = reseal(proof2, tester=liar, raiser=raiser2, timeout=120)
    assert out2["outcome"] == "red", (
        "a genuine red whose output merely MENTIONS a timeout was filed as the door's own "
        "impatience — its ladder never opened and its repair was never bounded")
    assert read_ladder(proof2) is not None, "the ladder must open for a real red"


def test_a_settled_red_costs_no_run_and_keeps_its_trouble_standing():
    """RUNG 1 HAS TWO LANES, AND THE SECOND ONE COST 417 SECONDS PER COMMIT TO FIND.

    `standing()` answers four ways and only one is proven, so the door's first cut sent the
    other three to the runner alike. Two of them belong there — never sealed, and
    green-but-the-fingerprint-moved are open questions a run is the only way to close. THE
    THIRD IS NOT A QUESTION. A red seal over a closure that has not moved since is an answer
    already taken from these exact bytes; running it again is guaranteed to reproduce it, and
    Law 1 calls re-deriving a settled answer a defect. Measured on this door's own first live
    fire: test_hollow.py is red at 417s, the hook fires on every commit, so the door would
    have spent seven minutes re-learning that fact before every commit in the repo, forever.

    THREE THINGS MUST HOLD AT ONCE and each is a separate way to get this wrong:
      - NO RUN IS SPENT. That is the whole point, and the tester's run counter is the only
        honest way to ask.
      - THE RECORD IS NOT TOUCHED. Skipping a run must never look like a reseal; a door that
        rewrote the record here would be minting a verdict with nothing behind it, which is
        this ticket's WRONG INTENT clause wearing a cheaper coat.
      - THE TROUBLE STANDS. The component IS red. If a hand cleared the trouble while the red
        persisted, silence here would launder a standing red into nothing — so the lane
        re-raises, and raising folds on identity.

    AND THE FINGERPRINT IS WHAT KEEPS RUNG 2 ALIVE: the second half moves the code, which
    moves the closure, and the door must go straight back to running. A lane that fired on
    `verdict != GREEN` alone would pass the first half of this tooth and blind the door to
    every repair that ever follows a red.
    """
    root, proof = _component()
    persist_validation(_record(proof, RED), proof_path=str(proof))

    raiser = _FakeRaiser()
    tester = _FakeTester(GREEN)
    record_path = Path(validations_path_for(str(proof)))
    before_bytes = record_path.read_bytes()
    # MTIME TOO, and not for tidiness. The record's date is second-resolution, so a rewrite
    # inside the same second is byte-identical and a content check alone reads it as "no
    # write" — measured, by a mutation that did exactly that and survived. The nanosecond
    # mtime is what makes "no run, NO WRITE" literal instead of "no difference I can see".
    before_mtime = record_path.stat().st_mtime_ns

    out = reseal(proof, tester=tester, raiser=raiser, skip_settled=True)
    assert out["outcome"] == "settled-red", out
    assert out["rung"] == 1 and out["ran"] is False, out
    assert tester.runs == 0, (
        f"the door re-ran a proof whose red was already settled — {tester.runs} run(s) spent "
        f"re-deriving an answer taken from these exact bytes (Law 1)")
    assert record_path.read_bytes() == before_bytes, (
        "skipping the run rewrote the record anyway — a verdict with no run behind it")
    assert record_path.stat().st_mtime_ns == before_mtime, (
        "the record was rewritten byte-for-byte — no content moved, but the door still went "
        "through its write door on a pass where nothing ran")
    assert raiser.raised, "the standing red was skipped AND went quiet — it must stay troubled"
    assert not raiser.cleared, "a settled red must never clear its own trouble"

    # THE REPAIR MOVES THE CLOSURE, so the lane must stand down and rung 2 must fire.
    (root / "code.py").write_text("VALUE = 99\n", encoding="utf-8")
    repaired = _FakeTester(GREEN)
    out2 = reseal(proof, tester=repaired, raiser=raiser, skip_settled=True)
    assert repaired.runs == 1, (
        "a repair moved the closure and the door STILL skipped the run — the settled-red "
        "lane is firing on the verdict alone and has blinded rung 2 to every repair")
    assert out2["outcome"] == "resealed", out2
    assert standing(str(proof))["proven"] is True, standing(str(proof))["why"]


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
