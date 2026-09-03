"""Proof: the survey brick — the second stackable learning brick built UNDER
pre-installed judges (survey-filters, PROVED before this module existed — the
judges-before-the-judged pattern's proving second instance).

Teeth a hollow build could not pass:
  - THE CHAIN IS PHYSICS AT DEPTH 3: stage 3 refuses without a berthed, readable
    stage-2 packet — AND refuses when that packet's own intent_ref (the stage-1
    link) is gone or unreadable. A broken link anywhere is loud, never a
    shallow fill.
  - THE FLOOR SURFACES THE CENSUS VERBATIM: each component ref's device_census
    row travels as measured (proofs counted, charter flag, devices) — survey
    reads MEASURED state, not authored charters (constrain owns those); a
    non-component ref is existence-measured, found vs missing kept apart.
  - THE SCHEMA GATE REFUSES what a hollow build would emit: missing fields, bad
    confidence, uncovered provenance, an unfiled ticket claim.
  - THE DOOR COMPOSES THE INSTALLED JUDGES: a phantom holding, an empty sought,
    a measureless absence — each refused AT THE BERTH by the same judge_survey
    the promotion gate runs — asserted by identity, not parallel behavior. And
    the inspector never imports survey.
  - THE BERTH LANDS AND ROUND-TRIPS; a refused packet leaves nothing behind.
  - THE DEPOSIT-BACK IS GATED: content is the ONE rendering (intent + the
    inventory), the berth must exist on disk, refusals leave the tree standing.
  - IMPORT ALLOWLIST over orient's import_map: survey.py composes exactly four
    cairn doors — the inspector's judge, chart's settled orient machinery,
    chart's tree verbs, and the orient INSTRUMENT (device_census — survey is the
    sweep stage; the settled measurer is its floor). No parallel scan, no db,
    no network.

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/devices/codemother/machines/survey/proofs/test_chart_survey.py     # exit 0 = green
"""
from __future__ import annotations

import json
import os
import pytest
import shutil
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import cairn.machines.build_inspector.inspector as inspector_mod
from cairn.devices.codemother.machines.survey import survey as survey_mod
from cairn.devices.codemother.machines.survey.survey import (
    AUTHORED_FIELDS, SurveyRefused, deposit_survey, survey_floor,
    survey_node_content, validate_survey, write_survey,
)
from cairn.tools.chain.grammar import component_of, component_roster
from cairn.tools.tree.tree import nexus_table
from cairn.devices.db_domain import store
from cairn.devices.librarian import trees
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

_NEXUS = f"survey_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"


def make_root():
    """A synthetic world: two components (alpha chartered with a proof, beta
    bare code), a berthed orient packet, and a berthed constrain packet chained
    to it — the two links stage 3 fills through."""
    tmp = str(scratch_dir("chart_survey_proof_"))
    root = os.path.join(tmp, "repo")
    # A commons sibling: the floor must resolve refs by the GATE'S semantics
    # (commons fallback included) — its first live fire reported filed tickets
    # as missing because its first cast checked a narrower world (a false
    # absence, this brick's own failure class; cured and pinned same day).
    os.makedirs(os.path.join(tmp, "CairnCommons", "tickets"))
    with open(os.path.join(tmp, "CairnCommons", "tickets", "filed.json"), "w") as fh:
        fh.write("{}\n")
    for comp in ("alpha", "beta"):
        os.makedirs(os.path.join(root, "cairn", comp))
        with open(os.path.join(root, "cairn", comp, comp + ".py"), "w") as fh:
            fh.write("x = 1\n")
    with open(os.path.join(root, "cairn", "alpha", "intention+why.json"), "w") as fh:
        json.dump({"component": "alpha", "falsifier": "RED if hollow"}, fh)
    os.makedirs(os.path.join(root, "cairn", "alpha", "proofs"))
    with open(os.path.join(root, "cairn", "alpha", "proofs", "test_a.py"), "w") as fh:
        fh.write("assert True\n")
    berth_dir = os.path.join(root, "instance", "packets")
    os.makedirs(berth_dir)
    orient_berth = os.path.join(berth_dir, "orient-20260728T170000-feedfeedfeed.json")
    with open(orient_berth, "w") as fh:
        json.dump({"intent": "sweep the alpha territory",
                   "domain": "alpha", "scope": "IN: alpha. OUT: beta.",
                   # PATH-SHAPED, because that is what the orient floor AUTHORS
                   # since 2026-08-14 — this fixture said "alpha" (a bare name)
                   # until 2026-08-17, which is why every test below stayed green
                   # for three days while the real stratum was dead. A fixture
                   # that agrees with the READER instead of the WRITER cannot
                   # fail. test_the_fixture_speaks_what_the_orient_floor_AUTHORS
                   # binds this shape to its producer so it cannot drift again.
                   "refs": ["cairn/alpha", "cairn/alpha/alpha.py",
                            "tickets/filed.json", "no/such/path.py"],
                   "unknowns": [], "confidence": 0.8,
                   "provenance": {"intent": "cc", "domain": "cc",
                                  "scope": "cc", "refs": "floor",
                                  "unknowns": "cc"}}, fh)
    constrain_berth = os.path.join(berth_dir, "constrain-20260728T170001-cafecafecafe.json")
    with open(constrain_berth, "w") as fh:
        json.dump({"intent_ref": orient_berth,
                   "constraints": [{"text": "alpha only", "source": "alpha",
                                    "kind": "charter"}],
                   "bounds": {"in": ["alpha"], "out": ["beta"]},
                   "unknowns": [], "confidence": 0.75,
                   "provenance": {"intent_ref": "floor", "constraints": "cc",
                                  "bounds": "cc", "unknowns": "cc"}}, fh)
    return root, orient_berth, constrain_berth


@pytest.fixture
def _world():
    return make_root()


@pytest.fixture
def root(_world):
    return _world[0]


@pytest.fixture
def orient_berth(_world):
    return _world[1]


@pytest.fixture
def constrain_berth(_world):
    return _world[2]


def good_packet(constrain_berth):
    return {
        "constrain_ref": constrain_berth,
        "sought": ["the settled chart machinery", "a prior sweep of this class"],
        # The address resolves against the REAL world — the judges are root-blind
        # by design (same shape as the constrain proof's real 'source').
        "holdings": [{"what": "the settled chart machinery",
                      # A LIVE address: judge_survey resolves a holding against the
                      # real roster, and "chart" stopped being a component on
                      # 2026-08-13 when the decomposition made it a skill.
                      "address": "base"}],
        "absences": [{"what": "a prior sweep of this class",
                      "measure": "survey tree walk returned no node over the floor"}],
        "unknowns": ["whether beta consumes alpha's output"],
        "confidence": 0.7,
        "provenance": {"constrain_ref": "floor", "sought": "cc",
                       "holdings": "floor", "absences": "cc",
                       "unknowns": "cc"},
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except SurveyRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected SurveyRefused mentioning %r, got none" % needle)


def test_the_chain_is_physics_at_depth_3(root, orient_berth, constrain_berth):
    expect_refusal(lambda: survey_floor(os.path.join(root, "no-berth.json")),
                   "not a berthed packet")
    not_constrain = os.path.join(root, "not_constrain.json")
    with open(not_constrain, "w") as fh:
        json.dump({"weird": True}, fh)
    expect_refusal(lambda: survey_floor(not_constrain), "not a constrain berth")
    # The deep link: a constrain berth whose orient berth is GONE refuses loudly.
    orphan = os.path.join(root, "orphan_constrain.json")
    with open(orphan, "w") as fh:
        json.dump({"intent_ref": os.path.join(root, "gone.json"),
                   "bounds": {"in": ["x"], "out": ["y"]}}, fh)
    expect_refusal(lambda: survey_floor(orphan), "the chain broke")
    # ...and one whose orient berth is unreadable refuses just as loudly.
    broken_orient = os.path.join(root, "broken_orient.json")
    with open(broken_orient, "w") as fh:
        fh.write("{not json")
    snapped = os.path.join(root, "snapped_constrain.json")
    with open(snapped, "w") as fh:
        json.dump({"intent_ref": broken_orient,
                   "bounds": {"in": ["x"], "out": ["y"]}}, fh)
    expect_refusal(lambda: survey_floor(snapped), "the chain broke")
    p = good_packet(constrain_berth)
    p["constrain_ref"] = os.path.join(root, "no-berth.json")
    expect_refusal(lambda: validate_survey(p, root=root), "not a berthed packet")


def test_floor_surfaces_the_census_verbatim(root, orient_berth, constrain_berth):
    facts = survey_floor(constrain_berth, root=root)
    assert facts["stratum"] == "floor"
    assert facts["intent"] == "sweep the alpha territory", \
        "the chain carries the upstream intent through both links"
    assert facts["bounds"] == {"in": ["alpha"], "out": ["beta"]}, \
        "the sweep runs inside stage 2's bounds — they travel with the floor"
    rows = {r["component"]: r for r in facts["census_rows"]}
    assert facts["census_rows"], \
        "THE STRATUM IS ALIVE — census_rows empty means every component ref fell " \
        "through to ref_exists(), which PASSES, so the packet looks healthy while " \
        "the deterministic half measured nothing (the 2026-08-14..17 silent hole)"
    assert list(rows) == ["alpha"], \
        "only chartered components ride the roster (beta is bare code)"
    assert rows["alpha"]["charter_on_disk"] is True
    assert rows["alpha"]["proofs"] == 1, \
        "the census row travels VERBATIM — measured facts, not a paraphrase"
    assert facts["refs_found"] == ["cairn/alpha/alpha.py", "tickets/filed.json"], \
        "found rides the GATE'S resolution semantics — a commons-filed ref " \
        "reported missing is a false absence (the floor's own first live-fire bug)"
    assert facts["refs_missing"] == ["no/such/path.py"], \
        "a ref the world lacks is reported missing, never silently dropped"


def test_the_fixture_speaks_what_the_orient_floor_AUTHORS(root, orient_berth,
                                                        constrain_berth):
    """THE SEAM'S TWO ENDS, EACH READ FROM ITS OWN DECLARATION — the tooth that
    would have caught the silent hole on the day it opened.

    Every other test here runs against a hand-written orient berth, so they prove
    what survey does with the shape the FIXTURE chose. That is worth nothing when
    the question is whether the fixture still matches its producer: on 2026-08-14
    the orient floor started authoring refs as repo-relative paths, the fixture went
    on saying "alpha", and survey's whole deterministic stratum died SILENTLY with
    every test green.

    So this one calls the real writer and asserts the INVARIANT rather than a
    snapshot: whatever the orient floor authors as a component ref, ``component_of``
    resolves to a name the census keys by. It never pins the exact strings — pinning
    output is how a proof starts re-asserting today's accident.

    Takes the synthetic world's handles for the runner's sake and uses NONE of
    them: the whole question is what the REAL orient floor authors against the
    REAL roster, and a fixture cannot answer a question about fixtures."""
    from cairn.devices.codemother.machines.orient.orient import floor_packet

    authored = floor_packet("survey the aider_shim device and the tester")
    refs = authored.get("refs") or []
    assert refs, "the orient floor grounded no refs for a request naming two live " \
                 "components — if this is honest the seam cannot be tested here"
    resolved = [(r, component_of(r)) for r in refs]
    named = [(r, n) for r, n in resolved if n is not None]
    assert named, (
        "NOT ONE ref the orient floor authored resolves to a component the census "
        "can key. That is the silent hole, reopened: %r" % (resolved,))
    for ref, name in named:
        assert name in set(component_roster()), \
            "component_of(%r) -> %r, which is not on the roster the census keys by" \
            % (ref, name)


def test_schema_gate_refuses_hollow_shapes(root, orient_berth, constrain_berth):
    missing = good_packet(constrain_berth)
    del missing["sought"]
    expect_refusal(lambda: validate_survey(missing, root=root), "sought")
    unlisted = dict(good_packet(constrain_berth), holdings="not a list")
    expect_refusal(lambda: validate_survey(unlisted, root=root), "must be a list")
    over = dict(good_packet(constrain_berth), confidence=2.0)
    expect_refusal(lambda: validate_survey(over, root=root), "confidence")
    uncovered = good_packet(constrain_berth)
    del uncovered["provenance"]["absences"]
    expect_refusal(lambda: validate_survey(uncovered, root=root), "absences")
    minted_ticket = dict(good_packet(constrain_berth), ticket="no-such-ticket")
    expect_refusal(lambda: validate_survey(minted_ticket, root=root), "no-such-ticket")


def test_the_door_composes_the_installed_judges(root, orient_berth, constrain_berth):
    # Identity first: the door's judge IS the inspector's — one implementation,
    # two mouths, nothing to drift between.
    assert survey_mod.judge_survey is inspector_mod.judge_survey
    phantom = dict(good_packet(constrain_berth),
                   holdings=[{"what": "a phantom holding",
                              "address": "no/such/thing.py"}])
    expect_refusal(lambda: validate_survey(phantom, root=root),
                   "survey_holdings_resolve")
    unswept = dict(good_packet(constrain_berth), sought=[])
    expect_refusal(lambda: validate_survey(unswept, root=root),
                   "survey_coverage_complete")
    unmeasured = dict(good_packet(constrain_berth),
                      absences=[{"what": "an unmeasured absence"}])
    expect_refusal(lambda: validate_survey(unmeasured, root=root),
                   "survey_coverage_complete")
    # And the inspector never imports survey — the module cannot shape its judge.
    inspector_src = Path(inspector_mod.__file__).read_text(encoding="utf-8")
    assert "cairn.devices.codemother.machines.survey.survey" not in inspector_src, \
        "direction inversion: the judge's owner must never import the judged"


def test_the_berth_lands_and_the_door_holds(root, orient_berth, constrain_berth):
    berth_dir = os.path.join(root, "instance", "survey_berth")
    packet = good_packet(constrain_berth)
    path = write_survey(packet, instance_dir=berth_dir, root=root)
    assert os.path.basename(path).startswith("survey-")
    with open(path) as fh:
        assert json.load(fh) == packet, "the berthed packet round-trips whole"
    refused = dict(packet, sought=[])
    try:
        write_survey(refused, instance_dir=berth_dir, root=root)
        raise AssertionError("the door passed what the judges red")
    except SurveyRefused:
        pass
    assert len(os.listdir(berth_dir)) == 1, \
        "a refused packet leaves nothing behind the door"


def test_deposit_back_is_gated(root, orient_berth, constrain_berth):
    berth_dir = os.path.join(root, "instance", "deposit_berth")
    packet = good_packet(constrain_berth)
    berth = write_survey(packet, instance_dir=berth_dir, root=root)
    content = survey_node_content(packet)
    assert content.startswith("sweep the alpha territory — HOLDS: ") \
        and "ABSENT: a prior sweep" in content, \
        "the node content is the ONE rendering: upstream intent + the inventory"
    # A berth that does not exist refuses, tree untouched.
    table = nexus_table(_NEXUS)
    before = trees.tree_state(_NEXUS, table=table, owner="chart")
    expect_refusal(lambda: deposit_survey(packet, [1.0, 0.0, 0.0],
                                          berth_path=berth + ".gone", root=root),
                   "does not exist")
    assert trees.tree_state(_NEXUS, table=table, owner="chart") == before
    # The real deposit lands in the survey corpus with the berth as provenance.
    unique = content + f" [{_NEXUS}]"
    r = trees.deposit(unique, [1.0, 0.0, 0.0],
                      {"source": berth, "constrain_ref": packet["constrain_ref"],
                       "confidence": packet["confidence"]},
                      tree=_NEXUS, table=table, owner="chart")
    rows = store.read(trees.NODES_TABLE, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == unique
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["standing"] == "hypothesis"


def test_import_allowlist(root, orient_berth, constrain_berth):
    # Composed over orient's import_map: the allowlist matches the module that
    # ACTUALLY ENTERS, not the spelling.
    from cairn.tools.orient.orient import import_map
    allow = ("__future__", "hashlib", "json", "os", "pathlib", "time",
             "cairn.machines.build_inspector.inspector", "cairn.tools.chain.grammar",
             "cairn.tools.tree.tree", "cairn.tools.orient.orient",
             # cairn.tools.gate joined 2026-08-13 (ruling every-machine-carries-
             # its-own-inspector-and-gate): this stage now holds its own gate, and
             # gate-ness is a DIRECT-import fact — which is how `cairn determinism`
             # and `cairnmap --gate` see it from outside without being told.
             "cairn.tools.gate.gate")
    seen = import_map(survey_mod.__file__)["measured"]["imports"]
    offenders = [m for m in seen
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"survey.py imports outside its allowlist: {offenders} — four composed "
        "doors only: the inspector's judge, chart's settled orient machinery, "
        "chart's tree verbs, and the orient instrument (the settled measurer)")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            t = nexus_table(_NEXUS)
            cur.execute(f'DROP TABLE IF EXISTS "{t}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
    finally:
        conn.close()



def test_refusal_is_one_pass_complete(root, orient_berth, constrain_berth):
    """Ticket chart-doors-refuse-in-one-pass: a multi-defective packet learns EVERY
    shape lack in ONE refusal, a second identical firing names the identical set
    (no whack-a-mole), and a broken chain read names its remediation."""
    bad = good_packet(constrain_berth)
    del bad["holdings"]
    bad["confidence"] = 2.0
    bad["provenance"] = dict(bad["provenance"], intruder="martian")

    def lack_set():
        try:
            validate_survey(bad, root=root)
        except SurveyRefused as e:
            msg = str(e)
            assert "all named on this one pass" in msg, msg
            return frozenset(l.strip() for l in msg.splitlines()
                             if l.strip().startswith("- "))
        raise AssertionError("multi-defective packet passed the gate")

    first, second = lack_set(), lack_set()
    assert first == second, (first, second)
    assert len(first) >= 3, first
    joined = " ".join(first)
    for needle in ("missing fields", "confidence", "stratum"):
        assert needle in joined, (needle, joined)
    try:
        survey_floor(os.path.join(root, "no-such-berth.json"))
        raise AssertionError("floor read a berth that does not exist")
    except SurveyRefused as e:
        assert "REMEDIATION" in str(e), str(e)



def test_request_identity_is_physics(root, orient_berth, constrain_berth):
    """Tickets berths-carry-request-identity + the-claim-rides-every-link: a packet
    claiming ticket A over a berth claiming ticket B is refused (MISMATCH), and a
    CLAIMLESS packet over that same claimed berth is refused (VANISH — Akien's
    verdict on cbbadb13530f: no warns, refuse and send back) — both named in the
    one-pass refusal."""
    foreign_doc = json.load(open(constrain_berth))
    foreign_doc["ticket"] = "tkt-b"
    foreign = os.path.join(root, "foreign-survey-ref.json")
    with open(foreign, "w") as fh:
        json.dump(foreign_doc, fh)
    bad = good_packet(constrain_berth)
    bad["ticket"] = "tkt-a"
    bad["constrain_ref"] = foreign
    try:
        validate_survey(bad, root=root)
        raise AssertionError("claim-A packet passed over a claim-B berth")
    except SurveyRefused as e:
        msg = str(e)
        assert "request-identity mismatch" in msg and "tkt-b" in msg, msg
    silent = good_packet(constrain_berth)
    silent.pop("ticket", None)
    silent["constrain_ref"] = foreign
    try:
        validate_survey(silent, root=root)
        raise AssertionError("claimless packet passed over a claimed berth")
    except SurveyRefused as e:
        msg = str(e)
        assert "request-identity vanished" in msg and "tkt-b" in msg, msg


def _main() -> int:
    root, orient_berth, constrain_berth = make_root()
    checks = [
        test_request_identity_is_physics,
        test_refusal_is_one_pass_complete,
        test_the_chain_is_physics_at_depth_3,
        test_floor_surfaces_the_census_verbatim,
        test_the_fixture_speaks_what_the_orient_floor_AUTHORS,
        test_schema_gate_refuses_hollow_shapes,
        test_the_door_composes_the_installed_judges,
        test_the_berth_lands_and_the_door_holds,
        test_deposit_back_is_gated,
        test_import_allowlist,
    ]
    try:
        for check in checks:
            check(root, orient_berth, constrain_berth)
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
        shutil.rmtree(os.path.dirname(root), ignore_errors=True)  # tmp holds repo + commons sibling
    print("green — chart/survey: stage 3 fills only through an unbroken two-link "
          "chain, the floor surfaces census rows verbatim, the schema gate refuses "
          "hollow shapes, the door composes the inspector's own judges (by "
          "identity), the berth round-trips, the deposit-back is gated, and the "
          "brick's doors are exactly the four composed ones")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
