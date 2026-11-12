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

from cairn.devices.tester.device import GREEN, RED, TIMEOUT  # noqa: E402
from cairn.devices.tester.reseal import (  # noqa: E402
    ResealRefused, proof_sha256, read_ladder, reseal, ruling_refusal, trouble_identity,
)
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.validation_store.validation_store import (  # noqa: E402
    persist_validation, read_validations, source_fingerprint, standing, validations_path_for,
)
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "4a05db0f2280": {
        "3": "test_the_greens_clear_reaches_the_holder_and_the_trouble_leaves_the_live_list",
    },
    "4d9115eb04cd": {
        "1": "test_a_component_whose_source_moved_reads_red_with_no_human_act",
        "2": "test_a_repair_leaving_the_proof_hash_alone_reseals_green_and_closes_the_ladder",
        "3": "test_a_moved_proof_is_refused_without_a_ruling_and_accepted_with_a_confirmed_one",
        "4": "test_an_unrepaired_red_is_one_trouble_carrying_the_tail_and_it_clears_on_the_green",
        "5": "test_no_pulse_path_reaches_the_door",
        "6": "test_no_rung_writes_a_seal_without_a_run_in_the_same_act",
        "7": "test_a_timeout_writes_no_seal_and_bounds_no_repair",
        "8": "test_a_settled_red_costs_no_run_and_keeps_its_trouble_standing",
        "9": "test_the_greens_clear_reaches_the_holder_and_the_trouble_leaves_the_live_list",
    },
    "b65e965237f3": {
        "1": "test_rung_1_clears_a_seal_red_standing_over_a_proven_green_without_a_run",
        "2": "test_rung_1_clears_nothing_where_no_seal_red_stands",
        "3": "test_a_moved_proof_keeps_its_standing_seal_red_through_a_reseal_that_is_not_green",
    },
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

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        self.runs += 1
        self.callers.append(caller)
        assert sink == "none", f"the door must dispose of the record itself, not sink={sink!r}"
        return _record(Path(proof_path), self.verdict,
                       evidence={"stderr_tail": self.tail} if self.tail else None)


class _TimingOut:
    """What `TesterDevice.run_proof` returns when the subject is killed: TIMEOUT, no returncode,
    and the runner's own wording. Copied from the runner rather than invented, because a
    tooth that made up the shape would prove the door against a fixture of its own design."""

    def __init__(self, timeout: int = 120):
        self.timeout, self.runs = timeout, 0

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        self.runs += 1
        return _record(Path(proof_path), TIMEOUT, evidence={
            "returncode": None, "stdout_tail": "",
            "stderr_tail": f"timed out after {timeout}s", "timeout_s": timeout,
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

_DOOR_MODULES = ("cairn.devices.tester.reseal", "cairn.devices.tester.cli")
_BARE_LAUNCHERS = {"exec", "eval", "__import__", "import_module"}


def _module_of(path: Path) -> str:
    """The dotted module a file under the repo would import as — what a relative import
    in it resolves against."""
    try:
        rel = path.resolve().relative_to(_REPO_ROOT)
    except ValueError:
        return ""
    return ".".join(rel.with_suffix("").parts)


def _reaches(path: Path, module: str | None = None) -> list[str]:
    """Every way this file REACHES the reseal door, as one line each — empty when it reaches
    nothing.

    Two shapes reach (adjudicated 2026-11-01, open-1fd084bd6c01, sieve why against probe why):
    an IMPORT of the door's module or the tester cli that fronts it, absolute or relative; or
    a reseal-bearing string — a literal, or a name bound to one, however many hops — inside
    the arguments of something that launches or loads: subprocess, os.system/popen/exec*/
    spawn*, import_module, __import__, exec, eval, runpy. A name merely HOLDING the string,
    compared against a record and never handed to a launcher, reaches nothing; nor does a
    comment or a docstring. An unparseable file is measured whole: the word anywhere reds it."""
    import ast

    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ["unparseable, and the word reseal appears in it"] if "reseal" in text.lower() else []
    module = _module_of(path) if module is None else module
    found = []

    def door(name: str) -> bool:
        return any(name == m or name.startswith(m + ".") for m in _DOOR_MODULES)

    launchers = set(_BARE_LAUNCHERS)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if door(a.name):
                    found.append(f"line {node.lineno}: import {a.name}")
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                pkg = module.split(".")[:-node.level]
                base = ".".join(pkg + ([node.module] if node.module else []))
            for a in node.names:
                if door(base) or door(f"{base}.{a.name}"):
                    found.append(f"line {node.lineno}: from {base} import {a.name}")
                if base in ("subprocess", "runpy", "importlib") or (base == "os" and (
                        a.name in ("system", "popen") or a.name.startswith(("exec", "spawn")))):
                    launchers.add(a.asname or a.name)

    def bearing(sub) -> bool:
        return any(isinstance(n, ast.Constant) and isinstance(n.value, str)
                   and "reseal" in n.value.lower() for n in ast.walk(sub))

    bound: set[str] = set()
    while True:  # a name bound to a name bound to the literal is still the literal
        grew = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and node.value is not None:
                v = node.value
                if bearing(v) or any(isinstance(n, ast.Name) and n.id in bound for n in ast.walk(v)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for t in targets:
                        for n in ast.walk(t):
                            if isinstance(n, ast.Name) and n.id not in bound:
                                bound.add(n.id)
                                grew = True
        if not grew:
            break

    def launches(func) -> bool:
        if isinstance(func, ast.Name):
            return func.id in launchers
        if isinstance(func, ast.Attribute):
            root = func.value
            while isinstance(root, ast.Attribute):
                root = root.value
            root = root.id if isinstance(root, ast.Name) else ""
            if func.attr == "import_module" or root in ("subprocess", "runpy"):
                return True
            return root == "os" and (func.attr in ("system", "popen")
                                     or func.attr.startswith(("exec", "spawn")))
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and launches(node.func):
            parts = list(node.args) + [k.value for k in node.keywords]
            if any(bearing(p) or any(isinstance(n, ast.Name) and n.id in bound
                                     for n in ast.walk(p)) for p in parts):
                found.append(f"line {node.lineno}: {ast.unparse(node.func)}(...) carries a reseal string")
    return found


# Each shape the narrowed tooth must still red, and two it must not — written out rather than
# derived, so a reach the narrowing forgot shows up here as a fixture that stops redding.
_REACH_FIXTURES = {
    "import_reseal": "import cairn.devices.tester.reseal\n",
    "from_tester_cli": "from cairn.devices.tester import cli\n",
    "from_reseal": "from cairn.devices.tester.reseal import reseal\n",
    "relative": "from .. import reseal\n",
    "subprocess_literal": "import subprocess\nsubprocess.run(['bin/cairn', 'test', '--reseal'])\n",
    "subprocess_bound": "import subprocess\nCMD = 'cairn test --reseal'\nsubprocess.Popen(CMD, shell=True)\n",
    "two_hops": "import os\nA = '--reseal'\nB = ['cairn', 'test', A]\nos.execvp('cairn', B)\n",
    "from_subprocess": "from subprocess import check_call\ncheck_call(['cairn', 'test', '--reseal'])\n",
    "os_system": "import os\nx = 1\nos.system(f'cairn test --reseal {x}')\n",
    "os_spawn": "import os\nos.spawnlp(os.P_WAIT, 'cairn', 'cairn', 'test', '--reseal')\n",
    "import_module": "import importlib\nimportlib.import_module('cairn.devices.tester.reseal')\n",
    "dunder_import": "__import__('cairn.devices.tester.reseal')\n",
    "exec": "exec('import cairn.devices.tester.reseal')\n",
    "eval": "eval(\"__import__('cairn.devices.tester.reseal')\")\n",
    "runpy": "import runpy\nrunpy.run_module('cairn.devices.tester.reseal')\n",
    "unparseable": "def (:\n    cairn test --reseal\n",
}
_CLEAR_FIXTURES = {
    "compared_only": ("import subprocess\n_CALLER = 'cairn test --reseal'\n"
                      "subprocess.run(['git', 'log', '-1'], timeout=10)\n"
                      "def sealed_by_hook(r):\n    return r.get('caller') == _CALLER\n"),
    "prose_only": '"""the reseal door runs proofs"""\n# a reseal is minutes\nX = 1\n',
}


def test_no_pulse_path_reaches_the_door():
    """The ticket's third constraint: *fired from pre-commit over staged files; never from
    any on_pulse path.* The door runs proofs — minutes of subprocess — and the beat already
    spends 23.5 of every 23.7 seconds re-walking corpora that did not move. A reseal sweep on
    the beat would not be slow, it would be a machine that never finishes one pulse before
    the next.

    Measured over shims, probes and the ground loop rather than over a list of files a
    future caller could sidestep: those three ARE the pulse surface.

    IT MEASURES A REACH, NOT A WORD (2026-11-01, open-1fd084bd6c01, ridden by ticket
    e8be83a46ea9). On 2026-09-09 (ticket 1accdc1781aa) the grep stopped reading prose,
    because "a paragraph reaches nothing". It still read every remaining string, so the probe
    a_commit_that_reseals_leaves_a_clean_tree.py redded it for holding the hook's caller
    string "cairn test --reseal" — which it only compares against a validation record's
    caller field, beside a read-only git log. Weighed sieve why against probe why: the claim
    is that a pulse path REACHES the door, and holding a string to compare reaches nothing
    either. So the tooth reads the two shapes that do reach (see `_reaches`), and before it
    trusts that narrowing over the live surfaces it proves every reach shape — sixteen of
    them, written out in `_REACH_FIXTURES` — still reds, and that the compare-only and
    prose-only shapes do not. A narrowing that lost a shape fails here, not in the field."""
    tmp = scratch_dir("cairn-pulsereach-")
    for name, src in _REACH_FIXTURES.items():
        f = tmp / f"{name}.py"
        f.write_text(src, encoding="utf-8")
        assert _reaches(f, module="cairn.devices.tester.probes.fixture"), \
            f"the narrowed tooth no longer reds the {name!r} reach: {src!r}"
    for name, src in _CLEAR_FIXTURES.items():
        f = tmp / f"{name}.py"
        f.write_text(src, encoding="utf-8")
        assert not _reaches(f, module="cairn.devices.tester.probes.fixture"), \
            (name, _reaches(f, module="cairn.devices.tester.probes.fixture"))

    surfaces = []
    surfaces += sorted((_REPO_ROOT / "cairn").rglob("shim.py"))
    surfaces += [p for p in sorted((_REPO_ROOT / "cairn").rglob("probes/*.py"))]
    surfaces += sorted((_REPO_ROOT / "cairn" / "devices" / "cairn" / "machines"
                        / "ground_loop").rglob("*.py"))
    assert surfaces, "the grep found no pulse surfaces at all — the tooth measured nothing"

    offenders = {}
    for path in surfaces:
        reach = _reaches(path)
        if reach:
            offenders[str(path.relative_to(_REPO_ROOT))] = reach
    assert not offenders, (
        f"the reseal door is reached from a pulse path: {offenders}. It runs proofs; the beat "
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


# ── tooth 9 ───────────────────────────────────────────────────────────────────────────

RECIPIENT = "cc"
"""The name trouble notifies by default, and so the only name whose clear takes a trouble off
its live list. Trouble's own proof (test_trouble.py, test_only_the_recipient_clears_it) holds
the fold; this proof holds that the door SIGNS with it."""


def _holder(root: Path):
    """A scratch trouble store and a raiser that writes it the way the holder lays it out: a
    live trouble is ``<store>/<id>.json``, a cleared one berths in the published tool's
    ``CLEARED_DIR``, and only the recipient's clear moves it (RULE 1: the tester's proofs
    measure the tester, so the holder here is a stand-in and the read goes through the store
    tool trouble publishes). Returns (store, raiser); the raiser records every clear."""
    from cairn.devices.trouble.tools.store.store import CLEARED_DIR

    store = root / "troubles"
    store.mkdir(parents=True, exist_ok=True)

    class _HolderRaiser:
        def __init__(self):
            self.cleared, self.signed = [], []

        def raise_trouble(self, identity, *, why, detail=None):
            path = store / f"{identity}.json"
            rec = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
                "id": identity, "standing": "OPEN", "why": why, "count": 0,
                "notified": [RECIPIENT], "cleared_by": []}
            rec["count"] += 1
            path.write_text(json.dumps(rec), encoding="utf-8")

        def clear_trouble(self, identity, *, by, what_changed):
            self.cleared.append(identity)
            self.signed.append({"by": by, "what_changed": what_changed})
            path = store / f"{identity}.json"
            if not path.exists():
                return
            rec = json.loads(path.read_text(encoding="utf-8"))
            rec["cleared_by"].append({"by": by})
            if by not in rec["notified"]:
                path.write_text(json.dumps(rec), encoding="utf-8")
                return
            rec["standing"] = "CLEARED"
            rec["resolution"] = {"what_changed": what_changed}
            (store / CLEARED_DIR).mkdir(exist_ok=True)
            (store / CLEARED_DIR / f"{identity}.json").write_text(json.dumps(rec), encoding="utf-8")
            path.unlink()

    return store, _HolderRaiser()


def _live_ids(store: Path) -> list:
    from cairn.devices.trouble.tools.store.store import live
    return [t["id"] for t in live(root=store)]


def test_the_greens_clear_reaches_the_holder_and_the_trouble_leaves_the_live_list():
    """RUNG 3's OTHER HALF: THE NAME THE CLEAR IS SIGNED WITH. Tooth 4 asserts the door EMITS a
    clear with the right identity. What stood wrong in the live store for four days
    (2026-09-09..13, 11 of 12 seal-red troubles) was the SIGNATURE: trouble clears per
    recipient, its troubles are notified to ``cc``, and the door signed ``by="cairn test
    --reseal"``. The fold appended the clear, read ``cc`` as still outstanding, and left the
    trouble OPEN.

    So the door's clear must be signed by the recipient, with its own name as provenance in
    what_changed, and after the green the published store tool reads the trouble gone."""
    root, proof = _component()
    store, raiser = _holder(root)

    persist_validation(_record(proof, GREEN), proof_path=str(proof))
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    identity = trouble_identity(proof)

    red = reseal(proof, tester=_FakeTester(RED, tail="AssertionError: fixture"), raiser=raiser)
    assert red["outcome"] == "red", red
    assert _live_ids(store) == [identity], "the red did not land as a live trouble"

    (root / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    green = reseal(proof, tester=_FakeTester(GREEN), raiser=raiser)
    assert green["outcome"] == "resealed", green
    assert [s["by"] for s in raiser.signed] == [RECIPIENT], (
        f"the door's clear is signed {[s['by'] for s in raiser.signed]!r}, not by the recipient "
        f"{RECIPIENT!r} — trouble appends such a clear and nothing ever leaves the inbox")
    assert "cairn test --reseal" in raiser.signed[0]["what_changed"], (
        "the door's name is provenance and belongs in what_changed")
    assert _live_ids(store) == [], "the published store tool still reads the trouble live"


# ── rung 1 settles a standing raise (ticket b65e965237f3) ─────────────────────────────

def test_rung_1_clears_a_seal_red_standing_over_a_proven_green_without_a_run():
    """MEASURED 2026-11-10/11: a seal-red raised while the standing verdict stayed green (a
    timeout) outlived every later green, because validation_store clears only on a verdict
    CHANGE and rung 1 returned without a word. Here the proof is sealed green over today's
    bytes, its seal-red stands live at a real holder, and one reseal must take it off the
    live list. The tester EXPLODES if called: rung 1 settles from the seal, never by a run."""
    root, proof = _component()
    persist_validation(_record(proof, GREEN), proof_path=str(proof))
    assert standing(str(proof))["proven"], "fixture: the seal must read proven"
    store, raiser = _holder(root)
    identity = trouble_identity(proof)
    raiser.raise_trouble(identity, why="fixture: a timeout raised while the seal stayed green")
    raiser.cleared.clear()
    assert _live_ids(store) == [identity], "fixture: the raise did not land"

    out = reseal(proof, tester=_Exploding(), raiser=raiser, trouble_root=store)
    assert out["outcome"] == "unchanged" and out["rung"] == 1 and out["ran"] is False, out
    assert out["cleared"] == identity, out
    assert _live_ids(store) == [], (
        "rung 1 read the proof proven and the seal-red it stood under is STILL LIVE — a false "
        "alarm the green already answered")


def test_rung_1_clears_nothing_where_no_seal_red_stands():
    """THE BLIND CLEAR STAYS DEAD (ticket 87f0fc7b3514: 5054 clears with no raise behind
    them, 2026-11-05). Rung 1 fires for every proof on every commit; a clear emitted for each
    would be that defect at corpus scale. A holder carrying some OTHER trouble, and a holder
    with no store at all, both draw no clear."""
    root, proof = _component()
    persist_validation(_record(proof, GREEN), proof_path=str(proof))
    store, holder = _holder(root)
    holder.raise_trouble("seal-red-some-other-proof", why="fixture: a neighbour's raise")
    raiser = _FakeRaiser()
    out = reseal(proof, tester=_Exploding(), raiser=raiser, trouble_root=store)
    assert out["outcome"] == "unchanged" and out["cleared"] is None, out
    assert raiser.cleared == [], f"rung 1 cleared with nothing of its own standing: {raiser.cleared}"
    assert _live_ids(store) == ["seal-red-some-other-proof"], (
        "rung 1 cleared a trouble under another proof's identity")
    out2 = reseal(proof, tester=_Exploding(), raiser=raiser, trouble_root=root / "no-store-here")
    assert out2["cleared"] is None and raiser.cleared == [], (out2, raiser.cleared)


def test_a_moved_proof_keeps_its_standing_seal_red_through_a_reseal_that_is_not_green():
    """A STALE GREEN MAY NOT CLEAR ITS OWN RED. The lane keys on ``standing()['proven']``, not on
    the seal's verdict: a green whose fingerprint moved is an open question, so it runs, and a
    run that times out settles nothing — the raise stays live at the holder."""
    root, proof = _component()
    persist_validation(_record(proof, GREEN), proof_path=str(proof))
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    assert not standing(str(proof))["proven"], "fixture: the fingerprint must have moved"
    store, raiser = _holder(root)
    identity = trouble_identity(proof)
    raiser.raise_trouble(identity, why="fixture: a standing seal-red")
    out = reseal(proof, tester=_TimingOut(), raiser=raiser, trouble_root=store)
    assert out["outcome"] == "timeout", out
    assert raiser.cleared == [], f"a reseal that was not green cleared {raiser.cleared}"
    assert _live_ids(store) == [identity], (
        "the standing seal-red left the live list though nothing proved the moved bytes")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
