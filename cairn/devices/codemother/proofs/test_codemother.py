"""Proofs for the CodeMother device — teeth a hollow build couldn't pass.

Covers: device skeleton, type system, per-project isolation, vocabulary,
mine, ingest, constraints compiler, constraint proof lifecycle, challenge,
query, and digest.
"""

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path

from cairn.devices.tester.scratch import scratch_dir


def _commons_root():
    """The operator's REAL commons, named the same from the live tree and from a worktree.

    THE CLASS OF BUG THIS ENDS, and it is a class with its own ticket
    (a-proof-that-reaches-a-sibling-repo-by-relative-path-cannot-be-reproven-elsewhere):
    ``parents[N].parent / "CairnCommons"`` is the sibling of WHATEVER CHECKOUT IS RUNNING.
    A worktree is a checkout of this repo at another path, so from
    ``/tmp/cairn-hollow-xxx/worktree`` that expression names a CairnCommons under /tmp that
    has never existed. Measured 2026-09-09 on THIS file: 29/29 green in the live tree, 28/29
    in ``git worktree add /tmp/hw HEAD``, the one red being
    ``test_a_green_seal_crosses_the_PROVEME_boat_that_NAMES_that_proof`` with
    ``unknown node-class 'code-seam' — no definition at /tmp/CairnCommons/node_classes/``.
    And because a declared tooth that is not green at HEAD makes every reversion reading
    unattributable, that one path was refusing the whole hollow measurement of ticket
    1accdc1781aa with ``HollowUnmeasurable``.

    WHY GIT'S COMMON DIR. ``--git-common-dir`` is the shared ``.git`` of the repo AND of
    every worktree of it, so its parent is the MAIN working tree from wherever this runs,
    and its sibling is the one commons the operator actually has. The precedent is
    ``cairn/devices/trouble/proofs/test_trouble.py`` (2026-09-09), which took the same fix
    for the same reason and now reads 37/37 both ways; the reasoning there — why not an env
    var, why not ``cairnmap.commons_root()`` (it derives from ``__file__`` and carries the
    same bug, and widening it from here is the shape Law 8 refuses) — holds here unchanged.
    """
    return _main_tree().parent / "CairnCommons"


def _main_tree():
    """The MAIN working tree of this repo, named the same from itself and from a worktree.

    ``--git-common-dir`` is the shared ``.git`` of the repo AND of every worktree of it, so
    its parent is the main tree from wherever this runs. Everything a proof reaches for
    outside its own scratch — the operator's commons, his real cast tickets, the node-class
    definitions — hangs off this one answer, so it is derived once here rather than
    re-spelled per tooth.
    """
    common = subprocess.run(
        ["git", "-C", str(Path(__file__).resolve().parent),
         "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True)
    if common.returncode == 0 and common.stdout.strip():
        return Path(common.stdout.strip()).parent
    # NOT A SILENT FALLBACK: outside a git checkout there is no main tree to name. The
    # checkout itself is the honest best effort, and the caller then fails LOUDLY naming
    # the path it looked in — the behaviour that surfaced this bug in the first place.
    return Path(__file__).resolve().parents[4]

# WHICH TICKET CLAUSES THESE TEETH COVER — read out of the AST by
# cairn/tools/proof_coverage, never by importing this module. The join is the
# intersection of three things already on disk: the ticket's clauses, this
# declaration, and the teeth the seal records as actually printed.
PROVES = {
    # A SEAM HAS ENDS IN MORE THAN ONE COMPONENT, and `proven_by` is read as one-or-many so
    # the crossing can name all of them. Clauses (1) and (4) of 1accdc1781aa are the tester's
    # end (cairn/devices/tester/proofs/test_the_seal_announces_itself.py); clause (3) is the
    # harbor's (machines/harbor_master/proofs/test_clearance.py). These two are codemother's.
    "1accdc1781aa": {
        "2": "test_a_green_seal_crosses_the_PROVEME_boat_that_NAMES_that_proof",
        "5": "test_a_seal_NO_PROVEME_TICKET_NAMES_crosses_nothing_and_troubles_nobody",
    },
    "8754ae677af6": {
        "1": "test_a_crossing_codemother_admits_names_her_in_the_record",
        "2": "test_the_door_still_refuses_an_unproven_boat_through_her",
        "3": "test_codemother_never_imports_the_harbor",
    },
}

# ── helpers ──────────────────────────────────────────────────────────────

def _tmp_project_root():
    """Create a temp directory that looks like a project root."""
    d = str(scratch_dir("codemother_test_"))
    for sub in ("types", "constraints", "mining"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    return d


# ══════════════════════════════════════════════════════════════════════════
# 1. DEVICE SKELETON
# ══════════════════════════════════════════════════════════════════════════

def test_shim_imports_and_has_correct_device_id():
    from cairn.devices.codemother.shim import CodeMotherShim
    s = CodeMotherShim()
    assert s.device_id == "codemother", f"device_id is {s.device_id!r}, expected 'codemother'"
    assert isinstance(s.probes(), list), "probes() must return a list"
    print("PASS: shim imports, device_id='codemother', probes() returns list")


def test_charter_exists_and_is_valid():
    charter_path = Path(__file__).parent.parent / "intention+why.json"
    assert charter_path.exists(), f"charter not found at {charter_path}"
    data = json.loads(charter_path.read_text())
    assert data["component"] == "codemother", f"charter component is {data['component']!r}"
    assert "falsifier" in data, "charter has no falsifier"
    assert "why" in data, "charter has no why"
    print("PASS: charter exists, component='codemother', has falsifier and why")


def test_probe_loads():
    from cairn.devices.codemother.probes.the_shim_delivers_mail import PROBE
    assert PROBE is not None, "PROBE is None"
    assert PROBE.why, "PROBE has no why"
    assert callable(PROBE.trigger), "PROBE trigger is not callable"
    print("PASS: probe loads, has why, trigger is callable")


# ══════════════════════════════════════════════════════════════════════════
# 2. TYPE SYSTEM
# ══════════════════════════════════════════════════════════════════════════

def test_positive_and_negative_types_are_distinct():
    from cairn.devices.codemother.types import positive, negative, TypePolarity
    p = positive("test-pos", "a positive pattern")
    n = negative("test-neg", "a negative pattern")
    assert p.polarity == TypePolarity.POSITIVE
    assert n.polarity == TypePolarity.NEGATIVE
    assert p.polarity != n.polarity, "positive and negative must be distinct"
    print("PASS: positive and negative types are distinct")


def test_type_roundtrip():
    from cairn.devices.codemother.types import positive, PatternType, PatternSignal
    original = positive(
        "test-roundtrip", "roundtrip test",
        signals=(PatternSignal("signal-a"), PatternSignal("signal-b", weight=0.5)),
        tags=("tag1", "tag2"),
    )
    d = original.to_dict()
    restored = PatternType.from_dict(d)
    assert restored.name == original.name
    assert restored.why == original.why
    assert restored.polarity == original.polarity
    assert len(restored.signals) == len(original.signals)
    print("PASS: type serializes and deserializes correctly")


def test_unify_distinguishes_positive_from_negative():
    from cairn.devices.codemother.types import positive, negative, PatternSignal
    from cairn.devices.codemother.unify import unify

    pos = positive("charter-pattern", "charters beside code",
                   signals=(PatternSignal("intention+why.json co-located with code"),))
    neg = negative("ground-loop-scope-creep", "adding features to the ground loop",
                   signals=(PatternSignal("adding learning to ground_loop"),))
    library = [pos, neg]

    results = unify(["adding learning to ground_loop"], library, threshold=0.3)
    neg_matches = [r for r in results if r.pattern.polarity.value == "negative"]
    pos_matches = [r for r in results if r.pattern.polarity.value == "positive"]
    assert len(neg_matches) > 0, "should match the negative type"
    assert len(pos_matches) == 0, "should NOT match the positive type"
    print(f"PASS: unify found {len(neg_matches)} negative, {len(pos_matches)} positive matches")


def test_schema_is_project_agnostic():
    from cairn.devices.codemother.types import PatternType
    import inspect
    source = inspect.getsource(PatternType)
    cairn_terms = ["cairn", "ground_loop", "harbor_master", "librarian"]
    for term in cairn_terms:
        assert term not in source, f"schema contains cairn-specific term '{term}'"
    print("PASS: schema has no cairn-specific field names")


# ══════════════════════════════════════════════════════════════════════════
# 3. PER-PROJECT ISOLATION
# ══════════════════════════════════════════════════════════════════════════

def test_projects_are_isolated():
    from cairn.devices.codemother.types import negative, PatternSignal
    from cairn.devices.codemother.project import (
        ensure_project, save_type, load_types, _PROJECTS_ROOT,
    )
    import cairn.devices.codemother.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemother_proj_")
    try:
        proj_mod._PROJECTS_ROOT = tmp

        ensure_project("alpha")
        ensure_project("beta")

        t = negative("alpha-only", "only in alpha",
                     signals=(PatternSignal("alpha signal"),))
        save_type("alpha", t)

        alpha_types = load_types("alpha")
        beta_types = load_types("beta")
        assert len(alpha_types) == 1, f"alpha should have 1 type, has {len(alpha_types)}"
        assert len(beta_types) == 0, f"beta should have 0 types, has {len(beta_types)}"
        print("PASS: projects are isolated — writing to alpha did not affect beta")
    finally:
        proj_mod._PROJECTS_ROOT = original_root


# ══════════════════════════════════════════════════════════════════════════
# 4. VOCABULARY
# ══════════════════════════════════════════════════════════════════════════

def test_vocabulary_loads():
    from cairn.devices.codemother.vocabulary import load_catalog, catalog_names
    names = catalog_names()
    assert len(names) > 0, "catalog is empty"
    assert "single-responsibility" in names, f"'single-responsibility' not in catalog: {names}"
    catalog = load_catalog()
    assert len(catalog) == len(names), "catalog and names count mismatch"
    for entry in catalog:
        assert entry.name, f"entry has no name"
        assert entry.why, f"entry {entry.name} has no why"
    print(f"PASS: vocabulary catalog loads with {len(catalog)} entries, all have name+why")


def test_vocabulary_validates_against_type_schema():
    from cairn.devices.codemother.vocabulary import load_catalog
    from cairn.devices.codemother.types import PatternType
    catalog = load_catalog()
    for entry in catalog:
        assert isinstance(entry, PatternType), f"{entry.name} is not a PatternType"
        d = entry.to_dict()
        restored = PatternType.from_dict(d)
        assert restored.name == entry.name
    print(f"PASS: all {len(catalog)} vocabulary entries validate against the type schema")


def test_vocabulary_is_project_agnostic():
    from cairn.devices.codemother.vocabulary import load_catalog
    catalog = load_catalog()
    for entry in catalog:
        assert entry.scope in ("", "universal"), \
            f"{entry.name} has non-universal scope: {entry.scope!r}"
    print("PASS: all vocabulary entries are project-agnostic")


# ══════════════════════════════════════════════════════════════════════════
# 5. MINE
# ══════════════════════════════════════════════════════════════════════════

def test_mine_produces_types_from_cairn():
    from cairn.devices.codemother.mine import scan_structure, derive_types
    cairn_root = Path(__file__).parent.parent.parent.parent  # cairn/
    observations = scan_structure(cairn_root)
    assert len(observations) > 0, "scan found zero observations"

    types = derive_types(observations, "cairn")
    assert len(types) > 0, f"derived zero types from {len(observations)} observations"

    type_names = [t.name for t in types]
    assert "charter-pattern" in type_names, f"missing charter-pattern in {type_names}"
    assert "proof-pattern" in type_names, f"missing proof-pattern in {type_names}"
    print(f"PASS: mine found {len(observations)} observations, derived {len(types)} types: {type_names}")


# ══════════════════════════════════════════════════════════════════════════
# 6. INGEST
# ══════════════════════════════════════════════════════════════════════════

def test_ingest_memory_files():
    from cairn.devices.codemother.ingest import ingest_memory_files
    memory_dir = Path.home() / ".claude" / "projects" / "-home-akien-dev-src-cairn" / "memory"
    if not memory_dir.is_dir():
        print("SKIP: memory directory not found")
        return

    types = ingest_memory_files(memory_dir)
    assert len(types) > 0, "ingested zero types from memory files"

    with_whys = [t for t in types if t.why]
    assert len(with_whys) == len(types), \
        f"{len(types) - len(with_whys)} types have no why"
    print(f"PASS: ingested {len(types)} negative types from memory files, all have whys")


# ══════════════════════════════════════════════════════════════════════════
# 7. CONSTRAINTS COMPILER
# ══════════════════════════════════════════════════════════════════════════

def test_compiler_deduplicates_by_why():
    from cairn.devices.codemother.types import negative, PatternSignal
    from cairn.devices.codemother.project import ensure_project, save_type, load_types
    from cairn.devices.codemother.constraints_compiler import compile_constraints
    import cairn.devices.codemother.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemother_compiler_")
    try:
        proj_mod._PROJECTS_ROOT = tmp
        ensure_project("test-dedup")

        same_why = "don't touch the ground loop"
        for i in range(3):
            save_type("test-dedup", negative(
                f"ground-loop-violation-{i}", same_why,
                signals=(PatternSignal("ground loop scope creep"),),
                source=f"session-{i}",
            ))

        compiled = compile_constraints("test-dedup")
        assert len(compiled) == 1, f"expected 1 compiled constraint, got {len(compiled)}"
        assert compiled[0]["incident_count"] == 3, \
            f"expected count=3, got {compiled[0]['incident_count']}"
        print(f"PASS: 3 incidents with same why compiled to 1 constraint with count=3")
    finally:
        proj_mod._PROJECTS_ROOT = original_root


# ══════════════════════════════════════════════════════════════════════════
# 8. CONSTRAINT PROOF LIFECYCLE
# ══════════════════════════════════════════════════════════════════════════

def test_constraint_proof_lifecycle():
    from cairn.devices.codemother.constraint_proof import (
        ConstraintProof, save_proof, load_proof,
    )
    tmp = scratch_dir("codemother_proof_")
    try:
        proof = ConstraintProof(
            constraint_name="test-constraint",
            founding_incident={"source": "test", "at": "2026-08-31", "what": "CC violated X"},
        )
        assert proof.is_active, "new proof should be active"
        assert proof.catch_count == 0, "new proof should have 0 catches"

        proof.record_catch("first live catch")
        assert proof.catch_count == 1, "should have 1 catch"

        proof.record_catch("second live catch")
        assert proof.catch_count == 2, "should have 2 catches"

        proof.retire("the cause was fixed")
        assert not proof.is_active, "retired proof should not be active"
        assert proof.catch_count == 2, "retirement should not lose catches"

        path = save_proof(tmp, proof)
        loaded = load_proof(tmp, "test-constraint")
        assert loaded is not None, "could not load saved proof"
        assert not loaded.is_active, "loaded proof should be retired"
        assert loaded.catch_count == 2, "loaded proof should have 2 catches"
        assert loaded.founding_incident["what"] == "CC violated X"

        print("PASS: constraint proof lifecycle — create, catch x2, retire, save, load")
    finally:
        pass


# ══════════════════════════════════════════════════════════════════════════
# 9. CHALLENGE
# ══════════════════════════════════════════════════════════════════════════

def test_challenge_catches_known_violation():
    from cairn.devices.codemother.types import negative, positive, PatternSignal
    from cairn.devices.codemother.project import ensure_project, save_type
    from cairn.devices.codemother.challenge import challenge
    import cairn.devices.codemother.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemother_challenge_")
    try:
        proj_mod._PROJECTS_ROOT = tmp
        ensure_project("test-challenge")

        save_type("test-challenge", negative(
            "ground-loop-scope-creep",
            "adding learning or monitoring features to the ground loop — it is just the heartbeat",
            signals=(PatternSignal("adding learning to ground_loop"),
                     PatternSignal("adding monitoring to ground_loop"),),
        ))
        save_type("test-challenge", positive(
            "heartbeat-only",
            "the ground loop is heartbeat + device list, nothing more",
            signals=(PatternSignal("ground loop heartbeat"),),
        ))

        result = challenge(["adding learning to ground_loop"], "test-challenge")
        assert len(result.violations) > 0, \
            "challenge should catch 'adding learning to ground_loop' as a violation"
        assert result.violations[0].pattern.name == "ground-loop-scope-creep"

        clean_result = challenge(["creating a new file in codemother/"], "test-challenge")
        assert len(clean_result.violations) == 0, \
            f"clean change should produce 0 violations, got {len(clean_result.violations)}"
        assert clean_result.clean, "clean change should be marked clean"

        print(f"PASS: challenge caught violation, clean change passed — "
              f"{len(result.violations)} violation(s), clean={clean_result.clean}")
    finally:
        proj_mod._PROJECTS_ROOT = original_root


# ══════════════════════════════════════════════════════════════════════════
# 10. QUERY
# ══════════════════════════════════════════════════════════════════════════

def test_query_returns_relevant_types():
    from cairn.devices.codemother.types import negative, positive, PatternSignal
    from cairn.devices.codemother.project import ensure_project, save_type
    from cairn.devices.codemother.query import query
    import cairn.devices.codemother.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemother_query_")
    try:
        proj_mod._PROJECTS_ROOT = tmp
        ensure_project("test-query")

        save_type("test-query", negative(
            "ground-loop-scope-creep",
            "CC-- x3: ground loop is just the heartbeat, nothing more",
            signals=(PatternSignal("ground_loop"),
                     PatternSignal("adding feature"),),
        ))
        save_type("test-query", positive(
            "heartbeat-pattern",
            "the ground loop fires a heartbeat",
            signals=(PatternSignal("ground_loop heartbeat"),),
        ))

        result = query("ground_loop", "adding a feature", "test-query", threshold=0.2)
        assert len(result.negative_matches) > 0, \
            "query should surface the CC-- x3 constraint for ground_loop"
        print(f"PASS: query returned {len(result.positive_matches)} positive, "
              f"{len(result.negative_matches)} negative matches for ground_loop")
    finally:
        proj_mod._PROJECTS_ROOT = original_root


# ══════════════════════════════════════════════════════════════════════════
# 11. DIGEST
# ══════════════════════════════════════════════════════════════════════════

def test_digest_consolidates():
    from cairn.devices.codemother.types import negative, PatternSignal
    from cairn.devices.codemother.project import ensure_project, save_type
    from cairn.devices.codemother.digest import digest
    import cairn.devices.codemother.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemother_digest_")
    try:
        proj_mod._PROJECTS_ROOT = tmp
        ensure_project("test-digest")

        same_why = "don't touch the ground loop"
        for i in range(3):
            save_type("test-digest", negative(
                f"gl-violation-{i}", same_why,
                signals=(PatternSignal("ground loop scope creep"),),
            ))

        result = digest("test-digest", use_hex=False)
        assert result["input_count"] == 3, f"expected 3 inputs, got {result['input_count']}"
        assert result["consolidated_count"] == 1, \
            f"expected 1 consolidated, got {result['consolidated_count']}"
        assert result["reduction"] == 2, f"expected reduction=2, got {result['reduction']}"
        print(f"PASS: digest consolidated 3 -> 1, reduction={result['reduction']}")
    finally:
        proj_mod._PROJECTS_ROOT = original_root


# ══════════════════════════════════════════════════════════════════════════
# 13. CODEMOTHER CROSSES A BOAT THROUGH THE HARBOR DOOR AS HERSELF
#     ticket 8754ae677af6 — the falsifier's three clauses, plus the two bugs
#     the voyage uncovered (bounds ruling
#     CairnCommons/decisions/2026-09-09-a-bug-the-voyage-uncovers-is-fixed-by-that-voyage.json)
# ══════════════════════════════════════════════════════════════════════════

# The boat these teeth move. It is harbor_master's OWN ticket, whose charter names
# codemother among the hands its gate admits — so a crossing that succeeds here is a
# crossing the authority check actually looked at, not one that had no owner to ask.
_HARBOR_BOAT = "6acd0cf29fe1"
# A cursor sitting ON PROVEME, so the legal forward step is PROVED. Written out rather
# than rendered because the fixture must not depend on a class definition that can move.
_FIXTURE_WORKFLOW = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
# The one tooth the fixture proof prints. Named once because three things must agree about
# it: the function, the PASS line the seal records, and the clause the ticket declares.
_FIXTURE_TOOTH = "test_nothing_is_nothing"


def _fixture_component(tag, *, seal=True, boat=None):
    """Mint a scratch component the census admits and the build gate passes.

    Returns ``(component_dir, proof_path)``. Every field here was driven empirically
    against the LIVE gate on 2026-09-09, and each one is load-bearing:

    - ``learns`` — the ``learning_declared`` sieve reads THIS key, not the
      ``how_it_learns`` that 70 charters carry (the known IOU at CLAUDE.md's residues).
      Writing only ``how_it_learns`` reds the gate.
    - ``claim_provenance`` — must be a non-empty dict or ``claim_provenance`` reds.
    - ``gated_by`` — the hands the fixture's own gate admits.
    - ``state.json`` — must EQUAL ``projector.project(history)`` literally, because
      ``state_is_projection`` compares them; for an empty history that is
      ``{"cursor": None, "window": [], "count": 0}``.

    ``seal=False`` leaves the proof NEVER RUN under the tester, which is how the
    refusal tooth gets a boat that is honestly not in proven-space.
    """
    from cairn.devices.tester.scratch import scratch_dir

    root = Path(scratch_dir(tag))
    comp = root / "a_fixture_component"
    (comp / "proofs").mkdir(parents=True, exist_ok=True)
    (comp / "intention+why.json").write_text(json.dumps({
        "component": "a_fixture_component",
        "why": "a fixture the census can measure and the build inspector can pass",
        "falsifier": "n/a — a fixture, born and destroyed inside one proof run",
        "role": "fixture",
        "runtime_role": "tool",
        "gated_by": ["codemother", "CC"],
        "how_it_learns": "It does not — a fixture holds no state between runs.",
        "learns": "It does not — a fixture is born and destroyed inside one proof run.",
        "claim_provenance": {"why": "cc-read", "role": "cc-read"},
    }), encoding="utf-8")
    (comp / "fixture.py").write_text("def nothing():\n    return None\n", encoding="utf-8")
    proof = comp / "proofs" / "test_fixture.py"
    # ``PROVES`` IS WRITTEN BEFORE THE SEAL, NEVER AFTER (2026-09-09, ticket 1accdc1781aa).
    # The coverage rung asks two questions of the same file: does it DECLARE the ticket's
    # clause (read off the AST) and is the seal still ABOUT this source (read off the
    # fingerprint). Sealing first and declaring after answers the first and breaks the
    # second, which is the shape ``seal_fingerprint_current`` exists to catch.
    declares = (f'PROVES = {{{boat!r}: {{"1": {_FIXTURE_TOOTH!r}}}}}\n\n\n'
                if boat else "")
    proof.write_text(
        declares +
        f'def {_FIXTURE_TOOTH}():\n'
        '    assert True\n'
        f'    print("PASS: {_FIXTURE_TOOTH}")\n\n\n'
        'if __name__ == "__main__":\n'
        f'    {_FIXTURE_TOOTH}()\n', encoding="utf-8")
    (comp / "history.json").write_text("[]", encoding="utf-8")
    (comp / "state.json").write_text(
        json.dumps({"cursor": None, "window": [], "count": 0}), encoding="utf-8")
    if seal:
        from cairn.devices.tester.device import TesterDevice
        TesterDevice().run_proof(str(proof), sink="validations", caller="cc")
    return comp, proof


# A boat that exists only inside this proof. NOT a cast id and never filed: the teeth
# below need a boat whose coverage they can build from nothing, and building six states
# onto a live voyage's name is what ``test_clearance``'s cast-registry note warns against.
_FIXTURE_BOAT = "cfa17e00b0a7"


_SECOND_TOOTH = "test_the_other_end_holds"


def _a_second_end(comp, boat, first_proof):
    """Mint, declare and seal a SECOND proof for the same boat, covering clause 2.

    A SEAM HAS ENDS IN MORE THAN ONE COMPONENT and this is the fixture shape of that: two
    proof files, one clause each, one boat. It lives here rather than inside
    ``_fixture_component`` because most teeth want the one-ended case — the two-ended one
    is a specific claim, made once, by the tooth that needs it.
    """
    other = comp / "proofs" / "test_other_end.py"
    other.write_text(
        f'PROVES = {{{boat!r}: {{"2": {_SECOND_TOOTH!r}}}}}\n\n\n'
        f'def {_SECOND_TOOTH}():\n'
        '    assert True\n'
        f'    print("PASS: {_SECOND_TOOTH}")\n\n\n'
        'if __name__ == "__main__":\n'
        f'    {_SECOND_TOOTH}()\n', encoding="utf-8")
    from cairn.devices.tester.device import TesterDevice
    tester = TesterDevice()
    tester.run_proof(str(other), sink="validations", caller="cc")
    # AND THE FIRST END IS RESEALED, because writing this file MOVED the component's
    # fingerprint and the seal already standing on the first proof is now about a tree that
    # no longer exists. That is the horizon rung doing its job — measured the first time
    # this fixture ran, where the refusal read "the code moved under the proof" and was
    # entirely correct. A fixture that left it stale would be measuring the horizon rung
    # instead of the coverage rung it is aimed at.
    tester.run_proof(str(first_proof), sink="validations", caller="cc")
    return other


@contextlib.contextmanager
def _the_boat_is_covered(comp, proof, *, boat=_FIXTURE_BOAT, second_end=None):
    """Give ``boat`` REAL coverage, and point the gate's owner read at the fixture corpus.

    THE COVERAGE RUNG IS SATISFIED, NEVER ROUTED AROUND (2026-09-09, ticket 1accdc1781aa).
    On the day the clearance gate grew its PROVED coverage rung this tooth went red, and
    the cheap repair was to aim the crossing at a target the rung does not guard. That
    would have left the tooth green over a claim it no longer makes: what it asserts is
    that a GATED crossing can actually be cleared and that the record names codemother,
    and a crossing that dodges one of the gates is not a gated crossing.

    So the coverage here is built for real, in the order the rung reads it:

    - the proof DECLARES the boat's clause (written before the seal — see
      ``_fixture_component``), and the tester has already SEALED it green;
    - ``record_hollow`` lands ``evidence.hollow[boat]`` on that standing seal with a
      NON-EMPTY tooth list, which is what says the build is not hollow;
    - the ticket's latest crossing NAMES the proof, so the rung has something to read.

    WHAT IS SUBSTITUTED IS THE CORPUS, NOT THE GATE. ``boat_owner_of`` takes its three
    roots as parameters for exactly this — its own docstring says "ONLY so a proof can
    point this at a fixture" — but ``clear`` calls it with none of them, and the defaults
    were bound at def time, so patching the module constants would do nothing. The wrapper
    below therefore calls THE REAL FUNCTION with fixture roots: every hop it makes is the
    hop the live gate makes, over files this proof wrote. The chokepoint's own named-ticket
    gate is a separate question with a separate source — existence only, via a glob that
    never opens the file — so ``_TICKETS`` is pointed at the same directory to make the
    fixture boat cast.
    """
    from cairn.devices.tester.validation_store import record_hollow
    import cairn.devices.cairn.machines.harbor_master.clearance as _clearance
    import cairn.tools.base.transitions as _transitions

    root = comp.parent
    landed = record_hollow(str(proof), boat, {"fixture.py": [_FIXTURE_TOOTH]})
    assert landed is True, (
        f"the hollow reading did not land on {proof}'s seal — the rung would refuse for a "
        "reason the fixture created, not one the gate found")
    # A SECOND END IS COVERED THE SAME WAY, NEVER EXEMPTED. Each end carries its own hollow
    # reading because the rung asks it of every proof the crossing names — an end admitted
    # on the first end's evidence would be a seam half-checked.
    if second_end is not None:
        assert record_hollow(str(second_end), boat, {"other.py": [_SECOND_TOOTH]}) is True, (
            f"the hollow reading did not land on {second_end}'s seal")

    # ``<root>/tickets`` is deliberately the shape a COMMONS has, not an arbitrary scratch
    # folder: three different readers ask where this boat lives — the owner read
    # (``tickets_dir``), the sealed handler's corpus scan (``load_tickets(commons)`` →
    # ``commons/tickets``) and ``grammar.ticket_path`` — and one directory in the commons'
    # own shape answers all three without any of them being told something different.
    tickets = root / "tickets"
    tickets.mkdir(parents=True, exist_ok=True)
    # ``<id>-<slug>.json``, WHICH IS THE FILENAME EVERY READER EXPECTS — measured the hard
    # way: a bare ``<id>.json`` resolves for ``boat_owner_of`` (it globs both ways) and for
    # ``_find_ticket``, and returns None from ``grammar.ticket_path``, whose hex branch is
    # ``<claim>-*.json`` and nothing else. Two of three readers said yes and the crossing
    # failed at the third. A fixture that is not filed the way a cast ticket is filed is a
    # fixture measuring a shape the world does not have.
    (tickets / f"{boat}-a-fixture-boat.json").write_text(json.dumps({
        "id": boat,
        "node_class": "code-seam",
        # ABSOLUTE, AND THAT IS WHAT MAKES ONE FIXTURE SERVE TWO RESOLVERS. ``os.path.join``
        # returns an absolute right-hand side unchanged, so ``boat_owner_of`` finds this
        # charter under any root it is given; and ``_resolve_component_dir`` has an explicit
        # absolute-path branch, so the sealed path derives this component's history from the
        # same field with nothing patched. A relative spelling would have needed a third
        # substitution to say the same thing twice.
        "owning_intention": str(comp / "intention+why.json"),
        "falsifier": (
            f"DONE when (1) {_FIXTURE_TOOTH} prints its PASS under the tester"
            + (f"; (2) {_SECOND_TOOTH} prints its PASS at the other end."
               if second_end is not None else ".")),
        "workflow_and_state": _FIXTURE_WORKFLOW,
        # ONE-OR-MANY, WRITTEN AS THE WORLD WRITES IT: a single-ended boat records a string
        # and a seam records a list, because that is what the live corpus holds and a
        # fixture that only ever wrote lists would not measure the string path at all.
        "crossings": [{"target": "PROVEME",
                       "proven_by": (str(proof) if second_end is None
                                     else [str(proof), str(second_end)])}],
    }), encoding="utf-8")

    real = _clearance.boat_owner_of
    real_load_class_def = _transitions.load_class_def
    saved_tickets = _transitions._TICKETS

    def _fixture_owner_of(boat_id, **kw):
        kw.setdefault("tickets_dir", str(tickets))
        kw.setdefault("cairn_root", str(root))
        kw.setdefault("commons_root", str(root))
        return real(boat_id, **kw)

    def _portable_load_class_def(node_class, *, root=None):
        """THE FOURTH CORPUS READ, and the one this fixture missed until 2026-09-09.

        The three above substitute WHERE THE BOAT LIVES. This one is where its CLASS lives:
        the gate validates the workflow string against ``code-seam.json``, and
        ``transitions._NODE_CLASSES`` names ``<this checkout>.parent / CairnCommons /
        node_classes``. That expression is right for the live tree and wrong for every
        worktree of it — see ``_commons_root`` for the measurement and the class of bug.

        A MODULE-CONSTANT PATCH WOULD DO NOTHING, which is why this is a wrapper: the root
        is a DEFAULT ARGUMENT on both ``load_class_def`` and ``emit``, bound at def time, so
        the constant is already spent by the time a fixture could reach it. And the test is
        "does the given root exist", not "did the caller pass one" — ``emit`` ALWAYS passes
        a root (its own default, which is the broken expression), so an ``or`` spelling
        would keep the broken path and change nothing. Measured: it did.

        THE REAL DEFINITION, NEVER A FIXTURE ONE. A synthetic ``code-seam.json`` written
        here would make the tooth pass by lowering the bar it measures — the workflow string
        on the fixture ticket has to conform to the class def the live corpus casts against,
        and a stub would let a drifted string through. This substitutes the ADDRESS and
        nothing else, exactly as the three wrappers above do.
        """
        if root is None or not Path(root).is_dir():
            root = _commons_root() / "node_classes"
        return real_load_class_def(node_class, root=root)

    _clearance.boat_owner_of = _fixture_owner_of
    _transitions.load_class_def = _portable_load_class_def
    _transitions._TICKETS = tickets
    try:
        yield boat
    finally:
        _clearance.boat_owner_of = real
        _transitions.load_class_def = real_load_class_def
        _transitions._TICKETS = saved_tickets


def _ask_codemother_to_cross(comp, proof, *, boat=_HARBOR_BOAT):
    """Fire ONE `cross` at codemother over the bus and return the reply body.

    This is the exact path `cairn codemother cross` walks — the CLI is a mouth over
    this request and nothing else — so the tooth measures the seam, not a helper.
    """
    from cairn.tools.bus_client import reach

    bus = reach("codemother", "harbor_master")
    # request() answers with the reply ENVELOPE; the device's answer is its body.
    reply = bus.request(
        sender="cc", to="codemother", verb="cross",
        why="proof: codemother crosses a boat as herself",
        body={"ticket": boat, "target": "PROVED", "workflow": _FIXTURE_WORKFLOW,
              "proven_by": str(proof),
              "history_path": str(comp / "history.json"),
              "state_path": str(comp / "state.json"),
              "timeout": 120.0},
        timeout=180)
    assert reply, "codemother never answered the cross request"
    return reply.get("body") or {}


def test_cross_is_a_declared_verb_on_a_real_device():
    """Clause (1)'s precondition: the verb EXISTS on the device, not just in the CLI.

    A mouth that names a verb its device does not declare is a mouth that always
    bounces — and the help text now compiles from ``declared_contract()`` for exactly
    that reason, so this tooth reads the same list the dispatcher reads."""
    from cairn.devices.codemother.shim import CodeMotherShim
    verbs = CodeMotherShim().declared_contract()["verbs"]
    assert "cross" in verbs, f"'cross' is not a declared verb; the device offers {verbs}"
    print("PASS: test_cross_is_a_declared_verb_on_a_real_device")


def test_a_crossing_codemother_admits_names_her_in_the_record():
    """FALSIFIER CLAUSE (1): the record says the hand was codemother's, not CC's.

    The whole ticket is this assertion. The crossing is fired over the bus with sender
    ``cc`` ON PURPOSE — the CLI is a person's mouth, and if the actor tracked the human
    at the keyboard the record would read 'cc' here. It reads 'codemother' because the
    hand that fires the clearance gate is the DEVICE the envelope reached, and the
    device asks the harbor as itself.

    AND THE BOAT IS COVERED, NOT EXEMPT. Until 2026-09-09 this tooth crossed
    harbor_master's own live ticket, which carries no crossings and no hollow reading —
    fine while PROVED asked only for proven-space, and a red the moment the clearance
    gate grew its coverage rung. The repair builds the coverage rather than dodging the
    rung; ``_the_boat_is_covered`` says why at length."""
    comp, proof = _fixture_component("cm_admit_", boat=_FIXTURE_BOAT)
    with _the_boat_is_covered(comp, proof) as boat:
        answer = _ask_codemother_to_cross(comp, proof, boat=boat)
    assert answer.get("accepted") is True, f"the crossing was refused: {answer}"
    assert answer.get("asked_as") == "codemother", \
        f"asked_as is {answer.get('asked_as')!r}, expected 'codemother'"
    assert answer.get("door") == "harbor_master", \
        f"door is {answer.get('door')!r}, expected 'harbor_master'"

    history = json.loads((comp / "history.json").read_text(encoding="utf-8"))
    assert len(history) == 1, f"expected exactly 1 crossing record, got {len(history)}"
    record = history[0]
    assert record.get("actor") == "codemother", \
        f"the record's actor is {record.get('actor')!r}, expected 'codemother'"
    assert record.get("cleared_by") == "codemother", \
        f"cleared_by is {record.get('cleared_by')!r}, expected 'codemother'"
    gate = record.get("clearance_gate") or ""
    assert "cleared by 'codemother'" in gate, \
        f"the clearance_gate line does not say who cleared it: {gate!r}"
    print("PASS: test_a_crossing_codemother_admits_names_her_in_the_record")


@contextlib.contextmanager
def _the_real_corpus_is_reachable():
    """Point the gate's corpus reads at the MAIN tree — for the teeth that use a REAL boat.

    ``_the_boat_is_covered`` builds a fixture commons and aims everything at it. This is the
    other case: a tooth whose boat is a genuine cast ticket, because what it measures is a
    refusal from a LATER rung and the owner rung has to resolve first for that refusal to be
    the one it sees. The defaults resolve the commons as the sibling of whatever checkout is
    running, so from a worktree the owner read finds no ticket at all and the door refuses
    ``OwnerUnresolvable`` — a refusal from the wrong rung, which reads as a red about a
    behaviour the tooth was not asking about. Measured 2026-09-09 in ``git worktree add
    /tmp/hw HEAD``: expected ``'Unproven'``, got ``'OwnerUnresolvable'``.

    NOTHING IS SOFTENED. Every root here is the operator's own — the same files the live
    gate reads — so the tooth still meets the real owner rung, the real node-class
    definition, and then the real proven-space rung that it exists to assert.
    """
    import cairn.devices.cairn.machines.harbor_master.clearance as _clearance
    import cairn.tools.base.transitions as _transitions

    commons, tree = _commons_root(), _main_tree()
    real_owner, real_load = _clearance.boat_owner_of, _transitions.load_class_def

    def _rooted_owner_of(boat_id, **kw):
        kw.setdefault("tickets_dir", str(commons / "tickets"))
        kw.setdefault("cairn_root", str(tree))
        kw.setdefault("commons_root", str(commons))
        return real_owner(boat_id, **kw)

    def _rooted_load(node_class, *, root=None):
        if root is None or not Path(root).is_dir():
            root = commons / "node_classes"
        return real_load(node_class, root=root)

    _clearance.boat_owner_of = _rooted_owner_of
    _transitions.load_class_def = _rooted_load
    try:
        yield
    finally:
        _clearance.boat_owner_of = real_owner
        _transitions.load_class_def = real_load


def test_the_door_still_refuses_an_unproven_boat_through_her():
    """FALSIFIER CLAUSE (2): reaching the door as codemother does not soften it.

    The fixture's proof is never sealed, so the boat is honestly outside proven-space
    (Law 8). The refusal must come back as DATA carrying its own class name — an
    exception cannot cross a bus envelope, and a refusal collapsed into a shrug is the
    Law 7 failure the handler was written against. And the history must be UNTOUCHED:
    a door that refuses but writes anyway has not refused."""
    comp, proof = _fixture_component("cm_refuse_", seal=False)
    with _the_real_corpus_is_reachable():
        answer = _ask_codemother_to_cross(comp, proof)
    assert answer.get("accepted") is False, f"an unproven boat was ADMITTED: {answer}"
    assert answer.get("refusal") == "Unproven", \
        f"the refusal is {answer.get('refusal')!r}, expected 'Unproven'"
    assert "proven-space" in (answer.get("reason") or ""), \
        f"the refusal does not say why: {answer.get('reason')!r}"
    history = json.loads((comp / "history.json").read_text(encoding="utf-8"))
    assert history == [], f"a refused crossing still wrote {len(history)} record(s)"
    print("PASS: test_the_door_still_refuses_an_unproven_boat_through_her")


def test_the_actor_is_the_envelopes_sender_not_the_bodys_claim():
    """The identity the gate judges is stamped by the transport, never chosen by the asker.

    If the body could name the actor, any device on the bus could claim to be any other
    and the Law 6 authority check would be deciding about a name the caller picked. The
    handler refuses a body that DISAGREES with the sender; a body that agrees is merely
    redundant. Fired straight at harbor_master so the tooth measures the door itself."""
    from cairn.tools.bus_client import reach

    bus = reach("harbor_master")
    reply = bus.request(
        sender="codemother", to="harbor_master", verb="clear",
        why="proof: the body may not name a different hand",
        body={"actor": "Akien", "workflow": _FIXTURE_WORKFLOW, "target": "PROVED",
              "boat_id": _HARBOR_BOAT, "proven_by": "/nonexistent/proof.py"},
        timeout=60)
    assert reply, "the harbor never answered the clear request"
    answer = reply.get("body") or {}
    assert answer.get("accepted") is False, \
        f"a body naming a DIFFERENT hand was accepted: {answer}"
    reason = answer.get("reason") or ""
    assert "'Akien'" in reason and "'codemother'" in reason, \
        f"the refusal does not name both hands it saw: {reason!r}"
    print("PASS: test_the_actor_is_the_envelopes_sender_not_the_bodys_claim")


def test_codemother_never_imports_the_harbor():
    """FALSIFIER CLAUSE (3): she reaches the door over the bus, never by import.

    An import would make the two devices one process at the seam and put the harbor's
    module tree inside codemother's — the standard bus contract exists so peers stay
    peers (Law 6, and the no-cross-device-imports ruling). The measure is a read of
    every .py under the device, not a grep of a single file."""
    device_root = Path(__file__).resolve().parent.parent
    offenders = []
    for py in sorted(device_root.rglob("*.py")):
        if "proofs" in py.parts or "validations" in py.parts:
            continue
        for n, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            if "harbor_master" in stripped:
                offenders.append(f"{py.relative_to(device_root)}:{n}: {stripped}")
    assert not offenders, \
        "codemother imports the harbor instead of reaching it:\n  " + "\n  ".join(offenders)
    print("PASS: test_codemother_never_imports_the_harbor")


def test_the_harbor_shim_is_reachable_by_its_own_name():
    """``reach('harbor_master')`` must find a shim that lives under a MACHINE tree.

    The resolver walked ``cairn/devices/<name>/shim.py`` and nothing else, so the
    harbor — which berths at ``cairn/devices/cairn/machines/harbor_master/`` — was
    unreachable by name and every caller had to know its path. A device that can only
    be reached by those who already know where it lives is not on the bus."""
    from cairn.tools.bus_client import reach

    bus = reach("harbor_master")
    wired = bus.list()
    assert "harbor_master" in wired, \
        f"harbor_master did not wire; the bus holds {sorted(wired)}"
    assert wired["harbor_master"].get("wired") is True, \
        f"harbor_master resolved but is not wired: {wired['harbor_master']}"
    print("PASS: test_the_harbor_shim_is_reachable_by_its_own_name")


def test_a_handler_that_posts_does_not_re_enter_its_own_mailbox():
    """THE BUG THIS VOYAGE UNCOVERED: the mail drain is re-entrant and must guard itself.

    The delivery receipt is written only AFTER ``deliver()`` returns (at-least-once —
    a raising receiver must leave the mail in the inbox), so while a handler runs its
    envelope is still ``undelivered``. Every ``request()`` posts, every post pokes the
    addressee, and the harbor's reply is addressed back to codemother — so codemother's
    ``cross`` handler poked its own mailbox mid-delivery and was handed the same envelope
    again, without bound. Measured 2026-09-09 by faulthandler on a request that never
    returned.

    The tooth drives the cycle directly: a shim whose deliver() re-enters the drain (the
    poke a post causes) must see its envelope EXACTLY ONCE. Without the guard this is a
    RecursionError, which is what the un-fixed shim actually did."""
    from cairn.tools.base.shim import BaseShim

    envelope = {"id": "env-1", "to": "a_fixture_device", "sender": "cc", "verb": "poke"}

    class _OneEnvelopeBus:
        """The narrowest bus that can show the cycle: mail stays undelivered until receipted."""

        def __init__(self):
            self.receipted = False

        def undelivered(self, to=None, limit=None):
            return [] if self.receipted else [dict(envelope)]

        def record_delivery(self, eid, to=None, by=None):
            self.receipted = True

    class _PostingShim(BaseShim):
        @property
        def device_id(self):
            return "a_fixture_device"

        def __init__(self, bus):
            super().__init__(bus=bus)
            self.seen = []

        def deliver(self, env):
            self.seen.append(env["id"])
            # what post() does to the addressee, inlined: the poke drains the mailbox
            self._check_mail()

    shim = _PostingShim(_OneEnvelopeBus())
    shim._check_mail()
    assert shim.seen == ["env-1"], \
        f"the envelope was delivered {len(shim.seen)} time(s), expected exactly 1: {shim.seen}"
    print("PASS: test_a_handler_that_posts_does_not_re_enter_its_own_mailbox")


def test_a_history_that_is_not_a_list_is_refused_by_name():
    """THE SECOND BUG THIS VOYAGE UNCOVERED: a bad history died four frames from its cause.

    A history.json written as an object loaded fine in ``read_history`` and then died
    inside ``project`` as ``KeyError: -1`` — a diagnostic surface saying nothing about
    which file was wrong or what shape it should have had (Law 7). The list shape is
    load-bearing everywhere below (append splats it, _window slices it, project indexes
    [-1]), so the read is where it gets asserted."""
    from cairn.devices.tester.scratch import scratch_dir
    from cairn.tools.charter import projector

    bad = Path(scratch_dir("cm_badhistory_")) / "history.json"
    bad.write_text(json.dumps({"records": []}), encoding="utf-8")
    try:
        projector.read_history(str(bad))
    except ValueError as e:
        message = str(e)
    else:
        raise AssertionError("a history that is not a list was read without complaint")
    assert str(bad) in message, f"the refusal does not name the file: {message!r}"
    assert "dict" in message, f"the refusal does not say what it found: {message!r}"
    assert "LIST" in message, f"the refusal does not say what a history is: {message!r}"
    print("PASS: test_a_history_that_is_not_a_list_is_refused_by_name")


# ══════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════
# 14. A GREEN SEAL CROSSES THE BOAT IT PROVES
#     ticket 1accdc1781aa — clauses (2) and (5) of the falsifier. Clause (1)
#     and (4) are the tester's end of the seam and berth with it
#     (cairn/devices/tester/proofs/test_the_seal_announces_itself.py);
#     clause (3) is the harbor's and berths with the gate
#     (cairn/devices/cairn/machines/harbor_master/proofs/test_clearance.py).
#     A seam has ends in more than one component, and `proven_by` is read as
#     one-or-many for exactly this reason.
# ══════════════════════════════════════════════════════════════════════════

@contextlib.contextmanager
def _the_sealed_path_can_find_the_boat(comp, boat=_FIXTURE_BOAT):
    """Point the sealed handler's two corpus reads at the fixture commons.

    WHAT IS SUBSTITUTED IS THE CORPUS, NOT A GATE — the same line ``_the_boat_is_covered``
    draws, and it matters more here because this tooth walks the whole seam. Two reads ask
    the world where a boat lives: ``_boats_named_on`` scans ``load_tickets(_COMMONS)`` for
    tickets standing at PROVEME, and ``_crossing_coordinates`` asks ``grammar.ticket_path``
    for the file so it can derive the workflow and the component's history. Both are
    pointed at ``<root>/tickets`` — the fixture ticket, in the commons' own shape.

    EVERYTHING ELSE RUNS FOR REAL: the bus request, the harbor's clearance gate with its
    authority check, its proven-space check, its PROVED coverage rung, the entry and exit
    gates, and the journal write. What a fixture may not do is put a manufactured PROVEME
    state onto a live voyage's name — measured 2026-09-09, the corpus holds ZERO tickets at
    PROVEME, so there is no real boat this handler could have been fired at.

    ``grammar.ticket_path`` is replaced by a WRAPPER around the real function rather than a
    stub: the lookup it performs — hex-id glob, whole-slug match, the 2026-09-09 narrowing —
    is logic this tooth wants exercised, not logic it wants to reimplement.
    """
    import cairn.devices.codemother.shim as _shim
    import cairn.tools.chain.grammar as _grammar

    root = comp.parent
    real_ticket_path = _grammar.ticket_path
    saved_commons = _shim._COMMONS

    def _fixture_ticket_path(claim, *args, **kw):
        # ``*args`` because ``root`` is POSITIONAL on the real signature and callers pass it
        # that way; swallowing it into keywords would make this wrapper refuse a call the
        # real function accepts.
        kw.setdefault("tickets_dir", str(root / "tickets"))
        return real_ticket_path(claim, *args, **kw)

    _grammar.ticket_path = _fixture_ticket_path
    _shim._COMMONS = root
    try:
        yield boat
    finally:
        _grammar.ticket_path = real_ticket_path
        _shim._COMMONS = saved_commons


def _tell_codemother_a_seal_landed(proof, *, verdict="green"):
    """Post one `sealed` message at codemother and return her answer.

    Sent as ``tester`` because that is who sends it in the world — ``cairn test --seal``
    is the only caller — and over ``request`` rather than ``post`` only so this tooth can
    read the answer. The handler cannot tell the difference: it reads the envelope's body
    and returns a dict either way, which is what clause (4)'s tooth relies on when the
    same message arrives by ``post`` and is drained off the mailbox instead.
    """
    from cairn.tools.bus_client import reach

    bus = reach("codemother", "harbor_master")
    reply = bus.request(
        sender="tester", to="codemother", verb="sealed",
        why=f"proof: a green seal on {proof} crosses the boat it proves",
        body={"proof": str(proof), "verdict": verdict,
              "source_fingerprint": "", "validations_path": ""},
        timeout=180)
    assert reply, "codemother never answered the sealed message"
    return reply.get("body") or {}


def _troubles_now():
    """How many trouble files stand in the commons right now. n=1 measurements, both ends.

    THROUGH ``_commons_root`` AND NOT THE SIBLING GUESS, because the guess made this
    function a hollow green rather than a red: in a worktree it named a directory that does
    not exist, ``is_dir()`` returned False, and BOTH readings came back 0 — so "no trouble
    was raised" was true of an empty set the tooth was never looking at. That is the
    coin-toss shape (a check that passes for the wrong reason), and it is worse here than
    the crossing bug above, which at least failed loudly.
    """
    troubles = _commons_root() / "troubles"
    return len(list(troubles.glob("*.json"))) if troubles.is_dir() else 0


def test_a_green_seal_crosses_the_PROVEME_boat_that_NAMES_that_proof():
    """FALSIFIER CLAUSE (2): the seal crosses the boat, and the record says codemother did it.

    THE DEFECT THIS ENDS, measured 2026-09-07: twelve tickets stood at PROVEME with a green
    seal already on the proof they named. Nothing was wrong with any of them — the proof had
    run, the seal had landed, the coverage was there. The crossing simply required a hand to
    remember, and twelve times nobody did. So the seal announces itself and the boat moves on
    the announcement.

    The whole seam is fired, end to end: a ``sealed`` message arrives at codemother, she finds
    the boat that named the proof, and she asks the HARBOR to cross it — as herself, over the
    bus, through the gate. She decides nothing about whether it may cross; the gate does, and
    it is the same gate with the same coverage rung a hand would have met.
    """
    comp, proof = _fixture_component("cm_sealed_", boat=_FIXTURE_BOAT)
    with _the_boat_is_covered(comp, proof) as boat,             _the_sealed_path_can_find_the_boat(comp, boat):
        answer = _tell_codemother_a_seal_landed(proof)

    assert answer.get("accepted") is True, f"the sealed message was refused: {answer}"
    assert answer.get("crossed") == [boat],         f"crossed is {answer.get('crossed')!r}, expected [{boat!r}]; refused={answer.get('refused')!r}"
    assert answer.get("refused") == [], f"a crossing was refused: {answer.get('refused')!r}"

    history = json.loads((comp / "history.json").read_text(encoding="utf-8"))
    assert len(history) == 1, f"expected exactly 1 crossing record, got {len(history)}"
    record = history[0]
    assert record.get("cleared_by") == "codemother",         f"cleared_by is {record.get('cleared_by')!r} — the record does not say whose hand it was"
    assert "PROVED" in (record.get("workflow_and_state") or record.get("to") or ""), record
    print("PASS: test_a_green_seal_crosses_the_PROVEME_boat_that_NAMES_that_proof")


def test_a_seal_NO_PROVEME_TICKET_NAMES_crosses_nothing_and_troubles_nobody():
    """FALSIFIER CLAUSE (5): the quiet case, and it must stay quiet.

    Most seals are this one. ``cairn test --seal`` over the corpus lands dozens of green
    seals on proofs no boat at PROVEME is waiting on, and the handler must answer each with
    a shrug: no crossing, and NO TROUBLE. A trouble raised here would be the loudest kind of
    Law 7 failure — a diagnostic surface reporting a problem that does not exist, once per
    proof per run, until nobody reads the surface at all.

    The corpus is the REAL one, deliberately: this tooth's claim is about a proof nothing
    names, and the strongest fixture for 'nothing names it' is a proof minted seconds ago in
    scratch, checked against every ticket actually on file."""
    comp, proof = _fixture_component("cm_unnamed_")
    before = _troubles_now()
    answer = _tell_codemother_a_seal_landed(proof)
    after = _troubles_now()

    assert answer.get("accepted") is True, f"the sealed message was refused: {answer}"
    assert answer.get("crossed") == [],         f"a proof no boat names crossed something: {answer.get('crossed')!r}"
    assert answer.get("refused") == [],         f"a proof no boat names produced a refusal: {answer.get('refused')!r}"
    assert after == before,         f"the quiet case raised {after - before} trouble(s) — a surface that cries at every seal"
    history = json.loads((comp / "history.json").read_text(encoding="utf-8"))
    assert history == [], f"nothing was named, yet {len(history)} crossing(s) were journaled"
    print("PASS: test_a_seal_NO_PROVEME_TICKET_NAMES_crosses_nothing_and_troubles_nobody")


def test_a_TWO_ENDED_SEAM_crosses_carrying_BOTH_ends_not_just_the_one_that_sealed():
    """THE DEFECT THIS VOYAGE UNCOVERED IN ITS OWN BUILD, fixed under the bounds ruling
    2026-09-09-a-bug-the-voyage-uncovers-is-fixed-by-that-voyage.

    ``_handle_sealed`` passed the ONE proof that had just sealed as the crossing's
    ``proven_by``. Everywhere else in this path the field is read as one-or-many precisely
    because a seam has ends in more than one component, and the crossing is the RECORD OF
    TRUTH about what this move was cleared onto — so a record naming one end of a two-ended
    seam claims less than the gate actually verified, and a reader a year out goes and looks
    at half the evidence (Law 5: the proof shares the address; Law 7: a record of truth never
    collapses).

    FOUND BY BUILDING THIS TICKET, not by reading the code: ``1accdc1781aa``'s own five
    clauses live in three files. The fix is one line of intent — the crossing carries what
    the BOAT declared, and the seal is only the event that says now.

    WHAT ACTUALLY BITES, MEASURED 2026-09-09 rather than assumed. This docstring first
    claimed the single-proof spelling would red at ``clause_declared``. IT DOES NOT, and the
    reason is worth keeping: ``_coverage_lacks`` composes ``coverage_lacks(ticket, ...)``,
    which reads the clause-to-tooth join off THE TICKET'S OWN crossings, not off the list
    this call passes — so the clause rung sees both ends however the caller spells the
    crossing. The list is used by ``hollow_lacks(ticket, named)`` alone. So the single-proof
    spelling loses two things and neither of them is clause coverage: the hollow reading is
    never demanded of the unnamed end, and the record on disk names one proof of two. The
    assertion below is the second one, and reverting the fix reds it verbatim:
    ``the record names '.../test_fixture.py' — a seam's crossing must name every end``."""
    comp, proof = _fixture_component("cm_two_ends_", boat=_FIXTURE_BOAT)
    other = _a_second_end(comp, _FIXTURE_BOAT, proof)
    with _the_boat_is_covered(comp, proof, second_end=other) as boat, \
            _the_sealed_path_can_find_the_boat(comp, boat):
        # SEALED ON ONE END ONLY — which is the real shape: a builder reseals the file they
        # touched, and the boat is proved by all of its ends.
        answer = _tell_codemother_a_seal_landed(proof)

    assert answer.get("accepted") is True, f"the sealed message was refused: {answer}"
    assert answer.get("refused") == [], (
        f"a two-ended seam was refused: {answer.get('refused')}")
    assert answer.get("crossed") == [boat], (
        f"expected the two-ended boat to cross, got {answer.get('crossed')}")

    history = json.loads((comp / "history.json").read_text(encoding="utf-8"))
    assert len(history) == 1, f"expected one crossing record, got {len(history)}: {history}"
    named = history[0].get("proven_by")
    assert isinstance(named, list) and {str(proof), str(other)} == {str(one) for one in named}, (
        f"the record names {named!r} — a seam's crossing must name every end, or the record "
        "claims less than the gate verified")
    print("PASS: test_a_TWO_ENDED_SEAM_crosses_carrying_BOTH_ends_not_just_the_one_that_sealed")


def test_a_RED_seal_crosses_nothing_at_all():
    """The clause-(5) neighbour the ticket's WRONG INTENT depends on: red never moves a boat.

    Not a clause of its own, and it is here because the WRONG INTENT clause is *'a boat
    auto-crossed to PROVED is later redded by Akien'* — the one shape that must be
    impossible for this path to produce on its own is a RED measurement moving anything.
    The handler answers before it ever looks for a boat, so a red seal cannot even reach the
    corpus scan."""
    comp, proof = _fixture_component("cm_red_seal_", boat=_FIXTURE_BOAT)
    with _the_boat_is_covered(comp, proof) as boat,             _the_sealed_path_can_find_the_boat(comp, boat):
        answer = _tell_codemother_a_seal_landed(proof, verdict="red")
    assert answer.get("accepted") is True, answer
    assert answer.get("crossed") == [],         f"a RED seal crossed {answer.get('crossed')!r} — the boat moved on a failed measurement"
    history = json.loads((comp / "history.json").read_text(encoding="utf-8"))
    assert history == [], f"a RED seal journaled {len(history)} crossing(s)"
    print("PASS: test_a_RED_seal_crosses_nothing_at_all")

if __name__ == "__main__":
    tests = [
        test_shim_imports_and_has_correct_device_id,
        test_charter_exists_and_is_valid,
        test_probe_loads,
        test_positive_and_negative_types_are_distinct,
        test_type_roundtrip,
        test_unify_distinguishes_positive_from_negative,
        test_schema_is_project_agnostic,
        test_projects_are_isolated,
        test_vocabulary_loads,
        test_vocabulary_validates_against_type_schema,
        test_vocabulary_is_project_agnostic,
        test_mine_produces_types_from_cairn,
        test_ingest_memory_files,
        test_compiler_deduplicates_by_why,
        test_constraint_proof_lifecycle,
        test_challenge_catches_known_violation,
        test_query_returns_relevant_types,
        test_digest_consolidates,
        test_cross_is_a_declared_verb_on_a_real_device,
        test_a_crossing_codemother_admits_names_her_in_the_record,
        test_the_door_still_refuses_an_unproven_boat_through_her,
        test_the_actor_is_the_envelopes_sender_not_the_bodys_claim,
        test_codemother_never_imports_the_harbor,
        test_the_harbor_shim_is_reachable_by_its_own_name,
        test_a_handler_that_posts_does_not_re_enter_its_own_mailbox,
        test_a_history_that_is_not_a_list_is_refused_by_name,
        test_a_green_seal_crosses_the_PROVEME_boat_that_NAMES_that_proof,
        test_a_seal_NO_PROVEME_TICKET_NAMES_crosses_nothing_and_troubles_nobody,
        test_a_TWO_ENDED_SEAM_crosses_carrying_BOTH_ends_not_just_the_one_that_sealed,
        test_a_RED_seal_crosses_nothing_at_all,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    if failed:
        sys.exit(1)
