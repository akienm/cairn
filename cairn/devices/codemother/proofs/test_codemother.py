"""Proofs for the CodeMother device — teeth a hollow build couldn't pass.

Covers: device skeleton, type system, per-project isolation, vocabulary,
mine, ingest, constraints compiler, constraint proof lifecycle, challenge,
query, and digest.
"""

import json
import os
import sys
from pathlib import Path

from cairn.devices.tester.scratch import scratch_dir

# WHICH TICKET CLAUSES THESE TEETH COVER — read out of the AST by
# cairn/tools/proof_coverage, never by importing this module. The join is the
# intersection of three things already on disk: the ticket's clauses, this
# declaration, and the teeth the seal records as actually printed.
PROVES = {
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


def _fixture_component(tag, *, seal=True):
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
    proof.write_text(
        'def test_nothing_is_nothing():\n'
        '    assert True\n'
        '    print("PASS: test_nothing_is_nothing")\n\n\n'
        'if __name__ == "__main__":\n'
        '    test_nothing_is_nothing()\n', encoding="utf-8")
    (comp / "history.json").write_text("[]", encoding="utf-8")
    (comp / "state.json").write_text(
        json.dumps({"cursor": None, "window": [], "count": 0}), encoding="utf-8")
    if seal:
        from cairn.devices.tester.device import TesterDevice
        TesterDevice().run_proof(str(proof), sink="validations", caller="cc")
    return comp, proof


def _ask_codemother_to_cross(comp, proof, *, boat=_HARBOR_BOAT):
    """Fire ONE `cross` at codemother over the bus and return the reply body.

    This is the exact path `cairn codemother cross` walks — the CLI is a mouth over
    this request and nothing else — so the tooth measures the seam, not a helper.
    """
    from cairn.tools.base.bus_client import reach

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
    device asks the harbor as itself."""
    comp, proof = _fixture_component("cm_admit_")
    answer = _ask_codemother_to_cross(comp, proof)
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


def test_the_door_still_refuses_an_unproven_boat_through_her():
    """FALSIFIER CLAUSE (2): reaching the door as codemother does not soften it.

    The fixture's proof is never sealed, so the boat is honestly outside proven-space
    (Law 8). The refusal must come back as DATA carrying its own class name — an
    exception cannot cross a bus envelope, and a refusal collapsed into a shrug is the
    Law 7 failure the handler was written against. And the history must be UNTOUCHED:
    a door that refuses but writes anyway has not refused."""
    comp, proof = _fixture_component("cm_refuse_", seal=False)
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
    from cairn.tools.base.bus_client import reach

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
    from cairn.tools.base.bus_client import reach

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
