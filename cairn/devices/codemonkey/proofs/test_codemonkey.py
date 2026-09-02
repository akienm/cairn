"""Proofs for the CodeMonkey device — teeth a hollow build couldn't pass.

Covers: device skeleton, type system, per-project isolation, vocabulary,
mine, ingest, constraints compiler, constraint proof lifecycle, challenge,
query, and digest.
"""

import json
import os
import sys
from pathlib import Path

from cairn.devices.tester.scratch import scratch_dir

# ── helpers ──────────────────────────────────────────────────────────────

def _tmp_project_root():
    """Create a temp directory that looks like a project root."""
    d = str(scratch_dir("codemonkey_test_"))
    for sub in ("types", "constraints", "mining"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    return d


# ══════════════════════════════════════════════════════════════════════════
# 1. DEVICE SKELETON
# ══════════════════════════════════════════════════════════════════════════

def test_shim_imports_and_has_correct_device_id():
    from cairn.devices.codemonkey.shim import CodeMonkeyShim
    s = CodeMonkeyShim()
    assert s.device_id == "codemonkey", f"device_id is {s.device_id!r}, expected 'codemonkey'"
    assert isinstance(s.probes(), list), "probes() must return a list"
    print("PASS: shim imports, device_id='codemonkey', probes() returns list")


def test_charter_exists_and_is_valid():
    charter_path = Path(__file__).parent.parent / "intention+why.json"
    assert charter_path.exists(), f"charter not found at {charter_path}"
    data = json.loads(charter_path.read_text())
    assert data["component"] == "codemonkey", f"charter component is {data['component']!r}"
    assert "falsifier" in data, "charter has no falsifier"
    assert "why" in data, "charter has no why"
    print("PASS: charter exists, component='codemonkey', has falsifier and why")


def test_probe_loads():
    from cairn.devices.codemonkey.probes.the_shim_delivers_mail import PROBE
    assert PROBE is not None, "PROBE is None"
    assert PROBE.why, "PROBE has no why"
    assert callable(PROBE.trigger), "PROBE trigger is not callable"
    print("PASS: probe loads, has why, trigger is callable")


# ══════════════════════════════════════════════════════════════════════════
# 2. TYPE SYSTEM
# ══════════════════════════════════════════════════════════════════════════

def test_positive_and_negative_types_are_distinct():
    from cairn.devices.codemonkey.types import positive, negative, TypePolarity
    p = positive("test-pos", "a positive pattern")
    n = negative("test-neg", "a negative pattern")
    assert p.polarity == TypePolarity.POSITIVE
    assert n.polarity == TypePolarity.NEGATIVE
    assert p.polarity != n.polarity, "positive and negative must be distinct"
    print("PASS: positive and negative types are distinct")


def test_type_roundtrip():
    from cairn.devices.codemonkey.types import positive, PatternType, PatternSignal
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
    from cairn.devices.codemonkey.types import positive, negative, PatternSignal
    from cairn.devices.codemonkey.unify import unify

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
    from cairn.devices.codemonkey.types import PatternType
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
    from cairn.devices.codemonkey.types import negative, PatternSignal
    from cairn.devices.codemonkey.project import (
        ensure_project, save_type, load_types, _PROJECTS_ROOT,
    )
    import cairn.devices.codemonkey.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemonkey_proj_")
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
    from cairn.devices.codemonkey.vocabulary import load_catalog, catalog_names
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
    from cairn.devices.codemonkey.vocabulary import load_catalog
    from cairn.devices.codemonkey.types import PatternType
    catalog = load_catalog()
    for entry in catalog:
        assert isinstance(entry, PatternType), f"{entry.name} is not a PatternType"
        d = entry.to_dict()
        restored = PatternType.from_dict(d)
        assert restored.name == entry.name
    print(f"PASS: all {len(catalog)} vocabulary entries validate against the type schema")


def test_vocabulary_is_project_agnostic():
    from cairn.devices.codemonkey.vocabulary import load_catalog
    catalog = load_catalog()
    for entry in catalog:
        assert entry.scope in ("", "universal"), \
            f"{entry.name} has non-universal scope: {entry.scope!r}"
    print("PASS: all vocabulary entries are project-agnostic")


# ══════════════════════════════════════════════════════════════════════════
# 5. MINE
# ══════════════════════════════════════════════════════════════════════════

def test_mine_produces_types_from_cairn():
    from cairn.devices.codemonkey.mine import scan_structure, derive_types
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
    from cairn.devices.codemonkey.ingest import ingest_memory_files
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
    from cairn.devices.codemonkey.types import negative, PatternSignal
    from cairn.devices.codemonkey.project import ensure_project, save_type, load_types
    from cairn.devices.codemonkey.constraints_compiler import compile_constraints
    import cairn.devices.codemonkey.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemonkey_compiler_")
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
    from cairn.devices.codemonkey.constraint_proof import (
        ConstraintProof, save_proof, load_proof,
    )
    tmp = scratch_dir("codemonkey_proof_")
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
    from cairn.devices.codemonkey.types import negative, positive, PatternSignal
    from cairn.devices.codemonkey.project import ensure_project, save_type
    from cairn.devices.codemonkey.challenge import challenge
    import cairn.devices.codemonkey.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemonkey_challenge_")
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

        clean_result = challenge(["creating a new file in codemonkey/"], "test-challenge")
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
    from cairn.devices.codemonkey.types import negative, positive, PatternSignal
    from cairn.devices.codemonkey.project import ensure_project, save_type
    from cairn.devices.codemonkey.query import query
    import cairn.devices.codemonkey.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemonkey_query_")
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
    from cairn.devices.codemonkey.types import negative, PatternSignal
    from cairn.devices.codemonkey.project import ensure_project, save_type
    from cairn.devices.codemonkey.digest import digest
    import cairn.devices.codemonkey.project as proj_mod

    original_root = proj_mod._PROJECTS_ROOT
    tmp = scratch_dir("codemonkey_digest_")
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
# RUNNER
# ══════════════════════════════════════════════════════════════════════════

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
